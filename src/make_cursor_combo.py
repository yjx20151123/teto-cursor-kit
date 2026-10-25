from PIL import Image, ImageDraw, ImageFilter
import struct, os, shutil, math
import numpy as np
from collections import deque

# 仓库内相对路径，可独立复现
BASE = os.path.dirname(os.path.abspath(__file__))
CUR_DIR = os.path.join(BASE, "..", "cursors")
ASSETS = os.path.join(BASE, "..", "assets")
PREVIEW = os.path.join(BASE, "..", "preview")
os.makedirs(CUR_DIR, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)
STABLE = CUR_DIR            # .cur 输出目录
DESK = PREVIEW              # 预览/reg 副本输出目录（仓库内，不碰桌面）
OUT_NAME = "teto_crosshair.cur"
TETO_SRC = os.path.join(ASSETS, "teto_chibi.png")

RED = (226, 25, 42, 255)
DOT_PINK = (255, 168, 197, 255)
HEART_PINK = (255, 182, 198, 255)
BLACK = (17, 17, 17, 255)

# ---------- 抠 Teto ----------
def cutout(path):
    img = Image.open(path).convert("RGBA"); W, H = img.size; px = img.load()
    gray = np.array(img.convert("L")).astype(np.float32)
    gx = np.zeros_like(gray); gy = np.zeros_like(gray)
    gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
    gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
    grad = np.sqrt(gx*gx + gy*gy)
    grad = np.array(Image.fromarray(np.clip(grad, 0, 255).astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(0.4))).astype(np.float32)
    T_EDGE, LOCAL_TOL = 12, 45
    def dist(c, r, g, b): return ((c[0]-r)**2 + (c[1]-g)**2 + (c[2]-b)**2)**0.5
    bg = bytearray(W*H); q = deque()
    for e in ([(x, 0) for x in range(W)] + [(x, H-1) for x in range(W)] +
              [(0, y) for y in range(H)] + [(W-1, y) for y in range(H)]):
        i = e[1]*W + e[0]
        if not bg[i]: bg[i] = 1; q.append(e)
    while q:
        x, y = q.popleft(); cr, cg, cb, _ = px[x, y]
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < W and 0 <= ny < H and not bg[ny*W+nx]:
                if grad[ny, nx] > T_EDGE: continue
                if dist(px[nx, ny], cr, cg, cb) < LOCAL_TOL:
                    bg[ny*W+nx] = 1; q.append((nx, ny))
    fg = bytearray(1 if not bg[i] else 0 for i in range(W*H))
    lab = [0]*(W*H); comps = []
    for i in range(W*H):
        if fg[i] and not lab[i]:
            cid = len(comps) + 1; area = 0; qq = deque([i]); lab[i] = cid
            while qq:
                j = qq.popleft(); area += 1; x, y = j % W, j // W
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1),
                               (x+1, y+1), (x-1, y-1), (x+1, y-1), (x-1, y+1)):
                    if 0 <= nx < W and 0 <= ny < H:
                        k = ny*W + nx
                        if fg[k] and not lab[k]: lab[k] = cid; qq.append(k)
            comps.append(area)
    if comps:
        big = comps.index(max(comps)) + 1
        fg = bytearray(1 if (fg[i] and lab[i] == big) else 0 for i in range(W*H))
    # ---- 去光晕：从与背景相邻的掩膜边缘吃掉近白像素（贴纸白边）----
    def near_white(x, y):
        r, g, b, _ = px[x, y]
        return ((255-r)**2 + (255-g)**2 + (255-b)**2) ** 0.5 < 130
    seeds = deque()
    for y in range(H):
        for x in range(W):
            i = y*W + x
            if fg[i] and near_white(x, y):
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if 0 <= nx < W and 0 <= ny < H and not fg[ny*W+nx]:
                        seeds.append((x, y)); break
    while seeds:
        x, y = seeds.popleft(); i = y*W + x
        if not fg[i] or not near_white(x, y): continue
        fg[i] = 0
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < W and 0 <= ny < H:
                k = ny*W + nx
                if fg[k]: seeds.append((nx, ny))
    m = np.array([255 if v else 0 for v in fg], np.uint8).reshape(H, W)
    m = np.array(Image.fromarray(m).filter(ImageFilter.MinFilter(3)))
    fg = np.array(m.reshape(-1).tolist(), np.uint8)
    arr = np.array(img).astype(np.uint8)
    mask = fg.astype(bool).reshape(H, W)
    rgb = arr[:, :, :3].astype(np.float32); known = mask.copy(); filled = rgb.copy()
    for _ in range(6):
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sr = np.roll(filled, (dy, dx), axis=(0, 1)); sk = np.roll(known, (dy, dx), axis=(0, 1))
            mm = (~known) & sk; filled[mm] = sr[mm]; known = known | mm
    arr[:, :, :3] = np.clip(filled, 0, 255).astype(np.uint8)
    al = np.zeros((H, W), np.uint8); al[mask] = 255
    arr[:, :, 3] = al
    out = Image.fromarray(arr, "RGBA")
    bb = out.getbbox(); out = out.crop(bb)
    corners_a = (int(al[2, 2]), int(al[2, -3]), int(al[-3, 2]), int(al[-3, -3]))
    print("teto cutout", out.size, "fg%=", round(fg.mean()*100, 1),
          "corner_alpha=", corners_a, "bbox=", out.getbbox())
    return out

