import os
import pygame as pg
import sys
import random
import math

# 画像などを読み込みやすくするため、実行ファイルのディレクトリを作業場所に設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

# ゲームの状態
STATE_RUNNING = "RUNNING" # 走るパート
STATE_BOSS = "BOSS"       # ボス戦パート
STATE_RESULT = "RESULT"   # 結果パート


class Koukaton(pg.sprite.Sprite):
    """自軍（こうかとん）を管理するクラス"""
    def __init__(self):
        super().__init__()
        # 基本画像の読み込み（失敗したら赤色の四角にする）
        self.image = pg.Surface((50, 50))
        self.image.fill(RED)
        self.load_image("3.png") # 初期画像

        self.rect = self.image.get_rect()
        self.reset_position() # 初期位置へ
        
        self.speed = 8
        self.count = 1  # 自軍の数
        self.swarm_offsets = [] # 群衆の座標リスト
        self.small_image = pg.transform.scale(self.image, (30, 30))

    def load_image(self, filename):
        """画像を読み込む関数（エラー回避付き）"""
        try:
            # figフォルダにある場合と直下にある場合の両方を考慮
            if os.path.exists(filename):
                img = pg.image.load(filename)
            elif os.path.exists(f"fig/{filename}"):
                img = pg.image.load(f"fig/{filename}")
            else:
                return # 画像がない場合は何もしない（赤い四角のまま）
            
            self.image = pg.transform.scale(img, (50, 50))
            self.small_image = pg.transform.scale(img, (30, 30))
        except:
            pass

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
            # 数が増えるほど広がる計算
            spread = 20 + (display_count // 5) 
            rx = random.randint(-spread, spread)
            ry = random.randint(-spread, spread)
            self.swarm_offsets.append((rx, ry))
        
        # 多すぎる分を削除
        while len(self.swarm_offsets) > display_count:
            self.swarm_offsets.pop()

    def apply_effect(self, operator, value):
        """ゲートを通ったときの計算と画像変更（1つ目のコードの機能）"""
        if operator == "+":
            self.count += value
            self.load_image("6.png") # 増えたら笑顔
        elif operator == "x":
            self.count *= value
            self.load_image("6.png") # 増えたら笑顔
        elif operator == "-":
            self.count -= value
            self.load_image("8.png") # 減ったら泣き顔
        elif operator == "/":
            self.count //= value
            self.load_image("8.png") # 減ったら泣き顔
        
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
    def __init__(self, x, y, width, height, pair_id):
        super().__init__()
        self.pair_id = pair_id # 左右ペアを識別するID（1つ目のコードの機能）
        self.width = width
        self.height = height
        
        # ランダムに計算の種類を決める
        self.operator = random.choice(["+", "+", "+", "-", "-", "x", "/"]) 
        
        if self.operator in ["+", "-"]:
            self.value = random.randint(5, 50)
        else: # x, /
            self.value = random.randint(2, 5)

        # 良い効果なら青、悪い効果なら赤
        is_good = False
        if self.operator == "+" or self.operator == "x":
            is_good = True
        
        self.color = BLUE if is_good else RED
        
        # 画像を作る
        self.image = pg.Surface((width, height))
        self.image.fill(self.color)
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
            # fig/21.png を優先的に探す
            if os.path.exists("fig/21.png"):
                img = pg.image.load("fig/21.png")
            elif os.path.exists("21.png"):
                img = pg.image.load("21.png")
            else:
                raise FileNotFoundError
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
        min_hp = 500 + (level - 1) * 500
        max_hp = 1000 + (level - 1) * 1000
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


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("ラストコカー・コカー（統合版）")
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
    
    result_start_time = 0 # 結果画面が出た時間
    is_win = False

    while True:
        # --- イベント処理（×ボタンで終了） ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

        # --- ゲートを出す処理 ---
        if game_state == STATE_RUNNING:
            gate_timer += 1 # 時間を進める
            
            # 一定時間経過 かつ まだ出し切っていない場合
            if gate_timer > GATE_SPAWN_TIME and spawned_gates < GATES_PER_ROUND:
                gate_timer = 0 # タイマーリセット
                
                # ペアIDを生成（1つ目のコードの機能）
                pair_id = random.randint(0, 999999)

                # 左のゲート
                gate_l = Gate(5, -100, WIDTH//2 - 10, 80, pair_id)
                gates.add(gate_l)
                all_sprites.add(gate_l)

                # 右のゲート
                gate_r = Gate(WIDTH//2 + 5, -100, WIDTH//2 - 10, 80, pair_id)
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
            # 1つ目のコードの当たり判定ロジックを使用
            hits = pg.sprite.spritecollide(player, gates, False) # まだ消さない
            if hits:
                passed_gates += 1
                
                # 選ばれたゲートを決定（2つ同時に当たったら左優先）
                if len(hits) == 1:
                    chosen_gate = hits[0]
                else:
                    chosen_gate = min(hits, key=lambda g: g.rect.x)
                
                # 効果を適用（画像変更含む）
                player.apply_effect(chosen_gate.operator, chosen_gate.value)
                
                # 選んだゲートを消す
                chosen_gate.kill()
                
                # ペアのもう片方も消す
                for other in gates:
                    if other.pair_id == chosen_gate.pair_id and other != chosen_gate:
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
        player.draw_swarm(screen)  # 自軍（わらわら）を描画

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
                    detail = font.render("All Dead...", True, WHITE)
                else:
                    msg = big_font.render("YOU LOSE...", True, RED)
                    detail = font.render(f"最終結果 {enemy.hp - player.count}ひき不足", True, WHITE)
                next_msg = font.render("", True, WHITE)

            # 文字を画面中央に配置
            screen.blit(msg, (WIDTH//2 - 150, HEIGHT//2 - 50))
            screen.blit(detail, (WIDTH//2 - 150, HEIGHT//2 + 20))
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
                    
                    player.reset_position() 
                    # 新しいラウンドでは初期画像に戻す
                    player.load_image("3.png")

                    enemy.kill()            # 今のボスを消す
                    gates.empty()           # ゲートを全部消す
                    all_sprites.empty()     # グループを空にする
                    
                    enemy = Enemy(level)    # 新しいボスを作る
                else:
                    pg.quit() # ゲーム終了
                    sys.exit()

        pg.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()