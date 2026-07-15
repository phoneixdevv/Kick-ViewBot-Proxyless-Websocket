import sys
import time
import random
import datetime
import threading
import asyncio
import websockets
import json
import os
from threading import Thread, Semaphore
import tls_client

CLIENT_TOKEN = "e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823"

channel = ""
channel_id = None
stream_id = None
max_threads = 0
threads = []
thread_limit = None
active = 0
stop = False
start_time = None
lock = threading.Lock()
connections = 0
attempts = 0
pings = 0
heartbeats = 0
viewers = 0
last_check = 0
successful_handshakes = 0
failed_handshakes = 0
connection_errors = 0

token_cache = []
cache_lock = threading.Lock()
performance_stats = {
    'connections_per_second': 0,
    'last_connection_count': 0,
    'last_calc_time': time.time(),
    'total_viewer_increase': 0
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

def clean_channel_name(name):
    if "kick.com/" in name:
        parts = name.split("kick.com/")
        channel = parts[1].split("/")[0].split("?")[0]
        return channel.lower()
    return name.lower()

def get_channel_info(name):
    global channel_id, stream_id
    try:
        s = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        s.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://kick.com/{name}',
            'Origin': 'https://kick.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
        response = s.get(f'https://kick.com/api/v2/channels/{name}')
        if response.status_code == 200:
            data = response.json()
            channel_id = data.get("id")
            if 'livestream' in data and data['livestream']:
                stream_id = data['livestream'].get('id')
            return channel_id
        return None
    except:
        return None

def get_token():
    try:
        session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }
        
        try:
            session.get("https://kick.com")
        except:
            pass
        
        session.headers = {
            'Accept': 'application/json, text/plain, */*',
            'X-CLIENT-TOKEN': CLIENT_TOKEN,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://kick.com',
            'Referer': 'https://kick.com/',
        }
        
        endpoints = [
            'https://kick.com/api/websocket/token',
            'https://websockets.kick.com/viewer/v1/token',
        ]
        
        for endpoint in endpoints:
            try:
                response = session.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("token") or data.get("data", {}).get("token")
                    if token:
                        return token
            except:
                continue
                
        return None
    except:
        return None

def prefetch_tokens():
    global stop
    while not stop:
        try:
            with cache_lock:
                if len(token_cache) < 300:
                    token = get_token()
                    if token:
                        token_cache.append(token)
            time.sleep(0.02)
        except:
            time.sleep(0.05)

def get_viewer_count():
    global viewers, last_check
    if not stream_id:
        return 0
    
    try:
        s = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        s.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://kick.com/{channel}',
            'Origin': 'https://kick.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
        response = s.get(f'https://kick.com/api/v2/channels/{channel}')
        if response.status_code == 200:
            data = response.json()
            if 'livestream' in data and data['livestream']:
                viewers = data['livestream'].get('viewer_count', 0)
            last_check = time.time()
            return viewers
        return viewers
    except:
        return viewers

