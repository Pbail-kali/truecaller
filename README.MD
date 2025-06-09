# Truecaller Style Telegram Bot Setup Guide

## 🚀 Features

✅ **Phone Number Lookup** - Get detailed information about any Indian phone number
✅ **Truecaller Integration** - Fetch names and caller ID data
✅ **Number Validation** - Check if numbers are valid and active
✅ **Force Subscription** - Users must join channels before using
✅ **Stylized Text** - All text uses Unicode small caps styling
✅ **MongoDB Integration** - All data is saved to database
✅ **Admin Commands** - Statistics, broadcast, and data export
✅ **Access Key Rotation** - Automatic rotation of API keys
✅ **Contact Buttons** - Direct WhatsApp and Telegram links

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **MongoDB** database (local or cloud like MongoDB Atlas)
3. **Telegram Bot Token** from @BotFather
4. **API Access Keys** for phone validation service

## 🔧 Installation Steps

### Step 1: Clone and Setup
```bash
# Create project directory
mkdir truecaller-bot
cd truecaller-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Choose a name for your bot
4. Choose a username (must end with 'bot')
5. Copy the bot token

### Step 3: Setup MongoDB
#### Option A: MongoDB Atlas (Recommended)
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create free account
3. Create new cluster
4. Get connection string
5. Replace `<password>` and `<username>` in connection string

#### Option B: Local MongoDB
1. Install MongoDB on your system
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017/`

### Step 4: Configure Bot
1. Open `main.py`
2. Replace configuration values:

```python
# Bot Configuration
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
MONGO_URI = "YOUR_MONGODB_CONNECTION_STRING"  # Replace with your MongoDB URI
OWNER_ID = 123456789  # Replace with your Telegram user ID

# Force subscription channels
FORCE_SUB_CHANNELS = [
    {"name": "Channel 1", "id": "@your_channel1", "url": "https://t.me/your_channel1"},
    {"name": "Channel 2", "id": "@your_channel2", "url": "https://t.me/your_channel2"}
]
```

### Step 5: Setup Access Keys
1. Edit `access_keys.txt` file
2. Add your API access keys (one per line):

```text
your_second_access_key_here
your_third_access_key_here
your_fourth_access_key_here
your_fifth_access_key_here
```

### Step 6: Get Your Telegram User ID
1. Message @userinfobot on Telegram
2. Copy your user ID
3. Replace `OWNER_ID` in the code

### Step 7: Setup Force Subscription Channels
1. Create Telegram channels
2. Add your bot as admin to both channels
3. Get channel usernames (e.g., @mychannel)
4. Update `FORCE_SUB_CHANNELS` in the code

## 🏃‍♂️ Running the Bot

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the bot
python main.py
```

## 🎛️ Admin Commands

### `/stats` - View Statistics
Shows:
- Total users
- Today's queries
- Access key information
- Current key index

### `/broadcast <message>` - Send Message to All Users
Example: `/broadcast 🎉 Bot updated with new features!`

### `/data` - Export All Data
Exports users and queries data to Excel file

## 🔑 API Information

### API 1: Truecaller Lookup
- **URL**: `https://xxxxxxxxx.xxx/xxxx/xxx/xxx/xxxxx?q={phone_number}`
- **Purpose**: Get caller name and ID information
- **Rate Limit**: No specific limit mentioned

### API 2: Phone Validation
- **URL**: `http://xxxxxxxxx.xxx/xxx/validate`
- **Purpose**: Validate phone numbers and get detailed info
- **Rate Limit**: 1000000000 requests per access key per month
- **Auto-rotation**: Bot automatically switches keys when limit reached

## 📱 Phone Number Format

The bot accepts Indian phone numbers in these formats:
- `9876543210` (without country code)
- `+919876543210` (with country code)
- `919876543210` (with country code, no +)

**Validation Rules:**
- Must be exactly 10 digits (after removing country code)
- Must start with 6, 7, 8, or 9
- Country code +91 is automatically added if missing

## 🎨 Text Styling

All bot text uses Unicode small caps for a unique look:
- Normal: `Hello World`
- Stylized: `ʜᴇʟʟᴏ ᴡᴏʀʟᴅ`

## 📊 Database Structure

### Users Collection
```json
{
  "user_id": 123456789,
  "username": "john_doe",
  "name": "John Doe",
  "first_seen": "2025-01-01T10:00:00Z",
  "last_seen": "2025-01-01T15:30:00Z",
  "query_count": 25
}
```

### Queries Collection
```json
{
  "user_id": 123456789,
  "phone_number": "9876543210",
  "result": {
    "truecaller": {...},
    "validation": {...}
  },
  "timestamp": "2025-01-01T15:30:00Z"
}
```

### Stats Collection
```json
{
  "type": "daily",
  "date": "2025-01-01",
  "queries": 150,
  "users": 45
}
```

## 🔒 Security Features

1. **Owner-only Commands**: Admin commands are restricted to owner ID
2. **Force Subscription**: Users must join channels before using
3. **Input Validation**: All phone numbers are validated before processing
4. **Error Handling**: Comprehensive error handling for API failures
5. **Rate Limiting**: Automatic API key rotation to prevent abuse

## 🐛 Troubleshooting

### Common Issues:

1. **Bot not responding**
   - Check bot token is correct
   - Ensure bot is not blocked by user
   - Check internet connection

2. **Database connection failed**
   - Verify MongoDB URI
   - Check MongoDB service is running
   - Ensure database user has proper permissions

3. **API not working**
   - Check access keys are valid
   - Verify API endpoints are accessible
   - Check rate limits

4. **Force subscription not working**
   - Ensure bot is admin in channels
   - Check channel usernames are correct
   - Verify channels are public or bot has access

### Debug Mode
Add this to enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Scaling Tips

1. **Multiple Access Keys**: Add more keys to `access_keys.txt` for higher limits
2. **Database Indexing**: Create indexes on frequently queried fields
3. **Caching**: Implement Redis caching for frequently requested numbers
4. **Load Balancing**: Use multiple bot instances with same database
5. **Monitoring**: Add monitoring for API response times and error rates

## 🔄 Updates and Maintenance

### Regular Tasks:
- Monitor API key usage
- Clean up old query data
- Update access keys when expired
- Backup database regularly
- Monitor bot performance

### Adding New Features:
- Update database schema if needed
- Add new command handlers
- Update help text and documentation
- Test thoroughly before deployment

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Review error logs
3. Test individual components
4. Contact support channel: @IND_BOTS

## 🎯 Usage Tips

1. **For Users**: Send phone numbers in format `9876543210`
2. **For Admins**: Use `/stats` regularly to monitor usage
3. **For Scaling**: Monitor API usage and add keys as needed
4. **For Security**: Regularly update access keys and monitor for abuse

---

**Note**: This bot is designed for educational and legitimate purposes only. Always respect privacy laws and terms of service of the APIs used.
