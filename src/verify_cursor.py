import struct, os, numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
CUR = os.path.join(BASE, "..", "cursors", "teto_crosshair.cur")
data = open(CUR, "rb").read()
res, itype, count = struct.unpack("<HHH", data[:6])
assert itype == 2, "not a cursor"
print(f"type={itype} count={count}")

def near_white(p):
    return ((255-p[0])**2 + (255-p[1])**2 + (255-p[2])**2)**0.5 < 95

off = 6 + 16*count
frames = []
for i in range(count):
    s = 6 + 16*i
    w, h, _, _, hx, hy, size, foff = struct.unpack("<BBBBHHII", data[s:s+16])
    w = 256 if w == 0 else w; h = 256 if h == 0 else h
    blob = data[foff:foff+size]
    bih = struct.unpack("<IiiHHIIiiII", blob[:40])
    bw, bh, bpp = bih[1], bih[2], bih[4]   # bh = 2*image_height for icons
    ih = bh // 2
    xor_len = ih * w * 4
    xor = blob[40:40+xor_len]
    arr = np.frombuffer(xor, dtype=np.uint8).reshape(ih, w, 4)  # BGRA
    # 转 RGBA，注意底向上
    arr = arr[::-1, :, :]
    rgb = arr[:, :, [2,1,0]].astype(int)
    alpha = arr[:, :, 3]
    frames.append((w, hx, hy, rgb, alpha))

for w, hx, hy, rgb, alpha in frames:
    H, W = alpha.shape
    am = alpha > 0
    fg = int(am.sum())
    corners = [int(alpha[2,2]), int(alpha[2,W-3]), int(alpha[H-3,2]), int(alpha[H-3,W-3])]
    # 毛边：近白且邻透明
    halo = 0
    for y in range(H):
        for x in range(W):
            if not am[y,x]: continue
            if near_white(rgb[y,x]):
                nb=False
                for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if 0<=nx<W and 0<=ny<H and alpha[ny,nx]==0:
                        nb=True;break
                if nb: halo+=1
    # 区域统计
    def reg(y0,y1,x0,x1):
        sub=rgb[y0:y1,x0:x1]; a=alpha[y0:y1,x0:x1]
        c=sub.reshape(-1,3); av=a.reshape(-1)
        red=int(np.sum((c[:,0]>150)&(c[:,1]<90)&(c[:,2]<90)&(av>0)))
        pink=int(np.sum((c[:,0]>230)&(c[:,1]>160)&(c[:,2]>170)&(av>0)))
        return red,pink
    r1=reg(0,H//3,0,W//3); r2=reg(H//3,2*H//3,W//3,2*W//3)
    print(f"\n[{w}px] hotspot=({hx},{hy}) 前景像素={fg} 四角alpha={corners}")
    print(f"  毛边(邻透明近白)={halo} ({halo/max(fg,1)*100:.2f}%)")
    print(f"  左上区(十字+爱心) 红={r1[0]} 粉={r1[1]} | 中部(Teto) 红={r2[0]} 粉={r2[1]}")

# 棋盘预览(用最大帧)，透明处显棋盘
W,H = frames[-1][0], frames[-1][3].shape[0]
rgb = frames[-1][3]; alpha=frames[-1][4]
img = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")
tile=16; bg=Image.new("RGBA",(W,H))
for yy in range(0,H,tile):
    for xx in range(0,W,tile):
        c=(170,170,170,255) if ((xx//tile+yy//tile)%2==0) else (255,255,255,255)
        bg.paste(Image.new("RGBA",(min(tile,W-xx),min(tile,H-yy)),c),(xx,yy))
out=Image.alpha_composite(bg,img); out.convert("RGB").save(os.path.join(BASE,"..","preview","crosshair_checker.png"))
print("\n棋盘预览 -> preview/crosshair_checker.png")
