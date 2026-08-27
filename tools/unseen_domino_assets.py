from __future__ import annotations

import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
FPS = 24
OUT = Path("storage/local_videos/unseen_domino")
OUT.mkdir(parents=True, exist_ok=True)

try:
    FONT_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
    FONT_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
except OSError:
    FONT_BIG = ImageFont.load_default()
    FONT_MED = ImageFont.load_default()


def gradient(top=(10, 18, 34), bottom=(33, 42, 58)):
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(top, dtype=float)[None, None, :]
    b = np.array(bottom, dtype=float)[None, None, :]
    arr = a * (1 - y) + b * y
    return Image.fromarray(np.repeat(arr, W, axis=1).astype(np.uint8), "RGB")


def road(draw, offset=0.0):
    horizon = 235
    draw.polygon([(330, H), (950, H), (760, horizon), (520, horizon)], fill=(27, 29, 34))
    for x0 in (495, 640, 785):
        for k in range(9):
            p = ((k / 9.0) + offset) % 1.0
            y1 = int(horizon + p * (H - horizon))
            y2 = min(H, y1 + int(16 + 65 * p))
            scale = (y1 - horizon) / max(1, H - horizon)
            x = int(640 + (x0 - 640) * scale)
            width = int(2 + 5 * scale)
            draw.rectangle([x - width, y1, x + width, y2], fill=(210, 211, 203))


def car(draw, x, y, scale=1.0, brake=False, body=(62, 68, 79)):
    w, h = int(112 * scale), int(62 * scale)
    x0, y0 = int(x - w / 2), int(y - h / 2)
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=max(4, int(10 * scale)), fill=body)
    draw.rounded_rectangle([x0 + int(20 * scale), y0 + int(8 * scale), x0 + w - int(20 * scale), y0 + int(27 * scale)], radius=max(3, int(7 * scale)), fill=(29, 38, 51))
    light = (255, 42, 32) if brake else (142, 20, 18)
    r = max(2, int(7 * scale))
    for lx in (x0 + int(19 * scale), x0 + w - int(19 * scale)):
        draw.ellipse([lx - r, y0 + h - 15 * scale - r, lx + r, y0 + h - 15 * scale + r], fill=light)


def glow_layer(base, centers, radius=22, opacity=180):
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for x, y in centers:
        gd.ellipse([x-radius, y-radius, x+radius, y+radius], fill=(255, 40, 30, opacity))
    glow = glow.filter(ImageFilter.GaussianBlur(radius / 2))
    return Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")


def brake_closeup(t):
    img = gradient((5, 8, 15), (20, 24, 31))
    d = ImageDraw.Draw(img)
    road(d, offset=t * 0.7)
    car(d, 640, 495, 2.35, brake=t > 1.0, body=(29, 33, 42))
    if t > 1.0:
        pulse = 0.85 + 0.15 * math.sin(t * 8)
        centers = [(530, 545), (750, 545)]
        img = glow_layer(img, centers, radius=int(36 * pulse), opacity=190)
    d = ImageDraw.Draw(img)
    d.text((55, 50), "ONE TAP", font=FONT_BIG, fill=(244, 244, 240))
    d.text((58, 125), "starts a wave you can't see", font=FONT_MED, fill=(180, 188, 199))
    return img


def ripple_topdown(t):
    img = Image.new("RGB", (W, H), (13, 18, 27))
    d = ImageDraw.Draw(img)
    lane_y = [205, 305, 405, 505]
    for y in lane_y:
        d.rectangle([0, y - 50, W, y + 50], fill=(28, 31, 37))
        for x in range(-80, W + 80, 160):
            xx = (x + int(t * 150)) % (W + 160) - 80
            d.rectangle([xx, y - 2, xx + 70, y + 2], fill=(190, 192, 188))
    wave_x = W - (t / 5.0) * (W + 220)
    for li, y in enumerate(lane_y):
        for i in range(11):
            x = (i * 140 + t * 95 + li * 35) % (W + 180) - 90
            braking = abs(x - wave_x) < 155
            car(d, x, y, 0.72, brake=braking, body=(55 + li * 15, 66, 83))
    d.text((55, 55), "THE WAVE MOVES BACKWARD", font=FONT_BIG, fill=(245, 245, 242))
    d.line([(int(wave_x), 150), (int(wave_x), 565)], fill=(255, 65, 50), width=6)
    return img


