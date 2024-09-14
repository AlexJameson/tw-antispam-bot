#!/usr/bin/env python3
from datetime import datetime
import logging
import os
import re
import json
import sys
sys.path.append('/opt/homebrew/lib/python3.11/site-packages')
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

if not db_stat.search(Stats.type == 'statistics'):
    db_stat.insert({'type': 'statistics', 'banned_total': 0, 'banned_auto': 0, 'ignored': 0, 'checked_automatically': 0})

async def show_stats(update: Update, context: CallbackContext):
    stats_list = db_stat.search(Stats.type == 'statistics')
    if stats_list:
        stats = stats_list[0]
        auto_ban_rate = int(stats['banned_auto']) / int(stats['banned_total']) * 100
        message = f"Starting from Sep 15, 2024:\n\nAutomatically checked: {stats['checked_automatically']}\nTotal banned (including auto): {stats['banned_total']}\nAutomatically banned: {stats['banned_auto']}\nAuto ban rate: {int(auto_ban_rate)}%"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No statistics found.")

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
        adult_pattern = '|'.join(map(re.escape, ADULT_TOKENS))
        betting_pattern = '|'.join(map(re.escape, BETTING_TOKENS))
        regular_patterns = re.findall(reg_pattern, words)
        num_regular = len(regular_patterns)
        crypto_patterns = re.findall(crypto_pattern, words)
        num_crypto = len(crypto_patterns)
        adult_patterns = re.findall(adult_pattern, words)
        num_adult = len(adult_patterns)
        betting_patterns = re.findall(betting_pattern, words)
        num_betting = len(betting_patterns)
		    
        mixed_words = find_mixed_words(words)
        num_mixed = len(mixed_words)
    
        verdict = f"""
<b>Обычные токены:</b> {num_regular}; [ {', '.join(regular_patterns)} ]
<b>Финансы/крипто:</b> {num_crypto}; [ {', '.join(crypto_patterns)} ]
<b>18+:</b> {num_adult}; [ {', '.join(adult_patterns)} ]
<b>Гемблинг:</b> {num_betting}; [ {', '.join(betting_patterns)} ]
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
        """
        if reply_to_message.text is not None:
            message_text = reply_to_message.text_html_urled
            text_message_content = f"👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
            await context.bot.send_message(chat_id=TARGET_CHAT,
                                    text=text_message_content,
                                    disable_web_page_preview=True,
                                    parse_mode="HTML",
                                    reply_markup=keyboard)
        elif reply_to_message.text is None:
            message_text = reply_to_message.caption_html_urled
            new_caption = f"👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
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
        
        stats_list = db_stat.search(Stats.type == 'statistics')
        if stats_list:
            stats = stats_list[0]
            db_stat.update({'banned_total': stats['banned_total'] + 1}, Stats.type == 'statistics')

    except TelegramError as e:
        # Handle error, send a custom message to the user if an error occurs
        error_message = f"Возникла ошибка: {str(e)}"
        await query.message.reply_html(error_message, disable_web_page_preview=True)
        await query.edit_message_reply_markup(None)

def find_mixed_words(text):
    regex = r"\b(?=[^\s_-]*[а-яА-ЯёЁ]+)[^\s_-]*[^-\sа-яА-ЯёЁ\W\d_]+[^\s_-]*\b"
	 # old regex to only find words containing both Cyrillic and non-Cyrillic characters
    # regex = r"\b(?=\w*[а-яА-Я]+)(?=\w*[^-_\sа-яА-Я\W]+)\w+\b"

    matches = re.findall(regex, text)
    return matches

