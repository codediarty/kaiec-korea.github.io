# -*- coding: utf-8 -*-
"""kaiec.kr 에 올릴 사이트 파일만 모으기 (2026.09.28, GitHub Actions 배포용)

저장소에는 사이트 파일과 함께 작업 메모 · 빌드 스크립트 · 도구가 들어 있어, 저장소를 통째로 배포하면
kaiec.kr/작업-메모.md 같은 내부 문서도 주소로 열립니다. 이 스크립트는 아래 허용 목록의 파일만
출력 폴더(기본 _site)로 복사하고, 복사한 페이지 안의 내부 주소(링크 · 이미지 · 스크립트 · srcset · CSS url())가
모두 출력 폴더 안에 있는지 확인합니다. 하나라도 없으면 종료 코드 1 로 멈춰 배포하지 않습니다.

허용 목록
  - 루트와 페이지 폴더(영문 소문자 · 숫자 · 하이픈 이름)의 *.html  (tools/ · posts-src/ 는 제외)
  - assets/ 아래 모든 파일 (.DS_Store · Thumbs.db · desktop.ini · __pycache__ 제외, 영상관 오리지널 MP4 포함)
  - 루트의 CNAME · robots.txt · sitemap.xml · rss.xml · llms.txt

사용: python3 tools/collect_site.py [출력 폴더, 기본 _site]
.github/workflows/pages.yml 이 push 때마다 이 스크립트로 _site 를 만들어 GitHub Pages 에 올립니다.
"""
import os
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_HOSTS = ("kaiec.kr", "www.kaiec.kr")
ROOT_FILES = ("CNAME", "robots.txt", "sitemap.xml", "rss.xml", "llms.txt")   # 2026.10.10 llms.txt(AI 안내문)
SKIP_DIRS = {"tools", "posts-src", "assets"}            # assets 는 따로 통째로 복사
PAGE_DIR = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROOT_HTML = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.html$")
JUNK = {".DS_Store", "Thumbs.db", "desktop.ini"}
ALLOWED_EXT = {".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".svg", ".webp", ".gif", ".ico",
               ".woff", ".woff2", ".ttf", ".otf", ".xml", ".txt", ".json", ".webmanifest", ".pdf", ".mp4", ".bin", ""}
# .bin: 위원 등록 사진 자동 맞춤의 얼굴 · 배경 모델 가중치(assets/vendor/face/, 2026.10.05)
# .mp4: AIEP 영상관 오리지널(assets/vid/, 2026.10.02 5판). 파일마다 20MB 아래로 만듦(저장소 · Pages 용량)


def auto_photos_in_use():
    """1분 등록 위원 사진(assets/img/members/auto-*.jpg) 가운데 지금 명단(assets/auto/members.js)에 있는 것만. 명단에서 빠진(숨김 · 해제) 위원 사진은 배포하지 않음"""
    keep = set()
    try:
        t = open(os.path.join(ROOT, "assets", "auto", "members.js"), encoding="utf-8").read()
        for f in re.findall(r'"photo":"(auto-[a-z]{2,4}\d{4}(?:-\d{1,2})?\.jpg)"', t):
            keep.add(f); keep.add(f[:-4] + "-240.jpg")
    except Exception:
        pass
    return keep


def collect(out):
    files = []
    auto_keep = auto_photos_in_use()
    # 1) 페이지(HTML)
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = os.path.relpath(dirpath, ROOT)
        parts = [] if rel == "." else rel.split(os.sep)
        if parts and (parts[0] in SKIP_DIRS or not all(PAGE_DIR.match(p) for p in parts)):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not (not parts and d in SKIP_DIRS) and PAGE_DIR.match(d)]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            if not parts and not ROOT_HTML.match(fn):
                continue
            files.append(os.path.join(*parts, fn) if parts else fn)
    # 2) assets/
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "assets")):
        dirnames[:] = [d for d in dirnames if d != "__pycache__" and not d.startswith(".")]
        for fn in filenames:
            if fn in JUNK or fn.startswith("."):
                continue
            if fn.startswith("auto-") and os.path.basename(dirpath) == "members" and fn not in auto_keep:
                continue
            files.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    # 3) 루트 파일
    for fn in ROOT_FILES:
        if os.path.isfile(os.path.join(ROOT, fn)):
            files.append(fn)
    for rel in files:
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), dst)
    return sorted(files)


