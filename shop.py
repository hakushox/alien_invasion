#
#
#

import pygame
import sys
from powerup import PowerUp
import math
import random
from resource_manager import resource_path
        
from account import load_account, verify_password, add_points, update_inventory, register

class Shop:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        _dummy = PowerUp(ai_game, 0, 0)

        sw = self.settings.screen_width
        sh = self.settings.screen_height

        self.window_width = int(sw * 0.4)
        self.window_height = int(sh * 0.7)
        self.window_rect = pygame.Rect(0, 0, self.window_width, self.window_height)
        self.window_rect.center =  (sw // 2, sh // 2)

        self.items = [
            {'name': 'life', 'price': 15000, 'mode': 0},
            {'name': 'spread', 'price': 8000, 'mode': 1},
            {'name': 'scatter', 'price': 9000, 'mode': 2},
            {'name': 'laser', 'price': 8000, 'mode': 3},
            {'name': 'invincible', 'price': 12000, 'mode': 4},
            {'name': 'kill_all', 'price': 15000, 'mode': 5},
            {'name': 'ammo', 'price': 11000, 'mode': 6},
            {'name': 'escort', 'price': 8000, 'mode': 7},
        ]
        self.item_rects = []
        card_width = int(self.window_width * 0.25)
        card_height = int(self.window_height * 0.2)
        padding = int(self.window_width * 0.05)  
        for i in range(len(self.items)):
            row = i // 3
            col = i % 3
            x = self.window_rect.left + padding + col * (card_width + padding)
            y = self.window_rect.top + int(self.window_height * 0.2) + row * (card_height + padding)
            self.item_rects.append(pygame.Rect(x, y, card_width, card_height))
        
        girl_poses = {
                0: pygame.image.load(resource_path(f'images/menu/girl_pos.png')).convert_alpha(),
                1: pygame.image.load(resource_path(f'images/menu/girl_pos01.png')).convert_alpha(),
                2: pygame.image.load(resource_path(f'images/menu/girl_pos02.png')).convert_alpha(),
                3: pygame.image.load(resource_path(f'images/menu/girl_pos023.png')).convert_alpha(),
                4: pygame.image.load(resource_path(f'images/menu/girl_pos011.png')).convert_alpha(),
                5: pygame.image.load(resource_path(f'images/menu/girl_pos022.png')).convert_alpha(),
                6: pygame.image.load(resource_path(f'images/menu/girl_pos03.png')).convert_alpha(),
                7: pygame.image.load(resource_path(f'images/menu/girl_pos024.png')).convert_alpha(),
}
        title_w, title_h = girl_poses[0].get_size()
        self.girl_responses = {
            'spread': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/girl_pos04.png')).convert_alpha(), (title_w // 6, title_h // 6)),
            'scatter': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/girl_pos05.png')).convert_alpha(), (title_w // 6, title_h // 6)),
            'laser': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/girl_pos06.png')).convert_alpha(), (title_w // 6, title_h // 6)),
            'invincible': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/girl_pos07.png')).convert_alpha(), (title_w // 6, title_h // 6)),

        }
        i = random.randint(0, 5)
        self.girl_pos = pygame.transform.scale(girl_poses[i], (title_w // 6, title_h // 6))
        self.girl_pos_purchase = pygame.transform.scale(girl_poses[1], (title_w // 6, title_h // 6))
        i = random.randint(6, 7)
        self.girl_pos_continue = pygame.transform.scale(girl_poses[i], (title_w // 6, title_h // 6))

        self.speech_bubbles = {
            'intro': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/speech bubble1.png')).convert_alpha(), (title_w // 3, title_h // 3)),
            'continue': pygame.transform.scale(pygame.image.load(resource_path(f'images/menu/speech bubble2.png')).convert_alpha(), (title_w // 3, title_h // 3)),

        }

        self.current_user = None
        self.selected = None
        self.accounts = load_account()
        self.points = 0
        self.buy_result = None
        self.temp_inventory = []
        self.button_hovered = False


    def run(self, continue_only=False):
        last_music = self.settings.current_music
        pygame.mixer.music.load(resource_path('sounds/shop_bg.mp3'))
        pygame.mixer.music.play(-1)
        self.settings.current_music = 'shop_bg.mp3'

        self.purchase_count = 0
        self.ai_game.inventory.refresh()
        

        if continue_only:
            item_to_show = [i for i, item in enumerate(self.items) if item['name'] == 'life']
            self.girl_pos = self.girl_pos_continue
        else: 
            self._login()
            item_to_show = list(range(len(self.items)))

        self.settings.enter_shop.play()
        active = True
        bought = False
        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        active = False
                    if event.key == pygame.K_RETURN:
                        self.buy_result = self._buy(continue_only=continue_only)
                        if self.buy_result == 'success':
                            self.settings.cha_ching.play()
                            self.ai_game.inventory.refresh()
                            bought_name = self.items[self.selected]['name']
                            if bought_name in self.girl_responses:
                                self.girl_pos = self.girl_responses[bought_name]
                            else:
                                self.girl_pos = self.girl_pos_purchase
                            if continue_only:
                                bought = True
                                active = False
                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()                    
                    if hasattr(self, 'back_rect') and self.back_rect.collidepoint(mouse_pos):
                        if not self.button_hovered:
                            self.settings.button_hovered.play() 
                            self.button_hovered = True
                    else:
                        self.button_hovered = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for i in item_to_show:
                        if self.item_rects[i].collidepoint(mouse_pos):
                            self.selected = i

                    if hasattr(self, 'back_rect') and self.back_rect.collidepoint(mouse_pos):
                        active = False
                                
            self._draw(item_to_show, continue_only=continue_only)
            if not continue_only:                
                self.ai_game.inventory.draw()
            pygame.display.flip()
            self.ai_game.clock.tick(60)
        pygame.mixer.music.load(resource_path(f'sounds/{last_music}'))  # 退出时换回
        pygame.mixer.music.play(-1)
        return bought
    
    def _login(self):
        if self.current_user:
            return
        cursor_visible = True
        cursor_timer = 0
        CURSOR_INTERVAL = 500
        font_input = pygame.font.SysFont(None, int(self.window_height * 0.05))
        font_prompt = pygame.font.SysFont(None, int(self.window_height * 0.04))   
        sh = self.settings.screen_height

        name = ''
        password = ''
        active = True
        welcome = False
        name_fail = False
        password_fail = False
        register_prompt = False
        stage = 'name'

        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if box_rect1.collidepoint(mouse_pos):
                        stage = 'name'
                    elif box_rect2.collidepoint(mouse_pos):
                        stage = 'password'

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        if stage == 'name':
                            stage = 'password'
                        else:
                            stage = 'name'
                    elif event.key == pygame.K_ESCAPE:
                        active = False
                    elif event.key == pygame.K_RETURN:
                        if stage == 'name' and name.strip():
                            if name in self.accounts:
                                self.settings.type_correct.play()
                                stage = 'password'
                            else:
                                self.settings.error.play()
                                register_prompt = True

                        elif stage == 'password':
                            if name not in self.accounts:
                                self.settings.error.play()
                                register_prompt = True
                                password = ''
                                stage = 'name'
                                
                            if verify_password(name, password):
                                self.current_user = name
                                self.points = self.accounts[name]['points']
                                self.settings.type_correct.play()
                                active = False
                                welcome = True
                            else:
                                self.settings.error.play()
                                password = ''
                                password_fail = True
                        elif stage == 'set_password':
                            register(name, password, 0)
                            self.current_user = name
                            self.points = 0
                            self.accounts = load_account()
                            self.settings.type_correct.play()
                            active = False
                            welcome = True
                            self.settings.welcome.play()
                    if register_prompt:
                        if event.key == pygame.K_y:
                            stage = 'set_password'
                            register_prompt = False
                        elif event.key == pygame.K_n:
                            register_prompt = False
                            name = ''

                    elif event.key == pygame.K_BACKSPACE:
                        if stage == 'name':
                            name = name[:-1]
                        else:
                            password = password[:-1]
                    else:
                        if event.unicode.isprintable():
                            if stage == 'name' and len(name) < 12:
                                name += event.unicode
                            elif stage == 'password' and len(password) < 4:
                                password += event.unicode
                            elif stage == 'set_password' and len(password) < 4:
                                password += event.unicode

            cursor_timer += self.ai_game.clock.tick(60)       #每秒60帧 = 1000/60 = 毫秒/帧
            if cursor_timer >= CURSOR_INTERVAL:
                cursor_visible = not cursor_visible     #酷
                cursor_timer = 0
            
            overlay = pygame.Surface((self.window_width, self.window_height))
            overlay.set_alpha(230)
            overlay.fill((20, 20, 40))
            self.screen.blit(overlay, self.window_rect.topleft)
            pygame.draw.rect(self.screen, (100, 100, 180), self.window_rect, 2)
            # 标题
            title = font_prompt.render('-- Login --', True, (255, 215, 0))
            self.screen.blit(title, title.get_rect(center=(self.window_rect.centerx,
                                                            self.window_rect.top + int(self.window_height * 0.1))))
            # 名字输入框
            prompt1 = font_prompt.render('Enter your name:', True, (255, 255, 255))
            self.screen.blit(prompt1, prompt1.get_rect(midleft=(self.window_rect.left + 40,
                                                                self.window_rect.top + int(self.window_height * 0.3))))
            box_rect1 = pygame.Rect(self.window_rect.centerx - 150,
                                    self.window_rect.top + int(self.window_height * 0.37),
                                    300, int(sh * 0.05))
            color1 = (255, 255, 100) if stage == 'name' else (150, 150, 150)
            pygame.draw.rect(self.screen, color1, box_rect1, 2)
            display_name = name + ('|' if cursor_visible and stage == 'name' else '')
            name_surf = font_input.render(display_name, True, (255, 255, 255))
            self.screen.blit(name_surf, name_surf.get_rect(center=box_rect1.center))

            prompt2 = font_prompt.render('Password:', True, (255, 255, 255))
            self.screen.blit(prompt2, prompt2.get_rect(midleft=(self.window_rect.left + 40,
                                                                self.window_rect.top + int(self.window_height * 0.55))))
            box_rect2 = pygame.Rect(self.window_rect.centerx - 150,
                                    self.window_rect.top + int(self.window_height * 0.62),
                                    300, int(sh * 0.05))
            color2 = (255, 255, 100) if stage == 'password' else (150, 150, 150)
            pygame.draw.rect(self.screen, color2, box_rect2, 2)
            display_password = '*' * len(password) + ('|' if cursor_visible and stage == 'password' or stage == 'set_password' else '')
            password_surf = font_input.render(display_password, True, (255, 255, 255))
            self.screen.blit(password_surf, password_surf.get_rect(center=box_rect2.center))
            hint = font_prompt.render('ESC to skip', True, (150, 150, 150))
            self.screen.blit(hint, hint.get_rect(center=(self.window_rect.centerx,
                                            self.window_rect.bottom - int(self.window_height * 0.05))))
            if name_fail:
                fail1 = font_prompt.render('Name not found', True, (255, 80, 80))
                self.screen.blit(fail1, fail1.get_rect(midleft=(self.window_rect.left + 40,
                                                             self.window_rect.top + int(self.window_height * 0.46))))
            if register_prompt:
                reg_surf = font_prompt.render('Name not found. Register? Y / N', True, (255, 215, 0))
                self.screen.blit(reg_surf, reg_surf.get_rect(center=(self.window_rect.centerx,
                                                          self.window_rect.top + int(self.window_height * 0.46))))
            if password_fail:
                fail2 = font_prompt.render('Wrong password', True, (255, 80, 80))
                self.screen.blit(fail2, fail2.get_rect(midleft=(self.window_rect.left + 40,
                                                             self.window_rect.top + int(self.window_height * 0.71))))
            pygame.display.flip()

        while welcome:
            font_welcome = pygame.font.SysFont(None, int(self.window_height * 0.15))  
            # self.screen.fill(self.settings.bg_color)
            overlay = pygame.Surface((self.window_width, self.window_height))
            overlay.set_alpha(230)
            overlay.fill((20, 20, 40))
            self.screen.blit(overlay, self.window_rect.topleft)
            pygame.draw.rect(self.screen, (100, 100, 180), self.window_rect, 2)
            prompt_welcome = font_welcome.render(f'Welcome, {name}!', True, (255, 215, 0))
            self.screen.blit(prompt_welcome, prompt_welcome.get_rect(center=(self.window_rect.centerx,
                                                                            self.window_rect.centery)))
            prompt_any_key = font_prompt.render(f'Press any key to continue!', True, (160, 160, 160))
            self.screen.blit(prompt_any_key, prompt_any_key.get_rect(center=(self.window_rect.centerx,
                                                    self.window_rect.bottom - int(self.window_height * 0.12))))
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    welcome = False

            pygame.display.flip()

    def _draw(self, items_to_show=None, continue_only=False):
        if items_to_show is None:
            items_to_show = list(range(len(self.items)))

        sw = self.settings.screen_width
        sh = self.settings.screen_height
        font_title = pygame.font.SysFont(None, int(sh * 0.06))
        font_item = pygame.font.SysFont(None, int(sh * 0.04))
        font_hint = pygame.font.SysFont(None, int(sh * 0.03))

        # 窗口背景
        self.screen.blit(self.ai_game.menu_bg, (0, 0))
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        self.screen.blit(overlay, self.window_rect.topleft)
        pygame.draw.rect(self.screen, (100, 100, 180), self.window_rect, 2)

        # if self.buy_result == 'not_logged_in':
        #     msg = font_hint.render('Please login first', True, (255, 80, 80))
        if self.buy_result == 'no_selection':
            msg = font_hint.render('Please select an item', True, (255, 80, 80))
        elif self.buy_result == 'not_enough':
            msg = font_hint.render('Not enough points', True, (255, 80, 80))
        elif self.buy_result == 'success':
            msg = font_hint.render('Purchase successful!', True, (80, 255, 80))
        elif self.buy_result == 'full':
            msg = font_hint.render('Inventory full!', True, (255, 80, 80))
        else:
            msg = None

        if msg:
            self.screen.blit(msg, msg.get_rect(center=(self.window_rect.centerx,
                                                    self.window_rect.bottom + int(self.window_height * 0.03))))
        # 标题
        title = font_title.render('-- Shop --', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(self.window_rect.centerx,
                                                        self.window_rect.top + int(self.window_height * 0.08))))

        if self.current_user:

            points_surf = font_item.render(f'{self.current_user} | Points: {self.points:,}', True, (255,255,100))
        else:
            points_surf = font_item.render(f'Guest  |  Points: {self.points:,}', True, (150, 150, 150))
        self.screen.blit(points_surf, points_surf.get_rect(midleft=(self.window_rect.left + 20,
                                                        self.window_rect.top + int(self.window_height * 0.15))))
        mouse_pos = pygame.mouse.get_pos()
        btn_w = int(sw * 0.08)
        btn_h = int(sh * 0.05)
        back_rect = pygame.Rect(self.window_rect.right - btn_w - 10, 
                                self.window_rect.top + 10, btn_w, btn_h)
        back_color = (160, 60, 60) if back_rect.collidepoint(mouse_pos) else (120, 40, 40)
        pygame.draw.rect(self.screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), back_rect, 1, border_radius=10)
        back_surf = font_hint.render('Back to Menu', True, (255, 255, 255))
        self.screen.blit(back_surf, back_surf.get_rect(center=back_rect.center))
        self.back_rect = back_rect

        for i in items_to_show:
            item = self.items[i]
            rect = self.item_rects[i]
            if i == self.selected:
                pygame.draw.rect(self.screen, (255, 215, 0), rect, 3)
            else:
                pygame.draw.rect(self.screen, (100, 100, 180), rect, 1)

            image = PowerUp._images[item['name']]
            orig_w, orig_h = image.get_size()
            img_area_h = int(rect.height * 0.5)
            scale = min(rect.width / orig_w, img_area_h / orig_h)
            scaled = pygame.transform.scale(image, (int(orig_w * scale), int(orig_h * scale)))
            self.screen.blit(scaled, scaled.get_rect(centerx=rect.centerx,
                                                   top=rect.top + 5))
            
            name_surf = font_item.render(item['name'], True , (255,255,255))
            self.screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx,
                                                                rect.top + int(rect.height * 0.7))))
            if continue_only:
                actual_price = int(item['price'] * (1+ self.purchase_count * 0.2) * 
                            math.sqrt(self.ai_game.stats.level))
            else:
                actual_price = int(item['price'] * (1 + self.purchase_count * 0.2) * 
                                    max(1, (math.sqrt(self.ai_game.stats.level) - 1)))
                            
            price_surf = font_hint.render(f"{actual_price:,} pts", True, (255, 215, 0))
            self.screen.blit(price_surf, price_surf.get_rect(center=(rect.centerx,
                                                                   rect.top + int(rect.height * 0.88))))
        hint = font_hint.render('ESC - Back    Click to select    ENTER - Buy', True, (150, 150, 150))
        self.screen.blit(hint, hint.get_rect(center=(self.window_rect.centerx,
                                                  self.window_rect.bottom - int(self.window_height * 0.04))))
        if continue_only:
            self.screen.blit(self.speech_bubbles['continue'], self.speech_bubbles['continue'].get_rect(center=(
                int(sw // 2 + self.window_width // 2 + 300), int(sh  // 2 + self.window_height // 2 - 350)
                )))
        else:
            self.screen.blit(self.girl_pos, self.girl_pos.get_rect(center=(
                                        int(sw // 2 + self.window_width // 2), int(sh  // 2 + self.window_height // 2 - 100)
                                        )))
        self.screen.blit(self.speech_bubbles['intro'], self.speech_bubbles['intro'].get_rect(center=(
                                        int(sw // 2 + self.window_width // 2 + 300), int(sh  // 2 + self.window_height // 2 - 350)
                                        )))
        
    def _buy(self, continue_only=False):
        if self.selected is None:
            return 'no_selection'
        base_price = self.items[self.selected]['price']
        actual_price = int(base_price * (1+ self.purchase_count * 0.2) * 
                           max(1, (math.sqrt(self.ai_game.stats.level) - 1)) )
        if continue_only:
            actual_price = int(base_price * (1+ self.purchase_count * 0.2) * 
                           math.sqrt(self.ai_game.stats.level))
        if self.points < actual_price:
            self.settings.error.play()
            return 'not_enough'
        if self.ai_game.inventory.is_full() and not continue_only:
            self.settings.error.play()
            return 'full'
        self.points -= actual_price
        if self.current_user:
            if self.ai_game.stats.score >= actual_price:
                self.ai_game.stats.score -= actual_price

            elif self.ai_game.stats.score < actual_price:                
                self.ai_game.stats.score = 0
            self.purchase_count += 1
            add_points(self.current_user, -actual_price)
            if continue_only:
                return 'success'
            update_inventory(self.current_user, self.items[self.selected]['name'])
        else:
            if continue_only:       # ← 加这里
                self.ai_game.stats.score -= actual_price
                return 'success'
            self.temp_inventory.append(self.items[self.selected]['name'])
            self.ai_game.stats.score -= actual_price
            
        return 'success'


 