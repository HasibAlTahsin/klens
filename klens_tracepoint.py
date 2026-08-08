#!/usr/bin/env python3
import sys, ctypes as ct, os
from bcc import BPF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_engine import handle as pii_handle

TARGET_PID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if not TARGET_PID:
    print('Usage: sudo python3 klens_tracepoint.py <server_pid>')
    sys.exit(1)

BPF_SRC = r'''
#include <uapi/linux/ptrace.h>
#define MAXCAP 256
#define TGT_PID __TARGET_PID__

struct event_t {
    u32 pid;
    u32 len;
    u32 syscall;
    u32 fd;
    char buf[MAXCAP];
};

BPF_PERF_OUTPUT(events);

static __always_inline int filter() {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    return pid != TGT_PID;
}

static __always_inline void capture(struct pt_regs *ctx, int fd, const void *data, size_t count, u32 sc) {
    struct event_t ev = {};
    ev.pid = bpf_get_current_pid_tgid() >> 32;
    ev.fd = fd;
    ev.syscall = sc;
    ev.len = count < MAXCAP ? count : MAXCAP;
    bpf_probe_read_user(&ev.buf, ev.len & (MAXCAP - 1), data);
    events.perf_submit(ctx, &ev, sizeof(ev));
}

// Tracepoint for sys_enter_write
TRACEPOINT_PROBE(syscalls, sys_enter_write) {
    if (filter()) return 0;
    int fd = args->fd;
    const void *buf = (const void *)args->buf;
    size_t count = args->count;
    capture(args, fd, buf, count, 1);
    return 0;
}

// Tracepoint for sys_enter_sendto
TRACEPOINT_PROBE(syscalls, sys_enter_sendto) {
    if (filter()) return 0;
    int fd = args->fd;
    const void *buf = (const void *)args->buf;
    size_t len = args->len;
    capture(args, fd, buf, len, 2);
    return 0;
}
'''

BPF_SRC = BPF_SRC.replace('__TARGET_PID__', str(TARGET_PID))

b = BPF(text=BPF_SRC)

SC_NAMES = {1: 'write', 2: 'sendto'}

print(f'[klens] tracepoint probing PID {TARGET_PID}')
print(f'[klens] Ctrl-C to stop')

class Event(ct.Structure):
    _fields_ = [
        ('pid', ct.c_uint),
        ('len', ct.c_uint),
        ('syscall', ct.c_uint),
        ('fd', ct.c_uint),
        ('buf', ct.c_char * 256),
    ]

def on_event(cpu, data, size):
    ev = ct.cast(data, ct.POINTER(Event)).contents
    try:
        payload = bytes(ev.buf[:ev.len]).decode('utf-8', 'replace')
    except Exception:
        return
    sc = SC_NAMES.get(ev.syscall, '?')
    preview = payload[:100].replace('\n', '\\n')
    print(f'[{sc}] PID={ev.pid} fd={ev.fd} | {preview}')
    pii_handle(ev.pid, payload, syscall=sc, fd=ev.fd)

b['events'].open_perf_buffer(on_event, page_cnt=64)

while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        print('\n[klens] stopped.')
        sys.exit(0)