def reaction_chain(t):
    img = gradient((12, 22, 40), (38, 41, 47))
    d = ImageDraw.Draw(img)
    road(d, offset=t * 0.45)
    positions = [(640, 330, .55), (640, 410, .8), (640, 520, 1.25), (640, 665, 1.8)]
    for idx, (x, y, s) in enumerate(positions):
        trigger = 0.7 + idx * 0.6
        car(d, x, y, s, brake=t > trigger, body=(52, 58, 69))
    d.text((60, 55), "EACH DRIVER REACTS", font=FONT_BIG, fill=(248, 248, 245))
    d.text((63, 130), "a little harder", font=FONT_MED, fill=(187, 194, 205))
    return img


def open_highway(t):
    img = gradient((44, 84, 117), (182, 139, 92))
    d = ImageDraw.Draw(img)
    road(d, offset=t * 0.55)
    for i in range(5):
        yy = 315 + i * 78 + 22 * math.sin(t * 0.8 + i)
        xx = 565 + (i % 2) * 150
        car(d, xx, yy, 0.55 + i * .13, brake=False, body=(42 + 18 * i, 62, 78))
    d.text((55, 52), "NO CRASH.", font=FONT_BIG, fill=(250, 248, 239))
    d.text((55, 126), "NO ROADWORK.", font=FONT_BIG, fill=(250, 248, 239))
    d.text((57, 205), "Still... traffic stops.", font=FONT_MED, fill=(235, 229, 212))
    return img


def phantom_title(t):
    img = Image.new("RGB", (W, H), (7, 10, 17))
    d = ImageDraw.Draw(img)
    y0 = H // 2 + 80
    pts = []
    for x in range(0, W + 1, 8):
        y = y0 + 65 * math.sin((x / 150) - t * 2.2) * math.exp(-((x - 640) / 600) ** 2)
        pts.append((x, y))
    d.line(pts, fill=(244, 61, 45), width=7)
    for i in range(9):
        x = (i * 155 + t * 120) % (W + 160) - 80
        y = y0 - 90 + (i % 3) * 55
        car(d, x, y, .58, brake=abs(x - (W - t * 180)) < 130, body=(58, 64, 78))
    d.text((W // 2, 120), "PHANTOM", anchor="ma", font=FONT_BIG, fill=(244, 244, 241))
    d.text((W // 2, 198), "TRAFFIC JAM", anchor="ma", font=FONT_BIG, fill=(244, 244, 241))
    d.text((W // 2, 286), "A jam with no visible cause", anchor="ma", font=FONT_MED, fill=(174, 184, 199))
    return img


def end_card(t):
    img = Image.new("RGB", (W, H), (5, 7, 12))
    d = ImageDraw.Draw(img)
    pulse = 0.5 + 0.5 * math.sin(t * 2)
    r = int(52 + 12 * pulse)
    cx, cy = W // 2, 210
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(235, 59, 45), width=5)
    d.ellipse([cx-13, cy-13, cx+13, cy+13], fill=(235, 59, 45))
    d.text((W // 2, 330), "UNSEEN DOMINO", anchor="ma", font=FONT_BIG, fill=(245, 245, 242))
    d.text((W // 2, 420), "Small causes. Massive consequences.", anchor="ma", font=FONT_MED, fill=(172, 181, 194))
    return img


def render(path: Path, fn, duration=5.0):
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for n in range(int(duration * FPS)):
        frame = fn(n / FPS)
        proc.stdin.write(np.asarray(frame, dtype=np.uint8).tobytes())
    proc.stdin.close()
    code = proc.wait()
    if code:
        raise SystemExit(f"ffmpeg failed for {path} with exit code {code}")


scenes = [
    ("01_brake.mp4", brake_closeup),
    ("02_ripple.mp4", ripple_topdown),
    ("03_reaction.mp4", reaction_chain),
    ("04_open_highway.mp4", open_highway),
    ("05_phantom.mp4", phantom_title),
    ("06_endcard.mp4", end_card),
]

for name, fn in scenes:
    print(f"Rendering {name}")
    render(OUT / name, fn, 5.0)

print(f"Created {len(scenes)} animated local clips in {OUT}")
