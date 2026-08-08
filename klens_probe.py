#!/usr/bin/env python3
import sys, ctypes as ct, os
from bcc import BPF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_engine import handle as pii_handle

BPF_SRC = r'''
#include <uapi/linux/ptrace.h>
#define MAXCAP 1024
struct event_t { u32 pid; u32 len; u32 syscall; u32 fd; char buf[MAXCAP]; };
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
'''

b = BPF(text=BPF_SRC)
print('[klens] Probing LLM responses... (Fixed bug)')

class Event(ct.Structure):
    _fields_ = [('pid', ct.c_uint), ('len', ct.c_uint), ('syscall', ct.c_uint), ('fd', ct.c_uint), ('buf', ct.c_char * 1024)]

def on_event(cpu, data, size):
    ev = ct.cast(data, ct.POINTER(Event)).contents
    try:
        payload = bytes(ev.buf[:ev.len]).decode('utf-8', 'replace')
    except:
        return
    
    sc = {1: 'write', 2: 'sendto'}.get(ev.syscall, '?')
    
    if 'HTTP/1.1 200 OK' in payload or '"content":' in payload:
        if 'curl -s' in payload or '[CAPTURED]' in payload:
            return
        
        # শুধু JSON বডি বের করে নাও, HTTP হেডার বাদ দাও
        if '{' in payload:
            payload = payload[payload.index('{'):]
            
        preview = payload[:250].replace('\n','\\n')
        print(f'\n[CAPTURED] {sc}(fd={ev.fd}, len={ev.len}): {preview}')
        pii_handle(ev.pid, payload, syscall=sc, fd=ev.fd)

b['events'].open_perf_buffer(on_event, page_cnt=64)
while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        break
