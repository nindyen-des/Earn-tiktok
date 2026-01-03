from flask import Flask, render_template, request, jsonify, Response
from fb_follower import FacebookFollower
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)
follower_bot = FacebookFollower('proxies.txt')
current_thread = None
status_callbacks = []
active_connections = {}

def status_callback(status_type, message):
    """Callback function to send status updates to all clients"""
    timestamp = datetime.now().strftime("%I:%M:%S %p")
    formatted_message = f"[{timestamp}] {message}"
    
    print(f"Status: {status_type} - {formatted_message}")
    
    # Send to all connected clients
    for client_id, callback in list(status_callbacks):
        try:
            callback(status_type, formatted_message)
        except:
            # Remove dead connections
            status_callbacks.remove((client_id, callback))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_following():
    global current_thread
    
    facebook_url = request.form.get('facebook_url')
    duration = request.form.get('duration', '0')
    
    if not facebook_url or 'facebook.com' not in facebook_url:
        return jsonify({
            "success": False, 
            "message": "❌ Invalid Facebook URL! Please enter a valid Facebook profile URL."
        })
    
    # Check if already running
    if current_thread and current_thread.is_alive():
        return jsonify({
            "success": False, 
            "message": "⚠️ Another process is already running!"
        })
    
    # Parse duration
    try:
        duration = int(duration) if duration and duration != '0' else None
    except:
        duration = None
    
    def run_follower():
        try:
            follower_bot.start_following(facebook_url, duration, status_callback)
        except Exception as e:
            status_callback("error", f"❌ Bot error: {str(e)}")
        finally:
            status_callback("info", "🛑 Process stopped")
    
    # Start the follower thread
    current_thread = threading.Thread(target=run_follower)
    current_thread.daemon = True
    current_thread.start()
    
    if duration:
        return jsonify({
            "success": True, 
            "message": f"🚀 Started following process for {duration} seconds!"
        })
    else:
        return jsonify({
            "success": True, 
            "message": "🚀 Started Facebook boost process!"
        })

@app.route('/status', methods=['GET'])
def get_status():
    stats = follower_bot.get_stats()
    
    # Calculate cooldown info
    cooldown_info = []
    for profile_id, last_time in follower_bot.last_order_time.items():
        elapsed = time.time() - last_time
        if elapsed < 86400:  # Still in cooldown
            hours_left = (86400 - elapsed) / 3600
            cooldown_info.append({
                "profile": profile_id[:20] + "..." if len(profile_id) > 20 else profile_id,
                "hours_left": round(hours_left, 1)
            })
    
    stats["cooldown_info"] = cooldown_info
    return jsonify(stats)

@app.route('/stop', methods=['POST'])
def stop_following():
    follower_bot.stop()
    
    if current_thread and current_thread.is_alive():
        current_thread.join(timeout=5)
    
    return jsonify({
        "success": True, 
        "message": "🛑 Process stopped successfully!",
        "follow_count": follower_bot.follow_count
    })

@app.route('/clear-cooldown', methods=['POST'])
def clear_cooldown():
    """Clear the cooldown cache (for testing)"""
    try:
        follower_bot.last_order_time = {}
        follower_bot.save_order_cache()
        return jsonify({
            "success": True, 
            "message": "✅ Cooldown cache cleared!"
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"❌ Error clearing cache: {str(e)}"
        })

@app.route('/events')
def events():
    """Server-Sent Events endpoint for real-time updates"""
    def generate():
        client_id = str(time.time())
        
        def event_callback(status_type, message):
            try:
                data = {
                    "type": status_type,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(data)}\n\n"
            except:
                pass
        
        # Add this callback to the list
        callback = event_callback
        status_callbacks.append((client_id, callback))
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'info', 'message': '✅ Connected to server', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Keep connection alive with heartbeats
            while True:
                yield f"data: {json.dumps({'type': 'ping', 'message': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                time.sleep(30)
        finally:
            # Clean up on disconnect
            for i, (cid, cb) in enumerate(status_callbacks):
                if cid == client_id and cb == callback:
                    status_callbacks.pop(i)
                    break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/test-api', methods=['GET'])
def test_api():
    """Test the zefame API directly"""
    try:
        import requests
        
        # Test the check endpoint
        test_url = "https://zefame-free.com/api_free.php"
        params = {
            "action": "check",
            "device": "test-device",
            "service": 244,
            "username": "share"
        }
        
        response = requests.get(test_url, params=params, timeout=10)
        result = response.json()
        
        return jsonify({
            "success": True,
            "api_status": "reachable",
            "response": result,
            "service_available": result.get('success', False)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "api_status": "unreachable",
            "error": str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Facebook Follower Bot Server...")
    print("🌐 Web Interface: http://localhost:5000")
    print("📱 Make sure you have valid proxies in proxies.txt")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
