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

            # クリック処理（中身は後で追加）
            if event.type == pg.MOUSEBUTTONDOWN:
                if stage1_rect.collidepoint(event.pos):
                    return 0  # STAGE 1 をクリックした時の処理を書く
                if stage2_rect.collidepoint(event.pos):
                    pg.quit()  # pygameを終了
                    subprocess.run([sys.executable, "kokakoka.py"])
                    sys.exit()

        # 描画
        screen.fill(BLACK)
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