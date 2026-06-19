#
import math

import pygame
import random
from powerup import PowerUp

class ShockWave:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.x = ai_game.ship.rect.centerx
        self.y = ai_game.ship.rect.centery
        self.radius = 0
        self.speed = 25
        self.max_radius = math.hypot (ai_game.settings.screen_width, ai_game.settings.screen_height)

        self.done = False
        self.hit_aliens = set()

    def update(self):
        from boss import Boss
        self.radius += self.speed
        for a in list(self.ai_game.aliens):
            if a in self.hit_aliens:
                continue
            dist = math.hypot(a.rect.centerx - self.x, a.rect.centery - self.y)

            if dist <= self.radius:
                self.hit_aliens.add(a)
                if getattr(a, 'hp', False):
                    a.hp -= 5 + self.ai_game.stats.level // 3 if isinstance(a, Boss) else 2 + self.ai_game.stats.level // 5
                    if a.hp <= 0 and not a.explode_timer:
                        a.explode()
                        a.explode_timer = 60
                        if isinstance(a, Boss):
                            self.ai_game.settings.boss_defeated.play()
                            for _ in range(random.randint(1, 3)):
                                p = PowerUp(self.ai_game, a.rect.centerx + random.randint(-200, 200),
                                                          a.rect.centery + random.randint(-300, 300))
                                self.ai_game.powerups.add(p)
                        else:
                            self.ai_game.stats.score += self.ai_game.settings.alien_points
                            if random.random() < self.ai_game.settings.powerup_odds:
                                self.ai_game.powerups.add(PowerUp(self.ai_game, a.rect.centerx, a.rect.centery))
                else:
                    a.explode()
                    a.explode_timer = 60
                    self.ai_game.stats.score += self.ai_game.settings.alien_points
                    if random.random() < self.ai_game.settings.powerup_odds:
                        self.ai_game.powerups.add(PowerUp(self.ai_game, a.rect.centerx, a.rect.centery))
        
        self.ai_game.sb.prep_score()
        self.ai_game.sb.check_high_score()

        if self.radius >= self.max_radius:
            self.ai_game._check_level_up()
            self.done = True

    def draw(self):
        if not self.done:
            pygame.draw.circle(self.screen, (255, 255, 200),
                             (self.x, self.y), int(self.radius), 3)    

                    

