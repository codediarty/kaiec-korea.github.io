# -*- coding: utf-8 -*-
"""한국AI윤리위원회 위원 명단 자동 반영 (GitHub Actions '위원 명단 자동 반영', 2026.10.05)

kaiec.kr/join/ 에서 1분 등록으로 위촉된 위원을 위원 활동 시스템(GET ?action=members.export)에서 받아
  - assets/auto/members.js            : window.KAIEC_AUTO_MEMBERS (위원 명단 · 명함이 합쳐 그림)
  - assets/img/members/auto-코드.jpg   : 명함 사진 480 · -240.jpg (아직 사이트에 없는 사진만 서버가 함께 보냄)
  - m/코드/index.html                  : 위원별 공유 주소(미리보기 · /members/#코드 로 넘김). 명단에서 빠지면 /members/ 로 넘기는 빈 쪽
을 고칩니다. 파일은 지우지 않습니다(운영자 컴퓨터 저장소와 합칠 때 지우기가 막힘). 명단에서 빠진 사진은 tools/collect_site.py 가 배포에서 뺍니다.
바뀐 게 있으면 GITHUB_OUTPUT 에 changed=true. 서버 응답이 이상하면(갑자기 절반 넘게 줄어듦 등) 아무것도 바꾸지 않습니다."""
import base64, io, json, os, re, sys, time, urllib.request

API = os.environ.get("KAIEC_API", "https://script.google.com/macros/s/AKfycbw3ZPLXHv92tfNVs7caH-Bf1OvMesqh0RfR8y4LCsT5DaE3otEbGWhyFLIY6FqoBEY/exec")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE_URL, SITE_NAME = "https://kaiec.kr", "한국AI윤리위원회"
LIST = os.path.join(ROOT, "assets", "auto", "members.js")
PHOTOS = os.path.join(ROOT, "assets", "img", "members")
CODE_RE = re.compile(r"^[A-Z]{2,4}\d{4}$")
NAME_RE = re.compile(r"^[가-힣a-zA-Z][가-힣a-zA-Z ·.'\-]{1,29}$")
EN_RE = re.compile(r"^[A-Za-z][A-Za-z '\-.]{1,39}$")
PHOTO_RE = re.compile(r"^auto-[a-z]{2,4}\d{4}(-\d{1,2})?\.jpg$")
EMAIL_RE = re.compile(r"^[^@\s<>\"']{1,64}@[A-Za-z0-9.\-]{1,120}\.[A-Za-z]{2,}$")
SINCE_RE = re.compile(r"^\d{4}\.\d{2}$")
changed = []


def out(k, v):
    f = os.environ.get("GITHUB_OUTPUT")
    if f:
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(f"{k}={v}\n")


