# -*- coding: utf-8 -*-
"""
한국AI윤리위원회(kaiec.kr) 빌드 결과 전체 검증
  사용법: 저장소 루트에서  python3 build.py  →  python3 tools/verify.py
  마지막 줄이 "전체 통과"여야 커밋·푸시합니다. 실패가 있으면 항목별로 원인이 표시됩니다.
검사 항목
  1. 생성 페이지·게시글 페이지·이동 스텁이 모두 존재하고, 원본 없는 잔존 결과물이 없는지
  2. 줄표(U+2014) 미사용 (저장소의 모든 텍스트 파일)
  3. 폐기 명칭(한국AI윤리협회, 2026.09.11~13 사용 후 SEO 문제로 원복)·협회 직함(회장)·옛 영문명·인증/검정/급수 표기 미사용,
     법적 지위를 넘어서는 표현·'민간'·자리표시 도메인 미사용
  4. 각 페이지의 canonical·네이버 인증 메타·설명·OG 이미지·브레드크럼 존재, JSON-LD 전부 파싱
  5. 내부 링크·이미지·CSS·JS 경로가 실제 파일을 가리키는지
  6. sitemap.xml·rss.xml 파싱, 사이트맵 항목과 실제 페이지 일치
  7. build.py 상수(웹훅·결제 링크·가격)가 페이지에 반영됐는지
  8. CNAME·robots.txt·.nojekyll 등 배포 파일
"""
import os, re, io, sys, glob, json
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)
import build  # 상수·url_for·out_path·load_posts 를 그대로 사용 (빌드는 실행되지 않음)

DASH = "\u2014"   # 줄표(긴 대시)
# 2026.09.14 원복: 기관명은 한국AI윤리위원회(Korea AI Ethics Committee). 아래 표기는 어디에도 남기지 않는다
OLD_NAMES = ["한국AI윤리협회", "한국 AI 윤리협회", "AI윤리협회", "AI 윤리 협회", "Association", "Ethics & Compliance",
             "Ethics Compliance", "ETHICS COMPLIANCE", "회장", "PRESIDENT",
             # 2026.09.14 양성과정 전환: 등록된 자격 제도가 아니므로 인증·검정·급수 표기를 쓰지 않는다 (양성과정·수료 시험·수료증으로 표기)
             "자격증", "자격검정", "자격과정", "자격 취득", "2급", "1급", "응시료", "합격증",
             # 2026.09.15 카피 개편: 수료증은 '위원회 공식'으로만 수식(명의 X), 심화과정은 위촉·등재 대신 '전문위원 등록', 삭제한 약한 문구 재유입 방지
             "명의 수료증", "명의 「", "위촉·등재", "첫 번째 이름이 당신", "새로운 전문 역량", "누가 책임지나요",
             # 2026.09.16 용어 전환: 수료 시험 → 이수 평가, 수료증 → 이수증 (평가응시 시스템 신설과 함께, 옛 표기 재유입 방지)
             "수료 시험", "수료증",
             # 2026.09.16 상단바 '인증시험' → '평가응시' 교체 (인증 표기 금지 규칙과 일치)
             "인증시험"]
BANNED = ["민간", "국가공인", "지정기부금", "세액공제", "기부금 영수증", "YOUR-DOMAIN",
          "탐지 우회", "우회 도구",   # 2026.09.15: 카피클린 제휴 관계상 탐지 우회를 다루는 콘텐츠를 싣지 않음 (문장 단위 사전점검으로 대체)
          "kaiec-korea.github.io/", "kaiec.skkc.co.kr"]
DOC_FILES = {"작업-메모.md", "README.md", "배포-가이드.md", "앱스스크립트-접수시트연동.txt",
             os.path.join("posts-src", "_작성방법.txt")}
