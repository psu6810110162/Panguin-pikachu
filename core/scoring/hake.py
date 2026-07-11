"""Hake Gain — normalized learning gain จากคะแนน pre/post-test (Hake, 1998)

หมายเหตุ: mockup ใน PDF ต้นฉบับโชว์ pre 40% -> post 90% เป็น "Gain: 0.50" แต่สูตร
Hake gain มาตรฐาน (post-pre)/(100-pre) ให้ 50/60 = 0.83 ไม่ใช่ 0.50 — ตัวเลขใน mockup
น่าจะเป็นแค่ค่าตัวอย่างสำหรับ UI ไม่ใช่ผลคำนวณจริง เราใช้สูตรมาตรฐานเพราะ "Hake Gain"
เป็นชื่อ metric เฉพาะทางที่ต้องคำนวณด้วยสูตรนี้เท่านั้นถึงจะเรียกว่า Hake Gain ได้
"""


def hake_gain(pretest_pct: float, posttest_pct: float) -> float | None:
    """(post - pre) / (100 - pre)

    Returns:
        None ถ้า pretest_pct >= 100 (ตอบถูกหมดตั้งแต่ pre-test แล้ว — gain ไม่มีความหมาย
        เพราะไม่มีที่ว่างให้ดีขึ้น ป้องกันหารด้วยศูนย์)
    """
    if pretest_pct >= 100:
        return None
    return (posttest_pct - pretest_pct) / (100 - pretest_pct)
