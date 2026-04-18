import sqlite3  # นำเข้าไลบรารีสำหรับจัดการฐานข้อมูล SQLite
import os       # นำเข้าไลบรารีสำหรับจัดการไฟล์และโฟลเดอร์
from datetime import datetime # นำเข้าคลาสจัดการวันที่และเวลา
from typing import List, Dict, Optional # นำเข้าตัวช่วยระบุประเภทข้อมูล (Type Hinting)
from core.logger import logger
from core.config import DEFAULT_PLAYER_NAME

DB_FILE = "game.db" # ชื่อไฟล์ฐานข้อมูลที่ใช้จัดเก็บ

class DatabaseManager:
    """
    คลาส Singleton สำหรับจัดการฐานข้อมูล SQLite
    - ใช้สำหรับสร้างตาราง (Schema)
    - เก็บประวัติกาารเล่น, สถิติระยะทาง, จำนวน Gem และสกินที่ซื้อแล้ว
    """
    _instance = None # ตัวแปรเก็บ Instance เดียวของคลาสนี้ (Singleton)
    
    def __new__(cls):
        """ ฟังก์ชันสร้าง Instance ใหม่ (จะสร้างเพียงครั้งเดียวตลอดการทำงานของโปรแกรม) """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.conn = None # ตัวแปรเก็บการเชื่อมต่อ (Connection)
        return cls._instance

    def connect(self):
        """ เริ่มต้นการเชื่อมต่อกับไฟล์ฐานข้อมูล """
        if not self.conn:
            self.conn = sqlite3.connect(DB_FILE) # เชื่อมต่อไฟล์ game.db
            self.conn.row_factory = sqlite3.Row  # ตั้งค่าให้ดึงข้อมูลออกมาในรูปแบบ Dictionary (เข้าถึงด้วยชื่อคอลัมน์ได้)
            self._ensure_tables() # ตรวจสอบและสร้างตารางถ้ายังไม่มี

    def _ensure_tables(self):
        """ ตรวจสอบและสร้างตารางพื้นฐานที่จำเป็นสำหรับตัวเกม """
        cursor = self.conn.cursor()
        
        # ตารางผู้เล่น (id, ชื่อ, จำนวน Gem, สกินที่ใส่)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            gem_balance INTEGER DEFAULT 0,
            equipped_skin TEXT DEFAULT "default",
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ตารางรอบการเล่น (Session ว่าเล่นเมื่อไหร่ นานแค่ไหน)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER REFERENCES players(id),
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            duration_s REAL DEFAULT 0.0
            )
        ''')
        
        # ตารางบันทึกคะแนนละเอียด (ระยะทาง, Gem ที่เก็บได้, อุปสรรคที่ผ่าน)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions(id),
            distance_m INTEGER NOT NULL,
            gems_collected INTEGER DEFAULT 0,
            obstacles_cleared INTEGER DEFAULT 0
            )
        ''')
        
        # ตารางเก็บรายการสกินที่ผู้เล่นคนนั้นๆ เป็นเจ้าของแล้ว
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_skins (
            player_id INTEGER REFERENCES players(id),
            skin_id TEXT NOT NULL,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, skin_id)
            )
        ''')
        self.conn.commit() # บันทึกการเปลี่ยนแปลงลงไฟล์
            
    def close(self):
        """ ปิดการเชื่อมต่อฐานข้อมูล """
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_db(self):
        """ ฟังก์ชันสาธารณะสำหรับเตรียมไฟล์ฐานข้อมูลให้พร้อม (เรียกจาก main.py) """
        self.connect()  # connect() calls _ensure_tables() internally
        logger.info("Database initialized.")

    # ==========================
    # ระบบจัดการข้อมูลผู้เล่นและสถิติ
    # ==========================
        
    def get_or_create_player(self, name: str) -> int:
        """ ดึง ID ของผู้เล่นจากชื่อ (ถ้าไม่เคยมีชื่อนี้มาก่อน จะสร้างโปรไฟล์ใหม่ให้ทันที) """
        self.connect()
        cursor = self.conn.cursor()
        
        # ลองค้นหาจากชื่อก่อน
        cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            return row['id'] # ถ้าเจอ คืนค่า ID เดิม
            
        # ถ้าไม่เจอ สร้างแถวข้อมูลใหม่
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid # คืนค่า ID ที่เพิ่งสร้างใหม่

    def save_game_session(self, player_name: str, distance: int, gems: int, duration: float = 0.0):
        """ บันทึกผลการเล่น "เมื่อจบเกม" (ระยะทาง, Gem, เวลาที่ใช้) """
        player_id = self.get_or_create_player(player_name)
        
        cursor = self.conn.cursor()
        
        # 1. อัปเดตยอด Gem รวมในกระเป๋าหลักของผู้เล่น
        cursor.execute("UPDATE players SET gem_balance = gem_balance + ? WHERE id = ?", (gems, player_id))
        
        # 2. บันทึกรอบการเล่น (Session)
        cursor.execute("INSERT INTO sessions (player_id, duration_s) VALUES (?, ?)", (player_id, duration))
        session_id = cursor.lastrowid
        
        # 3. บันทึกคะแนนและสถิติผูกกับ Session นั้น
        cursor.execute("INSERT INTO scores (session_id, distance_m, gems_collected) VALUES (?, ?, ?)", 
                       (session_id, distance, gems))
        
        self.conn.commit()

    def get_gem_balance(self, player_name: str) -> int:
        """ ตรวจสอบจำนวน Gem ปัจจุบันในกระเป๋าหลักของผู้เล่น """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT gem_balance FROM players WHERE name = ?", (player_name,))
        row = cursor.fetchone()
        return row['gem_balance'] if row else 0

    def deduct_gems(self, player_name: str, amount: int) -> bool:
        """ หัก Gem ออกจากกระเป๋า (ใช้เมื่อซื้อของใน Shop) คืนค่า True ถ้าหักสำเร็จ """
        current_balance = self.get_gem_balance(player_name)
        if current_balance < amount:
            return False # ยอดเงินไม่พอ
            
        cursor = self.conn.cursor()
        cursor.execute("UPDATE players SET gem_balance = gem_balance - ? WHERE name = ?", (amount, player_name))
        self.conn.commit()
        return True

    def get_personal_best(self, player_name: str) -> int:
        """ ดึงสถิติระยะทางที่ไกลที่สุด (Personal Best) ของผู้เล่นนั้นๆ """
        self.connect()
        cursor = self.conn.cursor()
        # ใช้คำสั่ง SQL JOIN เพื่อเชื่อม 3 ตารางแล้วหาค่า MAX ของระยะทาง
        cursor.execute('''
            SELECT MAX(s.distance_m) as pb
            FROM scores s 
            JOIN sessions ss ON s.session_id = ss.id
            JOIN players p ON ss.player_id = p.id
            WHERE p.name = ?
        ''', (player_name,))
        
        row = cursor.fetchone()
        return row['pb'] if row and row['pb'] else 0

    def get_history(self, player_name: str, limit: int = 100) -> List[Dict]:
        """ ดึงประวัติการเล่นย้อนหลัง (สูงสุด 100 รายการ) เพื่อแสดงในหน้า History """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ss.played_at, s.distance_m, s.gems_collected
            FROM scores s 
            JOIN sessions ss ON s.session_id = ss.id
            JOIN players p ON ss.player_id = p.id
            WHERE p.name = ?
            ORDER BY ss.played_at DESC 
            LIMIT ?
        ''', (player_name, limit))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_last_player_name(self) -> str:
        """ ดึงชื่อผู้เล่นที่เพิ่งเล่นล่าสุดออกมา เพื่อนำไปใส่ในช่องชื่ออัตโนมัติ """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.name 
            FROM players p
            JOIN sessions s ON p.id = s.player_id
            ORDER BY s.played_at DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        return row['name'] if row else DEFAULT_PLAYER_NAME

    def is_skin_owned(self, player_name: str, skin_id: str) -> bool:
        """ ตรวจสอบว่าผู้เล่นมีสกินไอดีนี้ในครอบครองหรือยัง """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 1 FROM player_skins ps
            JOIN players p ON ps.player_id = p.id
            WHERE p.name = ? AND ps.skin_id = ?
        ''', (player_name, skin_id))
        return cursor.fetchone() is not None

    def add_owned_skin(self, player_name: str, skin_id: str):
        """ เพิ่มสกินเข้าคลังของผู้เล่น (ใช้เมื่อกดซื้อสำเร็จ) """
        player_id = self.get_or_create_player(player_name)
        self.connect()
        cursor = self.conn.cursor()
        # ใช้ INSERT OR IGNORE เพื่อป้องกันการเพิ่มข้อมูลซ้ำกรณีมีอยู่แล้ว
        cursor.execute('''
            INSERT OR IGNORE INTO player_skins (player_id, skin_id)
            VALUES (?, ?)
        ''', (player_id, skin_id))
        self.conn.commit()