def show_stats():
    global stop, start_time, connections, attempts, pings, heartbeats, viewers, last_check
    global successful_handshakes, failed_handshakes, connection_errors
    
    initial_viewers = viewers
    last_lines = 0
    
    while not stop:
        try:
            now = time.time()
            
            if now - performance_stats['last_calc_time'] >= 1:
                current_conns = connections
                elapsed = now - performance_stats['last_calc_time']
                performance_stats['connections_per_second'] = int((current_conns - performance_stats['last_connection_count']) / elapsed)
                performance_stats['last_connection_count'] = current_conns
                performance_stats['last_calc_time'] = now
                performance_stats['total_viewer_increase'] = viewers - initial_viewers
            
            if now - last_check >= 3:
                get_viewer_count()
            
            with lock:
                if start_time:
                    elapsed = datetime.datetime.now() - start_time
                    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    duration = "00:00:00"
                
                ws_count = connections
                active_count = active
                ping_count = pings
                handshake_success = successful_handshakes
                handshake_failed = failed_handshakes
                viewer_display = viewers
                error_count = connection_errors
            
            progress_percent = (ws_count / max_threads * 100) if max_threads > 0 else 0
            
            for _ in range(last_lines):
                print("\033[1A\033[2K", end="")
            
            lines = []
            
            lines.append(f"{Colors.CYAN}🔥 kick viewer boost - phoneix  🔥{Colors.RESET}")
            lines.append(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            progress_color = Colors.GREEN if progress_percent > 75 else Colors.YELLOW if progress_percent > 40 else Colors.RED
            lines.append(f"{Colors.WHITE}TARGET: {max_threads} {Colors.CYAN}ACTIVE: {progress_color}{ws_count}/{max_threads} ({progress_percent:.1f}%){Colors.RESET}")
            lines.append(f"{Colors.WHITE}DURATION: {duration} {Colors.CYAN}SPEED: {performance_stats['connections_per_second']}/s{Colors.RESET}")
            lines.append("")
            
            conn_color = Colors.GREEN if ws_count > max_threads * 0.5 else Colors.YELLOW if ws_count > max_threads * 0.2 else Colors.RED
            active_color = Colors.YELLOW if active_count > 0 else Colors.RED
            lines.append(f"{Colors.BLUE}CONNECTIONS: {conn_color}{ws_count} {Colors.BLUE}ACTIVE: {active_color}{active_count}{Colors.RESET}")
            
            handshake_total = handshake_success + handshake_failed
            handshake_rate = (handshake_success / handshake_total * 100) if handshake_total > 0 else 0
            handshake_color = Colors.GREEN if handshake_rate > 90 else Colors.YELLOW if handshake_rate > 80 else Colors.RED
            lines.append(f"{Colors.BLUE}HANDSHAKES: {Colors.GREEN}{handshake_success} {Colors.RED}{handshake_failed} {Colors.BLUE}RATE: {handshake_color}{handshake_rate:.1f}%{Colors.RESET}")
            
            ping_color = Colors.GREEN if ping_count > 0 else Colors.RED
            lines.append(f"{Colors.BLUE}PINGS: {ping_color}{ping_count} {Colors.BLUE}ERRORS: {Colors.RED}{error_count}{Colors.RESET}")
            lines.append("")
            
            with cache_lock:
                cache_size = len(token_cache)
                cache_color = Colors.GREEN if cache_size > 200 else Colors.YELLOW if cache_size > 100 else Colors.RED
                lines.append(f"{Colors.MAGENTA}TOKEN CACHE: {cache_color}{cache_size}{Colors.RESET}")
            lines.append("")
            
            viewer_color = Colors.GREEN if viewer_display > 0 else Colors.YELLOW
            last_update = time.strftime('%H:%M:%S', time.localtime(last_check)) if last_check > 0 else "Never"
            total_increase = performance_stats['total_viewer_increase']
            
            lines.append(f"{Colors.CYAN}REAL VIEWER STATS:{Colors.RESET}")
            lines.append(f"{Colors.WHITE}CHANNEL: {channel} {Colors.CYAN}VIEWERS: {viewer_color}{viewer_display} (+{total_increase}){Colors.RESET}")
            lines.append(f"{Colors.WHITE}CHANNEL ID: {channel_id}{Colors.RESET}")
            if stream_id:
                lines.append(f"{Colors.WHITE}STREAM ID: {stream_id}{Colors.RESET}")
            lines.append(f"{Colors.WHITE}LAST UPDATE: {last_update}{Colors.RESET}")
            lines.append("")
            
            if performance_stats['connections_per_second'] > 0:
                remaining = max_threads - ws_count
                eta_seconds = remaining / performance_stats['connections_per_second']
                eta_minutes = int(eta_seconds / 60)
                eta_seconds = int(eta_seconds % 60)
                lines.append(f"{Colors.YELLOW}ETA: {eta_minutes}:{eta_seconds:02d} | Press Ctrl+C to stop{Colors.RESET}")
            else:
                lines.append(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.RESET}")
            
            lines.append(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            
            for line in lines:
                print(line)
            
            last_lines = len(lines)
            sys.stdout.flush()
            time.sleep(2)
            
        except Exception as e:
            time.sleep(2)

def connect():
    global active, attempts, channel_id, thread_limit
    global successful_handshakes, failed_handshakes, connection_errors
    
    with lock:
        active += 1
        attempts += 1
    
    try:
        token = None
        with cache_lock:
            if token_cache:
                token = token_cache.pop(0)
        
        if not token:
            token = get_token()
        
        if not token:
            with lock:
                failed_handshakes += 1
            return
        
        if not channel_id:
            channel_id = get_channel_info(channel)
            if not channel_id:
                with lock:
                    failed_handshakes += 1
                return
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(websocket_handler(token))
            with lock:
                successful_handshakes += 1
        except:
            with lock:
                failed_handshakes += 1
        finally:
            try:
                loop.close()
            except:
                pass
    except:
        with lock:
            connection_errors += 1
    finally:
        with lock:
            active -= 1
        thread_limit.release()

async def websocket_handler(token):
    global connections, stop, channel_id, heartbeats, pings
    
    connected = False
    
    try:
        url = f"wss://websockets.kick.com/viewer/v1/connect?token={token}"
        async with websockets.connect(url, ping_interval=None, ping_timeout=None, close_timeout=5) as ws:
            with lock:
                connections += 1
            connected = True
            
            handshake = {
                "type": "channel_handshake",
                "data": {"message": {"channelId": channel_id}}
            }
            await ws.send(json.dumps(handshake))
            with lock:
                heartbeats += 1
            
            ping_count = 0
            while not stop and ping_count < 120:
                ping_count += 1
                
                try:
                    ping = {"type": "ping"}
                    await asyncio.wait_for(ws.send(json.dumps(ping)), timeout=5)
                    with lock:
                        pings += 1
                    
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                    except:
                        pass
                        
                except:
                    break
                
                await asyncio.sleep(random.randint(8, 12))
                
    except Exception as e:
        pass
    finally:
        if connected:
            with lock:
                if connections > 0:
                    connections -= 1

def connection_manager():
    global threads, stop
    
    for _ in range(5):
        token_thread = Thread(target=prefetch_tokens, daemon=True)
        token_thread.start()
    
    print(f"{Colors.YELLOW}🔥 Pre-warming token cache...{Colors.RESET}")
    
    def fetch_tokens_batch():
        for _ in range(10):
            token = get_token()
            if token:
                with cache_lock:
                    token_cache.append(token)
    
    warm_threads = []
    for i in range(75):
        t = Thread(target=fetch_tokens_batch, daemon=True)
        t.start()
        warm_threads.append(t)
    
    for t in warm_threads:
        t.join(timeout=10)
    
    print(f"{Colors.GREEN}✅ Token cache ready: {len(token_cache)} tokens{Colors.RESET}")
    
    last_burst_time = time.time()
    burst_count = 0
    batch_multiplier = 1.0
    
    while not stop:
        try:
            current_connections = connections
            needed = max(0, max_threads - current_connections)
            
            if needed > 0 and current_connections < max_threads:
                current_time = time.time()
                time_since_burst = current_time - last_burst_time
                
                if time_since_burst >= 1.0:
                    burst_count = 0
                    last_burst_time = current_time
                    
                    with lock:
                        success_rate = successful_handshakes / max(1, successful_handshakes + failed_handshakes)
                    
                    if success_rate > 0.9:
                        batch_multiplier = min(2.0, batch_multiplier * 1.1)
                    elif success_rate < 0.7:
                        batch_multiplier = max(0.5, batch_multiplier * 0.9)
                
                with cache_lock:
                    cache_size = len(token_cache)
                
                if cache_size > 200:
                    max_burst_per_second = 300
                    base_batch = 150
                elif cache_size > 100:
                    max_burst_per_second = 200
                    base_batch = 100
                else:
                    max_burst_per_second = 150
                    base_batch = 75
                
                batch_size = int(min(needed, base_batch * batch_multiplier))
                remaining_burst = max_burst_per_second - burst_count
                batch_size = min(batch_size, remaining_burst)
                
                if batch_size > 0:
                    for i in range(batch_size):
                        if stop or connections >= max_threads:
                            break
                        
                        if thread_limit.acquire(blocking=False):
                            t = Thread(target=connect)
                            t.daemon = True
                            t.start()
                            threads.append(t)
                            burst_count += 1
            
            threads = [t for t in threads if t.is_alive()]
            time.sleep(0.005)
            
        except Exception:
            time.sleep(0.05)

def run(thread_count, channel_name):
    global max_threads, channel, start_time, threads, thread_limit, channel_id, stop
    
    max_threads = int(thread_count)
    channel = clean_channel_name(channel_name)
    thread_limit = Semaphore(max_threads * 2)
    start_time = datetime.datetime.now()
    
    print(f"{Colors.CYAN}Getting channel info for {channel}...{Colors.RESET}")
    channel_id = get_channel_info(channel)
    
    if not channel_id:
        print(f"{Colors.RED}Failed to get channel ID.{Colors.RESET}")
        return
    
    print(f"{Colors.GREEN}Channel ID: {channel_id}{Colors.RESET}")
    if stream_id:
        print(f"{Colors.GREEN}Stream ID: {stream_id}{Colors.RESET}")
    
    initial_viewers = get_viewer_count()
    print(f"{Colors.YELLOW}Initial viewers: {initial_viewers}{Colors.RESET}")
    
    print(f"{Colors.GREEN}🚀 Starting {max_threads} viewers - phoneix{Colors.RESET}")
    
    stats_thread = Thread(target=show_stats, daemon=True)
    stats_thread.start()
    
    manager_thread = Thread(target=connection_manager, daemon=True)
    manager_thread.start()
    
    initial_batch = min(max_threads, 100)
    print(f"{Colors.YELLOW}🔥 Launching {initial_batch} initial connections...{Colors.RESET}")
    
    for i in range(initial_batch):
        if stop:
            break
        if thread_limit.acquire(blocking=False):
            t = Thread(target=connect)
            t.daemon = True
            t.start()
            threads.append(t)
    
    try:
        while not stop:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop = True
        print(f"\n{Colors.YELLOW}Stopping...{Colors.RESET}")

if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.CYAN}🔥 kick view boost - phoneix 🔥{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*65}{Colors.RESET}")
        print(f"{Colors.YELLOW}Private tool for kick web.{Colors.RESET}")
        print()
        
        channel_input = input("Enter channel name: ").strip()
        if not channel_input:
            print("Channel name needed.")
            sys.exit(1)
        
        try:
            thread_input = int(input("Enter number of viewers: ").strip())
        except:
            thread_input = 100
        
        run(thread_input, channel_input)
    except KeyboardInterrupt:
        stop = True
        print(f"\n{Colors.YELLOW}Exiting...{Colors.RESET}")