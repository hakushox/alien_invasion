#
#
#
import pygame
from math import pi

class HealthArc:
    def __init__(self, owner, max_hp):
        self.owner = owner
        self.screen= owner.screen
        self.max_hp = max_hp
        self.current_hp = max_hp

        self.start_angle = pi / 4
        self.end_angle = 3 * pi / 4
        self.arcs_radian = pi / 2 / max_hp
        self.max_hp_color = (255, 255, 255)
        self.hp_color = (0, 135, 0)
        self.radius = owner.rect.height // 2 + 5
        self.arc_rect = pygame.Rect(0, 0, self.radius*2, self.radius*2)
        self.gap = self.arcs_radian * 0.1

    def update(self):
        self.arc_rect.center = self.owner.rect.center
        self.current_hp = self.owner.hp


    def draw(self):
        for i in range(self.max_hp):
            seg_start = self.start_angle + i * self.arcs_radian
            seg_stop = seg_start + self.arcs_radian - self.gap       
            if i >= self.max_hp - self.current_hp:   #血量计算的比较
                color = self.hp_color
            else:
                color = self.max_hp_color

            pygame.draw.arc(self.screen, color, self.arc_rect, 
             seg_start, seg_stop, width= 3)


