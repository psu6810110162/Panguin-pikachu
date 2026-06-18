import random

class ParticleShard:
    """
    A single shard particle with physics (velocity + gravity).
    """
    def __init__(self, x, y, vx=None, vy=None, life=0.4, size=6):
        self.x = x
        self.y = y
        self.vx = vx if vx is not None else random.uniform(-200, 200)
        self.vy = vy if vy is not None else random.uniform(100, 300)
        self.life = life
        self.max_life = life
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 800.0 * dt  # Gravity decay
        self.life -= dt

    @property
    def alpha(self):
        """Fade out as life decreases."""
        return max(0.0, self.life / self.max_life)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_shards(self, x, y, count=5):
        """Spawn small shard burst for partial crate hits (top-layer chip)."""
        for _ in range(count):
            self.particles.append(ParticleShard(
                x + random.uniform(-10, 10),
                y + random.uniform(-5, 5),
                vx=random.uniform(-150, 150),
                vy=random.uniform(80, 250),
                life=0.4,
                size=5
            ))

    def spawn_explosion(self, x, y, count=10):
        """Spawn full crate shattering explosion with wider, more dramatic spread."""
        for _ in range(count):
            self.particles.append(ParticleShard(
                x + random.uniform(-15, 15),
                y + random.uniform(-10, 10),
                vx=random.uniform(-350, 350),
                vy=random.uniform(150, 500),
                life=0.6,
                size=random.choice([5, 7, 9])
            ))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
