import os
import sys
import random
import math
import pygame as pg
import subprocess

# =====================
# 基本設定
# =====================
WIDTH = 1100
HEIGHT = 650
FPS = 60

ARROW_SPEED = 14
SWORD_SPEED = 6
ARROW_DMG = 1
SWORD_DMG = 1
ARROW_NUM = 1
SWORD_NUM = 1

ENEMY_IMAGE = "fig/alien1.png"
BOSS_IMAGE = "fig/103358909.jpg"

os.chdir(os.path.dirname(os.path.abspath(__file__)))

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GREEN = (80, 255, 80)
BLUE = (80, 120, 255)

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
    def __init__(self, level):
        self.is_boss = (level % 5 == 4)

        if self.is_boss:
            img = pg.image.load(BOSS_IMAGE).convert_alpha()
            scale = 1.5
            self.rect = pg.transform.rotozoom(img, 0, scale).get_rect(
                center=(WIDTH + 80, HEIGHT // 2)
            )
        else:
            img = pg.image.load(ENEMY_IMAGE).convert_alpha()
            scale = 0.3
            self.rect = pg.transform.rotozoom(img, 0, scale).get_rect(
                center=(WIDTH + 50, random.randint(100, HEIGHT - 100))
            )

        self.image = pg.transform.rotozoom(img, 0, scale)
        self.max_hp = (40 if self.is_boss else 10) + level * 2
        self.hp = self.max_hp
        self.speed = random.randint(1, 2) + level // 3

    def update(self):
        self.rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        rate = self.hp / self.max_hp
        h = 8 if self.is_boss else 5
        pg.draw.rect(screen, RED,
                     (self.rect.centerx - 25, self.rect.top - 12, 50, h))
        pg.draw.rect(screen, GREEN,
                     (self.rect.centerx - 25, self.rect.top - 12, 50 * rate, h))

# =====================
# Arrow
# =====================
class Arrow:
    def __init__(self, player, index, total):
        img = pg.image.load("fig/arrow.png").convert_alpha()
        self.image = pg.transform.rotozoom(img, 0, 0.1)

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
        self.image = pg.transform.rotozoom(img, -120, 0.125)

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
        txt = self.font.render(self.text, True, BLACK)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

def spawn_kill_gate(x, y, gates):
    if len(gates) >= 3:
        return
    effect, _ = random.choice(GATE_EFFECTS)
    gate = Gate(y, effect)
    gate.rect.centerx = x
    gates.append(gate)

# =====================
# ボス強化選択
# =====================
BOSS_UPGRADES = [
    ("arrow_num", "矢の数 ×2"),
    ("sword_num", "剣の数 ×2"),
    ("arrow_dmg", "矢DMG ×2"),
    ("sword_dmg", "剣DMG ×2"),
]

class BossChoice:
    def __init__(self, center, effect):
        self.effect = effect
        self.font = pg.font.SysFont("meiryo", 26)
        self.surface = pg.Surface((320, 80))
        self.surface.fill(BLUE)
        self.rect = self.surface.get_rect(center=center)
        self.text = self.font.render(effect[1], True, WHITE)

    def draw(self, screen):
        screen.blit(self.surface, self.rect)
        screen.blit(self.text, self.text.get_rect(center=self.rect.center))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

def apply_boss_upgrade(player, upgrade):
    if upgrade == "arrow_num":
        player.arrow_num *= 2
    elif upgrade == "sword_num":
        player.sword_num *= 2
    elif upgrade == "arrow_dmg":
        player.arrow_dmg *= 2
    elif upgrade == "sword_dmg":
        player.sword_dmg *= 2

def create_boss_choices():
    effects = random.sample(BOSS_UPGRADES, 3)
    ys = [HEIGHT//2 - 120, HEIGHT//2, HEIGHT//2 + 120]
    return [BossChoice((WIDTH//2, y), e) for e, y in zip(effects, ys)]

# =====================
# UI
# =====================
def draw_status_ui(screen, player, font):
    panel = pg.Surface((260, 250), pg.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    screen.blit(panel, (10, 10))

    texts = [
        f"HP : {player.hp}",
        "",
        "Arrow",
        f"  Num   : {player.arrow_num}",
        f"  DMG   : {player.arrow_dmg}",
        f"  Speed : {player.arrow_speed}",
        "",
        "Sword",
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
# Advertisement
# =====================
class Advertisement:
    def __init__(self):
        self.img = pg.Surface((WIDTH//2, HEIGHT))  #広告を載せる用の背景
        self.img.fill((128, 128, 128))
        self.img.set_alpha(200)
        try:
            self.imgx = pg.image.load("fig/bb.png")
            self.imgx = pg.transform.rotozoom(self.imgx, 0, 0.25)
            self.imgx_rct = self.img.get_rect()
            self.surx = pg.Surface((64, 64))
            self.surx.fill((152, 152, 152))
            self.imgNext = pg.image.load("fig/militaly.png")
            self.imgNext = pg.transform.rotozoom(self.imgNext, 0, 0.5)
            self.imgNext_rct = self.imgNext.get_rect()
            self.imgNext_rct.topleft = (WIDTH/2-250, HEIGHT/2-250)
        except:
            self.surx = pg.Surface((64, 64))  #×ボタン画像がない場合は灰色の四角のみ
            self.surx.fill((152, 152, 152))

        self.surx_rct = self.surx.get_rect()
        self.surx_rct.topleft = ((WIDTH/4-64 + WIDTH/2), 0)

    def update(self, screen):
        screen.blit(self.img, [WIDTH/4, 0])
        screen.blit(self.surx, self.surx_rct)
        screen.blit(self.imgx, self.surx_rct)
        screen.blit(self.imgNext, self.imgNext_rct)
            

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
    advertisement = Advertisement()

    start_se = pg.mixer.Sound("joi_sound/アヒルが大笑い.mp3")
    gameover_se = pg.mixer.Sound("joi_sound/鳥の奇声.mp3")

    boss_choices = []
    boss_choice_active = False

    enemy_timer = gate_timer = sword_timer = arrow_timer = 0
    enemy_count = 0
    font = pg.font.SysFont("meiryo", 26)
    start_se.play()

    pg.mixer.music.load("fig/joi.mp3")
    pg.mixer.music.set_volume(0.4)
    pg.mixer.music.play(-1)

    is_gameover = False  #ゲームオーバーフラグ

    while True:
        dt = clock.tick(FPS)
        enemy_timer += dt
        gate_timer += dt
        sword_timer += dt
        arrow_timer += dt

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if is_gameover:
                    gameover_se.play()
                    if advertisement.surx_rct.collidepoint(event.pos):
                        # ×ボタンでゲームリスタート
                        stage2(screen)
                        return
                    elif advertisement.imgNext_rct.collidepoint(event.pos):
                        # 広告部分クリックで別のゲームスタート
                        pg.quit()
                        subprocess.run([sys.executable, "shine.py"])
                        sys.exit()
        if not is_gameover:
            if enemy_timer >= 5000:
                enemy_timer = 0
                enemies.append(Enemy(enemy_count))
                enemy_count += 1

            if boss_choice_active and event.type == pg.MOUSEBUTTONDOWN:
                for choice in boss_choices:
                    if choice.clicked(event.pos):
                        apply_boss_upgrade(player, choice.effect[0])
                        boss_choices.clear()
                        boss_choice_active = False

        if not boss_choice_active:
            if enemy_timer >= 5000:
                enemy_timer = 0
                enemies.append(Enemy(enemy_count))
                enemy_count += 1

            if gate_timer >= 4000:
                gate_timer = 0
                gates.clear()
                e1, e2 = random.sample(GATE_EFFECTS, 2)
                gates.append(Gate(200, e1[0]))
                gates.append(Gate(450, e2[0]))

            if arrow_timer >= 500:
                arrow_timer = 0
                for i in range(player.arrow_num):
                    attacks.append(Arrow(player, i, player.arrow_num))

            if sword_timer >= 3000:
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
                    player.hp -= 3
                    enemies.remove(enemy)

            for atk in attacks[:]:
                for enemy in enemies[:]:
                    if atk.rect.colliderect(enemy.rect):
                        enemy.hp -= atk.dmg
                        if isinstance(atk, Sword):
                            attacks.remove(atk)
                        if atk in attacks:
                            attacks.remove(atk)
                        if enemy.hp <= 0:
                            if enemy.is_boss:
                                boss_choices = create_boss_choices()
                                boss_choice_active = True
                            else:
                                spawn_kill_gate(enemy.rect.centerx,
                                                enemy.rect.centery, gates)
                            enemies.remove(enemy)

        screen.blit(bg, (0, 0))
        for gate in gates:
            gate.draw(screen)
        for atk in attacks:
            atk.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)

        draw_status_ui(screen, player, font)

        if boss_choice_active:
            overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            for choice in boss_choices:
                choice.draw(screen)

            for gate in gates:
                gate.draw(screen)
            for atk in attacks:
                atk.draw(screen)
            for enemy in enemies:
                enemy.draw(screen)
            player.draw(screen)

            draw_status_ui(screen, player, font)

            if player.hp <= 0:
                is_gameover = True
                
  
        pg.display.update()
        if is_gameover:
            screen.blit(font.render("GAME OVER", True, RED),
                            (WIDTH // 2 - 80, HEIGHT // 2))
            pg.display.update()

            advertisement.update(screen)

# =====================
# 実行
# =====================
if __name__ == "__main__":
    pg.init()
    stage2(pg.display.set_mode((WIDTH, HEIGHT)))
    pg.quit()
    sys.exit()
