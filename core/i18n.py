import json
import os

_LANG = 'th'
_SETTINGS_PATH = os.path.expanduser('~/.panguin_settings.json')

STRINGS = {
    'th': {
        # ── Climate Report (Learning Path) ──────────────────
        'subtitle':      'สิ่งที่คุณได้เรียนรู้จากการวิ่ง',
        'back':          'กลับ',
        'no_quiz':       'ยังไม่เคยเล่น Quiz',
        'total_score':   'คะแนนรวม  {c}/{t}  ({pct}%)',
        'correct_of':    '{c}/{t} ถูก',
        'asked_n':       'ถาม {n} ครั้ง',
        'not_asked':     'ยังไม่ถาม',
        'master':        'MASTER',
        'view_facts':    'ดูข้อมูล',
        'reset':         'รีเซ็ต',
        'reset_confirm': 'รีเซ็ตความคืบหน้าทั้งหมดหรือไม่?',
        'confirm':       'ยืนยัน',
        'cancel':        'ยกเลิก',
        'accuracy':      'แม่น {pct}%',
        'challenge':     'Climate Challenge!',
        'timeout':       'หมดเวลา!',
        'correct_msg':   'ถูกต้อง!',
        'wrong_msg':     'ไม่ถูกต้อง',
        'close':         'ปิด',
        'climate_facts': 'ข้อเท็จจริงสภาพภูมิอากาศ',
        'toggle_lang':   'EN',
        # ── Menu ────────────────────────────────────────────
        'start_game':    'เริ่มเกม',
        'skins':         'สกิน',
        'history':       'ประวัติ',
        'climate_report':'รายงานภูมิอากาศ',
        'exit':          'ออก',
        'menu_tagline':  'ทุกก้าวมีความหมาย น้ำแข็งไม่รอใคร',
        # ── Game Over ───────────────────────────────────────
        'game_over':        'เกมจบแล้ว',
        'play_again':       'เล่นอีกครั้ง',
        'home':             'หน้าหลัก',
        'enter_name':       'พิมพ์ชื่อของคุณ',
        'distance_prefix':  'ระยะทาง: ',
        # ── History ─────────────────────────────────────────
        'leaderboard':   'กระดานผู้นำ',
        'no_history':    'ยังไม่มีประวัติ',
        # ── Shop ────────────────────────────────────────────
        'skins_title':   'สกิน',
        'equipped':      'กำลังสวม',
        'equip':         'สวมใส่',
        'buy_gems':      'ซื้อด้วย 10 เจม',
        # ── Quiz Popup ──────────────────────────────────────
        'quiz_correct_prefix': 'ถูกต้อง! +{gems}  ',
        'quiz_wrong_prefix':   'ผิด!  ',
    },
    'en': {
        # ── Climate Report (Learning Path) ──────────────────
        'subtitle':      'What You Learned From Running',
        'back':          'BACK',
        'no_quiz':       'No Quiz Played Yet',
        'total_score':   'Total Score  {c}/{t}  ({pct}%)',
        'correct_of':    '{c}/{t} Correct',
        'asked_n':       'Asked {n} Times',
        'not_asked':     'Not Started',
        'master':        'MASTER',
        'view_facts':    'View Facts',
        'reset':         'RESET',
        'reset_confirm': 'Reset all quiz progress?',
        'confirm':       'Confirm',
        'cancel':        'Cancel',
        'accuracy':      '{pct}% Accuracy',
        'challenge':     'Climate Challenge!',
        'timeout':       'Time Up!',
        'correct_msg':   'Correct!',
        'wrong_msg':     'Wrong',
        'close':         'Close',
        'climate_facts': 'Climate Facts',
        'toggle_lang':   'TH',
        # ── Menu ────────────────────────────────────────────
        'start_game':    'START GAME',
        'skins':         'SKINS',
        'history':       'HISTORY',
        'climate_report':'CLIMATE REPORT',
        'exit':          'EXIT',
        'menu_tagline':  "Every step counts. The ice won't wait.",
        # ── Game Over ───────────────────────────────────────
        'game_over':        'GAME OVER',
        'play_again':       'PLAY AGAIN',
        'home':             'HOME',
        'enter_name':       'Enter your name',
        'distance_prefix':  'DISTANCE: ',
        # ── History ─────────────────────────────────────────
        'leaderboard':   'LEADERBOARD',
        'no_history':    'NO HISTORY YET',
        # ── Shop ────────────────────────────────────────────
        'skins_title':   'SKINS',
        'equipped':      'EQUIPPED',
        'equip':         'EQUIP',
        'buy_gems':      'BUY (10 GEMS)',
        # ── Quiz Popup ──────────────────────────────────────
        'quiz_correct_prefix': 'Correct! +{gems}  ',
        'quiz_wrong_prefix':   'Wrong!  ',
    },
}


FONT_KF   = 'assets/Component_UI/Font/Kenney Future.ttf'
FONT_THAI = 'assets/Component_UI/Font/Thonburi.ttc'


def get_font() -> str:
    """คืน font ที่ถูกต้องตามภาษาปัจจุบัน — ใช้แทนการ hardcode font_name ทุกที่"""
    return FONT_THAI if _LANG == 'th' else FONT_KF


def t(key: str, **kwargs) -> str:
    s = STRINGS.get(_LANG, STRINGS['th']).get(key, key)
    return s.format(**kwargs) if kwargs else s


def set_language(lang: str):
    global _LANG
    _LANG = lang
    _save()


def get_language() -> str:
    return _LANG


def load():
    global _LANG
    try:
        with open(_SETTINGS_PATH) as f:
            _LANG = json.load(f).get('lang', 'th')
    except (FileNotFoundError, json.JSONDecodeError):
        _LANG = 'th'


def _save():
    try:
        data = {}
        try:
            with open(_SETTINGS_PATH) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        data['lang'] = _LANG
        with open(_SETTINGS_PATH, 'w') as f:
            json.dump(data, f)
    except OSError:
        pass
