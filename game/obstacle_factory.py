import random
from game.blocks import (
    PROP_ICE1, PROP_ICE2, PROP_ICE3,
    PROP_FORCE, PROP_REVERSE, PROP_TRAP,
)
from game.pool import Pools


class ObstacleFactory:
    """
    Biome-aware prop factory — density ควบคุมโดย grid._obstacle_chance()
    _pick_prop() เลือก *ประเภท* ไม่คืน BLANK (ทำให้มองเห็นได้ชัดเจน)
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

        Biome zones:
          0–15 m   : safe start (grid ไม่เรียก factory ช่วงนี้)
          15–80 m  : Arctic Ice  — ice1 + reward (force)
          80–250 m : Drought     — ice1/2 + force + reverse เริ่ม
          250–500 m: Flood       — ice2/3 + force/reverse + trap
          500+ m   : Wildfire    — full mix หนาแน่น
        """
        r = random.random()

        # Zone 1: Arctic Ice — สอนผู้เล่นก่อน, reward บ่อย
        if d < 80:
            if r < 0.65: return PROP_ICE1
            return PROP_FORCE           # 35% force = เก็บ gold buff ได้บ่อย

        # Zone 2: Drought — ice2 โผล่, reverse เริ่ม
        if d < 250:
            if r < 0.35: return PROP_ICE1
            if r < 0.60: return PROP_ICE2
            if r < 0.78: return PROP_FORCE
            return PROP_REVERSE         # 22% reverse

        # Zone 3: Flood — ice3 + trap เริ่มโผล่
        if d < 500:
            if r < 0.20: return PROP_ICE1
            if r < 0.40: return PROP_ICE2
            if r < 0.55: return PROP_ICE3
            if r < 0.70: return PROP_FORCE
            if r < 0.85: return PROP_REVERSE
            return PROP_TRAP

        # Zone 4: Wildfire — full mix, ice3/trap หนัก
        if r < 0.12: return PROP_ICE1
        if r < 0.28: return PROP_ICE2
        if r < 0.45: return PROP_ICE3
        if r < 0.60: return PROP_FORCE
        if r < 0.75: return PROP_REVERSE
        return PROP_TRAP

    @staticmethod
    def spawn_gem(col_position, row_position):
        """สร้าง Gem จาก Object Pool"""
        gem = Pools.gems.get()
        gem.reset()
        gem.col = col_position
        gem.row = row_position
        return gem
