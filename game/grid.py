from core.config import (
    TILE_TO_METER,
    PATH_WIDTH, SEGMENT_LEN_MIN, SEGMENT_LEN_MAX,
    PRELOAD_SEGMENTS, VISIBLE_BUFFER, FORK_CHANCE,
    FORK_SHORT_LEN, FORK_LONG_LEN, FORK_SIDE_OFFSET,
)
import random                             # นำเข้าไลบรารีสุ่ม
from game.obstacle_factory import ObstacleFactory # นำเข้าโรงงานผลิตอุปสรรค


class GridManager:
    """
    คลาสจัดการตาราง (Grid) และการสร้างทางเดินซิกแซกแบบไร้จุดจบ
    - เก็บข้อมูลตำแหน่งพื้น, สิ่งกีดขวาง และ Gem
    - มีระบบทางแยก (Diamond Fork) ที่บรรจบกลับมาที่เดิม
    """

    DIR_A = (1, 0)   # ทิศเฉียงขวา (เพิ่ม Col) ในมุมมอง Isometric
    DIR_B = (0, 1)   # ทิศเฉียงซ้าย (เพิ่ม Row) ในมุมมอง Isometric

    def __init__(self):
        self.forward_tiles  = 0     # นับจำนวนแผ่นพื้นที่เดินไปข้างหน้า (ใช้คำนวณระยะทาง)
        self.path           = []    # รายการพิกัดกึ่งกลางทางเดิน (Centerline)
        self.path_set       = set() # รวบรวมพิกัดพื้นทั้งหมด (ใช้เช็คการตกพื้น)
        self.turn_points    = []    # เก็บพิกัดจุดที่ต้องหันเลี้ยว
        self.obstacles      = {}    # เก็บพิกัดและตัววัตถุสิ่งกีดขวาง (พิกัด -> วัตถุ)
        self.gems           = {}    # เก็บพิกัดและตัว Gem (พิกัด -> วัตถุ)
        self.fork_tiles     = set() # เก็บพิกัดที่เป็นส่วนของทางแยก (เพื่อทาสีต่างออกไป)
        self.merge_points   = []    # เก็บจุดที่ทางแยกกลับมาบรรจบกัน

        self._last_pos  = (0, 0)    # ตำแหน่งสุดท้ายที่สร้างพื้นถึง
        self._last_dir  = self.DIR_A # ทิศทางสุดท้ายที่ใช้ในการสร้างพื้น
        self._seg_count = 0         # นับจำนวนช่วงทางเดินที่สร้างไปแล้ว
        self._last_cleaned_idx = 0  # ดัชนีล่าสุดที่ทำการลบพื้นหลังที่เดินผ่านมาแล้ว

    # ═══════════════════════════════════════════
    #  ฟังก์ชันสาธารณะ (Public API)
    # ═══════════════════════════════════════════

    def reset(self):
        """ ล้างข้อมูลทั้งหมดเพื่อเริ่มเกมใหม่ """
        self.forward_tiles  = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        self.obstacles.clear()
        self.gems.clear()
        self.fork_tiles.clear()
        self.merge_points.clear()
        self._last_pos  = (0, 0)
        self._last_dir  = self.DIR_A
        self._seg_count = 0
        self._last_cleaned_idx = 0
        self._build_start_platform() # สร้างพื้นเริ่มเกมขนาด 3x3
        for _ in range(PRELOAD_SEGMENTS):
            self._append_segment() # สร้างช่วงทางเดินล่วงหน้าตามจำนวนที่ตั้งไว้

    def step_forward(self):
        """ นํบจำนวนแผ่นพื้นที่เดินก้าวหน้าไป (ถูกเรียกเมื่อผู้เล่นเลี้ยวถูกทาง) """
        self.forward_tiles += 1

    def get_distance_m(self):
        """ คำนวณระยะทางเป็นเมตร: จำนวนแผ่นพื้น x ตัวคูณ (เช่น 1 แผ่น = 1 เมตร) """
        return self.forward_tiles * TILE_TO_METER

    def update_obstacles(self, dt, view_radius, penguin_pos):
        """ อัปเดตแอนิเมชันของกล่องและ Gem เฉพาะที่อยู่ในระยะการมองเห็นของผู้เล่น """
        p_col, p_row = penguin_pos # พิกัดปัจจุบันของเพนกวิน
        for pos, obs in self.obstacles.items():
            if obs.active:
                # เช็คว่าอยู่ในรัศมีสายตา (Bounding Box) หรือไม่
                if (p_col - view_radius <= pos[0] <= p_col + view_radius) and \
                   (p_row - view_radius <= pos[1] <= p_row + view_radius):
                    obs.update(dt) # สั่งให้อัปเดตเฟรมภาพ
        
        # อัปเดตการหมุนของ Gem
        for pos, gem in self.gems.items():
            if gem.active:
                if (p_col - view_radius <= pos[0] <= p_col + view_radius) and \
                   (p_row - view_radius <= pos[1] <= p_row + view_radius):
                    gem.update(dt)

    def is_on_path(self, col, row):
        """ ตรวจสอบว่าพิกัด (col, row) นี้มีแผ่นพื้นอยู่หรือไม่ (ถ้าไม่มีแสดงว่าตก) """
        return (col, row) in self.path_set

    def get_obstacle_at(self, col, row):
        """ ดึงวัตถุสิ่งกีดขวาง ณ ตำแหน่งนั้น (ถ้ามีและยังเปิดใช้งานอยู่) """
        obs = self.obstacles.get((col, row))
        if obs and obs.active:
            return obs
        return None

    def get_gem_at(self, col, row):
        """ ดึงวัตถุ Gem ณ ตำแหน่งนั้น """
        gem = self.gems.get((col, row))
        if gem and gem.active:
            return gem
        return None

    def get_path_index(self, col, row):
        """ หาว่าพิกัดนี้แผ่นที่เป็นลำดับที่เท่าไหร่ในทางกึ่งกลาง (Centerline) """
        try:
            return self.path.index((col, row))
        except ValueError:
            return -1

    def get_correct_direction_at(self, path_index):
        """ หาว่า ณ ตำแหน่งนี้ ทิศทางไปข้างหน้าที่ถูกต้องคือทิศไหน (ใช้สอนผู้เล่นหรือเช็คเงื่อนไข) """
        if path_index + 1 < len(self.path):
            c  = self.path[path_index]    # แผ่นปัจจุบัน
            n  = self.path[path_index + 1] # แผ่นถัดไป
            return (n[0] - c[0], n[1] - c[1]) # ผลต่างพิกัดคือทิศทาง
        return None

    def extend_if_needed(self, path_index):
        """ ตรวจสอบระยะห่าง ถ้าเดินเข้าใกล้ปลายทางที่สร้างไว้ ให้สร้างทางเพิ่มอัตโนมัติ """
        if len(self.path) - path_index < VISIBLE_BUFFER:
            self._append_segment()

    def is_fork_tile(self, col, row):
        """ ตรวจสอบว่าเป็นพื้นส่วนทางแยกหรือไม่ (ใช้ตอนวาดภาพเพื่อเปลี่ยนสีพื้น) """
        return (col, row) in self.fork_tiles

    def is_merge_point(self, col, row):
        """ ตรวจสอบว่าเป็นจุดที่ทางแยกกลับมาบรรจบกันหรือไม่ """
        return (col, row) in self.merge_points

    def remove_tile(self, col, row):
        """ ลบแผ่นพื้นออกจากแผนที่ (ใช้สำหรับระบบ "พื้นถล่ม" เมื่อเพนกวินยืนนิ่งนานเกินไป) """
        pos = (col, row)
        if pos in self.path_set:
            self.path_set.remove(pos) # ลบออกจากเซตพื้น
        # ลบสิ่งของที่อยู่บนพื้นนั้นด้วย
        self.obstacles.pop(pos, None)
        self.gems.pop(pos, None)

    def cleanup_behind(self, path_index):
        """ ระบบจัดการหน่วยความจำ: ลบสิ่งของ (กล่อง/Gem) ที่ผู้เล่นเดินผ่านมาไกลมากแล้ว """
        target_idx = path_index - 20 # กำหนดระยะปลอดภัยคือกองหลัง 20 ช่อง
        if target_idx <= self._last_cleaned_idx: return
        
        # ไล่ลบจากดัชนีล่าสุดที่เพิ่งล้างไป จนถึงระยะปลอดภัย
        for i in range(self._last_cleaned_idx, target_idx):
            if i >= len(self.path): break
            pos = self.path[i]
            self.obstacles.pop(pos, None)
            self.gems.pop(pos, None)
            self.path_set.discard(pos)  # ลบ tile เก่าออกเพื่อไม่ให้ render loop iterate ตลอด
            
        self._last_cleaned_idx = target_idx # อัปเดตจุดที่ล้างล่าสุด

    # ═══════════════════════════════════════════
    #  ฟังก์ชันภายในสำหรับการสร้าง (Internal Builders)
    # ═══════════════════════════════════════════

    def _build_start_platform(self):
        """ สร้างแท่นเริ่มเกมขนาด 3x3 เพื่อให้ผู้เล่นมีพื้นที่ตั้งตัวก่อนเริ่มวิ่ง """
        for c in range(3):
            for r in range(3):
                self.path_set.add((c, r))
        center = (1, 1) # กำหนดจุดกึ่งกลาง (1,1) เป็นจุดเริ่มเดิน
        self.path.append(center)
        self._last_pos = center # บันทึกไว้เป็นจุดต้นหาครั้งถัดไป

    def _append_segment(self):
        """ สร้างช่วงทางเดิน 1 ช่วง: อาจจะเป็น "ทางตรง" หรือ "ทางแยก" (สุ่ม 30%) """
        if random.random() < FORK_CHANCE and self._seg_count >= 2:
            # --- สร้างทางแยก (Diamond Fork) ---
            self._build_diamond_fork()
        else:
            # --- สร้างช่วงทางตรง ---
            self._build_straight(random.randint(SEGMENT_LEN_MIN, SEGMENT_LEN_MAX))

        # หลังจากจบช่วง (ตรง/แยก) ให้สร้างจุดหักเลี้ยว (Corner) เพื่อเปลี่ยนทิศทาง
        self._build_corner()
        self._seg_count += 1

    # ───────────────────────────────────────────
    #  การสร้างทางตรง (Straight segment)
    # ───────────────────────────────────────────
    def _build_straight(self, length, mark_fork=False):
        """ สร้างพื้นตรงไปทางทิศปัจจุบันตามความยาวที่ระบุ """
        col, row = self._last_pos
        cur_dir  = self._last_dir # ทิศทางที่จะมุ่งไป (DIR_A หรือ DIR_B)
        for _ in range(length):
            col += cur_dir[0]
            row += cur_dir[1]
            self._add_center(col, row) # เพิ่มจุดเข้า Centerline
            self._add_width(col, row, cur_dir) # เพิ่มความกว้างให้ทาง (ถ้า PATH_WIDTH > 1)
            if mark_fork:
                self.fork_tiles.add((col, row))
            
            # สุ่มวางกล่องอุปสรรค (โอกาส 20%) บนทางเดินหลัก
            if self._seg_count > 0 and random.random() < 0.2 and not mark_fork:
                if (col, row) not in self.obstacles:
                    dist = self.get_distance_m() # คำนวณความยากตามระยะทาง
                    obs = ObstacleFactory.spawn_obstacle(dist, col, row)
                    self.obstacles[(col, row)] = obs
            
            # สุ่มวาง Gem (โอกาส 40%) ถ้าจุดนั้นไม่มีกล่องวางอยู่
            elif self._seg_count > 0 and random.random() < 0.4 and not mark_fork:
                if (col, row) not in self.obstacles and (col, row) not in self.gems:
                    gem = ObstacleFactory.spawn_gem(col, row)
                    self.gems[(col, row)] = gem

        self._last_pos = (col, row) # อัปเดตจุดสุดท้าย

    # ───────────────────────────────────────────
    #  การสร้างทางแยกรูปเพชร (Diamond Fork)
    # ───────────────────────────────────────────
    def _build_diamond_fork(self):
        """
        สร้างทางแยกที่แยกออกไปแล้วกลับมาเจอกันที่จุดเดียว (Diamond-shaped)
          - เส้นสั้น: วิ่งตรงไปจุดบรรจบ (ทางลัด)
          - เส้นยาว: แยกออกด้านข้าง อ้อมไปเก็บ Gem แล้วกลับมาบรรจบ
        """
        start_col, start_row = self._last_pos
        cur_dir = self._last_dir
        # หา "ทิศตั้งฉาก" (Perpendicular) เพื่อใช้แยกออกด้านข้าง
        perp = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A

        # --- ส่วนของเส้นทางลัด (Branch Short) ---
        short_end = (
            start_col + cur_dir[0] * FORK_SHORT_LEN,
            start_row + cur_dir[1] * FORK_SHORT_LEN,
        )
        col, row = start_col, start_row
        for _ in range(FORK_SHORT_LEN):
            col += cur_dir[0]
            row += cur_dir[1]
            self._add_center(col, row)
            self._add_width(col, row, cur_dir)
        # จุดปลายสุดของเส้นลัดคือจุดบรรจบ (Merge Point)
        merge_col, merge_row = col, row

        # --- ส่วนของเส้นทางอ้อม (Branch Long) ---
        lc, lr = start_col, start_row
        # 1. เลี้ยวออกด้านข้าง
        for _ in range(FORK_SIDE_OFFSET):
            lc += perp[0]
            lr += perp[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr)) # มาร์คว่าเป็นทางแยกเพื่อทาสีพิเศษ

        # 2. วิ่งขนานไปทางทิศหลัก (มาร์คให้มี Gem เยอะเป็นพิเศษ)
        for _ in range(FORK_LONG_LEN):
            lc += cur_dir[0]
            lr += cur_dir[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr))
            
            # สุ่มวาง Gem บนทางอ้อม (โอกาสสูงถึง 60% เพื่อจูงใจให้คนอ้อมมาเก็บ)
            if random.random() < 0.6:
                if (lc, lr) not in self.gems:
                    gem = ObstacleFactory.spawn_gem(lc, lr)
                    self.gems[(lc, lr)] = gem

        # 3. เลี้ยวกลับเข้าหาจุดบรรจบ
        for _ in range(FORK_SIDE_OFFSET):
            lc -= perp[0]
            lr -= perp[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr))

        # บันทึกจุดบรรจบเพื่อให้ระบบรู้ว่าทางแยกจบลงที่นี่
        self.merge_points.append((merge_col, merge_row))
        self._last_pos = (merge_col, merge_row) # อัปเดตจุดสร้างต่อ

    # ───────────────────────────────────────────
    #  การสร้างจุดเลี้ยว (Corner)
    # ───────────────────────────────────────────
    def _build_corner(self):
        """ ทำการเลี้ยว 90 องศาเพื่อเปลี่ยนทิศทางการวิ่งซิกแซก """
        cur_dir = self._last_dir
        # สลับทิศทาง (ถ้าเดิน DIR_A อยู่ ให้เปลี่ยนเป็น DIR_B และในทางกลับกัน)
        nxt_dir = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A
        col, row = self._last_pos

        # บันทึกตำแหน่งนี้เป็นจุดที่ผู้เล่นต้องเลี้ยว
        self.turn_points.append((col, row))

        # ขยับไป 1 ก้าวในทิศทางใหม่เพื่อทำเป็นจุดเริ่มช่วงถัดไป
        col += nxt_dir[0]
        row += nxt_dir[1]
        self._add_center(col, row)

        self._last_pos = (col, row)
        self._last_dir = nxt_dir # บันทึกทิศทางใหม่ไว้ใช้งาน

    # ───────────────────────────────────────────
    #  เมธอดช่วยเหลือ (Helpers)
    # ───────────────────────────────────────────
    def _add_center(self, col, row):
        """ เพิ่มพิกัด (col, row) เข้าไปในรายการทางเดินกึ่งกลางหลัก """
        pos = (col, row)
        if pos not in self.path_set:
            self.path.append(pos)
            self.path_set.add(pos)

    def _add_width(self, col, row, direction):
        """ (ฟังก์ชันเสริม) เพิ่มความกว้างของทางเดินออกไปด้านข้าง (ถ้าตั้งค่า PATH_WIDTH > 1) """
        if PATH_WIDTH <= 1:
            return
            
        perp = (0, 1) if direction == self.DIR_A else (1, 0) # ทิศตั้งฉาก
        half = PATH_WIDTH // 2
        for sign in [1, -1]: # แผ่ออกทั้งสองด้าน
            for d in range(1, half + 1):
                self.path_set.add((col + perp[0]*d*sign,
                                   row + perp[1]*d*sign))
