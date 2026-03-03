class Gem:
    \"\"\"
    ไอเทมเพชรสำหรับเก็บสะสม
    \"\"\"
    def __init__(self):
        self.active = True
        
    def reset(self):
        self.active = True

    def collect(self):
        self.active = False
        return 1 # มูลค่า 1 Gem
