from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Choice:
    text: str
    heat_delta: int
    anger_delta: int
    is_systemic: bool  # True if it's the systemic correct answer (green line in DAG)

@dataclass
class JunctionData:
    zone_id: int
    category: str
    situation: str
    left_choice: Choice
    right_choice: Choice

# ข้อมูล 10 ทางแยก (Y-Junction Policy Encounters) ตาม GDD
JUNCTIONS: List[JunctionData] = [
    # ภาคที่ 1: หมวดสาเหตุ (Causes) — โซน 100m–300m
    JunctionData(
        zone_id=1, category="Causes", situation="วิกฤตพลังงานเมืองหลวง",
        left_choice=Choice("อนุมัติโรงไฟฟ้าถ่านหิน", +25, -20, False),
        right_choice=Choice("บังคับใช้โซลาร์ฟาร์ม", -20, +25, True)
    ),
    JunctionData(
        zone_id=2, category="Causes", situation="สัมปทานผืนป่า",
        left_choice=Choice("ระงับสัมปทาน+เขตป่าสงวน", -20, +25, True),
        right_choice=Choice("อนุมัติสัมปทานส่งออก", +25, -25, False)
    ),
    JunctionData(
        zone_id=3, category="Causes", situation="รถติดและควันดำ",
        left_choice=Choice("อุดหนุนราคา EV", -5, -20, False),
        right_choice=Choice("เก็บภาษีรถติด+รถเมล์ฟรี", -25, +25, True)
    ),
    # ภาคที่ 2: หมวดผลกระทบ (Impacts) — โซน 301m–600m
    JunctionData(
        zone_id=4, category="Impacts", situation="ระดับน้ำทะเลรุกคืบ",
        left_choice=Choice("สร้างกำแพงกั้นน้ำยักษ์", +20, -25, False),
        right_choice=Choice("ย้ายนิคม+ฟื้นฟูป่าชายเลน", -25, +30, True)
    ),
    JunctionData(
        zone_id=5, category="Impacts", situation="ภัยแล้งและวิกฤตอาหาร",
        left_choice=Choice("อุดหนุนสารเคมี/ปุ๋ยเร่งโต", +25, -20, False),
        right_choice=Choice("พืชทนแล้ง+เกษตรอินทรีย์", -20, +25, True)
    ),
    JunctionData(
        zone_id=6, category="Impacts", situation="ระเบิดเวลา Permafrost",
        left_choice=Choice("ปล่อยผ่าน", +40, -10, False),
        right_choice=Choice("บังคับเอกชนสร้างโดมดูดมีเทน", -35, +35, True)
    ),
    # ภาคที่ 3: หมวดการแก้ปัญหา (Solutions) — โซน 601m–1,000m
    JunctionData(
        zone_id=7, category="Solutions", situation="ภาษีคาร์บอน",
        left_choice=Choice("อนุมัติภาษีคาร์บอนก้าวหน้า", -35, +35, True),
        right_choice=Choice("ชะลอกฎหมาย", +30, -30, False)
    ),
    JunctionData(
        zone_id=8, category="Solutions", situation="ขยะ Fast Fashion",
        left_choice=Choice("เศรษฐกิจหมุนเวียน", -25, +25, True),
        right_choice=Choice("แคมเปญกระตุ้นยอดขาย", +25, -25, False)
    ),
    JunctionData(
        zone_id=9, category="Solutions", situation="แหล่งกักเก็บคาร์บอน",
        left_choice=Choice("เปิดเสรีพื้นที่สีเขียวให้เอกชน", +30, -30, False),
        right_choice=Choice("ภาษีที่ดินรกร้าง → พื้นที่ชุ่มน้ำ", -30, +30, True)
    ),
    JunctionData(
        zone_id=10, category="Solutions", situation="ทางเลือกโค้งสุดท้าย",
        left_choice=Choice("ระงับพลังงานฟอสซิล 100%", -50, +50, True),
        right_choice=Choice("ซื้อคาร์บอนเครดิต", +50, -50, False)
    ),
]

def get_junction(zone_id: int) -> JunctionData:
    """ดึงข้อมูลทางแยกตาม zone_id (1-10)"""
    for junction in JUNCTIONS:
        if junction.zone_id == zone_id:
            return junction
    raise ValueError(f"Junction not found for zone {zone_id}")