def fetch():
    last = None
    for k in range(3):
        try:
            req = urllib.request.Request(API + "?action=members.export&t=" + str(int(time.time())), headers={"User-Agent": "kaiec-members-sync"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:   # 앱스 스크립트가 잠깐 늦을 때
            last = e
            time.sleep(8 * (k + 1))
    raise SystemExit(f"서버에서 명단을 받지 못했습니다: {last}")


def write_if(path, data, binary=False):
    old = None
    if os.path.isfile(path):
        with open(path, "rb") as fp:
            old = fp.read()
    new = data if binary else data.encode("utf-8")
    if old == new:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fp:
        fp.write(new)
    changed.append(os.path.relpath(path, ROOT))
    return True


def jpeg(b64):
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        return None
    return raw if raw[:3] == b"\xff\xd8\xff" and 1000 < len(raw) < 400000 else None


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def member_page(m, cards):
    """build.py build_member_pages 와 같은 짜임(빌드 때 보안 다듬기가 더해짐). 표시용 kaiec-auto 꼬리표"""
    code, name = m["code"], m["name"]
    role = "AI 윤리 교육위원" if m.get("track") == "교육" else "AI 윤리 캠페인위원"
    title = f"{name} {role} · 디지털 명함"
    desc = f"한국AI윤리위원회 {role} {name}의 디지털 명함입니다. 명함에서 AI윤리전문가(AIEP) 양성과정을 알아보고 위원 추천 할인으로 바로 신청하실 수 있습니다."
    img = f"{SITE_URL}/assets/mail/card/{code}.jpg" if code in cards else f"{SITE_URL}/assets/img/og-image.jpg"
    iw, ih = ("640", "389") if code in cards else ("1200", "630")
    dest, url = f"/members/#{code}", f"{SITE_URL}/m/{code.lower()}/"
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="kaiec-auto" content="1">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{SITE_URL}/members/">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="ko_KR">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="{iw}">
<meta property="og:image:height" content="{ih}">
<meta property="og:image:alt" content="{esc(name)} 위원 디지털 명함">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{img}">
<meta http-equiv="refresh" content="1;url={dest}">
<style>
html,body{{margin:0;height:100%;background:#fff}}
body{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding-bottom:16vh;box-sizing:border-box;
  font:600 16px/1.5 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#1d2433}}
.spin{{width:34px;height:34px;box-sizing:border-box;border:3px solid #d9e1ee;border-top-color:#1f5fe0;border-radius:50%;animation:s .8s linear infinite}}
@keyframes s{{to{{transform:rotate(360deg)}}}}
a{{color:#1f5fe0;font-weight:500;font-size:14px}}
</style>
<script>location.replace({json.dumps(dest)});</script>
</head><body>
<span class="spin" aria-hidden="true"></span>
<span role="status">{esc(name)} 위원의 디지털 명함을 여는 중입니다</span>
<a href="{dest}">명함이 열리지 않으면 여기를 눌러 주세요</a>
</body></html>
"""


GONE_PAGE = ('<!DOCTYPE html>\n<html lang="ko"><head><meta charset="UTF-8">\n<meta name="kaiec-auto" content="1">\n<title>위원 명단 | ' + SITE_NAME + '</title>\n'
             '<meta name="robots" content="noindex, follow">\n<link rel="canonical" href="' + SITE_URL + '/members/">\n<meta http-equiv="refresh" content="0;url=/members/">\n'
             '<script>location.replace("/members/");</script>\n</head><body><p><a href="/members/">위원 명단으로 이동</a></p></body></html>\n')


def main():
    j = fetch()
    if not isinstance(j, dict) or j.get("v") != 1 or not isinstance(j.get("members"), list):
        raise SystemExit("서버 응답 형식이 맞지 않습니다: " + json.dumps(j, ensure_ascii=False)[:200])
    old = []
    if os.path.isfile(LIST):
        try:
            t = open(LIST, encoding="utf-8").read()
            old = json.loads(t[t.index("["):t.rindex("]") + 1])
        except Exception:
            old = []
    ms, seen = [], set()
    for e in j["members"]:
        code = str(e.get("code", ""))
        name = str(e.get("name", "")).strip()
        if not CODE_RE.match(code) or code in seen or not NAME_RE.match(name):
            continue
        seen.add(code)
        en = str(e.get("en", "")).strip()
        field = re.sub(r"[<>&\"'`\\]", "", str(e.get("field", ""))).strip()[:30]
        since = str(e.get("since", "")).strip()
        email = str(e.get("email", "")).strip()
        photo = str(e.get("photo", "")).strip()
        m = {"code": code, "name": name, "en": en if EN_RE.match(en) else "", "field": field, "since": since if SINCE_RE.match(since) else "",
             "track": "교육" if e.get("track") == "교육" else "", "photo": photo if PHOTO_RE.match(photo) else ""}
        if email and EMAIL_RE.match(email):
            m["email"] = email
        # 사진: 서버가 보낸 base64(아직 사이트에 없는 것)만 씀. 파일이 없고 받지도 못했으면 사진 없이(이름 첫 글자)
        if m["photo"]:
            big = os.path.join(PHOTOS, m["photo"]); small = big[:-4] + "-240.jpg"
            raw = jpeg(e.get("p", "")) if e.get("p") else None
            if raw:
                write_if(big, raw, binary=True)
                raw_s = jpeg(e.get("ps", "")) if e.get("ps") else None
                write_if(small, raw_s or raw, binary=True)
            if not os.path.isfile(big):
                m["photo"] = ""
            elif not os.path.isfile(small):
                write_if(small, open(big, "rb").read(), binary=True)
        ms.append(m)
    if len(old) >= 4 and len(ms) < len(old) * 0.5:
        print(f"! 서버 명단이 {len(old)} → {len(ms)}명으로 크게 줄어 이번에는 바꾸지 않습니다(다음 실행에서 다시 확인).")
        out("changed", "false")
        return 0
    body = ("/* 한국AI윤리위원회 자동 등록 위원 명단(저장소 자동 작업이 고침) */\nwindow.KAIEC_AUTO_MEMBERS="
            + json.dumps(ms, ensure_ascii=False, separators=(",", ":")) + ";\n")
    write_if(LIST, body)
    # 위원별 공유 주소
    cards = set()
    try:
        cards = set(json.load(open(os.path.join(ROOT, "assets", "mail", "card", "index.json"), encoding="utf-8")).get("codes") or [])
    except Exception:
        cards = set()
    now = {m["code"] for m in ms}
    for m in ms:
        path = os.path.join(ROOT, "m", m["code"].lower(), "index.html")
        cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
        if cur and ("Content-Security-Policy" in cur or 'name="kaiec-auto"' not in cur):
            continue   # 빌드가 만든(보안 다듬기 된) 쪽은 그대로
        write_if(path, member_page(m, cards))
    for o in old:
        c = str(o.get("code", "")) if isinstance(o, dict) else ""
        if CODE_RE.match(c) and c not in now:
            path = os.path.join(ROOT, "m", c.lower(), "index.html")
            if os.path.isfile(path) and 'name="kaiec-auto"' in open(path, encoding="utf-8").read():
                write_if(path, GONE_PAGE)
    print(f"위원 {len(ms)}명 · 바뀐 파일 {len(changed)}개")
    for c in changed[:50]:
        print("  ", c)
    out("changed", "true" if changed else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