ATTR = re.compile(r'\b(?:href|src|poster|data-src)\s*=\s*"([^"]*)"|\bsrcset\s*=\s*"([^"]*)"', re.I)
META_URL = re.compile(r'<meta[^>]+content="(https?://(?:www\.)?kaiec\.kr/[^"]*)"', re.I)
CSS_URL = re.compile(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)')
XML_URL = re.compile(r'https?://(?:www\.)?kaiec\.kr(/[^\s<"\']*)')


def target_path(url, base_url_path):
    """사이트 주소 → 출력 폴더 안의 후보 파일 경로들. 바깥 주소면 None."""
    url = url.strip()
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "sms:")):
        return None
    sp = urlsplit(url)
    if sp.scheme in ("http", "https") or url.startswith("//"):
        if sp.hostname not in SITE_HOSTS:
            return None
        path = sp.path or "/"
    elif sp.scheme:
        return None
    else:
        path = sp.path
        if not path:
            return None
        if not path.startswith("/"):
            path = os.path.normpath(os.path.join(os.path.dirname(base_url_path), path)).replace(os.sep, "/")
            if not path.startswith("/"):
                path = "/" + path
    path = unquote(path)
    if path.endswith("/"):
        return [path + "index.html"]
    name = path.rsplit("/", 1)[-1]
    if "." in name:
        return [path]
    return [path + ".html", path + "/index.html"]       # GitHub Pages: /about → about.html 또는 about/


def check(out, files):
    broken = []
    for rel in files:
        full = os.path.join(out, rel)
        low = rel.lower()
        if not (low.endswith(".html") or low.endswith(".css") or low.endswith(".xml")):
            continue
        text = open(full, encoding="utf-8", errors="replace").read()
        url_path = "/" + rel.replace(os.sep, "/")
        refs = []
        if low.endswith(".html"):
            for m in ATTR.finditer(text):
                if m.group(1) is not None:
                    refs.append(m.group(1))
                else:
                    refs += [c.strip().split()[0] for c in m.group(2).split(",") if c.strip()]
            refs += META_URL.findall(text)
        elif low.endswith(".css"):
            refs += CSS_URL.findall(text)
        else:
            refs += ["https://kaiec.kr" + p for p in XML_URL.findall(text)]
        for u in refs:
            if "{" in u or "'+" in u or "+'" in u:      # 스크립트 안에서 조립하는 주소는 건너뜀
                continue
            cands = target_path(u, url_path)
            if cands is None:
                continue
            if not any(os.path.isfile(os.path.join(out, c.lstrip("/"))) for c in cands):
                broken.append((rel, u))
    return broken


def main():
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site"))
    # 실수로 저장소나 다른 폴더를 지우지 않도록: 이름이 _ 로 시작하는 폴더(_site 등)나 빈 폴더만 비우고 다시 만듦
    if ROOT == out or ROOT.startswith(out + os.sep) or (
            os.path.isdir(out) and os.listdir(out) and not os.path.basename(out).startswith("_")):
        print("출력 폴더로 쓸 수 없습니다(이름이 _ 로 시작하는 폴더를 쓰세요):", out)
        return 2
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    files = collect(out)
    bad_ext = [f for f in files if os.path.splitext(f)[1].lower() not in ALLOWED_EXT]
    size = sum(os.path.getsize(os.path.join(out, f)) for f in files)
    pages = sum(1 for f in files if f.endswith(".html"))
    print(f"모은 파일 {len(files)}개 (페이지 {pages}개), {size / 1048576:.1f} MB → {out}")
    if bad_ext:
        print("허용하지 않는 형식이 섞였습니다:", bad_ext[:20])
        return 1
    for must in ("index.html", "404.html", "CNAME"):
        if must not in files:
            print("꼭 있어야 할 파일이 없습니다:", must)
            return 1
    broken = check(out, files)
    if broken:
        print(f"없는 파일을 가리키는 주소 {len(broken)}개:")
        for rel, u in broken[:50]:
            print("  ", rel, "→", u)
        return 1
    print("내부 주소 확인: 모두 있음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
