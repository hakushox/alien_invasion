#
#
#
import pygame
from pygame.sprite import Sprite 
import random
from alien_ai import AlienAi
from timer import timer

from resource_manager import resource_path

class PowerUp(Sprite):
    '''道具地点'''
    _images = {}    # 类属性，所有实例共享
    # @timer
    def __init__(self, ai_game, x, y):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.ai_game = ai_game
        self.screen_rect = self.screen.get_rect()

        # powerup_type 是唯一来源，mode 和图片都从它派生
        type_to_mode = {
            'life': 0, 'spread': 1, 'scatter': 2, 'laser': 3,
            'invincible': 4, 'kill_all': 5, 'ammo': 6, 'escort': 7,
        }

        if random.random() < self.settings.life_powerup_odds:
            # 非武器类道具
            self.powerup_type = random.choice(['life', 'invincible', 'kill_all', 'ammo', 'escort'])
        else:
            # 武器类道具，细分成具体类型
            # self.powerup_type = random.choice(['escort'])
            self.powerup_type = random.choice(['spread', 'scatter', 'laser', 'escort'])

        # mode 从 powerup_type 派生，weapon类型时传给 gunsys.mode
        self.mode = type_to_mode[self.powerup_type]

        if not PowerUp._images:
            PowerUp._images = {
                'life':       pygame.transform.scale(pygame.image.load(resource_path('images/powerup_life.png')).convert_alpha(),      (125*1.0*0.8, 82*1.5*0.8)),
                'spread':     pygame.transform.scale(pygame.image.load(resource_path('images/powerup_spread.png')).convert_alpha(),    (125*1.1*0.8, 82*1.5*0.8)),
                'scatter':    pygame.transform.scale(pygame.image.load(resource_path('images/powerup_scatter.png')).convert_alpha(),   (125*1.4*0.8, 82*1.5*0.8)),
                'laser':      pygame.transform.scale(pygame.image.load(resource_path('images/powerup_laser.png')).convert_alpha(),     (125*1.6*0.8, 82*1.5*0.8)),
                'invincible': pygame.transform.scale(pygame.image.load(resource_path('images/powerup_invincible.png')).convert_alpha(),(125*1.6*0.6, 82*1.5*0.8)),
                'kill_all':   pygame.transform.scale(pygame.image.load(resource_path('images/powerup_kill_all.png')).convert_alpha(),  (125*1.6*0.6, 82*1.5*0.8)),
                'ammo':       pygame.transform.scale(pygame.image.load(resource_path('images/powerup_ammo.png')).convert_alpha(),      (125*1.6*0.6, 82*1.5*0.9)),
                'escort':     pygame.transform.scale(pygame.image.load(resource_path('images/powerup_escort.png')).convert_alpha(),      (125*1.6*0.6, 82*1.5*0.9)),

            }

        # 图片也从 powerup_type 派生，不再用数字 key
        self.image = PowerUp._images[self.powerup_type]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = float(self.rect.x)
        self.y = self.rect.y

        self.buff = 1
        self.powerup_duration = 1300
        self.weapon_duration = 720
        self._bullet_count()

        self.visible = True
    def _bullet_count(self):
        if self.mode == 3:
            self.bullet_count = 3
            return
        
        self.bullet_count = 10
        
    def update(self):
        if any(isinstance(alien, AlienAi) for alien in self.ai_game.aliens.sprites()):
            return
        self.x += self.settings.alien_speed * self.settings.fleet_direction     
        self.rect.x = self.x    

    def drop(self):
        self.y += self.settings.fleet_drop_speed
        self.rect.y =self.y

    def timer(self):        
        self.powerup_duration -= 1
        if self.powerup_duration <= 180:
            self.visible = self.powerup_duration % 20 < 10          #一个bool的定义。 条件是余数<10

        return self.powerup_duration <= 0           #返回是bool值

    def blitme(self):
        if self.visible:            #因为该class每次被调用都是全新创建。（主程序init = None）所以，self.visible每次都是True
                                    #bool适合这种闪烁。
            self.screen.blit(self.image, self.rect)

