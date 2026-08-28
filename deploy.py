#!/usr/bin/env python3
"""Bot fayllarini VPS ga deploy qilish."""
import os
import sys
import tarfile
import io

HOST = "100.54.122.218"
USER = "ubuntu"
PASSWD = "_pbGEqc%Jo#LS6$Y7EE*tFrg"
REMOTE_DIR = "/home/ubuntu/taga_bot"

# Deploy qilinadigan fayllar va papkalar
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
INCLUDE_FILES = [
    "sonnet_final.py", "logo_engine.py", "logo_emoji_ids.py",
    "template_engine.py", "font_render.py", "templates_config.py",
    "requirements.txt",
]
INCLUDE_DIRS = ["templates", "templates_tgs", "templates_tgs2", "templates_tgs3", "fonts"]

try:
    import paramiko
except ImportError:
    print("paramiko o'rnatilmagan. O'rnatilmoqda...")
    os.system(f'"{sys.executable}" -m pip install paramiko')
    import paramiko

print(f"[1/4] {HOST} ga ulanmoqda...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWD, timeout=30)
print("      Ulandi!")

# Tar arxiv yaratish (xotirada)
print("[2/4] Fayllar arxivlanmoqda...")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    for fname in INCLUDE_FILES:
        fpath = os.path.join(LOCAL_DIR, fname)
        if os.path.exists(fpath):
            tar.add(fpath, arcname=fname)
            print(f"      + {fname}")
    for dname in INCLUDE_DIRS:
        dpath = os.path.join(LOCAL_DIR, dname)
        if os.path.isdir(dpath):
            tar.add(dpath, arcname=dname)
            print(f"      + {dname}/")
buf.seek(0)
data = buf.read()
print(f"      Arxiv hajmi: {len(data)//1024} KB")

# Remote papka tayyorlash
print("[3/4] Server tayyorlanmoqda...")
cmds = [
    f"mkdir -p {REMOTE_DIR}",
    f"pkill -f 'python.*sonnet_final' || true",
    f"pkill -f 'pm2.*taga' || true",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()

# Fayllarni yuborish
print("[4/4] Fayllar yuklanmoqda...")
sftp = client.open_sftp()

# Arxivni server ga yuborish
remote_tar = f"{REMOTE_DIR}/bot.tar.gz"
with sftp.open(remote_tar, "wb") as f:
    f.write(data)
    
# Arxivni ochish
stdin, stdout, stderr = client.exec_command(f"cd {REMOTE_DIR} && tar -xzf bot.tar.gz && rm bot.tar.gz")
stdout.channel.recv_exit_status()
err = stderr.read().decode()
if err:
    print(f"      XATO: {err}")
else:
    print("      Fayllar yuklandi!")

sftp.close()

# Serverni sozlash
print("\n[+] Server sozlanmoqda...")

setup_script = f"""
cd {REMOTE_DIR}

# Python va pip tekshirish
python3 --version

# pip ni yangilash
python3 -m pip install --upgrade pip --quiet

# Requirements o'rnatish
pip3 install aiogram==3.* --quiet 2>&1 | tail -3
pip3 install lottie pillow fonttools --quiet 2>&1 | tail -3

# PM2 bor-yo'qligini tekshirish
if ! command -v pm2 &> /dev/null; then
    echo "PM2 o'rnatilmoqda..."
    npm install -g pm2 2>/dev/null || (curl -sL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm install -g pm2)
fi

# BOT_TOKEN muhit o'zgaruvchisini o'rnatish
export BOT_TOKEN="8848328642:AAF4sNEeR911QQqY-rBmURRepgWyOsIlVvs"

# PM2 bilan botni ishga tushirish
pm2 delete taga_bot 2>/dev/null || true
pm2 start python3 --name taga_bot -- sonnet_final.py
pm2 save
pm2 startup 2>/dev/null | tail -1

echo "=== BOT STATUS ==="
pm2 status taga_bot
"""

print("    Paketlar o'rnatilmoqda (1-2 daqiqa)...")
stdin, stdout, stderr = client.exec_command(setup_script, timeout=180)
output = stdout.read().decode()
errors = stderr.read().decode()

print(output)
if errors:
    # filter out benign stderr
    real_errors = [l for l in errors.split('\n') if l and 'WARNING' not in l and 'DEPRECATION' not in l]
    if real_errors:
        print("Ogohlantirishlar:", '\n'.join(real_errors[:5]))

# Status tekshirish
print("\n=== YAKUNIY STATUS ===")
stdin, stdout, stderr = client.exec_command(f"cd {REMOTE_DIR} && pm2 status")
print(stdout.read().decode())

client.close()
print("\n✅ Deploy muvaffaqiyatli yakunlandi!")
print(f"   Bot {REMOTE_DIR} papkasida ishlamoqda.")
print(f"   Loglarni ko'rish: ssh {USER}@{HOST} 'pm2 logs taga_bot'")