RETIRED_STUBS = {"post-2026-09-11-name-change.html"}   # 삭제된 명칭변경 공지의 은퇴 스텁 (build.py가 만들지 않음)
# 교체된 게시글(md 머리 '교체: <새 slug>')은 build.load_posts()가 RETIRED_POSTS에 모으고 옛 주소 2곳에 새 글로 이동하는 스텁을 씁니다 (2026.09.15)
CORE = ["about.html", "business.html", "members.html", "lecture.html", "expert.html",
        "expert-apply.html", "experts.html", "join.html", "quiz.html", "exam.html", "partner.html", "copyclean.html", "news.html", "mou.html", "apply.html"]

results = []   # (이름, 통과 여부, 상세 목록)


def check(name, problems):
    results.append((name, not problems, problems))


def read(path):
    return io.open(path, encoding="utf-8").read()


def rel(path):
    return os.path.relpath(path, BASE).replace(os.sep, "/")


def text_files():
    out = []
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
        for f in files:
            if f.lower().endswith((".html", ".py", ".md", ".js", ".css", ".txt", ".xml", ".json", ".svg")):
                out.append(os.path.join(root, f))
    return sorted(out)


posts = build.load_posts()
RETIRED_NEWS = {slug: f"/news/{t}/" for slug, t in build.RETIRED_POSTS.items()}   # 옛 slug → 새 주소
RETIRED_STUBS |= {f"post-{slug}.html" for slug in build.RETIRED_POSTS}
for slug, t in build.RETIRED_POSTS.items():
    if not os.path.isfile(os.path.join("posts-src", f"{t}.md")):
        print(f"  ✗ 교체 대상 게시글 없음: {slug} → {t}"); raise SystemExit(1)
pages = {}   # filename → 생성 결과 경로 (index.html, 핵심 페이지, 게시글)
pages["index.html"] = "index.html"
for f in CORE:
    pages[f] = build.out_path(f)
for p in posts:
    pages[p["file"]] = build.out_path(p["file"])

# ---------------------------------------------------------------- 1. 파일 존재·잔존물
probs = []
for f, outp in pages.items():
    if not os.path.isfile(outp):
        probs.append(f"생성 파일 없음: {outp}")
    if f != "index.html" and not os.path.isfile(f):
        probs.append(f"이동 스텁 없음: {f}")
if not os.path.isfile("404.html"):
    probs.append("404.html 없음")
expected_news = {p["slug"] for p in posts}
for d in sorted(glob.glob("news/*/")):
    slug = d.rstrip("/\\").split(os.sep)[-1].split("/")[-1]
    if slug in RETIRED_NEWS:
        stub = read(os.path.join(d, "index.html")) if os.path.isfile(os.path.join(d, "index.html")) else ""
        if "noindex" not in stub or RETIRED_NEWS[slug] not in stub:
            probs.append(f"{d}: 교체된 칼럼의 은퇴 스텁 형식 이상 (noindex 또는 새 주소 {RETIRED_NEWS[slug]} 없음)")
        continue
    if slug not in expected_news:
        probs.append(f"원본 md 없는 게시글 결과물 잔존: {d} (지우세요)")
for f in sorted(glob.glob("post-*.html")):
    if f not in pages and f not in RETIRED_STUBS:
        probs.append(f"원본 md 없는 게시글 스텁 잔존: {f}")
for junk in ["board", "assets/js/news-data.js", "assets/img/posts/precheck-campaign.png",
             "posts-src/2026-09-11-name-change.md"]:
    if os.path.exists(junk):
        probs.append(f"정리 대상 파일 잔존: {junk}")
check(f"생성 페이지 {len(pages)}개 + 스텁 + 404 존재, 잔존물 없음", probs)

# ---------------------------------------------------------------- 2. 줄표
probs = []
for path in text_files():
    if rel(path) == "tools/verify.py":
        continue
    txt = read(path)
    if DASH in txt:
        n = txt.count(DASH)
        line = next(i for i, l in enumerate(txt.splitlines(), 1) if DASH in l)
        probs.append(f"{rel(path)}: 줄표 {n}곳 (첫 위치 {line}행)")
