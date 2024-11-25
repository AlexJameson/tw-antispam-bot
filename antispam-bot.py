#!/usr/bin/env python3
import datetime
import logging
import os
import re
import json
import sys
import emoji
sys.path.append('/opt/homebrew/lib/python3.11/site-packages')
from is_spam_message import new_is_spam_message, has_critical_patterns, has_mixed_words
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from spam_tokens import REGULAR_TOKENS, FINCRYPTO_TOKENS, ADULT_TOKENS, BETTING_TOKENS
from tinydb import TinyDB, Query

logging.basicConfig(level=logging.WARNING, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    filename="bot.log",
                    filemode="a")

load_dotenv()

TOKEN = os.getenv('ANTISPAM_TOKEN')
TARGET_CHAT = os.getenv('TARGET_GROUP_ID')
PRIMARY_ADMIN = os.getenv('PRIMARY_ADMIN')
BACKUP_ADMIN = os.getenv('BACKUP_ADMIN')

class DeleteCallbackData:
    def __init__(self, chat_id, message_id, user_id, update_message_id):
        self.ci = chat_id
        self.mi = message_id
        self.ui = user_id
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
    
    # Aggregate results by 'method'
    ban_count = {}
    for ban in bans:
        method = ban['method']
        if method in ban_count:
            ban_count[method] += 1
        else:
            ban_count[method] = 1
            
    total_bans = len(bans)
    auto_bans = ban_count.get('auto', 0)

    # Constructing the message
    if total_bans > 0:
        auto_ban_rate = (auto_bans / total_bans) * 100
        message = f"Statistics for '{period}':\n\nTotal bans: {total_bans}\nAutomatically banned: {auto_bans}\nAuto ban rate: {int(auto_ban_rate)}%"
    else:
        message = f"No bans recorded for the period '{period}'."
    
    # Replying to the message
    await update.message.reply_text(message)


async def check_repeated_emojis(text):
    
    # Convert emoji to aliases for easier handling
    emoji_text = emoji.demojize(text)
    
    # Pattern to match repeated emoji aliases
    pattern = r'(:[^:]+:)\1{3,}'
    
    matches = re.findall(pattern, emoji_text)
    
    if matches:
        # Convert matches back to emojis for display
        emoji_matches = [emoji.emojize(m) for m in matches]
        return '|'.join(emoji_matches)
    else:
        return None

def check_hashtags(text):
    
    # Pattern to match hashtags
    hashtag_pattern = r'#\w+'
    
    # Find all hashtags in the message
    hashtags = re.findall(hashtag_pattern, text)
    
    if hashtags:
        return ', '.join(hashtags)
    else:
        return None

async def report_manually(update: Update, context: CallbackContext):  
    if update.message.reply_to_message:
        reply_to_message = update.message.reply_to_message
        numeric_chat_id = reply_to_message.chat.id
        chat_id = str(numeric_chat_id).replace("-100", "")
        message_id = reply_to_message.message_id
        user = reply_to_message.from_user
        if user.last_name is not None:
            user_display_name = f"{user.first_name} {user.last_name}"
        elif user.last_name is None:
            user_display_name = f"{user.first_name}"
        user_link = f"https://t.me/{user.username}"
        link = f"https://t.me/c/{chat_id}/{message_id}"
        callback_data = DeleteCallbackData(chat_id, message_id, user.id, update.message.message_id)
        callback_data_serialized = json.dumps(callback_data, cls=ManualEncoder)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Удалить", callback_data=callback_data_serialized)]
        ])
        
        words = reply_to_message.text or reply_to_message.caption

        reg_pattern = '|'.join(map(re.escape, REGULAR_TOKENS))
        crypto_pattern = '|'.join(map(re.escape, FINCRYPTO_TOKENS))
        regular_patterns = re.findall(reg_pattern, words)
        num_regular = len(regular_patterns)
        crypto_patterns = re.findall(crypto_pattern, words)
        num_crypto = len(crypto_patterns)
		    
        mixed_words = has_mixed_words(words)
        num_mixed = len(mixed_words)        

        repeated_emojis = await check_repeated_emojis(words)
        repeated_emojis_bool = repeated_emojis is not None
        
        has_hashtags = check_hashtags(words)
    
        verdict = f"""
<b>Обычные токены:</b> {num_regular}; [ {', '.join(regular_patterns)} ]
<b>Финансы/крипто:</b> {num_crypto}; [ {', '.join(crypto_patterns)} ]
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>4+ одинаковых эмодзи подряд:</b> {repeated_emojis_bool}
<b>Хештеги:</b> {has_hashtags}
        """
        if reply_to_message.text is not None:
            message_text = reply_to_message.text_html_urled
            text_message_content = f"🥊 <b>Ручной бан:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
            await context.bot.send_message(chat_id=TARGET_CHAT,
                                    text=text_message_content,
                                    disable_web_page_preview=True,
                                    parse_mode="HTML",
                                    reply_markup=keyboard)
        elif reply_to_message.text is None:
            message_text = reply_to_message.caption_html_urled
            new_caption = f"🥊 <b>Ручной бан:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
            await context.bot.copy_message(chat_id=TARGET_CHAT,
                                    from_chat_id=reply_to_message.chat_id,
                                    message_id=reply_to_message.message_id,
                                    caption=new_caption,
                                    parse_mode="HTML",
                                    reply_markup=keyboard)
    else:
        return

