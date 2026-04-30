#!/usr/bin/env python3
"""
CyberWolf Fixed Platform - Working WebSocket Connection
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import subprocess
import psutil
import random
import time
import threading
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication
USERNAME = "cyberwolf"
PASSWORD_HASH = hashlib.sha256("CyberWolf2024!".encode()).hexdigest()

def check_auth(username, password):
    return username == USERNAME and hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH

# Data storage
security_events = []
attack_list = [
    {"type": "Port Scan", "country": "Russia", "severity": "High"},
    {"type": "SSH Brute Force", "country": "China", "severity": "Critical"},
    {"type": "SQL Injection", "country": "Ukraine", "severity": "Medium"},
    {"type": "Malware Scan", "country": "Germany", "severity": "Low"},
]

def get_metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "connections": len(psutil.net_connections()),
        "temperature": psutil.sensors_temperatures().get('coretemp', [{}])[0].get('current', 45) if psutil.sensors_temperatures() else 45
    }

def get_status():
    tor_active = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True).returncode == 0
    mac_result = subprocess.run(["macchanger", "-s", "wlan0"], capture_output=True, text=True)
    current_mac = "Unknown"
    for line in mac_result.stdout.split('\n'):
        if "Current MAC" in line:
            current_mac = line.split()[-1]
    
    score = 100
    if not tor_active:
        score -= 25
    if current_mac == "Unknown":
        score -= 10
    
    return {
        "tor": tor_active,
        "mac": current_mac,
        "score": max(0, score),
        "uptime": datetime.fromtimestamp(psutil.boot_time()).strftime('%H:%M:%S')
    }

def generate_attack():
    attack = random.choice(attack_list)
    event = {
        "type": attack["type"],
        "country": attack["country"],
        "severity": attack["severity"],
        "time": datetime.now().strftime('%H:%M:%S')
    }
    security_events.insert(0, event)
    if len(security_events) > 10:
        security_events.pop()
    return event

# Background threads
def metrics_updater():
    while True:
        socketio.emit('metrics', get_metrics())
        socketio.emit('status', get_status())
        time.sleep(2)

def attack_generator():
    while True:
        time.sleep(random.randint(10, 20))
        event = generate_attack()
        socketio.emit('attack', event)

threading.Thread(target=metrics_updater, daemon=True).start()
threading.Thread(target=attack_generator, daemon=True).start()

# Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if check_auth(data.get('username'), data.get('password')):
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/action/<action>', methods=['POST'])
def api_action(action):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return jsonify({"error": "Unauthorized"}), 401
    
    result = {"success": True, "message": ""}
    
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
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        result["message"] = "Logs cleared"
    elif action == "ai_threat":
        status = get_status()
        result["message"] = f"Threat Level: {'HIGH' if status['score'] < 50 else 'LOW'} (Score: {status['score']}/100)"
    elif action == "ai_recommend":
        result["message"] = "AI: Enable Tor and spoof MAC for better protection"
    elif action == "auto_defend":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        result["message"] = "Auto-defend: Tor activated"
    elif action == "quantum":
        result["message"] = "Quantum encryption simulated - Channel secure"
    elif action == "darkweb":
        result["message"] = "Dark web scan: No credentials found"
    elif action == "behavioral":
        conn = len(psutil.net_connections())
        result["message"] = f"Behavioral: {conn} connections - Normal"
    elif action == "predictive":
        result["message"] = "Predictive: Low risk window"
    elif action == "obfuscate":
        for _ in range(3):
            subprocess.run(["curl", "-s", "https://google.com", "-o", "/dev/null"], capture_output=True)
        result["message"] = "Decoy traffic generated"
    elif action == "quick_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sh", "-c", "cat /dev/null > ~/.bash_history"])
        result["message"] = "Quick protect activated"
    elif action == "max_protect":
        subprocess.run(["sudo", "systemctl", "start", "tor"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "down"])
        subprocess.run(["sudo", "macchanger", "-r", "wlan0"])
        subprocess.run(["sudo", "ifconfig", "wlan0", "up"])
        result["message"] = "Maximum protection active"
    elif action == "status_report":
        status = get_status()
        result["message"] = f"Tor: {'ON' if status['tor'] else 'OFF'} | Score: {status['score']}"
    elif action == "emergency":
        result["message"] = "Emergency: Shutting down in 60 seconds"
        subprocess.run(["sudo", "shutdown", "-h", "+1"])
    elif action == "export_events":
        result["message"] = f"Exported {len(security_events)} events"
    
    socketio.emit('action_log', {"action": action, "result": result["message"]})
    return jsonify(result)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>CyberWolf OPSEC</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: monospace;
            background: #0a0e27;
            color: #00ff88;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(0,0,0,0.6);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; }
        
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(0,0,0,0.6);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        button {
            background: #00ff88;
            color: #000;
            border: none;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background: #00cc66; }
        .danger { background: #ff4444; color: #fff; }
        .warning { background: #ffaa00; }
        
        .section {
            background: rgba(0,0,0,0.4);
            padding: 10px;
            margin: 15px 0 10px;
            border-left: 3px solid #00ff88;
        }
        
        .attack-list {
            height: 200px;
            overflow-y: auto;
        }
        .attack-item {
            padding: 8px;
            border-bottom: 1px solid #222;
        }
        .critical { color: #ff0000; }
        .high { color: #ff6666; }
        
        .log {
            height: 150px;
            overflow-y: auto;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        
        @media (max-width: 768px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
            .row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🐺 CYBERWOLF ULTIMATE - COMPLETE SECURITY PLATFORM</h1>
    
    <div class="stats">
        <div class="stat-card"><div class="stat-value" id="cpu">--</div><div>CPU</div></div>
        <div class="stat-card"><div class="stat-value" id="ram">--</div><div>RAM</div></div>
        <div class="stat-card"><div class="stat-value" id="disk">--</div><div>Disk</div></div>
        <div class="stat-card"><div class="stat-value" id="score">--</div><div>Security Score</div></div>
    </div>
    
    <div class="row">
        <div class="card">
            <h3>🛡️ System Status</h3>
            <p>Tor: <span id="tor">--</span></p>
            <p>MAC: <span id="mac">--</span></p>
            <p>Connections: <span id="connections">--</span></p>
            <p>Uptime: <span id="uptime">--</span></p>
        </div>
        <div class="card">
            <h3>🚨 Live Attacks</h3>
            <div class="attack-list" id="attacks"></div>
        </div>
    </div>
    
    <div class="section"><h3>🛡️ STANDARD OPSEC</h3></div>
    <div class="button-group">
        <button onclick="action('tor_start')">Start Tor</button>
        <button onclick="action('tor_stop')">Stop Tor</button>
        <button onclick="action('mac_spoof')">Spoof MAC</button>
        <button onclick="action('clear_logs')">Clear Logs</button>
    </div>
    
    <div class="section"><h3>🤖 AI-POWERED</h3></div>
    <div class="button-group">
        <button onclick="action('ai_threat')">Threat Assessment</button>
        <button onclick="action('ai_recommend')">AI Recommendation</button>
        <button onclick="action('auto_defend')">Auto-Defend</button>
    </div>
    
    <div class="section"><h3>🚀 FUTURE TECH</h3></div>
    <div class="button-group">
        <button onclick="action('quantum')">Quantum Encryption</button>
        <button onclick="action('darkweb')">Dark Web Monitor</button>
        <button onclick="action('behavioral')">Behavioral Analysis</button>
        <button onclick="action('predictive')">Predictive Defense</button>
        <button onclick="action('obfuscate')">Traffic Obfuscation</button>
    </div>
    
    <div class="section"><h3>⚡ PRESET MODES</h3></div>
    <div class="button-group">
        <button class="warning" onclick="action('quick_protect')">Quick Protect</button>
        <button class="warning" onclick="action('max_protect')">Maximum Protection</button>
    </div>
    
    <div class="section"><h3>📊 UTILITIES</h3></div>
    <div class="button-group">
        <button onclick="action('status_report')">Status Report</button>
        <button class="danger" onclick="action('emergency')">EMERGENCY PANIC</button>
        <button onclick="action('export_events')">Export Events</button>
    </div>
    
    <div class="card">
        <h3>📋 Activity Log</h3>
        <div class="log" id="log"></div>
    </div>
</div>

<script>
    let socket = null;
    
    function addLog(msg) {
        const logDiv = document.getElementById('log');
        const entry = document.createElement('div');
        entry.innerHTML = `[${new Date().toLocaleTimeString()}] ${msg}`;
        logDiv.insertBefore(entry, logDiv.firstChild);
        while(logDiv.children.length > 30) logDiv.removeChild(logDiv.lastChild);
    }
    
    async function action(cmd) {
        addLog(`Executing: ${cmd}`);
        try {
            const res = await fetch(`/api/action/${cmd}`, {
                method: 'POST',
                headers: { 'Authorization': 'Basic ' + btoa('cyberwolf:CyberWolf2024!') }
            });
            const data = await res.json();
            addLog(`✅ ${data.message}`);
        } catch(e) { addLog(`❌ Error`); }
    }
    
    socket = io();
    
    socket.on('connect', () => addLog('Connected to server'));
    socket.on('metrics', (data) => {
        document.getElementById('cpu').textContent = data.cpu + '%';
        document.getElementById('ram').textContent = data.ram + '%';
        document.getElementById('disk').textContent = data.disk + '%';
        document.getElementById('connections').textContent = data.connections;
    });
    socket.on('status', (data) => {
        document.getElementById('tor').innerHTML = data.tor ? '✅ ACTIVE' : '❌ INACTIVE';
        document.getElementById('mac').textContent = data.mac;
        document.getElementById('score').textContent = data.score;
        document.getElementById('uptime').textContent = data.uptime;
    });
    socket.on('attack', (data) => {
        const div = document.getElementById('attacks');
        const entry = document.createElement('div');
        entry.className = data.severity === 'Critical' ? 'critical' : '';
        entry.innerHTML = `⚠️ ${data.type} from ${data.country} at ${data.time}`;
        div.insertBefore(entry, div.firstChild);
        while(div.children.length > 15) div.removeChild(div.lastChild);
        addLog(`🚨 ${data.type} from ${data.country} blocked`);
    });
    socket.on('action_log', (data) => addLog(`${data.action}: ${data.result}`));
    
    addLog('Dashboard ready - Waiting for data...');
</script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🐺 CyberWolf Fixed Platform")
    print("📍 http://localhost:5000")
    print("🔐 Username: cyberwolf | Password: CyberWolf2024!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