check("줄표(긴 대시) 미사용", probs)

# ---------------------------------------------------------------- 3. 옛 명칭·금지 표현
probs = []
for path in text_files():
    r = rel(path)
    if r in ("tools/verify.py", "작업-메모.md", "앱스스크립트-접수시트연동.txt"):
        continue   # 규칙 설명·이력, 그리고 배포된 앱스 스크립트와 맞춰야 하는 시트 열 이름(내부용)은 검사 제외
    txt = read(path)
    for w in OLD_NAMES:
        if w in txt:
            probs.append(f"{r}: 폐기 명칭·표기 '{w}' {txt.count(w)}곳")
    if r in DOC_FILES:
        continue
    for w in BANNED:
        if w in txt:
            probs.append(f"{r}: 금지 표현 '{w}' {txt.count(w)}곳")
check("폐기 명칭(협회·회장·옛 영문명)·법적 지위 초과 표현·자리표시 도메인 미사용", probs)

# ---------------------------------------------------------------- 4. 페이지 메타·JSON-LD
probs = []
ld_total = 0
for f, outp in pages.items():
    html = read(outp)
    canonical = f"{build.SITE_URL}{build.url_for(f)}"
    if f'<link rel="canonical" href="{canonical}">' not in html:
        probs.append(f"{outp}: canonical 불일치 (기대 {canonical})")
    if 'name="naver-site-verification"' not in html:
        probs.append(f"{outp}: 네이버 소유확인 메타 없음")
    if not re.search(r'<meta name="description" content="[^"]{20,}"', html):
        probs.append(f"{outp}: description 없음 또는 너무 짧음")
    if 'property="og:image"' not in html:
        probs.append(f"{outp}: og:image 없음")
    if f != "index.html" and '"@type": "BreadcrumbList"' not in html:
        probs.append(f"{outp}: BreadcrumbList 없음")
    if "<title>" not in html or "</title>" not in html:
        probs.append(f"{outp}: title 없음")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        ld_total += 1
        try:
            json.loads(m.group(1))
        except Exception as e:
            probs.append(f"{outp}: JSON-LD 파싱 실패 ({e})")
    if 'lucide' in html and 'data-lucide=' in html:
        probs.append(f"{outp}: 치환되지 않은 아이콘 태그(data-lucide) 남음")
check(f"페이지 메타(canonical·네이버 인증·설명·OG·브레드크럼) + JSON-LD {ld_total}블록 파싱", probs)

# ---------------------------------------------------------------- 5. 내부 링크·자산 경로
probs = []
seen = set()
LINK = re.compile(r'(?:href|src|content)="(/[^"]*)"')
for f, outp in list(pages.items()) + [("404.html", "404.html")]:
    html = read(outp)
    for m in LINK.finditer(html):
        u = m.group(1).split("#")[0].split("?")[0]
        if u.startswith("//") or not u or u in seen or "'" in u or "+" in u:   # JS 문자열 조각은 제외
            continue
        seen.add(u)
        local = "index.html" if u == "/" else (u.lstrip("/") + "index.html" if u.endswith("/") else u.lstrip("/"))
        if not os.path.isfile(local):
            probs.append(f"{outp}: 깨진 내부 경로 {u}")
    for m in re.finditer(r'(?:href|src)="((?!https?:|mailto:|tel:|#|/|data:|javascript:)[^"]+)"', html):
        if "'" in m.group(1) or "+" in m.group(1):
            continue
        probs.append(f"{outp}: 루트 기준으로 변환되지 않은 상대 경로 {m.group(1)}")
# 스텁 검사
for f in pages:
    if f == "index.html":
        continue
    stub = read(f)
    if "noindex" not in stub or build.url_for(f) not in stub:
        probs.append(f"{f}: 이동 스텁 형식 이상 (noindex 또는 이동 주소 없음)")
