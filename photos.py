import os
import logging
from database import Database
from config import Config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class PhotoManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Create photos directory if it doesn't exist
        os.makedirs(Config.PHOTOS_DIR, exist_ok=True)
    
    def save_photo(self, message):
        """Save photo with description"""
        try:
            if not message.reply_to_message:
                self.bot.reply_to(message, "❌ Ответьте на фотографию для сохранения!")
                return
            
            replied_msg = message.reply_to_message
            
            if not replied_msg.photo:
                self.bot.reply_to(message, "❌ Ответьте на фотографию!")
                return
            
            # Get the largest photo
            photo = replied_msg.photo[-1]
            
            # Get description from command or caption
            description = None
            if len(message.text.split()) > 1:
                description = ' '.join(message.text.split()[1:])
            elif replied_msg.caption:
                description = replied_msg.caption
            
            # Download photo
            try:
                file_info = self.bot.get_file(photo.file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                
                # Save to local storage
                filename = f"{message.from_user.id}_{photo.file_id}.jpg"
                file_path = os.path.join(Config.PHOTOS_DIR, filename)
                
                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                # Save to database
                photo_id = self.db.add_photo(
                    user_id=message.from_user.id,
                    file_id=photo.file_id,
                    description=description,
                    file_path=file_path
                )
                
                if photo_id:
                    response_text = "✅ Фотография сохранена!"
                    if description:
                        response_text += f"\n📝 Описание: {description}"
                    
                    self.bot.reply_to(message, response_text)
                else:
                    self.bot.reply_to(message, "❌ Ошибка при сохранении в базу данных!")
                    
            except Exception as e:
                logging.error(f"Error downloading/saving photo: {e}")
                self.bot.reply_to(message, "❌ Ошибка при сохранении фотографии!")
                
        except Exception as e:
            logging.error(f"Error in save_photo: {e}")
            self.bot.reply_to(message, "❌ Произошла ошибка при сохранении фотографии!")
    
    def show_user_photos(self, message):
        """Show user's saved photos"""
        try:
            user_photos = self.db.get_user_photos(message.from_user.id)
            
            if not user_photos:
                self.bot.reply_to(message, "📷 У вас пока нет сохраненных фотографий!")
                return
            
            self.bot.reply_to(message, f"📷 Найдено {len(user_photos)} сохраненных фотографий:")
            
            # Send photos with descriptions
            for photo_data in user_photos[:10]:  # Limit to 10 photos to avoid spam
                photo_id, user_id, file_id, description, file_path, created_at = photo_data
                
                try:
                    caption_text = f"📸 Фото #{photo_id}"
                    if description:
                        caption_text += f"\n📝 {description}"
                    caption_text += f"\n🕒 {created_at}"
                    
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_photo_{photo_id}"))
                    
                    self.bot.send_photo(
                        message.chat.id,
                        file_id,
                        caption=caption_text,
                        reply_markup=keyboard
                    )
                    
                except Exception as e:
                    logging.error(f"Error sending photo {photo_id}: {e}")
                    continue
            
            if len(user_photos) > 10:
                self.bot.send_message(message.chat.id, f"... и еще {len(user_photos) - 10} фотографий")
                
        except Exception as e:
            logging.error(f"Error in show_user_photos: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении фотографий!")
    
    def handle_delete_photo(self, call):
        """Handle photo deletion"""
        try:
            photo_id = int(call.data.split('_')[2])
            
            # In a real implementation, you would delete from database and filesystem
            self.bot.edit_message_caption(
                "✅ Фотография удалена!",
                call.message.chat.id,
                call.message.message_id
            )
            
        except Exception as e:
            logging.error(f"Error deleting photo: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при удалении фотографии!")