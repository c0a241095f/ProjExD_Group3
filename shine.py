import os
import pygame as pg
import sys
import random
import subprocess

# --- 設定（数字を変えるとゲームバランスが変わります） ---
WIDTH = 600             # 画面の幅
HEIGHT = 800            # 画面の高さ
FPS = 60                # 1秒間のコマ数
GATES_PER_ROUND = 7     # 1周で出るゲートの数
GATE_SPAWN_TIME = 90    # ゲートが出る間隔（フレーム数。60で約1秒）

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
PURPLE = (200, 0, 200)

# ゲームの状態（わかりやすいように文字列で管理）
STATE_RUNNING = "RUNNING" # 走るパート
STATE_BOSS = "BOSS"       # ボス戦パート
STATE_RESULT = "RESULT"   # 結果パート

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, "fig")

class Koukaton(pg.sprite.Sprite):
    """自軍（こうかとん）を管理するクラス"""
    def __init__(self):
        super().__init__()
        # 画像の読み込み（失敗したら赤色の四角にする）
        self.image = pg.Surface((50, 50))
        self.image.fill(RED)
        try:
            self.image = pg.image.load("fig/3.png")
            self.image = pg.transform.scale(self.image, (50, 50))
        except:
            pass # 画像がなくてもエラーにしない

        self.rect = self.image.get_rect()
        self.reset_position() # 初期位置へ
        
        self.speed = 8
        self.count = 1  # 自軍の数
        self.swarm_offsets = [] # 群衆の座標リスト
        self.small_image = pg.transform.scale(self.image, (30, 30))

    def reset_position(self):
        """画面の下側・中央に戻す"""
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 100

    def update(self, game_state):
        """毎フレームの処理"""
        # ボス戦のとき：自動で画面中央へ寄せる
        if game_state == STATE_BOSS:
            if self.rect.centerx < WIDTH // 2:
                self.rect.centerx += 2
            elif self.rect.centerx > WIDTH // 2:
                self.rect.centerx -= 2
            return

        # 通常のとき：キーボードで左右移動
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pg.K_RIGHT]:
            self.rect.x += self.speed
        
        # 画面からはみ出さないようにする
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH

        # 群衆の見た目を更新
        self.update_swarm_positions()

    def update_swarm_positions(self):
        """自軍の数に合わせて、わらわら表示させる座標を決める"""
        display_count = self.count
        if display_count > 200: # 処理落ち防止のため上限を設定
            display_count = 200

        # 足りない分を追加
        while len(self.swarm_offsets) < display_count:
            # 数が増えるほど広がる計算（mathを使わず簡易的に）
            spread = 20 + (display_count // 5) 
            rx = random.randint(-spread, spread)
            ry = random.randint(-spread, spread)
            self.swarm_offsets.append((rx, ry))
        
        # 多すぎる分を削除
        while len(self.swarm_offsets) > display_count:
            self.swarm_offsets.pop()

    def apply_effect(self, operator, value):
        """ゲートを通ったときの計算"""
        if operator == "+":
            self.count += value
        elif operator == "x":
            self.count *= value
        elif operator == "-":
            self.count -= value
        elif operator == "/":
            self.count //= value # 割り算（整数）
        
        if self.count < 0:
            self.count = 0

    def draw_swarm(self, screen):
        """群衆を描画する"""
        if self.count <= 0: return
        # offsetsに保存されたズレを使って描画
        for ox, oy in self.swarm_offsets:
            draw_x = self.rect.centerx + ox - 15
            draw_y = self.rect.centery + oy - 15
            screen.blit(self.small_image, (draw_x, draw_y))


class Gate(pg.sprite.Sprite):
    """通ると数が増減するゲートのクラス"""
    def __init__(self, x, y, width, height, batch_id):
        super().__init__()
        self.batch_id = batch_id # 左右ペアを識別するID
        
        # ランダムに計算の種類を決める
        self.operator = random.choice(["+", "x", "-", "+", "x"]) 
        if self.operator == "+" or self.operator == "-":
            self.value = random.randint(10, 50)
        else: 
            self.value = random.randint(1, 3)

        # 良い効果なら青、悪い効果なら赤
        is_good = (self.operator == "+" or self.operator == "x")
        color = BLUE if is_good else RED
        
        # 画像を作る
        self.image = pg.Surface((width, height))
        self.image.fill(color)
        self.image.set_alpha(150) # 半透明にする

        # 文字を描く
        font = pg.font.SysFont("arial", 40, bold=True)
        text = font.render(f"{self.operator}{self.value}", True, WHITE)
        # 真ん中に配置
        text_rect = text.get_rect(center=(width // 2, height // 2))
        self.image.blit(text, text_rect)
        
        # 白い枠線
        pg.draw.rect(self.image, WHITE, (0, 0, width, height), 5)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        """下に落ちる処理"""
        self.rect.y += 5
        # 画面外に出たら消える
        if self.rect.top > HEIGHT:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """ボスのクラス"""
    def __init__(self, level=1):
        super().__init__()
        self.image = pg.Surface((150, 150))
        # 画像読み込み
        try:
            img = pg.image.load("fig/21.png") # ボス画像
            self.image = pg.transform.scale(img, (150, 150))
        except:
            self.image.fill(PURPLE) # 画像がなければ紫の四角
            font = pg.font.SysFont(None, 80)
            text = font.render("BOSS", True, WHITE)
            self.image.blit(text, (10, 50))
            pg.draw.rect(self.image, WHITE, (0,0,150,150), 5)

        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = -50 
        
        # レベルに応じてHPを決める（周回するたびに強くなる）
        min_hp = 500 + (level-1) * 500
        max_hp = 1000 + (level-1) * 10000
        self.hp = random.randint(min_hp, max_hp)

    def update(self):
        """下に降りてくる処理"""
        if self.rect.top < HEIGHT: 
            self.rect.y += 4

    def draw_hp(self, screen, font):
        """HPを表示する"""
        text = font.render(f"BOSS HP: {self.hp}", True, RED)
        # 背景を黒くして見やすくする
        bg_rect = text.get_rect(center=(self.rect.centerx, self.rect.top - 20))
        pg.draw.rect(screen, BLACK, bg_rect)
        screen.blit(text, bg_rect)

class Advertisement:
    """
    Advertisement の Docstring
    """
    def __init__(self):
        self.img = pg.Surface((WIDTH//2, HEIGHT))  #広告を載せる用の背景
        self.img.fill((128, 128, 128))
        self.img.set_alpha(200)
        try:
            self.imgx = pg.image.load(os.path.join(FIG_DIR, "bb.png"))
            self.imgx = pg.transform.rotozoom(self.imgx, 0, 0.25)
        except:
            self.surx = pg.Surface((64, 64))
            self.surx.fill((255, 0, 0))

        self.imgx_rct = self.imgx.get_rect()

        self.surx = pg.Surface((64, 64))
        self.surx.fill((255, 0, 0))
        self.surx_rct = self.surx.get_rect()
        self.surx_rct.topleft = ((WIDTH/4 + WIDTH/2) - 72, 0)

    def update(self, screen: pg.Surface):
        """
        update の Docstring
        
        :param self: 説明
        :param screen: 説明
        :type screen: pg.Surface
        """
        screen.blit(self.img, [WIDTH/4, 0])
        screen.blit(self.surx, self.surx_rct)
        screen.blit(self.imgx, self.surx_rct)
        
def main():
    def reset_game():
        player = Koukaton()
        enemy = Enemy(1)
        gates = pg.sprite.Group()
        all_sprites = pg.sprite.Group()

        all_sprites.add(player)

        return {
            "player": player,
            "enemy": enemy,
            "gates": gates,
            "all_sprites": all_sprites,
            "level": 1,
            "game_state": STATE_RUNNING,
            "spawned_gates": 0,
            "passed_gates": 0,
            "gate_timer": 0,
            "batch_counter": 0,
            "result_start_time": 0,
            "is_win": False,
        }
    
    game = reset_game()
    player = game["player"]
    enemy = game["enemy"]
    gates = game["gates"]
    all_sprites = game["all_sprites"]

    level = game["level"]
    game_state = game["game_state"]
    spawned_gates = game["spawned_gates"]
    passed_gates = game["passed_gates"]
    gate_timer = game["gate_timer"]
    batch_counter = game["batch_counter"]
    result_start_time = game["result_start_time"]
    is_win = game["is_win"]

    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("ラストコカー・コカー")
    clock = pg.time.Clock()
    
    # フォントの準備
    font = pg.font.SysFont("mspgothic", 30)
    big_font = pg.font.SysFont("arial", 60, bold=True)

    # スプライトをまとめるグループ
    all_sprites = pg.sprite.Group()
    gates = pg.sprite.Group()
    
    # プレイヤー作成
    player = Koukaton()
    
    # ゲーム管理用の変数
    level = 1
    enemy = Enemy(level)
    game_state = STATE_RUNNING
    
    spawned_gates = 0    # 出したゲートの数
    passed_gates = 0     # 通過したゲートの数
    
    gate_timer = 0       # 時間を数える変数
    batch_counter = 0    # ゲートペアのID
    
    result_start_time = 0 # 結果画面が出た時間
    is_win = False

    advertisement = Advertisement()

    while True:
        # --- イベント処理（×ボタンで終了） ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if advertisement.surx_rct.collidepoint(event.pos):
                        game = reset_game()
                        player = game["player"]
                        enemy = game["enemy"]
                        gates = game["gates"]
                        all_sprites = game["all_sprites"]

                        level = game["level"]
                        game_state = game["game_state"]
                        spawned_gates = game["spawned_gates"]
                        passed_gates = game["passed_gates"]
                        gate_timer = game["gate_timer"]
                        batch_counter = game["batch_counter"]
                        result_start_time = game["result_start_time"]
                        is_win = game["is_win"]

        # --- ゲートを出す処理 ---
        if game_state == STATE_RUNNING:
            gate_timer += 1 # 時間を進める
            
            # 一定時間経過 かつ まだ出し切っていない場合
            if gate_timer > GATE_SPAWN_TIME and spawned_gates < GATES_PER_ROUND:
                gate_timer = 0 # タイマーリセット
                batch_counter += 1
                
                # 左のゲート
                gate_l = Gate(5, -100, WIDTH//2 - 10, 80, batch_counter)
                gates.add(gate_l)
                all_sprites.add(gate_l)

                # 右のゲート
                gate_r = Gate(WIDTH//2 + 5, -100, WIDTH//2 - 10, 80, batch_counter)
                gates.add(gate_r)
                all_sprites.add(gate_r)
                
                spawned_gates += 1

        # --- ボス出現チェック ---
        if game_state == STATE_RUNNING:
            # ゲートを全部通過した、または全部出し終わって画面から消えたらボスへ
            if passed_gates >= GATES_PER_ROUND or (spawned_gates >= GATES_PER_ROUND and len(gates) == 0):
                game_state = STATE_BOSS
                all_sprites.add(enemy) # ボスを画面に追加

        # --- 更新処理 ---
        if game_state == STATE_RUNNING or game_state == STATE_BOSS:
            player.update(game_state)
            all_sprites.update()
        
        # --- 当たり判定（プレイヤー vs ゲート） ---
        if game_state == STATE_RUNNING:
            hits = pg.sprite.spritecollide(player, gates, True) # ぶつかったら消える
            if hits:
                passed_gates += 1
                for gate in hits:
                    player.apply_effect(gate.operator, gate.value)
                    # ペアのもう片方も消す
                    for other in gates:
                        if other.batch_id == gate.batch_id:
                            other.kill()

        # --- 当たり判定（プレイヤー vs ボス） ---
        if game_state == STATE_BOSS:
            if pg.sprite.collide_rect(player, enemy):
                game_state = STATE_RESULT
                result_start_time = pg.time.get_ticks()
                # 数がボスのHP以上なら勝ち
                if player.count >= enemy.hp:
                    is_win = True
                else:
                    is_win = False

        # --- 全滅判定 ---
        if game_state != STATE_RESULT and player.count <= 0:
            game_state = STATE_RESULT
            result_start_time = pg.time.get_ticks()
            is_win = False # 負け

        # --- 描画処理 ---
        screen.fill(BLACK) # 背景を黒にする
        
        # 縦線を描く
        pg.draw.line(screen, (50, 50, 50), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 2)
        
        all_sprites.draw(screen)   # ゲートやボスを描画
        player.draw_swarm(screen)  # 自軍を描画

        # 文字情報の表示
        info_text = font.render(f"自軍: {player.count} (Lv.{level})", True, WHITE)
        screen.blit(info_text, (player.rect.centerx + 60, player.rect.bottom))
        
        gate_text = font.render(f"GATE: {passed_gates}/{GATES_PER_ROUND}", True, (200, 200, 200))
        screen.blit(gate_text, (10, 50))

        # ボスのHP表示
        if game_state == STATE_BOSS or game_state == STATE_RESULT:
            if enemy.alive():
                enemy.draw_hp(screen, font)
        
        # 進行バーの表示
        if game_state == STATE_RUNNING:
            ratio = passed_gates / GATES_PER_ROUND
            if ratio > 1.0: ratio = 1.0
            
            # バーの枠
            pg.draw.rect(screen, WHITE, (100, 20, 400, 20), 2)
            # 中身（青色）
            pg.draw.rect(screen, BLUE, (100, 20, 400 * ratio, 20))

        # --- 結果画面 ---
        if game_state == STATE_RESULT:
            # 画面を少し暗くする
            overlay = pg.Surface((WIDTH, HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))

            if is_win:
                msg = big_font.render("YOU WIN!", True, BLUE)
                detail = font.render(f"現こうかとん: {player.count - enemy.hp}ひき", True, WHITE)
                next_msg = font.render("Next Round...", True, WHITE)
            else:
                if player.count <= 0:
                    msg = big_font.render("GAME OVER", True, RED)
                    detail = font.render("lose...", True, WHITE)
                else:
                    msg = big_font.render("YOU LOSE...", True, RED)
                    detail = font.render(f" 最終結果{enemy.hp - player.count}ひき", True, WHITE)
                next_msg = font.render("", True, WHITE)

            # 文字を画面中央に配置
            screen.blit(msg, (WIDTH//2 - 150, HEIGHT//2 - 50))
            screen.blit(detail, (WIDTH//2 - 100, HEIGHT//2 + 20))
            screen.blit(next_msg, (WIDTH//2 - 80, HEIGHT//2 + 60))

            # 3秒経過後の処理
            if pg.time.get_ticks() - result_start_time > 3000:
                if is_win:
                    # 次のラウンドへ進む処理
                    player.count -= enemy.hp # コストを払う
                    if player.count < 1: player.count = 1
                    level += 1
                    
                    # 状態をリセット
                    game_state = STATE_RUNNING
                    spawned_gates = 0
                    passed_gates = 0
                    gate_timer = 0
                    
                    player.reset_position() # プレイヤー位置リセット
                    enemy.kill()            # 今のボスを消す
                    gates.empty()           # ゲートを全部消す
                    all_sprites.empty()     # グループを空にする
                    
                    enemy = Enemy(level)    # 新しいボスを作る
                else:
                    advertisement.update(screen)
                    pg.display.update()
                    pg.time.wait(20000)
                    pg.quit()
                    sys.exit()

        pg.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()