teto_full = cutout(TETO_SRC)
teto_full.save(os.path.join(PREVIEW, "cut_teto.png"))

# ---------- 平滑矢量爱心 ----------
def heart_pts(size, k=1.0):
    n = 90; pts = []
    for i in range(n):
        t = 2*math.pi*i/n
        x = 16*(math.sin(t)**3)
        y = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
        pts.append((x, -y))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    cx = (minx+maxx)/2; cy = (miny+maxy)/2; Wd = maxx-minx; Hd = maxy-miny
    pad = max(1, round(size*0.06)); avail = size - 2*pad
    s = k*avail/max(Wd, Hd); out = []
    for x, y in pts: out.append((size/2 + (x-cx)*s, size/2 + (y-cy)*s))
    return out

def draw_smooth_heart(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.polygon(heart_pts(size, 1.06), fill=BLACK)
    d.polygon(heart_pts(size, 1.0), fill=HEART_PINK)
    return img

# ---------- 十字（画满 TS 画布）----------
def compose_cross(TS):
    cv = Image.new("RGBA", (TS, TS), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    c = TS / 2; lw = max(2, round(TS*0.018))
    d.line([(0, c), (TS, c)], fill=RED, width=lw)
    d.line([(c, 0), (c, TS)], fill=RED, width=lw)
    a = 0.05*TS; b = 0.13*TS; h = 0.16*TS
    d.line([(c-a, c-a-h), (c-a, c-a)], fill=RED, width=lw)
    d.line([(c-a-b, c-a), (c-a, c-a)], fill=RED, width=lw)
    d.line([(c+a, c-a-h), (c+a, c-a)], fill=RED, width=lw)
    d.line([(c+a, c-a), (c+a+b, c-a)], fill=RED, width=lw)
    d.line([(c-a, c+a), (c-a, c+a+h)], fill=RED, width=lw)
    d.line([(c-a-b, c+a), (c-a, c+a)], fill=RED, width=lw)
    d.line([(c+a, c+a), (c+a, c+a+h)], fill=RED, width=lw)
    d.line([(c+a, c+a), (c+a+b, c+a)], fill=RED, width=lw)
    rr = 0.045*TS
    d.ellipse([c-rr, c-rr, c+rr, c+rr], fill=DOT_PINK)
    hs = max(5, int(TS*0.10))
    for fx, fy in ((0.66, 0.40), (0.34, 0.72)):
        heart = draw_smooth_heart(hs)
        cv.alpha_composite(heart, (int(fx*TS-hs/2), int(fy*TS-hs/2)))
    return cv

# ---------- 合成：左上十字 + 中间 Teto ----------
def compose(S):
    cv = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    TS = round(S*0.33)
    off = -round(S*0.06)
    cv.alpha_composite(compose_cross(TS), (off, off))
    tw, th = teto_full.size
    sc = (S*0.62)/max(tw, th)
    t = teto_full.resize((max(1, round(tw*sc)), max(1, round(th*sc))), Image.LANCZOS)
    cv.alpha_composite(t, ((S - t.width)//2, (S - t.height)//2))
    hx = off + TS//2
    hy = off + TS//2
    return cv, (hx, hy)

def encode(cv, S):
    p = cv.load(); xor = bytearray(); andm = bytearray()
    for y in range(S-1, -1, -1):
        row = bytearray(); ar = bytearray(); n = 0
        for x in range(S):
            r, g, b, a = p[x, y]
            row += bytes((b, g, r, a))
            n += 1
            if n == 8: ar.append(0); n = 0   # 32bpp 光标 AND 掩膜全 0，透明靠 alpha
        if n: ar.append(0)
        while len(ar) % 4: ar.append(0)
        xor += row; andm += ar
    bih = struct.pack('<IiiHHIIiiII', 40, S, 2*S, 1, 32, 0, 0, 0, 0, 0, 0)
    return bih + bytes(xor) + bytes(andm)

SIZES = [32, 48, 64, 96, 128, 192, 256]
metas = []; blobs = []
for S in SIZES:
    cv, (hx, hy) = compose(S); data = encode(cv, S)
    metas.append((S, hx, hy, len(data))); blobs.append(data)
head = struct.pack('<HHH', 0, 2, len(SIZES)); off = 6 + 16*len(SIZES); dird = b''
for S, hx, hy, ln in metas:
    wf = 0 if S >= 256 else S
    dird += struct.pack('<BBBBHHII', wf, wf, 0, 0, hx, hy, ln, off); off += ln
cur_path = os.path.join(STABLE, OUT_NAME)
open(cur_path, "wb").write(head + dird + b''.join(blobs))
print("CUR", os.path.getsize(cur_path), "frames", len(SIZES))
for S, hx, hy, ln in metas:
    print(f"  {S}px hotspot=({hx},{hy}) ratio=({hx/S:.0%},{hy/S:.0%})")

for S in (48, 96, 256):
    cv, _ = compose(S)
    up = cv.resize((S*4, S*4), Image.LANCZOS) if S >= 96 else cv.resize((S*8, S*8), Image.LANCZOS)
    bg = Image.new("RGBA", up.size, (245, 245, 245, 255)); bg.alpha_composite(up)
    bg.convert("RGB").save(os.path.join(PREVIEW, f"crosshair_preview_{S}.png"))
print("PREVIEW ok")

frames = []
for S, hx, hy, ln in metas:
    cv, _ = compose(S); k = 8 if S == 32 else 2
    up = cv.resize((S*k, S*k), Image.LANCZOS)
    bgm = Image.new("RGBA", up.size, (245, 245, 245, 255)); bgm.alpha_composite(up)
    d = ImageDraw.Draw(bgm); sx, sy = hx*k, hy*k
    d.line([(sx-11, sy), (sx+11, sy)], fill=(0, 120, 255), width=2)
    d.line([(sx, sy-11), (sx, sy+11)], fill=(0, 120, 255), width=2)
    frames.append((S, bgm.convert("RGB")))
cols = 4; rows = (len(frames)+cols-1)//cols; cell = max(f[1].size[0] for f in frames); pad = 6
mont = Image.new("RGB", (cols*cell+(cols+1)*pad, rows*cell+(rows+1)*pad), (225, 225, 225))
for i, (S, bgm) in enumerate(frames):
    r, c = divmod(i, cols)
    mont.paste(bgm, (pad+c*cell+(cell-bgm.size[0])//2, pad+r*cell+(cell-bgm.size[1])//2))
mont.save(os.path.join(PREVIEW, "crosshair_hotspot_proof.png"))
print("PROOF ok")

content = 'Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\Control Panel\\Cursors]\n'
content += '"Crosshair"="' + cur_path.replace('\\', '\\\\') + '"\n'
open(os.path.join(STABLE, "teto_crosshair.reg"), 'w', encoding='ascii').write(content)
assert os.path.exists(cur_path), 'FAIL cur'
print("DEPLOY reg ->", cur_path, os.path.getsize(cur_path))
