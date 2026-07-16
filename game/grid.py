import random

from core.boss_data import BossItemPlacement, load_boss_data
from core.config import BOSS_DISTANCE_M, TILE_TO_METER
from core.items import ItemType
from core.logger import logger
from core.spawning import SpawningSystem
from core.state import load_difficulty
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
PROMPT_LEAD = 4


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
        self.scientific_items = {}  # (col, row) -> ItemType
        self.heart_pickups: set[tuple[int, int]] = set()
        self.boss_items = {}  # (col, row) -> BossItemPlacement
        self.fork_tiles = set()  # tile ที่เป็นส่วน fork (ใช้ render สีต่าง)
        self.merge_points = []  # จุดบรรจบของแต่ละ fork
        self.junction_prompts = {}
        # Post-policy atmosphere (ADR plan Task 4): systemic choices make the
        # next straight segments friendlier (fewer crates); non-systemic do
        # the opposite. Reset at each new junction spawn.
        self.environment_bias = "neutral"
        self.obstacle_spawn_multiplier = 1.0
        env = load_difficulty().get("environment", {})
        self._env_friendly_mult = float(env.get("friendly_obstacle_multiplier", 0.4))
        self._env_hostile_mult = float(env.get("hostile_obstacle_multiplier", 1.8))
        self._base_obstacle_chance = float(env.get("base_obstacle_chance", 0.2))

        self._last_pos = (0, 0)
        self._last_dir = self.DIR_A
        self._seg_count = 0
        self._last_cleaned_idx = 0
        self._total_generated = 0
        self.checkpoints_generated = 0
        self._boss_wave = 0
        self.resolved_fork = None
        hazards = load_difficulty().get("hazards", {})
        self.trigger_seconds_start = float(hazards.get("trigger_seconds_start", 2.5))
        self.trigger_seconds_min = float(hazards.get("trigger_seconds_min", 0.65))
        self.trigger_acceleration_exponent = float(hazards.get("acceleration_exponent", 1.5))
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
        self.scientific_items.clear()
        self.heart_pickups.clear()
        self.boss_items.clear()
        self.fork_tiles.clear()
        self.merge_points.clear()
        self.junction_prompts.clear()
        self.reset_environment_bias()
        self._last_pos = (0, 0)
        self._last_dir = self.DIR_A
        self._seg_count = 0
        self._last_cleaned_idx = 0
        self.resolved_fork = None
        # ต้อง reset ไม่งั้นรอบเล่นที่ 2 บอสไม่สร้างเวฟ (ค้างค่า 3 จากรอบก่อน)
        self._boss_wave = 0
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

    def trigger_seconds_for_distance(self, distance_m=None):
        """Return the grace time for a tile at this distance.

        The early run stays readable and forgiving; the hazard accelerates only
        later through the curve exponent, reaching the configured minimum near
        the boss threshold.  Keeping this calculation on the grid makes every
        caller use the same balance rule.
        """
        if distance_m is None:
            distance_m = self.get_distance_m()
        progress = max(0.0, min(1.0, float(distance_m) / BOSS_DISTANCE_M))
        eased_progress = progress**self.trigger_acceleration_exponent
        return (
            self.trigger_seconds_start
            + (self.trigger_seconds_min - self.trigger_seconds_start) * eased_progress
        )

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

    def get_junction_prompt(self, col, row):
        return self.junction_prompts.get((col, row))

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
            current_tile.trigger_timer = self.trigger_seconds_for_distance(score)

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
            self.scientific_items.pop(pos, None)
            self.heart_pickups.discard(pos)
            self.boss_items.pop(pos, None)
            self.junction_prompts.pop(pos, None)

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

    def get_scientific_item_at(self, col, row):
        return self.scientific_items.get((col, row))

    def get_heart_at(self, col: int, row: int) -> bool:
        return (col, row) in self.heart_pickups

    def apply_policy_environment(self, *, systemic: bool) -> None:
        """Bias obstacle density after a Y-junction policy choice."""
        if systemic:
            self.environment_bias = "friendly"
            self.obstacle_spawn_multiplier = self._env_friendly_mult
        else:
            self.environment_bias = "hostile"
            self.obstacle_spawn_multiplier = self._env_hostile_mult

    def reset_environment_bias(self) -> None:
        self.environment_bias = "neutral"
        self.obstacle_spawn_multiplier = 1.0

    def pop_boss_wave(self, wave_no):
        """Remove both alternatives for a resolved boss wave."""
        for pos, placement in list(self.boss_items.items()):
            if placement.wave == wave_no:
                self.boss_items.pop(pos)

    def get_path_index(self, col, row):
        try:
            return self.path.index((col, row))
        except ValueError:
            return -1

    def repair_path_ahead_of_checkpoint(self, col, row, tiles_ahead=30):
        """เรียกตอนกำลังจะ respawn ผู้เล่นที่ checkpoint (col,row)

        `update_tiles` นับถอยหลัง trigger_timer ของทุก tile ที่เคยถูกเหยียบไปแล้ว
        ต่อเนื่องไปเรื่อย ๆ ไม่สนใจว่าผู้เล่นยังอยู่ตรงนั้นไหม — ถ้าผู้เล่นตายแล้วรอ respawn
        (3 วิ) ทางเดินที่เดินผ่านมาก่อนตายอาจละลาย/หายไปหมดแล้ว พอ respawn กลับมาที่
        checkpoint แล้วเดินต่อจะตกทันที (tile ไม่มีอยู่ใน path_set) → ตาย → respawn → วนไม่จบ
        ฟังก์ชันนี้ "แช่แข็ง" ทางเดินช่วงสั้น ๆ ข้างหน้า checkpoint กลับเป็น normal/สร้างใหม่
        ถ้าหายไปแล้ว ให้ผู้เล่นมีทางเดินจริงให้เดินต่อได้เสมอหลัง respawn
        """
        idx = self.get_path_index(col, row)
        if idx < 0:
            return
        for pos in self.path[idx : idx + tiles_ahead]:
            tile = self.path_set.get(pos)
            if tile is None:
                self._add_tile(*pos)
            else:
                tile.state = "normal"
                tile.trigger_timer = self.trigger_seconds_for_distance()
                tile.offset_y = 0.0
                tile.fall_velocity = 0.0

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
        self.scientific_items.pop(pos, None)
        self.heart_pickups.discard(pos)
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
            self.scientific_items.pop(pos, None)
            self.heart_pickups.discard(pos)
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
        if self._total_generated >= BOSS_DISTANCE_M:
            if self._boss_wave < 3:
                self._build_boss_wave(self._boss_wave)
                self._boss_wave += 1
            else:
                self._build_straight(10, mark_fork=False)
            return

        if self._total_generated >= (self.checkpoints_generated) * 100:
            self._build_checkpoint_platform()

        current_distance_m = self._total_generated * TILE_TO_METER

        # D1-A2: โซนถึงกำหนด spawn แล้วหรือยัง — consume โซนเฉพาะเมื่อ fork
        # ถูกสร้างจริงเท่านั้น ไม่งั้นโซนหาย (junction < 10) ถ้า _seg_count ยังไม่พอ
        should_spawn_fork = (
            self.next_zone <= self.spawning_system.NUM_ZONES
            and current_distance_m >= self.next_spawn_distance
        )

        if should_spawn_fork and self._seg_count >= 2:
            # ─── Diamond Fork ───
            # New junction = new atmosphere cycle; clear prior policy bias.
            self.reset_environment_bias()
            self._build_diamond_fork(self.next_zone)
            logger.info(
                f"[SPAWN] Y-Junction โซน {self.next_zone} ที่ระยะ ~{current_distance_m}m "
                f"(กำหนด {self.next_spawn_distance}m)"
            )
            self.next_zone += 1
            self.next_spawn_distance = self.spawning_system.get_spawn_distance(self.next_zone)
        else:
            # ─── Straight Segment ─── (โซนที่ค้างจะถูกลองใหม่ segment ถัดไป)
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
            # ปรับโอกาสด้วย environment_bias หลังเลือกนโยบายที่ทางแยก
            obstacle_chance = min(1.0, self._base_obstacle_chance * self.obstacle_spawn_multiplier)
            if self._seg_count > 0 and random.random() < obstacle_chance and not mark_fork:
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

            if (
                self._seg_count > 0
                and not mark_fork
                and (col, row) not in self.obstacles
                and (col, row) not in self.gems
                and (col, row) not in self.scientific_items
                and (col, row) not in self.heart_pickups
                and random.random() < self._scientific_item_spawn_chance()
            ):
                self.scientific_items[(col, row)] = random.choice(list(ItemType))
            elif (
                self._seg_count > 0
                and not mark_fork
                and (col, row) not in self.obstacles
                and (col, row) not in self.gems
                and (col, row) not in self.scientific_items
                and (col, row) not in self.heart_pickups
                and random.random() < self._heart_pickup_spawn_chance()
            ):
                self.heart_pickups.add((col, row))

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
        if zone_id is not None:
            for pos in self.path[-PROMPT_LEAD:]:
                self.junction_prompts[pos] = zone_id
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
        """Build one forward-only boss fork.

        Meaningful tiles (centreline path, zone commit tiles, boss items, and merge
        points) must be reachable from ``path[0]`` with only ``(+1, 0)`` and
        ``(0, +1)``, and must still lead to the path end. Decorative diamond
        overhangs and start-platform tiles are excluded.
        """
        self._build_straight(3, mark_fork=True)
        start_col, start_row = self._last_pos
        cur_dir = self._last_dir
        perp = self.DIR_B if cur_dir == self.DIR_A else self.DIR_A
        perp_side = "left" if cur_dir == self.DIR_A else "right"
        dir_side = "right" if perp_side == "left" else "left"
        wave_no = wave_index + 1
        wave = load_boss_data().waves.get(wave_no)

        def build_lane(steps):
            col, row = start_col, start_row
            positions = []
            for direction, count in steps:
                for _ in range(count):
                    col += direction[0]
                    row += direction[1]
                    self._add_tile(col, row, is_fork=True, is_safe=True)
                    self.fork_tiles.add((col, row))
                    positions.append((col, row))
            return positions

        # Same endpoint, different positive-only order: 4d + 2p.
        dir_lane = build_lane(((cur_dir, 4), (perp, 2)))
        perp_lane = build_lane(((perp, 2), (cur_dir, 4)))
        if wave:
            # Deterministic by wave parity (not random) — reproducible across runs/
            # replays; the player already sees which item is on which side via HUD.
            dir_correct = wave_index % 2 == 0
            placements = (
                (dir_lane[1], dir_side, wave.correct_item if dir_correct else wave.wrong_item),
                (perp_lane[1], perp_side, wave.wrong_item if dir_correct else wave.correct_item),
            )
            for pos, side, item_id in placements:
                self.boss_items[pos] = BossItemPlacement(wave_no, item_id, side)

        merge = dir_lane[-1]
        self.merge_points.append(merge)
        self.path.append(merge)
        self._add_tile(*merge, is_safe=True)
        self._last_pos = merge

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

    @staticmethod
    def _scientific_item_spawn_chance():
        difficulty = load_difficulty()
        items = difficulty.get("items", {})
        return float(items.get("spawn_chance", 0.0)) if isinstance(items, dict) else 0.0

    @staticmethod
    def _heart_pickup_spawn_chance() -> float:
        difficulty = load_difficulty()
        hearts = difficulty.get("hearts", {})
        return float(hearts.get("pickup_chance", 0.0)) if isinstance(hearts, dict) else 0.0

    def _add_width(self, col, row, direction, is_safe=False):
        """ขยาย PATH_WIDTH ตั้งฉากกับ direction (ถ้ามากกว่า 1)"""
        if PATH_WIDTH <= 1:
            return

        perp = (0, 1) if direction == self.DIR_A else (1, 0)
        half = PATH_WIDTH // 2
        for sign in [1, -1]:
            for d in range(1, half + 1):
                self._add_tile(col + perp[0] * d * sign, row + perp[1] * d * sign, is_safe=is_safe)
