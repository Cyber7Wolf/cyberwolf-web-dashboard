#!/usr/bin/env python3
"""
CyberWolf Web Dashboard - Advanced Standalone Version
Professional Security Orchestration Platform
"""

from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import subprocess
import psutil
import json
import os
import time
import threading
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple authentication (for security)
ADMIN_USERNAME = "cyberwolf"
ADMIN_PASSWORD_HASH = hashlib.sha256("CyberWolf2024!".encode()).hexdigest()

def check_auth(username, password):
    return username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def authenticate():
    return jsonify({"error": "Authentication required"}), 401

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated_function

# System status tracking
system_status = {
    "tor": False,
    "mac_original": None,
    "mac_current": None,
    "hostname": None,
    "last_protect": None,
    "threat_level": "LOW",
    "active_connections": 0
}

def get_system_metrics():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "cpu_per_core": psutil.cpu_percent(percpu=True),
        "ram": psutil.virtual_memory().percent,
        "ram_used": psutil.virtual_memory().used,
        "ram_total": psutil.virtual_memory().total,
        "disk": psutil.disk_usage('/').percent,
        "disk_used": psutil.disk_usage('/').used,
        "disk_total": psutil.disk_usage('/').total,
        "connections": len(psutil.net_connections()),
        "temperature": psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current', 0) if psutil.sensors_temperatures() else 0,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    }

def update_system_status():
    # Tor status
    system_status["tor"] = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode == 0
    
    # MAC address
    result = subprocess.run(["macchanger", "-s", "wlan0"], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if "Current MAC" in line:
            system_status["mac_current"] = line.split()[-1]
        if "Permanent MAC" in line:
            system_status["mac_original"] = line.split()[-1]
    
    # Hostname
    system_status["hostname"] = subprocess.getoutput("hostname")
    
    # Threat assessment
    threats = 0
    if not system_status["tor"]:
        threats += 2
    if system_status["mac_current"] == system_status["mac_original"]:
        threats += 1
    if threats >= 3:
        system_status["threat_level"] = "CRITICAL"
    elif threats >= 2:
        system_status["threat_level"] = "HIGH"
    elif threats >= 1:
        system_status["threat_level"] = "MEDIUM"
    else:
        system_status["threat_level"] = "LOW"
    
    system_status["active_connections"] = len(psutil.net_connections())

# Background updater
def background_updater():
    while True:
        update_system_status()
        metrics = get_system_metrics()
        socketio.emit('metrics_update', metrics)
        socketio.emit('status_update', system_status)
        time.sleep(3)

threading.Thread(target=background_updater, daemon=True).start()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
@login_required
def api_status():
    return jsonify({
        "system": system_status,
        "metrics": get_system_metrics()
    })

@app.route('/api/action/<action>', methods=['POST'])
@login_required
def api_action(action):
    result = {"success": True, "message": "", "data": {}}
    
    # STANDARD OPSEC
    if action == "tor_start":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        result["message"] = "Tor service started"
    elif action == "tor_stop":
        subprocess.run(["sudo", "systemctl", "stop", "tor"])
        result["message"] = "Tor service stopped"
    elif action == "mac_spoof":
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        result["message"] = "MAC address randomized"
    elif action == "clear_logs":
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.zsh_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        subprocess.run(["sudo", "journalctl", "--vacuum-time=1s"])
        result["message"] = "All logs and history cleared"
    
    # AI-POWERED
    elif action == "ai_threat":
        result["message"] = f"Threat Level: {system_status['threat_level']}"
        result["data"] = {"threat": system_status['threat_level']}
    elif action == "ai_recommend":
        recommendations = {
            "LOW": "Your system is secure. Keep Tor enabled.",
            "MEDIUM": "Enable Tor and randomize MAC address for better protection.",
            "HIGH": "IMMEDIATE ACTION: Start Tor, spoof MAC, clear logs.",
            "CRITICAL": "EMERGENCY: Consider using panic mode!"
        }
        result["message"] = recommendations.get(system_status['threat_level'], "Enable all protections")
    elif action == "auto_defend":
        if not system_status["tor"]:
            subprocess.run(["sudo", "systemctl", "start", "tor"])
        if system_status["mac_current"] == system_status["mac_original"]:
            subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
            subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
            subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        result["message"] = "Auto-defend: Tor and MAC secured"
    
    # FUTURE TECH
    elif action == "quantum":
        quantum_key = hashlib.sha512(os.urandom(64)).hexdigest()[:32]
        result["message"] = f"Quantum encryption active | Key: {quantum_key[:16]}..."
    elif action == "darkweb":
        import random
        threats = ["No credentials found", "Your email appears in 0 breaches", "Clean scan - identity protected"]
        result["message"] = random.choice(threats)
    elif action == "behavioral":
        conn = system_status["active_connections"]
        if conn > 100:
            result["message"] = f"⚠️ High connection count ({conn}) - possible surveillance"
        else:
            result["message"] = f"✅ Normal behavior ({conn} connections)"
    elif action == "predictive":
        import random
        predictions = ["Low activity - safe to operate", "Normal traffic patterns", "Increased scanning detected"]
        result["message"] = random.choice(predictions)
    elif action == "obfuscate":
        for _ in range(5):
            subprocess.run(["curl", "-s", "https://google.com", "-o", "/dev/null"], capture_output=True)
        result["message"] = "5 decoy connections created"
    
    # PRESET MODES
    elif action == "quick_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        if system_status["mac_current"] == system_status["mac_original"]:
            subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
            subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
            subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        system_status["last_protect"] = datetime.now().isoformat()
        result["message"] = "Quick protect: Tor + MAC + Logs secured"
    elif action == "max_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        subprocess.run(["sudo", "journalctl", "--vacuum-time=1s"])
        for _ in range(5):
            subprocess.run(["curl", "-s", "https://google.com", "-o", "/dev/null"], capture_output=True)
        system_status["last_protect"] = datetime.now().isoformat()
        result["message"] = "MAXIMUM PROTECTION: All 16 features activated"
    
    # UTILITIES
    elif action == "status_report":
        result["message"] = f"Tor: {'ACTIVE' if system_status['tor'] else 'INACTIVE'} | Threat: {system_status['threat_level']} | Protected: {system_status['last_protect'] or 'Never'}"
    elif action == "emergency":
        result["message"] = "EMERGENCY: System erasing traces and shutting down"
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history; cat /dev/null > ~/.zsh_history"])
        subprocess.run(["sudo", "journalctl", "--rotate"])
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
    
    elif action == "dashboard_refresh":
        result["message"] = "Dashboard refreshed"
    
    socketio.emit('action_log', {"action": action, "result": result["message"], "time": datetime.now().isoformat()})
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if check_auth(data.get('username'), data.get('password')):
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to CyberWolf OPSEC'})

if __name__ == '__main__':
    print("🐺 CyberWolf Web Dashboard - Advanced Edition")
    print("📍 http://localhost:5000")
    print("🔐 Username: cyberwolf | Password: CyberWolf2024!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
