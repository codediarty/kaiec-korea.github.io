"""위원 사진을 명함용 480x480 JPG 로 만들기 (기존 사진과 같은 구도: 얼굴 폭 44%, 얼굴 중심 가로 50% · 세로 43%)

사용: python3 tools/member_photo.py 원본.png assets/img/members/yoo-inho.jpg
      python3 tools/member_photo.py 원본.png 저장.jpg --bg f2f3f5   (배경이 투명한 누끼 사진은 이 색으로 채움)
얼굴은 OpenCV 정면 얼굴 검출로 찾고, 사진 밖으로 나가는 부분은 배경색(투명이면 --bg, 아니면 사진 가장자리 색)으로 채웁니다.
얼굴을 못 찾으면 가운데 위쪽을 기준으로 자릅니다. 결과는 꼭 눈으로 확인하세요.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

FACE_W, FACE_CX, FACE_CY, OUT = 0.44, 0.50, 0.43, 480


def load(path, bg_hex):
    """(RGB 이미지, 채울 배경색, 투명 누끼 여부)"""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        if im.split()[3].getextrema()[0] < 250:      # 실제로 투명한 부분이 있는 누끼 사진
            color = tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4))
            bg = Image.new("RGB", im.size, color)
            bg.paste(im, mask=im.split()[3])
            return bg, color, True
    im = im.convert("RGB")
    a = np.asarray(im)
    edge = np.concatenate([a[:8].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    return im, tuple(int(v) for v in np.median(edge, axis=0)), False


def face_box(im):
    g = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY)
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    m = min(im.size)
    faces = casc.detectMultiScale(g, 1.1, 6, minSize=(int(m * 0.08), int(m * 0.08)))
    if len(faces) == 0:
        return None
    return max(faces, key=lambda b: b[2] * b[3])


def head_top(im):
    """밝은 배경 사진에서 머리 윗선(배경과 다른 픽셀이 처음 나오는 줄). 못 찾으면 None"""
    g = np.asarray(im.convert("L")).astype(int)
    h, w = g.shape
    mid = g[:, int(w * 0.15):int(w * 0.85)]
    bgv = np.median(g[:6])
    diff = (np.abs(mid - bgv) > 40).mean(axis=1)
    rows = np.where(diff > 0.03)[0]
    return int(rows[0]) if len(rows) and rows[0] < h * 0.5 else None


def make(src, dst, bg_hex="f2f3f5"):
    im, bg, cutout = load(src, bg_hex)
    fb = face_box(im)
    if fb is None:
        w = im.width
        s, cx, cy = w, w / 2, w * FACE_CY
        print("얼굴을 찾지 못해 위쪽 가운데 기준으로 자름")
    else:
        x, y, fw, fh = fb
        s, cx, cy = fw / FACE_W, x + fw / 2, y + fh / 2
    if cutout:
        # 누끼 사진: 모자라는 곳은 배경색으로 채움
        x0, y0, s = int(round(cx - FACE_CX * s)), int(round(cy - FACE_CY * s)), int(round(s))
        canvas = Image.new("RGB", (s, s), bg)
        canvas.paste(im, (-x0, -y0))
    else:
        # 일반 사진: 바깥을 채우면 경계가 보이므로 사진 안에서만 자르고, 머리 위가 잘리지 않게 맞춤
        s = min(s, im.width, im.height)
        x0 = min(max(cx - FACE_CX * s, 0), im.width - s)
        y0 = cy - FACE_CY * s
        top = head_top(im)
        if top is not None:
            y0 = min(y0, top - 0.04 * s)
        y0 = min(max(y0, 0), im.height - s)
        x0, y0, s = int(round(x0)), int(round(y0)), int(round(s))
        canvas = im.crop((x0, y0, x0 + s, y0 + s))
    canvas = canvas.resize((OUT, OUT), Image.LANCZOS)
    canvas.save(dst, "JPEG", quality=86, optimize=True, progressive=True)
    print(dst, "얼굴", None if fb is None else [int(v) for v in fb], "자른 크기", s, "시작", (x0, y0), os.path.getsize(dst), "bytes")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    bg = "f2f3f5"
    if "--bg" in sys.argv:
        bg = sys.argv[sys.argv.index("--bg") + 1].lstrip("#")
        args = [a for a in args if a != sys.argv[sys.argv.index("--bg") + 1]]
    make(args[0], args[1], bg)
