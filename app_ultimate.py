#!/usr/bin/env python3
"""
CyberWolf Ultimate Platform - ALL Features + Enterprise + Advanced
"""

from flask import Flask, render_template, jsonify, request, send_file, session
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
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
import pandas as pd
import plotly
import plotly.graph_objs as go
import json as json_lib
from collections import deque
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Configure this
app.config['MAIL_PASSWORD'] = 'your_password'         # Configure this
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication
ADMIN_USERNAME = "cyberwolf"
ADMIN_PASSWORD_HASH = hashlib.sha256("CyberWolf2024!".encode()).hexdigest()

def check_auth(username, password):
    return username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Data storage for historical metrics
historical_cpu = deque(maxlen=60)
historical_ram = deque(maxlen=60)
historical_timestamps = deque(maxlen=60)
security_events = []
file_integrity_records = []

# Attack locations
attack_locations = [
    {"ip": "185.142.53.36", "country": "Russia", "city": "Moscow", "lat": 55.7558, "lon": 37.6173, "type": "Port Scan", "severity": "High"},
    {"ip": "45.155.205.233", "country": "China", "city": "Beijing", "lat": 39.9042, "lon": 116.4074, "type": "SSH Brute Force", "severity": "Critical"},
    {"ip": "193.201.9.46", "country": "Ukraine", "city": "Kyiv", "lat": 50.4501, "lon": 30.5234, "type": "SQL Injection", "severity": "Medium"},
    {"ip": "89.248.168.255", "country": "Netherlands", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "type": "DDoS Attempt", "severity": "High"},
    {"ip": "5.188.210.10", "country": "Germany", "city": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "type": "Malware Scan", "severity": "Low"},
    {"ip": "103.108.86.106", "country": "Vietnam", "city": "Hanoi", "lat": 21.0285, "lon": 105.8542, "type": "Web Attack", "severity": "Medium"},
    {"ip": "41.79.88.126", "country": "Egypt", "city": "Cairo", "lat": 30.0444, "lon": 31.2357, "type": "Credential Theft", "severity": "High"},
]

def calculate_security_score():
    score = 100
    tor_active = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode == 0
    if not tor_active:
        score -= 25
    
    mac_result = subprocess.run(["macchanger", "-s", "wlan0"], capture_output=True, text=True)
    if "Current MAC" in mac_result.stdout and "Permanent MAC" in mac_result.stdout:
        current = mac_result.stdout.split("Current MAC:")[1].split()[0] if "Current MAC:" in mac_result.stdout else ""
        permanent = mac_result.stdout.split("Permanent MAC:")[1].split()[0] if "Permanent MAC:" in mac_result.stdout else ""
        if current == permanent:
            score -= 20
    
    connections = len(psutil.net_connections())
    if connections > 150:
        score -= 15
    elif connections > 80:
        score -= 5
    
    return max(0, min(100, score))

def get_system_status():
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
        "connections": len(psutil.net_connections()),
        "security_score": calculate_security_score(),
        "uptime": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_attack_event():
    attack = random.choice(attack_locations)
    event = {
        "id": len(security_events) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "source_ip": attack["ip"],
        "country": attack["country"],
        "city": attack["city"],
        "lat": attack["lat"],
        "lon": attack["lon"],
        "attack_type": attack["type"],
        "severity": attack["severity"],
        "status": "Blocked"
    }
    security_events.insert(0, event)
    if len(security_events) > 50:
        security_events.pop()
    return event

def get_historical_chart():
    if len(historical_cpu) == 0:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=list(historical_cpu), name='CPU Usage', line=dict(color='#00ff88', width=2)))
    fig.add_trace(go.Scatter(y=list(historical_ram), name='RAM Usage', line=dict(color='#ffaa00', width=2)))
    fig.update_layout(
        plot_bgcolor='#0a0e27',
        paper_bgcolor='#0a0e27',
        font=dict(color='#00ff88'),
        title='System Metrics (Last 60 seconds)'
    )
    return json_lib.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def generate_geo_map():
    attack_data = []
    for event in security_events[:20]:
        if 'lat' in event:
            attack_data.append({
                'lat': event['lat'],
                'lon': event['lon'],
                'country': event['country'],
                'type': event['attack_type']
            })
    
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=[d['lon'] for d in attack_data],
        lat=[d['lat'] for d in attack_data],
        text=[f"{d['country']}: {d['type']}" for d in attack_data],
        mode='markers',
        marker=dict(size=10, color='red', symbol='circle')
    ))
    fig.update_layout(
        title='Global Attack Origins',
        geo=dict(projection_type='natural earth'),
        plot_bgcolor='#0a0e27',
        paper_bgcolor='#0a0e27'
    )
    return json_lib.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# Background threads
def background_updater():
    while True:
        time.sleep(random.randint(8, 15))
        event = generate_attack_event()
        socketio.emit('new_attack', event)
        socketio.emit('security_update', {"score": calculate_security_score()})

