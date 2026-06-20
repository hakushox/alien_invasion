from bullet import Bullet
import pygame
import math
import random
from powerup import PowerUp
from shockwave import ShockWave
from powerup_gauge import PowerUpGauge
from ship import Ship

class GunSystem:
    def __init__(self, ai_game, owner=None, bullet_group=None, buff=1):
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.ship = owner if owner else self.ai_game.ship
        self.bullets = bullet_group if bullet_group is not None else self.ai_game.bullets
        self.modes = {
            0: lambda: self.bullets_normal(owner=owner), 
            1: self.bullet_spread, 
            2: self.bullet_scatter, 
            3: self.bullet_laser,
        }
        self.mode = 0
        self.buff = buff
        self.level = self.ai_game.stats.level

        self.total_duration = 0
        self.timer = 0
        self.bullet_count = 0
        
        self.laser_exhausted = False
        self.invincible_timer = 0
        self.invincible_total = 0
        
        # ── 无限弹药核心控制变量 ──
        self.ammo_limitless = 0
        self.ammo_total = 0
        self.last_bullet_count = 0
        self.last_bullet_allowed = self.settings.bullet_allowed # 初始备份

        self.gauge = PowerUpGauge(self, style='weapon')
        self.gauge_invincible = PowerUpGauge(self, style='invincible')
        self.gauge_ammo = PowerUpGauge(self, style='ammo')

    def get_timer(self):
        self.gauge.update()
        self.gauge_invincible.update()
        self.gauge_ammo.update()
        
        # 无限弹药计时递减
        if self.ammo_limitless > 0:
            self.ammo_limitless -= 1
            if self.ammo_limitless <= 0:
                # 状态结束，安全恢复备份的正常限制
                self.settings.bullet_allowed = self.last_bullet_allowed

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.ship.frame_playing = False # 修复原代码 ai_game.ship 指向可能不明确的问题
                
        if self.ammo_limitless <= 0:
            if self.timer > 0:
                self.timer -= 1
                if self.timer <= 0:
                    self.total_duration = 0
                return self.timer <= 0
        return False

    def get_bullets_limit(self):            
        # 若当前处于无限弹药状态，屏幕上允许的子弹上限直接解除限制
        if self.ammo_limitless > 0:
            return 999999
            
        if self.mode == 0:
            return self.settings.bullet_allowed
        elif self.mode == 3:
            return 1            

        return self.bullet_count * self.bullet_count    

    def _bullets_left(self):
        # ── 核心修复 1：无限弹药期间，绝不扣减特殊武器的弹药计数 ──
        if self.ammo_limitless > 0:
            return

        if self.bullet_count > 0:
            self.bullet_count -= 1
            if self.bullet_count <= 0:
                if self.mode == 3:
                    self.bullet_count = 0  
                    self.laser_exhausted = True  
                    self.timer = 0
                    self.total_duration = 0
                else:
                    self.mode = 0
                    self.exhausted = True
                    self.buff = 1 if self.ship == self.ai_game.ship else 0
                    self.timer = 0
                    self.total_duration = 0

    def bullets_normal(self, owner=None):
        from boss import Boss
        from escort import Escort
        if isinstance(owner, Boss):
            if self.ai_game.stats.level % 5 != 0:
                bullet_rows = max(1, int(math.sqrt(self.ai_game.stats.level) - 1))
            else:
                bullet_rows = 1
        elif isinstance(owner, Escort):
            bullet_rows = min(1 + self.ai_game.stats.level // 5, 4)
        else:
            bullet_rows = (self.settings.bullet_rows + self.level - 1)
        
        spacing = 30
        offsets = [(i - (bullet_rows - 1) / 2) * spacing for i in range(bullet_rows)]
        
        for offset in offsets:
            new_bullet = Bullet(self.ai_game, self.ship)
            new_bullet.rect.centerx = self.ship.rect.centerx + offset
            new_bullet.x = float(new_bullet.rect.centerx)
            self.bullets.add(new_bullet)
        
        self.settings.shot_channel.play(self.settings.fire_sound)  

    def _get_offsets(self):
        self.bullet_rows = self.settings.bullet_rows + self.buff
        spacing = 30
        return [(i - (self.bullet_rows - 1) / 2) * spacing for i in range(self.bullet_rows)]

    def bullet_spread(self):        
        self._bullets_left()
        self._last_offsets = []
        for offset in self._get_offsets():
            new_bullet = Bullet(self.ai_game, self.ship)
            new_bullet.rect.centerx = self.ship.rect.centerx + offset
            new_bullet.x = float(new_bullet.rect.centerx)
            self.bullets.add(new_bullet)
            self._last_offsets.append(offset)

        self.settings.shot_channel.play(self.settings.spread_shot_sound)  

    def bullet_scatter(self):          
        self._bullets_left()     
        for i, offset in enumerate(self._get_offsets()):
            new_bullet = Bullet(self.ai_game, self.ship)       
            new_bullet.rect.x = self.ship.rect.centerx + offset
            new_bullet.angle = (i - (self.bullet_rows - 1) / 2) * self.settings.angle
            new_bullet.x = new_bullet.rect.x
            self.bullets.add(new_bullet)        

        self.settings.shot_channel.play(self.settings.scatter_shot_sound)  

    def bullet_laser(self):
        self._bullets_left()
        new_bullet = Bullet(self.ai_game, self.ship, laser=True)
        self.bullets.add(new_bullet)
        self.settings.shot_channel.play(self.settings.laser_shot)

    def active_invincible(self, duration):
        self.settings.powerup_sound_channel.play(self.settings.powerup_invin)
        self.invincible_timer = duration
        self.invincible_total = duration
        self.ship.frames_playing = True      

    def activate_kill_all(self):
        from boss import Boss
        self.settings.kill_all.play()
        self.ai_game.boss_bullets.empty()
        self.ai_game.shockwave = ShockWave(self.ai_game)
    
    def activate_ammo(self, duration):
        """激活或重置无限弹药状态"""
        self.settings.powerup_sound_channel.play(self.settings.powerup_ammo) # 确保播放对应音效
        
        # ── 核心修复 2：只有当不在无限弹药状态时，才备份正常的允许子弹数 ──
        if self.ammo_limitless <= 0:  
            self.last_bullet_allowed = self.settings.bullet_allowed
        
        # 抛弃将变量设为 float('inf') 的危险做法，用常理逻辑控制
        self.ammo_limitless = duration
        self.ammo_total = duration
        
    def get_bullet_killable(self):
        return self.mode != 3