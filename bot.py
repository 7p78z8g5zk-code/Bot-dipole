import logging
import os
import requests
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
PHP_API_URL = os.getenv("PHP_API_URL", "http://127.0.0.1:8000/movies.php")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {user_name}! 🎬\n\nSend me any movie or anime name to search. No commands needed!\n\nAdmins can use /add Movie Name | https://link"
    )

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Better luck next time 😔"
        )
        return

    text = update.message.text[5:].strip() # Remove /add

    if "|" not in text:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /add Movie Name | https://link"
        )
        return

    name, link = [part.strip() for part in text.split("|", 1)]

    try:
        logging.info(f"Adding movie: {name} | {link}")
        response = requests.post(PHP_API_URL, data={'action': 'add', 'movie': name, 'link': link}, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ {data.get('message', 'Done')}"
                )
            except:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"API Error: {response.text}")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Server Error: {response.status_code}")
    except Exception as e:
        logging.error(f"Error adding movie: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Internal error.")

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_name = update.message.text.strip()
    if not movie_name or movie_name.startswith('/'): return

    user_first_name = update.effective_user.first_name

    try:
        response = requests.get(PHP_API_URL, params={'search': movie_name}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'found':
                link = data.get('link')
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"DRACXONgaming aapka link yeh raha 🔗\n{link}"
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Better luck next time 😔"
                )
        else:
            logging.error(f"Search API Error: {response.status_code}")
    except Exception as e:
        logging.error(f"Error searching movie: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN:
        print("BOT_TOKEN is missing!")
        exit(1)
        
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add', add_movie))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_movie))
    
    print("Bot is polling...")
    application.run_polling()