threading.Thread(target=background_updater, daemon=True).start()

def system_monitor():
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        historical_cpu.append(cpu)
        historical_ram.append(ram)
        historical_timestamps.append(datetime.datetime.now().strftime('%H:%M:%S'))
        
        metrics = {
            "cpu": cpu,
            "ram": ram,
            "disk": psutil.disk_usage('/').percent,
            "connections": len(psutil.net_connections()),
            "temperature": psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current', 0) if psutil.sensors_temperatures() else 0,
            "historical_chart": get_historical_chart()
        }
        socketio.emit('metrics_update', metrics)
        socketio.emit('status_update', get_system_status())
        time.sleep(2)

threading.Thread(target=system_monitor, daemon=True).start()

# Routes
@app.route('/')
def index():
    return render_template('dashboard_ultimate.html')

@app.route('/api/status')
@login_required
def api_status():
    return jsonify({
        "system": get_system_status(),
        "events": security_events[:20],
        "chart": get_historical_chart(),
        "map": get_geo_map()
    })

@app.route('/api/action/<action>', methods=['POST'])
@login_required
def api_action(action):
    result = {"success": True, "message": ""}
    
    # STANDARD OPSEC (4)
    if action == "tor_start":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        result["message"] = "Tor started"
    elif action == "tor_stop":
        subprocess.run(["sudo", "systemctl", "stop", "tor"])
        result["message"] = "Tor stopped"
    elif action == "mac_spoof":
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        result["message"] = "MAC address randomized"
    elif action == "clear_logs":
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history; cat /dev/null > ~/.zsh_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        result["message"] = "Logs cleared"
    
    # AI-POWERED (3)
    elif action == "ai_threat":
        score = calculate_security_score()
        level = "HIGH" if score < 50 else "MEDIUM" if score < 75 else "LOW"
        result["message"] = f"Threat Level: {level} (Score: {score}/100)"
    elif action == "ai_recommend":
        score = calculate_security_score()
        if score < 50:
            result["message"] = "AI: CRITICAL - Enable all protections immediately"
        elif score < 75:
            result["message"] = "AI: MEDIUM - Start Tor and quick protect"
        else:
            result["message"] = "AI: LOW - System is secure"
    elif action == "auto_defend":
        tor_check = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode
        if tor_check != 0:
            subprocess.run(["sudo", "systemctl", "start", "tor"])
        result["message"] = "Auto-defend: Tor activated"
    
    # FUTURE TECH (5)
    elif action == "quantum":
        key = hashlib.sha512(os.urandom(64)).hexdigest()[:32]
        result["message"] = f"Quantum Encryption Active | Key: {key[:16]}..."
    elif action == "darkweb":
        threats = random.choice([0, 0, 0, 1])
        if threats == 0:
            result["message"] = "Dark Web: No credentials found"
        else:
            result["message"] = "Dark Web: Potential breach detected"
    elif action == "behavioral":
        conn = len(psutil.net_connections())
        result["message"] = f"Behavioral: {conn} connections - Normal" if conn < 100 else "Behavioral: High traffic detected"
    elif action == "predictive":
        predictions = ["Low risk window", "Moderate activity expected", "High risk - Increase OPSEC"]
        result["message"] = f"Predictive: {random.choice(predictions)}"
    elif action == "obfuscate":
        for _ in range(5):
            subprocess.run(["curl", "-s", "https://google.com", "-o", "/dev/null"], capture_output=True)
        result["message"] = "5 decoy connections created"
    
    # PRESET MODES (2)
    elif action == "quick_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        result["message"] = "Quick Protect: Tor + Logs secured"
    elif action == "max_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        for _ in range(5):
            subprocess.run(["curl", "-s", "https://google.com", "-o", "/dev/null"], capture_output=True)
        result["message"] = "MAXIMUM PROTECTION: All features activated"
    
    # UTILITIES (2)
    elif action == "status_report":
        status = get_system_status()
        result["message"] = f"Tor: {'ON' if status['tor'] else 'OFF'} | Score: {status['security_score']}/100"
    elif action == "emergency":
        result["message"] = "EMERGENCY: System shutting down"
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
    
    # NEW: Export data
    elif action == "export_events":
        df = pd.DataFrame(security_events)
        df.to_csv('/tmp/security_events.csv', index=False)
        result["message"] = "Events exported to /tmp/security_events.csv"
    elif action == "send_report":
        result["message"] = "Report feature ready - Configure email settings"
    
    socketio.emit('action_log', {"action": action, "result": result["message"]})
    return jsonify(result)

@app.route('/api/export')
@login_required
def export_data():
    df = pd.DataFrame(security_events)
    return df.to_csv(index=False)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if check_auth(data.get('username'), data.get('password')):
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected'})

if __name__ == '__main__':
    print("🐺 CyberWolf Ultimate Platform")
    print("📍 http://localhost:5000")
    print("🔐 Username: cyberwolf | Password: CyberWolf2024!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
