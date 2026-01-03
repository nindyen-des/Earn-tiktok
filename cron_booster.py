import requests
import time
import random
import json
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

class FacebookBooster:
    def __init__(self, proxy_file='proxies.txt'):
        self.base_url = "https://zefame-free.com/api_free.php"
        self.proxies = self.load_proxies(proxy_file)
        self.proxy_index = 0
        self.boost_count = 0
        self.session = requests.Session()
        
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
        
        # Load stats
        self.stats_file = 'boost_stats.json'
        self.stats = self.load_stats()
    
    def load_proxies(self, filename):
        """Load proxies from file"""
        proxies = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        # Handle different proxy formats
                        if line.count(':') == 3:
                            # ip:port:user:pass format
                            ip, port, user, password = line.split(':')
                            proxy = f"http://{user}:{password}@{ip}:{port}"
                        elif line.count(':') == 2:
                            # ip:port:user format (no password)
                            ip, port, user = line.split(':')
                            proxy = f"http://{user}@{ip}:{port}"
                        else:
                            # ip:port format
                            proxy = f"http://{line}"
                        
                        proxies.append(proxy)
            
            print(f"✅ Loaded {len(proxies)} proxies")
            return proxies
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            return []
    
    def load_stats(self):
        """Load boost statistics"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
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
    
    def save_stats(self):
        """Save boost statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except:
            pass
    
    def get_next_proxy(self):
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def check_service_availability(self):
        """Check if zefame service is available"""
        params = {
            "action": "check",
            "device": "fb-booster-cron",
            "service": 244,  # Facebook service ID
            "username": "share"
        }
        
        try:
            proxies = self.get_next_proxy()
            response = self.session.get(self.base_url, headers=self.headers, 
                                       params=params, proxies=proxies, timeout=10)
            result = response.json()
            
            if result.get('success') or result.get('status') == 'success':
                allowed = result.get('data', {}).get('allowed') or result.get('available')
                if allowed is True or allowed == "1" or allowed == 1:
                    return True
            
            return False
        except Exception as e:
            print(f"⚠️ Service check error (using proxy): {e}")
            return False
    
    def send_boost_request(self, facebook_url):
        """Send boost request using proxy rotation"""
        headers = self.headers.copy()
        headers["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        
        data = {
            "action": "order",
            "service": 244,  # Facebook service ID
            "link": facebook_url,
            "uuid": f"fb-booster-cron-{int(time.time())}",
            "username": "share"
        }
        
        try:
            proxies = self.get_next_proxy()
            
            print(f"🔄 Using proxy: {proxies['http'] if proxies else 'No proxy'}")
            
            response = self.session.post(f"{self.base_url}?action=order",
                                       headers=headers, data=data,
                                       proxies=proxies, timeout=15)
            
            result = response.json()
            print(f"📡 API Response: {result}")
            
            # Update stats
            self.stats["total_boosts"] += 1
            boost_record = {
                "timestamp": datetime.now().isoformat(),
                "proxy_used": proxies['http'] if proxies else None,
                "success": False,
                "order_id": None,
                "error": None
            }
            
            if result.get('success'):
                order_id = result.get('data', {}).get('orderId', 'N/A')
                self.stats["successful_boosts"] += 1
                self.stats["last_boost"] = datetime.now().isoformat()
                boost_record.update({
                    "success": True,
                    "order_id": order_id
                })
                
                print(f"✅ Boost successful! Order ID: {order_id}")
                return {"success": True, "order_id": order_id}
            else:
                error_msg = result.get('message', result.get('error', 'Unknown error'))
                self.stats["failed_boosts"] += 1
                boost_record["error"] = error_msg
                
                print(f"❌ Boost failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            finally:
                self.stats["boost_history"].append(boost_record)
                # Keep only last 100 records
                if len(self.stats["boost_history"]) > 100:
                    self.stats["boost_history"] = self.stats["boost_history"][-100:]
                self.save_stats()
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return {"success": False, "error": str(e)}
    
    def run_single_boost(self, facebook_url):
        """Run a single boost cycle"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting Facebook Boost Cycle")
        print(f"{'='*60}")
        print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Target: {facebook_url}")
        print(f"🔄 Proxy rotation: {len(self.proxies)} proxies available")
        
        # Check service
        print("🔍 Checking service availability...")
        if not self.check_service_availability():
            print("⚠️ Service check failed, trying anyway...")
        
        # Send boost request
        print("🚀 Sending boost request...")
        result = self.send_boost_request(facebook_url)
        
        print(f"\n📊 Stats: Total={self.stats['total_boosts']}, "
              f"Success={self.stats['successful_boosts']}, "
              f"Failed={self.stats['failed_boosts']}")
        
        return result
    
    def continuous_boost(self, facebook_url, interval_seconds=30):
        """Continuous boosting with interval"""
        print(f"\n{'='*60}")
        print(f"🔄 STARTING CONTINUOUS BOOSTING")
        print(f"{'='*60}")
        print(f"🔗 Target URL: {facebook_url}")
        print(f"⏰ Interval: {interval_seconds} seconds")
        print(f"🔄 Proxy rotation: {len(self.proxies)} proxies")
        print(f"{'='*60}\n")
        
        cycle = 0
        try:
            while True:
                cycle += 1
                print(f"\n📦 Boost Cycle #{cycle}")
                print(f"📅 {datetime.now().strftime('%H:%M:%S')}")
                
                result = self.run_single_boost(facebook_url)
                
                print(f"⏳ Waiting {interval_seconds} seconds for next boost...")
                
                # Countdown timer
                for i in range(interval_seconds, 0, -1):
                    if i % 10 == 0 or i <= 5:
                        sys.stdout.write(f"\r⏰ Next boost in {i:3d} seconds...")
                        sys.stdout.flush()
                    time.sleep(1)
                
                print("\r" + " " * 50 + "\r", end="")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Continuous boosting stopped by user")
        except Exception as e:
            print(f"\n❌ Error in continuous boost: {e}")

def main():
    """Main function"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║       FACEBOOK BOOSTER - CRON EDITION        ║
    ║      Continuous Boosting with Proxy Rot      ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # Configuration
    FACEBOOK_URL = "https://www.facebook.com/profile.php?id=61577360791665"
    INTERVAL_SECONDS = 30  # Same as image (30 seconds)
    
    # Initialize booster
    booster = FacebookBooster('proxies.txt')
    
    if not booster.proxies:
        print("❌ No proxies found in proxies.txt!")
        print("Please add proxies in format: ip:port or ip:port:user:pass")
        return
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--single":
            # Single boost mode (for CRON)
            booster.run_single_boost(FACEBOOK_URL)
        elif sys.argv[1] == "--continuous":
            # Continuous mode
            booster.continuous_boost(FACEBOOK_URL, INTERVAL_SECONDS)
        elif sys.argv[1].startswith("http"):
            # Custom URL
            booster.run_single_boost(sys.argv[1])
        else:
            print(f"Usage: python {sys.argv[0]} [--single|--continuous|URL]")
    else:
        # Interactive mode
        print("\nSelect mode:")
        print("1. Single Boost (for CRON)")
        print("2. Continuous Boost (auto every 30s)")
        print("3. Custom URL")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            booster.run_single_boost(FACEBOOK_URL)
        elif choice == "2":
            booster.continuous_boost(FACEBOOK_URL, INTERVAL_SECONDS)
        elif choice == "3":
            url = input("Enter Facebook URL: ").strip()
            if url:
                booster.run_single_boost(url)
            else:
                print("❌ No URL provided")
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
