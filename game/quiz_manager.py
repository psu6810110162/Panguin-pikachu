import random
from typing import Optional, Dict


# ============================================================
# Question Bank — 5 ข้อต่อ biome รวม 20 ข้อ
# โครงสร้างแต่ละข้อ:
#   idx        : int  — เลขข้อภายใน biome (0-4)
#   q / q_en   : str  — คำถาม (ไทย / อังกฤษ)
#   choices / choices_en : list — 3 ตัวเลือก
#   answer     : int  — index ของคำตอบที่ถูก (0/1/2)
#   fact / fact_en : str — ข้อเท็จจริงสั้นๆ แสดงหลังตอบ
# ============================================================

QUESTIONS: Dict[str, list] = {
    'arctic': [
        {
            'idx': 0,
            'q':          'อาร์กติกร้อนขึ้นเร็วกว่าค่าเฉลี่ยโลกกี่เท่า?',
            'q_en':       'How many times faster is the Arctic warming than the global average?',
            'choices':    ['2 เท่า', '4 เท่า', '8 เท่า'],
            'choices_en': ['2 times', '4 times', '8 times'],
            'answer': 1,
            'fact':    'อาร์กติกร้อนขึ้น 4 เท่า เพราะ Arctic Amplification — น้ำแข็งละลายเปิดให้มหาสมุทรดูดซับความร้อนมากขึ้น',
            'fact_en': 'The Arctic warms 4× faster due to Arctic Amplification — melting ice exposes dark ocean that absorbs more heat.',
        },
        {
            'idx': 1,
            'q':          'เพนกวิน Emperor เสี่ยงสูญพันธุ์กี่เปอร์เซ็นต์ภายในปี ค.ศ. 2100?',
            'q_en':       'What percentage of Emperor Penguins could be extinct by 2100?',
            'choices':    ['50%', '75%', '98%'],
            'choices_en': ['50%', '75%', '98%'],
            'answer': 2,
            'fact':    'เพนกวิน Emperor พึ่งพาน้ำแข็งทะเลในการเพาะพันธุ์ หากแนวโน้มการปล่อยก๊าซยังเพิ่มขึ้น จะสูญพันธุ์ถึง 98%',
            'fact_en': 'Emperor Penguins depend on sea ice to breed. Under high-emission scenarios, 98% could be lost by 2100.',
        },
        {
            'idx': 2,
            'q':          'Ice-Albedo Feedback Loop ทำให้เกิดอะไร?',
            'q_en':       'What does the Ice-Albedo Feedback Loop cause?',
            'choices':    ['น้ำแข็งเพิ่มขึ้น', 'การละลายเร็วขึ้นเป็นทวีคูณ', 'อุณหภูมิลดลง'],
            'choices_en': ['More ice formation', 'Accelerating melt cycle', 'Temperature decrease'],
            'answer': 1,
            'fact':    'น้ำแข็งขาวสะท้อนแสงอาทิตย์ เมื่อละลาย มหาสมุทรสีเข้มดูดซับความร้อนมากขึ้น → ละลายเร็วขึ้น วนซ้ำ',
            'fact_en': 'White ice reflects sunlight. When it melts, the dark ocean absorbs more heat, causing faster melting in a feedback loop.',
        },
        {
            'idx': 3,
            'q':          'Arctic Amplification หมายถึงอะไร?',
            'q_en':       'What does "Arctic Amplification" mean?',
            'choices':    ['อาร์กติกร้อนเร็วกว่าพื้นที่อื่น', 'ลมในอาร์กติกแรงขึ้น', 'แสงแดดในอาร์กติกสว่างขึ้น'],
            'choices_en': ['Arctic warms faster than elsewhere', 'Winds in the Arctic get stronger', 'Sunlight in the Arctic gets brighter'],
            'answer': 0,
            'fact':    'Arctic Amplification คือปรากฏการณ์ที่อาร์กติกร้อนขึ้นเร็วกว่าค่าเฉลี่ยโลกถึง 4 เท่า',
            'fact_en': 'Arctic Amplification is the phenomenon where the Arctic region warms up to 4× faster than the global average.',
        },
        {
            'idx': 4,
            'q':          'น้ำแข็งทะเลอาร์กติกลดลงประมาณกี่เปอร์เซ็นต์ต่อทศวรรษ?',
            'q_en':       'By approximately what percentage per decade is Arctic sea ice declining?',
            'choices':    ['5%', '13%', '25%'],
            'choices_en': ['5%', '13%', '25%'],
            'answer': 1,
            'fact':    'น้ำแข็งทะเลอาร์กติกลดลงราว 13% ต่อทศวรรษ ตามข้อมูลจาก NSIDC ปี 2023',
            'fact_en': 'Arctic sea ice is declining by around 13% per decade, according to 2023 NSIDC data.',
        },
    ],

    'drought': [
        {
            'idx': 0,
            'q':          'ภัยแล้งที่รุนแรงขึ้นส่งผลต่อประชากรโลกกี่คน?',
            'q_en':       'How many people are affected by increasingly severe droughts?',
            'choices':    ['100 ล้านคน', '500 ล้านคน', '1,000 ล้านคน'],
            'choices_en': ['100 million', '500 million', '1 billion'],
            'answer': 2,
            'fact':    'IPCC 2023 ระบุว่าประชากรกว่า 1,000 ล้านคนทั่วโลกเผชิญกับความเครียดด้านน้ำจากภัยแล้งที่รุนแรงขึ้น',
            'fact_en': 'IPCC 2023 states that over 1 billion people face water stress from increasingly severe droughts.',
        },
        {
            'idx': 1,
            'q':          'หากไม่ลดก๊าซเรือนกระจก อุณหภูมิโลกจะเพิ่มขึ้นเท่าไรภายในปี 2100?',
            'q_en':       'Without reducing greenhouse gases, how much will global temperatures rise by 2100?',
            'choices':    ['1.5°C', '2.7°C', '5.0°C'],
            'choices_en': ['1.5°C', '2.7°C', '5.0°C'],
            'answer': 1,
            'fact':    'รายงาน AR6 ของ IPCC ระบุอุณหภูมิจะเพิ่มถึง 2.7°C ซึ่งจะส่งผลหายนะต่อระบบนิเวศทั่วโลก',
            'fact_en': 'The IPCC AR6 report projects a 2.7°C rise under current policies — catastrophic for ecosystems worldwide.',
        },
        {
            'idx': 2,
            'q':          'ก๊าซเรือนกระจกหลักที่มนุษย์ปล่อยออกมาคืออะไร?',
            'q_en':       'What is the main greenhouse gas emitted by humans?',
            'choices':    ['ออกซิเจน (O₂)', 'คาร์บอนไดออกไซด์ (CO₂)', 'ไนโตรเจน (N₂)'],
            'choices_en': ['Oxygen (O₂)', 'Carbon Dioxide (CO₂)', 'Nitrogen (N₂)'],
            'answer': 1,
            'fact':    'CO₂ จากการเผาไหม้เชื้อเพลิงฟอสซิลคือสาเหตุหลักของภาวะโลกร้อนในยุคอุตสาหกรรม',
            'fact_en': 'CO₂ from burning fossil fuels is the primary driver of global warming since the Industrial Revolution.',
        },
        {
            'idx': 3,
            'q':          'ประเทศไทยอยู่อันดับที่เท่าไรใน Climate Vulnerability Index (Germanwatch 2021)?',
            'q_en':       'What rank does Thailand hold in the Climate Vulnerability Index (Germanwatch 2021)?',
            'choices':    ['อันดับที่ 1', 'อันดับที่ 9', 'อันดับที่ 50'],
            'choices_en': ['1st', '9th', '50th'],
            'answer': 1,
            'fact':    'ไทยอยู่อันดับ 9 จาก 181 ประเทศที่เสี่ยงต่อภัยธรรมชาติจากการเปลี่ยนแปลงสภาพภูมิอากาศ',
            'fact_en': 'Thailand ranks 9th out of 181 countries most vulnerable to climate-related natural disasters.',
        },
        {
            'idx': 4,
            'q':          'มนุษย์เริ่มปล่อย CO₂ สะสมในชั้นบรรยากาศมากผิดปกตินับตั้งแต่ยุคใด?',
            'q_en':       'Since which era have humans been releasing abnormally high levels of CO₂?',
            'choices':    ['ยุคหิน', 'ยุคการปฏิวัติอุตสาหกรรม', 'ยุคสงครามโลก'],
            'choices_en': ['Stone Age', 'Industrial Revolution', 'World War Era'],
            'answer': 1,
            'fact':    'การปฏิวัติอุตสาหกรรมราว 200 ปีก่อนคือจุดเริ่มต้นของการปล่อย CO₂ ในระดับที่ไม่เคยมีในรอบ 800,000 ปี',
            'fact_en': 'The Industrial Revolution ~200 years ago marked the start of CO₂ levels unprecedented in 800,000 years.',
        },
    ],

    'flood': [
        {
            'idx': 0,
            'q':          'ระดับน้ำทะเลคาดว่าจะสูงขึ้นเท่าไรภายในปี 2100 หากไม่มีการแก้ไข?',
            'q_en':       'How much could sea levels rise by 2100 without climate action?',
            'choices':    ['0.01 เมตร', '0.28–1.01 เมตร', '10 เมตร'],
            'choices_en': ['0.01 meters', '0.28–1.01 meters', '10 meters'],
            'answer': 1,
            'fact':    'IPCC คาดการณ์ระดับน้ำทะเลสูงขึ้น 0.28–1.01 ม. กระทบประชากรชายฝั่งกว่า 1 พันล้านคน',
            'fact_en': 'IPCC projects 0.28–1.01 m sea level rise by 2100, threatening over 1 billion coastal residents.',
        },
        {
            'idx': 1,
            'q':          'เหตุการณ์น้ำท่วมรุนแรงเพิ่มความถี่เป็นกี่เท่าตั้งแต่ปี 1980?',
            'q_en':       'How many times more frequent have severe floods become since 1980?',
            'choices':    ['2 เท่า', '3 เท่า', '10 เท่า'],
            'choices_en': ['2 times', '3 times', '10 times'],
            'answer': 1,
            'fact':    'องค์การอุตุนิยมวิทยาโลก (WMO) ระบุว่าน้ำท่วมรุนแรงเพิ่มความถี่ 3 เท่าตั้งแต่ปี 1980',
            'fact_en': 'The World Meteorological Organization (WMO) reports that severe floods have tripled in frequency since 1980.',
        },
        {
            'idx': 2,
            'q':          'SDG 13 ของสหประชาชาติเกี่ยวข้องกับเรื่องอะไร?',
            'q_en':       'What does UN Sustainable Development Goal 13 address?',
            'choices':    ['Zero Hunger', 'Climate Action', 'Clean Water'],
            'choices_en': ['Zero Hunger', 'Climate Action', 'Clean Water'],
            'answer': 1,
            'fact':    'SDG 13 — Climate Action เรียกร้องให้ทุกประเทศดำเนินการเร่งด่วนเพื่อรับมือการเปลี่ยนแปลงสภาพภูมิอากาศ',
            'fact_en': 'SDG 13 — Climate Action calls on all nations to take urgent steps to combat climate change and its impacts.',
        },
        {
            'idx': 3,
            'q':          'Ice-Albedo Feedback Loop ส่งผลต่อระดับน้ำทะเลอย่างไร?',
            'q_en':       'How does the Ice-Albedo Feedback Loop affect sea levels?',
            'choices':    ['ลดระดับน้ำทะเล', 'ไม่มีผล', 'เร่งให้น้ำแข็งละลาย → ระดับน้ำสูงขึ้น'],
            'choices_en': ['Lowers sea levels', 'No effect', 'Speeds up ice melt → raises sea levels'],
            'answer': 2,
            'fact':    'น้ำแข็งขั้วโลกที่ละลายเร็วขึ้นจาก Feedback Loop เป็นสาเหตุหลักของการเพิ่มขึ้นของระดับน้ำทะเล',
            'fact_en': 'Faster polar ice melt driven by the Feedback Loop is a major contributor to rising sea levels.',
        },
        {
            'idx': 4,
            'q':          'กรีนแลนด์ตั้งอยู่บริเวณใด?',
            'q_en':       'Where is Greenland located?',
            'choices':    ['ใกล้เส้นศูนย์สูตร', 'ใกล้ขั้วโลกเหนือ', 'ใกล้ขั้วโลกใต้'],
            'choices_en': ['Near the equator', 'Near the North Pole', 'Near the South Pole'],
            'answer': 1,
            'fact':    'กรีนแลนด์อยู่ใกล้ขั้วโลกเหนือ มีแผ่นน้ำแข็งปกคลุม หากละลายทั้งหมดระดับน้ำทะเลจะสูงขึ้นถึง 7 เมตร',
            'fact_en': 'Greenland lies near the North Pole. If its ice sheet fully melted, sea levels would rise by up to 7 meters.',
        },
    ],

    'wildfire': [
        {
            'idx': 0,
            'q':          'ไฟป่าในออสเตรเลียช่วงปี 2019–2020 เผาผลาญพื้นที่กี่ล้านเฮกตาร์?',
            'q_en':       'How many million hectares did the 2019–2020 Australian wildfires burn?',
            'choices':    ['1 ล้านเฮกตาร์', '5 ล้านเฮกตาร์', '18.6 ล้านเฮกตาร์'],
            'choices_en': ['1 million hectares', '5 million hectares', '18.6 million hectares'],
            'answer': 2,
            'fact':    'ไฟป่าออสเตรเลีย "Black Summer" เผาผลาญ 18.6 ล้านเฮกตาร์ — ใหญ่กว่าประเทศไทยเกือบทั้งประเทศ',
            'fact_en': 'Australia\'s "Black Summer" fires burned 18.6 million hectares — nearly the area of the entire country of Thailand.',
        },
        {
            'idx': 1,
            'q':          'ฤดูกาลไฟป่ายาวนานขึ้นกี่เปอร์เซ็นต์เมื่อเทียบกับ 30 ปีก่อน?',
            'q_en':       'By what percentage has the wildfire season lengthened compared to 30 years ago?',
            'choices':    ['5%', '20%', '50%'],
            'choices_en': ['5%', '20%', '50%'],
            'answer': 1,
            'fact':    'การเปลี่ยนแปลงสภาพภูมิอากาศทำให้ฤดูกาลไฟป่ายาวนานขึ้นกว่า 20% สร้างความเสียหายกว้างขึ้นทุกปี',
            'fact_en': 'Climate change has extended the wildfire season by over 20%, causing wider damage every year.',
        },
        {
            'idx': 2,
            'q':          'Green Software Engineering หมายถึงอะไร?',
            'q_en':       'What does Green Software Engineering mean?',
            'choices':    ['เขียนโค้ดด้วยสีเขียว', 'ออกแบบซอฟต์แวร์ให้ใช้พลังงานน้อย', 'ใช้ระบบปฏิบัติการ Linux เท่านั้น'],
            'choices_en': ['Coding in green color', 'Designing software to use less energy', 'Using only Linux OS'],
            'answer': 1,
            'fact':    'Green Software Engineering ช่วยลด Carbon Footprint จากการประมวลผล และยืดอายุฮาร์ดแวร์รุ่นเก่า',
            'fact_en': 'Green Software Engineering reduces the carbon footprint of computing and extends the life of older hardware.',
        },
        {
            'idx': 3,
            'q':          'IPCC ย่อมาจากอะไร?',
            'q_en':       'What does IPCC stand for?',
            'choices':    ['International Police Climate Council', 'Intergovernmental Panel on Climate Change', 'Internet Protocol Climate Code'],
            'choices_en': ['International Police Climate Council', 'Intergovernmental Panel on Climate Change', 'Internet Protocol Climate Code'],
            'answer': 1,
            'fact':    'IPCC คือคณะกรรมการระหว่างรัฐบาลว่าด้วยการเปลี่ยนแปลงสภาพภูมิอากาศ รายงาน AR6 คือฉบับล่าสุด',
            'fact_en': 'IPCC is the Intergovernmental Panel on Climate Change. Its AR6 report is the latest comprehensive assessment.',
        },
        {
            'idx': 4,
            'q':          'การลดการใช้พลังงาน CPU/GPU ของซอฟต์แวร์ช่วยสิ่งแวดล้อมได้อย่างไร?',
            'q_en':       'How does reducing CPU/GPU usage in software help the environment?',
            'choices':    ['ทำให้จอภาพสว่างขึ้น', 'ลด Carbon Footprint จากการประมวลผล', 'ไม่มีผลต่อสิ่งแวดล้อม'],
            'choices_en': ['Makes screens brighter', 'Reduces carbon footprint from computing', 'Has no environmental impact'],
            'answer': 1,
            'fact':    'ทุกๆ การลดการใช้พลังงานในซอฟต์แวร์ช่วยลดการปล่อย CO₂ จากโรงไฟฟ้าที่ผลิตไฟฟ้าให้เซิร์ฟเวอร์และอุปกรณ์',
            'fact_en': 'Every reduction in software energy use lowers CO₂ emissions from power plants supplying servers and devices.',
        },
    ],
}


class QuizManager:
    """
    จัดการ Question Bank และ Session State
    - ไม่ถามข้อเดิมซ้ำภายในรอบเดียวกัน
    - reset() เมื่อเริ่มเกมใหม่
    """

    def __init__(self):
        self._asked: set = set()

    def reset(self):
        self._asked.clear()

    def get_question(self, biome_id: str) -> Optional[Dict]:
        """
        เลือก random question จาก biome ที่กำหนด
        คืน None ถ้าตอบครบทุกข้อใน biome นั้นแล้ว
        """
        pool = QUESTIONS.get(biome_id, [])
        available = [q for q in pool if (biome_id, q['idx']) not in self._asked]
        if not available:
            return None
        chosen = random.choice(available)
        self._asked.add((biome_id, chosen['idx']))
        return chosen
