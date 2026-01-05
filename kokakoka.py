import os
import sys
import random
import math
import pygame as pg

# =====================
# 基本設定
# =====================
WIDTH = 1100
HEIGHT = 650
FPS = 60
BG_SCROLL_SPEED = 5

ARROW_SPEED = 14
SWORD_SPEED = 6
ARROW_DMG = 1
SWORD_DMG = 1
ARROW_NUM = 1
SWORD_NUM = 1

os.chdir(os.path.dirname(os.path.abspath(__file__)))

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GREEN = (80, 255, 80)
YELLOW = (255, 255, 0)

# =====================
# プレイヤー
# =====================
class Player:
    def __init__(self, xy):
        img = pg.image.load("fig/0.png").convert_alpha()
        img = pg.transform.flip(img, True, False)
        self.image = pg.transform.rotozoom(img, 0, 1.8)
        self.rect = self.image.get_rect(center=xy)

        self.speed = 8
        self.hp = 5

        self.arrow_speed = ARROW_SPEED
        self.sword_speed = SWORD_SPEED
        self.arrow_dmg = ARROW_DMG
        self.sword_dmg = SWORD_DMG
        self.arrow_num = ARROW_NUM
        self.sword_num = SWORD_NUM

    def update(self):
        key = pg.key.get_pressed()
        if key[pg.K_UP]:
            self.rect.y -= self.speed
        if key[pg.K_DOWN]:
            self.rect.y += self.speed
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# =====================
# 敵
# =====================
class Enemy:
    def __init__(self, level=0):
        img = pg.image.load("fig/alien1.png").convert_alpha()
        self.image = pg.transform.rotozoom(img, 0, 0.3)
        self.rect = self.image.get_rect(
            center=(WIDTH + 50, random.randint(100, HEIGHT - 100))
        )
        self.max_hp = 30 + level * 5
        self.hp = self.max_hp
        self.speed = random.randint(3, 6) + level // 3

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        rate = self.hp / self.max_hp
        pg.draw.rect(screen, RED, (self.rect.centerx - 20, self.rect.top - 10, 20, 5))
        pg.draw.rect(screen, GREEN,
                     (self.rect.centerx - 20, self.rect.top - 10, 20 * rate, 5))

# =====================
# Arrow
# =====================
class Arrow:
    def __init__(self, player, index, total):
        img = pg.image.load("fig/arrow.png").convert_alpha()
        self.image = pg.transform.rotozoom(img, 0, 1 / 6)
        self.rect = self.image.get_rect(center=player.rect.center)
        # ★ 矢数に応じて上下にずらす
        offset = (index - (total - 1) / 2) * 20
        self.rect = self.image.get_rect(
            center=(player.rect.centerx, player.rect.centery + offset)
        )
        self.speed = player.arrow_speed
        self.dmg = player.arrow_dmg

    def update(self):
        self.rect.x += self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# =====================
# Sword
# =====================
class Sword:
    def __init__(self, player, index, total):
        img = pg.image.load("fig/sword.png").convert_alpha()
        self.image = pg.transform.rotozoom(img, -120, 1 / 6)
        self.rect = self.image.get_rect(center=player.rect.center)
        # ★ 扇状に初期配置
        angle = (index - (total - 1) / 2) * 15
        rad = math.radians(angle)

        self.rect = self.image.get_rect(
            center=(
                player.rect.centerx + math.cos(rad) * 30,
                player.rect.centery + math.sin(rad) * 30
            )
        )
        self.speed = player.sword_speed
        self.dmg = player.sword_dmg

    def update(self, enemies):
        if not enemies:
            return
        target = min(
            enemies,
            key=lambda e: math.hypot(
                e.rect.centerx - self.rect.centerx,
                e.rect.centery - self.rect.centery
            )
        )
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist:
            self.rect.x += dx / dist * self.speed
            self.rect.y += dy / dist * self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# =====================
# Gate
# =====================
GATE_EFFECTS = [
    ("hp", "HP +1"),
    ("speed_arrow", "矢速度 +1"),
    ("speed_sword", "剣速度 +1"),
    ("dmg_arrow", "矢DMG +1"),
    ("dmg_sword", "剣DMG +1"),
    ("num_arrow", "矢数 +1"),
    ("num_sword", "剣数 +1"),
]

