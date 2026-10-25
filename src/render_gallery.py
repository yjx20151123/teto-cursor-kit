"""生成 Teto 光标「全家福」预览图：把仓库内所有 .cur 渲染到一张深色网格图上，带中文标签。"""
import struct, os, io
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
CUR_DIR = os.path.join(BASE, "..", "cursors")
OUT = os.path.join(BASE, "..", "preview", "family_portrait.png")

# 顺序即展示顺序；Crosshair 放在显眼位置
CURSORS = [
    ("普通选择 Arrow", "teto_cursor.cur"),
    ("链接选择 Hand", "teto_hand.cur"),
    ("文本 IBeam", "teto_ibeam.cur"),
    ("后台运行 Busy", "teto_busy_static.cur"),
    ("等待 Wait", "teto_wait.cur"),
    ("不可用 No", "teto_unavailable.cur"),
    ("爱心 Heart", "teto_heart_static.cur"),
    ("精确选择 Crosshair ★", "teto_crosshair.cur"),
    ("角色 Chibi", "teto_chibi.cur"),
]

FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
try:
    FONT = ImageFont.truetype(FONT_PATH, 18)
except Exception:
    FONT = ImageFont.load_default()


def load_best(path):
    raw = open(path, "rb").read()
    raw = raw[:2] + b"\x01\x00" + raw[4:]   # 把 CUR 的 type 字节改成 1(ICO)，骗过 Pillow
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


cells = []
for label, fn in CURSORS:
    p = os.path.join(CUR_DIR, fn)
    if not os.path.exists(p):
        print("MISSING", p); continue
    img = load_best(p)
    cells.append((label, img))
    print("loaded", label, img.size)

cols = 3
cell = 170
pad = 22
label_h = 30
cw = cell + pad * 2
ch = cell + pad + label_h
rows = (len(cells) + cols - 1) // cols
W = cols * cw + pad
H = rows * ch + pad + 50   # 顶部留标题空间
canvas = Image.new("RGBA", (W, H), (26, 28, 38, 255))
d = ImageDraw.Draw(canvas)

# 标题
d.text((pad, 16), "重音テト Windows 光标套装", fill=(255, 182, 198, 255), font=FONT)
d.text((pad, 40), "Teto Cursor Pack · %d 个状态" % len(cells), fill=(170, 175, 190, 255), font=FONT)

for i, (label, img) in enumerate(cells):
    r, c = divmod(i, cols)
    x = pad + c * cw
    y = pad + 60 + r * ch
    # 单元格浅色底
    d.rounded_rectangle([x, y, x + cell, y + cell], radius=12, fill=(40, 43, 56, 255),
                       outline=(80, 84, 100, 255))
    s = min(cell / img.width, cell / img.height, 1.0) * 0.82
    ni = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    bx = x + (cell - ni.width) // 2
    by = y + (cell - ni.height) // 2
    canvas.alpha_composite(ni, (bx, by))
    d.text((x + cell // 2, y + cell + 8), label, fill=(220, 224, 235, 255),
           font=FONT, anchor="mm")

canvas.convert("RGB").save(OUT)
print("saved ->", OUT, canvas.size)
