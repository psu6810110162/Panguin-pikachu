# ตั้งค่าหน้าจอ
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
TARGET_FPS = 60

# ตั้งค่า Grid (กะระยะ 1 ช่อง = 1 เมตร)
GRID_WIDTH = 100
GRID_HEIGHT = 100
TILE_SIZE = 1           # ปรับสเกลภาพของช่องเดิน
TILE_TO_METER = 1       # 1 ช่อง = ระยะ 1 เมตร

# ตั้งค่าความเร็ว (ความยาก)
INITIAL_SPEED = 2.0     # ความเร็วตั้งต้น
SPEED_MULTIPLIER = 1.05 # ตัวคูณเพิ่มความเร็วตามระยะทาง
MAX_SPEED = 10.0        # เพดานความเร็วสูงสุด

# กลไกในเกม
REVIVE_COST_GEM = 100   # ทะลุหลุมใช้ Gem ชุบชีวิต 100 เม็ด