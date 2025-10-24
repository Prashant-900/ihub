import os
import sqlite3
import json
from datetime import datetime

DEFAULT_DIR = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(DEFAULT_DIR, exist_ok=True)
DB_PATH = os.environ.get('IHUB_SQLITE_PATH', os.path.join(DEFAULT_DIR, 'database.db'))


def _resolve_db_path(path):
    try:
        abs_path = os.path.abspath(path)
        parent = os.path.dirname(abs_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        return abs_path
    except Exception:
        return path

class DatabaseManager:
    def __init__(self, path=DB_PATH):
        # normalize to absolute path to avoid cwd-dependent DB files
        self.path = _resolve_db_path(path)
        try:
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
        except Exception as e:
            print('Failed to open sqlite DB at', self.path, 'error:', e)
            raise
        self._conn.row_factory = sqlite3.Row
        self._ensure_db()
        try:
            print(f"DatabaseManager initialized. DB path={self.path} exists={os.path.exists(self.path)}")
        except Exception:
            pass

    def _ensure_db(self):
        cur = self._conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                text TEXT,
                created_at TEXT,
                audio_id TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ai_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                timeline TEXT,
                audio_id TEXT,
                created_at TEXT
            )
        ''')
        self._conn.commit()

    def insert_message(self, role, text, audio_id=None):
        cur = self._conn.cursor()
        # create ISO8601 UTC timestamp to ensure consistent parsing on frontend
        created_at = datetime.utcnow().isoformat() + 'Z'
        cur.execute('INSERT INTO messages (role, text, audio_id, created_at) VALUES (?,?,?,?)', (role, text, audio_id, created_at))
        self._conn.commit()
        rowid = cur.lastrowid
        cur.execute('SELECT * FROM messages WHERE id=?', (rowid,))
        row = cur.fetchone()
        try:
            print('Inserted message row id=', rowid, 'role=', role, 'text_len=', len(text or ''), 'audio_id=', audio_id)
        except Exception:
            pass
        return dict(row)

    def insert_ai_response(self, text, timeline, audio_id=None):
        cur = self._conn.cursor()
        timeline_json = json.dumps(timeline)
        created_at = datetime.utcnow().isoformat() + 'Z'
        cur.execute('INSERT INTO ai_responses (text, timeline, audio_id, created_at) VALUES (?,?,?,?)', (text, timeline_json, audio_id, created_at))
        self._conn.commit()
        rowid = cur.lastrowid
        cur.execute('SELECT * FROM ai_responses WHERE id=?', (rowid,))
        row = cur.fetchone()
        try:
            print('Inserted ai_response id=', rowid, 'text_len=', len(text or ''), 'audio_id=', audio_id)
        except Exception:
            pass
        if row:
            return dict(row)
        return None

    def get_messages(self, limit=50):
        cur = self._conn.cursor()
        cur.execute('SELECT * FROM messages ORDER BY id DESC LIMIT ?', (limit,))
        return [dict(r) for r in cur.fetchall()]

    def get_ai_responses(self, limit=50):
        cur = self._conn.cursor()
        cur.execute('SELECT * FROM ai_responses ORDER BY id DESC LIMIT ?', (limit,))
        res = []
        for r in cur.fetchall():
            row = dict(r)
            try:
                row['timeline'] = json.loads(row['timeline']) if row.get('timeline') else None
            except Exception:
                row['timeline'] = None
            res.append(row)
        return res

# default instance
db = DatabaseManager()