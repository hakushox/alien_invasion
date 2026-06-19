#
#
#

from math import pi
import pygame

class PowerUpGauge:
    def __init__(self, gunsys, style='weapon'):
        self.gunsys = gunsys
        self.screen = gunsys.ai_game.screen
        self.ship = gunsys.ship
        self.style = style
        self.duration = 0
        self.total_duration = 0
        self.styles = {
            'weapon':     {'color': (255, 255, 255), 'offset': 0},
            'invincible': {'color': (0, 200, 255),   'offset': 10},
            'ammo':       {'color': (255, 215, 0),   'offset': 20},
        }
        self.color = self.styles[self.style]['color']
        self.offset = self.styles[style]['offset']
        self.radius = (self.ship.rect.width // 2 if self.ship.rect.width // 2 > self.ship.rect.height // 2\
                                        else self.ship.rect.height // 2) +self.offset

        self.start_angle =  pi / 2 

        self.per_arc_radian = 2 * pi / 60 
        self.per_arc_radian_gap = 2 * pi / 60 * 0.1
        

        self.gauge_rect = pygame.Rect(0,0, self.radius * 2, self.radius * 2)
        self.surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.surface.set_alpha(178)

    def _get_duration(self):
        if self.style == 'weapon':
            return self.gunsys.timer, self.gunsys.total_duration
        elif self.style == 'invincible':
            return self.gunsys.invincible_timer, self.gunsys.invincible_total
        elif self.style == 'ammo':
            return self.gunsys.ammo_limitless, self.gunsys.ammo_total

    def update(self):
        self.gauge_rect.center = self.ship.rect.center

    def drawme(self):
        duration, total_duration = self._get_duration()

        if duration <= 0 or total_duration <= 0:
            return
        if self.style == 'weapon' and self.gunsys.mode == 0:
            return
        
        self.surface.fill((0, 0, 0, 0))

        segments_to_show = int(duration / total_duration * 60)

        arc_rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)

        for i in range(60):
            seg_start = self.start_angle + i * self.per_arc_radian
            seg_stop = seg_start + self.per_arc_radian_gap
            if i < segments_to_show:
                pygame.draw.arc(self.surface, self.color, arc_rect,
                                seg_start, seg_stop, width=10)

        self.screen.blit(self.surface, self.gauge_rect.topleft)
# if i >= 60 - segments_to_show else (80, 80, 80)
