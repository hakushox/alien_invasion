#
#
#

import pygame
from alien_ai import AlienAi
import math
import random
from gunsystem import GunSystem
from bullet import Bullet
from laser import LaserBeam
# from timer import timer
from health_arc import HealthArc

from resource_manager import resource_path

class Boss(AlienAi):
    # @timer
    def __init__(self, ai_game, level):
        super().__init__(ai_game)
        self.boss_images = {
                    0: pygame.transform.scale(pygame.image.load(resource_path('images/boss/boss_idle.png')).convert_alpha(), (300, 200)),
                    1: pygame.transform.scale(pygame.image.load(resource_path('images/boss/boss_hunt.png')).convert_alpha(), (300, 200)),
                    2: pygame.transform.scale(pygame.image.load(resource_path('images/boss/boss_fury.png')).convert_alpha(), (300, 200)),
                    3: pygame.transform.scale(pygame.image.load(resource_path('images/boss/boss_beaten.png')).convert_alpha(), (300, 200)),
                }   
        self.status_image = 0
        self.image = self.boss_images[self.status_image]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.settings.screen_width//2  - self.rect.width // 2, self.settings.screen_height//2 - self.rect.height
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.level = level

        self.hp = 20 + level * 10
        self.hp_max = self.hp
        self.health_arc = HealthArc(self, self.hp)

        self.stage = 'idle'
        self.charge_timer = 0
        self.charge_prepare = 120

        self.speed = self.settings.boss_speed

        self.bounce_count = 3
        self.bounce_speed = 2
        self.bounce_timer = 0
        self.bounce_duration = 9

        self.charge_thresholds = [(int(self.hp * 0.8), 'prepare'),
                                  (int(self.hp * 0.6), 'hunt'), 
                                  (int(self.hp * 0.3), 'fury')]
        self.charge_index = 0

        self.shoot_timer = random.randint(60, max(100, 240 - level * 10))

        self.powerup_timer = 0

        self.fury_timer = 0
        self.fury_duration = 150
        self.fury_timer = self.fury_duration
        self.charge_multiplifier = min(5 + level / 2 , 12)
        self.fury_speed_boosted = True

        self.laser = LaserBeam(ai_game, self)
        
        self.gunsys = GunSystem(self.ai_game, owner=self, bullet_group=self.ai_game.boss_bullets, buff= 0)

        self.explode_duration = 120
        self.appeared = False 

        self.recent_damage = []
        self.frame_count = 0
        self.damage_window = 90
        self.damage_threshold = 10 + ai_game.stats.level * 1.5

    def _bounce(self):
        '''每帧减计时器，归零时反转方向、衰减速度、减次数、重置计时器 次数用完切换return。'''
        
        if self.bounce_timer > 0 and self.bounce_count > 0:
            self.bounce_timer -= 1
            self.x += self.direction_x * self.bounce_speed
            self.y += self.direction_y * self.bounce_speed
        elif self.bounce_timer <= 0:
            self.direction_x = self.direction_x * -1
            self.direction_y = self.direction_y * -1
            self.bounce_speed *= 0.6
            self.bounce_timer = self.bounce_duration / 2
            self.bounce_count -= 1
        
        if self.bounce_count <= 0:
            self.stage = 'return'
            self.bounce_speed = 2
        # print(f"timer:{self.bounce_timer} count:{self.bounce_count} speed:{self.bounce_speed:.1f}")
            
    def explode(self):
        self.status_image = 3
        self.explode_timer = self.explode_duration

    def _move_to_powerup(self):
        if not self.ai_game.powerups:
            return
        if self.gunsys.mode != 0:
            return
        if any(p.powerup_type in ['life', 'spread', 'scatter', 'laser'] for p in self.ai_game.powerups):
            target = min(self.ai_game.powerups, key=lambda p: 
                        math.hypot(p.rect.centerx - self.rect.centerx, p.rect.centery - self.rect.centery))
            dx = target.rect.centerx - self.rect.centerx
            dy = target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist == 0:
                return
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def collect_powerup(self, powerup):
        if powerup.powerup_type == 'life':
            self.hp += self.max_hp * 0.5
            self.gunsys.timer = powerup.weapon_duration  // 1.5
            self.gunsys.total_duration = powerup.weapon_duration // 1.5
            self.powerup_timer = self.gunsys.timer
        elif powerup.powerup_type in ['spread', 'scatter', 'laser']:
            self.gunsys.mode = powerup.mode
            self.gunsys.bullet_count = powerup.bullet_count
            self.gunsys.timer = powerup.weapon_duration // 1.5     
            self.gunsys.total_duration = powerup.weapon_duration // 1.5
            self.powerup_timer = self.gunsys.timer
    
    def _shoot(self):
        if self.gunsys and getattr(self.gunsys, 'exhausted', False):
            self.gunsys.mode = 0
            self.gunsys.exhausted = False
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:   
            ship = self.ai_game.ship
            dx = ship.rect.centerx - self.rect.centerx
            dy = ship.rect.centery - self.rect.centery
            base_angle = math.degrees(math.atan2(dy, dx)) + 90  

            if self.gunsys.mode == 3:              
                dist = math.hypot(dx, dy)
                self.laser.fire(self.rect.centerx, self.rect.centery, dx/dist, dy/dist)
                self.shoot_timer = random.randint(150, max(250, 500 - self.level * 10))               
                return    
                               
            before = set(self.ai_game.boss_bullets)
            self.gunsys.modes[self.gunsys.mode]()
            new_bullets = set(self.ai_game.boss_bullets) - before                         
            for bullet in new_bullets:
                bullet.angle += base_angle

            if self.gunsys.mode == 1:
                offsets = self.gunsys._last_offsets
                perp = math.radians(base_angle + 90)
                
                for bullet, offset in zip(new_bullets, offsets):
                    bullet.rect.centerx += int(math.sin(perp) * offset)
                    bullet.rect.centery += int(math.cos(perp) * offset)
                    bullet.x = float(bullet.rect.x)
                    bullet.y = float(bullet.rect.y)

            self.shoot_timer = random.randint(60, max(100, 240 - self.level * 10))

    def _stage_check(self):
        new_index = sum(1 for t, _ in self.charge_thresholds if self.hp < t)
        if new_index > self.charge_index:
            self.charge_index = new_index
            _, next_stage = self.charge_thresholds[new_index - 1]
            self.stage = next_stage       
                
            if self.stage == 'prepare':
                self.charge_timer = self.charge_prepare     

    def update(self):
        if not self.appeared:
            self.appeared = True       # ← 就在这里改，第一帧进来就设成True
            self.settings.boss_channel.play(self.settings.boss_appear)

        if self.explode_timer > 0:
            self.health_arc.update()
            super().update()
            return
        self.frame_count += 1
        self.recent_damage = [(f, d) for f, d in self.recent_damage
                              if self.frame_count - f <= self.damage_window]
        total_recent_damage = sum(d for _, d in self.recent_damage)
        if total_recent_damage >= self.damage_threshold:
            self.stage == 'prepare'
            self.charge_timer = self.charge_prepare
            self.recent_damage.clear()

        self.laser.update()
        if self.gunsys:
            self.gunsys.get_timer()

        if self.stage != 'fury' and self.stage != 'prepare' and self.stage != 'charge':
            if self.hp > self.hp_max * 0.5:
                self.status_image = 0

        if self.hp <= 0:
            self.status_image = 3
                    
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.laser.stop()
                self.gunsys.mode = 0
                self.gunsys.bullet_count = 0   

        if self.stage == 'idle':

            self.x += self.settings.alien_speed * self.direction_x           
          
            if self.x  <= 0 or self.x + self.rect.width > self.settings.screen_width:
                self.direction_x *= -1
            
            self._shoot()
            self._stage_check()

        elif self.stage == 'prepare':
            self.settings.boss_channel.play(self.settings.boss_charge)
            
            self.status_image = 1
            ship = self.ai_game.ship
            angle = math.degrees(math.atan2(ship.rect.centery - (self.y +self.rect.width // 2), 
                                            ship.rect.centerx - (self.x + self.rect.width // 2)))
            old_center = self.rect.center
            self.image = pygame.transform.rotate(self.boss_images[self.status_image], -angle+ 90)   
            self.rect = self.image.get_rect()
            self.rect.center = old_center    

            self.charge_timer -= 1
            if self.charge_index >= 2:
                self._shoot()

            if self.charge_timer <= 0:

                self.stage = 'charge'
                self.target_x = ship.rect.centerx
                self.target_y = ship.rect.centery

                dx = self.target_x - (self.x + self.rect.width//2)
                dy = self.target_y - (self.y + self.rect.height//2)
                dist = math.hypot(dx, dy)

                self.direction_x = dx / dist
                self.direction_y = dy / dist

                # self.direction_x = 0 if abs(dx) < 50 else (1 if dx > 0 else -1)
                # self.direction_y = 0 if abs(dy) < 50 else (1 if dy > 0 else -1)

        elif self.stage == 'charge':
            self.settings.boss_channel.play(self.settings.boss_hiss)

            self.x += self.direction_x * self.charge_multiplifier
            self.y += self.direction_y * self.charge_multiplifier

            if self.rect.centery >= self.settings.screen_height or self.rect.centery <= 0 \
                        or self.rect.centerx >= self.settings.screen_width or self.rect.centerx <= 0:

                self.stage = 'bounce'
                self.bounce_timer = self.bounce_duration
                self.bounce_count = 6
                self.direction_x = self.direction_x * -1
                self.direction_y = self.direction_y * -1

        elif self.stage == 'bounce':                       
            self._bounce()

        elif self.stage == 'return':
            if self.charge_index >= 2 and any(p.powerup_type in ['life', 'spread', 'scatter', 'laser'] for p in self.ai_game.powerups):
                self._move_to_powerup()
            else:        
                orig_w = self.boss_images[0].get_width()
                orig_h = self.boss_images[0].get_height()
                dx = self.settings.screen_width // 2 - (self.x + orig_w // 2)
                dy = self.settings.screen_height // 2 - (self.y + orig_h // 2)
                dist = math.sqrt(dx ** 2 + dy ** 2)
                speed = max(min(dist * 0.05, self.speed * 1.5), self.speed)
 
                if dist <= 10:
                    self.image = self.boss_images[self.status_image]
                    self.rect = self.image.get_rect()
                    self.rect.centerx = self.settings.screen_width // 2
                    self.rect.centery = self.settings.screen_height // 2
                    self.x = float(self.rect.x)
                    self.y = float(self.rect.y)

                    if self.charge_index >=2:
                        self.stage = 'fury'
                        self._shoot()
                        if self.fury_speed_boosted:
                            self.speed = self.speed + self.speed / 2
                            self.shoot_timer = random.randint(0, max(80, 200 - self.level * 10))
                            self.fury_speed_boosted = False                            
                    else:
                        self.stage = 'idle'
                else:
                    self.x += dx/dist * speed
                    self.y += dy/dist * speed

        if self.stage == 'hunt':
            self.settings.boss_channel.play(self.settings.boss_stagger)
            self._move_to_powerup()
            self._shoot()
            self._stage_check()
            self.x += self.settings.alien_speed * self.direction_x                 
            if self.x  <= 0 or self.x + self.rect.width > self.settings.screen_width:
                self.direction_x *= -1
        
        elif self.stage == 'fury':
            self.settings.boss_channel.play(self.settings.boss_fury)
            self.status_image = 2
           
            self._move_to_powerup()
            self._shoot()

            self.x += self.settings.alien_speed * self.direction_x                 
            if self.x  <= 0 or self.x + self.rect.width > self.settings.screen_width:
                self.direction_x *= -1

            self.fury_timer -= 1
            if self.fury_timer <= 0:
                self.stage = 'prepare'
                self.fury_timer = self.fury_duration
                self.charge_timer = int(self.charge_prepare * random.uniform(0.6, 0.9))
                self.charge_multiplifier = min(5 + self.level * 0.8, 15)

        if self.stage != 'prepare':
            self.image = self.boss_images[self.status_image]
        
        self.rect.x = self.x
        self.rect.y = self.y
        self.mask = pygame.mask.from_surface(self.image)
        self.health_arc.update()
    
    def explode(self):
        self.image = self.boss_images[3]
        self.explode_timer = self.explode_duration
