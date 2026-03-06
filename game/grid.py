from core.config import TILE_TO_METER
import random
from core.obstacle import ObstacleFactory

PATH_WIDTH       = 3    # กว้าง 3 tile
SEGMENT_LEN_MIN  = 6    # ความยาวตรงต่อ segment (สั้นสุด)
SEGMENT_LEN_MAX  = 12   # ความยาวตรงต่อ segment (ยาวสุด)
PRELOAD_SEGMENTS = 8    # สร้างล่วงหน้าตอนเริ่ม
VISIBLE_BUFFER   = 60   # extend_if_needed threshold
FORK_CHANCE      = 0.30 # 30% โอกาสเกิดทางแยก

FORK_SHORT_LEN = 4   # เส้นสั้น
FORK_LONG_LEN  = 7   # เส้นยาว (อ้อม)


class GridManager:
    """
    Endless Zigzag + Diamond Fork Generator
    ────────────────────────────────────────
    - path กว้าง 3 tile ตลอด
    - zigzag สลับ DIR_A ↔ DIR_B
    - 30% โอกาสสร้าง diamond fork แทน straight segment
    - ทุก fork บรรจบกลับที่จุดเดิม → ไม่มี dead-end
    - fork สั้น/ยาว → ผู้เล่นเลือกได้ (ยาว = gem เยอะกว่า)
    """

    DIR_A = (1, 0)   # iso-right (+col)
    DIR_B = (0, 1)   # iso-left  (+row)

    def __init__(self):
        self.forward_tiles  = 0
        self.path           = []    # centerline ที่เพนกวินเดิน
        self.path_set       = set() # ทุก tile รวม width
        self.turn_points    = []    # จุดที่ต้องกดเปลี่ยนทิศ
        self.obstacles      = {}    # (col, row) -> Obstacle
        self.fork_tiles     = set() # tile ที่เป็นส่วน fork (ใช้ render สีต่าง)
        self.merge_points   = []    # จุดบรรจบของแต่ละ fork

        self._last_pos  = (0, 0)
        self._last_dir  = self.DIR_A
        self._seg_count = 0

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    def reset(self):
        self.forward_tiles  = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        self.obstacles.clear()
        self.fork_tiles.clear()
        self.merge_points.clear()
        self._last_pos  = (0, 0)
        self._last_dir  = self.DIR_A
        self._seg_count = 0
        self._build_start_platform()
        for _ in range(PRELOAD_SEGMENTS):
            self._append_segment()

    def step_forward(self):
        self.forward_tiles += 1

    def get_distance_m(self):
        return self.forward_tiles * TILE_TO_METER

    def is_on_path(self, col, row):
        return (col, row) in self.path_set

    def get_obstacle_at(self, col, row):
        obs = self.obstacles.get((col, row))
        if obs and obs.active:
            return obs
        return None

    def get_path_index(self, col, row):
        try:
            return self.path.index((col, row))
        except ValueError:
            return -1

    def get_correct_direction_at(self, path_index):
        """ทิศทาง centerline ณ index นี้"""
        if path_index + 1 < len(self.path):
            c  = self.path[path_index]
            n  = self.path[path_index + 1]
            return (n[0] - c[0], n[1] - c[1])
        return None

    def extend_if_needed(self, path_index):
        """เรียกทุกครั้งที่เดิน — สร้าง segment ใหม่อัตโนมัติ"""
        if len(self.path) - path_index < VISIBLE_BUFFER:
            self._append_segment()

    def is_fork_tile(self, col, row):
        """ใช้ใน renderer เพื่อ render fork branch สีพิเศษ"""
        return (col, row) in self.fork_tiles

    def is_merge_point(self, col, row):
        return (col, row) in self.merge_points

    # ═══════════════════════════════════════════
    #  INTERNAL BUILDERS
    # ═══════════════════════════════════════════

    def _build_start_platform(self):
        """Platform 5×5 สำหรับจุดเริ่ม"""
        for c in range(5):
            for r in range(5):
                self.path_set.add((c, r))
        center = (2, 2)
        self.path.append(center)
        self._last_pos = center

    def _append_segment(self):
        """
        สร้าง 1 segment: straight หรือ diamond fork (30%)
        แล้วต่อด้วย corner เพื่อเปลี่ยนทิศ
        """
        if random.random() < FORK_CHANCE and self._seg_count >= 2:
            # ─── Diamond Fork ───
            self._build_diamond_fork()
        else:
            # ─── Straight Segment ───
            self._build_straight(random.randint(SEGMENT_LEN_MIN, SEGMENT_LEN_MAX))

        # corner เปลี่ยนทิศ
        self._build_corner()
        self._seg_count += 1

    # ───────────────────────────────────────────
    #  Straight segment
    # ───────────────────────────────────────────
    def _build_straight(self, length, mark_fork=False):
        """วิ่งตรงตามทิศปัจจุบัน length ก้าว"""
        col, row = self._last_pos
        cur_dir  = self._last_dir
        for _ in range(length):
            col += cur_dir[0]
            row += cur_dir[1]
            self._add_center(col, row)
            self._add_width(col, row, cur_dir)
            if mark_fork:
                self.fork_tiles.add((col, row))
            
            # สุ่มวาง Obstacle บน centerline (ยกเว้นช่วงแรกๆ)
            if self._seg_count > 0 and random.random() < 0.3 and not mark_fork:
                dist = self.get_distance_m()
                obs = ObstacleFactory.spawn_obstacle(dist, col, row)
                self.obstacles[(col, row)] = obs

        self._last_pos = (col, row)

    # ───────────────────────────────────────────
    #  Diamond Fork
    # ───────────────────────────────────────────
    def _build_diamond_fork(self):
        """
        สร้าง diamond fork จาก _last_pos:
          cur_dir = ทิศหลัก  (เช่น DIR_A)
          perp    = ทิศตั้งฉาก (เช่น DIR_B)

          branch_short: เดินตาม cur_dir  FORK_SHORT_LEN ก้าว
          branch_long:  เดินตาม perp 2 + cur_dir FORK_LONG_LEN + perp(-2) กลับ
                        (อ้อมด้านข้างแล้วกลับมาบรรจบ)

          MERGE POINT = ปลาย branch_short
                      = ปลาย branch_long (บรรจบกัน)
        """
        start_col, start_row = self._last_pos
        cur_dir = self._last_dir
        # ทิศตั้งฉาก (เอาทิศอื่นมาอ้อม)
        perp = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A

        # ── Branch Short (centerline หลัก) ──
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
        # short_end คือ merge point
        merge_col, merge_row = col, row

        # ── Branch Long (อ้อมด้านข้าง) ──
        # ออกทาง perp 2 ก้าว → วิ่ง cur_dir FORK_LONG_LEN → กลับ perp(-2)
        lc, lr = start_col, start_row
        SIDE_OFFSET = 2 + PATH_WIDTH  # ระยะออกด้านข้างให้ไม่ทับ branch short

        # ออกด้านข้าง
        for _ in range(SIDE_OFFSET):
            lc += perp[0]
            lr += perp[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr))

        # วิ่งตรงขนาน
        for _ in range(FORK_LONG_LEN):
            lc += cur_dir[0]
            lr += cur_dir[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr))
            # เพิ่ม width ของ branch long
            for sign in [1, -1]:
                self.path_set.add((lc + perp[0]*sign, lr + perp[1]*sign))
                self.fork_tiles.add((lc + perp[0]*sign, lr + perp[1]*sign))

        # กลับเข้า merge point
        for _ in range(SIDE_OFFSET):
            lc -= perp[0]
            lr -= perp[1]
            self.path_set.add((lc, lr))
            self.fork_tiles.add((lc, lr))

        # เติม width ที่จุดบรรจบ
        for sign in [1, -1]:
            self.path_set.add((merge_col + perp[0]*sign, merge_row + perp[1]*sign))

        # บันทึก merge point
        self.merge_points.append((merge_col, merge_row))
        self._last_pos = (merge_col, merge_row)

    # ───────────────────────────────────────────
    #  Corner (เลี้ยว 90°)
    # ───────────────────────────────────────────
    def _build_corner(self):
        """
        เลี้ยว PATH_WIDTH ก้าวไปทิศใหม่
        เพื่อให้ path กว้าง 3 ต่อกันสนิทที่มุม
        """
        cur_dir = self._last_dir
        nxt_dir = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A
        col, row = self._last_pos

        # บันทึกจุดหักเลี้ยว
        self.turn_points.append((col, row))

        for _ in range(PATH_WIDTH):
            col += nxt_dir[0]
            row += nxt_dir[1]
            self._add_center(col, row)
            self._add_width(col, row, cur_dir)
            self._add_width(col, row, nxt_dir)

        self._last_pos = (col, row)
        self._last_dir = nxt_dir

    # ───────────────────────────────────────────
    #  Helpers
    # ───────────────────────────────────────────
    def _add_center(self, col, row):
        pos = (col, row)
        if pos not in self.path_set:
            self.path.append(pos)
            self.path_set.add(pos)

    def _add_width(self, col, row, direction):
        """ขยาย PATH_WIDTH ตั้งฉากกับ direction"""
        perp = (0, 1) if direction == self.DIR_A else (1, 0)
        half = PATH_WIDTH // 2
        for sign in [1, -1]:
            for d in range(1, half + 1):
                self.path_set.add((col + perp[0]*d*sign,
                                   row + perp[1]*d*sign))
