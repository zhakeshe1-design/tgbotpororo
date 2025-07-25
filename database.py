import sqlite3
import logging
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Quotes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quotes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        chat_id INTEGER NOT NULL,
                        message_text TEXT NOT NULL,
                        author_name TEXT,
                        author_id INTEGER,
                        quote_type INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Photos table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS photos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        file_id TEXT NOT NULL,
                        description TEXT,
                        file_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Music table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS music (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        artist TEXT,
                        file_path TEXT,
                        file_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # TikTok table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tiktok_videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        url TEXT NOT NULL,
                        file_path TEXT,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logging.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
    
    def add_quote(self, user_id, chat_id, message_text, author_name=None, author_id=None, quote_type=1):
        """Add a new quote to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO quotes (user_id, chat_id, message_text, author_name, author_id, quote_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, chat_id, message_text, author_name, author_id, quote_type))
                quote_id = cursor.lastrowid
                conn.commit()
                return quote_id
        except sqlite3.Error as e:
            logging.error(f"Error adding quote: {e}")
            return None
    
    def get_user_quotes(self, user_id, limit=None):
        """Get quotes by user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM quotes WHERE user_id = ? ORDER BY created_at DESC'
                if limit:
                    query += f' LIMIT {limit}'
                cursor.execute(query, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting user quotes: {e}")
            return []
    
    def get_chat_quotes(self, chat_id, limit=None):
        """Get quotes from specific chat"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM quotes WHERE chat_id = ? ORDER BY created_at DESC'
                if limit:
                    query += f' LIMIT {limit}'
                cursor.execute(query, (chat_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting chat quotes: {e}")
            return []
    
    def get_random_quote(self):
        """Get random quote from all quotes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1')
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Error getting random quote: {e}")
            return None
    
    def delete_quote(self, quote_id, user_id):
        """Delete user's quote"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM quotes WHERE id = ? AND user_id = ?', (quote_id, user_id))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error deleting quote: {e}")
            return False
    
    def add_photo(self, user_id, file_id, description=None, file_path=None):
        """Add saved photo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO photos (user_id, file_id, description, file_path)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, file_id, description, file_path))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error adding photo: {e}")
            return None
    
    def get_user_photos(self, user_id):
        """Get user's saved photos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM photos WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting user photos: {e}")
            return []
    
    def add_music(self, user_id, title, artist=None, file_path=None, file_id=None):
        """Add music track"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO music (user_id, title, artist, file_path, file_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, title, artist, file_path, file_id))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error adding music: {e}")
            return None
    
    def get_random_tiktok(self):
        """Get random TikTok video"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM tiktok_videos ORDER BY RANDOM() LIMIT 1')
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Error getting random TikTok: {e}")
            return None