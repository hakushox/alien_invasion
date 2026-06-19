#
#
#
import pygame.font
from pygame.sprite import Group
from ship import Ship
from pygame.sprite import Sprite, Group
from timer import timer
from resource_manager import resource_path

class Scoreboard:
    '''A class to report scoring infomation.'''
    @timer
    def __init__(self, ai_game):
        '''Initialize scorekeeping attributes.'''
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats

        #Font settings for scoring information.
        self.text_color = (30, 30, 30) 
        self.font = pygame.font.SysFont(None, 88)
        self.font1 = pygame.font.SysFont(None, 48)

        self.mode_images = {
                            0: pygame.transform.scale(pygame.image.load(resource_path('images/ship/ship.png')), (50, 50)),
                            1: pygame.transform.scale(pygame.image.load(resource_path('images/powerup_spread.png')), (50, 50)),
                            2: pygame.transform.scale(pygame.image.load(resource_path('images/powerup_scatter.png')), (50, 50)),
                            3: pygame.transform.scale(pygame.image.load(resource_path('images/powerup_laser.png')), (50, 50)),
                        }   

        #Prepare the initial score image
        self.prep_score()
        self.prep_high_score()      #要初始时提及，因为主程序一开始就调用这数据。 'Scoreboard' object has no attribute 'last_score_image'.
        self.prep_level()
        self.prep_ships()
        self.prep_bullet_left()

    def prep_level(self):
        """Turn level into a rendered image"""
        level_str = f"Level: {self.stats.level}"
        self.level_image = self.font1.render(level_str, True, self.text_color,self.settings.bg_color)
        self.level_rect = self.level_image.get_rect()
        self.level_rect.centerx = self.screen_rect.centerx
        self.level_rect.top = self.high_score_rect.top

    def prep_bullet_left(self):
        self.icon = self.mode_images[self.ai_game.gunsys.mode] 
        self.icon_rect = self.icon.get_rect()
        bullet_count = 'Unlimited Ammo' if self.ai_game.gunsys.bullet_count == float('inf') else str(self.ai_game.gunsys.bullet_count)
        self.bullet_count_image = self.font1.render(bullet_count, True, self.text_color, self.settings.bg_color)
        self.bullet_count_image_rect = self.bullet_count_image.get_rect()
        self.bullet_count_image_rect.left = self.screen_rect.left + 150
        self.bullet_count_image_rect.bottom = self.screen_rect.bottom

        self.icon_rect.left = self.screen_rect.left + 100
        self.icon_rect.bottom = self.screen_rect.bottom - 20

    def prep_score(self):
        '''Turn the score into a rendered image.'''     
        round_score = round(self.stats.score, -1)  
        score_str = f'{round_score:,}'
        self.score_image = self.font.render(score_str, True, self.text_color, self.settings.bg_color)

        #Display the score at the top right of the screen.
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 50
        self.score_rect.top = 150

    def prep_high_score(self):

        high_score = f"Highest Points: {round(self.stats.high_score, -1):,}"
        self.high_score_image = self.font1.render(high_score, True, self.text_color, self.settings.bg_color)
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.right = self.screen_rect.right - 50
        self.high_score_rect.top = 50

    def check_high_score(self):
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()
    
    def prep_ships(self):
        if not hasattr(self, '_indicator_img'):
            self._indicator_img = pygame.transform.scale(
                pygame.image.load(resource_path('images/ship/ship_left_indictor.png')).convert_alpha(), 
                (125*4, 82*4))
        
        # 先算名字宽度
        name_width = 0
        if self.ai_game.shop.current_user:
            name_surf = self.font1.render(self.ai_game.shop.current_user, True, (55, 145, 0))
            name_width = name_surf.get_width()
            self.username_surf = name_surf  # 存起来给show_score用
        else:
            self.username_surf = None

        ship_start_x = name_width + 10  # 名字右边留10px间距
        
        self.ships = Group()
        for ship_number in range(self.stats.ships_left):
            ship = Sprite()
            ship.image = self._indicator_img
            ship.rect = ship.image.get_rect()
            ship.rect.x = ship_start_x + ship_number * 80
            ship.rect.y = -50
            self.ships.add(ship)
    def show_score(self):
        '''Display score on screen.'''
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
        self.screen.blit(self.level_image, self.level_rect)
        self.screen.blit(self.bullet_count_image, self.bullet_count_image_rect)
        self.screen.blit(self.icon, self.icon_rect)
        self.ships.draw(self.screen)
        if self.ai_game.shop.current_user:
            name = self.font1.render(f'Player: {self.ai_game.shop.current_user}', True, (255, 215, 0))
            self.screen.blit(name, name.get_rect(midleft=(10, -80 + self._indicator_img.get_height() // 2)))