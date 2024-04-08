#!/usr/bin/env python3
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import ApplicationBuilder, CallbackContext, MessageHandler, filters, CommandHandler, CallbackQueryHandler

logging.basicConfig(level=logging.WARNING, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    filename="bot.log",
                    filemode="a")

load_dotenv()

TOKEN = os.getenv('ANTISPAM_TOKEN')
TARGET_CHAT = os.getenv('TARGET_GROUP_ID')
PRIMARY_ADMIN = os.getenv('PRIMARY_ADMIN')
BACKUP_ADMIN = os.getenv('BACKUP_ADMIN')

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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Delete", callback_data=f"{chat_id}, {message_id}, {user.id}, {update.message.message_id}")]
        ])

        spam_indicator = 0
        if reply_to_message.text is not None:
            words = reply_to_message.text.split()
            message_text = reply_to_message.text_html_urled
            text_message_content = f"<a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n\n<a href='{link}'>Go to chat</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
            await context.bot.send_message(chat_id=TARGET_CHAT,
                                    text=text_message_content,
                                    disable_web_page_preview=True,
                                    parse_mode="HTML",
                                    reply_markup=keyboard)
        if reply_to_message.text is None:
            words = reply_to_message.caption.split()
            message_text = reply_to_message.caption_html_urled
            new_caption = f"<a href='{user_link}'><b>{user_display_name}</b></a>\n\n{message_text}\n\n<a href='{link}'>Go to chat</a>\n\n@{PRIMARY_ADMIN} @{BACKUP_ADMIN}"
            await context.bot.copy_message(chat_id=TARGET_CHAT,
                                    from_chat_id=reply_to_message.chat_id,
                                    message_id=reply_to_message.message_id,
                                    caption=new_caption,
                                    parse_mode="HTML",
                                    reply_markup=keyboard)
    else:
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Reply to a message with the /ban command."
        )

async def button_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    callback_data = query.data.split(',')
    message_id = callback_data[1].strip()
    command_id = callback_data[3].strip()
    chat_id_temp = str(callback_data[0])
    chat_id=f"-100{chat_id_temp}"
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    await context.bot.delete_message(chat_id=chat_id, message_id=command_id)
    user_id = callback_data[2].strip()
    # await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
    user = query.from_user
    if user.last_name is not None:
       user_display_name = f"{user.first_name} {user.last_name}"
    elif user.last_name is None:
       user_display_name = f"{user.first_name}"
    user_link = f"https://t.me/{user.username}"
    await query.message.reply_html(f"<a href='{user_link}'><b>{user_display_name}</b></a> banned the user with the ID {user_id}", disable_web_page_preview=True)


def main():
    print("I'm working")

    application = ApplicationBuilder().token(TOKEN).build()

    delete_handler = CallbackQueryHandler(button_delete)
    application.add_handler(delete_handler)

    application.add_handler(CommandHandler("ban", report_manually))
    application.run_polling()

if __name__ == '__main__':
    main()
