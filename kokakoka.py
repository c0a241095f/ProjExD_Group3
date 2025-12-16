import math
import os
import random
import sys
import time
import pygame as pg

BG_SCROLL_SPEED = 5
WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }
    
    state = "null"  # 状態の変数
    hyper_life = "null"  # 発動時間の変数

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): img,  # 右上
            (0, -1): img,  # 上
            (-1, -1): img,  # 左上
            (-1, 0): img,  # 左
            (-1, +1): img,  # 左下
            (0, +1): img,  # 下
            (+1, +1): img,  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 5

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":  # ハイパーモード中の処理
            self.hyper_life -= 1  # 持続時間を減算
            self.image = pg.transform.laplacian(self.image)  # ハイパーモードのエフェクト
            screen.blit(self.image, self.rect)
            if self.hyper_life < 0:  # 持続時間が0になったら
                self.state = "normal"  # ハイパーモード終了
                self.hyper_life = "normal"  # 持続時間リセット
                self.image = self.imgs[self.dire]  # 通常モードの画像に戻す
                screen.blit(self.image, self.rect)  # こうかとんを画面に転送
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.emp_hit = False

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = 0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    右端から出現し、背景と同じ速度で左へ流れる敵
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()

        # 右端固定、上下ランダム
        self.rect.left = WIDTH
        self.rect.centery = random.randint(self.rect.height // 2,HEIGHT - self.rect.height // 2)

        self.vx = BG_SCROLL_SPEED

        # 爆弾投下間隔（既存ロジックを活かす）
        self.interval = random.randint(50, 300)

    def update(self):
        """
        背景と同じ速度で左へ移動
        """
        self.rect.x -= self.vx

        # 画面外に出たら削除
        if self.rect.right < 0:
            self.kill()


class Shield(pg.sprite.Sprite):
    """
    防御壁（青い矩形）
    - 幅: 20
    - 高さ: こうかとんの身長の2倍
    - 発動時間: life フレーム（0未満で自壊）
    - こうかとんの向き（bird.dire）に合わせて回転し、前方へ1体分ずらして配置
    """
    def __init__(self, bird: "Bird", life: int):
        super().__init__()
        self.bird = bird
        self.life = life

        # 手順1：幅・高さを指定した空のSurface
        base_w = 20
        base_h = bird.rect.height * 2
        self.base_image = pg.Surface((base_w,base_h))

        # 手順2：矩形を描画（青、少し半透明）
        pg.draw.rect(
            self.base_image,
            (0,0,255),  # RGB
            (0, 0, base_w, base_h)
        )

        vx, vy = self.bird.dire  # 手順3
        
        # 回転後の rect を新規に取得
    
        self.rect = self.image.get_rect()

        # 手順6：向き方向に1体分ずらす（距離はこうかとんサイズ基準）
        # ずらし量（こうかとん1体分）
        offset_len = max(self.bird.rect.width, self.bird.rect.height)

        # 正規化方向ベクトル（vx, vy は -1,0,1 なので正規化しておくと拡張に強い）
        norm = math.hypot(vx, vy)
        dx = vx / norm if norm != 0 else 1.0
        dy = vy / norm if norm != 0 else 0.0

        # こうかとん中心から前方へ offset_len ずらした位置
        cx = self.bird.rect.centerx + dx * offset_len
        cy = self.bird.rect.centery + dy * offset_len

        self.rect.center = (cx, cy)

    def update(self):
        """
        - こうかとんの現在の向きに追従して回転・位置を再計算
        - 寿命 life を1減算、0未満で自壊
        """
    
        self.life -= 1
        if self.life < 0:
            self.kill()
        


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 1000
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
        

class EMP(pg.sprite.Sprite):
    """
    EMPで敵の動きを阻害するクラス
    """
    def __init__(self, emys, bombs):
        super().__init__()

        # 画面全体に黄色の半透明フィルタ（0.05秒）
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill((255, 255, 0, 120))   # 半透明の黄色
        self.rect = self.image.get_rect()
        self.life = 3   # 50fps × 3 ≒ 0.06秒

        # 敵機：爆弾投下不能 + ラプラシアン
        for emy in emys:
            emy.interval = math.inf
            emy.image = pg.transform.laplacian(emy.image)

        # 爆弾：速度低下 + 起爆せず消滅
        for bomb in bombs:
            bomb.speed = 2
            bomb.emp_hit = True   # フラグを立てる

    def update(self, screen):
        self.life -= 1
        screen.blit(self.image, self.rect)
        if self.life < 0:
            self.kill()


class Gravity(pg.sprite.Sprite):
     def __init__(self,life):
        super().__init__()
        
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0,0,0),(0, 0,WIDTH, HEIGHT))
        self.rect = self.image.get_rect()

        self.image.set_alpha(192)
        self.life=life

     def update(self):

        self.life -= 1
 
        if self.life < 0:
            self.kill()


def main():
    beam_time = 20
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    bg_img2 = pg.transform.flip(bg_img, True, False)
    score = Score()
    

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    emps = pg.sprite.Group()
    gravities=pg.sprite.Group()
    shields = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if score.value >= 20 and event.type == pg.KEYDOWN and event.key == pg.K_e:
                score.value -= 20
                emps.add(EMP(emys, bombs))
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bird.speed = 10
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:
                bird.speed = 5
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200:
                    gravities.add(Gravity(life=400))
                    score.value-=200

            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                # 発動条件：スコアが50より大、既に防御壁が存在しない
                if score.value >= 50 and len(shields) == 0:
                    shields.add(Shield(bird, life=400))  # 発動時間：400フレーム
                    score.value -= 50  # 消費スコア：50
        x = tmr * BG_SCROLL_SPEED % 3200
        screen.blit(bg_img, [-x, 0])
        screen.blit(bg_img2, [-x+1600, 0])
        screen.blit(bg_img, [-x+3200, 0])
            

        

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())
        
        if tmr%beam_time == 0:
            beams.add(Beam(bird))

        for emy in emys:
            if tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))


        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs,gravities,True,False).keys():#追加機能2
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for emy in pg.sprite.groupcollide(emys,gravities,True,False).keys():#追加機能2
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
            

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
                continue  # ハイパーモード中は無敵
            if bomb.emp_hit == True:
                continue
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            # return
        if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value >= 100:  # 右シフトキーが押下され，スコアが100以上の場合
            if bird.state == "hyper":
                continue  # すでにハイパーモード中なら何もしない
            bird.state ="hyper"  # ハイパーモードに移行
            score.value -= 100  # スコアを100ずつ減少
            bird.hyper_life = 500  # ハイパーモードの持続時間(500フレーム)
            bird.update(key_lst, screen)
        else:
            bird.update(key_lst, screen)
        for bomb in pg.sprite.groupcollide(shields,bombs,False,True):
            exps.add(Explosion(bomb,50))
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        gravities.update()
        gravities.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        emps.update(screen)
        emps.draw(screen)
        
        shields.update()
        shields.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50 + tmr*0.01)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()