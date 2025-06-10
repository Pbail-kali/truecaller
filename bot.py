import asyncio
import logging
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from io import BytesIO
import os
import warnings

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode, ChatType
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client

# Import configuration
from config import BotConfig, APIKeysManager, TextStyler, PhoneUtils

# Configure logging
logging.basicConfig(
    format=BotConfig.LOG_FORMAT, 
    level=logging.WARNING  # ya logging.ERROR
)
logger = logging.getLogger(__name__)

# Suppress httpx and telegram logs except WARNING and ERROR
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("telegram.bot").setLevel(logging.WARNING)

# Suppress asyncio and pyrogram peer id errors
class IgnorePeerIdInvalid(logging.Filter):
    def filter(self, record):
        return "Peer id invalid" not in record.getMessage()

logging.getLogger("asyncio").addFilter(IgnorePeerIdInvalid())
logging.getLogger("pyrogram").addFilter(IgnorePeerIdInvalid())

# warnings.showwarning = ignore_peer_id_error

class TruecallerBot:
    def __init__(self):
        # Validate configuration
        if not BotConfig.validate_config():
            raise ValueError("Invalid configuration. Please check config.py")
        
        self.mongo_client = MongoClient(BotConfig.MONGO_URI)
        self.db = self.mongo_client['truecaller_bot']
        self.users_collection = self.db[BotConfig.DB_COLLECTIONS['users']]
        self.queries_collection = self.db[BotConfig.DB_COLLECTIONS['queries']]
        self.stats_collection = self.db[BotConfig.DB_COLLECTIONS['stats']]
        
        # Initialize API keys manager
        self.api_keys = APIKeysManager(BotConfig.ACCESS_KEYS_FILE)
        self.access_keys = self.api_keys.keys  # <-- Add this line
        self.current_key_index = 0
        
        # Initialize stats
        self.init_stats()
    
    def init_stats(self):
        """Initialize statistics collection"""
        if not self.stats_collection.find_one({"type": "daily"}):
            self.stats_collection.insert_one({
                "type": "daily",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "queries": 0,
                "users": 0
            })
    
    async def check_subscription(self, user_id: int, bot: Bot) -> bool:
        """Check if user is subscribed to force sub channels or has pending join request"""
        for channel in BotConfig.FORCE_SUB_CHANNELS:
            try:
                member = await bot.get_chat_member(channel["id"], user_id)
                if member.status in ['left', 'kicked']:
                    # Check pending join request via userbot
                    if await has_pending_join_request(user_id, channel["id"]):
                        continue  # allow if join request pending
                    return False
            except Exception:
                # Check pending join request via userbot
                if await has_pending_join_request(user_id, channel["id"]):
                    continue
                return False
        return True

    async def get_subscription_keyboard(self, bot):
        keyboard = []
        for channel in BotConfig.FORCE_SUB_CHANNELS:
            url = await get_channel_invite_link(bot, channel["id"])
            if url:
                keyboard.append([InlineKeyboardButton(
                    f"📢 ᴊᴏɪɴ {channel['name']}",
                    url=url
                )])
        keyboard.append([InlineKeyboardButton(
            "✅ ᴄʜᴇᴄᴋ ᴍᴇᴍʙᴇʀsʜɪᴘ",
            callback_data="check_membership"
        )])
        return InlineKeyboardMarkup(keyboard),
    
    def stylize_text(self, text: str) -> str:
        """Convert text to stylized small caps Unicode"""
        normal = "abcdefghijklmnopqrstuvwxyz"
        small_caps = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
        
        result = ""
        for char in text.lower():
            if char in normal:
                result += small_caps[normal.index(char)]
            else:
                result += char
        return result
    
    async def check_subscription(self, user_id: int, bot: Bot) -> bool:
        """Check if user is subscribed to force sub channels or has pending join request"""
        for channel in BotConfig.FORCE_SUB_CHANNELS:
            try:
                member = await bot.get_chat_member(channel["id"], user_id)
                if member.status in ['left', 'kicked']:
                    # Check pending join request via userbot
                    if await has_pending_join_request(user_id, channel["id"]):
                        continue  # allow if join request pending
                    return False
            except Exception:
                # Check pending join request via userbot
                if await has_pending_join_request(user_id, channel["id"]):
                    continue
                return False
        return True
    
    async def get_subscription_keyboard(self, bot):
        keyboard = []
        for channel in BotConfig.FORCE_SUB_CHANNELS:
            url = await get_channel_invite_link(bot, channel["id"])
            if url:
                keyboard.append([InlineKeyboardButton(
                    f"📢 ᴊᴏɪɴ {channel['name']}",
                    url=url
                )])
        keyboard.append([InlineKeyboardButton(
            "✅ ᴄʜᴇᴄᴋ ᴍᴇᴍʙᴇʀsʜɪᴘ",
            callback_data="check_membership"
        )])
        return InlineKeyboardMarkup(keyboard)
    
    def validate_phone_number(self, number: str) -> tuple:
        """Validate Indian phone number format"""
        # Remove spaces and special characters
        clean_number = re.sub(r'[^\d+]', '', number)
        
        # Check if it has country code
        if clean_number.startswith('+91'):
            phone_number = clean_number[3:]  # Remove +91
        elif clean_number.startswith('91') and len(clean_number) > 10:
            phone_number = clean_number[2:]  # Remove 91
        else:
            phone_number = clean_number
        
        # Check if it's exactly 10 digits
        if len(phone_number) != 10:
            return False, "ɴᴜᴍʙᴇʀ ᴍᴜsᴛ ʙᴇ ᴇxᴀᴄᴛʟʏ 10 ᴅɪɡɪᴛs"
        
        # Check if it starts with 6, 7, 8, or 9
        if not phone_number[0] in ['6', '7', '8', '9']:
            return False, "ɪɴᴅɪᴀɴ ɴᴜᴍʙᴇʀs ᴍᴜsᴛ sᴛᴀʀᴛ ᴡɪᴛʜ 6, 7, 8, ᴏʀ 9"
        
        return True, phone_number
    
    def get_current_access_key(self) -> str:
        """Get current access key and rotate if needed"""
        if not self.access_keys:
            return None

        key = self.access_keys[self.current_key_index]
        # Only rotate if more than one key
        if len(self.access_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.access_keys)
        return key
    
    async def fetch_truecaller_data(self, phone_number: str) -> Dict:
        """Fetch data from Truecaller API"""
        try:
            url = f"https://true-call-check.vercel.app/api/truecaller?q=+91{phone_number}"
            response = requests.get(url, timeout=10)
            logger.info(f"Truecaller API response: {response.text}")  # <-- Add this line
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Truecaller API error: {e}")
        return {}
    
    async def fetch_validation_data(self, phone_number: str, context=None) -> Dict:
        """Fetch data from validation API with access key rotation"""
        max_attempts = len(self.access_keys)
        key_failed = False

        for attempt in range(max_attempts):
            access_key = self.get_current_access_key()
            if not access_key:
                break

            try:
                url = f"http://apilayer.net/api/validate"
                params = {
                    'access_key': access_key,
                    'number': f"{phone_number}",
                    'country_code': 'IN',
                    'format': '1'
                }

                response = requests.get(url, params=params, timeout=10)
                logger.info(f"Validation API response: {response.text}")
                if response.status_code == 200:
                    data = response.json()
                    if "success" in data and not data["success"]:
                        error_info = data.get('error', {}).get('info', '')
                        # Sirf jab limit exceed ho tab log channel me bhejein
                        if "Your monthly API request volume has been reached" in error_info or "limit" in error_info.lower():
                            key_failed = True
                            if context:
                                await context.bot.send_message(
                                    chat_id=BotConfig.LOG_CHANNEL_ID,
                                    text=f"❌ API key limit exceeded: `{access_key}`",
                                    parse_mode=ParseMode.MARKDOWN
                                )
                        logger.error(f"Validation API error: {error_info}")
                        continue  # Try next key
                    return data
            except Exception as e:
                logger.error(f"Validation API error with key {access_key}: {e}")
                continue

        # If all keys failed
        if key_failed and context:
            await context.bot.send_message(
                chat_id=BotConfig.LOG_CHANNEL_ID,
                text="❌ All API keys exhausted! Please add new keys.",
                parse_mode=ParseMode.MARKDOWN
            )
        return {}
    
    def format_phone_details(self, truecaller_data: Dict, validation_data: Dict, phone_number: str) -> str:
        lines = []
        lines.append("🌟 ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴅᴇᴛᴀɪʟs🌟\n")
        lines.append("╔════❰ ɴᴜᴍʙᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ❱═❍")
        lines.append(f"║┣⪼ <b>ɴᴜᴍʙᴇʀ:</b> +91{phone_number}")
        if truecaller_data:
            name = truecaller_data.get('name', 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ')
            lines.append(f"║┣⪼ <b>ɴᴀᴍᴇ:</b> {name}")
        if validation_data:
            country = validation_data.get('country_name', 'India')
            location = validation_data.get('location', 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ')
            carrier = validation_data.get('carrier', 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ')
            line_type = validation_data.get('line_type', 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ')
            valid = "✅ ᴠᴀʟɪᴅ" if validation_data.get('valid', False) else "❌ ɪɴᴠᴀʟɪᴅ"
            lines.append(f"║┣⪼ <b>ᴄᴏᴜɴᴛʀʏ:</b> {country}")
            lines.append(f"║┣⪼ <b>ʟᴏᴄᴀᴛɪᴏɴ:</b> {location}")
            lines.append(f"║┣⪼ <b>ᴄᴀʀʀɪᴇʀ:</b> {carrier}")
            lines.append(f"║┣⪼ <b>ʟɪɴᴇ ᴛʏᴘᴇ:</b> {line_type}")
            lines.append(f"║┣⪼ <b>ᴠᴀʟɪᴅ:</b> {valid}")
            timezone = validation_data.get('timezone', {})
            if timezone:
                tz_name = timezone.get('name', 'ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ')
                lines.append(f"║┣⪼ <b>ᴛɪᴍᴇᴢᴏɴᴇ:</b> {tz_name}")
        lines.append("║╰━━━━━━━━━━━━━━━➣")
        lines.append("╚══════════════════❍")
        lines.append("💬 ꜰᴏʀ ᴍᴏʀᴇ @INDIAN_HACKER_BOTS")
        return "\n".join(lines)
    
    def get_contact_buttons(self, phone_number: str):
        """Get WhatsApp and Telegram contact buttons"""
        keyboard = [
            [
                InlineKeyboardButton("✨ ᴡʜᴀᴛꜱᴀᴘᴘ", url=f"https://wa.me/+91{phone_number}"),
                InlineKeyboardButton("💫 ᴛᴇʟᴇɢʀᴀᴍ", url=f"https://t.me/+91{phone_number}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def save_user(self, user_id: int, username: str = None, name: str = None):
        """Save user to database and return True if new user"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "name": name,
            "first_seen": datetime.now()
        }
        result = self.users_collection.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": user_data,
                "$set": {"last_seen": datetime.now()}
            },
            upsert=True
        )
        return result.upserted_id is not None
    
    def save_query(self, user_id: int, phone_number: str, result: Dict):
        """Save query to database"""
        query_data = {
            "user_id": user_id,
            "phone_number": phone_number,
            "result": result,
            "timestamp": datetime.now()
        }
        
        self.queries_collection.insert_one(query_data)
        
        # Update user query count
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"query_count": 1}}
        )
        
        # Update daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        self.stats_collection.update_one(
            {"type": "daily", "date": today},
            {"$inc": {"queries": 1}},
            upsert=True
        )

# Initialize bot
bot_instance = TruecallerBot()

# Initialize pyrogram userbot client (global)
userbot = Client(
    name="userbot",
    api_id=BotConfig.PYROGRAM_API_ID,
    api_hash=BotConfig.PYROGRAM_API_HASH,
    session_string=BotConfig.PYROGRAM_STRING_SESSION
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    is_new = bot_instance.save_user(user.id, user.username, user.first_name)

    # 1. Sabse pehle sticker bhejo aur uska message object save karo
    sticker_msg = None
    try:
        sticker_msg = await update.message.reply_sticker("CAACAgQAAxkBAAEOrJ9oR9rh3jB2r1I3Qb5TZey80JIU-QACnxEAAqbxcR57wYUDyflSITYE")
    except Exception as e:
        logger.error(f"Sticker send error: {e}")

    # --- Log to channel only for new users ---
    if is_new:
        log_text = (
            f"👤 New User Started Bot\n"
            f"ID: <code>{user.id}</code>\n"
            f"Username: @{user.username}\n"
            f"Name: {user.first_name}"
        )
        try:
            await context.bot.send_message(
                chat_id=BotConfig.LOG_CHANNEL_ID,
                text=log_text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Log channel error: {e}")

    # Check subscription
    if not await bot_instance.check_subscription(user.id, context.bot):
        welcome_text = bot_instance.stylize_text(
            f"🎉 Welcome {user.first_name}!\n\n"
            "🔍 I can help you find phone number details just like Truecaller!\n\n"
            "⚠️ To use this bot, you must join our channels first:"
        )
        # Sticker delete karo (agar bheja gaya tha)
        if sticker_msg:
            try:
                await sticker_msg.delete()
            except Exception as e:
                logger.error(f"Sticker delete error: {e}")

        await update.message.reply_photo(
            photo=BotConfig.WELCOME_IMAGE,
            caption=welcome_text,
            reply_markup=await bot_instance.get_subscription_keyboard(context.bot)
        )
        return

    welcome_text = bot_instance.stylize_text(
        f"🎉 Welcome {user.first_name}!\n\n"
        "🔍 I can help you find phone number details just like Truecaller!\n\n"
        "📱 Just send me a phone number and I'll provide:\n"
        "• Name (if available)\n"
        "• Location\n"
        "• Carrier\n"
        "• Line Type\n"
        "• Validation Status\n"
        "• Timezone\n\n"
        "📝 Format: 98xxxxxxxx or +919xxxxxxxx\n\n"
        "💡 Example: 9876543210"
    )

    # Sticker delete karo (agar bheja gaya tha)
    if sticker_msg:
        try:
            await sticker_msg.delete()
        except Exception as e:
            logger.error(f"Sticker delete error: {e}")

    await update.message.reply_photo(
        photo=BotConfig.WELCOME_IMAGE,
        caption=welcome_text
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number messages"""
    user = update.effective_user

    # Ignore non-text messages
    if not update.message or not update.message.text:
        return

    message_text = update.message.text
    
    # Check subscription first
    if not await bot_instance.check_subscription(user.id, context.bot):
        await update.message.reply_photo(
            photo=BotConfig.WELCOME_IMAGE,
            caption=bot_instance.stylize_text(
                "⚠️ ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ꜰɪʀsᴛ ᴛᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ:"
            ),
            reply_markup=await bot_instance.get_subscription_keyboard(context.bot)
        )
        return
    
    # Check if message contains phone number
    if not re.search(r'[\d+]', message_text):
        await update.message.reply_text(
            bot_instance.stylize_text(
                "📱 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ\n\n"
                "📝 ꜰᴏʀᴍᴀᴛ: 98xxxxxxxx\n"
                "💡 ᴇxᴀᴍᴘʟᴇ: `9876543210`"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Validate phone number
    is_valid, result = bot_instance.validate_phone_number(message_text)
    if not is_valid:
        await update.message.reply_text(
            bot_instance.stylize_text(
                f"❌ ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ꜰᴏʀᴍᴀᴛ\n\n"
                f"🔍 ᴇʀʀᴏʀ: {result}\n\n"
                f"📝 ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ:\n"
                f"• 9876543210\n"
                f"• +919876543210\n\n"
                f"📱 ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɪɴᴅɪᴀɴ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ"
            )
        )
        return
    
    phone_number = result

    # --- Log to channel ---
    log_text = (
        f"🔎 User Query\n"
        f"User: <code>{user.id}</code> @{user.username}\n"
        f"Number: <code>+91{phone_number}</code>"
    )
    try:
        await context.bot.send_message(
            chat_id=BotConfig.LOG_CHANNEL_ID,
            text=log_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Log channel error: {e}")

    # Send processing message
    processing_msg = await update.message.reply_text(
        bot_instance.stylize_text("🔍 ꜰᴇᴛᴄʜɪɴɡ ᴅᴇᴛᴀɪʟs... ⏳")
    )
    
    try:
        # Fetch data from both APIs
        truecaller_data = await bot_instance.fetch_truecaller_data(phone_number)
        validation_data = await bot_instance.fetch_validation_data(phone_number, context)
        
        if not validation_data:
            await processing_msg.edit_text(
                bot_instance.stylize_text(
                    "❌ ᴀʟʟ ᴀᴘɪ ᴋᴇʏs ᴇxʜᴀᴜsᴛᴇᴅ ᴏʀ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ.\n\n"
                    "🔑 ᴘʟᴇᴀsᴇ ᴀᴅᴅ ɴᴇᴡ ᴋᴇʏs ᴏʀ ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ."
                )
            )
            return
        
        # Format and send details
        details_text = bot_instance.format_phone_details(truecaller_data, validation_data, phone_number)
        
        await processing_msg.edit_text(
            details_text,
            parse_mode=ParseMode.HTML,
            reply_markup=bot_instance.get_contact_buttons(phone_number)
        )
        
        # Save query to database
        bot_instance.save_query(user.id, phone_number, {
            "truecaller": truecaller_data,
            "validation": validation_data
        })
        
    except Exception as e:
        logger.error(f"Error processing phone number: {e}")
        await processing_msg.edit_text(
            bot_instance.stylize_text(
                "❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɡ ᴅᴇᴛᴀɪʟs\n\n"
                "🔄 ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ"
            )
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        user_id = query.from_user.id
        if await bot_instance.check_subscription(user_id, context.bot):
            # Only edit if not already success message
            success_caption = bot_instance.stylize_text(
                "✅ ᴛʜᴀɪᴋ ʏᴏᴜ ꜰᴏʀ ᴊᴏɪɴɪɴɢ!\n\n"
                "🔍 ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ\n"
                "📱 ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ!\n\n"
                "💡 ᴇxᴀᴍᴘʟᴇ: 9876543210"
            )
            if query.message.caption != success_caption:
                try:
                    await query.edit_message_caption(
                        caption=success_caption
                    )
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        raise
        else:
            # Always update if not subscribed (keyboard may change)
            try:
                await query.edit_message_caption(
                    caption=bot_instance.stylize_text(
                        "❌ ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ꜰɪʀsᴛ"
                    ),
                    reply_markup=await bot_instance.get_subscription_keyboard(context.bot)
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistics command (Owner only)"""
    if update.effective_user.id != BotConfig.OWNER_ID:
        await update.message.reply_text(
            bot_instance.stylize_text("❌ ʏᴏᴜ ᴀʀᴇ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ")
        )
        return
    
    # Get statistics
    total_users = bot_instance.users_collection.count_documents({})
    today = datetime.now().strftime("%Y-%m-%d")
    today_stats = bot_instance.stats_collection.find_one({"type": "daily", "date": today})
    today_queries = today_stats.get("queries", 0) if today_stats else 0
    
    # Get access key stats (mock for now)
    key_stats = f"🔑 ᴀᴄᴄᴇss ᴋᴇʏs: {len(bot_instance.access_keys)} ᴋᴇʏs ʟᴏᴀᴅᴇᴅ"
    
    stats_text = f"""
📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs**

👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: `{total_users}`
🔍 ᴛᴏᴅᴀʏ's ǫᴜᴇʀɪᴇs: `{today_queries}`
📅 ᴅᴀᴛᴇ: `{today}`

{key_stats}

🔄 ᴄᴜʀʀᴇɴᴛ ᴋᴇʏ ɪɴᴅᴇx: `{bot_instance.current_key_index}`
    """
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast command (Owner only)"""
    if update.effective_user.id != BotConfig.OWNER_ID:
        await update.message.reply_text(
            bot_instance.stylize_text("❌ ʏᴏᴜ ᴀʀᴇ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ")
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            bot_instance.stylize_text("📢 ᴜsᴀɢᴇ: /broadcast <ᴍᴇssᴀɢᴇ>")
        )
        return
    
    message = ' '.join(context.args)
    users = list(bot_instance.users_collection.find({}, {"user_id": 1}))
    
    sent = 0
    failed = 0
    
    progress_msg = await update.message.reply_text(
        bot_instance.stylize_text("📤 sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ...")
    )
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            failed += 1
    
    await progress_msg.edit_text(
        f"📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n"
        f"✅ sᴇɴᴛ: `{sent}`\n"
        f"❌ ꜰᴀɪʟᴇᴅ: `{failed}`\n"
        f"👥 ᴛᴏᴛᴀʟ: `{len(users)}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export data command (Owner only)"""
    if update.effective_user.id != BotConfig.OWNER_ID:
        await update.message.reply_text(
            bot_instance.stylize_text("❌ ʏᴏᴜ ᴀʀᴇ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ")
        )
        return
    
    try:
        # Export users data
        users_data = list(bot_instance.users_collection.find({}))
        queries_data = list(bot_instance.queries_collection.find({}))
        
        # Convert to DataFrames
        users_df = pd.DataFrame(users_data)
        queries_df = pd.DataFrame(queries_data)
        
        # Create Excel file
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            users_df.to_excel(writer, sheet_name='Users', index=False)
            queries_df.to_excel(writer, sheet_name='Queries', index=False)
        
        buffer.seek(0)
        
        await update.message.reply_document(
            document=buffer,
            filename=f"bot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            caption=bot_instance.stylize_text("📊 ʙᴏᴛ ᴅᴀᴛᴀ ᴇxᴘᴏʀᴛ")
        )
        
    except Exception as e:
        await update.message.reply_text(
            bot_instance.stylize_text(f"❌ ᴇʀʀᴏʀ ᴇxᴘᴏʀᴛɪɴɡ ᴅᴀᴛᴀ: {str(e)}")
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = (
        "ℹ️ <b>How to use this bot:</b>\n\n"
        "• <b>Send any Indian phone number</b> to get details.\n"
        "• <b>/stats</b> — Show bot statistics (owner only).\n"
        "• <b>/broadcast &lt;message&gt;</b> — Send message to all users (owner only).\n"
        "• <b>/data</b> — Export user and query data (owner only).\n"
        "\n"
        "Join our channels for updates!"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def get_channel_invite_link(bot: Bot, channel_id: str) -> str:
    try:
        chat = await bot.get_chat(channel_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        # For private channel, create join request link
        invite = await bot.create_chat_invite_link(
            chat_id=channel_id,
            creates_join_request=True  # <-- yeh line add karein
        )
        return invite.invite_link
    except Exception as e:
        return None

async def has_pending_join_request(user_id: int, channel_id: str) -> bool:
    try:
        print(f"Checking join requests for channel: {channel_id}")
        async for req in userbot.get_chat_join_requests(int(channel_id)):
            print(f"Found join request from: {req.user.id}")
            if req.user.id == user_id:
                print("User has pending join request!")
                return True
        print("No join request found for user.")
    except Exception as e:
        print(f"Error in has_pending_join_request: {e}")
    return False

async def main():
    # Start userbot (await karo)
    await userbot.start()
    print("✅ Userbot started!")

    # Create application
    application = Application.builder()\
        .token(BotConfig.BOT_TOKEN)\
        .concurrent_updates(10)\
        .build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("data", data_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    print("🚀 Bot is starting...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import sys
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import nest_asyncio
    nest_asyncio.apply()

    asyncio.run(main())
