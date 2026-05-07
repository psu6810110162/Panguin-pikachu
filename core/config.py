# ตั้งค่าขนาดหน้าจอพื้นฐาน (Pixels)
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
TARGET_FPS = 60 # เป้าหมายความลื่นไหลของเกม (เฟรมต่อวินาที)

# ตั้งค่าระบบตาราง (Grid System) - กะระยะ 1 ช่อง = 1 เมตร
GRID_WIDTH = 100
GRID_HEIGHT = 100
TILE_SIZE = 1           # ตัวคูณสเกลภาพของช่องเดิน
TILE_TO_METER = 1       # อัตราส่วน 1 ช่องตารางต่อระยะทาง 1 เมตร

# ตั้งค่าขนาด Tile สำหรับ Isometric (วัดจาก Asset จริงเพื่อให้วาดได้มุมที่ถูกต้อง)
TILE_W     = 130        # ความกว้างเต็มของแผ่นพื้น (Pixels)
TILE_H     = 65         # ความสูงเฉพาะผิวด้านบน (Ratio 2:1 สำหรับ Isometric)
TILE_IMG_H = 130        # ความสูงรวมของไฟล์ภาพ (รวมความหนาของดินด้านล่าง)

# ตั้งค่าความเร็ว (กลไกปรับความยากของเกม)
INITIAL_SPEED = 2.0     # ความเร็วเริ่มต้นเมื่อเริ่มวิ่ง
SPEED_MULTIPLIER = 1.05 # ตัวคูณสำหรับเพิ่มความเร็วขึ้นเรื่อยๆ ตามระยะทางที่วิ่งได้
MAX_SPEED = 10.0        # เพดานความเร็วสูงสุดที่เกมจะยอมให้เร็วได้

# กลไกอื่นๆ ในเกม
REVIVE_COST_GEM = 100   # ค่าธรรมเนียมในการชุบชีวิตเมื่อตกหลุม (ใช้ 100 Gem)

# --- Rendering / Pixel values ---
BOX_FRAME_W      = 28   # width of one Box2 spritesheet frame (px)
BOX_FRAME_H      = 24   # height of one Box2 spritesheet frame (px)
BOX_DRAW_W       = 56   # drawn width of box on screen
BOX_DRAW_H       = 48   # drawn height of box on screen
GEM_FLOAT_OFFSET = 12   # pixels gem floats above tile surface
GEM_FRAME_W      = 16   # width of one gem spritesheet frame (px)
GEM_FRAME_H      = 16   # height of one gem spritesheet frame (px)
GEM_DRAW_W       = 32   # drawn width of gem on screen
GEM_DRAW_H       = 32   # drawn height of gem on screen
PENGUIN_DRAW_SIZE  = 64  # drawn width/height of penguin sprite on screen
PENGUIN_SPRITE_W   = 32  # pixel width of one frame in the penguin spritesheet
VIEW_RADIUS        = 15  # tile radius rendered around penguin

# --- Camera ---
CAMERA_LERP = 0.15  # camera smoothing factor per frame
SHAKE_DECAY = 0.8   # multiplier applied to shake_amount each frame
SHAKE_STOP  = 0.5   # threshold below which shake is zeroed

# --- Grid / Path generation ---
PATH_WIDTH       = 1
SEGMENT_LEN_MIN  = 5     # minimum tiles per straight run (was 2)
SEGMENT_LEN_MAX  = 12    # maximum tiles per straight run (was 6)
PRELOAD_SEGMENTS = 8
VISIBLE_BUFFER   = 60
FORK_CHANCE      = 0.30
FORK_SHORT_LEN   = 4
FORK_LONG_LEN    = 7
FORK_SIDE_OFFSET = 2

# --- Animation speeds ---
OBSTACLE_ANIM_SPEED = 0.1   # seconds per frame for obstacle animations
GEM_ANIM_SPEED      = 0.15  # seconds per frame for gem animation

# --- Gameplay timing ---
MAX_IDLE_TIME = 2.0  # seconds idle before floor collapses

# --- Isometric movement directions ---
DIR_LEFT  = (0, 1)
DIR_RIGHT = (1, 0)

# --- Default player name (fallback) ---
DEFAULT_PLAYER_NAME = "Explorer"

# --- Buff durations ---
GOLD_BUFF_DURATION = 5.0   # วิ — Gold buff (force prop)
DARK_BUFF_DURATION = 5.0   # วิ — Dark buff (reverse prop)

# --- Quiz Event (Active Learning) ---
QUIZ_INTERVAL_MIN = 50     # m — popup เร็วสุด
QUIZ_INTERVAL_MAX = 100    # m — popup ช้าสุด