async def button_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data_string = query.data
    callback_data = json.loads(data_string)
    chat_id_temp = callback_data.get('ci', 'DefaultCI')
    message_id = callback_data.get('mi', 0)
    user_id = callback_data.get('ui', 0)
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
        moderator_display_name = f"{moderator.first_name} {moderator.last_name or ''}".strip()
        moderator_link = f"https://t.me/{moderator.username}"
        ban_report_message = f"""
        <a href='{moderator_link}'><b>{moderator_display_name}</b></a> забанил пользователя с ID {user_id}
        """
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

async def check_automatically(update: Update, context: CallbackContext):
    message = update.message
    numeric_chat_id = message.chat.id
    chat_id = str(numeric_chat_id).replace("-100", "")
    message_id = message.message_id
    user = message.from_user
    if user.last_name is not None:
        user_display_name = f"{user.first_name} {user.last_name}"
    elif user.last_name is None:
        user_display_name = f"{user.first_name}"
    user_link = f"https://t.me/{user.username}"

    if message.text is None and message.caption is None or (message.story is not None or message.video_note is not None):
        return

    words = message.text or message.caption
        
    reg_pattern = '|'.join(map(re.escape, REGULAR_TOKENS))
    crypto_pattern = '|'.join(map(re.escape, FINCRYPTO_TOKENS))
    betting_pattern = '|'.join(map(re.escape, BETTING_TOKENS))
    regular_patterns = re.findall(reg_pattern, words)
    num_regular = len(regular_patterns)
    crypto_patterns = re.findall(crypto_pattern, words)
    num_crypto = len(crypto_patterns)
    betting_patterns = re.findall(betting_pattern, words)
    num_betting = len(betting_patterns)
    
    mixed_words = has_mixed_words(words)
    num_mixed = len(mixed_words)
    
    spam_tokens = new_is_spam_message(words)
    crit_tokens = has_critical_patterns(words)
    crit_tokens_bool = crit_tokens is not None
    if crit_tokens:
        crit_tokens_string = crit_tokens.group()
    else: crit_tokens_string = None
    
    emoji_num = sum(1 for _ in emoji.emoji_list(words))
    if emoji_num > 12:
        emoji_critical_num = True
    else:
        emoji_critical_num = False
        
    repeated_emojis = await check_repeated_emojis(words)
    repeated_emojis_bool = repeated_emojis is not None

    is_reply = message.reply_to_message is not None
    
    has_hashtags = check_hashtags(words)
    has_hashtags_bool = has_hashtags is not None

    # Ban automatically
    if (len(words) < 530 and is_reply is False and has_hashtags_bool is False) and (("✅✅✅✅" in words or "✅✅✅✅" in words.replace('\U0001F537', '✅') or crit_tokens_bool is True or num_mixed > 1 or spam_tokens is not None or emoji_critical_num is True)):
        verdict = f"""
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>Основная регулярка:</b> {spam_tokens is not None}
<b>Критические токены:</b> {crit_tokens_string}
<b>Более 12 эмодзи:</b> {emoji_critical_num}
<b>4+ одинаковых эмодзи подряд:</b> {repeated_emojis_bool}
            """
        if message.text is not None:
            message_text = message.text_html_urled
            text_message_content = f"🎯 <b>Автоматический бан:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"

            try:
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                await context.bot.ban_chat_member(chat_id=message.chat_id, user_id=message.from_user.id)
                await context.bot.send_message(chat_id=TARGET_CHAT,
                                text=text_message_content,
                                disable_web_page_preview=True,
                                parse_mode="HTML")
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_stat.insert({
                    'type': 'ban',
                    'method': 'auto',
                    'timestamp': current_time
                })

                return

            except TelegramError as e:
                # Handle error, send a custom message if an error occurs
                error_message = f"Возникла ошибка при автоматическом бане: {str(e)}\n\n<a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"
                await context.bot.send_message(chat_id=TARGET_CHAT,
                                text=error_message,
                                disable_web_page_preview=True,
                                parse_mode="HTML")
                
                return

        elif message.text is None:
            message_text = message.caption_html_urled
            caption_content = f"🎯 <b>Автоматический бан:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"
            
            try:
                await context.bot.copy_message(chat_id=TARGET_CHAT,
                                from_chat_id=message.chat_id,
                                message_id=message.message_id,
                                caption=caption_content,
                                parse_mode="HTML")
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                await context.bot.ban_chat_member(chat_id=message.chat_id, user_id=message.from_user.id)
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_stat.insert({
                    'type': 'ban',
                    'method': 'auto',
                    'timestamp': current_time
                })

                return

            except TelegramError as e:
                # Handle error, send a custom message if an error occurs
                error_message = f"Возникла ошибка при автоматическом бане: {str(e)}\n\n<a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"
                await context.bot.copy_message(chat_id=TARGET_CHAT,
                                from_chat_id=message.chat_id,
                                message_id=message.message_id,
                                caption=error_message,
                                parse_mode="HTML")
                return

    # suggestion mode
    if (num_regular > 1 or num_crypto > 0 or num_betting > 0 or num_mixed > 1 or repeated_emojis_bool is True) and (len(words) < 530 and has_hashtags_bool is False):

        verdict = f"""
<b>Обычные токены:</b> {num_regular}; [ {', '.join(regular_patterns)} ]
<b>Финансы/крипто:</b> {num_crypto}; [ {', '.join(crypto_patterns)} ]
<b>Гемблинг:</b> {num_betting}; [ {', '.join(betting_patterns)} ]
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>4+ одинаковых эмодзи подряд:</b> {repeated_emojis}
<b>Хештеги:</b> {has_hashtags}
        """
        callback_data = DeleteCallbackData(chat_id, message_id, user.id, update.message.message_id)
        callback_data_serialized = json.dumps(callback_data, cls=ManualEncoder)
        keyboard = [
            [InlineKeyboardButton("Удалить", callback_data=callback_data_serialized),
             InlineKeyboardButton("Пропустить", callback_data='Declined')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if message.text is not None:
            message_text = message.text_html_urled
            text_message_content = f"🔎 <b>Подозрение на спам:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>"
            await context.bot.send_message(chat_id=TARGET_CHAT,
                                text=text_message_content,
                                disable_web_page_preview=True,
                                parse_mode="HTML",
                                reply_markup=reply_markup)
        elif message.text is None:
            message_text = message.caption_html_urled
            new_caption = f"🔎 <b>Подозрение на спам:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n"
            await context.bot.copy_message(chat_id=TARGET_CHAT,
                                from_chat_id=message.chat_id,
                                message_id=message.message_id,
                                caption=new_caption,
                                parse_mode="HTML",
                                reply_markup=reply_markup)

async def auto_ignore_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_reply_markup(None)

    except TelegramError as e:
        error_message = f"Возникла ошибка: {str(e)}"
        await query.message.reply_html(error_message, disable_web_page_preview=True)
        await query.edit_message_reply_markup(None)

async def delete_stories_and_video_notes(update: Update, context: CallbackContext):
    message = update.message
    if message.story or message.video_note:
        try:
            await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
            print(f"Deleted a story from {message.from_user.id}")
        except TelegramError as e:
            print(f"Возникла ошибка при удалении истории: {str(e)}")

def main():
    print("I'm working")

    application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()
    application.add_handler(CallbackQueryHandler(auto_ignore_button, pattern="Declined"))
    application.add_handler(CallbackQueryHandler(button_delete))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.STORY & ~filters.VIDEO_NOTE, check_automatically))
    application.add_handler(CommandHandler("ban", report_manually))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(MessageHandler(filters.FORWARDED & filters.STORY & filters.VIDEO_NOTE, delete_stories_and_video_notes))

    application.run_polling(allowed_updates=True)

if __name__ == '__main__':
    main()
