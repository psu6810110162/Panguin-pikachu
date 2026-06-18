import random

class ParticleShard:
    """
    A single shard of an obstacle.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-200, 200)
        self.vy = random.uniform(100, 300)
        self.life = 0.4  # Automatically delete after 0.4 seconds

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 800.0 * dt  # Gravity decay
        self.life -= dt

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_shards(self, x, y, count=5):
        for _ in range(count):
            self.particles.append(ParticleShard(x, y))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
