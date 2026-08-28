#!/usr/bin/env python3
import datetime
import logging
import os
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.helpers import mention_html
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler
from tinydb import TinyDB, Query

logging.basicConfig(level=logging.WARNING, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    filename="bot.log",
                    filemode="a")

load_dotenv()

TOKEN = os.getenv('ANTISPAM_TOKEN')
TARGET_CHAT = os.getenv('TARGET_GROUP_ID')
PRIMARY_ADMIN = os.getenv('PRIMARY_ADMIN') or ''
BACKUP_ADMIN = os.getenv('BACKUP_ADMIN') or ''
ADMIN_MENTIONS = f'@{PRIMARY_ADMIN} @{BACKUP_ADMIN}' if PRIMARY_ADMIN and BACKUP_ADMIN else ''

if not TOKEN:
    raise ValueError("ANTISPAM_TOKEN environment variable is not set")
if not TARGET_CHAT:
    raise ValueError("TARGET_GROUP_ID environment variable is not set")

def user_display_name(user):
    if user is None:
        return "Unknown"
    return f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

def user_link(user):
    if user is None:
        return ""
    if user.username:
        return f"https://t.me/{user.username}"
    return f"tg://user?id={user.id}"

class DeleteCallbackData:
    def __init__(self, chat_id, message_id, user_id, user_name, update_message_id):
        self.ci = chat_id
        self.mi = message_id
        self.ui = user_id
        self.un = user_name
        self.umi = update_message_id

class ManualEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DeleteCallbackData):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

db_stat_file = "./statistics.json"
if not os.path.exists(db_stat_file):
    with open(db_stat_file, "w") as file:
        file.write("{}")
db_stat = TinyDB(db_stat_file)

Stats = Query()

async def show_stats(update, context):
    # Capturing the command arguments for time period
    period = 'all'
    if context.args:
        period = context.args[0]  # assuming the first argument is the period
    
    # Determining the start date based on the period
    now = datetime.datetime.now()
    if period == 'day':
        start_date = now - datetime.timedelta(days=1)
    elif period == '3days':
        start_date = now - datetime.timedelta(days=3)
    elif period == 'week':
        start_date = now - datetime.timedelta(days=7)
    elif period == 'month':
        start_date = now - datetime.timedelta(days=30)  # approximating a month
    elif period == 'quarter':
        start_date = now - datetime.timedelta(days=90)  # approximating a quarter
    else:
        start_date = None  # For all-time stats

    if start_date:
        # Filter bans based on the start date
        bans = db_stat.search((Stats.type == 'ban') & (Stats.timestamp.test(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") >= start_date)))
    else:
        # Get all ban records
        bans = db_stat.search(Stats.type == 'ban')
    
    total_bans = len(bans)

    # Constructing the message
    if total_bans > 0:
        message = f"Statistics for '{period}':\n\nTotal bans: {total_bans}"
    else:
        message = f"No bans recorded for the period '{period}'."
    
    # Replying to the message
    await update.message.reply_text(message)


async def report_manually(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        return

    reply_to_message = update.message.reply_to_message
    numeric_chat_id = reply_to_message.chat.id
    chat_id = str(numeric_chat_id).replace("-100", "")
    message_id = reply_to_message.message_id
    user = reply_to_message.from_user

    name = user_display_name(user)
    profile_link = user_link(user)
    chat_link = f"https://t.me/c/{chat_id}/{message_id}"

    callback_data = DeleteCallbackData(chat_id, message_id, user.id, name, update.message.message_id)
    callback_data_serialized = json.dumps(callback_data, cls=ManualEncoder)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Удалить", callback_data=callback_data_serialized)]
    ])

    header = "🥊 <b>Ручной бан:</b>"
    user_line = f"👤 <a href='{profile_link}'><b>{name}</b></a> (ID: {user.id})"
    footer = f"<a href='{chat_link}'>Открыть в чате</a>\n\n{ADMIN_MENTIONS}"

    if reply_to_message.text is not None:
        message_text = reply_to_message.text_html_urled
        text_message_content = f"{header}\n\n{user_line}\n\n{message_text}\n\n{footer}"
        await context.bot.send_message(
            chat_id=TARGET_CHAT,
            text=text_message_content,
            disable_web_page_preview=True,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        message_text = reply_to_message.caption_html_urled
        new_caption = f"{header}\n\n{user_line}\n\n{message_text}\n\n{footer}"
        await context.bot.copy_message(
            chat_id=TARGET_CHAT,
            from_chat_id=reply_to_message.chat_id,
            message_id=reply_to_message.message_id,
            caption=new_caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

async def button_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data_string = query.data
    callback_data = json.loads(data_string)
    chat_id_temp = callback_data.get('ci', 'DefaultCI')
    message_id = callback_data.get('mi', 0)
    user_id = callback_data.get('ui', 0)
    user_name = callback_data.get('un', 'Unknown')
    command_id = callback_data.get('umi', 0)
    chat_id=f"-100{chat_id_temp}"
    
    if command_id != message_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=command_id)

        except TelegramError as e:
            error_message = f"Возникла ошибка: {str(e)}"
            await query.message.reply_html(error_message, disable_web_page_preview=True)
            await query.edit_message_reply_markup(None)
        
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

        moderator = query.from_user
        moderator_display_name = user_display_name(moderator)
        moderator_link = user_link(moderator)
        banned_user_mention = mention_html(user_id, user_name)

        ban_report_message = f"<a href='{moderator_link}'><b>{moderator_display_name}</b></a> забанил {banned_user_mention} (ID: {user_id})"

        await query.message.reply_html(ban_report_message, disable_web_page_preview=True)
        await query.edit_message_reply_markup(None)
            
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_stat.insert({
            'type': 'ban',
            'method': 'manual',
            'timestamp': current_time
        })

    except TelegramError as e:
        # Handle error, send a custom message to the user if an error occurs
        error_message = f"Возникла ошибка: {str(e)}"
        await query.message.reply_html(error_message, disable_web_page_preview=True)
        await query.edit_message_reply_markup(None)

def main():
    print("I'm working")

    application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()
    application.add_handler(CallbackQueryHandler(button_delete))
    application.add_handler(CommandHandler("ban", report_manually))
    application.add_handler(CommandHandler("stats", show_stats))

    application.run_polling(allowed_updates=True)

if __name__ == '__main__':
    main()
