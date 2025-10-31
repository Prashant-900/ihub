import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

DEFAULT_DIR = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(DEFAULT_DIR, exist_ok=True)
DB_PATH = os.environ.get('IHUB_SQLITE_PATH', os.path.join(DEFAULT_DIR, 'database.db'))


def _resolve_db_path(path: str) -> str:
    """Resolve database path to absolute path, creating parent directories if needed.
    
    Args:
        path: Database file path
        
    Returns:
        Absolute path to database file
    """
    try:
        abs_path = os.path.abspath(path)
        parent = os.path.dirname(abs_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        return abs_path
    except Exception as e:
        raise RuntimeError(f'Failed to resolve database path {path}: {e}')


class DatabaseManager:
    """SQLite database manager for conversation history and AI responses.
    
    Manages persistent storage of user messages and AI-generated responses with
    optional expression context and audio references.
    """

    def __init__(self, path: str = DB_PATH):
        """Initialize database manager.
        
        Args:
            path: Path to SQLite database file
            
        Raises:
            RuntimeError: If database connection fails
        """
        self.path = _resolve_db_path(path)
        try:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to open sqlite database at {self.path}: {e}')
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database tables if they don't exist."""
        try:
            cur = self._conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    text TEXT,
                    expression TEXT,
                    created_at TEXT NOT NULL,
                    audio_id TEXT
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS ai_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    timeline TEXT,
                    audio_id TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            self._conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to create database tables: {e}')

    def insert_message(
        self,
        role: str,
        text: str,
        audio_id: Optional[str] = None,
        expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert a message (user or system) into the database.
        
        Args:
            role: Message role ('user' or 'system')
            text: Message text content
            audio_id: Optional reference to audio file
            expression: Optional detected user expression/emotion
            
        Returns:
            Dictionary with inserted row data including id and created_at
        """
        try:
            cur = self._conn.cursor()
            created_at = datetime.utcnow().isoformat() + 'Z'
            cur.execute(
                '''INSERT INTO messages 
                   (role, text, audio_id, expression, created_at) 
                   VALUES (?, ?, ?, ?, ?)''',
                (role, text, audio_id, expression, created_at)
            )
            self._conn.commit()
            rowid = cur.lastrowid
            cur.execute('SELECT * FROM messages WHERE id=?', (rowid,))
            row = cur.fetchone()
            return dict(row) if row else {}
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to insert message: {e}')

    def insert_ai_response(
        self,
        text: str,
        timeline: List[Dict[str, Any]],
        audio_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Insert an AI response into the database.
        
        Args:
            text: Response text content
            timeline: Animation timeline data (list of animation states)
            audio_id: Optional reference to generated audio file
            
        Returns:
            Dictionary with inserted row data or None on error
        """
        try:
            cur = self._conn.cursor()
            timeline_json = json.dumps(timeline)
            created_at = datetime.utcnow().isoformat() + 'Z'
            cur.execute(
                '''INSERT INTO ai_responses 
                   (text, timeline, audio_id, created_at) 
                   VALUES (?, ?, ?, ?)''',
                (text, timeline_json, audio_id, created_at)
            )
            self._conn.commit()
            rowid = cur.lastrowid
            cur.execute('SELECT * FROM ai_responses WHERE id=?', (rowid,))
            row = cur.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to insert AI response: {e}')

    def get_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent messages from database.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries ordered by newest first
        """
        try:
            cur = self._conn.cursor()
            cur.execute(
                'SELECT * FROM messages ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to query messages: {e}')

    def get_ai_responses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent AI responses from database.
        
        Args:
            limit: Maximum number of responses to return
            
        Returns:
            List of AI response dictionaries with parsed timeline
        """
        try:
            cur = self._conn.cursor()
            cur.execute(
                'SELECT * FROM ai_responses ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            results = []
            for row in cur.fetchall():
                row_dict = dict(row)
                try:
                    row_dict['timeline'] = json.loads(row_dict['timeline']) if row_dict.get('timeline') else None
                except (json.JSONDecodeError, TypeError):
                    row_dict['timeline'] = None
                results.append(row_dict)
            return results
        except sqlite3.Error as e:
            raise RuntimeError(f'Failed to query AI responses: {e}')


# Global database instance
db = DatabaseManager()