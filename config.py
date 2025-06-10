# config.py - Configuration file for Truecaller Bot

import os
from dotenv import load_dotenv

load_dotenv()  # .env file load karega

class BotConfig:
    # Telegram Bot Token (Get from @BotFather)
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Owner Telegram User ID (Get from @userinfobot)
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))  # <-- apna log channel ka ID yahan daalein
    
    # Pyrogram Configuration
    PYROGRAM_API_ID = int(os.getenv("PYROGRAM_API_ID", "0"))  # <-- apna API_ID
    PYROGRAM_API_HASH = os.getenv("PYROGRAM_API_HASH")
    PYROGRAM_STRING_SESSION = os.getenv("PYROGRAM_STRING_SESSION")

    # API Configuration
    TRUECALLER_API_URL = os.getenv("TRUECALLER_API_URL")
    VALIDATION_API_URL = os.getenv("VALIDATION_API_URL")
    
    # Welcome Image URL
    WELCOME_IMAGE = os.getenv("WELCOME_IMAGE")

    # Force Subscription Channels
    FORCE_SUB_CHANNELS = [
        {"name": f"Channel {i+1}", "id": cid}
        for i, cid in enumerate(os.getenv("FORCE_SUB_CHANNELS", "").split(",") if os.getenv("FORCE_SUB_CHANNELS") else [])
    ]
    
    # Access Keys File Path
    ACCESS_KEYS_FILE = "access_keys.txt"
    
    # Rate Limiting
    MAX_QUERIES_PER_USER_PER_DAY = int(os.getenv("MAX_QUERIES_PER_USER_PER_DAY", "50"))
    MAX_QUERIES_PER_MINUTE = int(os.getenv("MAX_QUERIES_PER_MINUTE", "10"))
    
    # Supported Country Code
    COUNTRY_CODE = os.getenv("COUNTRY_CODE", "+91")
    COUNTRY_NAME = os.getenv("COUNTRY_NAME", "India")
    
    # Valid Starting Digits for Indian Numbers
    VALID_STARTING_DIGITS = os.getenv("VALID_STARTING_DIGITS", "6,7,8,9").split(",")
    
    # Bot Messages (Stylized)
    MESSAGES = {
        "welcome": (
            "🎉 ᴡᴇʟᴄᴏᴍᴇ {name}!\n\n"
            "🔍 ɪ ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ꜰɪɴᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴅᴇᴛᴀɪʟs ᴊᴜsᴛ ʟɪᴋᴇ ᴛʀᴜᴇᴄᴀʟʟᴇʀ!\n\n"
            "📱 ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴀɴᴅ ɪ'ʟʟ ᴘʀᴏᴠɪᴅᴇ:\n"
            "• ɴᴀᴍᴇ (ɪꜰ ᴀᴠᴀɪʟᴀʙʟᴇ)\n"
            "• ʟᴏᴄᴀᴛɪᴏɴ\n"
            "• ᴄᴀʀʀɪᴇʀ\n"
            "• ʟɪɴᴇ ᴛʏᴘᴇ\n"
            "• ᴠᴀʟɪᴅᴀᴛɪᴏɴ sᴛᴀᴛᴜs\n"
            "• ᴛɪᴍᴇᴢᴏɴᴇ\n\n"
            "📝 ꜰᴏʀᴍᴀᴛ: 98xxxxxxxx ᴏʀ +919xxxxxxxx\n\n"
            "💡 ᴇxᴀᴍᴘʟᴇ: 9876543210"
        ),
        "force_sub": (
            "⚠️ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ꜰɪʀsᴛ:"
        ),
        "join_channels": (
            "⚠️ ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ꜰɪʀsᴛ"
        ),
        "membership_verified": (
            "✅ ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴊᴏɪɴɪɴɢ!\n\n"
            "🔍 ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ\n"
            "📱 ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ!\n\n"
            "💡 ᴇxᴀᴍᴘʟᴇ: 9876543210"
        ),
        "invalid_format": (
            "📱 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ\n\n"
            "📝 ꜰᴏʀᴍᴀᴛ: 98xxxxxxxx\n"
            "💡 ᴇxᴀᴍᴘʟᴇ: `9876543210`"
        ),
        "processing": "🔍 ꜰᴇᴛᴄʜɪɴɢ ᴅᴇᴛᴀɪʟs... ⏳",
        "error": (
            "❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴅᴇᴛᴀɪʟs\n\n"
            "🔄 ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ"
        ),
        "unauthorized": "❌ ʏᴏᴜ ᴀʀᴇ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ",
        "broadcast_usage": "📢 ᴜsᴀɢᴇ: /broadcast <ᴍᴇssᴀɢᴇ>",
        "broadcast_start": "📤 sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...",
        "data_export": "📊 ʙᴏᴛ ᴅᴀᴛᴀ ᴇxᴘᴏʀᴛ"
    }
    
    # Button Labels
    BUTTONS = {
        "join_channel": "📢 ᴊᴏɪɴ {channel_name}",
        "check_membership": "✅ ᴄʜᴇᴄᴋ ᴍᴇᴍʙᴇʀsʜɪᴘ",
        "whatsapp": "💬 WhatsApp",
        "telegram": "📱 Telegram"
    }
    
    # Database Collections
    DB_COLLECTIONS = {
        "users": "users",
        "queries": "queries", 
        "stats": "stats"
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        required_fields = [
            "BOT_TOKEN",
            "MONGO_URI", 
            "OWNER_ID"
        ]
        for field in required_fields:
            value = getattr(cls, field)
            if not value or (isinstance(value, str) and "YOUR_" in value):
                print(f"❌ Please configure {field} in config.py")
                return False
        return True
    
    @classmethod
    def get_env_example(cls) -> str:
        """Get example environment variables"""
        return """
# Example .env file
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/truecaller_bot
OWNER_ID=123456789
        """.strip()
    
    @staticmethod
    def get_channel_url(channel_id_or_username):
        """Return t.me URL for channel username or ID"""
        val = str(channel_id_or_username)
        if val.startswith("@"):
            return f"https://t.me/{val.lstrip('@')}"
        elif val.startswith("-100"):
            # For public channels, use /c/ + id[4:], but this only works for supergroups, not public channels
            return f"https://t.me/c/{val[4:]}"
        else:
            return f"https://t.me/{val}"

# API Keys Management
class APIKeysManager:
    def __init__(self, keys_file: str = "access_keys.txt"):
        self.keys_file = keys_file
        self.keys = []
        self.current_index = 0
        self.load_keys()
    
    def load_keys(self) -> None:
        """Load API keys from file"""
        try:
            with open(self.keys_file, 'r') as f:
                self.keys = [line.strip() for line in f.readlines() if line.strip()]
            print(f"✅ Loaded {len(self.keys)} API keys")
        except FileNotFoundError:
            print(f"❌ {self.keys_file} not found. Creating example file...")
            self.create_example_file()
    
    def create_example_file(self) -> None:
        """Create example access keys file"""
        example_content = """# Add your API access keys here (one per line)
your_first_access_key_here
your_second_access_key_here
your_third_access_key_here
# Add more keys as needed
"""
        with open(self.keys_file, 'w') as f:
            f.write(example_content)
        print(f"📝 Created {self.keys_file} with example keys")
    
    def get_next_key(self) -> str:
        """Get next API key in rotation"""
        if not self.keys:
            return None
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key
    
    def get_current_key(self) -> str:
        """Get current API key without rotation"""
        if not self.keys:
            return None
        return self.keys[self.current_index]
    
    def reload_keys(self) -> None:
        """Reload keys from file"""
        self.load_keys()
        self.current_index = 0
        print("🔄 API keys reloaded")

# Text Styling Utility
class TextStyler:
    @staticmethod
    def stylize(text: str) -> str:
        """Convert text to stylized small caps Unicode"""
        normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        small_caps = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
        result = ""
        for char in text:
            if char in normal:
                result += small_caps[normal.index(char)]
            else:
                result += char
        return result

# Phone Number Utilities
class PhoneUtils:
    @staticmethod
    def clean_number(number: str) -> str:
        """Clean phone number from special characters"""
        import re
        return re.sub(r'[^\d+]', '', number)
    
    @staticmethod
    def validate_indian_number(number: str) -> tuple:
        """Validate Indian phone number format"""
        clean_number = PhoneUtils.clean_number(number)
        # Remove country code if present
        if clean_number.startswith('+91'):
            phone_number = clean_number[3:]
        elif clean_number.startswith('91') and len(clean_number) > 10:
            phone_number = clean_number[2:]
        else:
            phone_number = clean_number
        # Check length
        if len(phone_number) != 10:
            return False, "ɴᴜᴍʙᴇʀ ᴍᴜsᴛ ʙᴇ ᴇxᴀᴄᴛʟʏ 10 ᴅɪɡɪᴛs"
        # Check starting digit
        if phone_number[0] not in BotConfig.VALID_STARTING_DIGITS:
            return False, f"ɪɴᴅɪᴀɴ ɴᴜᴍʙᴇʀs ᴍᴜsᴛ sᴛᴀʀᴛ ᴡɪᴛʜ {', '.join(BotConfig.VALID_STARTING_DIGITS)}"
        return True, phone_number
    
    @staticmethod
    def format_number_with_country_code(number: str) -> str:
        """Format number with country code"""
        return f"{BotConfig.COUNTRY_CODE}{number}"

# Export configuration
__all__ = [
    'BotConfig',
    'APIKeysManager', 
    'TextStyler',
    'PhoneUtils'
]
