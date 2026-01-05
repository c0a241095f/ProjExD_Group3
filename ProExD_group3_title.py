import math
import os
import random
import subprocess
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650

os.chdir(os.path.dirname(os.path.abspath(__file__)))

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def main():
    pg.display.set_caption("ラストコカー・コカー")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    try:
        pg.mixer.music.load("fig/Ethan Meixsell - Thor's Hammer.mp3") # ファイル名
        pg.mixer.music.set_volume(0.5)          # 音量調節 (0.0 ～ 1.0)
        pg.mixer.music.play(-1)                 # -1 を指定すると無限ループ再生
    except pg.error:
        print("BGMファイルが見つかりません。")

    # フォント
    # フォント（SysFont・日本語対応）
    title_font = pg.font.SysFont("meiryo",72)
    stage_font = pg.font.SysFont("meiryo",18)

    # タイトル文字
    title_text = title_font.render("ラストコカー・コカー", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, 120))

    # ステージ選択枠
    stage1_rect = pg.Rect(300, 300, 180, 100)
    stage2_rect = pg.Rect(600, 300, 180, 100)

    # 背景として使う
    military_bg_img = pg.image.load("fig/militaly.png").convert() 
    arrow_bg_img = pg.image.load("fig/arrow_bg.png").convert()

    HALF_WIDTH = WIDTH // 2
    # 画面の左半分にフィットするようにリサイズ (1100 / 2 = 550)
    military_bg_img = pg.transform.scale(military_bg_img, (HALF_WIDTH, HEIGHT))
    # 画面の右半分にフィットするようにリサイズ
    arrow_bg_img = pg.transform.scale(arrow_bg_img, (HALF_WIDTH, HEIGHT))
    
    #（配置座標）
    military_bg_rect = military_bg_img.get_rect(topleft=(0, 0))              # 左上の (0, 0) から開始
    arrow_bg_rect = arrow_bg_img.get_rect(topleft=(HALF_WIDTH, 0))
    
    # ステージ文字
    stage1_text = stage_font.render("ミリタリーモード", True, WHITE)
    stage2_text = stage_font.render("アローモード", True, WHITE)
    # ステージ文字
    stage1_text = stage_font.render("ラストコカー", True, WHITE)
    stage2_text = stage_font.render("コカー・コカー", True, WHITE)
    stage1_text_rect = stage1_text.get_rect(center=stage1_rect.center)
    stage2_text_rect = stage2_text.get_rect(center=stage2_rect.center)

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            # クリック処理
            if event.type == pg.MOUSEBUTTONDOWN:
                if stage1_rect.collidepoint(event.pos):
                    pg.mixer.music.stop()  #ゲーム開始前にBGMを止める
                    pg.quit()
                    subprocess.run([sys.executable, "shine.py"])
                    sys.exit()
                    militaly_mode.run_military_mode(screen)  # STAGE 1 をクリックした時の処理を書く
                    pg.mixer.music.play(-1) # ゲームから戻ってきたら再度再生
                if stage2_rect.collidepoint(event.pos):
                    pg.quit()  # pygameを終了
                    subprocess.run([sys.executable, "kokakoka.py"])
                    pg.mixer.music.stop()  #ゲーム開始前にBGMを止める
                    sys.exit()
                    pg.mixer.music.play(-1) # ゲームから戻ってきたら再度再生
        # 描画
        screen.blit(military_bg_img, military_bg_rect)
        screen.blit(arrow_bg_img, arrow_bg_rect)
        screen.blit(title_text, title_rect)

        pg.draw.rect(screen, WHITE, stage1_rect, 2)
        pg.draw.rect(screen, WHITE, stage2_rect, 2)

        screen.blit(stage1_text, stage1_text_rect)
        screen.blit(stage2_text, stage2_text_rect)

        pg.display.update()


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
