class Obstacle:
    """
    Stacked crate obstacle with ice-block style progressive destruction.
    Each crate has stack_height (1-4) equal to its hp.
    Hits decrement hp by 1 and visually degrade the stack.
    Final hit (hp→0) triggers full break state.
    """
    STATE_IDLE  = 'Idle'
    STATE_HIT   = 'Hit'
    STATE_BREAK = 'Break'
    
    # Frame counts per spritesheet (Box2)
    STATE_FRAMES = {
        'Idle': 1,
        'Hit': 4,
        'Break': 4
    }

    def __init__(self, size=1):
        self.col = 0
        self.row = 0
        self.size = size            # original stack height (immutable reference)
        self.stack_height = size    # current visual stack height (decrements on hit)
        self.hp = size
        self.active = True
        self.state = self.STATE_IDLE
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.1  # seconds per frame
        
    def reset(self, size=1):
        self.size = size
        self.stack_height = size
        self.hp = size
        self.active = True
        self.state = self.STATE_IDLE
        self.anim_frame = 0
        self.anim_timer = 0

    def hit(self):
        """
        Called when penguin collides with this obstacle.
        Returns dict: {'destroyed': bool, 'old_hp': int}
        - destroyed=False: partial hit, penguin stays blocked
        - destroyed=True: final hit, obstacle goes inactive
        """
        if self.state == self.STATE_BREAK:
            return {'destroyed': False, 'old_hp': 0}
        
        old_hp = self.hp
        self.hp -= 1
        
        if self.hp <= 0:
            # Final hit — full destruction
            self.hp = 0
            self.stack_height = 0
            self.state = self.STATE_BREAK
            self.anim_frame = 0
            self.anim_timer = 0
            self.active = False
            return {'destroyed': True, 'old_hp': old_hp}
        else:
            # Partial hit — degrade visual by one layer
            self.stack_height = self.hp
            self.state = self.STATE_HIT
            self.anim_frame = 0
            self.anim_timer = 0
            return {'destroyed': False, 'old_hp': old_hp}

    def update(self, dt):
        """Update animation frames for Hit/Break sequences."""
        if not self.active:
            return

        max_frames = self.STATE_FRAMES.get(self.state, 1)
        if max_frames > 1:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame += 1
                
                if self.anim_frame >= max_frames:
                    if self.state == self.STATE_HIT:
                        # Return to idle after hit animation completes
                        self.state = self.STATE_IDLE
                        self.anim_frame = 0
                    elif self.state == self.STATE_BREAK:
                        # Break animation finished — deactivate fully
                        self.active = False
                        self.stack_height = 0

    def get_display_blocks(self):
        """Return number of crate layers to render."""
        return self.stack_height
