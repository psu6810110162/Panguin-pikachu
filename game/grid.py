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
        self.obstacles      = {}    # (col, row) → prop string (ice1/ice2/ice3/force/reverse/trap)
        self.gems           = {}    # เก็บพิกัดและตัว Gem (พิกัด -> วัตถุ)
        self.fork_tiles     = set() # เก็บพิกัดที่เป็นส่วนของทางแยก (เพื่อทาสีต่างออกไป)
        self.merge_points   = []    # เก็บจุดที่ทางแยกกลับมาบรรจบกัน
        self.falling_tiles  = {}    # (col, row) → seconds_remaining ก่อนพื้นร่วง
        self.trap_states    = {}    # (col, row) → {'open': bool, 'type': 'seals'|'tail', 'timer': float}

        self._last_pos        = (0, 0)    # ตำแหน่งสุดท้ายที่สร้างพื้นถึง
        self._last_dir        = self.DIR_A # ทิศทางสุดท้ายที่ใช้ในการสร้างพื้น
        self._seg_count       = 0          # นับจำนวนช่วงทางเดินที่สร้างไปแล้ว
        self._last_cleaned_idx= 0          # ดัชนีล่าสุดที่ทำการลบพื้นหลังที่เดินผ่านมาแล้ว
        self._used_positions  = set()      # ทุก pos ที่เคย add — ป้องกัน spawn ซ้ำหลัง cleanup
        self.path_index_map   = {}         # (col,row) → index ใน path — O(1) lookup สำหรับ renderer
        self._last_force_dist = 0          # ระยะทาง tile ล่าสุดที่ spawn force — บังคับ 100m gap

    # ═══════════════════════════════════════════
    #  ฟังก์ชันสาธารณะ (Public API)
    # ═══════════════════════════════════════════

    def reset(self):
        """ ล้างข้อมูลทั้งหมดเพื่อเริ่มเกมใหม่ """
        # คืน gem objects กลับ pool ก่อน clear — ป้องกัน pool leak ระหว่าง restart
        for gem in self.gems.values():
            gem.active = False
        self.forward_tiles  = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        self.obstacles.clear()
        self.gems.clear()
        self.fork_tiles.clear()
        self.merge_points.clear()
        self.falling_tiles.clear()
        self.trap_states.clear()
        self._last_pos         = (0, 0)
        self._last_dir         = self.DIR_A
        self._seg_count        = 0
        self._last_cleaned_idx = 0
        self._used_positions.clear()
        self.path_index_map.clear()
        self._last_force_dist  = 0
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
        """ อัปเดตแอนิเมชัน Gem เฉพาะที่อยู่ในระยะการมองเห็น (obstacles เป็น string ไม่ต้อง update) """
        p_col, p_row = penguin_pos
        for pos, gem in self.gems.items():
            if gem.active:
                if (p_col - view_radius <= pos[0] <= p_col + view_radius) and \
                   (p_row - view_radius <= pos[1] <= p_row + view_radius):
                    gem.update(dt)

    def is_on_path(self, col, row):
        """ ตรวจสอบว่าพิกัด (col, row) นี้มีแผ่นพื้นอยู่หรือไม่ (ถ้าไม่มีแสดงว่าตก) """
        return (col, row) in self.path_set

    def get_obstacle_at(self, col, row):
        """ คืน prop string ณ ตำแหน่งนั้น หรือ "" ถ้าไม่มี """
        return self.obstacles.get((col, row), "")

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

    def mark_falling(self, col, row, awareness_m):
        """Falling floor — delay = max(0.1, 3*(1 − awareness/1000)) จาก JS FloorBrick.tryDown"""
        delay = max(0.1, 3.0 * (1.0 - awareness_m / 1000.0))
        self.falling_tiles[(col, row)] = delay

    def update_falling(self, dt):
        """ลด timer ของ falling tiles, ลบพื้นออกเมื่อหมดเวลา"""
        done = [p for p, t in self.falling_tiles.items() if t - dt <= 0]
        for p in done:
            self.remove_tile(*p)
            del self.falling_tiles[p]
        for p in list(self.falling_tiles):
            if p not in done:
                self.falling_tiles[p] -= dt

    def update_traps(self, dt):
        """สลับสถานะ open/close และ type ของ trap ตาม timer (เหมือน JS Trap.js)"""
        for state in self.trap_states.values():
            state['timer'] -= dt
            if state['timer'] <= 0:
                state['open'] = not state['open']
                state['timer'] = 1.5 if state['open'] else 0.5
                if not state['open']:
                    state['type'] = 'tail' if state['type'] == 'seals' else 'seals'

    def init_trap(self, col, row):
        """เรียกตอน spawn trap prop เพื่อเริ่มต้น state"""
        import random as _r
        self.trap_states[(col, row)] = {
            'open':  False,
            'type':  'seals' if _r.random() < 0.5 else 'tail',
            'timer': 0.5,
        }

    def cleanup_behind(self, path_index):
        """ ระบบจัดการหน่วยความจำ: ลบสิ่งของ (กล่อง/Gem) ที่ผู้เล่นเดินผ่านมาไกลมากแล้ว """
        target_idx = path_index - 20 # กำหนดระยะปลอดภัยคือกองหลัง 20 ช่อง
        if target_idx <= self._last_cleaned_idx: return
        
        # ไล่ลบจากดัชนีล่าสุดที่เพิ่งล้างไป จนถึงระยะปลอดภัย
        for i in range(self._last_cleaned_idx, target_idx):
            if i >= len(self.path): break
            pos = self.path[i]
            self.obstacles.pop(pos, None)
            # คืน gem กลับ pool โดย set active=False ก่อน pop — ป้องกัน pool leak
            gem = self.gems.pop(pos, None)
            if gem:
                gem.active = False
            self.falling_tiles.pop(pos, None)
            self.trap_states.pop(pos, None)
            self.path_set.discard(pos)  # ลบ tile เก่าออกเพื่อไม่ให้ render loop iterate ตลอด

        self._last_cleaned_idx = target_idx # อัปเดตจุดที่ล้างล่าสุด

    # ═══════════════════════════════════════════
    #  ฟังก์ชันภายในสำหรับการสร้าง (Internal Builders)
    # ═══════════════════════════════════════════

    def _build_start_platform(self):
        """
        สร้างแท่นเริ่มเกมขนาด 3×3
        - path เริ่มที่ (1,1) → (2,1) เพื่อให้ต่อเนื่องกับ segment แรก (DIR_A = (1,0))
        - ถ้าไม่เพิ่ม (2,1) เข้า path ไว้ก่อน _build_straight จะข้ามมันเพราะอยู่ใน path_set แล้ว
          ทำให้ path มีช่องว่าง (1,1)→(3,1) — แก้ด้วยการ pre-add tile ขอบ platform
        """
        for c in range(3):
            for r in range(3):
                pos = (c, r)
                self.path_set.add(pos)
                self._used_positions.add(pos)   # ป้องกัน obstacle spawn ที่ start platform

        self.path_index_map[(1, 1)] = 0
        self.path_index_map[(2, 1)] = 1
        self.path.append((1, 1))   # จุดเริ่มเดิน
        self.path.append((2, 1))   # tile ขอบ platform ในทิศ DIR_A — ปิดช่องว่าง path
        self._last_pos = (2, 1)    # segment แรกเริ่มต่อจากขอบ platform

    def _append_segment(self):
        """ สร้างช่วงทางเดิน 1 ช่วง: อาจจะเป็น "ทางตรง" หรือ "ทางแยก" (สุ่ม 30%) """
        if random.random() < FORK_CHANCE and self._seg_count >= 2:
            # --- สร้างทางแยก (Diamond Fork) ---
            self._build_diamond_fork()
        else:
            # --- สร้างช่วงทางตรง (ยาวขึ้นตามระยะทาง = corridors ยาว = มีแรงกดดันมากขึ้น) ---
            dist = self.get_distance_m()
            extra = min(6, int(dist) // 100)   # +1 tile ต่อ 100m, สูงสุด +6
            seg_len = random.randint(SEGMENT_LEN_MIN + extra, SEGMENT_LEN_MAX + extra)
            self._build_straight(seg_len)

        # หลังจากจบช่วง (ตรง/แยก) ให้สร้างจุดหักเลี้ยว (Corner) เพื่อเปลี่ยนทิศทาง
        self._build_corner()
        self._seg_count += 1

    # ───────────────────────────────────────────
    #  การสร้างทางตรง (Straight segment)
    # ───────────────────────────────────────────
    # ─── Dynamic difficulty helpers ───────────────────────────────────────────
    def _obstacle_chance(self, dist):
        """
        ความน่าจะเป็นต่อ tile ที่จะมี prop
        0-15m : 0% (safe zone — ผู้เล่นตั้งตัว)
        15-80m: 30% (เริ่มเห็น ice/force บ้าง)
        80-250m: 50% (หนาแน่นขึ้น)
        250-500m: 65%
        500m+: 75%
        """
        if dist < 15:   return 0.00   # safe zone
        if dist < 80:   return 0.30
        if dist < 250:  return 0.50
        if dist < 500:  return 0.65
        return 0.75

    def _gem_chance(self, dist):
        """Gem spawn probability per non-obstacle tile, scaled by distance."""
        if dist < 30:   return 0.50   # generous early on
        if dist < 150:  return 0.40
        return 0.32                   # sparser late-game (harder to collect)

    def _build_straight(self, length, mark_fork=False):
        """
        สร้างพื้นตรงไปทางทิศปัจจุบัน — spawn prop เฉพาะ tile ใหม่เท่านั้น
        ใช้ตำแหน่ง tile ใน path (ไม่ใช่ตำแหน่ง player) เพื่อคำนวณ dist
        → แก้บัก preload ที่ dist=0 ทำให้ไม่มี obstacle ใน 60+ tiles แรก
        """
        col, row = self._last_pos
        cur_dir  = self._last_dir
        for _ in range(length):
            col += cur_dir[0]
            row += cur_dir[1]
            # tile_dist = ระยะทาง tile นี้จากจุดเริ่มต้น (ไม่ใช่ forward_tiles ของ player)
            tile_dist = len(self.path) * TILE_TO_METER
            is_new = self._add_center(col, row)   # True = tile ใหม่จริง ไม่เคยมีมาก่อน
            self._add_width(col, row, cur_dir)
            if mark_fork:
                self.fork_tiles.add((col, row))

            # Spawn เฉพาะ tile ใหม่แท้จริง (is_new) ไม่ใช่ fork / re-enter หลัง cleanup
            if self._seg_count > 0 and not mark_fork and is_new:
                if random.random() < self._obstacle_chance(tile_dist):
                    prop = ObstacleFactory.spawn_prop(tile_dist, col, row)
                    if prop:
                        # force (gold buff): บังคับ gap 100m — ไม่ให้ติดกัน
                        if prop == 'force':
                            if tile_dist - self._last_force_dist < 100:
                                prop = 'ice1'   # ถ้าใกล้เกิน ลด grade เป็น ice
                            else:
                                self._last_force_dist = tile_dist
                        self.obstacles[(col, row)] = prop
                        if prop == 'trap':
                            self.init_trap(col, row)
                # Gem: spawn บน tile ที่ไม่มี prop
                if (col, row) not in self.obstacles:
                    if random.random() < self._gem_chance(tile_dist):
                        gem = ObstacleFactory.spawn_gem(col, row)
                        self.gems[(col, row)] = gem

        self._last_pos = (col, row)

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
        """
        เพิ่มพิกัดเข้าทางเดิน
        คืน True เฉพาะเมื่อเป็น tile ที่ไม่เคยถูก add เลยในรอบนี้ — ใช้เพื่อ spawn obstacle
        False = เคยมีแล้ว (fork overlap หรือ cleanup แล้ว re-enter) → ห้าม spawn ซ้ำ
        """
        pos = (col, row)
        was_ever_used = pos in self._used_positions   # เคยสร้างไว้แล้วในอดีต?
        if pos not in self.path_set:
            self.path_index_map[pos] = len(self.path)  # บันทึก index ก่อน append
            self.path.append(pos)
            self.path_set.add(pos)
            self._used_positions.add(pos)
            return not was_ever_used   # True = ใหม่จริง, False = เคยผ่านมาแล้ว (re-enter)
        return False  # ยังอยู่ใน path_set — ซ้ำชัดเจน

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
