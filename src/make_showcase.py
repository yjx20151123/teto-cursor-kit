"""生成「鼠标效果图」：把 Teto 光标合成到真实使用场景里，方便展示/参赛截图。
输出到 ../preview/showcase_*.png
"""
import os, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
CUR_DIR = os.path.join(BASE, "..", "cursors")
OUT = os.path.join(BASE, "..", "preview")
os.makedirs(OUT, exist_ok=True)

FONT = "C:/Windows/Fonts/msyh.ttc"
try:
    F = lambda s: ImageFont.truetype(FONT, s)
except Exception:
    F = lambda s: ImageFont.load_default()


def load_best(path):
    raw = open(path, "rb").read()
    raw = raw[:2] + b"\x01\x00" + raw[4:]   # CUR -> ICO，骗过 Pillow
    im = Image.open(io.BytesIO(raw))
    frames = []
    try:
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i); im.load(); frames.append(im.copy().convert("RGBA"))
    except Exception:
        frames = [im.copy().convert("RGBA")]
    if not frames:
        frames = [im.convert("RGBA")]
    return max(frames, key=lambda x: x.size[0] * x.size[1])


def scale(img, px):
    s = px / max(img.size)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


def gradient(w, h, c1, c2):
    arr = np.zeros((h, w, 3), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.linspace(c1[i], c2[i], h).astype(np.uint8)[:, None]
    return Image.fromarray(arr).convert("RGBA")


def caption(img, text, pos, color=(235, 238, 245), size=22, bg=(20, 24, 34, 180)):
    d = ImageDraw.Draw(img)
    f = F(size)
    tw = d.textlength(text, font=f)
    x, y = pos
    d.rounded_rectangle([x - 8, y - 6, x + tw + 8, y + size + 6], radius=8, fill=bg)
    d.text((x, y), text, fill=color, font=f)


# ---------------- 场景1：桌面使用场景 ----------------
def scene_desktop():
    W, H = 1200, 720
    bg = gradient(W, H, (58, 74, 107), (30, 41, 64))
    d = ImageDraw.Draw(bg)
    # 一扇“应用窗口”
    wx, wy, ww, wh = 110, 80, 560, 400
    d.rounded_rectangle([wx, wy, wx + ww, wy + wh], radius=16, fill=(246, 248, 251), outline=(190, 196, 208))
    d.rounded_rectangle([wx, wy, wx + ww, wy + 38], radius=16, fill=(66, 133, 244))
    d.ellipse([wx + ww - 30, wy + 11, wx + ww - 14, wy + 27], fill=(234, 67, 53))
    d.ellipse([wx + ww - 54, wy + 11, wx + ww - 38, wy + 27], fill=(251, 188, 5))
    # 假文本行
    for i in range(7):
        d.rounded_rectangle([wx + 28, wy + 70 + i * 30, wx + ww - 120, wy + 70 + i * 30 + 12],
                            radius=6, fill=(222, 226, 234))
    # 一个按钮
    bx, by, bw, bh = wx + ww - 180, wy + wh - 76, 150, 46
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(52, 199, 123))
    d.text((bx + 30, by + 12), "开始", fill=(255, 255, 255), font=F(22))
    # 在按钮上放“普通选择”箭头光标（热点=箭头尖，置于按钮上）
    arrow = scale(load_best(os.path.join(CUR_DIR, "teto_cursor.cur")), 84)
    bg.alpha_composite(arrow, (bx + 24, by - 6))
    caption(bg, "普通选择 Arrow", (bx - 40, by - 70))
    # 在标题栏文字处放“链接选择”手型
    hand = scale(load_best(os.path.join(CUR_DIR, "teto_hand.cur")), 84)
    bg.alpha_composite(hand, (wx + 40, wy + 110))
    caption(bg, "链接选择 Hand", (wx + 40, wy + 70))
    # 右下角放 IBeam 表示正在打字
    ib = scale(load_best(os.path.join(CUR_DIR, "teto_ibeam.cur")), 84)
    bg.alpha_composite(ib, (wx + 300, wy + 250))
    caption(bg, "文本 IBeam", (wx + 300, wy + 212))
    # 标题
    d.text((40, 28), "重音テト 光标 · 桌面使用效果", fill=(255, 182, 198), font=F(30))
    bg.convert("RGB").save(os.path.join(OUT, "showcase_desktop.png"))
    print("saved showcase_desktop.png")


