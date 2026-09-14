# -*- coding: utf-8 -*-
"""OG 이미지 + 게시글 썸네일 30개 생성 (Playwright HTML 렌더)"""
import io, os, re, glob
from playwright.sync_api import sync_playwright
SITE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 저장소 루트
OUT=f"{SITE}/assets/img/posts"

CAT_COLOR={"공지":"#5B8DEF","칼럼":"#6FE3D8","연구·정책":"#9FB7FF","캠페인":"#F5C451"}

# slug → (대표 문구, 부제)
LABELS={
 "2024-03-15-founding":("한국AI윤리위원회 출범","설립 취지와 초대 임원진 안내"),
 "2025-03-14-first-anniversary":("설립 1년, 걸어온 길","한국AI윤리위원회 1주년"),
 "2025-05-20-company-checklist":("기업 AI 윤리 체크리스트 7가지","생성형 AI 도입 전 점검"),
 "2025-07-08-school-ai-ethics-edu":("학교·공공기관 AI 윤리교육","사용법 교육만으로는 부족한 이유"),
 "2025-09-16-genai-copyright":("생성형 AI 저작권 논란 정리","창작과 연구 현장의 기준"),
 "2025-11-11-ai-act-preview":("AI기본법 시행을 앞두고","기업과 기관이 준비해야 할 것"),
 "2026-02-05-ai-act-first-month":("AI기본법 시행 한 달","현장에서 가장 많이 받은 질문 5가지"),
 "2026-06-10-new-president":("제2대 위원장 취임","신동복 위원장"),
 "2026-07-02-executive-appointments":("신임 임원진 선임","부위원장 · 사무총장 · 감사"),
 "2026-07-28-university-ai-policy-2026":("2026 대학가 AI 정책의 방향","'금지'에서 '표기'로"),
 "2026-07-30-ai-writing-traits":("AI가 쓴 글의 특징 10가지","전문가는 어떻게 구별하는가"),
 "2026-08-01-journal-submission-ai-check":("학술지 투고 전 AI 검사","게재 철회를 부르는 3가지 실수"),
 "2026-08-03-student-report-ai-guide":("과제·레포트 AI 활용 가이드","대학생이 안전하게 챗GPT 쓰는 법"),
 "2026-08-05-advisors-experts":("고문·자문위원 및 전문위원 위촉","위원회 전문성을 뒷받침할 전문가"),
 "2026-08-05-ai-fake-references":("AI가 만든 가짜 참고문헌","DOI 검증이 필수가 된 이유"),
 "2026-08-07-copyclean-precheck-guide":("제출 전 AI 유사도 사전점검","카피클린 활용 가이드"),
 "2026-08-10-jaso-ai-check":("자기소개서 AI 검사 시대","챗GPT로 쓴 자소서, 기업은 알아볼까"),
 "2026-08-12-thesis-ai-citation-guide":("논문 AI 활용 표기 가이드","어디까지 쓰고, 어떻게 밝힐 것인가"),
 "2026-08-14-thesis-consulting-ethics":("논문컨설팅, 어디까지 허용될까","연구윤리 기준으로 보는 선택 가이드"),
 "2026-08-16-false-positive-response":("안 썼는데 AI로 판정됐다면","억울한 AI 판정에 대응하는 법"),
 "2026-08-17-precheck-campaign":("제출 전 사전점검 캠페인","AI 활용 문서, 스스로 확인하는 문화"),
 "2026-08-17-recruit":("전문위원 · AI 윤리위원 상시 모집","전공·경력 무관, 온라인 활동"),
 "2026-08-17-website-open":("공식 홈페이지 개설","kaiec.kr"),
 "2026-08-18-how-ai-detectors-work":("AI 검사기의 원리","AI가 쓴 글은 어떻게 탐지되는가"),
 "2026-08-19-ai-detection-bypass-risk":("AI 탐지 우회 도구의 실체","위원회가 사용을 권하지 않는 5가지 이유"),
 "2026-08-20-lower-ai-similarity":("AI 유사도 낮추기 전에","반드시 알아야 할 올바른 대응"),
 "2026-08-21-ai-similarity-check-guide":("AI 유사도 검사 가이드","제출 전 확인 절차"),
 "2026-08-22-new-members":("신규 회원사 안내","성균관대학교 RISE사업단 · 성균관컨설팅 · 카피클린"),
 "2026-09-10-fellowship-1st-recruit":("AI Ethics Fellowship 1기 모집","협력기관 모집 안내"),
 "2026-09-11-ai-ethics-expert-intro":("AI윤리전문가란 누구인가","AI 시대가 찾는 유망 전문 자격"),
}

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:630px;overflow:hidden;font-family:"Pretendard","Noto Sans CJK KR","Noto Sans KR",sans-serif;
  background:#0A1628;color:#fff;position:relative}
