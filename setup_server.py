#!/usr/bin/env python3
"""Server da botni to'g'ri ishga tushirish."""
import paramiko

HOST = "100.54.122.218"
USER = "ubuntu"
PASSWD = "_pbGEqc%Jo#LS6$Y7EE*tFrg"
REMOTE_DIR = "/home/ubuntu/taga_bot"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWD, timeout=30)
print("Ulandi!")

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out: print(out)
    if err and 'WARNING' not in err and 'DEPRECATION' not in err:
        filtered = [l for l in err.split('\n') if l.strip() and 'WARNING' not in l and 'DEPRECATION' not in l]
        if filtered: print("ERR:", '\n'.join(filtered))
    return out

# Python va pip
run("python3 --version")
run("pip3 --version || (curl -sS https://bootstrap.pypa.io/get-pip.py | python3)")

# Pip orqali kerakli paketlar
print("\n[1] Paketlar o'rnatilmoqda...")
run("pip3 install 'aiogram>=3.0,<4.0' lottie pillow fonttools 2>&1 | tail -5", timeout=180)

# requirements.txt
print("\n[2] requirements.txt dan o'rnatish...")
run(f"cd {REMOTE_DIR} && pip3 install -r requirements.txt 2>&1 | tail -5", timeout=120)

# PM2 o'rnatish
print("\n[3] PM2...")
run("npm install -g pm2 2>&1 | tail -3", timeout=60)

# Botni ishga tushirish
print("\n[4] Bot ishga tushirilmoqda...")
run(f"cd {REMOTE_DIR} && pm2 delete taga_bot 2>/dev/null; true")
run(f"cd {REMOTE_DIR} && BOT_TOKEN=8848328642:AAF4sNEeR911QQqY-rBmURRepgWyOsIlVvs pm2 start python3 --name taga_bot -- sonnet_final.py")
run("pm2 save")

# Startup sozlash
print("\n[5] Auto-start sozlanmoqda...")
out = run("pm2 startup 2>&1 | tail -2")
# Agar sudo buyrug' chiqsa - uni bajar
if "sudo" in out:
    sudo_cmd = [l for l in out.split('\n') if 'sudo' in l]
    if sudo_cmd:
        run(sudo_cmd[0].strip())

# Status
import time
time.sleep(3)
print("\n=== FINAL STATUS ===")
run("pm2 status")
run("pm2 logs taga_bot --lines 10 --nostream 2>&1")

client.close()
print("\n✅ Bot VPS da ishlamoqda!")