for f in RETIRED_STUBS:
    if os.path.isfile(f) and "noindex" not in read(f):
        probs.append(f"{f}: 은퇴 스텁에 noindex 없음")
check(f"내부 링크·자산 경로 {len(seen)}개 유효, 이동 스텁 형식", probs)

# ---------------------------------------------------------------- 6. sitemap·rss
probs = []
try:
    tree = ET.parse("sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text.strip() for e in tree.getroot().findall("s:url/s:loc", ns)]
    expected = {f"{build.SITE_URL}{build.url_for(f)}" for f in pages}
    for u in locs:
        if u not in expected:
            probs.append(f"sitemap에 불필요한 주소: {u}")
    for u in sorted(expected - set(locs)):
        probs.append(f"sitemap에 빠진 주소: {u}")
    if len(locs) != len(set(locs)):
        probs.append("sitemap 중복 주소")
    sm_count = len(locs)
except Exception as e:
    probs.append(f"sitemap.xml 파싱 실패: {e}"); sm_count = 0
try:
    rtree = ET.parse("rss.xml")
    items = rtree.getroot().findall("channel/item")
    if not (1 <= len(items) <= 20):
        probs.append(f"rss 항목 수 이상: {len(items)}")
    for it in items:
        link = it.findtext("link", "")
        if not link.startswith(build.SITE_URL + "/news/"):
            probs.append(f"rss 링크 형식 이상: {link}")
except Exception as e:
    probs.append(f"rss.xml 파싱 실패: {e}")
check(f"sitemap.xml {sm_count}개 주소 일치, rss.xml 파싱", probs)

# ---------------------------------------------------------------- 7. 상수 반영
probs = []
apply_html = read(pages["expert-apply.html"])
expert_html = read(pages["expert.html"])
index_html = read("index.html")
hook = build.SHEET_WEBHOOK
if hook:
    if not (hook.startswith("https://script.google.com/macros/s/") and hook.endswith("/exec")):
        probs.append(f"SHEET_WEBHOOK 형식 이상: {hook}")
    if hook not in apply_html:
        probs.append("접수 페이지에 SHEET_WEBHOOK 미반영")
    if re.search(r"AKfycb[\w-]+", apply_html) and hook.split("/s/")[1].split("/")[0] not in apply_html:
        probs.append("접수 페이지의 웹훅 주소가 build.py 상수와 다름")
else:
    probs.append("SHEET_WEBHOOK 비어 있음 (메일 폴백으로 동작)")
for name, url in (("PAY_URL_L2", build.PAY_URL_L2), ("PAY_URL_L1", build.PAY_URL_L1)):
    # 결제 링크는 접수 완료 화면(자동 이동)에만 있으면 됨. expert 페이지의 직접 결제 버튼은 2026.09.13 제거
    if url and url not in apply_html:
        probs.append(f"{name} 미반영 ({url})")
# 2026.09.16 평가응시 2차 개편: 로그인 화면에 기본·심화 결제 버튼(새 창), 설정에 시험 시간·결제 링크·EXAM_API 주입
exam_html = read(pages["exam.html"])
for name, url in (("PAY_URL_L2", build.PAY_URL_L2), ("PAY_URL_L1", build.PAY_URL_L1)):
    if url and f'href="{url}" target="_blank" rel="noopener"' not in exam_html:
        probs.append(f"/exam/ 로그인 화면에 {name} 결제 버튼(새 창) 없음 ({url})")
if f'api:{json.dumps(build.EXAM_API)}' not in exam_html:
    probs.append("/exam/ 설정(window.KAIEC_EXAM)에 EXAM_API 미반영")
for course, (total, _pass), minutes in (("기본과정", build.EXAM_BASIC, build.EXAM_MIN_BASIC), ("심화과정", build.EXAM_ADV, build.EXAM_MIN_ADV)):
    if f'"{course}":{{total:{total},minutes:{minutes},' not in exam_html:
        probs.append(f"/exam/ 설정에 {course} 문항 수·시험 시간({total}문항·{minutes}분) 미반영")
if 'id="exLoginForm"' not in exam_html or 'id="exDemoBtn"' in exam_html:
    probs.append("/exam/ 로그인 화면 구성 이상 (로그인 폼 없음 또는 체험 버튼이 다시 들어감)")
if build.won(build.PRICE_L2) not in expert_html or build.won(build.PRICE_L2) not in index_html:
    probs.append(f"기본과정 특별가 {build.won(build.PRICE_L2)} 미반영")
if build.DEADLINE not in expert_html:
    probs.append(f"마감 {build.DEADLINE} 미반영")
if build.COPYCLEAN_URL not in read(pages["copyclean.html"]):
    probs.append("COPYCLEAN_URL 미반영")
if "/join/#apply" not in read(pages["apply.html"]):
    probs.append("apply 페이지가 통합 신청 폼(/join/#apply)으로 연결되지 않음")
if 'id="joinForm"' not in read(pages["join.html"]) or build.SHEET_WEBHOOK not in read(pages["join.html"]):
    probs.append("join 페이지 신청 폼 또는 시트 웹훅 미반영")
check("build.py 상수(웹훅·결제 링크·가격·마감·구글폼·평가응시 설정) 페이지 반영", probs)

# ---------------------------------------------------------------- 8. 배포 파일
probs = []
if not os.path.isfile("CNAME") or read("CNAME").strip() != "kaiec.kr":
    probs.append("CNAME 이 kaiec.kr 이 아님")
if not os.path.isfile("robots.txt") or f"Sitemap: {build.SITE_URL}/sitemap.xml" not in read("robots.txt"):
    probs.append("robots.txt 에 Sitemap 줄 없음")
if not os.path.isfile(".nojekyll"):
    probs.append(".nojekyll 없음")
if not os.path.isfile(".gitignore") or "__pycache__" not in read(".gitignore"):
    probs.append(".gitignore 에 __pycache__ 없음")
# 2026.09.16: Claude 데스크톱 앱이 내려받은 파일(평가 정답이 든 Code.gs 등)이 저장소 폴더의 'Claude outputs/'에 생기므로 반드시 제외
if os.path.isfile(".gitignore") and "Claude outputs/" not in read(".gitignore"):
    probs.append(".gitignore 에 'Claude outputs/' 없음(관리자 자료 유출 방지)")
if os.path.isdir("Claude outputs"):
    tracked = os.popen('git ls-files -- "Claude outputs"').read().strip()
    if tracked:
        probs.append("'Claude outputs/' 안의 파일이 git에 올라가 있음: " + tracked.replace("\n", ", "))
for f in ("assets/css/style.css", "assets/js/main.js", "assets/img/og-image.png", "assets/img/favicon.svg"):
    if not os.path.isfile(f):
        probs.append(f"필수 자산 없음: {f}")
vs = set(re.findall(r'style\.css\?v=([0-9a-zA-Z]+)', index_html) + re.findall(r'main\.js\?v=([0-9a-zA-Z]+)', index_html))
if len(vs) != 1:
    probs.append(f"index.html 캐시 버전 태그 이상: {vs}")
check("배포 파일(CNAME·robots·.nojekyll·.gitignore·필수 자산·캐시 버전)", probs)

# ---------------------------------------------------------------- 결과
fails = 0
for name, ok, plist in results:
    print(("  ✓ " if ok else "  ✗ ") + name)
    if not ok:
        fails += 1
        for p in plist[:25]:
            print("      - " + p)
        if len(plist) > 25:
            print(f"      ... 외 {len(plist) - 25}건")
print()
if fails:
    print(f"실패 {fails}건 / 검사 {len(results)}개  (고친 뒤 python3 build.py → python3 tools/verify.py 재실행)")
    sys.exit(1)
print(f"전체 통과 (검사 {len(results)}개, 페이지 {len(pages)}개, 게시글 {len(posts)}건, 사이트맵 {sm_count}개 주소)")
