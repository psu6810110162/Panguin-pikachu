PROP_BLANK   = ""
PROP_ICE1    = "ice1"    # เหยียบ 1 ครั้งหาย
PROP_ICE2    = "ice2"    # เหยียบ → ice1
PROP_ICE3    = "ice3"    # เหยียบ → ice2
PROP_FORCE   = "force"   # Gold buff 5s
PROP_REVERSE = "reverse" # Dark buff — สลับซ้าย/ขวา
PROP_TRAP    = "trap"    # seal (ตาย) หรือ whale-tail (fly 15–25 tiles)

ICE_DEGRADE = {
    PROP_ICE3: PROP_ICE2,
    PROP_ICE2: PROP_ICE1,
    PROP_ICE1: PROP_BLANK,
}

def hit_ice(current_prop):
    """คืนค่า prop ใหม่หลังเหยียบ ice (ice3→ice2→ice1→blank)"""
    return ICE_DEGRADE.get(current_prop, PROP_BLANK)
