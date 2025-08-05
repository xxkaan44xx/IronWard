import sqlite3
import asyncio
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="moderation_bot.db"):
        self.db_path = db_path
        self.lock = asyncio.Lock()

    async def init_db(self):
        """Initialize database tables."""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Guild settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'tr',
                    prefix TEXT DEFAULT '!',
                    welcome_channel INTEGER,
                    goodbye_channel INTEGER,
                    log_channel INTEGER,
                    auto_role INTEGER,
                    mute_role INTEGER,
                    ticket_category INTEGER
                )
            ''')

            # Warnings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Temporary bans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_bans (
                    guild_id INTEGER,
                    user_id INTEGER,
                    expires_at DATETIME,
                    reason TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')

            # Muted users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS muted_users (
                    guild_id INTEGER,
                    user_id INTEGER,
                    expires_at DATETIME,
                    reason TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')

            # Auto-moderation settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS automod_settings (
                    guild_id INTEGER PRIMARY KEY,
                    anti_spam BOOLEAN DEFAULT 0,
                    anti_flood BOOLEAN DEFAULT 0,
                    anti_link BOOLEAN DEFAULT 0,
                    anti_invite BOOLEAN DEFAULT 0,
                    caps_filter BOOLEAN DEFAULT 0,
                    emoji_filter BOOLEAN DEFAULT 0,
                    mention_filter BOOLEAN DEFAULT 0,
                    word_filter BOOLEAN DEFAULT 0
                )
            ''')

            # Blacklisted words
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklisted_words (
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Moderation logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    moderator_id INTEGER,
                    target_id INTEGER,
                    action TEXT,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Additional tables for new features
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    guild_id INTEGER,
                    message_id INTEGER,  
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, message_id)
                )
            ''')

            # Reaction roles table
            await self.execute_query("""
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    emoji TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Blacklisted words table
            await self.execute_query("""
                CREATE TABLE IF NOT EXISTS blacklisted_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, word)
                )
            """)

            # Add new columns to guild_settings if they don't exist
            try:
                await self.execute_query("ALTER TABLE guild_settings ADD COLUMN modmail_enabled INTEGER DEFAULT 0")
            except:
                pass

            try:
                await self.execute_query("ALTER TABLE guild_settings ADD COLUMN modmail_channel INTEGER")
            except:
                pass

            conn.commit()
            conn.close()

    async def execute_query(self, query, params=None, fetch=False):
        """Execute a database query safely."""
        async with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch:
                    result = cursor.fetchall()
                    conn.close()
                    return result
                else:
                    conn.commit()
                    conn.close()
                    return cursor.rowcount
            except Exception as e:
                conn.close()
                raise e

    # Guild Settings Methods
    async def get_language(self, guild_id):
        """Get guild language."""
        result = await self.execute_query(
            "SELECT language FROM guild_settings WHERE guild_id = ?",
            (guild_id,), fetch=True
        )
        return result[0][0] if result and len(result) > 0 else 'tr'

    async def set_language(self, guild_id, language):
        """Set guild language."""
        await self.execute_query(
            "INSERT OR REPLACE INTO guild_settings (guild_id, language) VALUES (?, ?)",
            (guild_id, language)
        )

    async def get_prefix(self, guild_id):
        """Get guild prefix."""
        result = await self.execute_query(
            "SELECT prefix FROM guild_settings WHERE guild_id = ?",
            (guild_id,), fetch=True
        )
        return result[0][0] if result and len(result) > 0 else '!'

    async def set_prefix(self, guild_id, prefix):
        """Set guild prefix."""
        await self.execute_query(
            "INSERT OR REPLACE INTO guild_settings (guild_id, prefix) VALUES (?, ?)",
            (guild_id, prefix)
        )

    async def get_guild_settings(self, guild_id):
        """Get all guild settings."""
        result = await self.execute_query(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild_id,), fetch=True
        )
        if result and len(result) > 0:
            row = result[0]
            return {
                'language': row[1] if len(row) > 1 else 'tr',
                'prefix': row[2] if len(row) > 2 else '!',
                'welcome_channel': row[3] if len(row) > 3 else None,
                'goodbye_channel': row[4] if len(row) > 4 else None,
                'log_channel': row[5] if len(row) > 5 else None,
                'auto_role': row[6] if len(row) > 6 else None,
                'mute_role': row[7] if len(row) > 7 else None,
                'modmail_enabled': row[8] if len(row) > 8 else 0,
                'modmail_channel': row[9] if len(row) > 9 else None
            }
        return None

    async def update_guild_setting(self, guild_id, setting, value):
        """Update a specific guild setting."""
        await self.execute_query(
            f"INSERT OR REPLACE INTO guild_settings (guild_id, {setting}) VALUES (?, ?)",
            (guild_id, value)
        )

    # Warning Methods
    async def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Add a warning to user."""
        await self.execute_query(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason)
        )

    async def get_warnings(self, guild_id, user_id):
        """Get all warnings for a user."""
        result = await self.execute_query(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
            (guild_id, user_id), fetch=True
        )
        return result

    async def clear_warnings(self, guild_id, user_id):
        """Clear all warnings for a user."""
        await self.execute_query(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )

    # Temporary Ban Methods
    async def add_temp_ban(self, guild_id, user_id, expires_at, reason):
        """Add a temporary ban."""
        await self.execute_query(
            "INSERT OR REPLACE INTO temp_bans VALUES (?, ?, ?, ?)",
            (guild_id, user_id, expires_at, reason)
        )

    async def remove_temp_ban(self, guild_id, user_id):
        """Remove a temporary ban."""
        await self.execute_query(
            "DELETE FROM temp_bans WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )

    async def get_expired_bans(self):
        """Get all expired bans."""
        now = datetime.now()
        result = await self.execute_query(
            "SELECT guild_id, user_id FROM temp_bans WHERE expires_at <= ?",
            (now,), fetch=True
        )
        return result

    # Mute Methods
    async def add_mute(self, guild_id, user_id, expires_at, reason):
        """Add a mute."""
        await self.execute_query(
            "INSERT OR REPLACE INTO muted_users VALUES (?, ?, ?, ?)",
            (guild_id, user_id, expires_at, reason)
        )

    async def remove_mute(self, guild_id, user_id):
        """Remove a mute."""
        await self.execute_query(
            "DELETE FROM muted_users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )

    async def get_expired_mutes(self):
        """Get all expired mutes."""
        now = datetime.now()
        result = await self.execute_query(
            "SELECT guild_id, user_id FROM muted_users WHERE expires_at <= ?",
            (now,), fetch=True
        )
        return result

    # Auto-moderation Methods
    async def get_automod_settings(self, guild_id):
        """Get auto-moderation settings."""
        result = await self.execute_query(
            "SELECT * FROM automod_settings WHERE guild_id = ?",
            (guild_id,), fetch=True
        )
        if result and len(result) > 0:
            row = result[0]
            return {
                'anti_spam': bool(row[1]) if len(row) > 1 else False,
                'anti_flood': bool(row[2]) if len(row) > 2 else False,
                'anti_link': bool(row[3]) if len(row) > 3 else False,
                'anti_invite': bool(row[4]) if len(row) > 4 else False,
                'caps_filter': bool(row[5]) if len(row) > 5 else False,
                'emoji_filter': bool(row[6]) if len(row) > 6 else False,
                'mention_filter': bool(row[7]) if len(row) > 7 else False,
                'word_filter': bool(row[8]) if len(row) > 8 else False
            }
        return None

    async def update_automod_setting(self, guild_id, setting, value):
        """Update auto-moderation setting."""
        await self.execute_query(
            f"INSERT OR REPLACE INTO automod_settings (guild_id, {setting}) VALUES (?, ?)",
            (guild_id, int(value))
        )

    # Blacklisted Words Methods
    async def add_blacklisted_word(self, guild_id, word):
        """Add a blacklisted word."""
        await self.execute_query(
            "INSERT OR IGNORE INTO blacklisted_words (guild_id, word) VALUES (?, ?)",
            (guild_id, word.lower())
        )

    async def remove_blacklisted_word(self, guild_id, word):
        """Remove a blacklisted word."""
        await self.execute_query(
            "DELETE FROM blacklisted_words WHERE guild_id = ? AND word = ?",
            (guild_id, word.lower())
        )

    async def get_blacklisted_words(self, guild_id):
        """Get all blacklisted words."""
        result = await self.execute_query(
            "SELECT word FROM blacklisted_words WHERE guild_id = ?",
            (guild_id,), fetch=True
        )
        return [row[0] for row in result] if result else []

    # Moderation Log Methods
    async def add_mod_log(self, guild_id, moderator_id, user_id, action, reason):
        """Add a moderation log entry."""
        await self.execute_query(
            "INSERT INTO mod_logs (guild_id, moderator_id, user_id, action, reason) VALUES (?, ?, ?, ?, ?)",
            (guild_id, moderator_id, user_id, action, reason)
        )

    async def get_mod_logs(self, guild_id, limit=50):
        """Get moderation logs for a guild."""
        result = await self.execute_query(
            "SELECT * FROM mod_logs WHERE guild_id = ? ORDER BY timestamp DESC LIMIT ?",
            (guild_id, limit), fetch=True
        )
        if result:
            return [dict(zip(['guild_id', 'moderator_id', 'user_id', 'action', 'reason', 'timestamp'], row)) for row in result]
        return []

    async def get_mod_logs_for_user(self, guild_id, user_id, limit=10):
        """Get moderation logs for a specific user."""
        result = await self.execute_query(
            "SELECT * FROM mod_logs WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (guild_id, user_id, limit), fetch=True
        )
        if result:
            return [dict(zip(['guild_id', 'moderator_id', 'user_id', 'action', 'reason', 'timestamp'], row)) for row in result]
        return []

    async def get_reports(self, guild_id, limit=10):
        """Get reports from moderation logs."""
        result = await self.execute_query(
            "SELECT * FROM mod_logs WHERE guild_id = ? AND action = 'REPORT' ORDER BY timestamp DESC LIMIT ?",
            (guild_id, limit), fetch=True
        )
        if result:
            return [dict(zip(['guild_id', 'moderator_id', 'user_id', 'action', 'reason', 'timestamp'], row)) for row in result]
        return []