class Gate:
    def __init__(self, y, effect):
        self.effect = effect
        self.surface = pg.Surface((80, 150), pg.SRCALPHA)
        self.surface.fill((0, 200, 255, 120))
        self.rect = self.surface.get_rect(midleft=(WIDTH, y))
        self.speed = 6
        self.text = dict(GATE_EFFECTS)[effect]
        self.font = pg.font.SysFont("meiryo", 20)

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.surface, self.rect)
        txt = self.font.render(self.text, True, YELLOW)
        screen.blit(txt, txt.get_rect(center=self.rect.center))


def draw_status_ui(screen, player, font):
    # 背景パネル
    panel = pg.Surface((260, 250), pg.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    screen.blit(panel, (10, 10))

    texts = [
        f"HP : {player.hp}",
        "",
        f"Arrow",
        f"  Num   : {player.arrow_num}",
        f"  DMG   : {player.arrow_dmg}",
        f"  Speed : {player.arrow_speed}",
        "",
        f"Sword",
        f"  Num   : {player.sword_num}",
        f"  DMG   : {player.sword_dmg}",
        f"  Speed : {player.sword_speed}",
    ]

    y = 20
    for line in texts:
        txt = font.render(line, True, WHITE)
        screen.blit(txt, (20, y))
        y += 18


# =====================
# ステージ
# =====================
def stage2(screen):
    clock = pg.time.Clock()
    bg = pg.transform.scale(pg.image.load("fig/pg_bg.jpg"), (WIDTH, HEIGHT))

    player = Player((200, HEIGHT // 2))
    enemies = []
    attacks = []
    gates = []

    enemy_timer = gate_timer = sword_timer = arrow_timer = 0
    enemy_count = 0
    tmr = 0
    font = pg.font.SysFont("meiryo", 26)

    pg.mixer.music.load("fig/joi.mp3")
    pg.mixer.music.set_volume(0.4)
    pg.mixer.music.play(-1)

    while True:
        dt = clock.tick(FPS)
        enemy_timer += dt
        gate_timer += dt
        sword_timer += dt
        arrow_timer += dt

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        if enemy_timer >= 1200:
            enemy_timer = 0
            enemies.append(Enemy(enemy_count // 5))
            enemy_count += 1

        if gate_timer >= 3000:
            gate_timer = 0
            gates.clear()
            e1, e2 = random.sample(GATE_EFFECTS, 2)
            gates.append(Gate(200, e1[0]))
            gates.append(Gate(450, e2[0]))

        if arrow_timer >= 500:
            arrow_timer = 0
            for i in range(player.arrow_num):
                attacks.append(Arrow(player, i, player.arrow_num))

        if sword_timer >= 1500:
            sword_timer = 0
            for i in range(player.sword_num):
                attacks.append(Sword(player, i, player.sword_num))

        player.update()

        for gate in gates[:]:
            gate.update()
            if player.rect.colliderect(gate.rect):
                if gate.effect == "hp":
                    player.hp += 1
                elif gate.effect == "speed_arrow":
                    player.arrow_speed += 1
                elif gate.effect == "speed_sword":
                    player.sword_speed += 1
                elif gate.effect == "dmg_arrow":
                    player.arrow_dmg += 1
                elif gate.effect == "dmg_sword":
                    player.sword_dmg += 1
                elif gate.effect == "num_arrow":
                    player.arrow_num += 1
                elif gate.effect == "num_sword":
                    player.sword_num += 1
                gates.clear()

        for atk in attacks[:]:
            if isinstance(atk, Arrow):
                atk.update()
                if atk.rect.left > WIDTH:
                    attacks.remove(atk)
            else:
                atk.update(enemies)

        for enemy in enemies[:]:
            enemy.update()
            if enemy.rect.colliderect(player.rect):
                player.hp -= 1
                enemies.remove(enemy)
            elif enemy.rect.right < 0:
                enemies.remove(enemy)

        for atk in attacks[:]:
            for enemy in enemies[:]:
                if atk.rect.colliderect(enemy.rect):
                    enemy.hp -= atk.dmg
                    if isinstance(atk, Sword):
                        attacks.remove(atk)
                    if enemy.hp <= 0:
                        enemies.remove(enemy)

        screen.blit(bg, [0, 0])

        for gate in gates:
            gate.draw(screen)
        for atk in attacks:
            atk.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)

        draw_status_ui(screen, player, font)
        tmr += 1

        if player.hp <= 0:
            screen.blit(font.render("GAME OVER", True, RED),
                        (WIDTH // 2 - 80, HEIGHT // 2))
            pg.display.update()
            pg.time.wait(3000)
            return

        pg.display.update()

# =====================
# 実行
# =====================
if __name__ == "__main__":
    pg.init()
    stage2(pg.display.set_mode((WIDTH, HEIGHT)))
    pg.quit()
    sys.exit()

