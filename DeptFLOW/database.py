import sqlite3
from datetime import datetime, date
import pandas as pd
from typing import Optional, List, Tuple

class HabitDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('habits.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')

            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS habit_logs (
                    id INTEGER PRIMARY KEY,
                    habit_id INTEGER,
                    date DATE,
                    completed BOOLEAN,
                    FOREIGN KEY (habit_id) REFERENCES habits (id),
                    UNIQUE(habit_id, date)
                )
            ''')

    def add_habit(self, name):
        with self.conn:
            cursor = self.conn.execute(
                'INSERT INTO habits (name) VALUES (?)',
                (name,)
            )
            return cursor.lastrowid

    def get_habits(self):
        query = 'SELECT id, name, created_date FROM habits'
        return pd.read_sql_query(query, self.conn)

    def delete_habit(self, habit_id):
        with self.conn:
            self.conn.execute('DELETE FROM habit_logs WHERE habit_id = ?', (habit_id,))
            self.conn.execute('DELETE FROM habits WHERE id = ?', (habit_id,))

    def log_habit(self, habit_id, date, completed):
        with self.conn:
            self.conn.execute('''
                INSERT OR REPLACE INTO habit_logs (habit_id, date, completed)
                VALUES (?, ?, ?)
            ''', (habit_id, date, completed))

    def get_habit_logs(self, habit_id=None, start_date=None, end_date=None):
        query = '''
            SELECT h.name, hl.date, hl.completed
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id
            WHERE 1=1
        '''
        params = []

        if habit_id:
            query += ' AND h.id = ?'
            params.append(habit_id)
        if start_date:
            query += ' AND hl.date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND hl.date <= ?'
            params.append(end_date)

        return pd.read_sql_query(query, self.conn, params=params)

    def get_streak_data(self, habit_id):
        logs = pd.read_sql_query(
            'SELECT date, completed FROM habit_logs WHERE habit_id = ? ORDER BY date',
            self.conn,
            params=(habit_id,)
        )
        if logs.empty:
            return 0, 0

        current_streak = 0
        max_streak = 0
        current_count = 0

        for _, row in logs.iterrows():
            if row['completed']:
                current_count += 1
                max_streak = max(max_streak, current_count)
            else:
                current_count = 0

        current_streak = current_count
        return current_streak, max_streak


class WebhookDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('webhooks.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # Create webhooks table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    webhook_url TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create commands table with description
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY,
                    webhook_id INTEGER,
                    command_name TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks (id),
                    UNIQUE(webhook_id, command_name)
                )
            ''')

    def add_webhook(self, guild_id: str, webhook_url: str, name: str) -> int:
        """Add a new webhook configuration"""
        with self.conn:
            cursor = self.conn.execute(
                'INSERT INTO webhooks (guild_id, webhook_url, name) VALUES (?, ?, ?)',
                (guild_id, webhook_url, name)
            )
            return cursor.lastrowid

    def add_command(self, webhook_id: int, command_name: str, message_content: str, description: str, created_by: str) -> bool:
        """Add a new command for a webhook"""
        try:
            with self.conn:
                self.conn.execute(
                    'INSERT INTO commands (webhook_id, command_name, message_content, description, created_by) VALUES (?, ?, ?, ?, ?)',
                    (webhook_id, command_name, message_content, description, created_by)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_webhook(self, guild_id: str, name: str) -> Optional[Tuple[int, str]]:
        """Get webhook details by guild ID and name"""
        cursor = self.conn.execute(
            'SELECT id, webhook_url FROM webhooks WHERE guild_id = ? AND name = ?',
            (guild_id, name)
        )
        result = cursor.fetchone()
        return result if result else None

    def get_command(self, webhook_id: int, command_name: str) -> Optional[Tuple[str, str]]:
        """Get command message content and description"""
        cursor = self.conn.execute(
            'SELECT message_content, description FROM commands WHERE webhook_id = ? AND command_name = ?',
            (webhook_id, command_name)
        )
        result = cursor.fetchone()
        return result if result else None

    def list_webhooks(self, guild_id: str) -> List[Tuple[int, str, str]]:
        """List all webhooks for a guild"""
        cursor = self.conn.execute(
            'SELECT id, name, webhook_url FROM webhooks WHERE guild_id = ?',
            (guild_id,)
        )
        return cursor.fetchall()

    def list_commands(self, webhook_id: int) -> List[Tuple[str, str, str]]:
        """List all commands for a webhook with their descriptions"""
        cursor = self.conn.execute(
            'SELECT command_name, message_content, description FROM commands WHERE webhook_id = ?',
            (webhook_id,)
        )
        return cursor.fetchall()

    def delete_webhook(self, guild_id: str, name: str) -> bool:
        """Delete a webhook and its associated commands"""
        try:
            with self.conn:
                webhook = self.get_webhook(guild_id, name)
                if webhook:
                    webhook_id = webhook[0]
                    self.conn.execute('DELETE FROM commands WHERE webhook_id = ?', (webhook_id,))
                    self.conn.execute('DELETE FROM webhooks WHERE id = ?', (webhook_id,))
                    return True
                return False
        except sqlite3.Error:
            return False

    def delete_command(self, webhook_id: int, command_name: str) -> bool:
        """Delete a specific command"""
        try:
            with self.conn:
                cursor = self.conn.execute(
                    'DELETE FROM commands WHERE webhook_id = ? AND command_name = ?',
                    (webhook_id, command_name)
                )
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

# Add new table definition after the existing tables
class BotConfigDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('bot_config.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_config (
                    guild_id TEXT PRIMARY KEY,
                    log_channel_id TEXT NOT NULL,
                    manage_role_id TEXT NOT NULL,
                    al_message TEXT
                )
            ''')

    def save_config(self, guild_id: str, log_channel_id: str, manage_role_id: str, al_message: str = None) -> bool:
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT OR REPLACE INTO bot_config 
                    (guild_id, log_channel_id, manage_role_id, al_message)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, log_channel_id, manage_role_id, al_message))
            return True
        except sqlite3.Error:
            return False

    def get_config(self, guild_id: str) -> Optional[Tuple[str, str, str]]:
        cursor = self.conn.execute(
            'SELECT log_channel_id, manage_role_id, al_message FROM bot_config WHERE guild_id = ?',
            (guild_id,)
        )
        result = cursor.fetchone()
        return result if result else None