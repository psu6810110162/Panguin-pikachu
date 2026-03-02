import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_FILE = "game.db"

class DatabaseManager:
    # คลาส Singleton สำหรับจัดการฐานข้อมูล SQLite
    # ใช้สำหรับสร้าง Schema, เก็บประวัติและสถิติของคนเล่น
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.conn = None
        return cls._instance

    def connect(self):
        if not self.conn:
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row
            
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_db(self):
        """ สร้างและเตรียมความพร้อมตารางในฐานข้อมูล SQLite """
        self.connect()
        cursor = self.conn.cursor()
        
        # 1. แฟ้มประวัติและกระเป๋าตัวละคร (Players Table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                gem_balance INTEGER DEFAULT 0,
                equipped_skin TEXT DEFAULT "default",
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. บันทึกประวัติการเล่นเป็นรอบๆ (Sessions Table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER REFERENCES players(id),
                played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                duration_s REAL DEFAULT 0.0
            )
        ''')
        
        # 3. เก็บคะแนนและระยะทางผูกกับรอบการเล่น (Scores Table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES sessions(id),
                distance_m INTEGER NOT NULL,
                gems_collected INTEGER DEFAULT 0,
                obstacles_cleared INTEGER DEFAULT 0
            )
        ''')
        
        # 4. ตารางสกินตัวละครที่ซื้อแล้ว (Player Skins Table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_skins (
                player_id INTEGER REFERENCES players(id),
                skin_id TEXT NOT NULL,
                purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id, skin_id)
            )
        ''')
        
        self.conn.commit()
        print("[DB] Initialized tables successfully.")

    # ==========================
    # ระบบ Leaderboard & Queries
    # ==========================
        
    def get_or_create_player(self, name: str) -> int:
        """ ดึง ID ตัวละครตามชื่อ (ถ้าไม่มีชื่อในระบบจะสร้างให้ใหม่) """
        self.connect()
        cursor = self.conn.cursor()
        
        # ค้นหาไอดีจากชื่อ
        cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            return row['id']
            
        # สร้างโปรไฟล์ใหม่
        cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
        self.conn.commit()
        return cursor.lastrowid

    def save_game_session(self, player_name: str, distance: int, gems: int, duration: float = 0.0):
        """ บันทึกคะแนน ระยะทาง และไอเทม เมื่อจบเกมแต่ละรอบ """
        player_id = self.get_or_create_player(player_name)
        
        cursor = self.conn.cursor()
        
        # ทบจำนวน Gem เข้ากระเป๋าหลัก
        cursor.execute("UPDATE players SET gem_balance = gem_balance + ? WHERE id = ?", (gems, player_id))
        
        # สร้างใบประวัติ Session ใหม่
        cursor.execute("INSERT INTO sessions (player_id, duration_s) VALUES (?, ?)", (player_id, duration))
        session_id = cursor.lastrowid
        
        # บันทึกคะแนนลง Score ผูกกับ Session
        cursor.execute("INSERT INTO scores (session_id, distance_m, gems_collected) VALUES (?, ?, ?)", 
                       (session_id, distance, gems))
        
        self.conn.commit()

    def get_personal_best(self, player_name: str) -> int:
        """ ดึงคะแนนสูงสุด (Personal Best) ของผู้เล่นชื่อนี้ """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT MAX(s.distance_m) as pb
            FROM scores s 
            JOIN sessions ss ON s.session_id = ss.id
            JOIN players p ON ss.player_id = p.id
            WHERE p.name = ?
        ''', (player_name,))
        
        row = cursor.fetchone()
        return row['pb'] if row and row['pb'] else 0

    def get_history(self, player_name: str, limit: int = 50) -> List[Dict]:
        """ ดึงประวัติการวิ่งย้อนหลัง ไว้แสดงผลในหน้า History """
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

if __name__ == "__main__":
    db = DatabaseManager()
    db.init_db()
    
    print("Testing record insertion...")
    db.save_game_session("Arm", distance=150, gems=5)
    db.save_game_session("Arm", distance=200, gems=12)
    db.save_game_session("Pikachu", distance=85, gems=1)
    
    print(f"Arm's PB: {db.get_personal_best('Arm')} m")
    print(f"Arm's History: {db.get_history('Arm')}")
    
    db.close()
