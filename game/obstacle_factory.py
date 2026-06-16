import random
from game.blocks import PROP_ICE1, PROP_ICE2, PROP_ICE3, PROP_FORCE, PROP_TRAP
from game.pool import Pools


class ObstacleFactory:
    """
    Biome-aware prop factory — density ควบคุมโดย grid._obstacle_chance()
    _pick_prop() เลือก *ประเภท* ไม่คืน BLANK (ทำให้มองเห็นได้ชัดเจน)
    หมายเหตุ: PROP_REVERSE ถูกเอาออกจาก game design แล้ว
    """

    @staticmethod
    def spawn_prop(awareness_m, col_position, row_position):
        """คืน prop string — เรียกเฉพาะเมื่อ obstacle_chance ผ่านแล้ว"""
        return ObstacleFactory._pick_prop(awareness_m)

    @staticmethod
    def _pick_prop(d):
        """
        เลือกประเภท prop ตาม Awareness Index
        ไม่คืน BLANK — density ถูกควบคุมที่ grid._obstacle_chance() แล้ว
        force spacing (max 1/100m) บังคับที่ grid._build_straight()

        Biome zones:
          0–15 m   : safe start (grid ไม่เรียก factory ช่วงนี้)
          15–80 m  : Arctic Ice  — ice1 + force
          80–250 m : Drought     — ice1/ice2 + force
          250–500 m: Flood       — ice1/2/3 + force + trap
          500+ m   : Wildfire    — full mix หนาแน่น
        """
        r = random.random()

        # Zone 1: Arctic Ice — สอนผู้เล่นก่อน
        if d < 80:
            if r < 0.70: return PROP_ICE1
            return PROP_FORCE

        # Zone 2: Drought — ice2 โผล่
        if d < 250:
            if r < 0.40: return PROP_ICE1
            if r < 0.70: return PROP_ICE2
            return PROP_FORCE

        # Zone 3: Flood — ice3 + trap เริ่มโผล่
        if d < 500:
            if r < 0.25: return PROP_ICE1
            if r < 0.50: return PROP_ICE2
            if r < 0.68: return PROP_ICE3
            if r < 0.84: return PROP_FORCE
            return PROP_TRAP

        # Zone 4: Wildfire — full mix, ice3/trap หนัก
        if r < 0.15: return PROP_ICE1
        if r < 0.35: return PROP_ICE2
        if r < 0.55: return PROP_ICE3
        if r < 0.72: return PROP_FORCE
        return PROP_TRAP

    @staticmethod
    def spawn_gem(col_position, row_position):
        """สร้าง Gem จาก Object Pool"""
        gem = Pools.gems.get()
        gem.reset()
        gem.col = col_position
        gem.row = row_position
        return gem
