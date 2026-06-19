#
#
#

from alien import Alien
import random
from alien_ai import AlienAi
from boss import Boss
from timer import timer
import math

class FleetManager:
    # @timer
    def __init__(self, ai_game):
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.screen = ai_game.screen
        # _a = Alien(self.ai_game)
        # self.alien_width, self.alien_height = _a.rect.size
        # 然后所有队形方法直接用 self.alien_width，不再每次实例化。
        self.patterns = {
            3:self._fleet_grid, 2: self._fleet_v,
            4: self._fleet_split, 1: self._fleet_diamond,
            5: self._fleet_random,
        }
    
    def create_fleet(self, level):
        self.ai_game.aliens.empty()
        if level == 1:
            self.patterns[level]()

        elif level < 4:
            fleet_pick = random.randint(2,5)
            self.patterns[fleet_pick]()
        elif level == 4:
            self._fleet_ai(level)

        if level % 5 == 0:
            self._create_boss(level)
        if  level > 5 and level < 10:
            self._fleet_ai(level)
        
        if level > 9:
            self._fleet_ai(level)
            self._create_boss(level)

    def _create_boss(self, level):
        boss = Boss(self.ai_game, level)
        self.ai_game.aliens.add(boss)
        self.ai_game.boss = boss
        self.ai_game.boss_group.add(boss)

        if len(self.ai_game.boss_group) == 2:
            bosses = list(self.ai_game.boss_group)
            bosses[1].direction_x = bosses[0].direction_x * -1

    def _fleet_ai(self, level):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        alien_counts = 3 + int(math.log(level + 1) * 2.5)
        for _ in range(alien_counts):
            current_x = random.randint(alien_width, self.settings.screen_width - alien_width)
            current_y = random.randint(0, self.settings.screen_height //2 )
            self._create_alien_ai(current_x, current_y)
            
        # self._create_boss()

    def _create_alien_ai(self, x , y):
        new_alien = AlienAi(self.ai_game)
        new_alien.x = x
        new_alien.y = y
        new_alien.rect.x = new_alien.x
        new_alien.rect.y = new_alien.y
        self.ai_game.aliens.add(new_alien)

    def _create_alien(self, x, y):
        new_alien = Alien(self.ai_game)
        new_alien.x = x
        new_alien.rect.x = x
        new_alien.rect.y = y
        self.ai_game.aliens.add(new_alien)
    
    def _fleet_grid(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        current_x, current_y = alien_width, alien_height
        # 宽度铺满屏幕，高度限制在屏幕40%以内
        while current_x < sw - 2 * alien_width:
            while current_y < sh * 0.6:
                self._create_alien(current_x, current_y)
                current_y += 1.5 * alien_height
            current_y = alien_height
            current_x += 1.5 * alien_width

    def _fleet_v(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        # V形顶点在屏幕中央偏上，基于屏幕宽度决定列数
        center_x = sw // 2 - alien_width / 2
        top_y = sh * 0.45  # 顶点在屏幕45%高度处
        alien_count = sw // (int(alien_width * 2))  # 列数由屏幕宽度决定
        spacing = alien_width

        for i in range(alien_count):
            left_x = center_x - i * spacing
            right_x = center_x + i * spacing
            y = top_y - i * alien_height * 0.5  # 向上展开
            self._create_alien(int(left_x), int(y))
            if i != 0:
                self._create_alien(int(right_x), int(y))

    def _fleet_split(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        current_y = 0
        # 高度限制在屏幕40%以内，左右两侧各占屏幕宽度40%
        while current_y < sh * 0.4:
            current_x = alien_width
            while current_x < sw * 0.4:  # 左侧40%
                self._create_alien(current_x, current_y)
                current_x += alien_width * 1.5
            current_x = sw - alien_width * 2
            while current_x > sw * 0.6:  # 右侧40%
                self._create_alien(current_x, current_y)
                current_x -= alien_width * 1.5
            current_y += alien_height

    def _fleet_diamond(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        center_x = sw // 2 - alien_width // 2
        top_y = 0
        max_half =  (sw // 2 - alien_width) // alien_width  # 根据屏幕宽度限制最大列数

        row_count = int(sh * 0.7) // int(alien_height)

        for i in range(row_count):
            y = top_y + i * alien_height

            distance = abs(i - row_count // 2)
            half_width = (max_half - distance) * alien_width
            left_x = center_x - half_width
            right_x = center_x + half_width


            self._create_alien(int(left_x), int(y))
            if half_width != 0:
                self._create_alien(int(right_x), int(y))
            if i == row_count // 2:
                self._create_alien(int(center_x), int(y))
                self._create_alien(int(center_x + alien_width), int(y))

    def _fleet_random(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        max_counts = self._get_counts_available()
        set_counts = 12
        alien_counts = min(set_counts, max_counts)

        placed = []
        for _ in range(alien_counts):
            while True:
                # 随机位置限制在屏幕宽度和高度40%范围内
                current_x = random.randint(alien_width, sw - alien_width)
                current_y = random.randint(0, int(sh * 0.4))

                overlapped = any(
                    abs(current_x - px) < alien_width and abs(current_y - py) < alien_height
                    for px, py in placed
                )
                if not overlapped:
                    placed.append((current_x, current_y))
                    self._create_alien(current_x, current_y)
                    break

    def _get_counts_available(self):
        alien = Alien(self.ai_game)
        alien_width, alien_height = alien.rect.size
        sw = self.settings.screen_width
        sh = self.settings.screen_height

        # 可用区域为屏幕宽度 × 屏幕高度40%
        available_area = sw * sh * 0.4
        alien_area = alien_height * alien_width
        return int(available_area / alien_area * 0.5)