def is_spam_message(text):
    # Extended regex explained:
    # - (ищу людей|ищу партнеров|ищу партнёров) matches any of the starting phrases.
    # - .*? means any characters (non-greedily matched) following the starting phrase.
    # - The group (?: ... | ... | ...) contains different phrases to match later in the message.
    spam_pattern = re.compile(
        r"(набираю\s+команду|набираем\s+команду|ищу\s+людей|ищем\s+людей|ищу\s+партнеров|ищу\s+партнёров).*?("
        r"в\s+команду|для\s+заработка|личные\s+сообщения|в лс|л\.с|л\. с|"
        r"доход|доходы|дохода|заработок|заработка|прибыль|прибыли|занятость"
        r")",
        re.IGNORECASE | re.DOTALL
    )
    return spam_pattern.search(text)

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
    link = f"https://t.me/c/{chat_id}/{message_id}"

    words = message.text or message.caption
        
    reg_pattern = '|'.join(map(re.escape, REGULAR_TOKENS))
    crypto_pattern = '|'.join(map(re.escape, FINCRYPTO_TOKENS))
    adult_pattern = '|'.join(map(re.escape, ADULT_TOKENS))
    betting_pattern = '|'.join(map(re.escape, BETTING_TOKENS))
    regular_patterns = re.findall(reg_pattern, words)
    num_regular = len(regular_patterns)
    crypto_patterns = re.findall(crypto_pattern, words)
    num_crypto = len(crypto_patterns)
    adult_patterns = re.findall(adult_pattern, words)
    num_adult = len(adult_patterns)
    betting_patterns = re.findall(betting_pattern, words)
    num_betting = len(betting_patterns)
    
    mixed_words = find_mixed_words(words)
    num_mixed = len(mixed_words)
    
    spam_tokens = is_spam_message(words)
    if spam_tokens:
        spam_tokens_string = spam_tokens.group()
    else: spam_tokens_string = None

    stats_list = db_stat.search(Stats.type == 'statistics')
    if stats_list:
        stats = stats_list[0]
        db_stat.update({'checked_automatically': stats['checked_automatically'] + 1}, Stats.type == 'statistics')

    # Ban automatically
    if (len(words) < 400 and not "#вакансия" in words) and (("✅✅✅✅" in words or "✅✅✅✅" in words.replace('\U0001F537', '✅') or num_betting > 1 or num_mixed > 3 or spam_tokens is not None)):
        verdict = f"""
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
<b>Гемблинг:</b> {num_betting}; [ {', '.join(betting_patterns)} ]
<b>Новая регулярка:</b> {spam_tokens is not None} | {spam_tokens_string}
            """
        if message.text is not None:
            message_text = message.text_html_urled
            text_message_content = f"<b>╭∩╮( •̀_•́ )╭∩╮ Автоматический бан:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"

            try:
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                await context.bot.ban_chat_member(chat_id=message.chat_id, user_id=message.from_user.id)
                await context.bot.send_message(chat_id=TARGET_CHAT,
                                text=text_message_content,
                                disable_web_page_preview=True,
                                parse_mode="HTML")
                db_stat.update({'banned_auto': stats['banned_auto'] + 1, 'banned_total': stats['banned_total'] + 1}, Stats.type == 'statistics')
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
            text_message_content = f"<b>!!! Lord Protector автоматически забанил пользователя !!!</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}"
            new_caption = f"{text_message_content}\n<a href='{link}'>Открыть в чате</a>\n\n"
            
            try:
                await context.bot.ban_chat_member(chat_id=message.chat_id, user_id=message.from_user.id)
                await context.bot.copy_message(chat_id=TARGET_CHAT,
                                from_chat_id=message.chat_id,
                                message_id=message.message_id,
                                caption=new_caption,
                                parse_mode="HTML")
                await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
                db_stat.update({'banned_auto': stats['banned_auto'] + 1, 'banned_total': stats['banned_total'] + 1}, Stats.type == 'statistics')
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

    if (num_regular > 1 or num_crypto > 0 or num_adult > 0 or num_betting > 0) and (len(words) < 400):
        if "#вакансия" in words:
            return
        verdict = f"""
<b>Обычные токены:</b> {num_regular}; [ {', '.join(regular_patterns)} ]
<b>Финансы/крипто:</b> {num_crypto}; [ {', '.join(crypto_patterns)} ]
<b>18+:</b> {num_adult}; [ {', '.join(adult_patterns)} ]
<b>Гемблинг:</b> {num_betting}; [ {', '.join(betting_patterns)} ]
<b>Смешанные слова:</b> {num_mixed}; [ {', '.join(mixed_words)} ]
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
            text_message_content = f"<b>Подозрение на спам:</b>\n\n👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>"
            await context.bot.send_message(chat_id=TARGET_CHAT,
                                text=text_message_content,
                                disable_web_page_preview=True,
                                parse_mode="HTML",
                                reply_markup=reply_markup)
        elif message.text is None:
            message_text = message.caption_html_urled
            new_caption = f"👤 <a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n{verdict}\n<a href='{link}'>Открыть в чате</a>\n\n"
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
        
        stats_list = db_stat.search(Stats.type == 'statistics')
        if stats_list:
            stats = stats_list[0]
            db_stat.update({'ignored': stats['ignored'] + 1}, Stats.type == 'statistics')

    except TelegramError as e:
        error_message = f"Возникла ошибка: {str(e)}"
        await query.message.reply_html(error_message, disable_web_page_preview=True)
        await query.edit_message_reply_markup(None)

def main():
    print("I'm working")

    application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()
    application.add_handler(CallbackQueryHandler(auto_ignore_button, pattern="Declined"))
    application.add_handler(CallbackQueryHandler(button_delete))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_automatically))
    application.add_handler(CommandHandler("ban", report_manually))
    application.add_handler(CommandHandler("stats", show_stats))

    application.run_polling()

if __name__ == '__main__':
    main()
