from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import os
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
CRON_SCRIPT = "cron_booster.py"
STATS_FILE = "boost_stats.json"
CRON_PID_FILE = "cron_booster.pid"

class CronManager:
    def __init__(self):
        self.is_running = False
        self.process = None
        self.stats = self.load_stats()
    
    def load_stats(self):
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "total_boosts": 0,
            "successful_boosts": 0,
            "failed_boosts": 0,
            "last_boost": None,
            "boost_history": []
        }
    
    def start_cron(self, facebook_url, interval=30):
        """Start the continuous booster"""
        if self.is_running:
            return False, "Already running"
        
        def run_booster():
            try:
                # Run the booster script
                cmd = ["python", CRON_SCRIPT, "--continuous"]
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Save PID
                with open(CRON_PID_FILE, 'w') as f:
                    f.write(str(self.process.pid))
                
                self.is_running = True
                
                # Read output
                for line in iter(self.process.stdout.readline, ''):
                    print(f"[BOOSTER] {line.strip()}")
                
                self.process.wait()
                
            except Exception as e:
                print(f"Booster error: {e}")
            finally:
                self.is_running = False
                if os.path.exists(CRON_PID_FILE):
                    os.remove(CRON_PID_FILE)
        
        # Start in background thread
        thread = threading.Thread(target=run_booster, daemon=True)
        thread.start()
        
        return True, "Booster started"
    
    def stop_cron(self):
        """Stop the continuous booster"""
        if not self.is_running:
            return False, "Not running"
        
        try:
            # Try to kill by PID
            if os.path.exists(CRON_PID_FILE):
                with open(CRON_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                
                import signal
                os.kill(pid, signal.SIGTERM)
            
            # Kill process if still exists
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
            
            self.is_running = False
            
            if os.path.exists(CRON_PID_FILE):
                os.remove(CRON_PID_FILE)
            
            return True, "Booster stopped"
            
        except Exception as e:
            return False, f"Error stopping: {str(e)}"
    
    def run_single_boost(self, facebook_url):
        """Run a single boost"""
        try:
            cmd = ["python", CRON_SCRIPT, facebook_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Reload stats
            self.stats = self.load_stats()
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self):
        return {
            "running": self.is_running,
            "stats": self.stats,
            "last_boost": self.stats.get("last_boost"),
            "total_boosts": self.stats.get("total_boosts", 0),
            "success_rate": (self.stats.get("successful_boosts", 0) / 
                           max(self.stats.get("total_boosts", 1), 1)) * 100
        }

# Initialize cron manager
cron_manager = CronManager()

@app.route('/')
def index():
    return render_template('cron_dashboard.html')

@app.route('/api/start', methods=['POST'])
def start_booster():
    data = request.json
    facebook_url = data.get('facebook_url', '').strip()
    interval = int(data.get('interval', 30))
    
    if not facebook_url or 'facebook.com' not in facebook_url:
        return jsonify({"success": False, "message": "Invalid Facebook URL"})
    
    success, message = cron_manager.start_cron(facebook_url, interval)
    
    return jsonify({
        "success": success,
        "message": message,
        "running": cron_manager.is_running
    })

@app.route('/api/stop', methods=['POST'])
def stop_booster():
    success, message = cron_manager.stop_cron()
    
    return jsonify({
        "success": success,
        "message": message,
        "running": cron_manager.is_running
    })

@app.route('/api/boost', methods=['POST'])
def single_boost():
    data = request.json
    facebook_url = data.get('facebook_url', '').strip()
    
    if not facebook_url or 'facebook.com' not in facebook_url:
        return jsonify({"success": False, "message": "Invalid Facebook URL"})
    
    result = cron_manager.run_single_boost(facebook_url)
    
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    status = cron_manager.get_status()
    
    # Format boost history for display
    boost_history = []
    for boost in status['stats'].get('boost_history', [])[-10:]:  # Last 10
        try:
            dt = datetime.fromisoformat(boost['timestamp'].replace('Z', '+00:00'))
            time_ago = get_time_ago(dt)
            
            boost_history.append({
                'time': dt.strftime('%H:%M:%S'),
                'time_ago': time_ago,
                'success': boost.get('success', False),
                'order_id': boost.get('order_id', 'N/A'),
                'proxy': boost.get('proxy_used', 'N/A')
            })
        except:
            pass
    
    return jsonify({
        "running": status['running'],
        "total_boosts": status['total_boosts'],
        "last_boost": status['last_boost'],
        "success_rate": round(status['success_rate'], 1),
        "boost_history": boost_history,
        "stats": status['stats']
    })

@app.route('/api/test-proxies', methods=['GET'])
def test_proxies():
    """Test if proxies are working"""
    try:
        import requests
        
        # Test with a simple request
        test_url = "http://httpbin.org/ip"
        
        # Load proxies
        proxies = []
        if os.path.exists('proxies.txt'):
            with open('proxies.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        proxies.append(line)
        
        results = []
        for i, proxy in enumerate(proxies[:5]):  # Test first 5
            try:
                # Format proxy
                if proxy.count(':') == 3:
                    ip, port, user, password = proxy.split(':')
                    proxy_url = f"http://{user}:{password}@{ip}:{port}"
                elif proxy.count(':') == 2:
                    ip, port, user = proxy.split(':')
                    proxy_url = f"http://{user}@{ip}:{port}"
                else:
                    proxy_url = f"http://{proxy}"
                
                response = requests.get(test_url, 
                                      proxies={'http': proxy_url, 'https': proxy_url},
                                      timeout=10)
                
                results.append({
                    "proxy": proxy,
                    "status": "✅ Working",
                    "ip": response.json().get('origin', 'Unknown')
                })
                
            except Exception as e:
                results.append({
                    "proxy": proxy,
                    "status": f"❌ Failed: {str(e)[:50]}",
                    "ip": "N/A"
                })
        
        return jsonify({
            "success": True,
            "total_proxies": len(proxies),
            "tested": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

def get_time_ago(dt):
    """Convert datetime to 'X ago' format"""
    now = datetime.now(dt.tzinfo if dt.tzinfo else None)
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds/60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h ago"
    else:
        return f"{int(seconds/86400)}d ago"

if __name__ == '__main__':
    print("🚀 Starting Facebook Booster Dashboard...")
    print("🌐 Open: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
