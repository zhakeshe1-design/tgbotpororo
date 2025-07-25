import os
import re
import logging
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
from config import Config

class TikTokManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        os.makedirs(Config.TIKTOK_DIR, exist_ok=True)
        self._temp_urls = {}

    def is_tiktok_url(self, text):
        tiktok_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w\.-]+/video/\d+',
            r'https?://vm\.tiktok\.com/[\w\d]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w\d]+',
        ]
        for pattern in tiktok_patterns:
            if re.search(pattern, text):
                return True
        return False

    def extract_tiktok_url(self, text):
        tiktok_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w\.-]+/video/\d+',
            r'https?://vm\.tiktok\.com/[\w\d]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w\d]+',
        ]
        for pattern in tiktok_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def download_tiktok_video(self, message, url):
        try:
            status_msg = self.bot.reply_to(message, "🔄 Обрабатываю TikTok видео...")

            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best',
                'outtmpl': f'{Config.TIKTOK_DIR}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    self.bot.edit_message_text(
                        "❌ Не удалось получить информацию о видео!",
                        message.chat.id,
                        status_msg.message_id
                    )
                    return

                title = info.get('title', 'TikTok Video')
                uploader = info.get('uploader', 'Unknown')
                duration = info.get('duration', 0)

                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("📹 Скачать видео", callback_data=f"download_video_{hash(url)}"),
                    InlineKeyboardButton("🎵 Только звук", callback_data=f"download_audio_{hash(url)}")
                )

                video_info_text = (
                    f"🎬 **{title}**\n"
                    f"👤 Автор: {uploader}\n"
                    f"⏱ Длительность: {duration}с\n\n"
                    f"Выберите формат для скачивания:"
                )

                self.bot.edit_message_text(
                    video_info_text,
                    message.chat.id,
                    status_msg.message_id,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )

                self._temp_urls[hash(url)] = {
                    'url': url,
                    'info': info,
                    'user_id': message.from_user.id
                }

        except Exception as e:
            logging.error(f"Error in download_tiktok_video: {e}")
            self.bot.reply_to(message, "❌ Произошла ошибка при обработке TikTok!")

    def handle_download_callback(self, call):
        try:
            parts = call.data.split('_')
            if len(parts) < 3:
                self.bot.answer_callback_query(call.id, "❌ Некорректные данные!")
                return

            download_type = parts[1]  # 'video' or 'audio'
            url_hash = int(parts[2])

            if url_hash not in self._temp_urls:
                self.bot.answer_callback_query(call.id, "❌ Ссылка устарела!")
                return

            url_data = self._temp_urls[url_hash]
            url = url_data['url']
            info = url_data['info']

            if download_type == 'video':
                self._download_video_file(call, url, info)
            elif download_type == 'audio':
                self._download_audio_file(call, url, info)
            else:
                self.bot.answer_callback_query(call.id, "❌ Неизвестный тип загрузки!")

        except Exception as e:
            logging.error(f"Error in handle_download_callback: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при скачивании!")

    def _download_video_file(self, call, url, info):
        try:
            self.bot.edit_message_text(
                "⬬ Скачиваю видео...",
                call.message.chat.id,
                call.message.message_id
            )

            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best',
                'outtmpl': f'{Config.TIKTOK_DIR}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                filename = ydl.prepare_filename(info)

                if os.path.exists(filename):
                    with open(filename, 'rb') as video_file:
                        self.bot.send_video(
                            call.message.chat.id,
                            video_file,
                            caption=f"🎬 {info.get('title', 'TikTok Video')}"
                        )
                    self.bot.edit_message_text(
                        "✅ Видео скачано!",
                        call.message.chat.id,
                        call.message.message_id
                    )
                    try:
                        os.remove(filename)
                    except Exception:
                        pass
                else:
                    self.bot.edit_message_text(
                        "❌ Ошибка при скачивании видео!",
                        call.message.chat.id,
                        call.message.message_id
                    )

        except Exception as e:
            logging.error(f"Error downloading video: {e}")
            self.bot.edit_message_text(
                "❌ Ошибка при скачивании видео!",
                call.message.chat.id,
                call.message.message_id
            )

    def _download_audio_file(self, call, url, info):
        try:
            self.bot.edit_message_text(
                "⬬ Извлекаю звук...",
                call.message.chat.id,
                call.message.message_id
            )

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{Config.TIKTOK_DIR}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
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
                        self.bot.send_audio(
                            call.message.chat.id,
                            audio_file,
                            title=info.get('title', 'TikTok Audio')
                        )
                    self.bot.edit_message_text(
                        "✅ Звук извлечен!",
                        call.message.chat.id,
                        call.message.message_id
                    )
                    try:
                        os.remove(audio_filename)
                    except Exception:
                        pass
                else:
                    self.bot.edit_message_text(
                        "❌ Ошибка при извлечении звука!",
                        call.message.chat.id,
                        call.message.message_id
                    )

        except Exception as e:
            logging.error(f"Error downloading audio: {e}")
            self.bot.edit_message_text(
                "❌ Ошибка при извлечении звука!",
                call.message.chat.id,
                call.message.message_id
            )

    def get_random_tiktok(self, message):
        try:
            tiktok_data = self.db.get_random_tiktok()

            if not tiktok_data:
                self.bot.reply_to(message, "📱 Пока нет сохраненных TikTok видео!")
                return

            self.bot.reply_to(message, f"🎬 Случайное TikTok видео:\n{tiktok_data[3] or 'Без названия'}")

        except Exception as e:
            logging.error(f"Error getting random TikTok: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении TikTok видео!")
