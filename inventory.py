#
#
#
import pygame
from powerup import PowerUp
from account import load_account, save_accounts


class Inventory:
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.shop = ai_game.shop
        self.gunsys = ai_game.gunsys
        # self.temp_inventory = ai_game.shop.temp_inventory
        # self.current_user = ai_game.shop.current_user    这是复制，而不是引用。复制无法更新最新的变化

        # _dummy = PowerUp(ai_game, 0, 0)

        sw = self.settings.screen_width
        sh = self.settings.screen_height

        self.window_width = int(sw * 0.4)
        self.window_height = int(sh * 0.1)
        self.window_rect = pygame.Rect(0, 0, self.window_width, self.window_height)
        self.window_rect.centerx = sw // 2
        self.window_rect.bottom = sh - 10        
        self.name_to_mode = {
                'life': 0,
                'spread': 1,
                'scatter': 2,
                'laser': 3,
                'invincible': 4,
                'kill_all': 5,
                'ammo': 6,
                'escort': 7,
                    }
        self.name_to_stats = {
                'life': 0,
                'spread':   {'buff': 1, 'bullet_count': 10, 'duration': 720},
                'scatter':  {'buff': 1, 'bullet_count': 10, 'duration': 720},
                'laser':    {'buff': 1, 'bullet_count': 3,  'duration': 720},
                'invincible': {'duration': 60 * 6},
                'kill_all': {},   
                'ammo': {'duration': 60 * 6},   
                'escort': {'duration': 60 * 30},        
                
            }
        self.refresh()
        
    def refresh(self):
        if self.shop.current_user:
            accounts = load_account()
            self.items = accounts[self.shop.current_user]['inventory']
        else:
            self.items = self.shop.temp_inventory

        self.items_image = []
        for name in self.items:
            self.items_image.append(PowerUp._images[name])

        self.item_rects = []

        rows = (len(self.items) + 5) // 6
        self.window_height = int(self.settings.screen_height * 0.1) * rows
        self.window_rect.height = self.window_height
        self.window_rect.bottom = self.settings.screen_height - 10

        card_height = int(self.settings.screen_height * 0.1) 
        card_width = card_height
        padding = int(self.window_width * 0.05)  
        for i in range(len(self.items)):
            row = i // 6
            col = i % 6
            x = self.window_rect.left + padding + col * (card_width + padding)
            y = self.window_rect.top + row * (card_height )             
            self.item_rects.append(pygame.Rect(x, y, card_width, card_height))
    
    def use_item(self, index):
        if index >= len(self.items):
            return
        self.settings.powerup_sound.play()
        used = self.items.pop(index)
        mode = self.name_to_mode[used]
        stats = self.name_to_stats[used]
        
        if mode == 0:
            self.ai_game.stats.ships_left += 1
            self.ai_game.sb.prep_ships()
        elif mode == 4:
            self.gunsys.active_invincible(stats['duration'])
        elif mode == 5:
            self.gunsys.activate_kill_all()
        elif mode == 6:
            self.gunsys.activate_ammo(stats['duration'])
        elif mode == 7:
            self.ai_game._activate_escorts(duration=60 * 60)

        else:
            last_mode = self.gunsys.mode
            self.gunsys.mode = mode
            if last_mode == mode or last_mode == 0:
                self.gunsys.buff += stats['buff']
                self.gunsys.bullet_count += stats['bullet_count']
                self.gunsys.total_duration += stats['duration']
                self.gunsys.timer = self.gunsys.total_duration
                
            else:
                self.gunsys.total_duration = stats['duration']
                self.gunsys.timer = self.gunsys.total_duration
                self.gunsys.buff = stats['buff']
                self.gunsys.bullet_count = stats['bullet_count']
        if self.shop.current_user:
            accounts = load_account()
            accounts[self.shop.current_user]['inventory'] = self.items
            save_accounts(accounts) 
        self.refresh()

    def is_full(self):
        return len(self.items) >= 6

    def draw(self):
        sh = self.settings.screen_height
        font = pygame.font.SysFont(None, int(sh * 0.03))

        # 窗口背景
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(120)
        overlay.fill((20, 20, 40))
        self.screen.blit(overlay, self.window_rect.topleft)
        # pygame.draw.rect(self.screen, (100, 100, 180), self.window_rect, 2) 边框
        font_hint = pygame.font.SysFont(None, int(sh * 0.05))
        user = self.shop.current_user if self.shop.current_user else 'Guest'
        hint = font_hint.render(f"{user}'s bag  |  Press num key to use", True, (180, 180, 180))
        hint.set_alpha(180)
        self.screen.blit(hint, hint.get_rect(center=self.window_rect.center))

        for i, (rect, image) in enumerate(zip(self.item_rects, self.items_image)):
            # 格子边框
            pygame.draw.rect(self.screen, (100, 100, 180), rect, 1)

            # 图片等比缩放
            orig_w, orig_h = image.get_size()
            scale = min(rect.width / orig_w, rect.height / orig_h) * 0.8
            scaled = pygame.transform.scale(image, (int(orig_w * scale), int(orig_h * scale)))
            self.screen.blit(scaled, scaled.get_rect(center=rect.center))

            # 数字键提示
            key_surf = font.render(str(i + 1), True, (255, 215, 0))
            self.screen.blit(key_surf, key_surf.get_rect(topleft=(rect.left + 3, rect.top + 3)))



