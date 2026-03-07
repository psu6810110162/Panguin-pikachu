from enum import Enum, auto

class GameState(Enum):
    """ โครงสร้าง Enum สำหรับเก็บสถานะปัจจุบันของเกม """
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAMEOVER = auto()
    HISTORY = auto()
    SHOP = auto()

class StateManager:
    # คลาส Singleton ที่รับหน้าที่เปลี่ยนย้าย State ภาพรวมของเกม
    # เพื่อป้องกันการสับ State ชนกันระหว่างหน้าจอ
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.current_state = GameState.MENU
            cls._instance.selected_skin = 'Ninja Frog'
        return cls._instance
    
    def change_state(self, new_state: GameState):
        self.current_state = new_state
        print(f"[State] Changed to: {new_state.name}")
        
    def is_playing(self):
        return self.current_state == GameState.PLAYING
