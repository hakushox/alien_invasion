import pygame
import math
from bullet import Bullet
import random
from gunsystem import GunSystem
from resource_manager import resource_path


class Escort:
    def __init__(self, ai_game, stage='normal', side='left'):
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.screen = ai_game.screen
        self.ship = ai_game.ship
        self.level = ai_game.stats.level

        self.stage = stage
        self.side = side

        self.images = {
            'normal': pygame.transform.scale(
                pygame.image.load(
                    resource_path('images/ship/escort_normal.png')
                ).convert_alpha(),
                (91, 61)
            ),
            'large': pygame.transform.scale(
                pygame.image.load(
                    resource_path('images/ship/escort_large.png')
                ).convert_alpha(),
                (120, 80)
            ),
        }
        
        self.image = self.images[self.stage]
        self.image_rect = self.image.get_rect()
        self.image_rect.x, self.image_rect.y = (0, 0)
        self.rect = self.image_rect
        if self.stage == 'large':
            self.gunsys = GunSystem(ai_game, owner=self, bullet_group=ai_game.escort_bullets)
            self.shoot_timer = random.randint(
            40, int(max(80, 460 - math.sqrt(self.level) * 100))
        )
        else:
            self.shoot_timer = random.randint(
            int(max(30, 90 - self.level * 4)), int(max(60, 420 - math.sqrt(self.level) * 100))
        )
            self.gunsys = None
        
        self.timer = 60 * 30
        self.angle = 0

        # self.shoot_timer = random.randint(
        #     60, int(max(90, 420 - math.sqrt(self.level) * 100))
        # )
        self.multi_timer_active = False
        self.multi_timer_ticks = 720 

        self.half_cooldown = self.shoot_timer // 2
        self.reset_pos_timer = self.half_cooldown
        self.cannon_cooldown = 60
        self.display_angle = 0

    def normalize_angle(self, angle):
        """把角度限制到 [-180, 180]"""
        return (angle + 180) % 360 - 180

    def update(self):
        if self.stage == 'large':
            self.gunsys.get_timer()  # 每帧更新gauge位置
            if self.gunsys.timer <= 0 and self.gunsys.mode != 0:
                self.gunsys.mode = 0
                self.gunsys.buff = 1
                self.gunsys.bullet_count = 0
        if self.multi_timer_active:
            self.multi_timer_ticks -= 1
            if self.multi_timer_ticks <= 0:
                self.multi_timer_active = False

        self.shoot()
        self.timer -= 1
        if self.timer <= 0:
            self.ai_game.escorts.remove(self)
            self.ai_game.escort_count = len(self.ai_game.escorts)
            return

        orig_w = self.images[self.stage].get_width()

        if self.side == 'left':
            self.image_rect.centerx = self.ship.rect.x - orig_w // 2
        else:
            self.image_rect.centerx = self.ship.rect.right + orig_w // 2

        self.image_rect.centery = self.ship.rect.centery
        self.rect = self.image_rect

    def shoot(self):   
        
        if self.gunsys and self.gunsys.mode == 3:
            old_center = self.image_rect.center
            self.image = self.images[self.stage]
            self.image_rect = self.image.get_rect()
            self.image_rect.center = old_center
            return
        if not self.ai_game.aliens:
            self.angle = 0
            self.image = self.images[self.stage]
            return

        if self.cannon_cooldown > 0:
            self.cannon_cooldown -= 1
            return

        self.shoot_timer -= 1
        # 回正阶段
        if self.shoot_timer >= self.half_cooldown:
            if self.reset_pos_timer > 0:
                self.reset_pos_timer -= 1
                self.display_angle *= 0.8

                old_center = self.image_rect.center
                self.image = pygame.transform.rotate(
                    self.images[self.stage],
                    self.display_angle
                )
                self.image_rect = self.image.get_rect()
                self.image_rect.center = old_center
                self.rect = self.image_rect

            else:
                self.angle = 0
                old_center = self.image_rect.center
                self.image = self.images[self.stage]
                self.image_rect = self.image.get_rect()
                self.image_rect.center = old_center
                self.rect = self.image_rect
                
            return

        # 寻找最近目标
        target = min(self.ai_game.aliens, key=lambda a: math.hypot(
                a.rect.centerx - self.image_rect.centerx,
                a.rect.centery - self.image_rect.centery
            ))

        dx = target.rect.centerx - self.image_rect.centerx
        dy = target.rect.centery - self.image_rect.centery
        self.angle = math.atan2(dy, dx)

        rotation = self.normalize_angle(-math.degrees(self.angle) - 90)

        old_center = self.image_rect.center
        self.image = pygame.transform.rotate(self.images[self.stage], rotation)
        self.image_rect = self.image.get_rect()
        self.image_rect.center = old_center

        # 开火
        if self.shoot_timer <= 0:
            if self.stage == 'large':
                self.settings.escort_channel.play(self.settings.escort_shotl)
                before = set(self.ai_game.escort_bullets)
                self.gunsys.modes[self.gunsys.mode]()
                new_bullets = set(self.ai_game.escort_bullets) - before
                for b in new_bullets:
                    b.angle += math.degrees(self.angle) + 90
                if self.gunsys.mode == 1:
                    offsets = self.gunsys._last_offsets
                    perp = math.radians(math.degrees(self.angle) + 90 + 90)
                    sorted_bullets = sorted(new_bullets, key=lambda b: b.rect.x)
                    for b, offset in zip(sorted_bullets, offsets):
                        b.rect.centerx += int(math.sin(perp) * offset)
                        b.rect.centery += int(math.cos(perp) * offset)
                        b.x = float(b.rect.x)
                        b.y = float(b.rect.y)

            else:
                bullet = Bullet(self.ai_game, owner=self)
                bullet.angle = math.degrees(self.angle) + 90
                self.ai_game.escort_bullets.add(bullet)
                self.settings.escort_channel.play(self.settings.escort_shot)


            self.display_angle = rotation

            if self.stage == 'large':
                base = random.randint(90, int(max(120, 360 - math.sqrt(self.level))))
            else:
                base = random.randint(
                    int(max(30, 90 - self.level * 4)), int(max(90, 460 - math.sqrt(self.level) * 100))
                )
            self.shoot_timer = base // 5 if self.multi_timer_active else base

            self.half_cooldown = self.shoot_timer // 2
            self.reset_pos_timer = self.half_cooldown
            self.cannon_cooldown = 60

        self.rect = self.image_rect

    def shoot_laser(self):
        if not self.gunsys:
            return
        if self.gunsys.mode != 3:
            return
        if self.gunsys.laser_exhausted: 
            return
        self.gunsys.modes[3]()

    def blitme(self):
        if self.timer > 0:
            self.screen.blit(self.image, self.image_rect)