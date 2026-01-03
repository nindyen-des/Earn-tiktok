from flask import Flask, render_template, request, jsonify
from fb_follower import FacebookFollower
import threading
import time

app = Flask(__name__)
follower_bot = FacebookFollower('proxies.txt')
current_thread = None
status_callbacks = []

def status_callback(status_type, message):
    for callback in status_callbacks:
        callback(status_type, message)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_following():
    global current_thread
    
    facebook_url = request.form.get('facebook_url')
    duration = int(request.form.get('duration', 30))
    
    if not facebook_url or 'facebook.com' not in facebook_url:
        return jsonify({"success": False, "message": "Invalid Facebook URL"})
    
    if current_thread and current_thread.is_alive():
        return jsonify({"success": False, "message": "Another process is already running"})
    
    def run_follower():
        follower_bot.start_following(facebook_url, duration, status_callback)
    
    current_thread = threading.Thread(target=run_follower)
    current_thread.start()
    
    return jsonify({
        "success": True, 
        "message": f"Started following process for {duration} seconds"
    })

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"running": follower_bot.running})

@app.route('/stop', methods=['POST'])
def stop_following():
    follower_bot.stop()
    return jsonify({"success": True, "message": "Process stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
