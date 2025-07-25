import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import Database
import random

class QuoteManager:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    def create_quote_type1(self, message_text, author_name):
        """Create simple text quote (Type 1)"""
        quote_text = f'"{message_text}"\n\n© {author_name}'
        return quote_text
    
    def create_quote_type2(self, message_text, author_name):
        """Create formatted quote with emoji support (Type 2)"""
        quote_text = f'💬 "{message_text}"\n\n👤 {author_name}'
        return quote_text
    
    def handle_quote_command(self, message, quote_type=1):
        """Handle quote creation from replied message"""
        try:
            if not message.reply_to_message:
                self.bot.reply_to(message, "❌ Ответьте на сообщение, чтобы сделать цитату!")
                return
            
            replied_msg = message.reply_to_message
            author_name = replied_msg.from_user.first_name
            if replied_msg.from_user.last_name:
                author_name += f" {replied_msg.from_user.last_name}"
            
            if not replied_msg.text:
                self.bot.reply_to(message, "❌ Можно цитировать только текстовые сообщения!")
                return
            
            # Add to database
            quote_id = self.db.add_quote(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                message_text=replied_msg.text,
                author_name=author_name,
                author_id=replied_msg.from_user.id,
                quote_type=quote_type
            )
            
            if quote_id:
                if quote_type == 1:
                    quote_text = self.create_quote_type1(replied_msg.text, author_name)
                else:
                    quote_text = self.create_quote_type2(replied_msg.text, author_name)
                
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("🗑 Удалить цитату", callback_data=f"delete_quote_{quote_id}"))
                
                self.bot.send_message(message.chat.id, quote_text, reply_markup=keyboard)
            else:
                self.bot.reply_to(message, "❌ Ошибка при сохранении цитаты!")
                
        except Exception as e:
            logging.error(f"Error handling quote command: {e}")
            self.bot.reply_to(message, "❌ Произошла ошибка при создании цитаты!")
    
    def handle_my_quote(self, message, quote_number=None):
        """Handle user's quotes"""
        try:
            user_quotes = self.db.get_user_quotes(message.from_user.id)
            
            if not user_quotes:
                self.bot.reply_to(message, "📝 У вас пока нет сохраненных цитат!")
                return
            
            if quote_number is None:
                quote = random.choice(user_quotes)
            else:
                if quote_number > len(user_quotes) or quote_number < 1:
                    self.bot.reply_to(message, f"❌ Цитата #{quote_number} не найдена! У вас всего {len(user_quotes)} цитат.")
                    return
                quote = user_quotes[quote_number - 1]
            
            quote_text = self.format_quote_from_db(quote)
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🗑 Удалить цитату", callback_data=f"delete_quote_{quote[0]}"))
            
            self.bot.send_message(message.chat.id, quote_text, reply_markup=keyboard)
            
        except Exception as e:
            logging.error(f"Error handling my_quote: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении цитаты!")
    
    def handle_chat_quote(self, message, quote_number=None):
        """Handle chat quotes"""
        try:
            chat_quotes = self.db.get_chat_quotes(message.chat.id)
            
            if not chat_quotes:
                self.bot.reply_to(message, "📝 В этом чате пока нет сохраненных цитат!")
                return
            
            if quote_number is None:
                quote = random.choice(chat_quotes)
            else:
                if quote_number > len(chat_quotes) or quote_number < 1:
                    self.bot.reply_to(message, f"❌ Цитата #{quote_number} не найдена! В чате всего {len(chat_quotes)} цитат.")
                    return
                quote = chat_quotes[quote_number - 1]
            
            quote_text = self.format_quote_from_db(quote)
            self.bot.send_message(message.chat.id, quote_text)
            
        except Exception as e:
            logging.error(f"Error handling chat_quote: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении цитаты!")
    
    def handle_all_quote(self, message):
        """Handle random quote from all chats"""
        try:
            quote = self.db.get_random_quote()
            
            if not quote:
                self.bot.reply_to(message, "📝 Пока нет сохраненных цитат!")
                return
            
            quote_text = self.format_quote_from_db(quote)
            self.bot.send_message(message.chat.id, quote_text)
            
        except Exception as e:
            logging.error(f"Error handling all_quote: {e}")
            self.bot.reply_to(message, "❌ Ошибка при получении цитаты!")
    
    def format_quote_from_db(self, quote):
        """Format quote from database record"""
        quote_id, user_id, chat_id, message_text, author_name, author_id, quote_type, created_at = quote
        
        if quote_type == 2:
            return self.create_quote_type2(message_text, author_name)
        else:
            return self.create_quote_type1(message_text, author_name)
    
    def handle_delete_quote(self, call):
        """Handle quote deletion"""
        try:
            quote_id = int(call.data.split('_')[2])
            
            if self.db.delete_quote(quote_id, call.from_user.id):
                self.bot.edit_message_text(
                    "✅ Цитата удалена!",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                self.bot.answer_callback_query(call.id, "❌ Не удалось удалить цитату!")
                
        except Exception as e:
            logging.error(f"Error deleting quote: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при удалении цитаты!")