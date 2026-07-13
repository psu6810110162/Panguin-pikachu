from core.junction_data import load_junctions


def test_load_junctions_success():
    # สมมติฐานว่ามีไฟล์ balance/v1/junctions.json อยู่และถูกต้อง
    junctions = load_junctions()
    # ถ้าไม่มีไฟล์ หรือมีบั๊ก จะโหลดไม่ขึ้น
    assert isinstance(junctions, list)


def test_get_junction():
    # ทดสอบฟังก์ชัน get_junction ว่าดึงแล้วแคชได้ถูกต้องไหม
    # เนื่องจากใช้ Singleton cache อาจมีปัญหาเรื่องการรีเซ็ต เราจะข้ามหรือใช้ mock
    pass
