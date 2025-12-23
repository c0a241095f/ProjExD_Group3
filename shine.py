import os
import pygame as pg
import sys
import random

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数設定 ---
WIDTH, HEIGHT = 600, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255) # プラス効果の色
RED = (255, 50, 50)  # マイナス効果の色
GREEN = (0, 200, 0)

# ゲームモード定数
MODE_ARROW = "ARROW"       # 装備強化モード
MODE_MILITARY = "MILITARY" # 増殖モード

# 現在のモード設定（ここを書き換えるとゲームが変わります）
# CURRENT_MODE = MODE_ARROW 
CURRENT_MODE = MODE_MILITARY

class Koukaton(pg.sprite.Sprite):
    """
    こうかとん（プレイヤー）クラス
    """
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.image = pg.Surface((50, 50))
        self.image.fill((255, 0, 0)) # 画像がない場合の赤色
        
        # 画像読み込み試行
        try:
            img = pg.image.load("3.png")
            self.image = pg.transform.scale(img, (50, 50))
        except FileNotFoundError:
            pass

        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 50
        self.speed = 8
        
        # モードごとのステータス
        if self.mode == MODE_ARROW:
            self.power = 1 # 装備レベル
        else:
            self.count = 1 # こうかとんの数（残機）

    def update(self):
        """
        左右移動の制御
        """
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pg.K_RIGHT]:
            self.rect.x += self.speed
        
        # 画面外に出ないように制限
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def apply_effect(self, operator, value):
        """
        ゲート通過時の効果適用
        """
        if self.mode == MODE_MILITARY:
            # ミリタリーモード：数の増減
            #POINT4 こうかとんの表情の画像
            if operator == "+":
                self.count += value
                img = pg.image.load("6.png")
                self.image = pg.transform.scale(img, (50, 50))

            elif operator == "x":
                self.count *= value
                img = pg.image.load("6.png")
                self.image = pg.transform.scale(img, (50, 50))
            elif operator == "-":
                self.count -= value
                img = pg.image.load("8.png")
                self.image = pg.transform.scale(img, (50, 50))
            elif operator == "/":
                self.count //= value
                img = pg.image.load("8.png")
                self.image = pg.transform.scale(img, (50, 50))
            
            # 0未満にならないように
            if self.count < 0: self.count = 0
            
        elif self.mode == MODE_ARROW:
            # アローモード：装備（攻撃力）の増減
            if operator == "+" or operator == "x":
                # 増える場合は単純に強化
                if operator == "+": self.power += 1
                if operator == "x": self.power += value
            else:
                if operator == "-": self.power -= 1
                if operator == "/": self.power -= value
                
            
            if self.power < 1: self.power = 1


