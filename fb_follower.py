import requests
import time
import random
import threading
from urllib.parse import urlparse

class FacebookFollower:
    def __init__(self, proxy_file='proxies.txt'):
        self.base_url = "https://zefame-free.com/api_free.php"
        self.device_id = "fb-follower-bot-v1.0"
        self.proxies = self.load_proxies(proxy_file)
        self.running = False
        
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
    
    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def extract_profile_id(self, facebook_url):
        try:
            parsed = urlparse(facebook_url)
            query_params = parsed.query
            
            if 'id=' in query_params:
                profile_id = query_params.split('id=')[1].split('&')[0]
                return profile_id
            elif '/profile.php' in parsed.path and 'id=' in query_params:
                profile_id = query_params.split('id=')[1].split('&')[0]
                return profile_id
            elif '/profile.php' in parsed.path:
                path_parts = parsed.path.split('/')
                for i, part in enumerate(path_parts):
                    if part == 'profile.php' and i + 1 < len(path_parts):
                        return path_parts[i + 1]
            
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                return path_parts[-1]
            
            return None
        except Exception as e:
            print(f"Error extracting profile ID: {e}")
            return None
    
    def check_service_availability(self, service_id=244):
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
            
            if result.get('success') or result.get('status') == 'success':
                allowed = result.get('data', {}).get('allowed') or result.get('available')
                return bool(allowed)
            
            return False
        except Exception as e:
            print(f"Service check error: {e}")
            return False
    
    def send_follow_request(self, facebook_url, service_id=244):
        headers = self.headers.copy()
        headers["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        
        data = {
            "action": "order",
            "service": service_id,
            "link": facebook_url,
            "uuid": self.device_id,
            "username": "share"
        }
        
        try:
            proxy = self.get_random_proxy()
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            
            response = requests.post(f"{self.base_url}?action=order", 
                                   headers=headers, data=data, 
                                   proxies=proxies, timeout=15)
            result = response.json()
            
            if result.get('success'):
                order_id = result.get('data', {}).get('orderId', 'N/A')
                return {"success": True, "order_id": order_id}
            else:
                return {"success": False, "error": result.get('message', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def start_following(self, facebook_url, duration=30, callback=None):
        self.running = True
        
        if not self.check_service_availability():
            if callback:
                callback("error", "Service is not available at the moment")
            return False
        
        profile_id = self.extract_profile_id(facebook_url)
        if not profile_id:
            if callback:
                callback("error", "Could not extract Facebook profile ID")
            return False
        
        if callback:
            callback("info", f"Target Profile ID: {profile_id}")
            callback("info", f"Starting follow process for {duration} seconds...")
        
        start_time = time.time()
        follow_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                result = self.send_follow_request(facebook_url)
                
                if result["success"]:
                    follow_count += 1
                    if callback:
                        callback("success", f"Follow request #{follow_count} sent successfully! Order ID: {result['order_id']}")
                else:
                    if callback:
                        callback("error", f"Follow attempt failed: {result['error']}")
                
                wait_time = random.uniform(25, 35)
                time.sleep(wait_time)
                
            except Exception as e:
                if callback:
                    callback("error", f"Error: {str(e)}")
                time.sleep(10)
        
        self.running = False
        
        if callback:
            callback("info", f"Process completed. Total follow requests sent: {follow_count}")
        
        return True
    
    def stop(self):
        self.running = False
