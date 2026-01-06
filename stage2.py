import os
import sys
import random
import math
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
FPS = 60  # フレームレート

SWORD_SPEED = 6  # 剣の速度
ARROW_SPEED = 14  # 矢の速度

os.chdir(os.path.dirname(os.path.abspath(__file__)))

WHITE = (255, 255, 255)  # 白色
BLACK = (0, 0, 0)  # 黒色
RED = (255, 60, 60)  # 赤色
GREEN = (80, 255, 80)  # 緑色
YELLOW = (255, 255, 0)  # 黄色


class Player:
    """
    プレイヤーキャラクターこうかとんを操作するキャラクタークラス
    """
    def __init__(self, xy):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        もどり値：なし
        """
        img = pg.image.load("joi_fig/0.png").convert_alpha()
        img = pg.transform.flip(img, True, False)
        self.image = pg.transform.rotozoom(img, 0, 1.8)
        self.rect = self.image.get_rect(center=xy)

        self.speed = 8
        self.hp = 5
        self.sword_atk = 1  # 剣の攻撃力
        self.arrow_atk = 1  # 矢の攻撃力

    def update(self):
        """
        こうかとんの移動と画面内制限を行うメソッド
        引数：なし
        もどり値：なし
        """
        key = pg.key.get_pressed()
        if key[pg.K_UP]:
            self.rect.y -= self.speed
        if key[pg.K_DOWN]:
            self.rect.y += self.speed
        self.rect.clamp_ip(pg.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen):
        """
        こうかとんを画面に描画するメソッド
        引数 screen：描画先Surface
        もどり値：なし
        """
        screen.blit(self.image, self.rect)


class Gate:
    """
    アイテム効果を持つ壁クラス
    """
    def __init__(self, y, effect, color):
        """
        壁Surfaceを生成する
        引数1 y：壁のy座標
        引数2 effect：壁の効果内容（"hp" / "sword" / "arrow"）
        引数3 color：壁の色（RGBAタプル）
        もどり値：なし
        """
        self.surface = pg.Surface((80, 150), pg.SRCALPHA)
        self.surface.fill(color)
        self.rect = self.surface.get_rect(midleft=(WIDTH, y))
        self.speed = 6
        self.effect = effect

        if effect == "hp":
            self.text = "HP +1"
        elif effect == "sword":
            self.text = "剣 +1"
        elif effect == "arrow":
            self.text = "矢 +1"
        else:
            self.text = ""

        self.font = pg.font.SysFont("meiryo", 22)

    def update(self):
        """
        壁を左方向に移動させるメソッド
        引数：なし
        もどり値：なし
        """
        self.rect.x -= self.speed

    def draw(self, screen):
        """
        壁と効果テキストを描画するメソッド
        引数 screen：描画先Surface
        もどり値：なし
        """
        screen.blit(self.surface, self.rect)
        if self.text:
            txt = self.font.render(self.text, True, YELLOW)
            screen.blit(txt, txt.get_rect(center=self.rect.center))


class Enemy:
    """
    敵キャラクターエイリアンに関するクラス
    """
    def __init__(self, level=0):
        """
        引数に基づきエイリアン画像Surfaceを生成する
        引数 level：敵のレベル（デフォルト0）
        もどり値：なし
        """
        img = pg.image.load("joi_fig/alien1.png").convert_alpha()
        self.image = pg.transform.rotozoom(img, 0, 1.2)
        self.rect = self.image.get_rect(
            center=(WIDTH + 50, random.randint(100, HEIGHT - 100))
        )

        self.max_hp = 30 + level * 5
        self.hp = self.max_hp
        self.speed = random.randint(3, 6) + level // 3

    def update(self):
        """
        敵を左方向に移動させるメソッド
        引数：なし
        もどり値：なし
        """
        self.rect.x -= self.speed

    def draw(self, screen):
        """
        敵とHPバーを描画するメソッド
        引数 screen：描画先Surface
        もどり値：なし
        """
        screen.blit(self.image, self.rect)
        rate = self.hp / self.max_hp
        pg.draw.rect(screen, RED,
                     (self.rect.centerx - 20, self.rect.top - 10, 20, 5))
        pg.draw.rect(screen, GREEN,
                     (self.rect.centerx - 20, self.rect.top - 10, 20 * rate, 5))


class AttackItem:
    """
    攻撃アイテム（剣・矢）に関するクラス
    """
    def __init__(self, kind, player, index):
        """
        引数に基づき攻撃アイテム画像Surfaceを生成する
        引数1 kind：攻撃アイテムの種類（"sword"または"arrow"）
        引数2 player：プレイヤーキャラクターオブジェクト
        引数3 index：攻撃アイテムのインデックス
        もどり値：なし
        """
        self.kind = kind
        self.player = player
        self.index = index

        img = pg.image.load(f"joi_fig/{kind}.png").convert_alpha()
        if kind == "sword":
            img = pg.transform.rotozoom(img, -120, 1 / 6)
            self.speed = SWORD_SPEED
        else:
            img = pg.transform.rotozoom(img, 180, 1 / 6)
            self.speed = ARROW_SPEED

        self.image = img
        self.rect = self.image.get_rect(center=player.rect.center)

        self.angle = index * 60
        self.radius = 50

    def update(self, enemies):
        """
        攻撃アイテムの移動を行うメソッド
        引数 enemies：敵キャラクターリスト
        もどり値：なし
        """
        if self.kind == "sword":
            if enemies:
                target = min(enemies, key=lambda e: math.hypot(
                    e.rect.centerx - self.rect.centerx,
                    e.rect.centery - self.rect.centery))
                dx = target.rect.centerx - self.rect.centerx
                dy = target.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist:
                    dx /= dist
                    dy /= dist
                self.rect.x += dx * self.speed
                self.rect.y += dy * self.speed
            else:
                self.angle += 4
                rad = math.radians(self.angle)
                self.rect.centerx = self.player.rect.centerx + math.cos(rad) * self.radius
                self.rect.centery = self.player.rect.centery + math.sin(rad) * self.radius
        else:
            self.rect.x += self.speed

    def draw(self, screen):
        """
        攻撃アイテムを画面に描画するメソッド
        引数 screen：描画先Surface
        もどり値：なし
        """
        screen.blit(self.image, self.rect)


def stage2(screen):
    """
    ステージ2のメインループ
    引数 screen：画面Surface
    もどり値：なし
    """
    clock = pg.time.Clock()

    bg = pg.image.load("joi_fig/pg_bg.jpg").convert()
    bg = pg.transform.scale(bg, (WIDTH, HEIGHT))

    start_se = pg.mixer.Sound("joi_sound/アヒルが大笑い.mp3")
    gameover_se = pg.mixer.Sound("joi_sound/鳥の奇声.mp3")

    pg.mixer.music.load("joi_sound/famipop3.mp3")
    pg.mixer.music.set_volume(0.4)

    start_se.play()
    pg.mixer.music.play(-1)

    player = Player((200, HEIGHT // 2))
    enemies = []
    attacks = []
    gates = []

    enemy_timer = 0
    gate_timer = 0
    sword_timer = 0
    arrow_timer = 0
    enemy_count = 0

    font = pg.font.SysFont("meiryo", 26)

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
            level = enemy_count // 5
            enemies.append(Enemy(level))
            enemy_count += 1

        if gate_timer >= 3000:
            gate_timer = 0
            gates.clear()

            effects = ["hp", "sword", "arrow"]
            ys = [250, 450]

            for y in ys:
                effect = random.choice(effects)
                if effect == "hp":
                    color = (0, 200, 255, 120)
                elif effect == "sword":
                    color = (255, 80, 80, 120)
                else:
                    color = (80, 255, 80, 120)

                gates.append(Gate(y, effect, color))

        if sword_timer >= 1500:
            sword_timer = 0
            attacks.append(AttackItem("sword", player, len(attacks)))

        if arrow_timer >= 500:
            arrow_timer = 0
            attacks.append(AttackItem("arrow", player, 0))

        player.update()

        for gate in gates[:]:
            gate.update()
            if player.rect.colliderect(gate.rect):
                if gate.effect == "hp":
                    player.hp += 1
                elif gate.effect == "sword":
                    player.sword_atk += 1
                elif gate.effect == "arrow":
                    player.arrow_atk += 1
                gates.clear()

        for atk in attacks[:]:
            atk.update(enemies)
            if atk.kind == "arrow" and atk.rect.left > WIDTH:
                attacks.remove(atk)

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
                    if atk.kind == "arrow":
                        enemy.hp -= max(1, player.arrow_atk)
                    else:
                        enemy.hp -= player.sword_atk

                    if atk.kind == "sword":
                        attacks.remove(atk)

                    if enemy.hp <= 0:
                        enemies.remove(enemy)

        screen.blit(bg, (0, 0))
        for gate in gates:
            gate.draw(screen)
        for atk in attacks:
            atk.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)

        screen.blit(
            font.render(
                f"HP:{player.hp}  剣:{player.sword_atk}  矢:{player.arrow_atk}",
                True, WHITE),
            (20, 20)
        )

        if player.hp <= 0:
            pg.mixer.music.stop()
            gameover_se.play()
            screen.blit(font.render("GAME OVER", True, RED),
                        (WIDTH // 2 - 80, HEIGHT // 2))
            pg.display.update()
            pg.time.wait(3000)
            return

        pg.display.update()


if __name__ == "__main__":
    pg.init()
    stage2(pg.display.set_mode((WIDTH, HEIGHT)))
    pg.quit()
    sys.exit()