class Gate(pg.sprite.Sprite):
    """
    通過すると数値が変動するゲートクラス
    """
    def __init__(self, x, y, width, height,pair_id):
        super().__init__()
        self.width = width
        self.height = height
        self.pair_id = pair_id   # ← POINT1 ゲートID

        
        # ランダムな演算と値を生成
        self.operator = random.choice(["+","+", "+", "-", "-", "x","/"]) # 出てくるもの調整可能
        
        
        if self.operator in ["+", "-"]:
            self.value = random.randint(5, 50)
        else: # x (掛け算) /(割り算)
            self.value = random.randint(2, 5)

        # 良い効果（青）か悪い効果（赤）か判定
        is_good = False
        if self.operator == "+" or self.operator == "x":
            is_good = True
        elif self.operator == "-" or self.operator == "/":
            is_good = False
        
        self.color = BLUE if is_good else RED
        
        # 画像（サーフェス）の作成
        self.image = pg.Surface((width, height))
        self.image.fill(self.color)
        self.image.set_alpha(150) # 半透明にする

        # テキスト描画
        font = pg.font.SysFont("arial", 40, bold=True)
        text_str = f"{self.operator}{self.value}"
        text_surf = font.render(text_str, True, WHITE)
        
        # テキストを中央に配置
        text_rect = text_surf.get_rect(center=(width // 2, height // 2))
        self.image.blit(text_surf, text_rect)
        
        # 枠線を描く
        pg.draw.rect(self.image, WHITE, (0, 0, width, height), 5)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.speed_y = 5# 落下速度

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()


class Bullet(pg.sprite.Sprite):
    """
    アローモード用の弾
    """
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((10, 20))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 10

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption(f"ラストコカー・コカー [{CURRENT_MODE} MODE]")
    clock = pg.time.Clock()
    font = pg.font.SysFont("mspgothic", 30)

    # スプライトグループの作成
    all_sprites = pg.sprite.Group()
    gates = pg.sprite.Group()
    bullets = pg.sprite.Group()

    # プレイヤー生成
    player = Koukaton(CURRENT_MODE)
    all_sprites.add(player)

    # ゲート生成用タイマー
    GATE_SPAWN_EVENT = pg.USEREVENT + 1
    pg.time.set_timer(GATE_SPAWN_EVENT, 1500) # 1.5秒ごとにゲート生成

    # 背景スクロール用変数
    bg_y = 0

    while True:
        # 1. イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            
            # ゲート生成  
            if event.type == GATE_SPAWN_EVENT:
                # 画面を2分割して左右にゲートを出すかランダムに決定
                gate_width = WIDTH // 2 - 10
                
    
                #ゲートにIDを追加する
                pair_id = random.randint(0, 999999)  # ペアIDを生成

                # 左側のゲート
                gate_l = Gate(5, -100, gate_width, 80, pair_id)
                gates.add(gate_l)
                all_sprites.add(gate_l)

                # 右側のゲート
                gate_r = Gate(WIDTH // 2 + 5, -100, gate_width, 80, pair_id)
                gates.add(gate_r)
                all_sprites.add(gate_r)
                
              


        # 2. 更新処理
        all_sprites.update()

        # アローモードの場合、弾を自動発射
        if CURRENT_MODE == MODE_ARROW:
            # 簡易的な連射制御（フレーム数で調整）
            if pg.time.get_ticks() % 10 == 0:
                # 装備レベル(power)に応じて発射数を変えるなどのロジックが可能
                # ここではシンプルに1発
                bullet = Bullet(player.rect.centerx, player.rect.top)
                bullets.add(bullet)
                all_sprites.add(bullet)

        #追加機能　1 and　2
        # 衝突判定：プレイヤーとゲート
        # 衝突したら効果を適用してゲートを消す

        hits = pg.sprite.spritecollide(player, gates, False)  # TrueをFalseにして消さないで判定

        if hits:
            # 両方同時に当たった場合は左を優先
            if len(hits) == 1:
        # 片方だけに当たった場合 → そのゲートだけ適用
                chosen_gate = hits[0]
            else:
        # 両方同時に当たった場合 → 左側を優先
                chosen_gate = min(hits, key=lambda g: g.rect.x)



        # 効果を適用
            player.apply_effect(chosen_gate.operator, chosen_gate.value)

        # 選んだゲートだけ消す
            chosen_gate.kill()

        # 他のゲートは消す（効果は適用しない）
            for g in gates:
                if g.pair_id == chosen_gate.pair_id and g != chosen_gate:
                    g.kill()

        # 3. 描画処理
        screen.fill(BLACK)
        
        # 背景スクロール演出（縦線）
        bg_y = (bg_y + 5) % HEIGHT
        pg.draw.line(screen, (50, 50, 50), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 2)
        for i in range(0, HEIGHT, 100):
            line_y = (bg_y + i) % HEIGHT
            pg.draw.line(screen, (30, 30, 30), (0, line_y), (WIDTH, line_y), 1)

        all_sprites.draw(screen)

        # ステータス表示
        if CURRENT_MODE == MODE_MILITARY:
            info_text = f"こうかとん数: {player.count}"
            # ミリタリーモードなら、こうかとんの上に数を表示
            count_lbl = font.render(f"{player.count}", True, WHITE)
            screen.blit(count_lbl, (player.rect.centerx - 10, player.rect.top - 30))
        else:
            info_text = f"装備レベル: {player.power}"
        
        score_surf = font.render(info_text, True, WHITE)
        screen.blit(score_surf, (10, 10))

        # ゲームオーバー判定（ミリタリーモードで数が0以下になったら等）
        if CURRENT_MODE == MODE_MILITARY and player.count <= 0:
            gameover_text = font.render("GAME OVER", True, RED)
            screen.blit(gameover_text, (WIDTH//2 - 80, HEIGHT//2))
            pg.display.update()
            pg.time.wait(2000)
            return # メインループを抜けて終了

        pg.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()