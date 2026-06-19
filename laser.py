#if True:	True	‌执行‌
#if not True:	False	‌不执行‌
#if False:	False	‌不执行‌
#if not False:	True	‌执行
#


import pygame
import math
import random
from timer import timer

class LaserBeam:
    @timer
    def __init__(self, ai_game, owner):
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.screen =ai_game.screen
        self.owner = owner

        self.color = (88, 88, 88)
        self.width = 3
        self.tail_length = 300
        self.speed = 12
        self.max_bounces = 4

        self.active = False
        self.hit_ship = False

        # self.head_x = 0.0
        # self.head_y = 0.0
        # self.dir_x = 0.0
        # self.dir_y = 0.0

        self.lasers = []


    def fire(self, start_x, start_y, dir_x, dir_y):
        self.active = True

        self.lasers.append({'path': [(start_x, start_y)],       # 折点列表，初始只有发射点
                            'head_x': start_x, 
                            'head_y': start_y,
                            'dir_x': dir_x,              # 头部当前方向，单位向量
                            'dir_y': dir_y, 
                            'bounces': 0, 
                            'escaped': False,               # 超过max_bounces次后设True
                            'total_travel': 0.0,
                            })
        sounds = [self.settings.laser_shot1_sound, self.settings.laser_shot2_sound]
        self.settings.boss_laser_sound_channel.play(random.choice(sounds))

    def stop(self):
        self.active = False
        self.lasers =[]

    def _move_head(self, laser):
        screen_w = self.settings.screen_width
        screen_h = self.settings.screen_height

        new_x = laser['head_x'] + laser['dir_x'] * self.speed
        new_y = laser['head_y'] + laser['dir_y'] * self.speed

        if not laser['escaped']:
            hit = False
            if new_x <= 0:
                new_x = 0
                laser['dir_x'] = abs(laser['dir_x'])
                hit = True
            elif new_x > screen_w:
                new_x = float(screen_w)
                laser['dir_x'] = -abs(laser['dir_x'])
                hit = True

            if new_y <= 0:
                new_y = 0
                laser['dir_y'] = abs(laser['dir_y'])    # 强制向下
                hit = True
            elif new_y >= screen_h:
                new_y = float(screen_h)
                laser['dir_y'] = -abs(laser['dir_y'])    # 强制向上
                hit = True
            
            if hit:
                laser['path'].append((new_x, new_y))   ## 碰边的点坐标加入path作为新折点，之后头部从这里沿新方向继续
                laser['bounces'] += 1
                if laser['bounces'] > self.max_bounces:
                    laser['escaped'] = True
        
        laser['head_x'] = new_x
        laser['head_y'] = new_y
        laser['total_travel'] += self.speed
    
    def _is_gone(self, laser):
        if not laser['escaped']:
            return False
        screen_w = self.settings.screen_width
        screen_h = self.settings.screen_height
        return (laser['head_x'] < 0 or laser['head_x'] > screen_w or
                laser['head_y'] < 0 or laser['head_y'] > screen_h)

    def _get_draw_segments(self, laser):
        points = laser['path'] + [(laser['head_x'], laser['head_y'])]

        segments = []
        remaining = self.tail_length
        
        for i in range(len(points) - 1, 0, -1):
            x2, y2 = points[i]
            x1, y1 = points[i -1]
            seg_len = math.hypot(x2- x1, y2- y1)

            if seg_len <=0:
                continue        #跳过 从头再循环下一轮
            if seg_len <= remaining:
                segments.append((x1,y1,x2,y2))
                remaining -= seg_len
            else:
                ratio = remaining / seg_len     #缩放系数（scale factor：我要走的距离，占整条向量长度的多少比例。
                cut_x = x2 + (x1 - x2) * ratio      #终点 - 起点 = 方向向量  
                cut_y = y2 + (y1 - y2) * ratio
                segments.append((cut_x, cut_y, x2, y2))
                break
        
        return segments
    
    def _check_hit(self, laser):
        if self.ai_game.gunsys.invincible_timer > 0:
            ship_rect = self.ai_game.ship.rect
            for x1, y1, x2, y2 in self._get_draw_segments(laser):
                if ship_rect.clipline(x1, y1, x2, y2):
                    laser['escaped'] = True  # 标记为消失
                    return False  # 
        ship_rect = self.ai_game.ship.rect
        for x1, y1, x2, y2 in self._get_draw_segments(laser):
            if ship_rect.clipline(x1, y1, x2, y2):
                return True
        return False
    def update(self):
        if not self.active:
            return

        for laser in self.lasers:
            self._move_head(laser)

        # any()：只要有一条laser打中ship就返回True
        self.hit_ship = any(self._check_hit(laser) for laser in self.lasers)

        # 列表推导式过滤掉已消失的laser
        # _is_gone()返回True表示这条laser已飞出屏幕，这条 laser 不进入新列表，相当于从列表删除
        self.lasers = [l for l in self.lasers if not self._is_gone(l)]

        if not self.lasers:
            self.active = False

    def draw(self):
        if not self.active:
            return
        for laser in self.lasers:
            for x1, y1, x2, y2 in self._get_draw_segments(laser):
                pygame.draw.line(self.screen, self.color,
                                 (int(x1), int(y1)), (int(x2), int(y2)), self.width)
                


