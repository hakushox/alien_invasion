#
#
#
import math
import pygame
from pygame.sprite import Sprite
from timer import timer
from resource_manager import resource_path

class Bullet(Sprite):
    '''Create a bullet object at the ship's current position'''
    _laser_frames = None
    # @timer
    def __init__(self, ai_game, owner=None,laser=False):
        super().__init__()
        from escort import Escort
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = self.settings.bullet_color if owner and not isinstance(owner, Escort) else (255, 255, 255)         #都去Setting里调， 达成一个地方控制全局
        self.owner = owner

        #Create a bullet rect at (0, 0) and then set the correct position.
        self.rect = pygame.Rect(0, 0, self.settings.bullet_width, 
                                self.settings.bullet_height)
        self.rect.midtop = owner.rect.center if owner else ai_game.ship.rect.center    #center是元组。(ai_game.ship.rect.centerx, ai_game.ship.rect.centery - 50)

        self.image = pygame.Surface((self.settings.bullet_width, self.settings.bullet_height))
        self.image.fill(self.color)
        self.mask = pygame.mask.from_surface(self.image)
        self.original_image = self.image.copy()

        #Store the bullet's position as a float.
        self.y = float(self.rect.y)
        self.x = float(self.rect.x)
        self.speed = 8 if owner else self.settings.bullet_speed    #init有的，任何方法里用到 self.xxx，Python 就会去找这个属性，找不到就报 AttributeError。
        self.angle = 0              #十分关键，直接决定cos() 是垂直的 sin()是0
        
        self.laser = laser
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_speed = 3
        if self.laser:
            if Bullet._laser_frames is None:
                frames = []
                for i in range(1, 7):
                    img = pygame.image.load(resource_path(f'images/laser/Comp 1_0000{i}.png')).convert_alpha()
                    frames.append(img)  # 原始尺寸存起来，不预先缩放
                Bullet._laser_frames = frames
            
            self.x = float(owner.rect.centerx if owner else ai_game.ship.rect.centerx)
            self.y = float(owner.rect.centery if owner else ai_game.ship.rect.centery)
            self.laser_h = int(self.y)  # ship到屏幕顶部的距离

            raw = Bullet._laser_frames[0]
            orig_w, orig_h = raw.get_size()
            new_w = int(orig_w * 0.5)
            self.image = pygame.transform.scale(raw, (new_w, orig_h))
            self.rect = self.image.get_rect()
            self.rect.midbottom = (int(self.x), int(self.y))
            self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if self.laser:
            self.frame_timer += 1
            if self.frame_timer >= self.frame_speed:
                self.frame_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(Bullet._laser_frames):
                    self.kill()
                    return
                raw = Bullet._laser_frames[self.frame_index]
                orig_w, orig_h = raw.get_size()
                new_w = int(orig_w * 0.3)
                self.image = pygame.transform.scale(raw, (new_w, orig_h))
                self.rect = self.image.get_rect()
                self.rect.midbottom = (int(self.x), int(self.y))
                self.mask = pygame.mask.from_surface(self.image)
            return  # laser不需要移动逻辑，直接return
        self.y -= self.speed * math.cos(math.radians(self.angle))      #坐标系是从发射点开始的。
        self.x += self.speed * math.sin(math.radians(self.angle))
        #Update the rect position
        self.rect.y = self.y
        self.rect.x = self.x

        if self.angle != 0:
            self.image = pygame.transform.rotate(self.original_image, -self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)
            self.mask = pygame.mask.from_surface(self.image)


    def draw_bullet(self):
        '''Draw the bullet to the screen.'''
        self.screen.blit(self.image, self.rect)

