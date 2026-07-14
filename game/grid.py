import random

from core.boss_data import load_boss_data
from core.config import TILE_TO_METER
from core.spawning import SpawningSystem
from game.obstacle_factory import ObstacleFactory


class Tile:
    def __init__(self, col, row, is_fork=False, is_safe=False):
        self.col = col
        self.row = row
        self.is_fork = is_fork
        self.is_safe = is_safe
        self.state = "normal"
        self.trigger_timer = 1.2
        self.offset_y = 0.0
        self.fall_velocity = 0.0
        self.zone_id = None
        self.side = None


PATH_WIDTH = 1  # กว้าง 1 tile (ผอมลงตามสั่ง)
SEGMENT_LEN_MIN = 2  # สั้นลงเพื่อให้ซิกแซกถี่ขึ้น (ตามสั่ง)
SEGMENT_LEN_MAX = 6  # สั้นลงเพื่อให้ซิกแซกถี่ขึ้น
PRELOAD_SEGMENTS = 8  # สร้างล่วงหน้าตอนเริ่ม
VISIBLE_BUFFER = 60  # extend_if_needed threshold
FORK_CHANCE = 0.30  # 30% โอกาสเกิดทางแยก

FORK_SHORT_LEN = 4  # เส้นสั้น
FORK_LONG_LEN = 7  # เส้นยาว (อ้อม)


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

    DIR_A = (1, 0)  # iso-right (+col)
    DIR_B = (0, 1)  # iso-left  (+row)

    def __init__(self):
        self.forward_tiles = 0
        self.path = []  # centerline ที่เพนกวินเดิน
        self.path_set = {}  # ทุก tile รวม width
        self.turn_points = []  # จุดที่ต้องกดเปลี่ยนทิศ
        self.obstacles = {}  # (col, row) -> Obstacle
        self.gems = {}  # (col, row) -> Gem
        self.boss_items = {}  # (col, row) -> str (item_id)
        self.fork_tiles = set()  # tile ที่เป็นส่วน fork (ใช้ render สีต่าง)
        self.merge_points = []  # จุดบรรจบของแต่ละ fork

        self._last_pos = (0, 0)
        self._last_dir = self.DIR_A
        self._seg_count = 0
        self._last_cleaned_idx = 0
        self._total_generated = 0
        self.checkpoints_generated = 0
        self.resolved_fork = None
        # Day 1: D1-A2 Zone-Based Spawning
        self.spawning_system = SpawningSystem()
        self.next_zone = 1
        self.next_spawn_distance = self.spawning_system.get_spawn_distance(self.next_zone)

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    @staticmethod
    def to_isometric(x, y, tile_width, tile_height):
        iso_x = (x - y) * (tile_width / 2)
        iso_y = (x + y) * (tile_height / 2)
        return iso_x, iso_y

    def reset(self):
        self.forward_tiles = 0
        self.path.clear()
        self.path_set.clear()
        self.turn_points.clear()
        self.obstacles.clear()
        self.gems.clear()
        self.boss_items.clear()
        self.fork_tiles.clear()
        self.merge_points.clear()
        self._last_pos = (0, 0)
        self._last_dir = self.DIR_A
        self._seg_count = 0
        self._last_cleaned_idx = 0
        self.resolved_fork = None
        self._build_start_platform()
        self.spawning_system = SpawningSystem()
        self.next_zone = 1
        self.next_spawn_distance = self.spawning_system.get_spawn_distance(self.next_zone)
        for _ in range(PRELOAD_SEGMENTS):
            self._append_segment()

    def step_forward(self):
        self.forward_tiles += 1

    def get_distance_m(self):
        return self.forward_tiles * TILE_TO_METER

    def check_fork_resolution(self, col, row):
        tile = self.path_set.get((col, row))
        if tile and tile.zone_id is not None and tile.side is not None:
            self.resolved_fork = (tile.zone_id, tile.side)
            tile.zone_id = None
            tile.side = None

    def pop_resolved_fork(self):
        res = self.resolved_fork
        self.resolved_fork = None
        return res

    def update_obstacles(self, dt, view_radius, penguin_pos):
        """อัปเดตแอนิเมชันของอุปสรรคที่อยู่ในระยะมองเห็น"""
        p_col, p_row = penguin_pos
        for pos, obs in self.obstacles.items():
            # เช็คระยะแบบหยาบๆ (Bounding Box)
            if (
                obs.active
                and p_col - view_radius <= pos[0] <= p_col + view_radius
                and p_row - view_radius <= pos[1] <= p_row + view_radius
            ):
                obs.update(dt)

        # อัปเดต Gem
        for pos, gem in self.gems.items():
            if (
                gem.active
                and p_col - view_radius <= pos[0] <= p_col + view_radius
                and p_row - view_radius <= pos[1] <= p_row + view_radius
            ):
                gem.update(dt)

    def update_tiles(self, dt, penguin_pos):
        p_col, p_row = penguin_pos

        current_tile = self.path_set.get((p_col, p_row))
        if current_tile and current_tile.state == "normal" and not current_tile.is_safe:
            current_tile.state = "triggered"
            score = self.get_distance_m()
            current_tile.trigger_timer = max(0.35, 1.2 - (score * 0.002))

        to_remove = []
        for pos, tile in self.path_set.items():
            if tile.is_safe:
                continue

            if tile.state == "triggered":
                tile.trigger_timer -= dt
                if tile.trigger_timer <= 0:
                    tile.state = "falling"
                    tile.fall_velocity = 0.0
            elif tile.state == "falling":
                tile.fall_velocity += 1500.0 * dt
                tile.offset_y -= tile.fall_velocity * dt
                if tile.offset_y < -1500:
                    tile.state = "destroyed"
                    to_remove.append(pos)

        for pos in to_remove:
            self.path_set.pop(pos, None)
            self.obstacles.pop(pos, None)
            self.gems.pop(pos, None)
            self.boss_items.pop(pos, None)

    def is_on_path(self, col, row):
        return (col, row) in self.path_set

    def get_obstacle_at(self, col, row):
        obs = self.obstacles.get((col, row))
        if obs and obs.active:
            return obs
        return None

    def get_gem_at(self, col, row):
        gem = self.gems.get((col, row))
        if gem and gem.active:
            return gem
        return None

    def get_boss_item_at(self, col, row):
        return self.boss_items.get((col, row))

    def get_path_index(self, col, row):
        try:
            return self.path.index((col, row))
        except ValueError:
            return -1

    def get_correct_direction_at(self, path_index):
        """ทิศทาง centerline ณ index นี้"""
        if path_index + 1 < len(self.path):
            c = self.path[path_index]
            n = self.path[path_index + 1]
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

    def remove_tile(self, col, row):
        """ลบ Tile ออกจากแผนที่ (ใช้สำหรับระบบทางเดินถล่ม)"""
        pos = (col, row)
        self.path_set.pop(pos, None)
        # ลบ object ที่อาจจะอยู่บนนั้นด้วย
        self.obstacles.pop(pos, None)
        self.gems.pop(pos, None)
        self.boss_items.pop(pos, None)
        # Note: ไม่ลบจาก self.path เพื่อไม่ให้ลำดับพิกัดเสีย (แต่ renderer จะไม่วาดเพราะไม่อยู่ใน path_set)

    def cleanup_behind(self, path_index):
        """ลบวัตถุที่ผู้เล่นเดินผ่านมาไกลพอแล้ว เพื่อประหยัด Memory และไม่ให้รก"""
        target_idx = path_index - 20
        if target_idx <= self._last_cleaned_idx:
            return

        # ลบไล่มาจากจุดที่ล้างครั้งล่าสุด
        for i in range(self._last_cleaned_idx, target_idx):
            if i >= len(self.path):
                break
            pos = self.path[i]
            self.obstacles.pop(pos, None)
            self.gems.pop(pos, None)
            self.boss_items.pop(pos, None)

        self._last_cleaned_idx = target_idx

        # บริหารจัดการ path และ path_set ด้วย (ถ้าต้องการความคลีนขั้นสุด)
        # แต่ในที่นี้เน้น object ที่ต้อง update/draw ก่อน

    # ═══════════════════════════════════════════
    #  INTERNAL BUILDERS
    # ═══════════════════════════════════════════

    def _add_tile(self, col, row, is_fork=False, is_safe=False):
        if (col, row) not in self.path_set:
            self.path_set[(col, row)] = Tile(col, row, is_fork, is_safe)

    def _build_start_platform(self):
        """Generate a 4x4 safe starting platform at (0,0)."""
        self._total_generated = 0
        self.checkpoints_generated = 0
        self._last_pos = (0, 0)
        self._last_dir = self.DIR_A
        self._build_checkpoint_platform()
        self.path_index = 0

    def _build_checkpoint_platform(self):
        """Generate a 4x4 safe checkpoint platform at the current end of the path."""
        col, row = self._last_pos
        cur_dir = self._last_dir
        for i in range(4):
            for j in range(-1, 3):
                c = col + (i if cur_dir[0] else j)
                r = row + (j if cur_dir[0] else i)
                self._add_tile(c, r, is_safe=True)
                if j == 0 and (c, r) not in self.path:
                    self.path.append((c, r))
                    self._total_generated += 1

        self._last_pos = (col + 3 * cur_dir[0], row + 3 * cur_dir[1])
        self.checkpoints_generated += 1

    def _append_segment(self):
        """
        สร้าง 1 segment: straight หรือ diamond fork (30%)
        แล้วต่อด้วย corner เพื่อเปลี่ยนทิศ
        """
        if self._total_generated >= 1000:
            if not hasattr(self, "_boss_wave"):
                self._boss_wave = 0
            if self._boss_wave < 3:
                self._build_boss_wave(self._boss_wave)
                self._boss_wave += 1
            else:
                self._build_straight(10, mark_fork=False)
            return

        if self._total_generated >= (self.checkpoints_generated) * 100:
            self._build_checkpoint_platform()

        current_distance_m = self._total_generated * TILE_TO_METER
        should_spawn_fork = False

        if (
            self.next_zone <= self.spawning_system.NUM_ZONES
            and current_distance_m >= self.next_spawn_distance
        ):
            should_spawn_fork = True
            self.next_zone += 1
            self.next_spawn_distance = self.spawning_system.get_spawn_distance(self.next_zone)

        if should_spawn_fork and self._seg_count >= 2:
            # ─── Diamond Fork ───
            self._build_diamond_fork(self.next_zone - 1)
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
        cur_dir = self._last_dir
        for _ in range(length):
            col += cur_dir[0]
            row += cur_dir[1]
            is_safe = self._add_center(col, row)
            self._add_width(col, row, cur_dir, is_safe=is_safe)
            if mark_fork:
                self.fork_tiles.add((col, row))

            # สุ่มวาง Obstacle บน centerline (ยกเว้นช่วงแรกๆ)
            # ปรับโอกาสเหลือ 0.2 เพื่อไม่ให้รกเกินไปเมื่อซิกแซกถี่ขึ้น
            if self._seg_count > 0 and random.random() < 0.2 and not mark_fork:
                # เช็คไม่ให้วางทับพิกัดเดิมที่มีกล่องอยู่แล้ว (กันการเจนซ้ำซ้อน)
                if (col, row) not in self.obstacles:
                    dist = self.get_distance_m()
                    obs = ObstacleFactory.spawn_obstacle(dist, col, row)
                    self.obstacles[(col, row)] = obs

            # สุ่มวาง Gem บน centerline (ถ้าไม่มีกล่อง และไม่มี Gem ที่จุดเดิม)
            # [FIX] เช็คให้ชัวร์ว่าไม่ทับ Obstacle ที่เพิ่งวางไปหมาดๆ หรือที่มีอยู่แล้ว
            elif (
                self._seg_count > 0
                and random.random() < 0.4
                and not mark_fork
                and (col, row) not in self.obstacles
                and (col, row) not in self.gems
            ):
                gem = ObstacleFactory.spawn_gem(col, row)
                self.gems[(col, row)] = gem

        self._last_pos = (col, row)

    # ───────────────────────────────────────────
    #  Diamond Fork
    # ───────────────────────────────────────────
    def _build_diamond_fork(self, zone_id=None):
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

        is_perp_left = cur_dir == self.DIR_A
        long_side = "left" if is_perp_left else "right"
        short_side = "right" if is_perp_left else "left"

        # ── Branch Short (centerline หลัก) ──
        col, row = start_col, start_row
        for i in range(FORK_SHORT_LEN):
            col += cur_dir[0]
            row += cur_dir[1]
            is_safe = self._add_center(col, row)
            self._add_width(col, row, cur_dir, is_safe=is_safe)
            if i == 0 and zone_id is not None:
                tile = self.path_set.get((col, row))
                if tile:
                    tile.zone_id = zone_id
                    tile.side = short_side
        # short_end คือ merge point
        merge_col, merge_row = col, row

        # ── Branch Long (อ้อมด้านข้าง) ──
        # ออกทาง perp 2 ก้าว → วิ่ง cur_dir FORK_LONG_LEN → กลับ perp(-2)
        lc, lr = start_col, start_row
        SIDE_OFFSET = 2  # ระยะห่างสำหรับ 1-tile path

        # ออกด้านข้าง
        for i in range(SIDE_OFFSET):
            lc += perp[0]
            lr += perp[1]
            self._add_tile(lc, lr, is_fork=True)
            self.fork_tiles.add((lc, lr))
            if i == 0 and zone_id is not None:
                tile = self.path_set.get((lc, lr))
                if tile:
                    tile.zone_id = zone_id
                    tile.side = long_side

        # วิ่งตรงขนาน (เพิ่ม Gem ที่นี่)
        for _ in range(FORK_LONG_LEN):
            lc += cur_dir[0]
            lr += cur_dir[1]
            self._add_tile(lc, lr, is_fork=True)
            self.fork_tiles.add((lc, lr))

            # สุ่มวาง Gem บนทางแยก (Long Branch)
            if random.random() < 0.6 and (lc, lr) not in self.gems:  # โอกาสเยอะหน่อยให้คุ้มที่อ้อม
                gem = ObstacleFactory.spawn_gem(lc, lr)
                self.gems[(lc, lr)] = gem

        # กลับเข้า merge point
        for _ in range(SIDE_OFFSET):
            lc -= perp[0]
            lr -= perp[1]
            self._add_tile(lc, lr, is_fork=True)
            self.fork_tiles.add((lc, lr))

        # บันทึก merge point
        self.merge_points.append((merge_col, merge_row))
        self._last_pos = (merge_col, merge_row)

    # ───────────────────────────────────────────
    #  Boss Wave (Symmetric Fork for 2 Lanes)
    # ───────────────────────────────────────────
    def _build_boss_wave(self, wave_index):
        """
        สร้างทางแยก 2 เลนซ้าย-ขวา
        """
        start_col, start_row = self._last_pos
        cur_dir = self._last_dir
        perp = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A

        boss_data = load_boss_data()
        wave = boss_data.waves.get(wave_index + 1)

        # Straight before split
        self._build_straight(3)

        # Splitting
        left_col, left_row = self._last_pos
        right_col, right_row = self._last_pos

        for _ in range(2):
            left_col -= perp[0]
            left_row -= perp[1]
            right_col += perp[0]
            right_row += perp[1]
            self._add_tile(left_col, left_row, is_fork=True)
            self._add_tile(right_col, right_row, is_fork=True)

        for i in range(4):
            left_col += cur_dir[0]
            left_row += cur_dir[1]
            right_col += cur_dir[0]
            right_row += cur_dir[1]
            self._add_tile(left_col, left_row, is_fork=True)
            self._add_tile(right_col, right_row, is_fork=True)
            self.fork_tiles.add((left_col, left_row))
            self.fork_tiles.add((right_col, right_row))

            if i == 1 and wave:
                is_left_correct = random.choice([True, False])
                left_item = wave.correct_item if is_left_correct else wave.wrong_item
                right_item = wave.wrong_item if is_left_correct else wave.correct_item
                self.boss_items[(left_col, left_row)] = left_item
                self.boss_items[(right_col, right_row)] = right_item

        # Merge back
        for _ in range(2):
            left_col += perp[0]
            left_row += perp[1]
            right_col -= perp[0]
            right_row -= perp[1]
            self._add_tile(left_col, left_row, is_fork=True)
            self._add_tile(right_col, right_row, is_fork=True)

        self.merge_points.append((left_col, left_row))
        self.path.append((left_col, left_row))
        self._add_tile(left_col, left_row, is_safe=True)
        self._last_pos = (left_col, left_row)
        self._total_generated += 11

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

        # สำหรับ 1 tile เลี้ยวทันทีโดยไม่ต้องเผื่อความกว้าง
        col += nxt_dir[0]
        row += nxt_dir[1]
        self._add_center(col, row)

        self._last_pos = (col, row)
        self._last_dir = nxt_dir

    # ───────────────────────────────────────────
    #  Helpers
    # ───────────────────────────────────────────
    def _add_center(self, col, row):
        pos = (col, row)
        if pos not in self.path_set:
            self.path.append(pos)
            self._total_generated += 1
            is_safe = False
            if self._total_generated <= 7 or self._total_generated % 100 < 6:
                is_safe = True
            self._add_tile(col, row, is_safe=is_safe)
            return is_safe
        return False

    def _add_width(self, col, row, direction, is_safe=False):
        """ขยาย PATH_WIDTH ตั้งฉากกับ direction (ถ้ามากกว่า 1)"""
        if PATH_WIDTH <= 1:
            return

        perp = (0, 1) if direction == self.DIR_A else (1, 0)
        half = PATH_WIDTH // 2
        for sign in [1, -1]:
            for d in range(1, half + 1):
                self._add_tile(col + perp[0] * d * sign, row + perp[1] * d * sign, is_safe=is_safe)
