import telebot
import logging
import os
from config import Config
from quotes import QuoteManager
from music import MusicManager
from photos import PhotoManager
from tiktok import TikTokManager
from telebot import types


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Initialize bot
bot = telebot.TeleBot(Config.BOT_TOKEN)

# Initialize managers
quote_manager = QuoteManager(bot)
music_manager = MusicManager(bot)
photo_manager = PhotoManager(bot)
tiktok_manager = TikTokManager(bot)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
🤖 *PororokzBot* — многофункциональный Telegram-бот

📝 *Цитаты:*
/quote, /q — Создать цитату (тип 1)
/quote2, /q2 — Создать цитату (тип 2, с emoji)
/my_quote \\[номер\\], /m_q \\[номер\\] — Ваша цитата
/her_quote \\[номер\\], /h_q \\[номер\\] — Цитата пользователя (ответ)
/chat_quote \\[номер\\], /c_q \\[номер\\] — Цитата из чата
/mchat_quote \\[номер\\], /mc_q \\[номер\\] — Ваша цитата из чата
/all_quote — Случайная цитата
/delete_quote ID, /d_q ID — Удалить цитату

🎵 *Музыка:*
/myz название — Найти и скачать музыку

📷 *Фотографии:*
/save_photo, /save_scan — Сохранить фото (ответ)
/photos, /scans — Ваши сохранённые фото

📱 *TikTok:*
Просто отправьте ссылку на TikTok-видео для скачивания
/tiktok — Случайное TikTok видео

