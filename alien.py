#因为alien在主程序里被初始化为self.aliens = pygame.sprite.Group()
#Alien 自己的方法（check_edges, explode）→ 必须先取出实例（for循环就是）后alien.check_edges()
# 或self.aliens.sprites()[0].check_edges 
#
#
import pygame
from pygame.sprite import Sprite
from timer import timer

from resource_manager import resource_path

class Alien(Sprite):

    '''A class to represent a single alien in the fleet'''

    _image_idle = None
    _image_explode = None
    # @timer
    def __init__(self, ai_game):

        '''Initialize the alien and set its starting position.'''
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        #Load the alien image and set its rect attribute.
        if Alien._image_idle is None:
            target_width = self.settings.screen_width // 12
            target_height = int(target_width * 200 / 220)
            Alien._image_idle = pygame.transform.scale(
                pygame.image.load(resource_path('images/alien.png')).convert_alpha(), (target_width, target_height))
            Alien._image_explode = pygame.transform.scale(
                pygame.image.load(resource_path('images/alien_explode.png')).convert_alpha(), (target_width, target_height))

        self.image_idle = Alien._image_idle
        self.image_explode = Alien._image_explode
        self.image = self.image_idle
        self.rect = self.image.get_rect()

        #Start each new alien near the top left of the screen.
        self.rect.x = self.rect.width       #self.rect.x = 0 或 self.rect.topleft = (0, 0)
        self.rect.y = self.rect.height

        #Store the alien's exact horizontal position.
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.explode_timer = 0
        self.explode_duration = 12
        
    
    def check_edges(self):
        '''Return True if alien is at edge of screen.'''
        screen_rect = self.screen.get_rect()
        return (self.rect.right >= screen_rect.right) or (self.rect.left <= 0)


    def update(self):
        '''Move the alien to the right or left'''
        if self.explode_timer > 0:
            self.explode_timer -= 1
            if self.explode_timer == 0:
                self.kill()         #kill() Sprite自带,将sprite从Group消除
            return    #到此终止函数的。但凡被kill()都不会继续下面

        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.rect.x = self.x            #self.rect.x只能是int, 所以先用self.x做运算，然后将结果给rect.x取整数。

    def explode(self):
        self.image = self.image_explode
        self.explode_timer = self.explode_duration


#