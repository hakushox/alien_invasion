#
#
#

import pygame
from pygame.sprite import Sprite
from timer import timer
from resource_manager import resource_path

class Ship(Sprite):
    '''A class to manage the ship.'''
    
    # @timer
    def __init__(self, ai_game):
        '''Initialize the ship and set its starting position.'''
        super().__init__()
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = ai_game.screen.get_rect()
        self.settings = ai_game.settings

        target_width = self.settings.screen_width // 11
        target_height = int(target_width * (82*2) / (125*2))


        #Load the ship image and get its rect.
        self.ship_images = {
                    'ship_idle': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship.png')).convert_alpha(), (target_width, target_height)),
                    'ship_spread': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship_spread.png')).convert_alpha(),  (target_width, target_height)),
                    'ship_scatter': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship_scatter.png')).convert_alpha(),  (target_width, target_height)),
                    'ship_laser': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship_laser.png')).convert_alpha(),  (target_width, target_height)),
                    'ship_angery': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship_angery.png')).convert_alpha(),  (target_width, target_height)),
                    'ship_laugh': pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship_laugh.png')).convert_alpha(),  (target_width, target_height)),
                }   
        self.ship_index = 'ship_idle'
        self.image = self.ship_images[self.ship_index]

        self.rect = self.image.get_rect()           #一个函数的返回值是某个类的对象，你就可以直接对它调用那个类的方法，不需要自己手动实例化。

        #Start each new ship at the bottom center of the screen
        # self.rect.midbottom = self.screen_rect.midbottom
        self.rect.midbottom = (self.screen_rect.midbottom[0], self.screen_rect.midbottom[1]- 100)
        #Store a float for the ship's exact horizontal position.
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        #Movement flag;start with a ship that's not moving.
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

        self.fire_timer = 0
        self.fire_duration = 30

        self.invinci_timer = 0
        self.invinci_duration = 120
        self.visible = True

        self.frames = [
            pygame.transform.scale(
                pygame.image.load(
                    resource_path(f'images/ship/move/ship_laser/ship_laser_0000{i}.png')).convert_alpha(), 
                (125*2, 82*2))   for i in range(4)                                                                              
        ]
        self.frames_index = 0
        self.frames_timer = 0
        self.frames_speed = 3
        self.frames_playing = False
        self.frames_forward = True
        self.frames_done = False


    def update(self):
        '''Update the ship's position based on the movement flag.'''
        #Upadate the ship's x value, not the rect
        if self.moving_right and self.rect.centerx < self.screen_rect.right:      #这段两个条件要看清楚。
            self.x += self.settings.ship_speed
        if self.moving_left and self.rect.centerx > 0:
            self.x -= self.settings.ship_speed
        if self.moving_up and self.rect.centery > 0:
            self.y -= self.settings.ship_speed
        if self.moving_down and self.rect.centery < self.screen_rect.bottom:
            self.y +=   self.settings.ship_speed
        if self.moving_down or self.moving_left or self.moving_right or self.moving_up:
            if not self.settings.ship_flying_sound_channel.get_busy():
                self.settings.ship_flying_sound_channel.play(self.settings.ship_flying_sound)
        else:
            self.settings.ship_flying_sound_channel.stop()

        #Update rect object from self.x
        self.rect.x = self.x
        self.rect.y = self.y

        if self.fire_timer > 0:
            self.fire_timer -= 1

        if self.ai_game.gunsys.mode == 3 and not self.frames_playing \
            and not self.frames_done:
            self.frames_playing = True
            self.frames_index = 0
            self.frames_forward = True
        
        if self.frames_playing:
            self.frames_timer += 1
            if self.frames_timer >= self.frames_speed:
                self.frames_timer = 0
                if self.frames_forward:
                    self.frames_index += 1
                    if self.frames_index >= len(self.frames):
                        self.frames_index = len(self.frames) - 1
                        self.frames_forward = False
                else:
                    self.frames_index -= 1
                    if self.frames_index <= 0:
                        self.frames_index = 0
                        if self.ai_game.gunsys.invincible_timer > 0:
                            self.frames_playing = True
                            self.frames_forward = True
                        else:
                            self.frames_playing = False
                            self.frames_done = True

    def _play_frames(self):
        if not self.frames_playing:
            return
        self.frames_timer += 1
        if self.frames_timer < self.frames_speed:
            return
        
        self.frames_timer = 0
        self.frames_index += 1 if self.frames_forward else -1
        last = len(self.frames) - 1
        if self.frames_index > last:
            self.frames_index = last
            self.frames_forward = False
        if self.frames_index < 0:
            self.frames_index = 0
            self.frames_playing = False
     

    def center_ship(self):
        '''Center the ship on the screen.'''
        self.rect.midbottom = (self.screen_rect.midbottom[0], self.screen_rect.midbottom[1] -100)
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def invincible_timer(self):
        if self.invinci_timer > 0:
            self.invinci_timer -= 1
            self.visible = self.invinci_timer % 10 < 5
        else:
            self.visible = True
        return self.invinci_timer <= 0                   

    def blitme(self):
        '''Draw the ship at its current location.'''
        if self.visible:   
            mode_to_image = {
                            0: 'ship_idle',
                            1: 'ship_spread',
                            2: 'ship_scatter',
                            3: 'ship_laser',
                            
             }

            if self.frames_playing:
                self.screen.blit(self.frames[self.frames_index], self.rect) 
            else:
                ship_index = mode_to_image.get(self.ai_game.gunsys.mode, 'ship_idle') 
                self.image = self.ship_images[ship_index]
                self.screen.blit(self.image, self.rect)
            if self.invinci_timer > 0:
                self.image = self.ship_images['ship_angery']
                self.screen.blit(self.image, self.rect)
            if self.fire_timer > 0:
                self.image = self.ship_images['ship_laugh']
                self.screen.blit(self.image, self.rect)
