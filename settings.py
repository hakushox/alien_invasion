#
#
#
import pygame
from timer import timer
from resource_manager import resource_path
import math


class Settings:
    '''A class to store all settings for Alien Invasion.'''
    @timer
    def __init__(self):
        '''Initialize the game's settings.'''
        #Screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (230, 230, 230)

        #Ship setting        
        self.ship_limit = 3

        #Bullet settings
        
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)

        self.angle = 15

        #Alien settings
        self.fleet_drop_speed = 20
        
        self.powerup_odds = 0.25
        self.life_powerup_odds = 0.1
        #fleet_direction of 1 represents right; -1 represents left.
        
        
        #How quickly the game speed up
        self.speedup_scale = 1.1
        self.score_scale = 1.5

        self.initialize_dynamic_settings()
        #Scoring settings.
        self.alien_points = 50

        self.fire_sound = pygame.mixer.Sound(resource_path('sounds/fire.mp3'))
        self.spread_shot_sound = pygame.mixer.Sound(resource_path('sounds/spread_shot.wav'))
        self.scatter_shot_sound =pygame.mixer.Sound(resource_path('sounds/bubble_shot.mp3'))
        self.laser_shot = pygame.mixer.Sound(resource_path('sounds/laser_shot_03.mp3'))
        self.shot_channel = pygame.mixer.Channel(1)
        self.fire_sound.set_volume(.4)

        self.explode_sound = pygame.mixer.Sound(resource_path('sounds/meow.mp3'))
        self.explode_sound_channel = pygame.mixer.Channel(2)
        self.explode_sound.set_volume(.6)
        self.button_hovered = pygame.mixer.Sound(resource_path('sounds/button.wav'))
        self.button_pressed = pygame.mixer.Sound(resource_path('sounds/cat_hiss.mp3') )
        self.ship_hit_sound = pygame.mixer.Sound(resource_path('sounds/ouch.mp3'))      
        self.powerup_sound = pygame.mixer.Sound(resource_path('sounds/powerup.wav'))
        self.powerup_life_sound = pygame.mixer.Sound(resource_path('sounds/get_a_life.mp3'))   
        self.powerup_sound.set_volume(0.3)

        self.cat_charge_sound = pygame.mixer.Sound(resource_path('sounds/boss_charge.mp3'))
        self.cat_charge_sound.set_volume(0.5)
        self.laser_shot1_sound = pygame.mixer.Sound(resource_path('sounds/laser_shot_01.mp3'))
        self.laser_shot2_sound = pygame.mixer.Sound(resource_path('sounds/laser_shot_02.mp3'))
        self.boss_laser_sound_channel = pygame.mixer.Channel(3)

        self.ship_flying_sound = pygame.mixer.Sound(resource_path('sounds/flying.mp3'))
        self.ship_flying_sound_channel = pygame.mixer.Channel(0)

        self.boss_defeated = pygame.mixer.Sound(resource_path('sounds/boss_defeat.mp3'))
        self.ship_defeated = pygame.mixer.Sound(resource_path('sounds/ship_defeated.mp3'))
        self.welcome = pygame.mixer.Sound(resource_path('sounds/welcome.mp3'))
        self.error = pygame.mixer.Sound(resource_path('sounds/error.mp3'))
        self.type_correct = pygame.mixer.Sound(resource_path('sounds/type_correct.wav'))

        self.boss_appear = pygame.mixer.Sound(resource_path('sounds/boss_appear.mp3'))
        self.boss_fury = pygame.mixer.Sound(resource_path('sounds/boss_fury.mp3'))
        self.boss_hiss = pygame.mixer.Sound(resource_path('sounds/boss_hiss.mp3'))
        self.boss_stagger = pygame.mixer.Sound(resource_path('sounds/boss_stagger.mp3'))
        self.boss_charge = pygame.mixer.Sound(resource_path('sounds/boss_charge.mp3'))
        self.boss_channel = pygame.mixer.Channel(6)

        self.button_click = pygame.mixer.Sound(resource_path('sounds/button_click.mp3'))
        self.enter_shop = pygame.mixer.Sound(resource_path('sounds/enter_shop.mp3'))
        self.cha_ching = pygame.mixer.Sound(resource_path('sounds/cha_ching.mp3'))
        self.error = pygame.mixer.Sound(resource_path('sounds/error.mp3'))
        self.kill_all = pygame.mixer.Sound(resource_path('sounds/kill_all.mp3'))
        self.powerup_ammo = pygame.mixer.Sound(resource_path('sounds/powerup_ammo.mp3'))
        self.powerup_invin = pygame.mixer.Sound(resource_path('sounds/powerup_invin.mp3'))
        self.powerup_escort = pygame.mixer.Sound(resource_path('sounds/powerup_escort.wav'))
        self.powerup_sound_channel = pygame.mixer.Channel(4)
        self.powerup_sound_channel2 = pygame.mixer.Channel(5)
        self.escort_shotl = pygame.mixer.Sound(resource_path('sounds/escort_shotl.wav'))
        self.escort_shot = pygame.mixer.Sound(resource_path('sounds/escort_shot.wav'))
        self.escort_appear = pygame.mixer.Sound(resource_path('sounds/escort_appear.wav'))
        self.escort_hit = pygame.mixer.Sound(resource_path('sounds/escort_hit.wav'))
        self.escort_channel = pygame.mixer.Channel(7)




        pygame.mixer.music.load(resource_path('sounds/bg.wav'))
        self.current_music = None

    def initialize_dynamic_settings(self):
        '''Initialize settings that change throughout the game.'''
        self.ship_speed = 5.5
        self.bullet_speed = 10.0
        self.alien_speed = 2.0
        self.boss_speed = 6
        self.bullet_allowed = 3
        self.bullet_rows = 1

        #fleet_direction of 1 represents right; -1 represents left.
        self.fleet_direction = 1
    
    def increase_speed(self,level):
        '''Increase speed settings.'''
        if level % 5 == 0:
            pygame.mixer.music.load(resource_path('sounds/boss_fight.mp3'))
            pygame.mixer.music.play(-1)
            self.current_music = 'boss_fight.mp3'
        elif level % 5 != 0 and self.current_music != 'bg.wav':
            pygame.mixer.music.load(resource_path('sounds/bg.wav'))
            pygame.mixer.music.play(-1)
            self.current_music = 'bg.wav'
             
        if level % 4 == 0:
            self.ship_speed = min(self.ship_speed *self.speedup_scale, 20)
            self.bullet_speed = min(self.bullet_speed * self.speedup_scale, 30)
            self.alien_speed = min(self.alien_speed * self.speedup_scale, 10)
            self.alien_points = int(self.alien_points * math.sqrt(level))        
            self.bullet_rows = min(self.bullet_rows + 1, 3)       
            self.bullet_allowed += self.bullet_rows
        self.boss_speed = min(self.boss_speed + 0.2, 12) 





