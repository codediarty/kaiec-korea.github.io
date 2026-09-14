# -*- coding: utf-8 -*-
"""헤더/푸터 워드마크(한국AI윤리위원회 + KOREA AI ETHICS COMMITTEE)를 글꼴 외곽선(벡터 패스) SVG로 생성 → tools/wordmark.svg (build.py가 읽어 헤더에 인라인).
사용법: python3 tools/make_wordmark.py  (Noto Serif CJK Black이 설치된 환경에서)
- 국문: Noto Serif CJK KR Black (사이트의 Noto Serif KR 900과 같은 디자인), 영문 캡션: Archivo Bold
- 웹폰트 로딩·힌팅과 무관하게 어떤 화면에서도 선명하게 그려지도록 텍스트 대신 패스를 사용"""
from fontTools.ttLib import TTFont, TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import re

KO_TEXT = "한국AI윤리위원회"
EN_TEXT = "KOREA AI ETHICS COMMITTEE"
KO_SIZE = 21.0      # px (현재 CSS 21px)
EN_SIZE = 9.0       # px (현재 CSS 9px)
KO_TRACK = 0.012    # em
GAP = 4.0           # 국문 베이스라인 아래 ~ 영문 윗선 간격(px)

ko_font = TTCollection('/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc').fonts[1]   # KR
import os
HERE = os.path.dirname(os.path.abspath(__file__))
en_font = TTFont(os.path.join(HERE, 'fonts', 'archivo-latin-700-normal.woff'))   # @fontsource/archivo (OFL)

def line_paths(font, text, size, tracking_em, y_base):
    """텍스트 한 줄을 (path d, 총 폭 px, bbox) 로. y_base: SVG 좌표계 베이스라인(px)."""
    upm = font['head'].unitsPerEm
    scale = size / upm
    cmap = font.getBestCmap(); gs = font.getGlyphSet(); hmtx = font['hmtx']
    x = 0.0; ds = []; ymin = 1e9; ymax = -1e9
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise SystemExit(f"글리프 없음: {ch!r}")
        adv = hmtx[gname][0] * scale
        if ch != ' ':
            pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}")
            # 글꼴 좌표(y 위로) → SVG(y 아래로): scale(s, -s) + translate(x, y_base)
            tpen = TransformPen(pen, (scale, 0, 0, -scale, x, y_base))
            gs[gname].draw(tpen)
            d = pen.getCommands()
            if d:
                ds.append(d)
                bp = BoundsPen(gs); gs[gname].draw(TransformPen(bp, (scale, 0, 0, -scale, x, y_base)))
                if bp.bounds:
                    ymin = min(ymin, bp.bounds[1]); ymax = max(ymax, bp.bounds[3])
        x += adv + tracking_em * size
    x -= tracking_em * size
    return " ".join(ds), x, (ymin, ymax)

# 1) 국문: 베이스라인을 임시 0에 두고 bbox 측정 후 재배치
ko_d, ko_w, (ko_ymin, ko_ymax) = line_paths(ko_font, KO_TEXT, KO_SIZE, KO_TRACK, 0.0)
# 2) 영문: 국문 폭에 맞춰 자간 계산 (글자 사이 24칸)
en_d0, en_w0, _ = line_paths(en_font, EN_TEXT, EN_SIZE, 0.0, 0.0)
n_gaps = len(EN_TEXT) - 1
en_track_px = (ko_w - en_w0) / n_gaps
en_d, en_w, (en_ymin, en_ymax) = line_paths(en_font, EN_TEXT, EN_SIZE, en_track_px / EN_SIZE, 0.0)

# 3) 세로 배치: 국문 윗선을 0.5px 여백에 맞추고, 영문은 국문 아래 GAP. 베이스라인을 정한 뒤 다시 그린다 (후처리 이동 없음)
ko_shift = -ko_ymin + 0.5
en_shift = ko_shift + ko_ymax + GAP - en_ymin
H = en_shift + en_ymax + 0.5
W = max(ko_w, en_w) + 0.5
ko_path, _, _ = line_paths(ko_font, KO_TEXT, KO_SIZE, KO_TRACK, ko_shift)
en_path, _, _ = line_paths(en_font, EN_TEXT, EN_SIZE, en_track_px / EN_SIZE, en_shift)
svg = (f'<svg class="brand-wm" viewBox="0 0 {W:.2f} {H:.2f}" aria-hidden="true" focusable="false">'
       f'<path id="wm-ko" style="fill:var(--wm-ko,#0B1B36)" d="{ko_path}"/>'
       f'<path id="wm-en" style="fill:var(--wm-en,#76839A)" d="{en_path}"/></svg>')
open(os.path.join(HERE, 'wordmark.svg'), 'w', encoding='utf-8').write(svg + "\n")
print(f"tools/wordmark.svg  W={W:.2f} H={H:.2f} ko_w={ko_w:.2f} en_w={en_w:.2f} en_track={en_track_px:.3f}px bytes={len(svg.encode())}")
