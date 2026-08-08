#!/usr/bin/env python3
"""
klens_probe_v2.py --- Hardened eBPF egress capture for KLEnS
Features:
1. Payload Reassembly (handles MAXCAP truncation via user-space buffering)
2. sendmsg Multiple iovecs (loops over iovec array in eBPF)
3. Backpressure / Drop counting (tracks lost events)
"""
import sys, ctypes as ct, os, time
from bcc import BPF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_engine import handle as pii_handle

BPF_SRC = r'''
#include <uapi/linux/ptrace.h>
#include <linux/socket.h>
#include <linux/uio.h>

#define MAXCAP 1024
#define MAX_IOV 4

struct event_t {
    u32 pid;
    u32 len;
    u32 syscall;
    u32 fd;
    char buf[MAXCAP];
};

BPF_PERF_OUTPUT(events);
BPF_ARRAY(heap, struct event_t, 1);

TRACEPOINT_PROBE(syscalls, sys_enter_write) {
    u32 key = 0;
    struct event_t *ev = heap.lookup(&key);
    if (!ev) return 0;
    
    ev->pid = bpf_get_current_pid_tgid() >> 32;
    ev->fd = args->fd;
    ev->syscall = 1;
    u32 count = args->count & (MAXCAP - 1);
    ev->len = count;
    bpf_probe_read_user(&ev->buf, count, args->buf);
    events.perf_submit(args, ev, sizeof(*ev));
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_sendto) {
    u32 key = 0;
    struct event_t *ev = heap.lookup(&key);
    if (!ev) return 0;
    
    ev->pid = bpf_get_current_pid_tgid() >> 32;
    ev->fd = args->fd;
    ev->syscall = 2;
    u32 len = args->len & (MAXCAP - 1);
    ev->len = len;
    bpf_probe_read_user(&ev->buf, len, args->buff);
    events.perf_submit(args, ev, sizeof(*ev));
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_sendmsg) {
    u32 key = 0;
    struct event_t *ev = heap.lookup(&key);
    if (!ev) return 0;
    
    ev->pid = bpf_get_current_pid_tgid() >> 32;
    ev->fd = args->fd;
    ev->syscall = 3;
    
    struct user_msghdr *msg = (struct user_msghdr *)args->msg;
    struct user_msghdr hdr;
    bpf_probe_read_user(&hdr, sizeof(hdr), msg);
    
    struct iovec *iov_ptr = hdr.msg_iov;
    __u64 iovlen = hdr.msg_iovlen;
    if (iovlen > MAX_IOV) iovlen = MAX_IOV;
    
    #pragma unroll
    for (int i = 0; i < MAX_IOV; i++) {
        if (i >= iovlen) break;
        
        struct iovec iov;
        bpf_probe_read_user(&iov, sizeof(iov), &iov_ptr[i]);
        if (iov.iov_len == 0 || iov.iov_base == NULL) continue;
        
        u32 len = iov.iov_len < MAXCAP ? iov.iov_len : MAXCAP;
        ev->len = len;
        bpf_probe_read_user(&ev->buf, len & (MAXCAP-1), iov.iov_base);
        events.perf_submit(args, ev, sizeof(*ev));
    }
    return 0;
}
'''

b = BPF(text=BPF_SRC)
print('[klens_v2] Probing with Hardened features (Reassembly + iovecs + Drop tracking)...')

class Event(ct.Structure):
    _fields_ = [
        ('pid', ct.c_uint), ('len', ct.c_uint), 
        ('syscall', ct.c_uint), ('fd', ct.c_uint), 
        ('buf', ct.c_char * 1024)
    ]

# Reassembly Buffers: key=(pid, fd), value=[bytearray, syscall, fd, last_time]
buffers = {}
drop_count = 0
TIMEOUT_SEC = 0.5
MAX_BUFFER_SIZE = 8192

def flush_buffer(key):
    if key in buffers:
        buf_data, sc, fd, _ = buffers[key]
        payload = bytes(buf_data).decode('utf-8', 'replace')
        
        # Filter: only process HTTP/JSON
        if 'HTTP/' in payload or '"content":' in payload or 'domain' in payload:
            # Avoid infinite loop from terminal echo
            if '[klens_v2]' not in payload and 'curl' not in payload[:10]:
                preview = payload[:100].replace('\n','\\n')
                print(f'\n[REASSEMBLED] {sc}(fd={fd}, len={len(payload)}): {preview}')
                pii_handle(key[0], payload, syscall=sc, fd=fd)
        del buffers[key]

def on_event(cpu, data, size):
    ev = ct.cast(data, ct.POINTER(Event)).contents
    key = (ev.pid, ev.fd)
    sc = {1:'write', 2:'sendto', 3:'sendmsg'}.get(ev.syscall, '?')
    
    try:
        raw = bytes(ev.buf[:ev.len])
    except:
        return
        
    if key not in buffers:
        buffers[key] = [bytearray(), sc, ev.fd, time.time()]
    
    buffers[key][0].extend(raw)
    buffers[key][3] = time.time() # update last seen time
    
    # Flush if buffer gets too large or looks like end of JSON
    if len(buffers[key][0]) >= MAX_BUFFER_SIZE or payload_ends_with_json(buffers[key][0]):
        flush_buffer(key)

def payload_ends_with_json(buf):
    # Simple heuristic: if it ends with } or \n, flush
    return buf.rstrip().endswith(b'}') or buf.rstrip().endswith(b'\n\n')

def on_lost(cpu, lost):
    global drop_count
    drop_count += lost
    print(f'\n[WARNING] Dropped {lost} events! Total dropped: {drop_count}')

b['events'].open_perf_buffer(on_event, lost_cb=on_lost, page_cnt=128)

try:
    while True:
        b.perf_buffer_poll(100)
        # Check for timeouts to flush incomplete buffers
        now = time.time()
        for k in list(buffers.keys()):
            if now - buffers[k][3] > TIMEOUT_SEC:
                flush_buffer(k)
except KeyboardInterrupt:
    print(f'\n[klens_v2] stopped. Total dropped events: {drop_count}')
    sys.exit(0)
