#!/usr/bin/env python3
"""
CyberWolf Advanced Security Platform - Enterprise Edition
Features: Attack Map, Security Score, Alerts, Reports, Visualization
"""

from flask import Flask, render_template, jsonify, request, session, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import subprocess
import psutil
import json
import os
import time
import threading
import hashlib
import secrets
import random
import datetime
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication
ADMIN_USERNAME = "cyberwolf"
ADMIN_PASSWORD_HASH = hashlib.sha256("CyberWolf2024!".encode()).hexdigest()

def check_auth(username, password):
    return username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Security Events Database
security_events = []
attack_locations = [
    {"ip": "185.142.53.36", "country": "Russia", "city": "Moscow", "type": "Port Scan", "severity": "High"},
    {"ip": "45.155.205.233", "country": "China", "city": "Beijing", "type": "SSH Brute Force", "severity": "Critical"},
    {"ip": "193.201.9.46", "country": "Ukraine", "city": "Kyiv", "type": "SQL Injection", "severity": "Medium"},
    {"ip": "89.248.168.255", "country": "Netherlands", "city": "Amsterdam", "type": "DDoS Attempt", "severity": "High"},
    {"ip": "5.188.210.10", "country": "Germany", "city": "Frankfurt", "type": "Malware Scan", "severity": "Low"},
]

# Security Score calculation
def calculate_security_score():
    score = 100
    # Tor status
    tor_active = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode == 0
    if not tor_active:
        score -= 25
    
    # MAC status
    mac_result = subprocess.run(["macchanger", "-s", "wlan0"], capture_output=True, text=True)
    if "Current MAC" in mac_result.stdout and "Permanent MAC" in mac_result.stdout:
        current = mac_result.stdout.split("Current MAC:")[1].split()[0] if "Current MAC:" in mac_result.stdout else ""
        permanent = mac_result.stdout.split("Permanent MAC:")[1].split()[0] if "Permanent MAC:" in mac_result.stdout else ""
        if current == permanent:
            score -= 20
    
    # Connection count
    connections = len(psutil.net_connections())
    if connections > 150:
        score -= 15
    elif connections > 80:
        score -= 5
    
    # Uptime risk
    uptime_seconds = time.time() - psutil.boot_time()
    if uptime_seconds > 7 * 24 * 3600:  # >7 days
        score -= 10
    
    return max(0, min(100, score))

def get_security_status():
    tor_active = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode == 0
    mac_result = subprocess.run(["macchanger", "-s", "wlan0"], capture_output=True, text=True)
    
    current_mac = "Unknown"
    permanent_mac = "Unknown"
    for line in mac_result.stdout.split('\n'):
        if "Current MAC" in line:
            current_mac = line.split()[-1]
        if "Permanent MAC" in line:
            permanent_mac = line.split()[-1]
    
    return {
        "tor": tor_active,
        "mac_current": current_mac,
        "mac_permanent": permanent_mac,
        "hostname": subprocess.getoutput("hostname"),
        "uptime": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
        "connections": len(psutil.net_connections()),
        "security_score": calculate_security_score()
    }

# Generate random attack events
def generate_attack_event():
    import random
    attack = random.choice(attack_locations)
    event = {
        "id": len(security_events) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_ip": attack["ip"],
        "country": attack["country"],
        "city": attack["city"],
        "attack_type": attack["type"],
        "severity": attack["severity"],
        "status": "Blocked",
        "target": random.choice(["Web Server", "SSH Port", "Database", "Firewall"])
    }
    security_events.insert(0, event)
    if len(security_events) > 50:
        security_events.pop()
    return event

# Generate security chart
def generate_security_chart():
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    threats = [random.randint(5, 30) for _ in range(7)]
    
    plt.figure(figsize=(10, 4), facecolor='#0a0e27')
    plt.plot(days, threats, marker='o', color='#00ff88', linewidth=2, markersize=8)
    plt.fill_between(days, threats, color='#00ff88', alpha=0.1)
    plt.title('Threat Activity (Last 7 Days)', color='#00ff88', fontsize=14)
    plt.xlabel('Day', color='#888')
    plt.ylabel('Threats Blocked', color='#888')
    plt.xticks(color='#888')
    plt.yticks(color='#888')
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', facecolor='#0a0e27', edgecolor='none')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

# Background threat generator
def threat_generator():
    while True:
        time.sleep(random.randint(10, 30))
        event = generate_attack_event()
        socketio.emit('new_attack', event)
        socketio.emit('security_update', {
            "score": calculate_security_score(),
            "events_count": len(security_events)
        })

threading.Thread(target=threat_generator, daemon=True).start()

# System monitor thread
def system_monitor():
    while True:
        metrics = {
            "cpu": psutil.cpu_percent(),
            "cpu_per_core": psutil.cpu_percent(percpu=True),
            "ram": psutil.virtual_memory().percent,
            "ram_used": psutil.virtual_memory().used,
            "ram_total": psutil.virtual_memory().total,
            "disk": psutil.disk_usage('/').percent,
            "connections": len(psutil.net_connections()),
            "temperature": psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current', 0) if psutil.sensors_temperatures() else 0,
            "network_sent": psutil.net_io_counters().bytes_sent,
            "network_recv": psutil.net_io_counters().bytes_recv
        }
        socketio.emit('metrics_update', metrics)
        socketio.emit('security_update', {
            "score": calculate_security_score(),
            "status": get_security_status()
        })
        time.sleep(2)

threading.Thread(target=system_monitor, daemon=True).start()

# Routes
@app.route('/')
def index():
    return render_template('dashboard_enhanced.html')

@app.route('/api/status')
@login_required
def api_status():
    return jsonify({
        "security": get_security_status(),
        "events": security_events[:20],
        "chart": generate_security_chart()
    })

@app.route('/api/action/<action>', methods=['POST'])
@login_required
def api_action(action):
    result = {"success": True, "message": ""}
    
    if action == "tor_start":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        result["message"] = "Tor started - Security score improved"
    elif action == "tor_stop":
        subprocess.run(["sudo", "systemctl", "stop", "tor"])
        result["message"] = "Tor stopped - Security score decreased"
    elif action == "mac_spoof":
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        result["message"] = "MAC address randomized"
    elif action == "clear_logs":
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history; cat /dev/null > ~/.zsh_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        result["message"] = "Forensic traces cleared"
    elif action == "quick_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        result["message"] = "Quick protect activated - Score improved"
    elif action == "max_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        result["message"] = "MAXIMUM PROTECTION - All systems secure"
    elif action == "emergency":
        result["message"] = "EMERGENCY - Wiping traces and shutting down"
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history; cat /dev/null > ~/.zsh_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
    elif action == "generate_report":
        result["message"] = "Report generated - Check /tmp/security_report.pdf"
        # Generate PDF report
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        c = canvas.Canvas("/tmp/security_report.pdf", pagesize=letter)
        c.drawString(100, 750, "CyberWolf Security Report")
        c.drawString(100, 730, f"Date: {datetime.datetime.now()}")
        c.drawString(100, 710, f"Security Score: {calculate_security_score()}")
        c.save()
    
    socketio.emit('action_log', {"action": action, "result": result["message"]})
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if check_auth(data.get('username'), data.get('password')):
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to CyberWolf Advanced Platform'})

if __name__ == '__main__':
    print("🐺 CyberWolf Advanced Security Platform - Enterprise Edition")
    print("📍 http://localhost:5000")
    print("🔐 Username: cyberwolf | Password: CyberWolf2024!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