.bg{position:absolute;inset:0;
  background:
    radial-gradient(900px 460px at 88% -10%,rgba(0,180,166,.22),transparent 62%),
    radial-gradient(760px 420px at 6% 12%,rgba(31,95,224,.36),transparent 60%),
    linear-gradient(135deg,#0A1628 0%,#0F2A5F 58%,#0B1B3A 100%)}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),
  linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:60px 60px;
  mask-image:linear-gradient(90deg,transparent 30%,#000 100%);-webkit-mask-image:linear-gradient(90deg,transparent 30%,#000 100%)}
.ring{position:absolute;border-radius:50%;border:1.5px solid rgba(159,196,255,.22)}
.r1{width:520px;height:520px;right:-140px;top:60px}
.r2{width:340px;height:340px;right:-50px;top:150px;border-color:rgba(111,227,216,.28)}
.r3{width:180px;height:180px;right:30px;top:230px;border-color:rgba(255,255,255,.14)}
.orb{position:absolute;right:75px;top:275px;width:90px;height:90px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%,#8FB7FF,#1F5FE0 60%,#0F2A5F);box-shadow:0 0 60px rgba(111,227,216,.45)}
.bar{position:absolute;left:0;top:0;bottom:0;width:14px}
.wrap{position:absolute;left:76px;top:0;bottom:0;right:80px;display:flex;flex-direction:column;justify-content:space-between;padding:60px 0 54px}
.brand{display:flex;align-items:center;gap:16px}
.badge{background:#0F2A5F;border:2px solid rgba(255,255,255,.55);color:#fff;font-weight:900;letter-spacing:.2em;
  font-size:21px;padding:12px 18px;border-radius:12px;box-shadow:inset 0 0 0 3px #0F2A5F,inset 0 0 0 4px rgba(255,255,255,.35)}
.bko{font-family:"Noto Serif CJK KR","Noto Serif CJK SC",serif;font-weight:900;font-size:34px;letter-spacing:-.02em;line-height:1}
.ben{font-size:12.5px;letter-spacing:.24em;color:#A9C0E0;font-weight:700;margin-top:6px}
.chip{display:inline-flex;align-items:center;gap:10px;font-size:19px;font-weight:800;letter-spacing:.06em;
  padding:9px 18px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}
.chip i{width:10px;height:10px;border-radius:50%;display:inline-block}
h1{font-size:64px;font-weight:900;line-height:1.22;letter-spacing:-.035em;max-width:820px;margin-top:22px;text-wrap:balance}
.sub{font-size:27px;color:#C4D4EC;margin-top:18px;max-width:800px;line-height:1.5;font-weight:500}
.foot{display:flex;justify-content:space-between;align-items:flex-end;font-size:19px;color:#A9C0E0;font-weight:600}
.accent{background:linear-gradient(96deg,#6FE3D8,#8FB7FF);-webkit-background-clip:text;background-clip:text;color:transparent}
"""

def post_html(cat, color, title, sub, date):
    return f"""<html><head><meta charset="utf-8"><style>{BASE_CSS}</style></head><body>
<div class="bg"></div><div class="grid"></div>
<div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div><div class="orb"></div>
<div class="bar" style="background:linear-gradient(180deg,{color},rgba(255,255,255,.08))"></div>
<div class="wrap">
  <div>
    <span class="chip"><i style="background:{color}"></i>{cat}</span>
    <h1>{title}</h1>
    <div class="sub">{sub}</div>
  </div>
  <div class="foot">
    <div class="brand"><div class="badge">KAIEC</div><div><div class="bko">한국AI윤리위원회</div><div class="ben">KOREA AI ETHICS COMMITTEE</div></div></div>
    <div>{date}</div>
  </div>
</div></body></html>"""

OG_HTML = f"""<html><head><meta charset="utf-8"><style>{BASE_CSS}
h1{{font-size:58px;margin-top:26px;max-width:900px}}
.sub{{font-size:25px;margin-top:20px}}
.chips{{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}}
.chips span{{font-size:17px;font-weight:700;padding:9px 16px;border-radius:999px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.18);color:#E6EEF9}}
</style></head><body>
<div class="bg"></div><div class="grid"></div>
<div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div><div class="orb"></div>
<div class="wrap">
  <div>
    <div class="brand"><div class="badge">KAIEC</div><div><div class="bko">한국AI윤리위원회</div><div class="ben">KOREA AI ETHICS COMMITTEE</div></div></div>
    <h1>한국AI윤리위원회(KAIEC)<br><span class="accent">책임 있는 AI 활용을 위한 전문기관</span></h1>
    <div class="sub">AI 윤리 교육 · 연구 · 캠페인 · AI윤리전문가 양성 및 국내외 협력</div>
  </div>
  <div class="chips"><span>AI윤리전문가 자격과정</span><span>AI 윤리 교육 · 출강</span><span>사전점검 캠페인</span><span>기업 · 기관 협력</span></div>
</div></body></html>"""

def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width":1200,"height":630}, device_scale_factor=1)
        # OG
        pg.set_content(OG_HTML); pg.wait_for_timeout(300)
        pg.screenshot(path=f"{SITE}/assets/img/og-image.png", clip={"x":0,"y":0,"width":1200,"height":630})
        print("og-image.png 생성")
        # posts
        n=0
        for md in sorted(glob.glob(f"{SITE}/posts-src/*.md")):
            slug = os.path.basename(md)[:-3]
            s = io.open(md, encoding="utf-8").read()
            cat = re.search(r"^분류:\s*(.+)$", s, re.M).group(1).strip()
            date = re.search(r"^날짜:\s*(.+)$", s, re.M).group(1).strip()
            title, sub = LABELS.get(slug, (re.search(r"^제목:\s*(.+)$", s, re.M).group(1).strip(), ""))
            color = CAT_COLOR.get(cat, "#5B8DEF")
            pg.set_content(post_html(cat, color, title, sub, date)); pg.wait_for_timeout(120)
            fn = f"thumb-{slug}.jpg"
            pg.screenshot(path=f"{OUT}/{fn}", type="jpeg", quality=86, clip={"x":0,"y":0,"width":1200,"height":630})
            # md 이미지 필드 갱신
            s2 = re.sub(r"^이미지:.*$", f"이미지: {fn}", s, count=1, flags=re.M)
            io.open(md, "w", encoding="utf-8").write(s2)
            n+=1
        print("썸네일", n, "개 생성 + md 갱신")
        b.close()

if __name__ == "__main__":
    main()
