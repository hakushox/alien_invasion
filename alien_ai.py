#
#
#

import random
from alien import Alien
from timer import timer
from health_arc import HealthArc

class AlienAi(Alien):
    # @timer
    def __init__(self, ai_game):
        super().__init__(ai_game)
        self.ai_game = ai_game
        self.settings = ai_game.settings

        self.hp = 2 + max(0, (self.ai_game.stats.level - 5) // 2)
        self.health_arc = HealthArc(self, self.hp)

        self.speed = self.settings.alien_speed
        self.direction_x = random.choice([-1, 1])
        self.direction_y = random.choice([-1, 1])
        self.move_timer = random.randint(60, 180)
        

    def update(self):
        if self.explode_timer > 0:
            self.health_arc.update()
            super().update()
            return
        if self.move_timer <= 0:
            ship = self.ai_game.ship
            if random.random() < 0.7:
                self.direction_x = 1 if ship.rect.x > self.rect.x else -1
                self.direction_y = 1 if ship.rect.y > self.rect.y else -1
            else:
                self.direction_x = random.choice([-1, 1])
                self.direction_y = random.choice([-1, 1])
            self.move_timer = random.randint(60, 300)

        self.move_timer -= 1
        self.rect.x +=  self.direction_x * self.settings.alien_speed
        self.rect.y += self.direction_y * self.settings.alien_speed

        if self.rect.left <= 0 or self.rect.right > self.settings.screen_width:
            self.direction_x *= -1
        if self.rect.bottom >= self.settings.screen_height or self.rect.top <= 0:
            self.direction_y *= -1
        self.health_arc.update()
    def check_edges(self):
        return False