from enum import Enum, auto
from core.logger import logger

class GameState(Enum):
    """ รายการสถานะต่างๆ ของเกม (Menu, Playing, Shop, ฯลฯ) """
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAMEOVER = auto()
    HISTORY = auto()
    SHOP = auto()

class StateManager:
    """ 
    StateManager (Singleton)
    ทำหน้าที่เก็บสถานะส่วนกลางของแอปพลิเคชัน เช่น กำลังเล่นอยู่หรือไม่ หรือผู้เล่นใช้สกินอะไร
    เพื่อแชร์ข้อมูลข้ามไปมาระหว่างหน้าจอต่างๆ ได้อย่างปลอดภัย
    """
    _instance = None
    
    def __new__(cls):
        # ตรวจสอบว่าเป็น Instance แรกหรือไม่ (Singleton Pattern)
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.current_state = GameState.MENU # สถานะเริ่มต้นคือเมนู
            cls._instance.selected_skin = 'Classic'         # สกินเริ่มต้น
        return cls._instance
    
    def change_state(self, new_state: GameState):
        """ สั่งเปลี่ยนสถานะของเกม """
        self.current_state = new_state
        logger.info(f"State changed to: {new_state.name}")
        
    def is_playing(self):
        """ ตรวจสอบว่าขณะนี้เกมกำลังดำเนินการเล่นอยู่หรือไม่ """
        return self.current_state == GameState.PLAYING
