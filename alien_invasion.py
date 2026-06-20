#__init__创建实例时执行一次, 把这个对象需要的东西准备好，挂在 self 上，让其他方法后面能用
#真正能动起来的是 method
#
# 判断要不要独立成class: 1，这个东西将来会不会被多种不同的"对象"使用，或者会不会独立变化
#                       2，这个东西有自己的属性（数据），也有自己的行为（函数）
# eg.飞船——有位置、速度（属性），能移动、能射击（行为）;用户——有用户名、密码（属性），能登录、能注销（行为）;银行账户——有余额（属性），能存款、取款（行为）
#
##内部init定义里的值是起点，且不希望被外部改。


import sys

import pygame
from time import sleep
import random
import math

from settings import Settings
from game_stats import GameStats
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from scoreboard import Scoreboard
from gunsystem import GunSystem
from powerup import PowerUp
from fleetmanager import FleetManager
from alien_ai import AlienAi
from boss import Boss
from shop import Shop
from inventory import Inventory
from escort import Escort

from timer import timer
from resource_manager import resource_path
from account import add_points, load_account

class AlienInvasion:
    '''Overall class to manange game assets and behavior'''
    def __init__(self):     #初始化模块，无arg参要求。 内部所有都被调用时运行一次。
        '''Initialize the game, and create game resources.'''
        pygame.init()       
        self.clock = pygame.time.Clock()
        self.settings = Settings()
                        
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_height = self.screen.get_rect().height
        self.settings.screen_width = self.screen.get_rect().width
        # self.screen = pygame.display.set_mode(
        #     (self.settings.screen_width, self.settings.screen_height)
        # )                                                                 
         
        pygame.display.set_caption("Alien Invasion")

        #Create an instance to store game statistics.
        self.stats = GameStats(self)


        self.ship = Ship(self)          #确定一开始就有 → 直接创建实例
        
        self.bullets = pygame.sprite.Group()            #数量不定、动态生成 → 先准备容器，用的时候再往里加
        self.aliens = pygame.sprite.Group()             #只是创建一个空容器 （list）,后面往里面加，详见new系列-add
        self.boss_group = pygame.sprite.Group()
        self.boss = None
        self.fleet_manager = FleetManager(self)
        self.gunsys = GunSystem(self)
        self.powerups = pygame.sprite.Group()        #先设置空值，否则updatescreen会AttributeError
        self.fleet_manager.create_fleet(self.stats.level)

        #Start Alien Invasion in an active state.
        self.game_active = False

        #Make the Play button.
        self.play_button = Button(self, 'Play')
        self.button_hovered = False
        #boss子弹袋子
        self.boss_bullets = pygame.sprite.Group()
        #test
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 1000  

        self.demo_timer = 60 * 60
        self.show_instructions = True

        self.instruction_icons = [
            (pygame.image.load(resource_path('images/powerup_spread.png')).convert_alpha(),  'Spread Shot  - 10 rounds'),
            (pygame.image.load(resource_path('images/powerup_scatter.png')).convert_alpha(), 'Scatter Shot - 10 rounds'),
            (pygame.image.load(resource_path('images/powerup_laser.png')).convert_alpha(),   'Laser        -  3 rounds'),
        ]

        self.game_started = False
        self.shop = Shop(self)
        self.inventory = Inventory(self)
        
        self.sb = Scoreboard(self)
        # self.menu_bg = pygame.image.load(resource_path('images/menu_bg.png')).convert()
        self.menu_frames = [            
                pygame.image.load(
                    resource_path(f'images/menu/menu_bg{i+1}.png')).convert_alpha() 
                    for i in range(11)                                                                              
        ]
        self.menu_frames_speed = 5
        self.menu_frames_playing1 = False
        self.menu_frames_playing2 = False
        self.menu_frames_timer = 0
        self.menu_frames_index = 0
        self.menu_frames_done = False
        self.menu_frames_forward = True
        self.menu_frames_activate = 0
        self.playing_round = 0
                                                        
        img_w, img_h = self.menu_frames[0].get_size()
        sw = self.settings.screen_width
        sh = self.settings.screen_height
        scale = max(sw / img_w, sh / img_h)  # 取较大的缩放比，确保覆盖全屏
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
         # 居中裁剪
        x = (new_w - sw) // 2
        y = (new_h - sh) // 2
        for i in range(len(self.menu_frames)):
            scaled = pygame.transform.scale(self.menu_frames[i], (new_w, new_h))       
            self.menu_frames[i] = scaled.subsurface(pygame.Rect(x, y, sw, sh)).copy()

        
        self.menu_bg = random.choice([
                                pygame.image.load(resource_path(f'images/menu/menu_shop{i+1}.png')).convert_alpha() 
                                for i in range(3)
                                ])
        bg_w, bg_h = self.menu_bg.get_size()
        bg_scale = max(sw / bg_w, sh / bg_h)
        bg_new_w = int(bg_w * bg_scale)
        bg_new_h = int(bg_h * bg_scale)
        bg_x = (bg_new_w - sw) // 2
        bg_y = (bg_new_h - sh) // 2
        scaled = pygame.transform.scale(self.menu_bg, (bg_new_w, bg_new_h))
        self.menu_bg = scaled.subsurface(pygame.Rect(bg_x, bg_y, sw, sh)).copy()        

        self.instruction_bgs = {
                            'arrow': pygame.image.load(resource_path('images/ui/arrow.png')).convert_alpha(),
                            'space': pygame.image.load(resource_path('images/ui/space.png')).convert_alpha(),
                            'esc':   pygame.image.load(resource_path('images/ui/esc.png')).convert_alpha(),
                            'enter': pygame.image.load(resource_path('images/ui/enter.png')).convert_alpha(),
                            'num':   pygame.image.load(resource_path('images/ui/num.png')).convert_alpha(),
                        }
        self.btn_images = {
                        'play':  pygame.image.load(resource_path('images/ui//button1.png')).convert_alpha(),
                        'login': pygame.image.load(resource_path('images/ui//button1.png')).convert_alpha(),
                        'shop':  pygame.image.load(resource_path('images/ui//button1.png')).convert_alpha(),
                    }
        title_image = pygame.image.load(resource_path(f'images/ui/title.png')).convert_alpha()
        title_w, title_h = title_image.get_size()
        self.scaled_title = pygame.transform.rotate(pygame.transform.scale(title_image, (title_w // 2.8, title_h // 2.8)), 25)
                                              
        pygame.mixer.set_num_channels(8) 
        self.confirm_exit = False
        self.pause_game = False

        self.show_ranking = False
        self.last_logout_click = 0
        self.show_howtoplay = False

        self.escorts = []
        self.escort_count = 0
        self.escort_bullets = pygame.sprite.Group()
        self.shockwave = None

           
    def run_game(self):
        '''Start the main loop for the game'''
               
        pygame.mixer.music.load(resource_path('sounds/intro.mp3'))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
        self.settings.current_music = 'intro.mp3'
        while True:
            self._check_events()
            
            if self.game_active and not self.pause_game:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()  
                self.ship.invincible_timer()
                self._check_powerup_collisions()
                for escort in self.escorts:
                    escort.update()
                #test
                self.powerup_spawn_timer +=1
                if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                    self.powerup_spawn_timer = 0
                    for _ in range(1):
                        self.powerups.add(PowerUp(self, random.randint(100, self.settings.screen_width),
                                              random.randint(100, self.settings.screen_height - 200)))
                if self.powerups: 
                    for p in self.powerups.copy():                    
                        p.update()  
                        if p.timer():
                            self.powerups.remove(p)
                if self.gunsys.get_timer() or self.gunsys.laser_exhausted:
                    laser_alive = any(getattr(b, 'laser', False) for b in self.bullets) or\
                                    any(getattr(b, 'laser', False) for b in self.escort_bullets)
                    if not laser_alive:
                        self.gunsys.mode = 0
                        self.gunsys.laser_exhausted = False
                        self.ship.frames_done = False
                        self.gunsys.buff = 1
                        self.sb.prep_bullet_left()
                        self.gunsys.bullet_count = 0
                        for e in self.escorts:
                            if e.stage == 'large':
                                e.gunsys.mode = 0
                                e.gunsys.laser_exhausted = False
                                e.gunsys.bullet_count = 0

            else:
                self.demo_timer -= 1
                if self.show_instructions:
                    if self.demo_timer <= 0:
                        self.demo_timer = 60 * 15
                        self.show_instructions = False

                if not self.show_instructions:                    
                    self._demo_update()
                    if self.demo_timer <= 0:
                        self.show_instructions = True
                        self.demo_timer = 60 * 60
                     
            self._update_screen()           #尽管在if外，每帧也都会运行。

            self.clock.tick(60)

    def _check_play_button(self, mouse_pos):
        '''When click Play.'''
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            #Reset the game statistics.
            self.ship.moving_right = False
            self.ship.moving_left = False
            self.ship.moving_up = False
            self.ship.moving_down = False
            # for _ in range(5):
            #             self.powerups.add(PowerUp(self, random.randint(100, self.settings.screen_width),
            #                                   random.randint(100, self.settings.screen_height - 200)))
            self.stats.reset_stats()
            self.sb.check_high_score()
            self.sb.prep_score()
            self.game_active = True
            #Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()
            self.boss_group.empty()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.gunsys.mode = 0
            self.settings.bullet_rows = 1
            self.sb.prep_bullet_left()

            self.settings.button_pressed.play()
            #Reset the game settings.
            self.settings.initialize_dynamic_settings()
            pygame.mixer.music.load(resource_path('sounds/bg.wav'))
            pygame.mixer.music.play(-1)
            self.settings.current_music = 'bg.wav'
            #Create a new fleet and center the ship
            self.fleet_manager.create_fleet(self.stats.level)
            self.ship.center_ship()
            self.inventory.refresh()
        
            #Hide the mouse cursor
            pygame.mouse.set_visible(False)

    def _check_events(self):
        '''Respond to key presses and mouse events'''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)  

                if not self.game_active and not self.game_started:
                    if not self.show_instructions:
                        self.show_instructions = True
                    self.demo_timer = 60 * 60              
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
                        
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                hovered = (self.play_button.rect.collidepoint(mouse_pos) or \
                    (hasattr(self, 'shop_button_rect')) and self.shop_button_rect.collidepoint(mouse_pos) or\
                    (hasattr(self, 'login_button_rect')) and self.login_button_rect.collidepoint(mouse_pos) or\
                    (hasattr(self, 'rank_button_rect') and self.rank_button_rect.collidepoint(mouse_pos)) or\
                    (hasattr(self, 'howtoplay_button_rect')) and self.howtoplay_button_rect.collidepoint(mouse_pos))
                if hovered and not self.button_hovered:
                    self.settings.button_hovered.play() 
                    self.button_hovered = True
                elif not hovered:
                    self.button_hovered = False

                if not self.game_active and not self.game_started:
                    if not self.show_instructions:
                        self.show_instructions = True
                    self.demo_timer = 60 * 60             
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.confirm_exit:
                    if self.confirm_yes_rect.collidepoint(mouse_pos):
                        sys.exit()
                    elif self.confirm_no_rect.collidepoint(mouse_pos):
                        self.confirm_exit = False
                        self.pause_game = False
                        if self.game_active:
                            pygame.mouse.set_visible(False)
                            self._still_ship()
            
                self._check_play_button(mouse_pos)
                if not self.game_active and not self.game_started:
                    if hasattr(self, 'shop_button_rect'):
                        if self.shop_button_rect.collidepoint(mouse_pos):
                           self.shop.run()
                    if hasattr(self, 'login_button_rect'):
                        if self.login_button_rect.collidepoint(mouse_pos):
                            if not self.shop.current_user:
                                self.shop._login()
                            else:
                                now = pygame.time.get_ticks()
                                if now - self.last_logout_click < 400:
                                    self.last_logout_click = 0
                                    self.shop.current_user = None
                                else:
                                    self.last_logout_click = now

                    if self.rank_button_rect.collidepoint(mouse_pos):
                        self.show_ranking = True
                    if hasattr(self, 'ranking_close_rect') and self.ranking_close_rect.collidepoint(mouse_pos):
                        self.show_ranking = False
                    if hasattr(self, 'howtoplay_button_rect') and self.howtoplay_button_rect.collidepoint(mouse_pos):
                        self.show_howtoplay = True
                    if hasattr(self, 'howtoplay_close_rect') and self.howtoplay_close_rect.collidepoint(mouse_pos):
                        self.show_howtoplay = False
                            
    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            #Move the ship to the right
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
            for e in self.escorts:
                e.shoot_laser()
                
        elif event.key == pygame.K_ESCAPE:
            pygame.mouse.set_visible(True)
            self.pause_game = True
            self.confirm_exit = True
        if not self.game_active:
            return
        if  event.key in (pygame.K_1, pygame.K_2, pygame.K_3, 
            pygame.K_4, pygame.K_5, pygame.K_6):
            index = event.key - pygame.K_1
            self.inventory.use_item(index)
    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _fire_bullet(self):
        '''Create a new bullet and add it to the bullets group.'''
        if self.gunsys.mode in (1, 2):
            can_fire = True
        else:
            can_fire = len(self.bullets) < self.gunsys.get_bullets_limit()        
        if can_fire:
            self.gunsys.modes[self.gunsys.mode]()      
            self.sb.prep_bullet_left()
            self.ship.fire_timer = self.ship.fire_duration
                
    def _update_bullets(self):
        self.escort_bullets.update()
        self.bullets.update()
          #Get rid of bullets that have disappeared
        for bullet in self.bullets.copy():              #一边遍历列表，一边修改同一个列表,会出 bug —— 某些元素可能被跳过。所以用copy()
            if bullet.rect.bottom < 0  or bullet.rect.left > self.settings.screen_width \
            or bullet.rect.right < 0:
                self.bullets.remove(bullet)
        for bullet in self.escort_bullets.copy():
             if bullet.rect.bottom < 0  or bullet.rect.left > self.settings.screen_width \
            or bullet.rect.right < 0:
                self.escort_bullets.remove(bullet)

        # print(len(self.bullets))
        self.boss_bullets.update()
        for bullet in self.boss_bullets.copy():
            if bullet.rect.top > self.settings.screen_height  or bullet.rect.left > self.settings.screen_width \
            or bullet.rect.right < 0:
                self.boss_bullets.remove(bullet)
        self._check_bullet_alien_collisions()
        

    def _check_bullet_alien_collisions(self):
        #Check for any bullets that have hit aliens.
        #if so, get rid of the bullet and the alien.
        all_bullets = pygame.sprite.Group(*self.bullets, *self.escort_bullets)   #组合list

        non_boss_aliens = pygame.sprite.Group(a for a in self.aliens if not isinstance(a, Boss))
        collisions = pygame.sprite.groupcollide(
                all_bullets, non_boss_aliens, self.gunsys.get_bullet_killable(), False,
            )           #其实是调用的Sprite内部kill()

        boss_collisions = pygame.sprite.groupcollide(
            all_bullets, self.boss_group, self.gunsys.get_bullet_killable(), False,
            pygame.sprite.collide_mask
        )
        if not hasattr(self, '_laser_hit_cooldown'):
            self._laser_hit_cooldown = {}
        for key in list(self._laser_hit_cooldown):
            self._laser_hit_cooldown[key] -= 1
            if self._laser_hit_cooldown[key] <= 0:
                del self._laser_hit_cooldown[key]
        already_exploded = set()

        if collisions:
            for bullet, aliens in collisions.items():
                if not getattr(bullet, 'laser', False):
                    bullet.kill()  # 非激光子弹才消除
                for alien in aliens:
                    if self.game_active:
                        self.stats.score += self.settings.alien_points
                    if isinstance(alien, Boss):
                        pass
                    elif not alien.explode_timer:
                        if hasattr(alien, 'hp'):
                            if getattr(bullet, 'laser', False):
                                
                                key = (alien, bullet)
                                if key in self._laser_hit_cooldown:
                                    continue
                                self._laser_hit_cooldown[key] = 22
                                if isinstance(bullet.owner, Ship):
                                    alien.hp -= 5 + self.stats.level // 4
                                elif isinstance(bullet.owner, Escort):
                                    alien.hp -= (5 + self.stats.level // 4) // 2
                                else:
                                    alien.hp -= 1
                            else:
                                alien.hp -= 1
                            if alien.hp <= 0 and alien not in already_exploded:
                                already_exploded.add(alien)
                                alien.explode()
                                if random.random() < self.settings.powerup_odds:
                                    self.powerups.add(PowerUp(self, alien.rect.centerx, alien.rect.centery))
                        else:
                            if alien not in already_exploded:
                                already_exploded.add(alien)
                                alien.explode()
                                if random.random() < self.settings.powerup_odds:
                                    self.powerups.add(PowerUp(self, alien.rect.centerx, alien.rect.centery))

        if boss_collisions:
            hit_bosses = set()
            bullet_count = 0
            for bullet, aliens in boss_collisions.items():
                hit_bosses.update(aliens)
                bullet_count += 1
                if self.game_active:
                    bonus = 1 + math.log(bullet_count, 2) * 0.1
                    self.stats.score += int(self.settings.alien_points * len(hit_bosses) * bonus)
                for alien in aliens:                    
                    if getattr(bullet, 'laser', False):
                        key = (alien, bullet)
                        if key in self._laser_hit_cooldown:
                            continue   
                        self._laser_hit_cooldown[key] = 22
                        if isinstance(bullet.owner, Ship):
                            alien.hp -= 5 + self.stats.level // 3
                        elif isinstance(bullet.owner, Escort):
                            alien.hp -= (5 + self.stats.level // 3) // 2
                        else:
                            alien.hp -= 1
                        alien.recent_damage.append((alien.frame_count, 8 + self.stats.level // 5))
                    else:
                        alien.hp -= 1
                        alien.recent_damage.append((alien.frame_count, 1))
                    if alien.hp <= 0 and not alien.explode_timer:
                        alien.explode()
                        self.settings.boss_defeated.play()
                        for _ in range(random.randint(1, 3)):
                            p = PowerUp(self, alien.rect.centerx + random.randint(-200, 200),
                                                    alien.rect.centery + random.randint(-300, 300) )
                            self.powerups.add(p)
                              
        if collisions or boss_collisions:            
            self.settings.explode_sound_channel.play(self.settings.explode_sound)
            self.sb.prep_score()
            self.sb.check_high_score() 
        self._check_level_up()

    def _check_level_up(self):
        if not self.aliens:     #Group行为类似list. 空list就是False,
            #Destroy existing bullets and create new fleet.
            self.bullets.empty()

            self.stats.level += 1       #尽管stats的 初始块里没有level变量，但是，因rest_stats()在init里运行，所以被创建了。
            if self.stats.level % 5 == 0:
                pygame.mouse.set_visible(True)
                accounts = load_account()
                if self.shop.current_user:
                    add_points(self.shop.current_user, self.stats.score)
                    self.shop.points = accounts[self.shop.current_user]['points']
                else:
                    self.shop.points = self.stats.score
                self.shop.run()
                self._still_ship()
            pygame.mouse.set_visible(False)
            self.settings.increase_speed(self.stats.level)
            self.sb.prep_level()
            self.ship.center_ship()
            self.fleet_manager.create_fleet(self.stats.level)

            self.shockwave = None


    def _update_aliens(self):
        '''Update the position of all aliens in the fleet.'''
        #Check if the fleet is at an edge, then update postions.
        self._check_fleet_edges()
        self.aliens.update()            #调用的是 Group 的 .update()，而 Group 内部会遍历它所有的成员，逐个调用每个成员自己的 .update()。
        # print(alien.rect.x, alien.rect.y)
        #Look for alien-ship collisions

        ram_aliens = pygame.sprite.spritecollide(self.ship,
                        pygame.sprite.Group(a for a in self.aliens if not getattr(a, 'explode_timer', 0)),
                        False, pygame.sprite.collide_mask)
        if ram_aliens:
            if not hasattr(self, '_ram_cooldown'):
                self._ram_cooldown = {}
            for key in list(self._ram_cooldown):
                self._ram_cooldown[key] -= 1
                if self._ram_cooldown[key] <= 0:
                    del self._ram_cooldown[key]
            if self.gunsys.invincible_timer <= 0:
                if self.ship.invincible_timer():
                    time_to_remove = next((e for e in self.escorts if e.stage=='large'), None)
                    if time_to_remove:
                        self.settings.escort_channel.play(self.settings.escort_hit)
                        self.escorts.remove(time_to_remove)
                        self.escort_count = len(self.escorts)
                        self.ship.invinci_timer = 120
                        for alien in ram_aliens:
                            if hasattr(alien, 'hp'):
                                alien.hp -= 5 + self.stats.level // 5
                                if alien.hp <= 0 and not alien.explode_timer:
                                    alien.explode()
                            else:
                                alien.explode()
                        return
                    self._ship_hit()
                    self.escorts.clear()
                    self.escort_count = 0

            else:
                for alien in ram_aliens:
                    if isinstance(alien, Boss):
                        if alien in self._ram_cooldown:
                            continue
                        self._ram_cooldown[alien] = 60
                        alien.hp -= 8 + self.stats.level // 5
                        alien.recent_damage.append((alien.frame_count, 8 + self.stats.level // 5))
                        if alien.hp <= 0 and not alien.explode_timer:
                            alien.explode()
                            self.settings.boss_defeated.play()
                            for _ in range(random.randint(1, 3)):
                                p = PowerUp(self, alien.rect.centerx + random.randint(-200, 200),
                                                alien.rect.centery + random.randint(-300, 300))
                                self.powerups.add(p)
                    else:
                        alien.explode()
                        self.stats.score += self.settings.alien_points
                        if random.random() < self.settings.powerup_odds:
                            self.powerups.add(PowerUp(self, alien.rect.centerx, alien.rect.centery))
                if ram_aliens:
                    self.settings.explode_sound_channel.play(self.settings.explode_sound)
                    self.sb.prep_score()
                    self.sb.check_high_score()
                self._check_level_up()

        if pygame.sprite.spritecollideany(self.ship, self.boss_bullets, pygame.sprite.collide_mask):
            if self.gunsys.invincible_timer <= 0:
                if self.ship.invincible_timer():
                    time_to_remove = next((e for e in self.escorts if e.stage=='large'), None)
                    if time_to_remove:
                        self.escorts.remove(time_to_remove)
                        self.escort_count = len(self.escorts)
                        self.ship.invinci_timer = 60
                        pygame.sprite.spritecollide(self.ship, self.boss_bullets, True, pygame.sprite.collide_mask)

                        return
                    self._ship_hit()
                    self.escorts.clear()
                    self.escort_count = 0
            else:
                pygame.sprite.spritecollide(self.ship, self.boss_bullets, True, pygame.sprite.collide_mask)
                
        for boss in self.boss_group:
            if boss.laser.hit_ship:
                if self.ship.invincible_timer():
                    time_to_remove = next((e for e in self.escorts if e.stage=='large'), None)
                    if time_to_remove:
                        self.escorts.remove(time_to_remove)
                        self.escort_count = len(self.escorts)
                        self.ship.invinci_timer = 120

                        return
                    self._ship_hit()
                    self.escorts.clear()
                    self.escort_count = 0       
        if self.shockwave:
            self.shockwave.update()
        
        #Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()
        
    def _check_fleet_edges(self):
        '''Respond appropriately if any aliens have reached an edge.'''
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        '''Drop the entire fleet and change the fleet's direction.'''
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        if self.powerups:
            for p in self.powerups:
                p.drop()
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        '''Respond to the ship being hit by an alien.'''
        # print(f"_ship_hit called, ships_left: {self.stats.ships_left}, game_active: {self.game_active}")
        if self.stats.ships_left > 0:
            #decrement ships_left.
            self.stats.ships_left -= 1
            self.sb.prep_bullet_left()
            self.sb.prep_ships()
            self.gunsys.bullet_count = 0
            
            #Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            # self.aliens.empty()
            self.settings.ship_hit_sound.play()

            #Create a new fleet and center the ship
            # self.fleet_manager.create_fleet(self.stats.level)

            self.gunsys.mode = 0
            self.gunsys.buff = 0
            self.gunsys.bullet_count = 0    
            self.ship.invinci_timer = self.ship.invinci_duration 
            self._update_screen()           
            pygame.display.flip()  
            #Pause.
            sleep(0.5)
            self.ship.center_ship()

        else:
            if self.game_active:
                self.settings.ship_defeated.play()
                self.ship.invinci_timer = self.ship.invinci_duration
                self._update_screen()
                pygame.display.flip()  
            #Pause.
                sleep(1.5)
                pygame.mouse.set_visible(True)
                self._still_ship()
                self.shop.buy_result = None
                bought = self.shop.run(continue_only=True)
                if bought:
                    # self.stats.ships_left += 1
                    self.ship.center_ship()                    
                    self.sb.prep_ships()
                    self._still_ship()
                    self.gunsys.active_invincible(duration=300)
                    return  # 不进入game over
                self.game_active = False
                self.game_started = True
                
                self._game_over_loop()
            # print("game_active set to False")

    def _still_ship(self):
        self.ship.moving_right = False
        self.ship.moving_left = False
        self.ship.moving_up = False
        self.ship.moving_down = False

    def _check_aliens_bottom(self):

        '''Check if any aliens have reached the bottom of the screen.'''
        for alien in self.aliens.sprites():
            if isinstance(alien, AlienAi):
                continue            #跳出循环
                
            if alien.rect.bottom >= self.settings.screen_height:
                self._ship_hit()
                break
    
    def _check_powerup_collisions(self):
        # if self.powerups:   可删可留  空列表不占资源
        for p in self.powerups.copy():
            if self.ship.rect.colliderect(p.rect):
                self.powerups.remove(p)

                if p.powerup_type == 'life':
                    self.stats.ships_left += 1
                    self.sb.prep_ships()
                    if self.gunsys.timer > 0:
                        self.gunsys.total_duration += p.weapon_duration 
                        self.gunsys.timer += self.gunsys.total_duration
                    self.settings.powerup_life_sound.play()
                elif p.powerup_type == 'invincible':
                    self.gunsys.active_invincible(p.weapon_duration / 2)
                elif p.powerup_type == 'kill_all':
                    self.gunsys.activate_kill_all()
                elif p.powerup_type == 'ammo':
                    self.gunsys.activate_ammo(p.weapon_duration / 2)
                    for e in self.escorts:
                        e.multi_timer_active = True
                        e.multi_timer_ticks = p.weapon_duration
                        if e.stage == 'large':
                            e.gunsys.ammo_limitless = p.weapon_duration 
                            e.gunsys.ammo_total = p.weapon_duration 

                elif p.powerup_type == 'escort':
                    self._activate_escorts()
                    self.settings.powerup_escort.play()
                    self.settings.escort_channel.play(self.settings.escort_appear)
                elif p.powerup_type in ('spread', 'scatter', 'laser'): 
                    last_mode = self.gunsys.mode
                    self.gunsys.mode = p.mode
         
                    if last_mode == p.mode or last_mode == 0:
                        self.gunsys.buff += p.buff
                        self.gunsys.bullet_count += p.bullet_count
                        self.gunsys.total_duration += p.weapon_duration / 2
                        self.gunsys.timer = self.gunsys.total_duration
                        
                    else:
                        self.gunsys.total_duration = p.weapon_duration
                        self.gunsys.timer = self.gunsys.total_duration
                        self.gunsys.buff = p.buff
                        self.gunsys.bullet_count = p.bullet_count

                    for e in self.escorts:
                        if e.stage == 'large':
                            e.gunsys.mode = self.gunsys.mode
                            e.gunsys.timer = self.gunsys.timer
                            e.gunsys.total_duration = self.gunsys.total_duration
                            e.gunsys.bullet_count = self.gunsys.bullet_count
                            e.gunsys.buff = self.gunsys.buff
                            e.gunsys.laser_exhausted = self.gunsys.laser_exhausted

                    self.sb.prep_bullet_left()
                    self.settings.powerup_sound.play()
        
        for alien in self.aliens:
            if isinstance(alien, Boss) and not alien.explode_timer:   #计时时，false
                hit = pygame.sprite.spritecollideany(alien, self.powerups, pygame.sprite.collide_mask) #返回list里的第一个，这里是pwerups
                if hit:
                    if hit.powerup_type not in ['invincible', 'kill_all', 'ammo', 'escort']:
                        self.powerups.remove(hit)
                        alien.collect_powerup(hit)
                        self.settings.powerup_sound.play()

    def _activate_escorts(self, duration=60 * 60):
        self.escort_count = len(self.escorts)
        stages = [e.stage for e in self.escorts]
        sides = [e.side for e in self.escorts]
        large_side = next((e.side for e in self.escorts if e.stage == 'large'), None)

        # print("activate, count:", self.escort_count, "escorts:", [e.stage for e in self.escorts])
        if self.escort_count == 0:
            self.escorts.append(Escort(self, stage='normal', side='left'))
        elif self.escort_count == 1 and 'large' not in stages and 'right' not in sides:            
            self.escorts.append(Escort(self, stage='normal', side='right'))
        elif self.escort_count == 1 and 'large' not in stages and 'right' in sides:            
            self.escorts.append(Escort(self, stage='normal', side='left'))
        elif self.escort_count == 2 and 'large' not in stages:
            self.escorts.append(Escort(self, stage='large', side='left'))
            self._remove_escort('normal', 'left')
            self._remove_escort('normal', 'right')
        elif self.escort_count == 1 and 'large' in stages:
            side = 'right' if 'left' in sides else 'left'
            self.escorts.append(Escort(self, stage='normal', side=side))
        elif self.escort_count == 2 and large_side == 'left' and 'normal' in stages:
            self.escorts.append(Escort(self, stage='large', side='right'))
            self._remove_escort('normal', 'right')
        elif self.escort_count == 2 and large_side == 'right' and 'normal' in stages:
            self.escorts.append(Escort(self, stage='large', side='left'))
            self._remove_escort('normal', 'left')
        
        for e in self.escorts:
            e.timer = duration if e.stage == 'normal' else duration // 2

    def _remove_escort(self, stage, side):
        target = next((e for e in self.escorts if e.side==side and e.stage==stage), None)
        if target:
            self.escorts.remove(target)

    def _demo_update(self):
        self.ship.moving_down = False
        self.ship.moving_left = False
        self.ship.moving_right = False
        self.ship.moving_up = False

        danger = None
        danger_dist = float('inf')
        for bullet in self.boss_bullets:
            dist = math.hypot(self.ship.rect.centerx - bullet.rect.centerx,
                              self.ship.rect.centery - bullet.rect.centery)
            if dist < danger_dist:
                danger_dist = dist
                danger = bullet
        boss = None
        target = None
        if self.aliens:
            non_boss = [a for a in self.aliens if not isinstance(a, Boss)]
            if non_boss:
                target = min(self.aliens.sprites(), key=lambda a:
                         math.hypot(a.rect.centerx - self.ship.rect.centerx,
                                    a.rect.centery - self.ship.rect.centery))
            else:
                boss = next((a for a in self.aliens if isinstance(a, Boss)), None)
                center_x = self.settings.screen_width // 2
                center_y = self.settings.screen_height * 0.8
                dx_b = center_x - self.ship.rect.centerx
                dy_b = center_y - self.ship.rect.centery
                self.ship.moving_right = dx_b > 100
                self.ship.moving_left = dx_b < -100
                self.ship.moving_down = dy_b > 100
                self.ship.moving_up = dy_b < -100

        target_powerup = None
        if self.powerups:
            target_powerup = min(self.powerups, key=lambda p: math.hypot(
                p.rect.centerx - self.ship.rect.centerx,
                p.rect.centery - self.ship.rect.centery
            ))
       
        DANGER_THRESHOLD = 200
        ATTACK_X_THRESHOLD = 50
        SAFE_DIST = 250
        TOO_FAR = 500
        BOSS_SAFE_DIST = 200

        boss_too_close = (boss and not boss.explode_timer and
                          math.hypot(boss.rect.centerx - self.ship.rect.centerx,
                                     boss.rect.centery - self.ship.rect.centery) < BOSS_SAFE_DIST)
        
        
        if danger and danger_dist < DANGER_THRESHOLD:
            dx = self.ship.rect.centerx - danger.rect.centerx
            dy = self.ship.rect.centery - danger.rect.centery

            self.ship.moving_down = dy > 0
            self.ship.moving_left = dx < 0
            self.ship.moving_up = dy < 0 
            self.ship.moving_right = dx > 0
        
        elif target:
            aim_x = target.rect.centerx
            aim_y = target.rect.bottom + 250

            dx = aim_x - self.ship.rect.centerx
            dy = aim_y - self.ship.rect.centery
            dist = math.hypot(dx, dy)

            target_dist = math.hypot(
                target.rect.centerx - self.ship.rect.centerx,
                target.rect.centery - self.ship.rect.centery
            )

            if target_dist < SAFE_DIST:
                self.ship.moving_right = dx < 0
                self.ship.moving_left = dx > 0
                self.ship.moving_up = True
            elif dist > 10:
                self.ship.moving_right = dx > 0
                self.ship.moving_left = dx < 0
                self.ship.moving_down = dy > 0
                self.ship.moving_up = dy < 0

        elif boss_too_close:
            dx = self.ship.rect.centerx - boss.rect.centerx
            dy = self.ship.rect.centery - boss.rect.centery
            self.ship.moving_right = dx > 0
            self.ship.moving_left = dx < 0
            self.ship.moving_down = dy > 0
            self.ship.moving_up = dy < 0

        elif target_powerup:
            dx_p = target_powerup.rect.centerx - self.ship.rect.centerx
            dy_p = target_powerup.rect.centery - self.ship.rect.centery
            self.ship.moving_right = dx_p > 0
            self.ship.moving_left = dx_p < 0
            self.ship.moving_down = dy_p > 0             
            self.ship.moving_up = dy_p < 0

        if self.ship.rect.left <= 0:
            self.ship.moving_left = False
        if self.ship.rect.right >= self.settings.screen_width:
            self.ship.moving_right = False
        if self.ship.rect.top <= 0:
            self.ship.moving_up = False
        if self.ship.rect.bottom >= self.settings.screen_height:
            self.ship.moving_down = False
        
        self.ship.update()
        self.ship.invincible_timer()
        self._update_bullets()
        self._update_aliens()
        self._check_powerup_collisions()
        self._fire_bullet()
    
    def _menu_playing(self):
        self.menu_frames_activate += 1
        if self.menu_frames_activate > 60:   
            self.menu_frames_activate = 0
            if not self.menu_frames_playing1 and not self.menu_frames_playing2:
                r= random.random()
                if r < 0.15:
                    self.menu_frames_playing2 = True
                    self.menu_frames_index = 2
                    self.menu_frames_forward = True
                elif r < 0.5:
                    self.menu_frames_playing1 = True
            
        if self.menu_frames_playing1:
            self.menu_frames_timer +=1
            if self.menu_frames_timer < self.menu_frames_speed * 2:
                return
            self.menu_frames_timer = 0
            self.menu_frames_index += 1
            if self.menu_frames_index > 1:
                self.menu_frames_index = 0
                self.menu_frames_playing1 = False
                
        elif self.menu_frames_playing2:
            
            self.menu_frames_timer += 1
            if self. menu_frames_timer < self.menu_frames_speed :
                return
            self.menu_frames_timer = 0
            self.menu_frames_index += 1 if self.menu_frames_forward else -1
            if self.menu_frames_index > len(self.menu_frames) - 1:
                self.menu_frames_index = len(self.menu_frames) - 1
                self.menu_frames_forward = False
                self.playing_round += 1
            if self.menu_frames_index <  len(self.menu_frames) - 4:
                self.menu_frames_index = len(self.menu_frames) - 4
                self.menu_frames_forward = True
                self.playing_round += 1
            if self.playing_round > 7:
                self.playing_round = 0
                self.menu_frames_index = 0               
                self.menu_frames_playing2 = False
                

    def _draw_instructions(self):

        sw = self.settings.screen_width
        sh = self.settings.screen_height
        mouse_pos = pygame.mouse.get_pos()
        self._menu_playing()
        self.screen.blit(self.menu_frames[self.menu_frames_index], (0, 0))

        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font_title = pygame.font.SysFont(None, int(sh * 0.1))
        font = pygame.font.SysFont(None, int(sh * 0.045))
        font_small = pygame.font.SysFont(None, int(sh * 0.032))

        # 游戏标题
        # title = font_title.render('Angry Cat Mercy', True, (255, 255, 0))
        self.screen.blit(self.scaled_title, self.scaled_title.get_rect(center=(int(sw * 0.12), int(sh * 0.22))))

        howtoplay_rect = pygame.Rect(int(sw * 0.05), int(sh * 0.85), int(sw * 0.12), int(sh * 0.05))
        htp_color = (60, 100, 140) if howtoplay_rect.collidepoint(mouse_pos) else (40, 70, 110)
        pygame.draw.rect(self.screen, htp_color, howtoplay_rect, border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), howtoplay_rect, 2, border_radius=20)
        htp_surf = font.render('How to Play', True, (255, 255, 255))
        self.screen.blit(htp_surf, htp_surf.get_rect(center=howtoplay_rect.center))
        self.howtoplay_button_rect = howtoplay_rect

        if self.show_howtoplay:
            self._draw_howtoplay_window()

        # -- 右半边 --
        right_cx = int(sw * 0.75)
        btn_w = int(sw * 0.18)
        btn_h = int(sh * 0.07)
        btn_x = right_cx - btn_w // 2

        def draw_btn(label, y, color_base, color_hover, btn_font=None):
            if btn_font is None:
                btn_font = font
            rect = pygame.Rect(btn_x, y, btn_w, btn_h)
            color = color_hover if rect.collidepoint(mouse_pos) else color_base
            pygame.draw.rect(self.screen, color, rect, border_radius=25)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=25)
            surf = btn_font.render(label, True, (255, 255, 255))
            self.screen.blit(surf, surf.get_rect(center=rect.center))
            return rect

        # 登录状态
        login_font = pygame.font.SysFont(None, int(sh * 0.05))
        if self.shop.current_user:
            user_text = login_font.render(
                f'Player: {self.shop.current_user}  |  Points: {self.shop.points:,}',
                True, (255, 215, 0))
        else:
            user_text = login_font.render('Not logged in', True, (150, 150, 150))
        self.screen.blit(user_text, user_text.get_rect(center=(right_cx, int(sh * 0.22))))

        # Play 按钮（大）
        play_w = int(btn_w * 1.2)
        play_h = int(btn_h * 1.4)
        play_rect = pygame.Rect(right_cx - play_w // 2, int(sh * 0.3), play_w, play_h)
        play_color = (80, 200, 80) if play_rect.collidepoint(mouse_pos) else (60, 160, 60)
        pygame.draw.rect(self.screen, play_color, play_rect, border_radius=35)
        pygame.draw.rect(self.screen, (255, 255, 255), play_rect, 2, border_radius=35)
        play_surf = font_title.render('PLAY', True, (255, 255, 255))
        self.screen.blit(play_surf, play_surf.get_rect(center=play_rect.center))
        # 同步给 Button 类的点击检测
        self.play_button.rect = play_rect
        self.play_button.msg_image_rect.center = play_rect.center

        # Login 按钮
        
        login_label = 'Double CLICKs to log out' if self.shop.current_user else 'Login'
        login_rect = draw_btn(login_label, int(sh * 0.52), (80, 80, 160), (110, 110, 200),btn_font=None)

        # Shop 按钮
        shop_rect = draw_btn('Shop', int(sh * 0.64), (100, 60, 140), (130, 80, 180))

        rank_rect = draw_btn('Ranking', int(sh * 0.76), (100, 80, 40), (140, 110, 60))

        # 底部提示
        hint = font_small.render('Survive the chasing from angry Mercy', True, (120, 120, 120))
        self.screen.blit(hint, hint.get_rect(center=(sw // 2, int(sh * 0.93))))

        if self.show_ranking:
            self._draw_ranking_window()

        # 存储供点击检测
        self.shop_button_rect = shop_rect
        self.login_button_rect = login_rect
        self.rank_button_rect = rank_rect

    def _draw_ranking_window(self):
        sw = self.settings.screen_width
        sh = self.settings.screen_height
        mouse_pos = pygame.mouse.get_pos()

        win_w = int(sw * 0.35)
        win_h = int(sh * 0.7)
        win_rect = pygame.Rect(0, 0, win_w, win_h)
        win_rect.center = (sw // 2, sh // 2)

        overlay = pygame.Surface((win_w, win_h))
        overlay.set_alpha(240)
        overlay.fill((20, 20, 40))
        self.screen.blit(overlay, win_rect.topleft)
        pygame.draw.rect(self.screen, (100, 100, 180), win_rect, 2)

        font_title = pygame.font.SysFont(None, int(sh * 0.05))
        font = pygame.font.SysFont(None, int(sh * 0.038))
        font_small = pygame.font.SysFont(None, int(sh * 0.03))

        title = font_title.render('-- Ranking --', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(win_rect.centerx,
                                                        win_rect.top + int(win_h * 0.08))))
        from rankings import load_rankings
        rankings = load_rankings().copy()
        if not rankings:
            empty = font.render('No records yet', True, (150, 150, 150))
            self.screen.blit(empty, empty.get_rect(center=(win_rect.centerx, win_rect.centery)))
        else:
            for i, entry in enumerate(rankings[:10]):
                y = win_rect.top + int(win_h * 0.18) + i * int(win_h * 0.075)
                color = (255, 215, 0) if i == 0 else (200, 200, 200) if i == 1 else (180, 120, 60) if i == 2 else (180, 180, 180)
                rank_surf = font.render(f'#{i+1}', True, color)
                self.screen.blit(rank_surf, rank_surf.get_rect(midleft=(win_rect.left + int(win_w * 0.08), y)))
                name_surf = font.render(entry['name'], True, (255, 255, 255))
                self.screen.blit(name_surf, name_surf.get_rect(midleft=(win_rect.left + int(win_w * 0.22), y)))
                score_surf = font.render(f"{entry['score']:,}", True, color)
                self.screen.blit(score_surf, score_surf.get_rect(midright=(win_rect.right - int(win_w * 0.32), y)))
                time_surf = font_small.render(entry['time'], True, (120, 120, 120))
                self.screen.blit(time_surf, time_surf.get_rect(midright=(win_rect.right - int(win_w * 0.04), y)))

        if self.shop.current_user:
            find_ranking = load_rankings().copy()
            time_records =[]
            for r, i in enumerate(find_ranking):
                if i['name'] == self.shop.current_user:
                    time_records.append((r, i['time']))
            time_records.sort(key=lambda x: x[1], reverse=True)
            
            latest_rank = time_records[0][0]
            latest_time = time_records[0][1]
            from datetime import datetime
            dt = datetime.strptime(latest_time, '%Y-%m-%d %H:%M')
            dt_formatted = dt.strftime('%H:%M %m/%d')
            user_hint = font_small.render(f'Your latest rank is {latest_rank + 1} at {dt_formatted}', True, (255, 255, 255))
            self.screen.blit(user_hint, user_hint.get_rect(midbottom=(win_rect.centerx, win_rect.bottom)))

        # 关闭按钮
        close_w = int(sw * 0.07)
        close_h = int(sh * 0.045)
        close_rect = pygame.Rect(win_rect.right - close_w - 10, win_rect.top + 10, close_w, close_h)
        close_color = (160, 60, 60) if close_rect.collidepoint(mouse_pos) else (120, 40, 40)
        pygame.draw.rect(self.screen, close_color, close_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), close_rect, 1, border_radius=8)
        close_surf = font_small.render('Close', True, (255, 255, 255))
        self.screen.blit(close_surf, close_surf.get_rect(center=close_rect.center))
        self.ranking_close_rect = close_rect

    def _draw_howtoplay_window(self):
        sw = self.settings.screen_width
        sh = self.settings.screen_height
        mouse_pos = pygame.mouse.get_pos()

        win_w = int(sw * 0.35)
        win_h = int(sh * 0.75)
        win_rect = pygame.Rect(0, 0, win_w, win_h)
        win_rect.center = (sw // 2, sh // 2)

        overlay = pygame.Surface((win_w, win_h))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 40))
        self.screen.blit(overlay, win_rect.topleft)
        pygame.draw.rect(self.screen, (100, 100, 180), win_rect, 2)

        font_title = pygame.font.SysFont(None, int(sh * 0.05))
        font = pygame.font.SysFont(None, int(sh * 0.04))
        font_small = pygame.font.SysFont(None, int(sh * 0.03))

        title = font_title.render('-- How to Play --', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(win_rect.centerx,
                                                        win_rect.top + int(win_h * 0.07))))

        lines = [
                ('arrow', 'Arrow keys   Move'),
                ('space', 'Space            Fire'),
                ('esc',   'ESC               Exit'),
                ('enter', 'Enter            Buy item'),
                ('num',   '1 ~ 6              Use item'),
            ]
        icon_h = int(sh * 0.07)
        icon_size = int(sh * 0.06)
        row_gap = int(win_h * 0.12)
        start_y = win_rect.top + int(win_h * 0.12)

        for i, (key, line) in enumerate(lines):
            line_y = start_y + i * row_gap
            bg_img = self.instruction_bgs[key]
            orig_w, orig_h = bg_img.get_size()
            new_w = int(orig_w * icon_h / orig_h)
            scaled_bg = pygame.transform.scale(bg_img, (new_w, icon_h))
            text_surf = font.render(line, True, (255, 255, 255))
            total_w = new_w + 15 + text_surf.get_width()
            img_x = win_rect.centerx - total_w // 2
            self.screen.blit(scaled_bg, (img_x, line_y))
            self.screen.blit(text_surf, text_surf.get_rect(midleft=(img_x + new_w + 25, line_y + icon_h // 2)))

        # 提示语
        tip = font_small.render('Log in to purchase powerful items from the Shop!', True, (180, 220, 255))
        self.screen.blit(tip, tip.get_rect(center=(win_rect.centerx, win_rect.top + int(win_h * 0.76))))

        # Powerups
        icon_labels = ['Spread', 'Scatter', 'Laser']
        section = font_small.render('-- Collect Powerups --', True, (180, 180, 180))
        self.screen.blit(section, section.get_rect(center=(win_rect.centerx,
                                                            win_rect.top + int(win_h * 0.82))))
        icons_total_w = len(self.instruction_icons) * icon_size + (len(self.instruction_icons) - 1) * int(sw * 0.03)
        icons_start_x = win_rect.centerx - icons_total_w // 2
        for i, (img, _) in enumerate(self.instruction_icons):
            orig_w, orig_h = img.get_size()
            scaled = pygame.transform.scale(img, (int(orig_w * icon_size / orig_h), icon_size))
            ix = icons_start_x + i * (icon_size + int(sw * 0.03))
            self.screen.blit(scaled, (ix, win_rect.top + int(win_h * 0.87)))
            label = font_small.render(icon_labels[i], True, (200, 200, 200))
            self.screen.blit(label, label.get_rect(centerx=ix + icon_size // 2,
                                                    top=win_rect.top + int(win_h * 0.87) + icon_size + 4))
        # 关闭按钮
        close_w = int(sw * 0.07)
        close_h = int(sh * 0.045)
        close_rect = pygame.Rect(win_rect.right - close_w - 10, win_rect.top + 10, close_w, close_h)
        close_color = (160, 60, 60) if close_rect.collidepoint(mouse_pos) else (120, 40, 40)
        pygame.draw.rect(self.screen, close_color, close_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), close_rect, 1, border_radius=8)
        close_surf = font_small.render('Close', True, (255, 255, 255))
        self.screen.blit(close_surf, close_surf.get_rect(center=close_rect.center))
        self.howtoplay_close_rect = close_rect

    def _draw_game_over(self, rankings=None, highlight=None, name=None):
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font_big = pygame.font.SysFont(None, int(sh * 0.1))

        title = font_big.render('Game Over', True, (255, 255, 0))
        self.screen.blit(title, title.get_rect(center=(sw // 2, int(sh * 0.15))))

        current_score = font_big.render(f'Your Score: {self.stats.score}', True, (255, 255, 0))
        current_score_rect = current_score.get_rect(center=(self.sb.screen_rect.centerx, int(sh * 0.35)))
        self.screen.blit(current_score, current_score_rect)

        if rankings:
            font_rank = pygame.font.SysFont(None, int(sh * 0.04))
            font_time = pygame.font.SysFont(None, int(sh * 0.028))
            font_title = pygame.font.SysFont(None, int(sh * 0.045))
            
            left_x = sw // 6          # 排行榜左对齐基准，屏幕左侧
            right_x = sw * 2 // 3     # 本次排名左对齐基准，屏幕右侧，与left_x对称

            rank_title = font_title.render('-- Ranking --', True, (255, 215, 0))
            self.screen.blit(rank_title, rank_title.get_rect(midleft=(left_x, int(sh * 0.25))))

            if highlight is not None and name:
                your_title = font_title.render(f"-- {name}'s  Rank --", True, (255, 215, 0))
                self.screen.blit(your_title, your_title.get_rect(midleft=(right_x, int(sh * 0.25))))

                current_rank = font_rank.render(f" No.{highlight+1}", True, (255, 215, 0))
                self.screen.blit(current_rank, current_rank.get_rect(midleft=(right_x, int(sh * 0.35))))

                rank_score = font_rank.render(f"{self.stats.score:,}", True, (255, 215, 0))
                self.screen.blit(rank_score, rank_score.get_rect(midleft=(right_x, int(sh * 0.42))))

            for i, entry in enumerate(rankings[:5]):
                y = int(sh * (0.3 + i * 0.09))

                color = (255, 215, 0) if i == highlight else (255, 255, 255)

                name_surf = font_rank.render(f"{i+1}. {entry['name']}", True, color)
                self.screen.blit(name_surf, name_surf.get_rect(midleft=(left_x, y)))

                score_surf = font_rank.render(f"{entry['score']:,}", True, color)
                self.screen.blit(score_surf, score_surf.get_rect(midleft=(left_x + 200, y)))

                time_surf = font_time.render(f"{entry['time']}", True, color)
                self.screen.blit(time_surf, time_surf.get_rect(midleft=(left_x, y + int(sh * 0.03))))

    def _game_over_loop(self):
        cursor_visible = True
        cursor_timer = 0
        CURSOR_INTERVAL = 500
        sw = self.settings.screen_width
        sh = self.settings.screen_height
        font_input = pygame.font.SysFont(None, int(sh * 0.05))
        font_prompt = pygame.font.SysFont(None, int(sh * 0.04))

        from rankings import load_rankings, add_entry
        rankings = load_rankings()       

        name = ''
        active = True
        login_prompt1 = False
        login_prompt2 = False
        accounts = load_account()

        while active:
            if self.shop.current_user:
                active = False
                add_points(self.shop.current_user, self.stats.score)
                name = self.shop.current_user

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and name.strip():
                        if name in accounts:
                            login_prompt2 = True
                            #用户已存在，是否存入当前分数？
                        else:
                            login_prompt1 = True
                            #是否登录存入自己的分数？
                    elif event.key == pygame.K_y and login_prompt2:
                        add_points(name, self.stats.score)
                        active = False
                    elif event.key == pygame.K_n and login_prompt2:
                        active = False
                    elif event.key == pygame.K_y and login_prompt1:
                        self.shop._login()
                        active = False
                    elif event.key == pygame.K_n and login_prompt1:
                        active = False

                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        if len(name) < 12:
                            name += event.unicode
                    
            self._draw_game_over(rankings)

            cursor_timer += self.clock.tick(60)         #每秒60帧 = 1000/60 = 毫秒/帧
            if cursor_timer >= CURSOR_INTERVAL:
                cursor_visible = not cursor_visible     #酷
                cursor_timer = 0

            prompt = font_prompt.render('Enter your name:', True,  (255, 255, 255))
            self.screen.blit(prompt, prompt.get_rect(center=(sw // 2, int(sh * 0.55))))
            box_rect = pygame.Rect(sw // 2 - 150, int(sh * 0.6), 300, int(sh * 0.06))
            pygame.draw.rect(self.screen, (255, 255, 255), box_rect, 2)
            display_name = name + ('|' if cursor_visible else '')       #帅
            name_surf = font_input.render(display_name, True, (255, 255, 255))
            self.screen.blit(name_surf, name_surf.get_rect(center=box_rect.center))
            if login_prompt1:
                lp_surf = font_prompt.render('Login to save points? Y / N', True, (255, 215, 0))
                self.screen.blit(lp_surf, lp_surf.get_rect(center=(sw // 2, int(sh * 0.72))))
            if login_prompt2:
                lp_surf = font_prompt.render('Account exists! Save points to it? Y / N', True, (255, 215, 0))
                self.screen.blit(lp_surf, lp_surf.get_rect(center=(sw // 2, int(sh * 0.72))))

            pygame.display.flip()

        self.rankings, self.my_rank = add_entry(name.strip(), self.stats.score)
        self.my_name = name.strip()
        self._draw_game_over(self.rankings, highlight=self.my_rank, name=self.my_name.strip())
        pygame.display.flip()
        pygame.time.wait(2000)

    def _draw_confirm_exit(self):
        sw = self.settings.screen_width
        sh = self.settings.screen_height
        mouse_pos = pygame.mouse.get_pos()

        # 半透明遮罩
        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # 弹窗背景
        box_w = int(sw * 0.35)
        box_h = int(sh * 0.3)
        box_rect = pygame.Rect(sw // 2 - box_w // 2, sh // 2 - box_h // 2, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 30, 30), box_rect, border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), box_rect, 2, border_radius=20)

        # 文字
        font_title = pygame.font.SysFont(None, int(sh * 0.06))
        font = pygame.font.SysFont(None, int(sh * 0.04))
        title = font_title.render('Exit Game?', True, (255, 255, 0))
        self.screen.blit(title, title.get_rect(center=(sw // 2, sh // 2 - int(sh * 0.08))))
        hint = font.render('Your data might not be saved.', True, (180, 180, 180))
        self.screen.blit(hint, hint.get_rect(center=(sw // 2, sh // 2 - int(sh * 0.02))))

        # 按钮
        btn_w = int(sw * 0.1)
        btn_h = int(sh * 0.07)
        gap = int(sw * 0.03)

        yes_rect = pygame.Rect(sw // 2 - btn_w - gap // 2, sh // 2 + int(sh * 0.05), btn_w, btn_h)
        no_rect  = pygame.Rect(sw // 2 + gap // 2,          sh // 2 + int(sh * 0.05), btn_w, btn_h)

        yes_color = (200, 60, 60) if yes_rect.collidepoint(mouse_pos) else (160, 40, 40)
        no_color  = (60, 160, 60) if no_rect.collidepoint(mouse_pos)  else (40, 120, 40)

        pygame.draw.rect(self.screen, yes_color, yes_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), yes_rect, 2, border_radius=15)
        pygame.draw.rect(self.screen, no_color,  no_rect,  border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), no_rect,  2, border_radius=15)

        font_btn = pygame.font.SysFont(None, int(sh * 0.045))
        self.screen.blit(font_btn.render('Yes', True, (255, 255, 255)), 
                        font_btn.render('Yes', True, (255, 255, 255)).get_rect(center=yes_rect.center))
        self.screen.blit(font_btn.render('No',  True, (255, 255, 255)), 
                        font_btn.render('No',  True, (255, 255, 255)).get_rect(center=no_rect.center))

        self.confirm_yes_rect = yes_rect
        self.confirm_no_rect  = no_rect    
  
    def _update_screen(self):
        '''Update images on the screen, and flip to the new screen.'''
        #Redraw the screen during each pass through the loop
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()

        # if self.game_active:
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        for bullet in self.boss_bullets.sprites():
            bullet.draw_bullet()
        for bullet in self.escort_bullets:
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)
        for alien in self.aliens:
            if hasattr(alien, 'health_arc'):
                alien.health_arc.draw()
        if self.powerups:
            for p in self.powerups:
                p.blitme()
        for boss in self.boss_group:
            boss.laser.draw()  
        self.gunsys.gauge.drawme()
        self.gunsys.gauge_invincible.drawme()
        self.gunsys.gauge_ammo.drawme()
        for alien in self.aliens:
            if isinstance(alien, Boss) and alien.gunsys:
                alien.gunsys.gauge.drawme()
        for e in self.escorts:
            if e.stage == 'large' and e.gunsys:
                e.gunsys.gauge.drawme()
                e.gunsys.gauge_ammo.drawme()
        #Display score
        self.sb.show_score()
        self.inventory.draw()
        for escort in self.escorts:
            escort.blitme()
        if self.shockwave:
            self.shockwave.draw()

        #Draw the play button if the game is inactive.
        if not self.game_active:
            if not self.game_started:
                if self.show_instructions:
                    self._draw_instructions()
                    if self.shop.current_user:
                        self.inventory.draw()
                    
            else:
                self._draw_game_over(
                    getattr(self, 'rankings', None),
                    highlight=getattr(self, 'my_rank', None),
                    name=getattr(self, 'my_name', None))       
                      #最后画
        if self.confirm_exit:
            self._draw_confirm_exit()
        #Make the most recently drawn screen visible
        pygame.display.flip()


if __name__ == '__main__':
    #Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()

