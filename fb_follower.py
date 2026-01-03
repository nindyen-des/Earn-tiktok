import requests
import time
import random
import threading
from urllib.parse import urlparse
import json
import os

class FacebookFollower:
    def __init__(self, proxy_file='proxies.txt'):
        self.base_url = "https://zefame-free.com/api_free.php"
        self.device_id = "fb-follower-bot-v1.0"
        self.proxies = self.load_proxies(proxy_file)
        self.running = False
        self.follow_count = 0
        self.start_time = None
        self.last_order_time = {}
        self.order_cache = {}
        
        self.headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://zefame.com",
            "referer": "https://zefame.com/",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
        
        # Load order cache from file
        self.load_order_cache()
    
    def load_proxies(self, filename):
        proxies = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        proxies.append(line)
            print(f"Loaded {len(proxies)} proxies")
            return proxies
        except:
            print("No proxy file found, running without proxies")
            return []
    
    def load_order_cache(self):
        """Load previously successful orders from cache file"""
        try:
            if os.path.exists('order_cache.json'):
                with open('order_cache.json', 'r') as f:
                    self.order_cache = json.load(f)
                    self.last_order_time = self.order_cache.get('last_order_time', {})
        except:
            self.order_cache = {'last_order_time': {}}
    
    def save_order_cache(self):
        """Save successful orders to cache file"""
        try:
            self.order_cache['last_order_time'] = self.last_order_time
            with open('order_cache.json', 'w') as f:
                json.dump(self.order_cache, f)
        except:
            pass
    
    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def extract_profile_id(self, facebook_url):
        """Extract Facebook profile ID from URL"""
        try:
            parsed = urlparse(facebook_url)
            
            # Handle different Facebook URL formats
            if 'profile.php?id=' in facebook_url:
                query_params = parsed.query
                if 'id=' in query_params:
                    profile_id = query_params.split('id=')[1].split('&')[0]
                    if profile_id.isdigit():
                        return profile_id
            
            # Handle facebook.com/username format
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                # Return the last part of the path
                return path_parts[-1]
            
            return None
        except Exception as e:
            print(f"Error extracting profile ID: {e}")
            return None
    
    def check_service_availability(self, service_id=244):
        """Check if the zefame service is available"""
        params = {
            "action": "check",
            "device": self.device_id,
            "service": service_id,
            "username": "share"
        }
        
        try:
            proxy = self.get_random_proxy()
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            response = requests.get(self.base_url, headers=self.headers, params=params, 
                                  proxies=proxies, timeout=10)
            result = response.json()
            
            print(f"Service check response: {result}")  # DEBUG
            
            if result.get('success') or result.get('status') == 'success':
                allowed = result.get('data', {}).get('allowed') or result.get('available')
                if allowed is True or allowed == "1" or allowed == 1:
                    return True
            
            return False
        except Exception as e:
            print(f"Service check error: {e}")
            return False
    
    def can_send_order(self, profile_id):
        """Check if we can send another order for this profile (24-hour cooldown)"""
        if profile_id not in self.last_order_time:
            return True
        
        last_time = self.last_order_time[profile_id]
        elapsed = time.time() - last_time
        
        # 24 hours cooldown (86400 seconds)
        if elapsed >= 86400:
            return True
        
        hours_left = (86400 - elapsed) / 3600
        print(f"Cooldown active: {hours_left:.1f} hours remaining for profile {profile_id}")
        return False
    
    def send_follow_request(self, facebook_url, service_id=244):
        """Send follow request to zefame API"""
        headers = self.headers.copy()
        headers["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        
        # Extract profile ID for cooldown tracking
        profile_id = self.extract_profile_id(facebook_url) or "unknown"
        
        # Check cooldown
        if not self.can_send_order(profile_id):
            return {
                "success": False, 
                "error": f"24-hour cooldown active for this profile. Please wait before trying again.",
                "cooldown": True
            }
        
        # Prepare request data (EXACTLY like your terminal version)
        data = {
            "action": "order",
            "service": service_id,
            "link": facebook_url,
            "uuid": self.device_id,
            "username": "share"
        }
        
        print(f"Sending follow request data: {data}")  # DEBUG
        
        try:
            proxy = self.get_random_proxy()
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            # Use the SAME URL format as your terminal version
            url = f"{self.base_url}?action=order"
            response = requests.post(url, headers=headers, data=data, 
                                   proxies=proxies, timeout=15)
            
            result = response.json()
            print(f"API Response: {result}")  # DEBUG
            
            if result.get('success'):
                order_id = result.get('data', {}).get('orderId', 'N/A')
                
                # Update cooldown timer
                self.last_order_time[profile_id] = time.time()
                self.save_order_cache()
                
                return {
                    "success": True, 
                    "order_id": order_id,
                    "message": f"Order placed successfully! Order ID: {order_id}"
                }
            else:
                error_msg = result.get('message', result.get('error', 'Unknown error'))
                return {
                    "success": False, 
                    "error": f"API Error: {error_msg}",
                    "cooldown": False
                }
                
        except Exception as e:
            return {
                "success": False, 
                "error": f"Request failed: {str(e)}",
                "cooldown": False
            }
    
    def simulate_follow_requests(self, facebook_url, duration=None, callback=None):
        """Simulate follow requests for testing (when API doesn't work)"""
        if callback:
            callback("info", "API TEST MODE: Simulating follow requests...")
        
        start_time = time.time()
        count = 0
        
        while self.running:
            if duration and (time.time() - start_time) >= duration:
                break
            
            count += 1
            if callback:
                callback("success", f"[SIMULATED] Follow request #{count} sent! Order ID: SIM{count:06d}")
            
            # Wait random time
            time.sleep(random.uniform(5, 15))
            
            # Break early if duration set
            if duration and (time.time() - start_time) >= duration:
                break
        
        if callback:
            callback("info", f"Simulation complete. Total requests: {count}")
        
        return True
    
    def start_following(self, facebook_url, duration=None, callback=None):
        """Main function to start following process"""
        self.running = True
        self.follow_count = 0
        self.start_time = time.time()
        
        if callback:
            callback("info", "🔍 Starting Facebook Follower Bot...")
            callback("info", f"📱 Target URL: {facebook_url}")
        
        # Step 1: Extract profile ID
        profile_id = self.extract_profile_id(facebook_url)
        if profile_id:
            if callback:
                callback("info", f"✅ Profile ID extracted: {profile_id}")
        else:
            if callback:
                callback("warning", "⚠️ Could not extract profile ID, using URL as is")
            profile_id = "url_" + str(hash(facebook_url) % 10000)
        
        # Step 2: Check cooldown
        if not self.can_send_order(profile_id):
            if callback:
                last_time = self.last_order_time.get(profile_id, 0)
                elapsed = time.time() - last_time
                hours_left = (86400 - elapsed) / 3600
                callback("error", f"⏳ 24-hour cooldown active! Please wait {hours_left:.1f} more hours.")
            self.running = False
            return False
        
        # Step 3: Check service availability
        if callback:
            callback("info", "🔌 Checking service availability...")
        
        if not self.check_service_availability():
            if callback:
                callback("warning", "⚠️ Service check failed. Trying direct order anyway...")
        else:
            if callback:
                callback("success", "✅ Service is available!")
        
        # Step 4: Send follow request
        if callback:
            callback("info", "🚀 Sending follow request to API...")
        
        result = self.send_follow_request(facebook_url)
        
        if result["success"]:
            self.follow_count += 1
            if callback:
                callback("success", f"🎉 {result['message']}")
                callback("info", "✅ Follow request successful! The boost will start shortly.")
        else:
            if result.get("cooldown"):
                if callback:
                    callback("error", f"⏳ {result['error']}")
            else:
                if callback:
                    callback("error", f"❌ {result['error']}")
                
                # Try simulation mode if API fails
                if callback:
                    callback("info", "🔄 Switching to simulation mode for testing...")
                return self.simulate_follow_requests(facebook_url, duration, callback)
        
        self.running = False
        
        if callback:
            elapsed = time.time() - self.start_time
            callback("info", f"⏱️ Process completed in {elapsed:.1f} seconds")
            callback("info", f"📊 Total successful requests: {self.follow_count}")
        
        return True
    
    def stop(self):
        self.running = False
    
    def get_stats(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            return {
                "running": self.running,
                "follow_count": self.follow_count,
                "elapsed_time": int(elapsed),
                "cooldown_profiles": len(self.last_order_time)
            }
        return {"running": self.running, "follow_count": self.follow_count}
