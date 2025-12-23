import os
import sys
import time
import json
import asyncio
import threading
import websockets
import random
from datetime import datetime
import discord
from discord.ext import commands, tasks

TOKEN_URL = "https://discord.com/api/v9/users/@me"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

async def check_token(token):
    headers = {"Authorization": token}
    async with websockets.connect("wss://gateway.discord.gg/?v=9&encoding=json") as ws:
        await ws.send(json.dumps({"op": 2, "d": {"token": token, "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"}}}))
        response = await ws.recv()
        if "Invalid" in response:
            return False
        return True

async def fetch_guild_id_for_channel(token, channel_id):
    try:
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://discord.com/api/v9/channels/{channel_id}", headers=headers) as response:
                if response.status == 200:
                    channel_data = await response.json()
                    return channel_data.get("guild_id")
                elif response.status == 404:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Channel not found (404)")
                    return None
                else:
                    return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching guild ID: {e}")
        return None

# --- PHẦN CLASS SPAMVOICE ĐÃ SỬA LỖI ---
class SpamVoice:
    def __init__(self, token, channel_id, mp3_file):
        self.token = token
        self.channel_id = channel_id
        self.mp3_file = mp3_file
        
        # SỬA LỖI: Khai báo Intents
        intents = discord.Intents.default()
        intents.message_content = True 
        
        # SỬA LỖI: Thêm argument 'intents' vào khởi tạo Bot
        self.client = commands.Bot(command_prefix="!", intents=intents, self_bot=True)
        
        self.is_running = True
        self.voice = None
        
        self.client.event(self.on_ready)
        
        # Sử dụng tasks.loop đúng cách
        self.spam_voice_task = tasks.loop(seconds=1.0)(self.spam_voice_func)
    
    async def on_ready(self):
        print(f"Đã đăng nhập: {self.client.user}")
        if not self.spam_voice_task.is_running():
            self.spam_voice_task.start()
    
    async def spam_voice_func(self):
        try:
            voice_channel = self.client.get_channel(int(self.channel_id))
            if not voice_channel:
                voice_channel = await self.client.fetch_channel(int(self.channel_id))
            
            if not self.voice or not self.voice.is_connected():
                self.voice = await voice_channel.connect()
            
            if not self.voice.is_playing():
                self.voice.play(discord.FFmpegPCMAudio(self.mp3_file))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang phát nhạc...")
                
        except Exception as e:
            print(f"Lỗi Xả Mic: {e}")
            await asyncio.sleep(5)
    
    def start(self):
        self.client.run(self.token)
    
    def stop(self):
        self.is_running = False
        self.spam_voice_task.cancel()
        asyncio.run_coroutine_threadsafe(self.client.close(), self.client.loop)

# --- GIỮ NGUYÊN CLASS HANGVOICE VÀ CÁC HÀM KHÁC TỪ FILE CŨ CỦA BẠN ---
class HangVoice:
    def __init__(self, token, channel_id, mute, deaf, stream):
        self.token = token
        self.channel_id = channel_id
        self.mute = mute
        self.deaf = deaf
        self.stream = stream
        self.ws = None
        self.heartbeat_interval = None
        self.session_id = None
        self.resume_gateway_url = None
        self.last_sequence = None
        self.is_running = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.heartbeat_task = None
        self.last_heartbeat_ack = True
        self.ws_connected = False
        self.guild_id = None
        self.HEARTBEAT_TIMEOUT = 30
        self.user_id = None
        self.last_activity = time.time()
        self.idle_timeout = 300
        self.connected = False
        
    async def connect(self):
        try:
            self.ws = await websockets.connect("wss://gateway.discord.gg/?v=9&encoding=json", 
                                             ping_interval=None,
                                             max_size=10_000_000,
                                             close_timeout=5)
            self.ws_connected = True
            self.connected = True
            
            await self.ws.send(json.dumps({
                "op": 2,
                "d": {
                    "token": self.token,
                    "capabilities": 16381,
                    "properties": {"$os": "windows", "$browser": "chrome", "$device": "desktop"},
                    "presence": {"status": "online", "since": 0, "activities": [], "afk": False},
                    "intents": 641
                }
            }))
            
            self.guild_id = await fetch_guild_id_for_channel(self.token, self.channel_id)
            
            while self.is_running and self.ws_connected:
                data = await asyncio.wait_for(self.ws.recv(), timeout=self.HEARTBEAT_TIMEOUT)
                await self.handle_event(json.loads(data))
                
        except Exception as e:
            await self.reconnect()

    async def handle_event(self, data):
        op, t, d = data.get('op'), data.get('t'), data.get('d')
        if op == 10:
            self.heartbeat_interval = d['heartbeat_interval'] / 1000
            await self.start_heartbeat()
        elif op == 0 and t == "READY":
            self.user_id = d.get('user', {}).get('id')
            await self.join_voice()
        elif op == 11:
            self.last_heartbeat_ack = True

    async def start_heartbeat(self):
        async def heartbeat_loop():
            while self.is_running and self.ws_connected:
                await self.ws.send(json.dumps({"op": 1, "d": self.last_sequence}))
                await asyncio.sleep(self.heartbeat_interval)
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def join_voice(self):
        payload = {
            "op": 4,
            "d": {
                "guild_id": self.guild_id,
                "channel_id": self.channel_id,
                "self_mute": self.mute,
                "self_deaf": self.deaf,
                "self_video": self.stream,
                "self_stream": True
            }
        }
        await self.ws.send(json.dumps(payload))

    async def reconnect(self):
        await asyncio.sleep(5)
        await self.connect()

    def start(self):
        asyncio.run(self.connect())

async def get_gateway_url(token):
    return "wss://gateway.discord.gg/?v=9&encoding=json"

def spam_voice_handler():
    clear_screen()
    token = input("Nhập Token: ")
    mp3_file = input("Nhập File .mp3: ")
    channel_id = input("Nhập ID Kênh Cần Xả: ")
    if not os.path.exists(mp3_file):
        print("File không tồn tại!")
        return
    spam = SpamVoice(token, channel_id, mp3_file)
    spam.start()

def hang_voice_handler():
    clear_screen()
    token_file = input("Nhập File Chứa Token: ")
    channel_id = input("Nhập ID Room Voice: ")
    mute = input("Tắt Mic? (y/n): ").lower() == 'y'
    deaf = input("Tắt Loa? (y/n): ").lower() == 'y'
    stream = input("Bật Video? (y/n): ").lower() == 'y'
    
    with open(token_file, 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    for i, token in enumerate(tokens):
        t = threading.Thread(target=lambda: HangVoice(token, channel_id, mute, deaf, stream).start())
        t.daemon = True
        t.start()
        time.sleep(0.5)
    
    while True: time.sleep(1)

def main():
    while True:
        clear_screen()
        print("1. Xả Mic\n2. Treo Room")
        choice = input("Chọn: ")
        if choice == "1": spam_voice_handler()
        elif choice == "2": hang_voice_handler()

if __name__ == "__main__":
    main()