# ---------------- 场景2：十字光标实战（画图场景 + 热点标注）----------------
def scene_crosshair():
    W, H = 1200, 720
    bg = gradient(W, H, (44, 52, 70), (26, 31, 46))
    d = ImageDraw.Draw(bg)
    # 画布区
    cx, cy, cw, ch = 90, 90, 1020, 560
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=14, fill=(250, 250, 252), outline=(200, 205, 215))
    # 浅色网格
    gd = ImageDraw.Draw(bg)
    for gx in range(cx + 40, cx + cw, 40):
        gd.line([(gx, cy + 10), (gx, cy + ch - 10)], fill=(232, 234, 240), width=1)
    for gy in range(cy + 40, cy + ch, 40):
        gd.line([(cx + 10, gy), (cx + cw - 10, gy)], fill=(232, 234, 240), width=1)
    # 放十字光标（我们只想展示“左上十字+中间Teto”的真实形态）
    ch0 = load_best(os.path.join(CUR_DIR, "teto_crosshair.cur"))
    ch_img = scale(ch0, 220)
    px, py = cx + 560, cy + 250   # 放置位置（左上角对齐）
    bg.alpha_composite(ch_img, (px, py))
    # 标出热点（十字圆点，约画布 9~11% 处）——在同一缩放下估算
    s = 220 / max(ch0.size)
    hx, hy = int(px + 0.10 * 220), int(py + 0.10 * 220)
    gd.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], outline=(0, 150, 255), width=3)
    gd.line([(hx - 40, hy), (hx + 40, hy)], fill=(0, 150, 255), width=2)
    gd.line([(hx, hy - 40), (hx, hy + 40)], fill=(0, 150, 255), width=2)
    caption(bg, "热点 = 十字圆点", (hx + 34, hy - 14), color=(150, 210, 255))
    d.text((40, 28), "精确选择 Crosshair · 实战效果（热点已标蓝）", fill=(255, 182, 198), font=F(28))
    bg.convert("RGB").save(os.path.join(OUT, "showcase_crosshair.png"))
    print("saved showcase_crosshair.png")


# ---------------- 场景3：全套光标铺在桌面上 ----------------
def scene_gallery():
    W, H = 1200, 760
    bg = gradient(W, H, (50, 64, 94), (28, 36, 56))
    d = ImageDraw.Draw(bg)
    d.text((40, 24), "重音テト 光标套装 · 全状态一览", fill=(255, 182, 198), font=F(30))
    items = [
        ("普通选择 Arrow", "teto_cursor.cur"),
        ("链接选择 Hand", "teto_hand.cur"),
        ("文本 IBeam", "teto_ibeam.cur"),
        ("后台运行 Busy", "teto_busy_static.cur"),
        ("等待 Wait", "teto_wait.cur"),
        ("不可用 No", "teto_unavailable.cur"),
        ("爱心 Heart", "teto_heart_static.cur"),
        ("精确选择 Crosshair", "teto_crosshair.cur"),
        ("角色 Chibi", "teto_chibi.cur"),
    ]
    cols, cell = 3, 360
    pad = 40
    for i, (label, fn) in enumerate(items):
        r, c = divmod(i, cols)
        x = pad + c * cell
        y = 90 + r * 200
        d.rounded_rectangle([x, y, x + 300, y + 150], radius=14, fill=(40, 46, 64), outline=(90, 96, 116))
        cur = scale(load_best(os.path.join(CUR_DIR, fn)), 90)
        bg.alpha_composite(cur, (x + 105, y + 25))
        caption(bg, label, (x + 18, y + 122), size=18)
    bg.convert("RGB").save(os.path.join(OUT, "showcase_gallery.png"))
    print("saved showcase_gallery.png")


scene_desktop()
scene_crosshair()
scene_gallery()
print("DONE")
