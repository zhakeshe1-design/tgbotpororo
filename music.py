from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import logging
import yt_dlp

from database import Database
from config import Config



class MusicManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        os.makedirs(Config.MUSIC_DIR, exist_ok=True)
        self._search_cache = {}
        
    def download_from_info(self, message, info):
        try:
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown Artist')
            url = info.get('webpage_url')

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{Config.MUSIC_DIR}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                filename = ydl.prepare_filename(info)
                audio_filename = os.path.splitext(filename)[0] + '.mp3'

            if os.path.exists(audio_filename):
                with open(audio_filename, 'rb') as audio_file:
                    sent = self.bot.send_audio(
                        message.chat.id,
                        audio_file,
                        title=title,
                        performer=uploader
                    )

                self.db.add_music(
                    user_id=message.chat.id,
                    title=title,
                    artist=uploader,
                    file_path=audio_filename,
                    file_id=sent.audio.file_id if sent.audio else None
                )

                self.bot.send_message(message.chat.id, "✅ Музыка жіберілді!")
                os.remove(audio_filename)

            else:
                self.bot.send_message(message.chat.id, "❌ Файл табылмады!")

        except Exception as e:
            logging.error(f"Error downloading selected music: {e}")
            self.bot.send_message(message.chat.id, "❌ Қате орын алды!")

    def search_music_list(self, message, query):
        """Музыка іздеу (қысқаша жауаппен 1-2 ән)"""
        
        try:
            self.bot.reply_to(message, "🔍 Іздеудемін...")

            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt', 
                'default_search': 'ytsearch1',
                'retries': 10,              # 👈 қайта көру
                'fragment_retries': 10, 
                'outtmpl': f'{Config.MUSIC_DIR}/%(title)s.%(ext)s',
                'nooverwrites': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)

            if not info or 'entries' not in info or len(info['entries']) == 0:
                self.bot.reply_to(message, "❌ Музыка табылмады!")
                return

            entry = info['entries'][0]
            self.download_from_info(message, entry)

        except Exception as e:
            logging.error(f"Error in search_music_list: {e}")
            self.bot.reply_to(message, "❌ Қате орын алды!")
            
    


    def show_music_options(self, message, query):
        """Музыка іздеу, 5-6 нұсқасын көрсетеді меню түрінде"""
    
        try:
            self.bot.reply_to(message, "🔍 Музыкалар ізделуде...")

            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'cookiefile': 'cookies.txt', 
                'default_search': 'ytsearch5',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)

            if not info or 'entries' not in info or len(info['entries']) == 0:
                self.bot.reply_to(message, "❌ Музыка табылмады!")
                return

            keyboard = InlineKeyboardMarkup()
            self._search_cache = {}

            text = "🎧 Найдено:\n\n"
            for i, entry in enumerate(info['entries'], 1):
                title = entry.get('title', 'Без названия')
                uploader = entry.get('uploader', 'Неизвестно')
                text += f"{i}. {title} — {uploader}\n"
                callback_data = f"music_choose_{i}"
                self._search_cache[callback_data] = {
                    'info': entry,
                    'user_id': message.from_user.id
                }
                keyboard.add(InlineKeyboardButton(f"🎵 {i}", callback_data=callback_data))

            self.bot.send_message(message.chat.id, text, reply_markup=keyboard)

        except Exception as e:
            logging.error(f"Error in show_music_options: {e}")
            self.bot.reply_to(message, "❌ Қате орын алды!")



    def handle_music_selection(self, call):
        try:
            parts = call.data.split("_")
            idx = int(parts[2]) - 1
            user_id = int(parts[3])

            if call.from_user.id != user_id:
                self.bot.answer_callback_query(call.id, "❗ Это не ваш запрос.")
                return

            results = self._search_cache.get(user_id)
            if not results or idx >= len(results):
                self.bot.answer_callback_query(call.id, "❌ Истекло время выбора.")
                return

            video = results[idx]
            title = video.get('title', 'Unknown')
            uploader = video.get('uploader', 'Unknown Artist')
            url = video['webpage_url']

            self.bot.edit_message_text(
                f"⬬ Скачиваю: *{title}* - *{uploader}*...",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{Config.MUSIC_DIR}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                filename = ydl.prepare_filename(video)
                mp3_file = os.path.splitext(filename)[0] + '.mp3'

            if os.path.exists(mp3_file):
                with open(mp3_file, 'rb') as audio:
                    sent = self.bot.send_audio(
                        call.message.chat.id,
                        audio,
                        title=title,
                        performer=uploader
                    )
                self.bot.edit_message_text(
                    "✅ Музыка отправлена!",
                    call.message.chat.id,
                    call.message.message_id
                )
                try:
                    os.remove(mp3_file)
                except:
                    pass
            else:
                self.bot.edit_message_text("❌ Ошибка при скачивании!", call.message.chat.id, call.message.message_id)

        except Exception as e:
            logging.error(f"Error in handle_music_selection: {e}", exc_info=True)
            self.bot.edit_message_text("❌ Ошибка при обработке!", call.message.chat.id, call.message.message_id)