Используйте @PororokzBot в inline-режиме для цитат и фото в любом чате!
"""

    # Кнопка "Добавить в группу"
    add_group_btn = types.InlineKeyboardMarkup()
    add_group_btn.add(
        types.InlineKeyboardButton("➕ Добавить бота в группу", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    )

    bot.reply_to(message, welcome_text, reply_markup=add_group_btn)

# Quote commands
@bot.message_handler(commands=['quote', 'q'])
def handle_quote(message):
    quote_manager.handle_quote_command(message, quote_type=1)

@bot.message_handler(commands=['quote2', 'q2'])
def handle_quote2(message):
    quote_manager.handle_quote_command(message, quote_type=2)

@bot.message_handler(commands=['my_quote', 'm_q'])
def handle_my_quote(message):
    try:
        parts = message.text.split()
        quote_number = int(parts[1]) if len(parts) > 1 else None
        quote_manager.handle_my_quote(message, quote_number)
    except (ValueError, IndexError):
        quote_manager.handle_my_quote(message)

    
@bot.callback_query_handler(func=lambda call: call.data.startswith("music_choose_"))
def handle_music_choice(call):
    callback_id = call.data
    data = music_manager._search_cache.get(callback_id)

    if not data:
        bot.answer_callback_query(call.id, "❌ Бұл сілтеме ескірген.")
        return

    info = data['info']
    music_manager.download_from_info(call.message, info)

    
 
@bot.message_handler(commands=['her_quote', 'h_q'])
def handle_her_quote(message):
    # This would be similar to my_quote but for the replied user
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Ответьте на сообщение пользователя!")
        return
    # Implementation would be similar to my_quote
    bot.reply_to(message, "🚧 Функция в разработке!")

@bot.message_handler(commands=['chat_quote', 'c_q'])
def handle_chat_quote(message):
    try:
        parts = message.text.split()
        quote_number = int(parts[1]) if len(parts) > 1 else None
        quote_manager.handle_chat_quote(message, quote_number)
    except (ValueError, IndexError):
        quote_manager.handle_chat_quote(message)

@bot.message_handler(commands=['mchat_quote', 'mc_q'])
def handle_mchat_quote(message):
    # User's quotes from current chat
    bot.reply_to(message, "🚧 Функция в разработке!")

@bot.message_handler(commands=['all_quote'])
def handle_all_quote(message):
    quote_manager.handle_all_quote(message)

@bot.message_handler(commands=['delete_quote', 'd_q'])
def handle_delete_quote_cmd(message):
    try:
        parts = message.text.split()
        if len(parts) > 1:
            quote_id = int(parts[1])
            # This would call quote_manager.handle_delete_quote with proper parameters
            bot.reply_to(message, "🚧 Используйте кнопку удаления под цитатой!")
        else:
            bot.reply_to(message, "❌ Укажите ID цитаты!")
    except ValueError:
        bot.reply_to(message, "❌ Неверный ID цитаты!")

# Music commands
@bot.message_handler(commands=['myz'])
def handle_music_search(message):
    query = message.text[len('/myz'):].strip()
    if not query:
        bot.reply_to(message, "❗ Введите название трека. Пример: `/myz либо Муз Shape of You`", parse_mode="Markdown")
        return
    music_manager.search_music_list(message, query)
    
@bot.message_handler(func=lambda message: message.text.lower().startswith('муз '))
def handle_myz_text(message):
    query = message.text[4:].strip()  # "Муз " сөзінен кейін бәрі
    if not query:
        bot.reply_to(message, "🎵 Қандай ән керек екенін жазыңыз. Мысалы: `Муз Ерке Есмахан`", parse_mode='Markdown')
        return
    music_manager.show_music_options(message, query)


# Photo commands
@bot.message_handler(commands=['save_photo', 'save_scan'])
def handle_save_photo(message):
    photo_manager.save_photo(message)

@bot.message_handler(commands=['photos', 'scans'])
def handle_show_photos(message):
    photo_manager.show_user_photos(message)

# TikTok commands
@bot.message_handler(commands=['tiktok'])
def handle_random_tiktok(message):
    tiktok_manager.get_random_tiktok(message)

# Handle TikTok URLs in messages
@bot.message_handler(func=lambda message: tiktok_manager.is_tiktok_url(message.text or ''))
def handle_tiktok_url(message):
    url = tiktok_manager.extract_tiktok_url(message.text)
    if url:
        tiktok_manager.download_tiktok_video(message, url)

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        if call.data.startswith('delete_quote_'):
            quote_manager.handle_delete_quote(call)
        elif call.data.startswith('delete_photo_'):
            photo_manager.handle_delete_photo(call)
        elif call.data.startswith('download_'):
            tiktok_manager.handle_download_callback(call)
        else:
            bot.answer_callback_query(call.id, "❌ Неизвестная команда!")
            
    except Exception as e:
        logging.error(f"Error handling callback: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка!")

# Inline query handler (for accessing quotes and photos from any chat)
@bot.inline_handler(lambda query: query.query.lower().startswith('цитаты') or query.query.lower() == '')
def handle_inline_quotes(query):
    try:
        from telebot.types import InlineQueryResultArticle, InputTextMessageContent
        
        user_quotes = quote_manager.db.get_user_quotes(query.from_user.id, limit=50)
        
        results = []
        for i, quote in enumerate(user_quotes[:10]):  # Limit to 10 results
            quote_text = quote_manager.format_quote_from_db(quote)
            
            result = InlineQueryResultArticle(
                id=str(quote[0]),
                title=f"Цитата #{quote[0]}",
                description=quote[3][:100] + "..." if len(quote[3]) > 100 else quote[3],
                input_message_content=InputTextMessageContent(quote_text)
            )
            results.append(result)
        
        if not results:
            result = InlineQueryResultArticle(
                id='no_quotes',
                title="Нет сохраненных цитат",
                description="Создайте цитаты в чатах с ботом",
                input_message_content=InputTextMessageContent("📝 У меня пока нет сохраненных цитат!")
            )
            results.append(result)
        
        bot.answer_inline_query(query.id, results, cache_time=60)
        
    except Exception as e:
        logging.error(f"Error handling inline query: {e}")

@bot.inline_handler(lambda query: query.query.lower().startswith('photos'))
def handle_inline_photos(query):
    try:
        from telebot.types import InlineQueryResultPhoto
        
        user_photos = photo_manager.db.get_user_photos(query.from_user.id)
        
        results = []
        for photo in user_photos[:10]:  # Limit to 10 results
            result = InlineQueryResultPhoto(
                id=str(photo[0]),
                photo_url=f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{photo[1]}",
                thumb_url=f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{photo[1]}",
                caption=photo[2] if photo[2] else f"Фото #{photo[0]}"
            )
            results.append(result)
        
        bot.answer_inline_query(query.id, results, cache_time=60)
        
    except Exception as e:
        logging.error(f"Error handling inline photos: {e}")

if __name__ == '__main__':
    logging.info("Starting PororokzBot...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot error: {e}")
        print(f"❌ Ошибка бота: {e}")
        print("Убедитесь, что:")
        print("1. BOT_TOKEN установлен в файле .env")
        print("2. Токен валидный")
        print("3. Интернет соединение работает")
