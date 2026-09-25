# -*- coding: utf-8 -*-
"""
한국AI윤리위원회(KAIEC) 정적 사이트 빌더
- 공통 헤더/푸터를 각 HTML에 그대로 박아 넣어 완전한 정적 파일을 생성합니다.
  (JS로 헤더를 그리면 네이버 크롤러가 메뉴를 못 읽는 경우가 있어 이렇게 처리)
- 메뉴나 푸터를 바꾸려면 이 파일을 수정하고 `python3 build.py`를 다시 실행하세요.
"""
import os, io, re, glob, datetime
import html as _html
from icons import ICONS

BASE = os.path.dirname(os.path.abspath(__file__))

_ICON_RE = re.compile(r'<i data-lucide="([a-z0-9\-]+)"([^>]*)></i>')


def inline_icons(html):
    """<i data-lucide="x"> 를 실제 SVG로 치환합니다.
    외부 CDN(unpkg 등)에 의존하지 않으므로 인터넷 상황과 무관하게 아이콘이 항상 표시됩니다."""
    def rep(m):
        name, attrs = m.group(1), m.group(2)
        inner = ICONS.get(name)
        if inner is None:
            return ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
                'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                'stroke-linejoin="round" aria-hidden="true"%s>%s</svg>' % (attrs, inner))
    return _ICON_RE.sub(rep, html)
SITE_URL = "https://kaiec.kr"                 # 실제 배포 주소 (커스텀 도메인)
SITE_NAME = "한국AI윤리위원회"
SITE_EN = "Korea AI Ethics Committee"         # 홈페이지·로고용 영문명 (KAIEC = Korea AI Ethics Committee)
SITE_EN_FORMAL = "Korea AI Ethics Committee"  # 공식 영문 명칭 (위원회 소개 개요표 표기용, 브랜드명과 동일)
EMAIL = "contact@kaiec.kr"                     # ← 대표 문의 메일 (2026.09.22 공식 도메인 메일로 전환. 수신은 ImprovMX → kaiec.korea@gmail.com 전달, 발신은 지메일 별칭)
# (구) 위원 지원서 구글폼. 2026.09.13부터 위원·회원기관 신청은 자체 폼(join.html → 시트 웹훅)으로 받으므로 CTA에서는 사용하지 않음
GOOGLE_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSezVLiJJVsieoUS2gLRt2Y22MmwhO3MtWevR-tPaJPmoYra4Q/viewform"
# 카피클린 문서검사 바로가기 (모든 카피클린 CTA가 이 주소로 연결됨)
COPYCLEAN_URL = "https://skkc.co.kr/ai-detector"
# AI윤리전문가 양성과정 교육비 결제 링크 (성균관컨설팅 skkc.co.kr 안전결제 PG)
# 결제 링크가 발급되면 아래에 넣고 재실행하세요. 비워두면 결제 버튼이 표시되지 않고
# 신청 폼 완료 화면에서 결제를 안내하는 흐름으로 운영합니다.
# 2026.09.21 기본·심화를 하나의 「AI윤리전문가 양성과정」으로 통합. 결제 상품은 skkc.co.kr idx=26 하나만 씁니다
# (idx=27 심화과정 상품은 더 이상 사이트에서 연결하지 않음). 평가 백엔드 Code 1.5.0(통합판)은 결제 메일 상품명에
# 'AI윤리전문가' 또는 '양성과정'만 있으면 통합 과정으로 자동 등록하므로, 1.5.0 배포 뒤에는 idx=26 상품명에서 '기본과정' 표기를 빼도 됩니다
# (1.4.4 이하가 돌고 있는 동안에는 '기본과정' 표기를 남겨 두어야 자동 등록이 됩니다).
PAY_URL = "https://skkc.co.kr/shop_view?idx=26"      # AI윤리전문가 양성과정 교육비 결제 링크
# 수강 신청을 구글 스프레드시트로 자동 수집하는 앱스 스크립트 웹 앱 주소(/exec 로 끝남).
# 시트에 연결되면 이 주소를 넣고 재실행하세요. 비어 있으면 신청 내용이 메일 앱으로 발송됩니다.
SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbzgaREsZ8Y89wem8ovbC9tsFhQzwDH458kadx9qvpGVvdkeE5XCkjqBG9BB4dwnTbly/exec"
# 양성과정 가격 정보 (변경 시 여기만 수정 후 재실행: expert·신청 폼·메인 배너·게시글 배너에 일괄 반영)
LIST_PRICE, PRICE = 300000, 99000      # 통합 과정 정가 / 특별가 (2026.09.21 통합하며 149,000원 → 99,000원, 09.22 정가 290,000 → 300,000원. skkc.co.kr idx=26 상품 가격도 같이 맞출 것)
PRICE_SHORT = "9.9만원"                  # 제목·배지용 짧은 표기 (PRICE를 바꾸면 이것도 함께)
# 2026.09.23: 기수(1기)·'모집 중'·접수 마감·D-day 표기는 '이제 막 시작한 곳'처럼 보인다는 판단으로 사이트 전체에서 뺐습니다.
# DEADLINE·DEADLINE_ISO·HOOK_AFTER 상수도 삭제했고, verify.py 가 기수·마감 표기의 재유입을 막습니다.
# 2026.09.21: '연 100명 한정 양성'(QUOTA) 표기는 과정이 작아 보인다는 판단으로 사이트 전체에서 뺐습니다 (verify.py가 '명 한정' 재유입을 막음).
# 쓰는 표기: 특별가(정가 대비), 전 과정 100% 온라인, 결제 당일 시작, 이수 즉시 공식 등재 (2026.09.22 '추가 비용' 표기는 사이트 전체에서 뺌)
HOOK_ZERO = "전 과정 100% 온라인"        # 2026.09.22: 사이트 전체에서 '추가 비용' 표기를 빼기로 해 이 훅을 100% 온라인으로 교체(변수명은 유지)
HOOK_START = "결제 당일 학습 시작"       # 결제 즉시 학습자료(PDF) 발송, 준비되면 바로 응시
HOOK_REG = "이수 즉시 공식 등재"         # 이수와 동시에 홈페이지 공식 등록
# 2026.09.22 채용 통계 (Microsoft · LinkedIn 2024 Work Trend Index, 31개국 31,000명): 리더 71%는 AI 역량 없는 경력자보다 AI 역량 있는 저경력자를 뽑겠다, 66%는 AI 역량 없으면 채용 안 한다.
# /expert/ Career Value 띠와 신청 폼 머리글에 같은 문구를 씁니다 (수치·출처는 STAT_71로 한 곳에서 관리).
STAT_71 = {
    "num": "71%",
    "head": "이제는 전 세계 리더의 71%가 경력보다 AI 역량을 먼저 봅니다.",
    "body": "AI 역량이 없는 경력자보다 <strong>AI 역량을 갖춘 저경력자를 채용하겠다</strong>는 리더가 71%, AI 역량이 없으면 채용하지 않겠다는 리더가 66%입니다. "
            "이력서의 AI 역량은 이제 '있으면 좋은 것'이 아니라 가장 먼저 보는 평가 기준입니다.",
    "src": "출처: Microsoft · LinkedIn, 2024 Work Trend Index (31개국 31,000명 조사)",
}
POSTS_LASTMOD = "2026-09-14"            # 게시글 전체 틀이 바뀐 마지막 날짜 (사이트맵 lastmod 하한: 기관명 원복)
# 양성과정 표기 (2026.09.14): 등록된 자격 제도가 아니므로 인증(자격)·검정·급수 표현은 쓰지 않습니다 (금지 표기는 tools/verify.py OLD_NAMES 참고).
# 2026.09.16부터 '이수 평가·이수증·이수 기준·이수자 명부·이수번호·미이수'로 표기합니다 (옛 표기가 다시 들어오면 verify.py가 알려 줌).
# 이수증 앞 수식은 '한국AI윤리위원회 공식'으로 통일하고('명의'는 쓰지 않음). 2026.09.21 통합: 이수 = 위원회 공식 등록(이수자 명부·홈페이지 등재) + 전문위원 등록 신청 자격
PROG = "AI윤리전문가 양성과정"
DOC = "이수증"
DOC_FULL = f"{PROG} {DOC}"                # 「AI윤리전문가 양성과정 이수증」
PROG_EN = "AI Ethics Professional, Korea AI Ethics Committee"  # 이력서 영문 표기 (2026.09.22: 약어 KAIEC 대신 기관명을 풀어 씀. 이수번호 KAIEC-E-연도-일련번호가 약어를 대신함)
RESUME_KO = "AI윤리전문가 · 한국AI윤리위원회 이수"          # 이력서 국문 한 줄 (뒤에 이수번호 No. KAIEC-E-2026-0001 을 붙임)
RESUME_NO = "No. KAIEC-E-2026-0001"                    # 이력서 예시용 이수번호 형식
EXAM = (40, 70)                           # 이수 평가: 문항 수, 이수 기준 점수 (통합 과정. 백엔드 Code 1.5.0의 「AI윤리전문가 양성과정」 평가와 같음)
EXAM_MIN = 60                             # 시험 시간(분): 응시자가 [시험 시작]을 누른 때부터
# 평가 백엔드가 1.4.4 이하로 돌고 있으면 계정의 과정이 '기본과정'·'심화과정'으로 올 수 있으므로 /exam/ 설정에는 옛 값도 함께 넣어 둡니다 (호환용, 사이트에는 표시하지 않음)
EXAM_LEGACY_ADV = (50, 70)
EXAM_MIN_LEGACY_ADV = 75
EXAM_WINDOW_DAYS = 30                     # 응시 가능 기간: 결제일부터 30일
# 수강생에게 제공하는 학습자료 (과정 설명에 한 줄로 표기, 2026.09.16)
MATERIALS = "『핵심이론』 표준교재, 실전 모의고사 2회분, 정답 및 해설 별책, 『실무 도구집』, 이수 평가 응시 안내"   # 5종 모두 PDF로 제공
# 이수 평가 시스템(/exam/) 백엔드: '평가 운영 시트'에 연결된 앱스 스크립트 웹 앱 주소(/exec). 접수용 SHEET_WEBHOOK과는 별개 프로젝트입니다.
# 비어 있으면 로그인 카드에 '평가 시스템 연결 준비 중'을 표시하고 체험 모드(브라우저 안 모의 평가)만 동작합니다.
EXAM_API = "https://script.google.com/macros/s/AKfycbzgPS8uXz2Xqjfy4PxtFOIbBV31GqHwxYc4ZT12F8zrQkFKQAG0v96UGy8Yg2U2b4MYsQ/exec"
# 학습 방식 (2026.09.16: 온라인 강의를 없애고 위원회 표준교재 자율학습 + 온라인 이수 평가로 전환)
STUDY_MONTHS = 30                          # 2024년 3월 연구 착수 이후 산학 공동 연구·집필 기간(개월)
TEXTBOOK_CH = 9                            # 표준교재 장 수 (PART I 기초 개념 제1~2장 · II AI 활용과 윤리 제3~4장 · III 주요 위험과 사례 제5~7장 · IV 실무 적용 제8~9장 · V 종합 정리, 부록 A~D)
TEXTBOOK_PAGES = 232                       # 『핵심이론』 개정 디자인판 쪽수 (2026.09.22 사용자 제공 개정 디자인 PDF 5종 기준. 합계 372쪽: 13+232+31+20+76. 이전 통합판은 153/214)
MATERIAL_PAGES = 372                       # 학습자료 5종 PDF 합계 쪽수 (개정 디자인판)
# 재응시 표기 (2026.09.16): '무제한'을 앞세우면 평가가 가벼워 보이므로, 기준은 그대로 두고 기회만 열어 둔다는 뜻으로 적습니다
RETAKE = "기준에 이를 때까지 재응시"           # 응시 기간 안에서는 응시 횟수를 제한하지 않습니다
RETAKE_LONG = "기준은 낮추지 않되, 응시 기간 안에서는 기준에 이를 때까지 다시 응시하실 수 있습니다."
# 제공 학습자료 5종: (제목, 분량 표기, 설명, 키워드 칩)  ※ 2026.09.21 통합 교재 완성판 기준(쪽수는 실제 PDF)
MATERIAL_ITEMS = [
    ("『핵심이론』 표준교재", f"{TEXTBOOK_PAGES}쪽 · {TEXTBOOK_CH}개 장 · 부록 4종",
     "기초 개념(제1~2장), AI 활용과 윤리(제3~4장), 주요 위험과 사례(제5~7장), 실무 적용(제8~9장)의 네 부와 종합 정리·시험 대비, "
     "부록(핵심 용어 74개 · 국내외 규범 비교표 · AI 윤리 연표 · 암기 노트 60)까지 한 권에 담은 본 과정의 중심 교재입니다. "
     "장마다 학습 목표와 출제 포인트, 핵심 정리, 단원 확인문제가 붙어 있어 처음 보는 분도 순서대로 따라가면 됩니다.",
     ["AI 윤리 핵심 가치", "국제 원칙 · 법제", "거버넌스 · 사례 분석", "단원 확인문제 · 해설"]),
    ("실전 모의고사 2회분", "2회 × 40문항 · OMR 답안지",
     "실제 이수 평가와 같은 출제 기준표(5개 영역 · 40문항 · 60분)와 난이도로 구성한 모의고사 2회분입니다. OMR 형식 답안지가 함께 들어 있어 시간을 재며 실전처럼 풀어볼 수 있습니다.",
     ["실제 평가와 동일 형식", "2회분 수록", "OMR 답안지 포함"]),
    ("정답 및 해설 별책", "80문항 해설 · 근거 절 표시",
     "모의고사 80문항의 정답과 함께 왜 그 답인지의 근거를 조문·원칙 단위로 풀어 둔 별책입니다. 해설마다 교재의 근거 절이 표시되어 틀린 문항이 어느 영역에 몰려 있는지 스스로 점검할 수 있습니다.",
     ["문항별 근거 해설", "영역별 약점 점검"]),
    ("『실무 도구집』", "실무 양식 13종 · 활용 안내",
     "배운 내용을 다음 주 업무에 바로 옮기기 위한 실무 양식 13종입니다. 조직 AI 활용 가이드라인, AI 시스템 인벤토리, 고영향 AI 점검표, 윤리영향평가 보고서, 데이터시트·모델 카드, 공급업체 실사표, 사고 보고서, AI 윤리위원회 운영 규정 등 그대로 고쳐 쓰는 형태로 수록했습니다.",
     ["실무 양식 13종", "사내 AI 기준", "AI 활용 고지문"]),
    ("이수 평가 응시 안내", "출제 기준표 · 7일 학습 플랜 · FAQ",
     "출제 기준표와 영역별 문항 비중, 응시 절차, 유의사항, 재응시와 이수증 발급, 자주 묻는 질문을 정리한 안내서입니다. 무엇이 어디에서 몇 문항 나오는지 미리 알고 공부할 수 있습니다.",
     ["출제 기준표", "영역별 문항 비중", "응시 절차 안내"]),
]
# 학습자료 다시 내려받기(/exam/ 로그인 후 보조 패널, 2026.09.22 백엔드 Code 1.5.6 materials): 학습자료 5종은 안내 메일의 내려받기 링크로 나가고,
# 이 패널은 메일을 잃어버린 수강생용입니다. 드라이브 파일 이름 앞 번호(00~04)로 짝을 맞춰 제목·분량·아이콘을 붙이고, 번호가 없는 파일은
# 파일 이름 그대로 보여 줌. mb 는 체험 모드 표시용 대략값(실제 화면은 서버가 준 용량)
MATERIAL_FILES = [
    ("00", "이수 평가 응시 안내", "13쪽 · 출제 기준표 · 7일 학습 플랜", "clipboard-list", 0.2),
    ("01", "『핵심이론』 표준교재", f"{TEXTBOOK_PAGES}쪽 · {TEXTBOOK_CH}개 장 · 부록 4종", "book-open", 82),
    ("02", "실전 모의고사 2회분", "31쪽 · 2회 × 40문항 · OMR 답안지", "pen-line", 7.5),
    ("03", "정답 및 해설 별책", "20쪽 · 80문항 해설 · 근거 절 표시", "file-check", 5.6),
    ("04", "『실무 도구집』", "76쪽 · 실무 양식 13종", "file-text", 12.6),
]
# 이수자에게 주는 것 (2026.09.21 통합 과정의 핵심 혜택. expert·experts·신청 폼에서 함께 씀): (아이콘, 제목, 설명)
BENEFITS = [
    ("award", "한국AI윤리위원회 공식 이수증",
     "이수번호가 기재된 「AI윤리전문가 양성과정 이수증」(PDF). 이력서 교육·연수 칸에 그대로 씁니다."),
    ("file-search", "홈페이지 공식 등록 · 검색",
     "이수 즉시 위원회 홈페이지에 AI윤리전문가로 등록. 이름과 이수번호로 누구나 검색할 수 있습니다."),
    ("pen-line", "이력서 · 자기소개서 활용 가이드",
     "이력서 어느 칸에 어떻게 쓰는지, 자기소개서 문장 예시와 면접 답변 포인트까지. 이수자 전용 가이드."),
    ("id-card", "이력서 가이드",
     f"국문: {RESUME_KO} ({RESUME_NO}) / 영문: {PROG_EN} ({RESUME_NO}). 이대로 적으면 됩니다."),
    ("briefcase", "『실무 도구집』 양식 13종",
     "사내 AI 사용 기준, AI 활용 고지문, 위험도 점검표 등. 고쳐 쓰는 실무 양식, 이수 뒤에도 계속 씁니다."),
    ("user-check", "위원회 전문위원 지원 자격",
     "이수자는 전문위원 등록을 신청할 수 있습니다. 등록되면 프로필 공개, 전문강사·자문 활동으로 이어집니다."),
    ("shield-check", "위원회가 직접 확인해 주는 이력",
     "기업·기관·학교가 문의하면 위원회가 이수 사실을 확인해 드립니다. 위원회가 뒷받침하는 이력입니다."),
    ("heart-handshake", "위원회 공식 활동 참여",
     "AI 윤리 캠페인, Fellowship, 지역 운영위원·캠퍼스 위원장 지원 자격. 활동 경력이 더해집니다."),
]
def won(n): return f"{n:,}원"


def exam_text():
    """평가 구성 한 줄: '40문항 · 60분 · 70점 이상' """
    return f"{EXAM[0]}문항 · {EXAM_MIN}분 · {EXAM[1]}점 이상"


# =============================================================================
#  소식 게시판 (블로그) 엔진
#  - posts-src/ 폴더의 .md 파일 1개 = 게시글 1개 (개별 HTML 페이지로 생성 → SEO 최적)
#  - 파일명이 곧 주소가 됩니다: posts-src/2026-08-17-open.md → post-2026-08-17-open.html
#  - 작성법은 posts-src/_작성방법.txt 참고
# =============================================================================
CATEGORIES = ["공지", "칼럼", "캠페인", "활동", "연구·정책"]

# CSS/JS 주소 뒤에 붙는 버전 태그(캐시 갱신용). 자산 파일 내용의 해시라서 CSS/JS가 실제로 바뀔 때만 값이 바뀌고,
# 글 하나만 고친 빌드에서는 다른 페이지가 그대로 유지됩니다 (커밋·배포 파일 수 최소화)
def _asset_version():
    import hashlib
    h = hashlib.sha1()
    for pattern in ("assets/css/*.css", "assets/js/*.js"):
        for p in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), pattern))):
            with open(p, "rb") as f:
                h.update(os.path.basename(p).encode() + b"\0" + f.read() + b"\0")
    return h.hexdigest()[:10]

BUILD_V = _asset_version()


def _inline(s):
    """굵게 **텍스트**, 링크 [텍스트](주소) 변환"""
    s = _html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    def _link(m):
        txt, url = m.group(1), m.group(2)
        ext = ' target="_blank" rel="noopener"' if url.startswith('http') else ''
        return f'<a href="{url}"{ext} style="color:var(--blue);font-weight:600">{txt}</a>'
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', _link, s)
    return s


def md_to_html(body):
    """간단 마크다운 → HTML (##소제목, ###소소제목, -목록, ![설명](이미지), 문단)"""
    out, buf = [], []
    inlist = False

    def flush_p():
        if buf:
            out.append('<p>' + _inline(' '.join(buf)) + '</p>')
            buf.clear()

    def close_list():
        nonlocal inlist
        if inlist:
            out.append('</ul>')
            inlist = False

    for raw in body.strip().splitlines():
        line = raw.strip()
        if not line:
            flush_p(); close_list(); continue
        m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', line)
        if m:
            flush_p(); close_list()
            alt, src = m.group(1), m.group(2)
            if not src.startswith('http'):
                src = 'assets/img/posts/' + src
            cap = f'<figcaption>{_inline(alt)}</figcaption>' if alt else ''
            out.append(f'<figure><img src="{src}" alt="{_html.escape(alt)}" loading="lazy">{cap}</figure>')
            continue
        if line.startswith('### '):
            flush_p(); close_list(); out.append('<h3>' + _inline(line[4:]) + '</h3>'); continue
        if line.startswith('## '):
            flush_p(); close_list(); out.append('<h2>' + _inline(line[3:]) + '</h2>'); continue
        if line.startswith('- '):
            flush_p()
            if not inlist:
                out.append('<ul>'); inlist = True
            out.append('<li>' + _inline(line[2:]) + '</li>'); continue
        close_list()
        buf.append(line)
    flush_p(); close_list()
    return '\n'.join(out)


RETIRED_POSTS = {}   # 옛 slug → 새 slug. md 머리에 '교체: <새 slug>'가 있는 게시글은 페이지를 만들지 않고 새 글로 이동하는 은퇴 스텁만 남깁니다 (2026.09.15)


def write_retired_stub(slug, target_slug, title):
    """교체된 게시글의 옛 주소 2개(post-<slug>.html, /news/<slug>/)에 새 글로 이동하는 noindex 스텁을 씁니다"""
    url = f"/news/{target_slug}/"; canonical = f"{SITE_URL}{url}"
    stub = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>{_html.escape(title)} | {SITE_NAME}</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace("{url}"+location.search+location.hash);</script>
</head><body><p>이 글은 <a href="{canonical}">{canonical}</a> 로 교체되었습니다.</p></body></html>
"""
    for target in (os.path.join(BASE, f"post-{slug}.html"), os.path.join(BASE, "news", slug, "index.html")):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with io.open(target, "w", encoding="utf-8") as f:
            f.write(stub)


def load_posts():
    """posts-src/*.md 읽어 게시글 목록(최신순) 반환 ('교체:' 머리글이 있는 md는 은퇴 스텁만 쓰고 목록에서 제외)"""
    posts = []
    for path in glob.glob(os.path.join(BASE, "posts-src", "*.md")):
        raw = io.open(path, encoding='utf-8').read()
        head, sep, body = raw.partition('\n---')
        if not sep:
            print("  ⚠ 건너뜀(--- 구분선 없음):", os.path.basename(path)); continue
        meta = {}
        for line in head.strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
        slug = os.path.splitext(os.path.basename(path))[0]
        if meta.get('교체'):
            RETIRED_POSTS[slug] = meta['교체']
            write_retired_stub(slug, meta['교체'], meta.get('제목', slug))
            continue
        date = meta.get('날짜', '2026.01.01')
        try:
            dt = datetime.datetime.strptime(date, "%Y.%m.%d")
        except ValueError:
            dt = datetime.datetime(2026, 1, 1)
        posts.append({
            "slug": slug,
            "file": f"post-{slug}.html",
            "title": meta.get('제목', slug),
            "date": date,
            "dt": dt,
            "category": meta.get('분류', '공지'),
            "keywords": [k.strip() for k in meta.get('키워드', '').split(',') if k.strip()],
            "image": meta.get('이미지', '').strip(),
            "summary": meta.get('요약', ''),
            "body": body.strip(),
        })
    posts.sort(key=lambda p: (p["dt"], p["slug"]), reverse=True)
    return posts


def board_card(p):
    """게시판 목록 카드 1개"""
    if p["image"]:
        thumb = f'<div class="board-thumb"><img src="assets/img/posts/{p["image"]}" alt="{_html.escape(p["title"])}" loading="lazy"></div>'
    else:
        thumb = f'''<div class="board-thumb board-thumb--ph">
            <span class="ph-mark">K<em>AI</em>EC</span><span class="ph-cat">{p["category"]}</span></div>'''
    badge = 'badge--teal' if p["category"] == '캠페인' else ('badge--gray' if p["category"] in ('활동', '연구·정책') else '')
    return f'''        <a class="board-card" href="{p["file"]}" data-cat="{p["category"]}">
          {thumb}
          <div class="board-body">
            <div class="board-meta"><span class="badge {badge}">{p["category"]}</span><span class="board-date">{p["date"]}</span></div>
            <div class="board-title">{p["title"]}</div>
            <p class="board-sum">{p["summary"]}</p>
            <span class="board-more">자세히 보기 →</span>
          </div>
        </a>'''

NAV = [
    ("about.html", "위원회 소개"),
    ("business.html", "주요사업"),
    ("members.html", "위원 명단"),
    ("lecture.html", "강의 신청"),
    ("copyclean.html", "카피클린"),
    ("news.html", "커뮤니티"),
    ("mou.html", "사회공헌"),
]

LOGO_SVG = """<svg class="brand-mark" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="kgBg" x1="4" y1="2" x2="46" y2="46" gradientUnits="userSpaceOnUse">
      <stop stop-color="#1E56D6"/><stop offset=".52" stop-color="#12336F"/><stop offset="1" stop-color="#0A1628"/>
    </linearGradient>
    <linearGradient id="kgShield" x1="14" y1="10" x2="36" y2="40" gradientUnits="userSpaceOnUse">
      <stop stop-color="#CFE0FF"/><stop offset="1" stop-color="#6FE3D8"/>
    </linearGradient>
    <linearGradient id="kgSheen" x1="0" y1="0" x2="20" y2="26" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="kgGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse"
      gradientTransform="translate(24 19.5) scale(7.5)">
      <stop stop-color="#6FE3D8" stop-opacity=".55"/><stop offset="1" stop-color="#6FE3D8" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="48" height="48" rx="12.5" fill="url(#kgBg)"/>
  <rect x="1" y="1" width="46" height="46" rx="11.5" stroke="#fff" stroke-opacity=".14"/>
  <path d="M0 12.5C0 5.6 5.6 0 12.5 0h23C42.4 0 48 5.6 48 12.5V17C40 8.8 26 4.6 0 15.5v-3Z" fill="url(#kgSheen)"/>
  <path d="M24 8.6 36.4 14v10.3c0 7-5 12-12.4 13.9C16.6 36.3 11.6 31.3 11.6 24.3V14L24 8.6Z"
        stroke="url(#kgShield)" stroke-width="2.1" stroke-linejoin="round"/>
  <circle cx="24" cy="19.5" r="7.5" fill="url(#kgGlow)"/>
  <circle cx="24" cy="19.5" r="2.7" fill="#6FE3D8"/>
  <circle cx="17.9" cy="28.6" r="2.2" fill="#F2F7FF"/>
  <circle cx="30.1" cy="28.6" r="2.2" fill="#F2F7FF"/>
  <path d="M22.6 21.6 18.9 26.7M25.4 21.6 29.1 26.7M20.1 28.6h7.8"
        stroke="#DCE9FF" stroke-width="1.6" stroke-linecap="round"/>
  <path d="M24 12.2v3.2M16 16l2.6 1.6M32 16l-2.6 1.6" stroke="#8FB7FF" stroke-width="1.3" stroke-linecap="round" opacity=".8"/>
</svg>"""

# 워드마크: 글꼴 외곽선을 벡터 패스로 굳힌 SVG (tools/make_wordmark.py로 생성, 2026.09.14).
# 웹폰트 로딩·OS 힌팅과 무관하게 어떤 화면에서도 선명하게 렌더링됩니다. 헤더가 원본(id 포함), 푸터는 <use>로 재사용.
# 색은 CSS 변수 --wm-ko / --wm-en (헤더 남색·회색, 푸터 흰색·연회색)로 지정합니다.
WORDMARK_SVG = io.open(os.path.join(BASE, "tools", "wordmark.svg"), encoding="utf-8").read().strip()
BADGE_SVG = io.open(os.path.join(BASE, "tools", "badge.svg"), encoding="utf-8").read().strip()   # 배지 글자 KAIEC (벡터)
_wm_vb = re.search(r'viewBox="([^"]+)"', WORDMARK_SVG).group(1)
WORDMARK_USE = (f'<svg class="brand-wm" viewBox="{_wm_vb}" aria-hidden="true" focusable="false">'
                f'<use href="#wm-ko"/><use href="#wm-en"/></svg>')


def brand(reuse=False):
    """헤더·푸터 공통 브랜드 블록. reuse=True(푸터)는 헤더 SVG의 패스를 <use>로 참조해 페이지 용량을 아낍니다."""
    wm = WORDMARK_USE if reuse else WORDMARK_SVG
    return f"""<a class="brand" href="index.html" aria-label="{SITE_NAME} 홈">
        <span class="brand-badge">{BADGE_SVG}</span>
        <span class="brand-text">{wm}<span class="sr-only">{SITE_NAME} (KAIEC) {SITE_EN}</span></span>
      </a>"""


def header():
    """공통 헤더. 2026.09.22: 메뉴의 'KAIEC 참여' 항목은 상단 바와 [위원 참여하기] 버튼(2026.09.25 개명, 이전 'KAIEC 참여하기')과 겹쳐 뺐고,
    메뉴 글자 사이 여백을 넓히고 메뉴와 버튼 사이에 세로 구분선(.nav-sep)을 두어 덜 촘촘하게 정리."""
    links = "\n          ".join(
        f'<a href="{h}">{t}</a>' for h, t in NAV
    )
    return f"""<header class="site-header">
    <div class="topbar">
      <div class="topbar-inner">
        <span class="topbar-left">KOREA AI ETHICS COMMITTEE</span>
        <span class="topbar-right">
          <a href="mailto:{EMAIL}">{EMAIL}</a><span class="tsep" aria-hidden="true"></span>
          <a href="join.html">위원 참여</a><span class="tsep" aria-hidden="true"></span>
          <a class="tb-exam" href="exam.html">평가응시</a>
        </span>
      </div>
    </div>
    <div class="header-inner">
      {brand()}
      <nav class="nav" id="nav">
          {links}
          <a class="nav-exam" href="exam.html"><i data-lucide="lock"></i>평가응시<span>수강생 로그인</span></a>
          <span class="nav-sep" aria-hidden="true"></span>
          <span class="header-cta"><a class="btn btn-primary btn-sm" href="experts.html">AI윤리전문가 보기</a><a class="btn btn-ghost btn-sm" href="join.html">위원 참여하기</a></span>
      </nav>
      <button class="nav-toggle" id="navToggle" aria-label="메뉴 열기" aria-expanded="false" aria-controls="nav">
        <i data-lucide="menu"></i>
      </button>
    </div>
  </header>"""


def footer():
    col1 = "\n            ".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[:4])
    col2 = "\n            ".join(f'<li><a href="{h}">{t}</a></li>' for h, t in NAV[4:])
    return f"""<footer class="site-footer">
    <div class="wrap">
      <div class="footer-top">
        <div class="footer-brand">
          {brand(True)}
          <p class="footer-desc">생성형 AI 시대의 책임 있는 AI 활용과 건전한 AI 윤리 문화 확산을 위해 교육·연구·캠페인·사회공헌 활동을 수행하는 AI 윤리 전문기관입니다.</p>
        </div>
        <div class="footer-col">
          <h4>위원회</h4>
          <ul>
            {col1}
          </ul>
        </div>
        <div class="footer-col">
          <h4>활동</h4>
          <ul>
            {col2}
            <li><a href="experts.html">AI윤리전문가 명단</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>문의</h4>
          <ul>
            <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
            <li><a href="join.html">위원 참여하기</a></li>
            <li><a href="mou.html">사회공헌</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-info">
        <span>기관명 한국AI윤리위원회</span><span class="fsep">|</span>
        <span>대표자 위원장 신동복</span><span class="fsep">|</span>
        <span>고유번호 272-32-01885</span><span class="fsep">|</span>
        <span>연구실 : 경기도 수원시 장안구 서부로 2066 성균관대학교 브릿지팩토리 (16419)</span><span class="fsep">|</span>
        <span>공식 문의 <a href="mailto:{EMAIL}" style="color:inherit">{EMAIL}</a></span>
      </div>
      <div class="footer-info footer-info--sub">
        <span>교육비 결제 · 환급은 교육 운영사 <a href="https://www.skkc.co.kr" target="_blank" rel="noopener" style="color:inherit">성균관컨설팅</a>이 수행하며, 통신판매업 신고 등 판매자 정보는 해당 사이트에서 확인하실 수 있습니다.</span><span class="fsep">|</span>
        <span>연구실 주소는 소재지 표기이며 해당 대학과의 제휴·후원·인증을 의미하지 않습니다.</span>
      </div>
      <div class="footer-legal">
        <a href="terms.html">서비스 이용안내</a>
        <a href="privacy.html">개인정보·운영정책</a>
      </div>
      <div class="footer-bottom">
        <span>© <span id="year">2026</span> {SITE_NAME} (Korea AI Ethics Committee). All rights reserved.</span>
        <span>문의 {EMAIL}</span>
      </div>
    </div>
  </footer>"""


def url_for(filename):
    """생성 파일명 → 사이트 내 깔끔한 주소 (.html 없는 SEO 친화 URL)
       index.html → /   |  about.html → /about/   |  post-<slug>.html → /news/<slug>/"""
    if filename == "index.html": return "/"
    if filename == "404.html":   return "/404.html"
    if filename.startswith("post-"): return "/news/" + filename[5:-5] + "/"
    return "/" + filename[:-5] + "/"


def out_path(filename):
    """실제로 저장할 경로 (디렉터리 + index.html 구조 → GitHub Pages가 /about/ 로 서빙)"""
    u = url_for(filename)
    return filename if u.endswith(".html") or u == "/" and filename == "index.html" else u.lstrip("/") + "index.html"


_LINK_RE = re.compile(r'(href|src)="([A-Za-z0-9_\-]+\.html)((?:[?#][^"]*)?)"')
def clean_links(html):
    """생성된 HTML 안의 상대 링크(x.html)와 자산 경로(assets/…)를 루트 기준 깔끔한 주소로 변환"""
    html = _LINK_RE.sub(lambda m: f'{m.group(1)}="{url_for(m.group(2))}{m.group(3)}"', html)
    html = re.sub(r'(["\'])assets/', r'\1/assets/', html)
    html = _bust_assets(html)
    return html


# 캐시 버전이 안 붙은 자산(주로 *-data.js)에 ?v= 를 자동으로 붙입니다.
# 이게 없으면 연혁·명단·제휴 기관 데이터를 고쳐도 방문자 브라우저가 옛 파일을 계속 씁니다(2026.09.18).
_BUST_RE = re.compile(r'(src|href)="(/assets/(?:js|css)/[A-Za-z0-9._-]+\.(?:js|css))"')


def _bust_assets(html):
    return _BUST_RE.sub(lambda m: f'{m.group(1)}="{m.group(2)}?v={BUILD_V}"', html)


def _strip_tags(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def _faq_ld(body):
    """본문의 <details class="acc"> FAQ를 FAQPage 구조화 데이터로 자동 변환 (검색 결과 FAQ 리치 스니펫)"""
    items = re.findall(r'<details class="acc">\s*<summary>(.*?)</summary>\s*<div class="acc-body">(.*?)</div>\s*</details>', body, re.S)
    if not items:
        return ""
    ents = ",\n    ".join(
        '{"@type": "Question", "name": %s, "acceptedAnswer": {"@type": "Answer", "text": %s}}'
        % (_json_str(_strip_tags(q)), _json_str(_strip_tags(a))) for q, a in items)
    return ('<script type="application/ld+json">\n{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [\n    '
            + ents + '\n  ]}\n</script>\n')


def _crumb_ld(filename, title, parent=None):
    """BreadcrumbList 구조화 데이터 (홈 › [상위] › 현재)"""
    items = [("홈", f"{SITE_URL}/")]
    if parent:
        items.append((parent[0], f"{SITE_URL}{url_for(parent[1])}"))
    items.append((title, f"{SITE_URL}{url_for(filename)}"))
    lis = ",\n    ".join('{"@type": "ListItem", "position": %d, "name": %s, "item": "%s"}' % (i + 1, _json_str(n), u)
                         for i, (n, u) in enumerate(items))
    return ('<script type="application/ld+json">\n{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [\n    '
            + lis + '\n  ]}\n</script>\n')


def page(filename, title, desc, body, extra_head="", extra_script="", keywords=None, og_image=None,
         og_type="website", published=None, crumb_parent=None, sticky=None):
    canonical = f"{SITE_URL}{url_for(filename)}"
    full_title = title if filename == "index.html" else f"{title} | {SITE_NAME}"
    # 설명·제목에 큰따옴표가 있으면 meta content="..." 속성이 끊겨 설명이 비어 보이므로 &quot; 로 바꿉니다
    desc = desc.replace('"', '&quot;')
    full_title = full_title.replace('"', '&quot;')
    kw = ", ".join(keywords) if keywords else "한국AI윤리위원회, 한국 AI 윤리위원회, AI윤리위원회, AI 윤리 위원회, KAIEC, AI윤리, 인공지능 윤리, AI윤리전문가, AI윤리전문가 양성과정, AI 윤리 교육, AI 윤리 이수증, 생성형 AI, 카피클린"
    ogimg = og_image or f"{SITE_URL}/assets/img/og-image.png"
    article_meta = (f'<meta property="article:published_time" content="{published}">\n'
                    f'<meta property="article:modified_time" content="{published}">\n') if (og_type == "article" and published) else ""
    auto_ld = ""
    if filename != "index.html" and filename != "404.html":
        auto_ld += _crumb_ld(filename, title, crumb_parent)
    auto_ld += _faq_ld(body)
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kw}">
<meta name="author" content="{SITE_NAME}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta name="naver-site-verification" content="ce63d05d0de8c8bd3ff3aef7851061be7e0c4f9c">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="ko_KR">
<meta property="og:image" content="{ogimg}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{full_title}">
{article_meta}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{ogimg}">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" as="style" crossorigin
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Caveat:wght@600&family=Noto+Serif+KR:wght@600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css?v={BUILD_V}">
<script>document.documentElement.className+=' js';</script>
{auto_ld}{extra_head}</head>
<body>
  {header()}
  <main>
{body}
  </main>
{sticky_cta(sticky) if sticky else ""}  {footer()}
  <script src="assets/js/main.js?v={BUILD_V}"></script>
{extra_script}</body>
</html>
"""
    html = clean_links(inline_icons(html))
    target = os.path.join(BASE, out_path(filename))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with io.open(target, "w", encoding="utf-8") as f:
        f.write(html)
    # 기존 .html 주소로 들어온 방문자·검색엔진을 새 주소로 안내 (noindex + canonical + 즉시 이동)
    if filename not in ("index.html", "404.html"):
        stub = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>{full_title}</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={url_for(filename)}">
<script>location.replace("{url_for(filename)}"+location.search+location.hash);</script>
</head><body><p>이 페이지는 <a href="{canonical}">{canonical}</a> 로 이동했습니다.</p></body></html>
"""
        with io.open(os.path.join(BASE, filename), "w", encoding="utf-8") as f:
            f.write(stub)
    print("  ✓", url_for(filename))



def resume_box(note_basic=True):
    """이력서 기재 예시 (2026.09.21 통합): 이수 직후 쓰는 두 줄과, 전문위원 등록 뒤에 더해지는 한 줄"""
    return f"""        <div class="resume-line reveal">
          <span class="resume-label">이력서 가이드</span>
          <div class="resume-rows">
            <div class="rrow">
              <span class="resume-tag">이수 직후</span>
              <div class="rlines">
                <p><b>국문 이력서</b><code>{RESUME_KO} ({RESUME_NO})</code></p>
                <p><b>영문 이력서</b><code>{PROG_EN} ({RESUME_NO})</code></p>
                <small>교육·연수 칸에 한 줄이면 됩니다. 이수번호는 이름과 함께 홈페이지에서 검색되므로, 칸이 좁으면 번호를 빼고 <strong>{PROG_EN}</strong>까지만 적어도 됩니다.
                  링크드인은 Name에 AI Ethics Professional, Issuing organization에 Korea AI Ethics Committee, Credential ID에 이수번호, URL에 kaiec.kr/experts/ 를 넣습니다.
                  자기소개서 문장 예시와 면접 답변 포인트는 이수자 전용 <strong>이력서·자기소개서 활용 가이드</strong>로 함께 드립니다.</small>
              </div>
            </div>
            <div class="rrow">
              <span class="resume-tag resume-tag--adv">전문위원 등록 후</span>
              <div class="rlines">
                <p><b>경력사항</b><code>한국AI윤리위원회(KAIEC) 전문위원</code></p>
                <small>이수 후 전문위원 등록을 신청해 등록되면 <strong>경력사항에 한 줄이 더 생깁니다.</strong>
                  홈페이지에 프로필이 공개되고 전문강사 · 자문 활동이 가능합니다.</small>
              </div>
            </div>
          </div>
        </div>"""


def hero_sub(title, desc, crumb):
    return f"""    <section class="page-hero">
      <div class="wrap page-hero-inner">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; {crumb}</p>
        <h1>{title}</h1>
        <p>{desc}</p>
      </div>
    </section>"""


# 메인 피처 카드 '카피클린 문서검사' 타일: 래스터 대신 벡터 게이지 (어떤 배율에서도 글씨가 깨지지 않음, 2026.09.15)
GAUGE_SVG = (
    '<svg class="gauge" viewBox="0 0 92 114" role="img" aria-label="카피클린 AI 문서 분석 결과: AI 유사도 53%">'
    '<defs><linearGradient id="ccArc" x1="1" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#FFC46B"/><stop offset=".55" stop-color="#F58C48"/><stop offset="1" stop-color="#E0553F"/>'
    '</linearGradient></defs>'
    '<circle cx="46" cy="46" r="26.5" fill="none" stroke="#fff" stroke-opacity=".17" stroke-width="4.6"/>'
    '<circle cx="46" cy="46" r="26.5" fill="none" stroke="url(#ccArc)" stroke-width="4.6" stroke-linecap="round"'
    ' stroke-dasharray="88.3 166.5" transform="rotate(-90 46 46)"/>'
    '<text x="46" y="48.6" text-anchor="middle" font-size="20.5" font-weight="800" letter-spacing="-1.1" fill="#fff">53%</text>'
    '<text x="46" y="59.4" text-anchor="middle" font-size="6.4" font-weight="700" letter-spacing=".02" fill="#8FD2C8">AI 유사도</text>'
    '<path d="M32 86h28" stroke="#fff" stroke-opacity=".16" stroke-width=".9"/>'
    '<text x="46" y="98.5" text-anchor="middle" font-size="6" font-weight="800" letter-spacing=".24" fill="#BFE8E1">COPYCLEAN</text>'
    '</svg>')


CERT_CTA = "AI윤리전문가 양성과정 신청하기"        # 사이트 공통 1순위 버튼 문구
CERT_HREF = "expert-apply.html"                   # 2026.09.21 통합: 과정 선택이 없어져 ?course= 없이 신청 페이지로


def cert_band_inner(sec_label="위원 참여하기", sec_href="join.html", title=None, text=None):
    """전 페이지 공통 하단 전환 배너의 안쪽(.cta-band): 1순위는 항상 양성과정 신청, 2순위만 페이지 성격에 맞게"""
    title = title or "AI 시대에 가장 먼저 필요한 전문가, 지금 준비하세요"
    # 2026.09.23 사용자 지시로 '1기 모집 중 · 접수 마감 · 1기 특별가 (정가)' 홍보 문구 삭제(절제된 기관 톤). 가격·마감은 /expert/ 와 신청 페이지에서만 안내
    text = text or (f"AI윤리전문가 양성과정은 {HOOK_ZERO}으로 진행됩니다. "
                    f"위원회 표준교재와 온라인 이수 평가로 한국AI윤리위원회 공식 이수증을 받고, 이수 즉시 홈페이지에 공식 등록되세요.")
    return f"""<div class="cta-band reveal">
          <div><h2>{title}</h2>
            <p>{text}</p></div>
          <div class="btns">
            <a class="btn btn-white" href="{CERT_HREF}">{CERT_CTA}</a>
            <a class="btn btn-light" href="{sec_href}">{sec_label}</a>
          </div>
        </div>"""


def cert_band(sec_label="위원 참여하기", sec_href="join.html", title=None, text=None):
    """공통 전환 배너 섹션 전체"""
    return f"""

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner(sec_label, sec_href, title, text)}
      </div>
    </section>"""


def sticky_cta(mode="all"):
    """화면 하단 고정 접수 바 (스크롤 후 표시, 푸터·배너가 보이면 숨김). mode: all | mobile"""
    cls = " sticky-cta--mobile" if mode == "mobile" else ""
    return f"""  <div class="sticky-cta{cls}" id="stickyCta" aria-hidden="true">
    <div class="sticky-cta-inner">
      <div class="sticky-cta-text">
        <strong>AI윤리전문가<em class="sticky-more"> 양성과정</em> 특별가 {won(PRICE)}</strong>
        <span>{HOOK_ZERO}<em class="sticky-more"> · {HOOK_START} · {HOOK_REG}</em></span>
      </div>
      <a class="btn btn-primary btn-sm" href="{CERT_HREF}">양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
    </div>
  </div>
"""


# =============================================================================
#  콘텐츠
# =============================================================================

BUSINESS = [
    ("shield-check", "책임 있는 생성형 AI 활용 확산",
     "생성형 AI를 활용하는 개인과 조직이 지켜야 할 기본 원칙을 정리하고 확산합니다. 학습·연구·업무 현장에서 AI를 '숨기는 도구'가 아니라 '밝히고 검증하는 도구'로 쓰는 문화를 만드는 것을 목표로 합니다.",
     ["AI 활용 원칙 및 자율 가이드라인 정리", "분야별 AI 활용 체크리스트 배포", "AI 윤리 인식 개선 활동"]),
    ("megaphone", "AI 윤리 캠페인 및 교육·콘텐츠",
     "온라인 캠페인, 카드뉴스, 영상, 강의 자료 등 누구나 쉽게 접근할 수 있는 형태로 AI 윤리 콘텐츠를 제작·배포합니다. 대학생·대학원생·연구자·직장인 등 실사용자 눈높이에 맞춘 실용적 내용을 지향합니다.",
     ["온·오프라인 AI 윤리 캠페인 기획", "교육 자료 및 강의 콘텐츠 제작", "SNS 기반 인식 개선 콘텐츠 운영"]),
    ("award", "AI윤리전문가 양성과정 운영",
     "AI 윤리 지식과 실무역량을 갖춘 전문 인력을 양성합니다. 「AI윤리전문가 양성과정」과 전문강사 양성을 운영하고, 이수자를 위원회 홈페이지에 공식 등록하며, 전문위원 등록으로 AI 윤리위원·전문위원 제도와 현장 활동까지 연결합니다.",
     ["AI윤리전문가 양성과정 운영", "전문강사 양성 및 출강 연계", "AI 윤리위원·전문위원 위촉 및 활동 지원"]),
    ("handshake", "대학·기업·기관과의 제휴·협력",
     "대학, 기업, 협회, 연구기관과 뜻을 모아 AI 윤리 캠페인과 교육, 연구를 함께합니다. 각 기관의 현장 상황에 맞는 AI 윤리 실천 방안을 대가 없이 함께 설계합니다.",
     ["공동 AI 윤리 캠페인", "공동 세미나·교육 개최", "기관 맞춤형 AI 윤리 자문"]),
    ("file-search", "AI 활용 문서의 책임 있는 사전점검",
     "논문·과제·보고서 등 AI를 활용해 작성한 문서를 제출 전에 스스로 점검하는 문화를 확산합니다. 제재가 아닌 <strong>자기 점검</strong>을 통해 불필요한 오해와 분쟁을 예방하는 것이 목적입니다.",
     ["사전점검 문화 확산 캠페인", "제휴 서비스 「카피클린」과의 공동 활동", "점검 가이드라인 안내"]),
    ("book-open", "AI 윤리 연구 및 정책·사회적 이슈 공유",
     "국내외 AI 윤리 기준, 관련 정책 동향, 사회적 쟁점을 정리해 공유합니다. 특정 입장을 대변하기보다 논의에 필요한 정보를 정리해 전달하는 데 초점을 둡니다.",
     ["국내외 AI 윤리 동향 정리", "이슈 브리프 및 리포트 발행", "연구·토론 모임 운영"]),
]

VALUES = [
    ("scale", "책임성", "AI가 만든 결과에 대한 책임은 사람에게 있습니다. 활용 과정과 결과를 설명할 수 있어야 합니다."),
    ("eye", "투명성", "AI를 사용했다면 숨기지 않고 밝힙니다. 어디에, 어떻게 썼는지 드러내는 것이 신뢰의 출발점입니다."),
    ("scale-3d", "공정성", "AI 활용이 특정 집단에 불리하게 작동하지 않도록 살피고, 편향을 인식하며 사용합니다."),
    ("heart-handshake", "포용성", "기술 접근성의 차이가 새로운 격차가 되지 않도록, 누구나 이해할 수 있는 언어로 알립니다."),
]

CHARTER = [
    "AI가 만든 결과물의 최종 책임은 이를 사용한 사람에게 있음을 인식한다.",
    "학습·연구·업무에 AI를 활용한 경우, 요구되는 범위에서 그 사실과 활용 정도를 밝힌다.",
    "AI가 생성한 내용을 그대로 신뢰하지 않고, 사실관계와 출처를 스스로 확인한다.",
    "타인의 저작물과 개인정보가 AI 입력·출력 과정에서 침해되지 않도록 주의한다.",
    "AI를 이용해 타인을 기만하거나 허위 정보를 유포하지 않는다.",
    "제출·공표를 앞둔 문서는 사전에 스스로 점검하여 불필요한 분쟁을 예방한다.",
    "AI 윤리에 대해 배운 것을 주변과 나누어 건전한 활용 문화를 함께 넓혀간다.",
]


# ---------------------------------------------------------------- index.html
def build_index(posts):
    biz_cards = "\n".join(f"""        <article class="card reveal">
          <div class="card-icon"><i data-lucide="{ic}"></i></div>
          <h3>{t}</h3>
          <p>{d.split('.')[0]}.</p>
        </article>""" for ic, t, d, _ in BUSINESS)

    val_cards = "\n".join(f"""        <article class="card reveal">
          <div class="card-icon card-icon--teal"><i data-lucide="{ic}"></i></div>
          <h3>{t}</h3>
          <p>{d}</p>
        </article>""" for ic, t, d in VALUES)

    body = f"""    <section class="hero">
      <div class="wrap hero-inner">
        <span class="hero-badge"><span class="dot"></span>KAIEC · Korea AI Ethics Committee</span>
        <h1>한국AI윤리위원회(KAIEC)<br><span class="accent">책임 있는 AI 활용을 위한 전문기관</span></h1>
        <p>AI 윤리 교육, 연구, 캠페인, AI윤리전문가 양성 및 국내외 협력 활동을 추진합니다.</p>

        <div class="ai-visual">
            <img src="assets/img/hero-ai.jpg" alt="Responsible AI, Better Tomorrow. 한국AI윤리위원회의 AI 윤리 핵심가치 (책임성 · 투명성 · 공정성 · 사람 중심)">
          </div>

          <div class="hero-bottom">
          <div class="hero-ctas">
            <a class="btn btn-primary" href="expert.html">AI윤리전문가 양성과정 <i data-lucide="arrow-right"></i></a>
            <a class="btn btn-light" href="join.html">위원 참여하기 <i data-lucide="arrow-right"></i></a>
            <a class="btn btn-light" href="lecture.html">전문강사 출강 신청 <i data-lucide="arrow-right"></i></a>
            <a class="btn btn-light" href="copyclean.html">카피클린 문서검사 <i data-lucide="arrow-right"></i></a>
          </div>

        </div>
      </div>
    </section>

    <section class="section section--tight" style="padding-top:34px">
      <div class="wrap">
        <div class="feature-cards">
          <a class="fcard reveal" href="expert.html">
            <div class="fc-visual fc-v1"><img src="assets/img/cards/card-cert.jpg" alt="AI윤리전문가 양성과정 이수증" loading="lazy"></div>
            <div class="fc-body">
              <h3>AI윤리전문가 양성과정</h3>
              <p>100% 온라인으로 완성하는 AI 전문 이력<br>공식 이수증 발급<br>AI윤리전문가 공식 등록</p>
              <span class="fc-more">자세히 보기 <i data-lucide="arrow-right"></i></span>
            </div>
          </a>
          <a class="fcard reveal" href="lecture.html">
            <div class="fc-visual fc-v2"><img src="assets/img/cards/card-lecture.jpg" alt="전문강사 출강 교육 현장" loading="lazy" style="object-position:74% 28%"></div>
            <div class="fc-body">
              <h3>전문강사 출강 안내</h3>
              <p>학교·기업·공공기관 맞춤형<br>AI 윤리 교육</p>
              <span class="fc-more">자세히 보기 <i data-lucide="arrow-right"></i></span>
            </div>
          </a>
          <a class="fcard reveal" href="{COPYCLEAN_URL}" target="_blank" rel="noopener">
            <div class="fc-visual fc-v3 fc-gauge">{GAUGE_SVG}</div>
            <div class="fc-body">
              <h3>카피클린 문서검사</h3>
              <p>AI 사용 여부 확인<br>제출 전 사전점검</p>
              <span class="fc-more">자세히 보기 <i data-lucide="arrow-right"></i></span>
            </div>
          </a>
          <a class="fcard reveal" href="mou.html">
            <div class="fc-visual fc-v4"><img src="assets/img/cards/card-partner.png" alt="성균관대학교 RISE사업단 로고" loading="lazy"></div>
            <div class="fc-body">
              <h3>기업·기관 협력</h3>
              <p>AI 교육·캠페인·AX 컨설팅<br>공동사업 협력 제안</p>
              <span class="fc-more">자세히 보기 <i data-lucide="arrow-right"></i></span>
            </div>
          </a>
        </div>
      </div>
    </section>

    <section class="section section--tight offer-sec">
      <div class="wrap">
        <div class="offer-grid">
          <div class="offer-why reveal">
            <span class="eyebrow">AI Ethics Expert Program</span>
            <h2 class="h-sec" style="text-align:left">한국AI윤리위원회<br>AI윤리전문가 양성과정</h2>
            <p class="h-sub" style="text-align:left;margin:0 0 22px">위원회 표준교재와 온라인 이수 평가로 <strong>위원회 공식 이수증과 공식 등록</strong>까지.
               2026년 AI기본법 시행으로 기업·기관·학교가 찾기 시작한 스펙을 지금 준비하세요.</p>
            <div class="why-stats">
              <div><strong>2026. 1</strong><span>AI기본법 시행</span></div>
              <div><strong>2026. 8</strong><span>EU AI Act 투명성 의무 발효</span></div>
              <div><strong>2024. 3</strong><span>한국AI윤리위원회 설립</span></div>
              <div><strong>6개 분과</strong><span>전문위원회 운영</span></div>
            </div>
          </div>
          <div class="offer-card reveal">
            <div class="offer-top">
              <span class="offer-quota">{HOOK_ZERO} · {HOOK_REG}</span>
            </div>
            <h3>AI윤리전문가 양성과정</h3>
            <p>위원회가 직접 집필한 학습자료 5종과 온라인 이수 평가로 한국AI윤리위원회 공식 이수증을 받고, 홈페이지에 공식 등록되는 하나의 과정입니다.</p>
            <div class="price-line price-line--light">
              <span class="price-list">정가 {won(LIST_PRICE)}</span>
              <span class="price-now">{won(PRICE)}</span>
              <span class="price-tag">특별가</span>
            </div>
            <ul class="offer-list">
              <li>전공·경력 제한 없이 누구나 수강, 전 과정 온라인</li>
              <li>공식 이수증 · 홈페이지 공식 등록 · 이력서·자기소개서 활용 가이드 모두 포함</li>
              <li>이수 기준 {EXAM[1]}점, 응시 기간 안 {RETAKE}</li>
              <li>이수 후 전문위원 등록 신청 자격 (전문강사 · 자문 활동)</li>
            </ul>
            <div class="offer-btns">
              <a class="btn btn-primary" href="{CERT_HREF}">양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
              <a class="btn btn-ghost" href="expert.html">과정 자세히 보기</a>
            </div>
          </div>
        </div>
        <div class="partner-strip reveal">
          <span class="partner-strip-label">함께하는 기관</span>
          <img src="assets/img/partner-rise.jpg" alt="성균관대학교 RISE사업단" class="partner-strip-logo">
          <span class="partner-strip-text">성균관컨설팅</span>
          <span class="partner-strip-text">카피클린 (CopyClean)</span>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <a class="quiz-teaser reveal" href="quiz.html">
          <div class="quiz-teaser-body">
            <span class="eyebrow">Self Check · 실무 진단</span>
            <h2>이 7가지, 당신이라면 어떻게 판단하시겠습니까?</h2>
            <p>AI 초안 보고서의 표기, 회의 녹취의 외부 AI 입력, AI가 준 통계의 인용.
               실제로 자주 틀리는 장면 7개입니다. 문항마다 근거 해설이 바로 나옵니다.</p>
          </div>
          <div class="quiz-teaser-side">
            <div class="quiz-teaser-score"><span>7문항</span><b>14점 만점</b></div>
            <span class="btn btn-primary">실무 진단 시작하기 <i data-lucide="arrow-right"></i></span>
          </div>
        </a>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:44px">
          <span class="eyebrow">Our Mission</span>
          <h2 class="h-sec">기술의 속도를 따라가는 윤리의 기준</h2>
          <p class="h-sub">생성형 AI는 이미 학습·연구·업무의 일상이 되었습니다. 그러나 '어디까지 써도 되는가'에 대한
             기준은 아직 정리되지 않았습니다. 위원회는 그 기준을 함께 만들고 알리는 일을 합니다.</p>
        </div>
        <div class="grid grid-4">
{val_cards}
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:44px">
          <span class="eyebrow">Main Business</span>
          <h2 class="h-sec">6대 주요사업</h2>
          <p class="h-sub">선언에 머무르지 않고 현장에서 실제로 작동하는 활동을 지향합니다.</p>
        </div>
        <div class="grid grid-3">
{biz_cards}
        </div>
        <div class="center" style="margin-top:38px">
          <a class="btn btn-ghost" href="business.html">주요사업 자세히 보기 <i data-lucide="arrow-right"></i></a>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="split">
          <div class="reveal">
            <span class="eyebrow">Partner Program</span>
            <h2 class="h-sec">AI 윤리위원</h2>
            <p class="lead" style="margin-bottom:20px">AI 윤리에 관심 있는 누구나 온라인·재택 방식으로 참여할 수 있는
               위원회의 대표 참여 제도입니다.</p>
            <ul style="display:grid;gap:12px;margin-bottom:26px">
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span>AI 윤리 문화 확산 캠페인 참여</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span>홈페이지 공식 위원 명단 등재 및 활동증명서 발급</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span>활동 실적에 따른 인센티브 지급</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span>전 과정 온라인·재택 진행</span></li>
            </ul>
            <a class="btn btn-primary" href="partner.html">위원 제도 알아보기 <i data-lucide="arrow-right"></i></a>
          </div>
          <div class="split-visual reveal">
            <span class="badge badge--teal" style="align-self:flex-start">ONLINE · 재택</span>
            <h3 style="font-size:26px;letter-spacing:-.035em">함께 알리는 사람이<br>문화를 만듭니다</h3>
            <p style="color:#B8CBE8;font-size:15px;line-height:1.8">
              거창한 자격이나 경력이 필요하지 않습니다. AI를 활용하는 분이라면 누구나
              AI 윤리를 알리는 주체가 될 수 있습니다.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="split">
          <div class="split-visual reveal" style="background:linear-gradient(150deg,#0A1628,#00857A)">
            <span class="badge" style="align-self:flex-start;background:rgba(255,255,255,.16);color:#fff">제휴 서비스</span>
            <h3 style="font-size:26px;letter-spacing:-.035em">카피클린<br><span style="font-size:16px;font-weight:600;opacity:.8">CopyClean</span></h3>
            <p style="color:#CDE9E5;font-size:15px;line-height:1.8">
              논문·과제·보고서·자기소개서 등 다양한 문서를 대상으로
              AI 활용 여부를 사전에 확인할 수 있도록 지원하는 AI 문서 분석 서비스입니다.</p>
          </div>
          <div class="reveal">
            <span class="eyebrow">Affiliated Service</span>
            <h2 class="h-sec">제휴 서비스 「카피클린」</h2>
            <p class="lead" style="margin-bottom:18px">
              위원회는 카피클린과 함께 <strong>AI 활용 문서의 사전점검</strong>과
              <strong>책임 있는 AI 활용 문화 확산</strong>을 위한 캠페인·제휴 활동을 진행합니다.</p>
            <div class="notice notice--teal" style="margin-bottom:24px">
              위원회가 <strong>윤리 기준과 캠페인</strong>을, 카피클린이 <strong>AI 문서 분석 기술</strong>을 맡아
              "제출 전에 스스로 확인하는 문화"를 함께 만들어갑니다.
            </div>
            <div style="display:flex;gap:11px;flex-wrap:wrap">
              <a class="btn btn-teal" href="{COPYCLEAN_URL}" target="_blank" rel="noopener">카피클린 바로가기 <i data-lucide="external-link"></i></a>
              <a class="btn btn-ghost" href="copyclean.html">제휴 내용 자세히 보기 <i data-lucide="arrow-right"></i></a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:32px;flex-wrap:wrap">
          <div>
            <span class="eyebrow">News &amp; Campaign</span>
            <h2 class="h-sec" style="margin-bottom:0">최근 소식</h2>
          </div>
          <a class="btn btn-ghost btn-sm" href="news.html">전체 보기 <i data-lucide="arrow-right"></i></a>
        </div>
        <div class="board-grid">
{chr(10).join(board_card(p) for p in posts[:3])}
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("위원 참여하기", "join.html")}
      </div>
    </section>"""

    org_ld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "WebSite",
      "@id": "{SITE_URL}/#website",
      "url": "{SITE_URL}/",
      "name": "한국AI윤리위원회",
      "alternateName": "KAIEC",
      "inLanguage": "ko-KR",
      "publisher": {{ "@id": "{SITE_URL}/#organization" }}
    }},
    {{
      "@type": "WebPage",
      "@id": "{SITE_URL}/#webpage",
      "url": "{SITE_URL}/",
      "name": "한국AI윤리위원회(KAIEC) | 공식 홈페이지",
      "isPartOf": {{ "@id": "{SITE_URL}/#website" }},
      "about": {{ "@id": "{SITE_URL}/#organization" }},
      "primaryImageOfPage": "{SITE_URL}/assets/img/og-image.png",
      "inLanguage": "ko-KR"
    }},
    {{
      "@type": "Organization",
      "@id": "{SITE_URL}/#organization",
      "name": "한국AI윤리위원회",
      "legalName": "한국AI윤리위원회",
      "alternateName": ["KAIEC", "한국 AI 윤리위원회", "AI윤리위원회", "Korea AI Ethics Committee"],
      "url": "{SITE_URL}/",
      "logo": {{
        "@type": "ImageObject",
        "url": "{SITE_URL}/assets/img/logo-512.png",
        "width": 512,
        "height": 512
      }},
      "image": "{SITE_URL}/assets/img/og-image.png",
      "description": "한국AI윤리위원회(KAIEC)는 책임 있는 AI 활용 문화를 넓히기 위해 AI 윤리 교육과 연구, 캠페인, AI윤리전문가 양성과 기관 협력을 추진하는 AI 윤리 전문 기관입니다.",
      "slogan": "책임 있는 AI 활용을 위한 전문기관",
      "foundingDate": "2024-03",
      "knowsAbout": ["AI 윤리", "인공지능 윤리", "AI기본법", "EU AI Act", "AI 거버넌스", "생성형 AI 활용 윤리", "AI 리터러시", "AI 윤리 교육"],
      "areaServed": {{ "@type": "Country", "name": "대한민국" }},
      "email": "{EMAIL}",
      "address": {{
        "@type": "PostalAddress",
        "streetAddress": "서부로 2066 성균관대학교 브릿지팩토리",
        "addressLocality": "수원시 장안구",
        "addressRegion": "경기도",
        "postalCode": "16419",
        "addressCountry": "KR"
      }},
      "contactPoint": {{
        "@type": "ContactPoint",
        "email": "{EMAIL}",
        "contactType": "customer service",
        "availableLanguage": "Korean"
      }}
    }}
  ]
}}
</script>
"""
    page("index.html",
         "한국AI윤리위원회(KAIEC) | 공식 홈페이지",
         "한국AI윤리위원회(KAIEC) 공식 홈페이지입니다. 책임 있는 AI 활용을 위한 AI 윤리 교육·연구·캠페인·전문가 양성 및 기관 협력을 추진합니다.",
         body, sticky="mobile", extra_head='<link rel="preload" as="image" href="assets/img/hero-ai.jpg" fetchpriority="high">\n' + org_ld)


# ---------------------------------------------------------------- about.html
def _chair_name():
    """members-data.js 의 위원장 항목에서 성함을 읽음 (인사말 본문·서명에 빌드 시 직접 넣어 검색엔진에도 보이게)."""
    js = io.open(os.path.join(BASE, "assets", "js", "members-data.js"), encoding="utf-8").read()
    m = re.search(r"group:\s*'위원장'.*?name:\s*'([^']+)'", js)
    return m.group(1) if m else "위원장"


def org_chart():
    """조직도 (2026.09.23 '조직·위원' 페이지에서 '위원회 소개' 페이지로 이동). 직책은 위원회 체계에 맞춤:
    위원장 → (감사 · 고문·자문위원단 독립) → 부위원장 · 사무총장 → 사무국 3팀 / 전문위원회 6개 분과 / AI 윤리 캠페인위원 → 지역 운영위원회 · 캠퍼스 위원회"""
    return """        <div class="org-chart">
          <!-- 위원장 -->
          <div class="oc-node oc-lv1">
            <div class="oc-tag">CHAIRPERSON</div>
            <div class="oc-title">위원장</div>
            <div class="oc-desc">위원회 대표 · 전체 활동 총괄</div>
          </div>

          <!-- 감사 / 고문·자문위원단 (독립 기구) -->
          <div class="oc-siderow">
            <div class="oc-node oc-side">
              <div class="oc-tag" style="color:var(--gray-500)">AUDITOR</div>
              <div class="oc-title" style="font-size:15.5px">감사</div>
              <div class="oc-desc">운영 · 회계 독립 감사</div>
            </div>
            <div class="oc-dash"></div>
            <div class="oc-spine"></div>
            <div class="oc-dash"></div>
            <div class="oc-node oc-side">
              <div class="oc-tag" style="color:var(--gray-500)">ADVISORY BOARD</div>
              <div class="oc-title" style="font-size:15.5px">고문 · 자문위원단</div>
              <div class="oc-desc">학술고문 · 법률고문 · 분야별 자문</div>
            </div>
          </div>

          <!-- 부위원장 · 사무총장 -->
          <div class="oc-node oc-lv2">
            <div class="oc-tag">VICE CHAIRPERSON · SECRETARY GENERAL</div>
            <div class="oc-title">부위원장 · 사무총장</div>
            <div class="oc-desc">위원장 보좌 · 위원회 운영 총괄</div>
          </div>

          <div class="oc-vline"></div>
          <div class="oc-hline"></div>

          <!-- 3대 축: 사무국 / 전문위원회 / AI 윤리 캠페인위원 -->
          <div class="oc-branches">
            <div class="oc-branch">
              <div class="oc-stub"></div>
              <div class="oc-node oc-pillar">
                <div class="oc-tag">SECRETARIAT</div>
                <div class="oc-title">사무국</div>
                <div class="oc-desc">행정 · 운영 실무 총괄</div>
              </div>
              <div class="oc-childs">
                <div class="oc-child">기획운영팀 <small>사업 기획 · 총무 · 회의 운영</small></div>
                <div class="oc-child">대외협력팀 <small>공동 캠페인 · 기관 협력 · 국제 교류</small></div>
                <div class="oc-child">콘텐츠·홍보팀 <small>캠페인 · 콘텐츠 · 채널 운영</small></div>
              </div>
            </div>
            <div class="oc-branch">
              <div class="oc-stub"></div>
              <div class="oc-node oc-pillar oc-pillar--teal">
                <div class="oc-tag" style="color:#00857A">EXPERT COMMITTEES</div>
                <div class="oc-title">전문위원회</div>
                <div class="oc-desc">6개 분과 · 분야별 자문과 기준 검토</div>
              </div>
              <div class="oc-childs">
                <div class="oc-child">AI·기술 분과 <small>생성형 AI 기술 동향 · 판별 기술</small></div>
                <div class="oc-child">법·정책 분과 <small>AI 관련 법제 · 정책 동향</small></div>
                <div class="oc-child">교육·리터러시 분과 <small>AI 윤리 교육 · 교안 개발 · 전문가 양성</small></div>
                <div class="oc-child">연구·출판윤리 분과 <small>논문·연구물 AI 활용 기준</small></div>
                <div class="oc-child">데이터·개인정보 분과 <small>데이터 윤리 · 프라이버시</small></div>
                <div class="oc-child">미디어·콘텐츠 분과 <small>허위정보 · 콘텐츠 윤리</small></div>
              </div>
            </div>
            <div class="oc-branch">
              <div class="oc-stub"></div>
              <div class="oc-node oc-pillar oc-pillar--teal" style="border-top-color:var(--teal)">
                <div class="oc-tag" style="color:#00857A">CAMPAIGN COMMITTEE</div>
                <div class="oc-title">AI 윤리 캠페인위원</div>
                <div class="oc-desc">온라인 전국 활동 · 상시 모집</div>
              </div>
              <div class="oc-childs">
                <div class="oc-child">캠페인 참여 <small>온라인 캠페인 · 확산 활동</small></div>
                <div class="oc-child">콘텐츠 활동 <small>카드뉴스 · 영상 · 홍보</small></div>
                <div class="oc-child">현장 소통 <small>대학 · 커뮤니티 알림</small></div>
              </div>
            </div>
          </div>

          <div class="oc-vline"></div>

          <!-- 지역 · 캠퍼스 조직 -->
          <div class="oc-band">
            <span class="badge">전국 조직</span>
            <div>
              <div class="oc-title">지역 운영위원회 · 캠퍼스 위원회</div>
              <div class="oc-desc">권역별 지역 운영위원과 대학별 캠퍼스 위원장을 중심으로 한 현장 확산 조직</div>
            </div>
          </div>

        </div>"""


def build_about():
    """위원회 소개 (2026.09.23 재구성): 위원장 인사말(새 문안) → 미션 · 비전 → 4대 핵심가치 → 조직도 → AI 윤리 실천 헌장 → 주요 연혁 · 위원회 개요.
    설립 취지 절은 인사말이 그 내용을 담고 있어 삭제. 인사말 문안은 사용자가 확정한 원문 그대로(굵은 글씨 위치 포함)."""
    chair = _chair_name()
    val_rows = "\n".join(f"""        <article class="card reveal">
          <div class="card-icon"><i data-lucide="{ic}"></i></div>
          <h3>{t}</h3>
          <p>{d}</p>
        </article>""" for ic, t, d in VALUES)

    charter = "\n".join(f"""          <li style="display:flex;gap:16px;padding:18px 0;border-bottom:1px solid var(--gray-200)">
            <span style="flex-shrink:0;width:30px;height:30px;border-radius:9px;background:var(--blue-050);color:var(--blue);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px">{i+1}</span>
            <span style="font-size:16px;line-height:1.75;color:var(--gray-700);padding-top:2px">{c}</span>
          </li>""" for i, c in enumerate(CHARTER))

    body = hero_sub("위원회 소개",
                    "AI를 책임 있게 활용하는 사회를 만드는 AI 윤리 전문 기구, 한국AI윤리위원회입니다.",
                    "위원회 소개") + f"""

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:36px">
          <span class="eyebrow">Message</span>
          <h2 class="h-sec serif">위원장 인사말</h2>
        </div>
        <div class="greeting greeting--wide serif">
          <p class="greeting-open">안녕하십니까.<br>한국AI윤리위원회 위원장 {chair}입니다.</p>
          <div class="greeting-flow">
            <aside class="greeting-side">
              <div class="greeting-photo">
                <img src="assets/img/chairman.jpg" alt="한국AI윤리위원회 위원장 {chair}">
              </div>
              <div class="greeting-cap">
                <span class="gc-role">한국AI윤리위원회 위원장</span>
                <span class="gc-name">{chair}</span>
              </div>
            </aside>
            <p>한국AI윤리위원회 홈페이지를 찾아주신 여러분께 진심으로 감사드립니다.</p>
            <p>생성형 인공지능을 비롯한 AI 기술은 빠른 속도로 발전하며 우리의 학습과 연구, 산업과 업무 전반에 새로운 변화를
            만들어가고 있습니다. 이제 AI를 활용하는 능력은 개인과 조직의 중요한 역량으로 자리 잡고 있으며, 앞으로 그 활용 범위는
            더욱 넓어질 것입니다.</p>
            <p>그러나 기술의 발전과 활용이 빠르게 확산되는 만큼, <strong>AI를 어디까지, 그리고 어떻게 활용하는 것이 바람직한가에
            대한 사회적 기준과 책임 있는 활용 문화</strong> 역시 함께 마련되어야 합니다.</p>
            <p>AI를 활용했다는 이유만으로 그 가치를 부정해서도 안 되며, 반대로 AI가 만들어낸 결과를 아무런 검토와 책임 없이
            받아들여서도 안 됩니다. 중요한 것은 기술의 사용 여부가 아니라, <strong>어떤 원칙과 책임 아래 AI를 활용하느냐</strong>에
            있다고 생각합니다.</p>
            <p>한국AI윤리위원회는 이러한 시대적 변화 속에서 <strong>AI의 책임 있는 활용 기준을 연구하고, 올바른 AI 활용 문화를
            사회 전반에 확산하기 위해 설립된 AI 윤리 전문 기구</strong>입니다.</p>
            <p>위원회는 AI 윤리가 선언적인 원칙에 머무르지 않고 교육·연구·산업 현장에서 실제로 실천될 수 있도록 다양한 활동을
            추진하고 있습니다. AI 윤리 및 책임 있는 활용에 관한 <strong>교육과 전문인력 양성</strong>, 관련 <strong>연구 및 기준
            마련</strong>, 올바른 AI 활용을 위한 <strong>캠페인과 인식 확산</strong>, 대학·기업·기관과의 <strong>협력 및 사회공헌
            활동</strong> 등을 통해 건강한 AI 생태계를 만들어가고자 합니다.</p>
            <p>특히 AI를 활용하는 과정에서 스스로 한 번 더 점검하고, 필요한 경우 그 활용 사실을 투명하게 밝히며, 최종 결과에
            대해서는 사람이 책임지는 문화를 중요하게 생각합니다. 이러한 작은 실천들이 쌓일 때 AI는 불신의 대상이 아니라 우리 사회가
            신뢰하고 활용할 수 있는 기술로 자리 잡을 수 있을 것입니다.</p>
            <p>앞으로도 한국AI윤리위원회는 전문가와 현장의 다양한 목소리에 귀 기울이며, 전문위원과 지역·캠퍼스 조직, 그리고 전국의
            AI 윤리위원들과 함께 <strong>기술의 발전과 사회적 책임이 조화를 이루는 AI 문화</strong>를 만들어가겠습니다.</p>
            <blockquote class="greeting-quote">
              AI 기술을 잘 활용하는 사회를 넘어,<br>
              <strong>AI를 책임 있게 활용하는 사회</strong>를 만드는 것.<br>
              그 길에 한국AI윤리위원회가 함께하겠습니다.
            </blockquote>
            <p>여러분의 지속적인 관심과 참여를 부탁드립니다.</p>
            <p>감사합니다.</p>
            <div class="greeting-sign">
              <span class="gs-org">한국AI윤리위원회</span>
              <span class="gs-name"><small>위원장</small>{chair}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--ink">
      <div class="wrap">
        <div class="grid grid-2" style="gap:48px">
          <div>
            <span class="eyebrow">Mission</span>
            <h2 class="h-sec" style="color:#fff">미션</h2>
            <p class="h-sub" style="font-size:17px">
              생성형 AI를 활용하는 모든 사람이 <strong style="color:#6FE3D8">책임 있게, 투명하게, 공정하게</strong>
              AI를 사용할 수 있도록 실천 가능한 기준을 만들고 확산한다.
            </p>
          </div>
          <div>
            <span class="eyebrow">Vision</span>
            <h2 class="h-sec" style="color:#fff">비전</h2>
            <p class="h-sub" style="font-size:17px">
              AI 활용 사실을 <strong style="color:#6FE3D8">숨기지 않아도 되는 사회</strong>,
              사전 점검이 제재가 아니라 상식이 되는 문화를 만든다.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Core Values</span>
          <h2 class="h-sec">4대 핵심가치</h2>
        </div>
        <div class="grid grid-4">
{val_rows}
        </div>
      </div>
    </section>

    <section class="section section--gray" id="org">
      <div class="wrap">
        <div class="center" style="margin-bottom:46px">
          <span class="eyebrow">Organization</span>
          <h2 class="h-sec">조직도</h2>
          <p class="h-sub">위원회는 위원장을 중심으로 사무국과 6개 전문분과, AI 윤리 캠페인위원을 두고,
             전국 단위의 지역 운영위원회·캠퍼스 위원회로 확장되는 구조입니다. 직책별 구성원은 <a href="members.html" style="color:var(--blue);font-weight:600">위원 명단 페이지</a>에서 확인하실 수 있습니다.</p>
        </div>
{org_chart()}
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">Charter</span>
          <h2 class="h-sec">AI 윤리 실천 헌장</h2>
          <p class="h-sub">위원회와 위원이 함께 공유하는 7개 실천 조항입니다.</p>
        </div>
        <div class="charter-box">
          <ul>
{charter}
          </ul>
        </div>
        <div class="notice notice--teal" style="margin-top:26px">
          본 헌장은 <strong>자율적 실천 규범</strong>이며 법적 구속력을 가지지 않습니다.
          위원회의 모든 활동과 위원의 활동은 이 헌장을 기준으로 삼습니다.
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="grid grid-2" style="gap:52px;align-items:start">
          <div>
            <span class="eyebrow">History</span>
            <h2 class="h-sec">주요 연혁</h2>
            <p class="h-sub" style="margin-bottom:30px">위원회의 활동 기록입니다.</p>
            <div class="timeline" id="historyList"></div>
          </div>
          <div>
            <span class="eyebrow">Overview</span>
            <h2 class="h-sec">위원회 개요</h2>
            <p class="h-sub" style="margin-bottom:26px">기본 정보와 운영 원칙입니다.</p>
            <div class="table-wrap">
              <table class="tbl" style="min-width:auto">
                <tbody>
                  <tr><th style="width:34%">명칭</th><td>한국AI윤리위원회<br><span style="color:var(--gray-500);font-size:13.5px">{SITE_EN_FORMAL} (KAIEC)</span></td></tr>
                  <tr><th>설립</th><td>2024년 3월</td></tr>
                  <tr><th>성격</th><td>AI 윤리 전문기관</td></tr>
                  <tr><th>목적</th><td>책임 있는 생성형 AI 활용 및 AI 윤리 문화 확산</td></tr>
                  <tr><th>주요 활동</th><td>교육 · 연구 · 캠페인 · 사회공헌 · AI 윤리위원 운영</td></tr>
                  <tr><th>조직</th><td>사무국 3팀 · 전문위원회 6개 분과 · AI 윤리 캠페인위원 · 지역 운영위원회 · 캠퍼스 위원회</td></tr>
                  <tr><th>임원 · 위원 임기</th><td>2년 (연임 가능)</td></tr>
                  <tr><th>회의 · 의결</th><td>정기회의 분기 1회, 임시회의 수시 (온라인 병행)<br><span style="color:var(--gray-500);font-size:13.5px">재적위원 과반수 출석과 출석위원 과반수 찬성</span></td></tr>
                  <tr><th>운영 방식</th><td>온라인 기반 (위원 활동 재택 가능)</td></tr>
                  <tr><th>대표 문의</th><td><a href="mailto:{EMAIL}" style="color:var(--blue);font-weight:600">{EMAIL}</a></td></tr>
                </tbody>
              </table>
            </div>
            <div class="notice notice--teal" style="margin-top:22px">
              위원회 활동에 관한 문의는 언제든 환영합니다. 대표 메일로 보내주시면 담당자가 신속히 회신드립니다.
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("위원 참여하기", "join.html")}
      </div>
    </section>"""

    script = """  <script src="assets/js/history-data.js"></script>
  <script>
  (function(){
    var box=document.getElementById('historyList');
    if(box&&window.KAIEC_HISTORY){
      box.innerHTML=window.KAIEC_HISTORY.map(function(h){
        return '<div class="tl-item"><div class="tl-date">'+h.date+'</div>'
          +'<div class="tl-title">'+h.title+'</div>'
          +(h.desc?'<div class="tl-desc">'+h.desc+'</div>':'')+'</div>';
      }).join('');
    }
  })();
  </script>
"""
    page("about.html", "위원회 소개",
         f"한국AI윤리위원회 위원장 {chair} 인사말, 미션과 비전, 4대 핵심가치, 조직도, AI 윤리 실천 헌장 7개 조항과 위원회 개요를 안내합니다.",
         body, extra_script=script)


# ------------------------------------------------------------- business.html
def build_business():
    blocks = []
    for i, (ic, t, d, items) in enumerate(BUSINESS):
        lis = "\n".join(f"""              <li style="display:flex;gap:10px;align-items:flex-start;padding:7px 0">
                <i data-lucide="chevron-right" style="width:17px;height:17px;color:var(--blue);flex-shrink:0;margin-top:5px"></i>
                <span style="font-size:15px;color:var(--gray-700)">{x}</span></li>""" for x in items)
        rev = "direction:rtl" if i % 2 else ""
        inner = "direction:ltr" if i % 2 else ""
        blocks.append(f"""      <div class="split reveal" style="margin-bottom:64px;{rev}">
          <div style="{inner}">
            <span class="card-num">사업 {i+1:02d}</span>
            <h2 style="font-size:26px;letter-spacing:-.035em;margin-bottom:14px">{t}</h2>
            <p style="font-size:16px;color:var(--gray-600);line-height:1.8;margin-bottom:18px">{d}</p>
            <ul>
{lis}
            </ul>
          </div>
          <div class="split-visual" style="{inner};min-height:250px{';background:linear-gradient(150deg,#0A1628,#00857A)' if i%3==2 else ''}">
            <div class="card-icon" style="background:rgba(255,255,255,.14);color:#fff;width:58px;height:58px">
              <i data-lucide="{ic}" style="width:27px;height:27px"></i>
            </div>
            <h3 style="font-size:22px;letter-spacing:-.035em">{t}</h3>
          </div>
        </div>""")

    body = hero_sub("주요사업",
                    "선언에 머무르지 않고 현장에서 작동하는 6개 영역의 활동을 추진합니다.",
                    "주요사업") + f"""

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:52px">
          <span class="eyebrow">Main Business</span>
          <h2 class="h-sec">6대 주요사업</h2>
          <p class="h-sub">교육 · 연구 · 캠페인 · 사회공헌을 축으로, 현장에서 실제로 활용할 수 있는 결과물을 만드는 데 집중합니다.</p>
        </div>
{"".join(blocks)}
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">How We Work</span>
          <h2 class="h-sec">추진 방식</h2>
        </div>
        <div class="grid grid-4">
          <article class="card reveal"><span class="card-num">STEP 01</span><h3>현장 확인</h3>
            <p>대학·기업·연구 현장에서 실제로 어떤 어려움이 있는지 확인하는 것에서 출발합니다.</p></article>
          <article class="card reveal"><span class="card-num">STEP 02</span><h3>기준 정리</h3>
            <p>국내외 AI 윤리 기준과 정책 동향을 참고해 실천 가능한 형태로 정리합니다.</p></article>
          <article class="card reveal"><span class="card-num">STEP 03</span><h3>확산·교육</h3>
            <p>캠페인·콘텐츠·강의 등 접근하기 쉬운 형태로 만들어 널리 알립니다.</p></article>
          <article class="card reveal"><span class="card-num">STEP 04</span><h3>협력 확대</h3>
            <p>대학·기업·협회와의 MOU 및 파트너 활동으로 실천 범위를 넓힙니다.</p></article>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("협력·교육 문의하기", "mou.html#inquiry")}
      </div>
    </section>"""

    page("business.html", "주요사업",
         "AI 윤리 교육·캠페인, AI윤리전문가 양성과정, 대학·기업 협력, AI 활용 문서 사전점검, AI 윤리 연구까지 한국AI윤리위원회의 6대 주요사업을 소개합니다.",
         body)


# -------------------------------------------------------------- members.html
def build_members():
    """위원 명단 (2026.09.23: 옛 '조직 · 위원' 페이지. 조직도 · 6개 전문분과 · 운영 개요는 '위원회 소개'(about) 로 옮기고
    이 페이지는 위원 명단과 공식 파트너만 둠. 명단 데이터는 assets/js/members-data.js)"""
    body = hero_sub("위원 명단",
                    "위원장과 임원진, 고문·자문위원, 사무국, 전문위원, 지역·캠퍼스 조직, AI 윤리 캠페인위원, 그리고 공식 등록된 AI윤리전문가까지 한국AI윤리위원회와 함께하는 분들입니다.",
                    "위원 명단") + f"""

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Members</span>
          <h2 class="h-sec">위원회 구성</h2>
          <p class="h-sub">직책과 전문분야를 기준으로 안내합니다. 조직 구성은 <a href="about.html#org" style="color:var(--blue);font-weight:600">조직도</a>를 참고해 주세요.</p>
        </div>
        <div id="memberSections"></div>

      </div>
    </section>

    <section class="section section--gray" id="experts">
      <div class="wrap">
        <div class="sec-head sec-head--split">
          <div>
            <span class="eyebrow">AI Ethics Professionals</span>
            <h2 class="h-sec">AI윤리전문가</h2>
            <p class="h-sub" style="margin:0">AI윤리전문가 양성과정 이수 평가를 통과해 한국AI윤리위원회에 공식 등록된 분들입니다.
               성명 또는 이수번호로 등록 사실을 확인하실 수 있습니다. <span id="mExpertCount"></span></p>
          </div>
          <form class="mini-search" role="search" onsubmit="return false">
            <i data-lucide="search"></i>
            <input type="search" id="mExpertQ" placeholder="성명 · 이수번호 검색" aria-label="AI윤리전문가 검색" autocomplete="off">
            <span class="mini-search-n" id="mExpertN"></span>
          </form>
        </div>
        <div class="member-grid" id="mExpertGrid" hidden></div>
        <div class="reg-empty" id="mExpertEmpty" hidden>
          <i data-lucide="award"></i>
          <div>
            <strong>AI윤리전문가 등록 명단은 이수 확정 순서대로 게시됩니다.</strong>
            <p>AI윤리전문가 양성과정 이수 평가를 통과하면 이수번호와 함께 이 명단에 공식 등록되며, 검색창에서 성명 또는 이수번호로 등록 사실을 확인할 수 있습니다.</p>
            <a href="expert.html">AI윤리전문가 양성과정 안내 →</a>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:36px">
          <span class="eyebrow">Official Partners</span>
          <h2 class="h-sec">공식 파트너</h2>
          <p class="h-sub">한국AI윤리위원회와 함께하는 공식 파트너입니다.</p>
        </div>
        <div class="logo-grid" id="officialPartners" style="max-width:760px;margin:0 auto"></div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("위원으로 참여하기", "join.html#apply")}
      </div>
    </section>"""

    script = """  <script src="assets/js/members-data.js"></script>
  <script src="assets/js/experts-data.js"></script>
  <script>
  /* AI윤리전문가 명단 (experts-data.js KAIEC_EXPERTS, /experts/ 와 같은 데이터) + 우측 작은 검색 */
  (function(){
    var list=window.KAIEC_EXPERTS||[];
    var grid=document.getElementById('mExpertGrid'),empty=document.getElementById('mExpertEmpty'),cnt=document.getElementById('mExpertCount');
    var q=document.getElementById('mExpertQ'),nEl=document.getElementById('mExpertN');
    if(!grid)return;
    function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
    if(!list.length){
      empty.hidden=false;
      if(q)q.addEventListener('input',function(){nEl.textContent=q.value.trim()?'등록자 없음':'';});
      return;
    }
    cnt.textContent='(등록 '+list.length+'명)';
    function card(m){
      var av=m.photo?'<div class="member-avatar member-avatar--photo"><img src="assets/img/experts/'+esc(m.photo)+'" alt="'+esc(m.name)+'" loading="lazy"></div>'
        :'<div class="member-avatar">'+esc((m.name||'?').replace(/[^가-힣A-Za-z]/g,'').slice(0,1)||'·')+'</div>';
      var role=m.expert?'AI윤리전문가 · 전문위원':'AI윤리전문가';
      return '<div class="member expert">'+av
        +'<div class="member-role">'+role+'</div>'
        +'<div class="member-name">'+esc(m.name)+'</div>'
        +(m.no?'<div class="expert-no">이수번호 '+esc(m.no)+'</div>':'')
        +'<div class="member-field">'+esc(m.field||'')+(m.org?'<br>'+esc(m.org):'')+'</div>'
        +(m.since?'<div class="expert-since">'+esc(m.since)+' 등록</div>':'')
        +'</div>';
    }
    function render(term){
      var t=(term||'').replace(/\s+/g,'').toLowerCase();
      var rows=t?list.filter(function(m){return ((m.name||'')+(m.no||'')).replace(/\s+/g,'').toLowerCase().indexOf(t)>=0;}):list;
      grid.innerHTML=rows.length?rows.map(card).join(''):'<p class="ex-empty" style="grid-column:1/-1;text-align:center;color:var(--gray-500);padding:26px 0">일치하는 등록자가 없습니다.</p>';
      nEl.textContent=t?rows.length+'명':'';
    }
    render(''); grid.hidden=false;
    q.addEventListener('input',function(){render(q.value);});
  })();
  (function(){
    var box=document.getElementById('memberSections');
    if(!box||!window.KAIEC_MEMBERS)return;
    function avatar(m){
      if(m.photo)return '<div class="member-avatar member-avatar--photo"><img src="assets/img/members/'+m.photo+'" alt="'+m.name+'" loading="lazy"></div>';
      var initial=(m.name||'?').replace(/[^가-힣A-Za-z]/g,'').slice(0,1)||'·';
      return '<div class="member-avatar">'+initial+'</div>';
    }
    function card(m,g){
      if(m.name==='공석'){
        return '<div class="member member--vacant">'
          +'<div class="member-avatar">-</div>'
          +'<div class="member-role">'+(m.role||g)+'</div>'
          +'<div class="member-name">공석</div>'
          +'<div class="member-field">'+(m.field||'위촉 예정')+'</div></div>';
      }
      return '<div class="member">'
        +avatar(m)
        +'<div class="member-role">'+(m.role||g)+'</div>'
        +'<div class="member-name">'+m.name+'</div>'
        +'<div class="member-field">'+(m.field||'')+'</div>'
        +'</div>';
    }
    /* 공석은 회색 카드 나열 대신 '위촉 진행 중' 요약 카드 1장으로 표시 */
    function recruitCard(label,n,roles){
      return '<a class="member member--recruit" href="apply.html#individual">'
        +'<div class="member-avatar"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" x2="19" y1="8" y2="14"/><line x1="22" x2="16" y1="11" y2="11"/></svg></div>'
        +'<div class="member-role">'+label+'</div>'
        +'<div class="member-name">위촉 진행 중 · '+n+'석</div>'
        +'<div class="member-field">'+(roles||'지원 안내 보기')+' →</div></a>';
    }
    function secHTML(g,inPair){
      var list=window.KAIEC_MEMBERS.filter(function(m){return m.group===g});
      if(!list.length)return '';
      var filled=list.filter(function(m){return m.name!=='공석'});
      var vacant=list.filter(function(m){return m.name==='공석'});
      var cnt=filled.length?('('+filled.length+'명'+(vacant.length?' · '+vacant.length+'석 위촉 중':'')+')')
                            :('(위촉 진행 중 · '+vacant.length+'석)');
      var cards=filled.map(function(m){return card(m,g)}).join('');
      if(vacant.length){
        var roles=vacant.map(function(m){return m.role}).filter(function(r,i,a){return r&&a.indexOf(r)===i}).join(' · ');
        cards+=recruitCard(g,vacant.length,roles);
      }
      return '<div style="margin-bottom:'+(inPair?'0':'44px')+'">'
        +'<h3 style="font-size:19px;margin-bottom:18px;display:flex;align-items:center;gap:10px">'
        +'<span style="width:4px;height:19px;background:var(--blue);border-radius:2px"></span>'+g
        +' <span style="font-size:13px;font-weight:600;color:var(--gray-500)">'+cnt+'</span></h3>'
        +'<div class="member-grid">'+cards+'</div></div>';
    }
    var html='';
    /* 상단 2열 배치: 위원장|부위원장, 고문·자문위원|감사 */
    [['위원장','부위원장'],['고문·자문위원','감사']].forEach(function(pair){
      var l=secHTML(pair[0],true), r=secHTML(pair[1],true);
      if(l||r) html+='<div class="pair-row">'+l+r+'</div>';
    });
    ['사무국','전문위원','지역 운영위원','캠퍼스 위원장','AI 윤리 앰버서더'].forEach(function(g){
      html+=secHTML(g,false);
    });
    /* AI 윤리 캠페인위원: 총원만큼 카드 표시, 이름 없으면 공석 */
    var total=window.KAIEC_CAMPAIGN_COUNT||0;
    var named=window.KAIEC_CAMPAIGN_MEMBERS||[];
    if(total){
      var cards='';
      named.slice(0,total).forEach(function(m){
        cards+=card({role:'캠페인위원',name:m.name,field:m.field||'캠페인 · 확산 활동',photo:m.photo},'캠페인위원');
      });
      var remain=Math.max(0,total-named.length);
      if(remain) cards+=recruitCard('AI 윤리 캠페인위원',remain,'전공·경력 무관 · 온라인 활동 · 홈페이지 명단 등재');
      html+='<div style="margin-bottom:10px">'
        +'<h3 style="font-size:19px;margin-bottom:18px;display:flex;align-items:center;gap:10px">'
        +'<span style="width:4px;height:19px;background:var(--teal);border-radius:2px"></span>AI 윤리 캠페인위원'
        +' <span style="font-size:13px;font-weight:600;color:var(--gray-500)">(총 '+total+'명 · 위촉 '+Math.min(named.length,total)+'명)</span></h3>'
        +'<div class="member-grid">'+cards+'</div></div>';
    }
    box.innerHTML=html||'<p style="text-align:center;color:var(--gray-500);padding:40px 0">위원 명단은 준비 중입니다.</p>';
    /* 공식 파트너 */
    var op=document.getElementById('officialPartners');
    if(op&&window.KAIEC_OFFICIAL_PARTNERS&&window.KAIEC_OFFICIAL_PARTNERS.length){
      op.innerHTML=window.KAIEC_OFFICIAL_PARTNERS.map(function(p){
        var inner=p.logo?'<img src="assets/img/'+p.logo+'" alt="'+p.name+' 로고" loading="lazy">'
                        :'<span class="logo-fallback">'+p.name+'</span>';
        var body='<div class="logo-item">'+inner+'</div>';
        var ext=p.url&&p.url.indexOf('http')===0?' target="_blank" rel="noopener"':'';
        return p.url?'<a href="'+p.url+'"'+ext+'>'+body+'</a>':body;
      }).join('');
    }else if(op){op.parentElement.parentElement.style.display='none'}
  })();
  </script>
"""
    page("members.html", "위원 명단",
         "한국AI윤리위원회 위원장·부위원장·감사·고문 및 자문위원, 사무국, 전문위원, 지역 운영위원·캠퍼스 위원장, AI 윤리 캠페인위원 명단과 공식 등록 AI윤리전문가(성명·이수번호 검색), 공식 파트너를 안내합니다.",
         body, extra_script=script)


# -------------------------------------------------------------- partner.html
def build_partner():
    faqs = [
        ("AI나 윤리 전공자가 아니어도 지원할 수 있나요?",
         "네, 가능합니다. AI 윤리위원은 전공이나 경력 요건이 없습니다. 생성형 AI를 사용해 본 경험이 있고 책임 있는 활용에 관심이 있다면 누구나 지원하실 수 있습니다."),
        ("활동은 어디에서 하나요? 정해진 근무 시간이 있나요?",
         "모든 활동은 온라인·재택으로 진행되며 정해진 출근 시간이나 장소가 없습니다. 각자의 일정에 맞춰 배정된 활동을 수행하시면 됩니다."),
        ("공식 위원 명단 등재와 활동증명서는 무엇인가요?",
         "위촉되면 한국AI윤리위원회 홈페이지의 공식 위원 명단에 성명이 등록되고, 활동 실적에 따라 위원회가 활동 기간과 내역을 확인한 활동증명서를 발급합니다. 누구나 확인할 수 있는 공식 기록이라 대외활동 이력서나 포트폴리오의 증빙 자료로 활용하실 수 있습니다."),
        ("인센티브는 어떤 기준으로 지급되나요?",
         "활동 실적(캠페인 참여, 콘텐츠 제작, 제휴 캠페인 기여 등)을 기준으로 산정합니다. 구체적인 기준과 지급 방식은 위촉 시 개별 안내드립니다."),
        ("활동 기간은 어떻게 되나요?",
         "기본 위촉 기간은 6개월이며, 상호 협의에 따라 연장할 수 있습니다. 개인 사정으로 중도 종료를 원하실 경우 언제든 알려주시면 됩니다."),
        ("비용이 드나요?",
         "가입비·교육비·연회비 등 위원이 위원회에 지불하는 비용은 일절 없습니다."),
    ]
    faq_html = "\n".join(f"""        <details class="acc">
          <summary>{q}</summary>
          <div class="acc-body">{a}</div>
        </details>""" for q, a in faqs)

    body = hero_sub("AI 윤리위원",
                    "온라인·재택으로 AI 윤리 문화 확산에 참여하는 위원회의 대표 참여 제도입니다.",
                    "AI 윤리위원") + f"""

    <section class="section">
      <div class="wrap-narrow center">
        <span class="eyebrow">Partner Program</span>
        <h2 class="h-sec">AI 윤리를 알리는 사람,<br>지금 AI 윤리위원으로 시작하세요</h2>
        <p class="h-sub" style="margin:0 auto">
          AI 윤리는 전문가 몇 명이 아니라, AI를 매일 활용하는 사람들이 함께 만들어갑니다.
          AI 윤리위원은 그 확산을 현장에서 이끄는 위원회의 실천 조직입니다. 온라인·재택으로 참여할 수 있습니다.
        </p>
        <div style="display:flex;gap:11px;justify-content:center;flex-wrap:wrap;margin-top:28px">
          <a class="btn btn-primary" href="join.html#apply">위원 지원하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-ghost" href="#apply-info">활동·혜택 먼저 보기</a>
        </div>
      </div>
    </section>

    <section class="section section--gray section--tight" id="apply-info">
      <div class="wrap">
        <div class="grid grid-4">
          <div class="card reveal center"><div class="card-icon" style="margin:0 auto 16px"><i data-lucide="wifi"></i></div>
            <h3>100% 온라인</h3><p>출근·대면 없이 재택으로 참여</p></div>
          <div class="card reveal center"><div class="card-icon" style="margin:0 auto 16px"><i data-lucide="id-card"></i></div>
            <h3>공식 명단 등재</h3><p>홈페이지 공식 위원 명단 등록</p></div>
          <div class="card reveal center"><div class="card-icon" style="margin:0 auto 16px"><i data-lucide="file-check"></i></div>
            <h3>활동증명서</h3><p>활동 내역 확인 문서 발급</p></div>
          <div class="card reveal center"><div class="card-icon card-icon--teal" style="margin:0 auto 16px"><i data-lucide="gift"></i></div>
            <h3>활동 인센티브</h3><p>실적에 따른 인센티브 지급</p></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Activities</span>
          <h2 class="h-sec">위원 활동 내용</h2>
          <p class="h-sub">본인의 관심과 여건에 맞는 활동을 선택해 참여하실 수 있습니다.</p>
        </div>
        <div class="grid grid-3">
          <article class="card reveal">
            <div class="card-icon"><i data-lucide="megaphone"></i></div>
            <h3>AI 윤리 문화 확산 캠페인</h3>
            <p>온라인 캠페인, 카드뉴스·영상 등 AI 윤리 콘텐츠를 공유하고 주변에 알리는 활동입니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon"><i data-lucide="pen-line"></i></div>
            <h3>콘텐츠 기획 및 제작</h3>
            <p>사례 정리, 글·이미지·영상 제작 등 위원회 콘텐츠 제작에 참여합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="handshake"></i></div>
            <h3>카피클린 제휴 캠페인</h3>
            <p>제휴 서비스 「카피클린」과 함께하는 AI 활용 문서 사전점검 캠페인에 참여합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon"><i data-lucide="school"></i></div>
            <h3>대학·커뮤니티 알림 활동</h3>
            <p>소속 대학, 학과, 온라인 커뮤니티 등에 AI 윤리 활동을 안내합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon"><i data-lucide="clipboard-list"></i></div>
            <h3>현장 의견 수집</h3>
            <p>AI 활용 현장에서 겪는 어려움과 사례를 수집해 위원회에 전달합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon"><i data-lucide="users-round"></i></div>
            <h3>위원 네트워크 참여</h3>
            <p>온라인 모임과 스터디에 참여해 다른 위원들과 정보를 나눕니다.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="section section--ink">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Benefits</span>
          <h2 class="h-sec" style="color:#fff">위원 혜택</h2>
        </div>
        <div class="grid grid-3">
          <div style="background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:30px">
            <div style="width:46px;height:46px;border-radius:13px;background:rgba(111,227,216,.16);color:#6FE3D8;display:flex;align-items:center;justify-content:center;margin-bottom:16px"><i data-lucide="award"></i></div>
            <h3 style="color:#fff;font-size:18px;margin-bottom:9px">홈페이지 공식 위원 명단 등재</h3>
            <p style="color:#9FB3D1;font-size:14.5px;line-height:1.75">위촉되면 한국AI윤리위원회 홈페이지 공식 위원 명단에 성명이 등록됩니다. 누구나 확인할 수 있는 공식 기록입니다.</p>
          </div>
          <div style="background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:30px">
            <div style="width:46px;height:46px;border-radius:13px;background:rgba(111,227,216,.16);color:#6FE3D8;display:flex;align-items:center;justify-content:center;margin-bottom:16px"><i data-lucide="file-check"></i></div>
            <h3 style="color:#fff;font-size:18px;margin-bottom:9px">활동증명서 발급</h3>
            <p style="color:#9FB3D1;font-size:14.5px;line-height:1.75">활동 종료 또는 요청 시 활동 기간과 내역을 담은 증명서를 발급합니다.</p>
          </div>
          <div style="background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:30px">
            <div style="width:46px;height:46px;border-radius:13px;background:rgba(111,227,216,.16);color:#6FE3D8;display:flex;align-items:center;justify-content:center;margin-bottom:16px"><i data-lucide="trending-up"></i></div>
            <h3 style="color:#fff;font-size:18px;margin-bottom:9px">활동 인센티브</h3>
            <p style="color:#9FB3D1;font-size:14.5px;line-height:1.75">캠페인 참여·콘텐츠 제작 등 활동 실적에 따라 인센티브를 지급합니다.</p>
          </div>
        </div>
        <div class="footer-disclaimer" style="margin-top:26px">
          인센티브의 구체적 기준과 지급 방식은 위촉 시 개별 안내드립니다.
          활동증명서는 요청 시 발급해 드립니다.
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">How to Join</span>
          <h2 class="h-sec">지원 자격 및 절차</h2>
        </div>
        <div class="table-wrap" style="margin-bottom:34px">
          <table class="tbl" style="min-width:auto">
            <tbody>
              <tr><th style="width:28%">지원 자격</th><td>AI 윤리에 관심 있는 만 19세 이상 누구나 (전공·경력 무관)</td></tr>
              <tr><th>활동 방식</th><td>온라인 · 재택</td></tr>
              <tr><th>위촉 기간</th><td>6개월 (협의 시 연장 가능)</td></tr>
              <tr><th>모집 시기</th><td>상시</td></tr>
              <tr><th>지원 비용</th><td>없음 (가입비·교육비 일절 없음)</td></tr>
            </tbody>
          </table>
        </div>
        <div class="grid grid-4">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">온라인 지원</h3><p style="font-size:14px">지원서 작성·제출</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">서류 검토</h3><p style="font-size:14px">약 3~5일 소요</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">위촉 안내</h3><p style="font-size:14px">공식 명단 등재 · 오리엔테이션</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">활동 시작</h3><p style="font-size:14px">활동 배정 및 수행</p></div>
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">FAQ</span>
          <h2 class="h-sec">자주 묻는 질문</h2>
        </div>
{faq_html}
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("AI 윤리위원 지원하기", "join.html#apply")}
      </div>
    </section>"""

    page("partner.html", "AI 윤리위원",
         "한국AI윤리위원회 AI 윤리위원은 온라인·재택으로 AI 윤리 문화 확산 캠페인에 참여하며, 홈페이지 공식 위원 명단 등재와 활동증명서 발급, 활동 실적에 따른 인센티브 혜택을 받을 수 있습니다.",
         body)


# ------------------------------------------------------------- copyclean.html
def build_copyclean():
    body = hero_sub("제휴 서비스 「카피클린」",
                    "AI 활용 문서의 책임 있는 사전점검 문화를 함께 만들어가는 위원회의 협력 서비스입니다.",
                    "카피클린") + f"""

    <section class="section">
      <div class="wrap">
        <div class="notice" style="margin-bottom:48px">
          <strong>파트너십:</strong> 한국AI윤리위원회와 「카피클린(CopyClean)」은
          AI 활용 문서의 <strong>사전점검 문화 확산</strong>을 위해 협력하는 파트너입니다.
          위원회는 윤리 기준·캠페인·교육을, 카피클린은 AI 문서 분석 기술을 담당합니다.
        </div>

        <div class="split">
          <div class="reveal">
            <span class="eyebrow">Affiliated Service</span>
            <h2 class="h-sec">카피클린 (CopyClean)</h2>
            <p class="lead" style="margin-bottom:18px">
              논문 · 과제 · 보고서 · 자기소개서 등 다양한 문서를 대상으로
              <strong>AI 활용 여부를 사전에 확인</strong>할 수 있도록 지원하는 AI 문서 분석 서비스입니다.
            </p>
            <p style="font-size:16px;color:var(--gray-600);line-height:1.8;margin-bottom:24px">
              제출하기 전에 스스로 확인해 볼 수 있다는 점이 핵심입니다.
              문제를 사후에 지적하는 것이 아니라, 사전에 점검해 불필요한 오해와 분쟁을 예방하는 데 목적이 있습니다.
            </p>
            <a class="btn btn-teal" href="{COPYCLEAN_URL}" target="_blank" rel="noopener">카피클린 공식 사이트 바로가기 <i data-lucide="external-link"></i></a>
          </div>
          <div class="split-visual reveal" style="background:linear-gradient(150deg,#0A1628,#00857A)">
            <div class="card-icon" style="background:rgba(255,255,255,.15);color:#fff;width:56px;height:56px">
              <i data-lucide="file-search" style="width:26px;height:26px"></i>
            </div>
            <h3 style="font-size:25px;letter-spacing:-.035em">제출 전에<br>스스로 확인하는 습관</h3>
            <p style="color:#CDE9E5;font-size:15px;line-height:1.8">
              논문 · 과제 · 보고서 · 자기소개서<br>다양한 문서의 AI 활용 여부 사전 확인</p>
            <a class="btn btn-white btn-sm" href="{COPYCLEAN_URL}" target="_blank" rel="noopener" style="align-self:flex-start">skkc.co.kr <i data-lucide="external-link"></i></a>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Collaboration</span>
          <h2 class="h-sec">위원회 × 카피클린 제휴 활동</h2>
          <p class="h-sub">위원회는 카피클린과 함께 AI 활용 문서의 사전점검 및 책임 있는 AI 활용 문화 확산을 위한
             캠페인과 제휴 활동을 진행합니다.</p>
        </div>
        <div class="grid grid-3">
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="megaphone"></i></div>
            <h3>사전점검 캠페인</h3>
            <p>“제출 전에 한 번 확인하기”를 주제로 한 공동 캠페인을 기획·운영합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="book-open-check"></i></div>
            <h3>가이드라인 공동 개발</h3>
            <p>문서 유형별 AI 활용 표기 및 점검 가이드라인을 함께 정리해 배포합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="graduation-cap"></i></div>
            <h3>대학·기관 대상 안내</h3>
            <p>대학과 기관을 대상으로 사전점검 문화의 필요성을 함께 알립니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="users"></i></div>
            <h3>위원 연계 활동</h3>
            <p>AI 윤리위원이 참여하는 제휴 캠페인을 공동으로 운영합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="bar-chart-3"></i></div>
            <h3>사례 수집 및 공유</h3>
            <p>현장에서 실제로 발생하는 AI 활용 관련 사례를 수집해 공유합니다.</p>
          </article>
          <article class="card reveal">
            <div class="card-icon card-icon--teal"><i data-lucide="shield-check"></i></div>
            <h3>윤리 기준 자문</h3>
            <p>위원회가 정리한 AI 윤리 기준을 서비스 운영에 참고할 수 있도록 자문합니다.</p>
          </article>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="cta-band reveal" style="background:linear-gradient(140deg,#03231F,#00857A)">
          <div>
            <h2>제출 전, 카피클린에서 직접 확인해 보세요</h2>
            <p style="color:#BFE8E3">논문 · 과제 · 보고서 · 자기소개서의 AI 활용 여부를 제출 전에 스스로 점검할 수 있습니다.</p>
          </div>
          <div class="btns">
            <a class="btn btn-white" href="{COPYCLEAN_URL}" target="_blank" rel="noopener">카피클린 바로가기 <i data-lucide="external-link"></i></a>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">FAQ</span>
          <h2 class="h-sec">AI 유사도 검사, 자주 묻는 질문</h2>
        </div>
        <details class="acc">
          <summary>AI 유사도 검사란 무엇인가요?</summary>
          <div class="acc-body">문서의 문장들이 생성형 AI(챗GPT 등)로 작성됐을 가능성을 분석해 <strong>AI 유사도</strong>라는
            지표로 보여주는 검사입니다. 학위논문·학술지 논문·과제·레포트·자기소개서가 주요 대상입니다.
            개념이 처음이라면 <a href="post-2026-08-21-ai-similarity-check-guide.html" style="color:var(--blue);font-weight:600">AI 유사도 검사 완전 가이드</a>를 먼저 읽어보세요.</div>
        </details>
        <details class="acc">
          <summary>표절검사와 AI 유사도 검사는 다른 건가요?</summary>
          <div class="acc-body">다릅니다. 표절검사는 기존 문서와 겹치는 부분을 찾고, AI 유사도 검사는 문장이
            AI로 생성됐을 가능성을 판정합니다. 그래서 표절검사에 문제가 없어도 AI 유사도는 높게 나올 수 있습니다.
            제출 문서라면 두 관점 모두 점검하는 것이 안전합니다.</div>
        </details>
        <details class="acc">
          <summary>AI 유사도가 높게 나오면 어떻게 해야 하나요?</summary>
          <div class="acc-body">자동 변환 도구로 낮추는 방식은 권하지 않습니다. 카피클린의 AI 유사도 상세리포트로
            어느 문장이 판정됐는지 확인한 뒤, 해당 부분을 <strong>본인의 언어로 다시 쓰고 재검사</strong>하는 것이
            가장 안전하고 확실한 방법입니다. 자세한 순서는
            <a href="post-2026-08-20-lower-ai-similarity.html" style="color:var(--blue);font-weight:600">올바른 대응 가이드</a>에 정리되어 있습니다.</div>
        </details>
        <details class="acc">
          <summary>어떤 문서를 검사할 수 있나요?</summary>
          <div class="acc-body">학위논문, 학술지 논문, 과제·레포트, 자기소개서를 검사할 수 있습니다.
            논문 심사 전, 과제 제출 전, 채용 서류 마감 전 등 <strong>제출 직전 단계</strong>에서 이용하는 것이 가장 효과적입니다.
            이용 순서는 <a href="post-2026-08-07-copyclean-precheck-guide.html" style="color:var(--blue);font-weight:600">카피클린 이용 가이드</a>를 참고하세요.</div>
        </details>
        <details class="acc">
          <summary>AI를 활용하지 않았는데도 검사가 필요한가요?</summary>
          <div class="acc-body">AI 탐지는 확률 판정이라 직접 쓴 글이 판정되는 경우도 드물게 있습니다.
            제출 전 검사 결과를 보관해 두면 오해가 생겼을 때 <strong>소명 자료</strong>가 됩니다.
            억울한 판정에 대한 대응법은 <a href="post-2026-08-16-false-positive-response.html" style="color:var(--blue);font-weight:600">별도 칼럼</a>에서 다룹니다.</div>
        </details>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">Roles</span>
          <h2 class="h-sec">역할 구분</h2>
          <p class="h-sub">두 주체의 역할을 명확히 구분해 안내드립니다.</p>
        </div>
        <div class="table-wrap">
          <table class="tbl">
            <thead>
              <tr><th style="width:22%">구분</th><th>한국AI윤리위원회</th><th>카피클린 (CopyClean)</th></tr>
            </thead>
            <tbody>
              <tr><th>성격</th><td>AI 윤리 전문기관</td><td>AI 문서 분석 서비스</td></tr>
              <tr><th>역할</th><td>AI 윤리 문화 확산, 교육·연구·캠페인, 사회공헌</td><td>문서의 AI 활용 여부 사전 확인 지원</td></tr>
              <tr><th>관계</th><td colspan="2" style="text-align:center;font-weight:700;color:var(--blue)">캠페인·제휴 활동을 함께하는 협력 파트너</td></tr>
              <tr><th>대상</th><td>개인 · 대학 · 기업 · 협회 등</td><td>논문 · 과제 · 보고서 · 자기소개서 등 문서</td></tr>
            </tbody>
          </table>
        </div>
        <div class="notice notice--teal" style="margin-top:24px">
          두 파트너는 "제출 전에 스스로 확인하는 문화"라는 공동의 목표 아래
          캠페인 · 교육 · 가이드라인 개발을 함께 진행하고 있습니다.
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("사회공헌 활동 문의", "mou.html#inquiry")}
      </div>
    </section>"""

    page("copyclean.html", "카피클린 · AI 유사도 검사",
         "카피클린(CopyClean)은 논문·과제·자기소개서의 AI 유사도를 문장 단위로 검사하는 AI 문서 분석 서비스입니다. 한국AI윤리위원회 제휴 서비스로 제출 전 사전점검 캠페인을 함께합니다.",
         body,
         keywords=["카피클린", "AI 유사도 검사", "AI 유사도", "AI 검사기", "논문 AI 검사", "과제 AI 검사",
                   "자소서 AI 검사", "챗GPT 검사", "AI 유사도 상세리포트", "논문컨설팅", "AI 사전점검"])


# ----------------------------------------------------------------- news.html
def build_news(posts):
    cat_btns = '<button class="btn btn-sm btn-primary" data-cat="전체">전체</button>' + "".join(
        f'<button class="btn btn-sm btn-ghost" data-cat="{c}">{c}</button>' for c in CATEGORIES)
    cards = "\n".join(board_card(p) for p in posts) if posts else \
        '<p style="text-align:center;color:var(--gray-500);padding:50px 0">등록된 소식이 없습니다.</p>'

    body = hero_sub("커뮤니티",
                    "AI 윤리 · AI 유사도 검사 · 연구윤리에 대한 전문가 칼럼과 위원회 소식을 전합니다.",
                    "커뮤니티") + f"""

    <section class="section">
      <div class="wrap">
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:30px" id="newsFilter">
          {cat_btns}
        </div>
        <div class="board-grid" id="boardGrid">
{cards}
        </div>
      </div>
    </section>"""

    script = """  <script>
  /* 분류 필터: 게시글 자체는 정적 HTML이라 검색엔진이 전부 읽습니다 */
  (function(){
    var filter=document.getElementById('newsFilter');
    var cards=document.querySelectorAll('#boardGrid .board-card');
    if(!filter)return;
    filter.addEventListener('click',function(e){
      var b=e.target.closest('button[data-cat]');if(!b)return;
      filter.querySelectorAll('button').forEach(function(x){x.className='btn btn-sm btn-ghost'});
      b.className='btn btn-sm btn-primary';
      var cat=b.getAttribute('data-cat');
      cards.forEach(function(c){
        c.style.display=(cat==='전체'||c.getAttribute('data-cat')===cat)?'':'none';
      });
    });
  })();
  </script>
"""
    page("news.html", "커뮤니티 · AI 윤리 칼럼과 위원회 소식",
         "AI 윤리, AI기본법, AI 유사도 검사와 연구윤리, AI윤리전문가 양성과정까지. 한국AI윤리위원회의 전문가 칼럼, 공지, 캠페인 소식을 한곳에서 확인하세요.",
         body + cert_band("양성과정 안내", "expert.html"), extra_script=script,
         keywords=["AI 유사도 검사", "AI 유사도", "AI 검사기", "논문컨설팅", "논문 컨설팅", "카피클린",
                   "AI 탐지", "논문 AI 검사", "과제 AI 검사", "자소서 AI 검사"])


# ------------------------------------------------------------- 게시글 페이지
def build_post(p, posts):
    idx = posts.index(p)
    prev_p = posts[idx + 1] if idx + 1 < len(posts) else None   # 이전 글(더 오래된 글)
    next_p = posts[idx - 1] if idx > 0 else None                # 다음 글(더 새 글)

    cover = ""
    ogimg = None
    if p["image"]:
        cover = f'''        <div class="post-cover"><img src="assets/img/posts/{p["image"]}" alt="{_html.escape(p["title"])}"></div>\n'''
        ogimg = f'{SITE_URL}/assets/img/posts/{p["image"]}'

    tags = "".join(f'<span class="chip">#{k}</span>' for k in p["keywords"])
    badge = 'badge--teal' if p["category"] == '캠페인' else ''

    nav_html = '<div class="post-nav">'
    nav_html += (f'<a class="btn btn-ghost btn-sm" href="{prev_p["file"]}"><i data-lucide="arrow-left"></i> 이전 글</a>'
                 if prev_p else '<span></span>')
    nav_html += '<a class="btn btn-primary btn-sm" href="news.html">목록으로</a>'
    nav_html += (f'<a class="btn btn-ghost btn-sm" href="{next_p["file"]}">다음 글 <i data-lucide="arrow-right"></i></a>'
                 if next_p else '<span></span>')
    nav_html += '</div>'

    # 관련 글: 같은 분류 2건 + 다른 분류 1건(양성과정 소개 글 우선) → 분류를 섞어야 다음 클릭이 나옴
    same = [q for q in posts if q is not p and q["category"] == p["category"]]
    others = [q for q in posts if q is not p and q not in same]
    intro = [q for q in others if "ai-ethics-expert-intro" in q["file"]]
    rel = same[:2] + (intro[:1] or others[:1])
    rel = (rel + [q for q in same[2:] + others if q not in rel])[:3]

    # 본문 가공: 읽는 시간, h2 목차(3개 이상일 때), 마지막 h2 앞 양성과정 안내 박스
    body_html = md_to_html(p["body"])
    plain_len = len(_strip_tags(body_html))
    read_min = max(1, round(plain_len / 550))
    heads = re.findall(r'<h2>(.*?)</h2>', body_html)
    for i, h in enumerate(heads, 1):
        body_html = body_html.replace(f'<h2>{h}</h2>', f'<h2 id="sec-{i}">{h}</h2>', 1)
    toc_html = ""
    if len(heads) >= 3:
        toc_html = ('<nav class="toc" aria-label="목차"><span class="toc-title">이 글의 내용</span><ol>'
                    + "".join(f'<li><a href="#sec-{i}">{_strip_tags(h)}</a></li>' for i, h in enumerate(heads, 1))
                    + '</ol></nav>')
    mid_cta = f"""<aside class="post-cta">
  <span class="post-cta-kicker">한국AI윤리위원회 주관 · AI윤리전문가 양성과정</span>
  <strong>AI를 어디까지 어떻게 활용해야 하는지, 기준을 아는 사람이 조직의 리스크를 줄입니다.</strong>
  <p>위원회 표준교재와 온라인 이수 평가로 한국AI윤리위원회 공식 이수증을 받고 홈페이지에 공식 등록되세요. 특별가 {won(PRICE)}(정가 {won(LIST_PRICE)}) · {HOOK_ZERO}.</p>
  <span class="post-cta-links"><a class="btn btn-primary btn-sm" href="{CERT_HREF}">{CERT_CTA}</a><a class="btn btn-ghost btn-sm" href="quiz.html">AI 윤리 실무 진단</a></span>
</aside>
"""
    if len(heads) >= 2:
        last = f'<h2 id="sec-{len(heads)}">'
        body_html = body_html.replace(last, mid_cta + last, 1)
    else:
        body_html += mid_cta
    rel_html = ""
    if rel:
        cards = "".join(
            f'<a class="rel-card" href="{q["file"]}">'
            + (f'<div class="rel-thumb"><img src="assets/img/posts/{q["image"]}" alt="" loading="lazy"></div>' if q["image"] else '')
            + f'<div class="rel-body"><span class="rel-cat">{q["category"]} · {q["date"]}</span><strong>{q["title"]}</strong></div></a>'
            for q in rel)
        rel_html = f"""
    <section class="section section--tight rel-sec">
      <div class="wrap">
        <h2 class="rel-title">함께 읽으면 좋은 글</h2>
        <div class="rel-grid">{cards}</div>
      </div>
    </section>"""

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner" style="max-width:var(--wrap)">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; <a href="news.html" style="color:inherit">커뮤니티</a></p>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
          <span class="badge {badge}">{p["category"]}</span>
          <span style="font-size:13.5px;color:#7E9AC0;font-weight:600">{p["date"]}</span>
        </div>
        <h1 style="max-width:820px">{p["title"]}</h1>
        <p>{p["summary"]}</p>
        <p class="post-meta"><i data-lucide="clock"></i> 읽는 시간 약 {read_min}분 · 한국AI윤리위원회</p>
      </div>
    </section>

    <section class="section">
      <div class="post-wrap">
{cover}        {toc_html}
        <article class="post-body">
{body_html}
        </article>
        <div class="post-tags">{tags}</div>
{nav_html}
      </div>
    </section>
{rel_html}
    <section class="section section--tight">
      <div class="wrap">
        {cert_band_inner("양성과정 안내", "expert.html", title="한국AI윤리위원회 AI윤리전문가 양성과정")}
      </div>
    </section>"""

    iso_date = p["dt"].strftime("%Y-%m-%d")
    ld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {_json_str(p["title"])},
  "articleSection": {_json_str(p["category"])},
  "inLanguage": "ko-KR",
  "description": {_json_str(p["summary"])},
  "datePublished": "{iso_date}",
  "dateModified": "{iso_date}",
  "keywords": {_json_str(", ".join(p["keywords"]))},
  {'"image": ["' + ogimg + '"],' if ogimg else ''}
  "author": {{"@type": "Organization", "name": "{SITE_NAME}", "url": "{SITE_URL}"}},
  "publisher": {{"@type": "Organization", "name": "{SITE_NAME}", "logo": {{"@type": "ImageObject", "url": "{SITE_URL}/assets/img/og-image.png"}}}},
  "mainEntityOfPage": "{SITE_URL}{url_for(p["file"])}"
}}
</script>
"""
    page(p["file"], p["title"],
         (p["summary"] or p["title"])[:150],
         body, extra_head=ld,
         keywords=p["keywords"] or None, og_image=ogimg,
         og_type="article", published=iso_date, crumb_parent=("커뮤니티", "news.html"), sticky="mobile")


def _json_str(s):
    import json
    return json.dumps(s, ensure_ascii=False)


# ---------------------------------------------- 법적 고지 문서 (2026.09.17 신설)
LEGAL_DATE = "2026년 9월 17일"
ORG_HEAD = "신동복"                      # 위원장 (대표자 표기)
ORG_REG = "272-32-01885"                # 고유번호
ORG_ADDR = "경기도 수원시 장안구 서부로 2066 성균관대학교 브릿지팩토리 (16419)"
PRIVACY_OFFICER = "오준호 사무총장"
PAY_AGENT = "성균관컨설팅"
PAY_AGENT_URL = "https://www.skkc.co.kr"


def legal_page(fname, nav_title, h1, lead, sections, desc):
    """서비스 이용안내·개인정보 운영정책 공통 틀.
    sections 항목은 (소제목, 본문) 또는 (소제목, 본문, id), 문자열이면 그대로 삽입합니다."""
    parts = []
    for it in sections:
        if isinstance(it, str):
            parts.append(it)
            continue
        sid = f' id="{it[2]}"' if len(it) > 2 else ''
        parts.append(f"""        <section class="lg-sec"{sid}>
          <h2>{it[0]}</h2>
          {it[1]}
        </section>""")
    secs = "\n".join(parts)
    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner" style="padding-block:60px 54px">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; {nav_title}</p>
        <h1>{h1}</h1>
        <p style="max-width:720px">{lead}</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="lg-meta">
          <span>시행일 {LEGAL_DATE}</span><span class="fsep">|</span>
          <span>한국AI윤리위원회 (Korea AI Ethics Committee)</span>
        </div>
        <div class="legal">
{secs}
        </div>
        <div class="lg-links">
          <a href="terms.html">서비스 이용안내</a>
          <a href="privacy.html">개인정보·운영정책</a>
        </div>
      </div>
    </section>"""
    page(fname, nav_title, desc, body, sticky=None)


def build_legal():
    # ---------------------------------------------------------------- 이용약관
    legal_page(
        "terms.html", "서비스 이용안내", "서비스 이용안내",
        "한국AI윤리위원회가 운영하는 kaiec.kr 과 이곳에서 제공하는 교육·평가·발급 서비스의 이용 조건입니다. "
        "신청 전에 확인해 주시기 바랍니다.",
        [
            ("제1조 (목적)",
             "<p>이 약관은 한국AI윤리위원회(이하 “위원회”)가 kaiec.kr 을 통해 제공하는 AI윤리전문가 양성과정, "
             "온라인 이수 평가, 이수증 발급과 이수자 등록, 그 밖의 부수 서비스(이하 “서비스”)의 이용에 관하여 "
             "위원회와 이용자의 권리·의무 및 책임 사항을 정하는 것을 목적으로 합니다.</p>"),
            ("제2조 (용어의 정의)",
             "<ol><li><strong>이용자</strong>란 이 약관에 따라 서비스를 이용하는 모든 분을 말합니다.</li>"
             "<li><strong>수강자</strong>란 AI윤리전문가 양성과정을 신청하고 교육비 결제를 완료한 이용자를 말합니다.</li>"
             "<li><strong>학습자료</strong>란 위원회가 수강자에게 제공하는 표준교재, 모의고사, 정답 및 해설, 실무 도구집, "
             "응시 안내 등 전자문서(PDF) 일체를 말합니다.</li>"
             "<li><strong>이수 평가</strong>란 위원회가 온라인으로 시행하는 평가를 말합니다.</li>"
             "<li><strong>이수증</strong>이란 이수 기준을 충족한 수강자에게 위원회가 발급하는 교육 이수 확인 문서를 말합니다.</li></ol>"),
            ("제3조 (약관의 게시와 개정)",
             "<ol><li>위원회는 이 약관을 서비스 화면에 게시하여 이용자가 언제든지 확인할 수 있도록 합니다.</li>"
             "<li>위원회는 관계 법령을 위반하지 않는 범위에서 이 약관을 개정할 수 있으며, 개정 시 적용일과 개정 사유를 "
             "명시하여 적용일 7일 전부터 서비스 화면에 공지합니다. 이용자에게 불리한 개정의 경우에는 30일 전부터 공지합니다.</li>"
             "<li>이용자가 개정 약관의 적용에 동의하지 않는 경우 서비스 이용을 중단하고 탈퇴를 요청할 수 있습니다.</li></ol>"),
            ("제4조 (서비스의 내용)",
             "<p>위원회가 제공하는 서비스는 다음과 같습니다.</p>"
             "<ol><li>AI윤리전문가 양성과정 학습자료의 제공</li>"
             "<li>온라인 이수 평가의 시행과 채점, 결과 안내</li>"
             "<li>이수 기준 충족자에 대한 이수증(PDF) 발급과 이수자 명부 등록</li>"
             "<li>AI 윤리 관련 공개 자료, 캠페인, 교육기부 등 공익 활동</li>"
             "<li>기관 대상 출강·자문 및 협력 사업</li></ol>"),
            ("제5조 (신청과 계약의 성립)",
             "<ol><li>양성과정 이용계약은 이용자가 신청 양식을 작성하여 제출하고, 교육비 결제가 완료된 시점에 성립합니다.</li>"
             "<li>이용자는 신청 시 정확한 정보를 기재하여야 합니다. 허위 정보로 인해 발생한 불이익은 이용자가 부담합니다.</li>"
             "<li>신청 이메일은 이수 평가 시스템의 로그인 계정으로 사용되므로, 결제 시에도 동일한 이메일을 입력하여야 합니다. "
             "이메일 불일치로 계정이 생성되지 않은 경우 이용자는 위원회에 정정을 요청하여야 합니다.</li>"
             "<li>위원회는 다음 각 호의 경우 신청을 승낙하지 않거나 사후에 계약을 해지할 수 있습니다."
             "<ul><li>타인의 명의를 도용하거나 허위 정보를 기재한 경우</li>"
             "<li>이 약관을 위반하여 과거에 이용이 제한된 사실이 있는 경우</li>"
             "<li>서비스의 정상적인 운영을 방해할 우려가 명백한 경우</li></ul></li></ol>"),
            ("제6조 (교육비의 결제)",
             f"<ol><li>교육비 결제와 그에 따른 전자결제 업무는 위원회의 교육 운영사인 {PAY_AGENT}"
             f"(<a href=\"{PAY_AGENT_URL}\" target=\"_blank\" rel=\"noopener\">{PAY_AGENT_URL}</a>)가 수행합니다. "
             "결제 수단, 영수증 발행, 통신판매업 신고 사항 등 판매자 정보는 해당 사이트에서 확인하실 수 있습니다.</li>"
             "<li>공지된 교육비는 학습자료 제공, 이수 평가 응시와 재응시, 이수증 발급, 이수자 등록에 드는 비용을 모두 포함합니다. "
             "위원회는 이 밖의 명목으로 추가 비용을 청구하지 않습니다.</li>"
             "<li>기수별 특별가 등 한시적으로 적용되는 금액은 공지된 기간에만 적용되며, 기간 종료 후 신청분에는 적용되지 않습니다.</li></ol>"),
            ("제7조 (학습자료의 제공)",
             "<ol><li>위원회는 결제 확인 후 이용자가 신청 시 기재한 이메일로 학습자료(PDF) 내려받기 링크를 발송합니다.</li>"
             "<li>학습자료는 전자문서로만 제공되며 인쇄물 형태로는 제공하지 않습니다.</li>"
             "<li>이용자의 이메일 오기재, 수신 거부 설정, 메일함 용량 초과 등 이용자 측 사유로 수신되지 않은 경우에도 "
             "위원회가 발송을 완료한 때에 제공이 개시된 것으로 봅니다. 이 경우 이용자의 요청이 있으면 위원회는 재발송합니다.</li></ol>"),
            ("제8조 (이수 평가)",
             "<ol><li>이수 평가는 결제일부터 공지된 응시 기간 안에 온라인으로 응시할 수 있습니다.</li>"
             "<li>응시 기간 안에서는 이수 기준에 도달할 때까지 횟수 제한 없이 다시 응시할 수 있으며, 재응시에 드는 추가 비용은 없습니다.</li>"
             "<li>이용자의 통신 환경, 기기 성능, 브라우저 설정 등 이용자 측 사유로 응시가 중단된 경우 위원회는 "
             "확인 가능한 범위에서 응시 기회를 복구할 수 있으나, 그로 인한 시간 손실에 대한 보상 의무는 지지 않습니다.</li>"
             "<li>다음 각 호에 해당하면 해당 응시를 무효로 처리합니다."
             "<ul><li>본인이 아닌 사람이 응시한 경우</li>"
             "<li>계정을 타인과 공유하거나 양도한 경우</li>"
             "<li>문항이나 답안을 촬영·복제·유출한 경우</li>"
             "<li>그 밖에 평가의 공정성을 현저히 해친 경우</li></ul></li></ol>"),
            ("제9조 (이수증 발급과 이수자 등록)",
             "<ol><li>이수 기준을 충족한 수강자에게는 이수번호가 부여된 이수증(PDF)이 발급되고, 위원회 이수자 명부에 등록됩니다.</li>"
             "<li>발급은 결과 확인 후 통상 7일 이내에 이루어지며, 공휴일·시스템 점검·확인 지연 등의 사정이 있는 경우 소요 기간이 달라질 수 있습니다.</li>"
             "<li>이수자는 별도의 등록 신청 절차를 거쳐 위원회 전문위원으로 등록될 수 있습니다. 전문위원 등록은 "
             "위원회의 심사를 거치며, 이수 사실만으로 당연히 등록되는 것은 아닙니다.</li>"
             "<li>이수자는 이수 사실을 이력서, 포트폴리오 등에 기재할 수 있습니다. 다만 위원회가 부여하지 않은 명칭이나 "
             "등급을 임의로 덧붙여 표기해서는 안 됩니다.</li></ol>"),
            ("제10조 (이수증의 성격)",
             "<p>이수증은 위원회가 자체적으로 운영하는 교육과정의 이수 사실을 확인하는 문서이며, "
             "<strong>국가가 신설하거나 공인한 제도가 아니며, 「자격기본법」이 정한 검정 절차를 거치지 않습니다.</strong> 위원회는 서비스 어디에서도 "
             "이수증을 면허나 인증으로 표기하지 않으며, 이용자 또한 제도상의 자격을 얻은 것으로 표기해서는 안 됩니다. "
             "이수 사실은 특정한 취업, 승진, 채용, 수주 등의 결과를 보장하지 않습니다.</p>"),
            ("제11조 (지식재산권)",
             "<ol><li>학습자료, 평가 문항, 해설, 홈페이지에 게시된 글·이미지·디자인 등 서비스와 관련된 저작물의 권리는 "
             "위원회 또는 정당한 권리자에게 있습니다.</li>"
             "<li>이용자는 학습자료와 평가 문항을 개인의 학습 목적으로만 사용할 수 있으며, 위원회의 사전 서면 동의 없이 "
             "다음 행위를 해서는 안 됩니다."
             "<ul><li>복제, 전송, 배포, 출판, 판매, 대여, 공유 링크 게시</li>"
             "<li>강의·교재 등 2차적 저작물 작성 및 영리적 이용</li>"
             "<li>파일의 워터마크·표기 제거 또는 변경</li></ul></li>"
             "<li>위원회가 무료로 공개한 자료는 출처를 밝히는 조건으로 누구나 인용·활용할 수 있습니다. "
             "다만 원문을 변형하여 위원회의 견해인 것처럼 표시해서는 안 됩니다.</li>"
             "<li>제2항을 위반한 경우 위원회는 서비스 이용을 제한하고 이수를 취소할 수 있으며, 그로 인한 손해의 배상을 청구할 수 있습니다.</li></ol>"),
            ("제12조 (이용자의 의무)",
             "<p>이용자는 다음 행위를 해서는 안 됩니다.</p>"
             "<ol><li>타인의 명의·이메일·연락처를 도용하는 행위</li>"
             "<li>계정을 타인에게 대여·양도·공유하는 행위</li>"
             "<li>학습자료 또는 평가 문항을 무단으로 복제·유출하는 행위</li>"
             "<li>자동화 프로그램 등으로 서비스에 비정상적인 부하를 발생시키는 행위</li>"
             "<li>위원회 또는 제3자의 명예를 훼손하거나 권리를 침해하는 행위</li>"
             "<li>위원회의 명칭, 로고, 이수증 서식을 무단으로 사용하거나 위원회와의 관계를 사실과 다르게 표시하는 행위</li></ol>"),
            ("제13조 (이수 취소 및 이용 제한)",
             "<ol><li>위원회는 제8조 제4항, 제11조 제2항, 제12조를 위반한 사실이 확인되면 사전 통지 후 이수를 취소하고 "
             "이수자 명부에서 말소할 수 있습니다. 긴급한 경우에는 先조치 후 통지할 수 있습니다.</li>"
             "<li>제1항에 따라 이수가 취소된 경우 이미 납부한 교육비는 환급되지 않습니다.</li>"
             "<li>이용자는 취소 통지를 받은 날부터 14일 이내에 위원회에 이의를 제기할 수 있으며, 위원회는 접수일부터 "
             "14일 이내에 검토 결과를 회신합니다.</li></ol>"),
            ("제14조 (청약철회와 환불)",
             "<p>청약철회와 환불에 관한 사항은 이 문서 아래의 <a href=\"#refund\">청약철회와 환불</a>에서 정한 바에 따릅니다.</p>"),
            ("제15조 (서비스의 변경과 중단)",
             "<ol><li>위원회는 교육과정의 구성, 학습자료의 내용, 평가 문항, 운영 일정을 개선 목적으로 변경할 수 있습니다. "
             "이미 결제한 수강자에게 불리한 변경이 있는 경우 사전에 통지합니다.</li>"
             "<li>시스템 점검, 설비 교체, 통신 장애, 천재지변 등 부득이한 사유가 있는 경우 서비스의 전부 또는 일부를 "
             "일시 중단할 수 있으며, 이 경우 사전에 공지합니다. 예측할 수 없는 사유인 경우에는 사후에 공지합니다.</li>"
             "<li>제2항에 따른 중단으로 응시 기간이 실질적으로 줄어든 경우 위원회는 그에 상응하는 기간을 연장합니다.</li></ol>"),
            ("제16조 (면책)",
             "<ol><li>위원회는 천재지변, 전시·사변, 정전, 기간통신사업자의 서비스 중단 등 불가항력으로 서비스를 제공할 수 "
             "없는 경우 책임을 지지 않습니다.</li>"
             "<li>위원회는 이용자의 귀책사유로 발생한 서비스 이용 장애에 대하여 책임을 지지 않습니다.</li>"
             "<li>위원회가 제공하는 교육·자료·자문은 일반적인 정보 제공을 목적으로 하며, 개별 사안에 대한 법률 자문이나 "
             "법적 판단을 대체하지 않습니다. 구체적인 사안은 변호사 등 전문가의 확인을 받으시기 바랍니다.</li>"
             "<li>위원회는 이수 사실이 이용자의 취업, 이직, 승진, 수주 등 특정한 결과로 이어질 것을 보장하지 않습니다.</li>"
             "<li>그 밖의 표기·인용·협력 관계에 관한 안내는 <a href=\"privacy.html#notice\">운영 및 표기에 관한 안내</a>를 참고하시기 바랍니다.</li></ol>"),
            ("제17조 (준거법과 분쟁의 해결)",
             "<ol><li>이 약관과 서비스 이용에 관하여는 대한민국 법령을 적용합니다.</li>"
             "<li>서비스 이용과 관련하여 분쟁이 발생한 경우 위원회와 이용자는 성실히 협의하여 해결하도록 노력합니다.</li>"
             "<li>협의로 해결되지 않는 경우 「민사소송법」에 따른 관할 법원에 소를 제기할 수 있습니다.</li></ol>"
             f"<p class=\"lg-note\">부칙 · 이 약관은 {LEGAL_DATE}부터 시행합니다.</p>"),
            '        <div class="lg-part" id="refund">청약철회와 환불</div>',
            ("가. 한눈에 보기",
             "<table class=\"lg-table\"><tbody>"
             "<tr><th>학습자료 발송 전</th><td>결제일부터 7일 이내 청약철회 가능 · 전액 환불</td></tr>"
             "<tr><th>학습자료 발송 개시 후</th><td><strong>청약철회 제한</strong> (「전자상거래 등에서의 소비자보호에 관한 법률」 제17조 제2항 제5호)</td></tr>"
             "<tr><th>이수 평가 응시 후</th><td>청약철회 불가</td></tr>"
             "<tr><th>미이수 · 미응시 · 기간 경과</th><td>환불 사유에 해당하지 않음</td></tr>"
             "</tbody></table>"),
            ("나. 청약철회가 가능한 경우",
             "<p>결제를 완료했으나 <strong>아직 학습자료가 발송되지 않은 상태</strong>라면, 결제일부터 7일 이내에 청약철회를 "
             "요청하실 수 있습니다. 이 경우 결제 수단과 동일한 방법으로 전액 환불해 드립니다.</p>"
             "<p>학습자료는 결제 확인 후 순차적으로 발송되므로, 철회를 원하시면 가능한 한 빨리 요청해 주시기 바랍니다.</p>"),
            ("다. 청약철회가 제한되는 경우",
             "<p>AI윤리전문가 양성과정의 학습자료는 「콘텐츠산업 진흥법」상 디지털콘텐츠에 해당합니다. "
             "「전자상거래 등에서의 소비자보호에 관한 법률」 제17조 제2항 제5호는 <strong>디지털콘텐츠의 제공이 개시된 경우</strong> "
             "청약철회를 제한할 수 있도록 정하고 있습니다.</p>"
             "<p>따라서 다음의 경우에는 청약철회와 환불이 제한됩니다.</p>"
             "<ol><li>신청 시 기재한 이메일로 학습자료(PDF) 내려받기 링크가 발송된 경우</li>"
             "<li>이수 평가 시스템에 로그인하여 응시를 시작한 경우</li>"
             "<li>학습자료의 전부 또는 일부를 내려받은 경우</li></ol>"
             "<p class=\"lg-note\">위원회는 결제 안내 화면과 이 문서에 청약철회 제한 사실을 사전에 명확히 "
             "고지하고 있으며, 표준교재의 구성과 쪽수, 실제 평가와 같은 형식의 샘플 문항을 결제 전에 공개하고 있습니다.</p>"),
            ("라. 법령으로 보장되는 예외",
             "<p>청약철회가 제한되는 경우에도, 다음에 해당하면 법령에 따라 청약철회를 요청하실 수 있습니다.</p>"
             "<ol><li>제공된 학습자료가 표시·광고 내용과 다르거나 계약 내용과 다르게 이행된 경우: 그 사실을 안 날 또는 "
             "알 수 있었던 날부터 30일 이내, 공급받은 날부터 3개월 이내</li>"
             "<li>위원회의 귀책사유로 학습자료가 제공되지 않거나 이수 평가를 응시할 수 없게 된 경우</li></ol>"
             "<p>이 경우 위원회는 사실관계를 확인한 뒤 전액 또는 이행되지 않은 부분에 해당하는 금액을 환불합니다.</p>"),
            ("마. 환불 사유에 해당하지 않는 경우",
             "<p>다음은 환불 사유에 해당하지 않습니다.</p>"
             "<ol><li>이수 평가에서 이수 기준에 도달하지 못한 경우. 응시 기간 안에서는 추가 비용 없이 다시 응시하실 수 있습니다.</li>"
             "<li>응시 기간 안에 응시하지 않아 기간이 지난 경우</li>"
             "<li>학습자료를 수령한 뒤의 단순 변심, 개인 일정 변경, 학습 시간 부족</li>"
             "<li>학습자료의 내용이 기대와 다르다는 주관적 판단. 다만 제3항 제1호에 해당하는 경우는 예외입니다.</li>"
             "<li>이용자의 이메일 오기재로 학습자료를 받지 못한 경우. 이 경우 위원회는 정정된 주소로 재발송해 드립니다.</li>"
             "<li>이용약관 위반으로 이수가 취소되거나 이용이 제한된 경우</li></ol>"),
            ("바. 신청과 처리 절차",
             f"<ol><li>청약철회를 원하시는 분은 위원회 공식 메일(<a href=\"mailto:{EMAIL}\">{EMAIL}</a>)로 "
             "성명, 결제에 사용한 이메일, 결제일, 요청 사유를 보내 주시기 바랍니다.</li>"
             "<li>위원회는 접수일부터 3영업일 이내에 처리 가능 여부를 회신합니다.</li>"
             f"<li>환불이 확정된 경우 결제는 {PAY_AGENT}를 통해 이루어졌으므로, 위원회의 확인 통보 후 "
             "해당 결제 수단으로 환급됩니다. 카드 결제의 경우 카드사 정산 일정에 따라 대금 청구가 취소되기까지 "
             "영업일 기준 3~5일이 더 걸릴 수 있습니다.</li></ol>"),
            ("사. 결제와 판매자 정보",
             f"<p>교육비 결제와 환급 처리는 위원회의 교육 운영사인 {PAY_AGENT}"
             f"(<a href=\"{PAY_AGENT_URL}\" target=\"_blank\" rel=\"noopener\">{PAY_AGENT_URL}</a>)가 수행합니다. "
             "통신판매업 신고 번호를 포함한 판매자 정보와 결제 수단별 약관은 해당 사이트 하단에서 확인하실 수 있습니다. "
             "교육과정의 운영, 이수 평가, 이수증 발급과 이수자 등록은 위원회가 직접 수행합니다.</p>"),
            ("아. 분쟁의 해결",
             "<p>환불과 관련하여 위원회와 이용자 사이에 분쟁이 발생한 경우, 양측은 성실히 협의하여 해결하도록 노력합니다. "
             "협의가 이루어지지 않는 경우 이용자는 공정거래위원회 또는 시·도지사에게 피해구제를 신청하거나 "
             "한국소비자원 소비자상담센터(국번 없이 1372)의 도움을 받으실 수 있습니다.</p>"
             f"<p class=\"lg-note\">이 부분은 {LEGAL_DATE}부터 적용되며, 이용약관과 함께 하나의 계약 내용을 이룹니다.</p>"),
        ],
        "한국AI윤리위원회 kaiec.kr 서비스 이용안내. AI윤리전문가 양성과정의 신청과 결제, 학습자료 제공, 이수 평가, "
        "이수증 발급과 이수자 등록, 지식재산권, 청약철회와 환불, 면책과 분쟁 해결에 관한 조건을 안내합니다.")

    # -------------------------------------------------- 개인정보 · 운영정책
    legal_page(
        "privacy.html", "개인정보·운영정책", "개인정보·운영정책",
        "한국AI윤리위원회가 이용자의 개인정보를 어떤 목적으로 어떻게 처리하는지, 그리고 홈페이지에 사용된 표현과 "
        "표기가 각각 어떤 의미인지 안내합니다.",
        [
            '        <div class="lg-part" id="privacy" style="margin-top:0;padding-top:0;border-top:0">개인정보처리방침</div>',
            ("1. 수집하는 개인정보의 항목과 방법",
             "<table class=\"lg-table\"><thead><tr><th>구분</th><th>수집 항목</th></tr></thead><tbody>"
             "<tr><th>양성과정 신청</th><td>성명, 이메일, 직업·활동 분야, 신청 과정, 활용 목적</td></tr>"
             "<tr><th>이수 평가 응시</th><td>성명, 이메일(로그인 아이디), 휴대전화 번호 뒤 4자리(초기 비밀번호), 응시 기록, 답안, 점수</td></tr>"
             "<tr><th>위원 참여 신청</th><td>성명, 이메일, 휴대전화(선택), 직업·활동 분야, 소속(선택), 참여 구분, 지원 동기, 자기소개</td></tr>"
             "<tr><th>사회공헌 활동 문의</th><td>기관·단체명, 담당자 성명, 연락처, 문의 내용</td></tr>"
             "<tr><th>출강 문의</th><td>기관명, 담당자 성명, 연락처, 교육 희망 내용</td></tr>"
             "<tr><th>자동 생성 정보</th><td>접속 일시, 서비스 이용 기록(이수 평가 시스템 이용 시)</td></tr>"
             "</tbody></table>"
             "<p>개인정보는 홈페이지의 신청·문의 양식을 통해 이용자가 직접 입력하는 방법으로만 수집합니다. "
             "위원회는 사상, 신념, 노동조합 가입, 정치적 견해, 건강, 성생활에 관한 정보 등 민감정보와 "
             "주민등록번호를 수집하지 않습니다.</p>"),
            ("2. 개인정보의 처리 목적",
             "<ol><li>양성과정 신청자 확인, 학습자료 발송, 교육 운영에 관한 안내</li>"
             "<li>이수 평가 계정 생성과 본인 확인, 응시 관리, 채점과 결과 안내</li>"
             "<li>이수증 발급, 이수자 명부 등록, 기관의 요청이 있을 때 이수 사실 확인 회신</li>"
             "<li>전문위원 등록 심사와 홈페이지 프로필 공개(이용자가 희망한 경우에 한함)</li>"
             "<li>참여 신청 검토, 위촉과 활동 안내</li>"
             "<li>협력·출강 문의에 대한 회신과 협의</li>"
             "<li>민원 처리와 분쟁 대응</li></ol>"),
            ("3. 개인정보의 보유 및 이용 기간",
             "<table class=\"lg-table\"><thead><tr><th>구분</th><th>보유 기간</th></tr></thead><tbody>"
             "<tr><th>양성과정 신청 정보</th><td>수집일부터 3년</td></tr>"
             "<tr><th>이수자 명부(성명, 이메일, 과정, 이수번호, 이수일)</th><td>이수 사실 확인 업무를 위해 보관. 이용자가 삭제를 요청하면 즉시 파기</td></tr>"
             "<tr><th>이수 평가 응시 기록과 답안</th><td>수집일부터 3년</td></tr>"
             "<tr><th>참여 신청 정보</th><td>수집일부터 3년. 활동 종료 또는 삭제 요청 시 즉시 파기</td></tr>"
             "<tr><th>협력 · 출강 문의</th><td>회신 완료일부터 1년</td></tr>"
             "</tbody></table>"
             "<p>다만 관계 법령에 따라 보존할 필요가 있는 경우에는 해당 법령이 정한 기간 동안 보관합니다. "
             "이수자가 이수 사실 확인을 원하지 않아 명부에서 삭제를 요청하는 경우, 삭제 이후에는 위원회가 "
             "제3자의 확인 요청에 회신할 수 없습니다.</p>"),
            ("4. 개인정보의 제3자 제공",
             "<p>위원회는 이용자의 개인정보를 제3자에게 제공하지 않습니다. 다만 다음의 경우는 예외로 합니다.</p>"
             "<ol><li>이용자가 사전에 동의한 경우</li>"
             "<li>기관·기업이 이수 사실의 진위 확인을 요청하고 이용자가 이를 동의한 경우. 이 경우 제공되는 정보는 "
             "성명, 이수 과정, 이수번호, 이수일로 한정합니다.</li>"
             "<li>법령에 특별한 규정이 있거나 수사기관이 법령이 정한 절차와 방법에 따라 요구한 경우</li></ol>"),
            ("5. 개인정보 처리의 위탁과 국외 이전",
             "<p>위원회는 서비스 운영을 위해 아래와 같이 개인정보 처리 업무를 위탁하고 있으며, 위탁 업무의 내용과 "
             "수탁자가 변경되는 경우 이 방침을 통해 공개합니다.</p>"
             "<table class=\"lg-table\"><thead><tr><th>수탁자</th><th>위탁 업무</th><th>이전 국가 · 시점 · 방법</th></tr></thead><tbody>"
             "<tr><th>Google LLC</th><td>신청·문의 내용의 저장(Google 스프레드시트), 자동 알림 메일 발송(Google Apps Script), "
             "이수 평가 시스템의 데이터 저장</td><td>미국 · 이용자가 양식을 제출하는 시점에 네트워크를 통해 전송</td></tr>"
             f"<tr><th>{PAY_AGENT}</th><td>교육비 결제와 환급 처리</td><td>국내</td></tr>"
             "</tbody></table>"
             "<p>Google LLC 로 이전되는 항목은 제1항에서 정한 수집 항목과 같으며, 보유 기간은 제3항과 같습니다. "
             "이용자는 개인정보의 국외 이전을 거부할 수 있으나, 이 경우 온라인 신청과 이수 평가 응시가 제한될 수 있습니다. "
             "거부를 원하시는 분은 위원회 공식 메일로 연락해 주시면 대체 방법을 안내해 드립니다.</p>"),
            ("6. 개인정보의 파기",
             "<ol><li>보유 기간이 지나거나 처리 목적이 달성된 개인정보는 지체 없이 파기합니다.</li>"
             "<li>전자적 파일은 복구할 수 없는 방법으로 영구 삭제하고, 출력물은 분쇄하거나 소각합니다.</li></ol>"),
            ("7. 정보주체의 권리와 행사 방법",
             "<ol><li>이용자는 언제든지 자신의 개인정보에 대한 열람, 정정, 삭제, 처리 정지를 요구할 수 있습니다.</li>"
             f"<li>권리 행사는 위원회 공식 메일(<a href=\"mailto:{EMAIL}\">{EMAIL}</a>)로 요청하실 수 있으며, "
             "위원회는 접수일부터 10일 이내에 조치하고 결과를 회신합니다.</li>"
             "<li>이용자는 개인정보 수집·이용에 대한 동의를 거부할 권리가 있습니다. 다만 필수 항목의 동의를 거부하는 "
             "경우 양성과정 신청, 이수 평가 응시 등 해당 서비스의 이용이 제한됩니다.</li>"
             "<li>만 14세 미만 아동의 개인정보는 수집하지 않습니다.</li></ol>"),
            ("8. 개인정보의 안전성 확보 조치",
             "<ol><li>개인정보 처리 담당자를 최소한으로 지정하고 접근 권한을 관리합니다.</li>"
             "<li>이수 평가 시스템의 비밀번호는 이용자가 직접 변경할 수 있으며, 초기 비밀번호를 계속 사용하지 않도록 안내합니다.</li>"
             "<li>개인정보가 저장된 문서와 파일에 대한 접근을 통제하고, 전송 구간은 암호화(HTTPS)합니다.</li>"
             "<li>개인정보 처리 시스템의 접속 기록을 보관합니다.</li></ol>"),
            ("9. 자동 수집 장치의 운영",
             "<p>위원회 홈페이지는 광고 목적의 추적 기술을 사용하지 않습니다. 이수 평가 시스템은 응시 상태 유지를 위해 "
             "이용자의 브라우저 저장 공간(sessionStorage, localStorage)에 로그인 토큰과 임시 답안을 보관하며, "
             "이 정보는 이용자의 기기에만 저장되고 브라우저를 닫거나 로그아웃하면 삭제됩니다. "
             "추후 방문 분석 도구를 도입하는 경우 이 방침을 개정하여 사전에 공개합니다.</p>"),
            ("10. 개인정보 보호책임자",
             f"<table class=\"lg-table\"><tbody>"
             f"<tr><th>개인정보 보호책임자</th><td>{PRIVACY_OFFICER}</td></tr>"
             f"<tr><th>연락처</th><td><a href=\"mailto:{EMAIL}\">{EMAIL}</a></td></tr>"
             "</tbody></table>"
             "<p>개인정보 처리와 관련한 문의, 불만 처리, 피해 구제는 위 연락처로 요청해 주시기 바랍니다.</p>"),
            ("11. 권익침해 구제 방법",
             "<p>개인정보 침해로 상담이나 분쟁 조정이 필요한 경우 아래 기관에 도움을 요청하실 수 있습니다.</p>"
             "<ol><li>개인정보 침해신고센터 (국번 없이 118, privacy.kisa.or.kr)</li>"
             "<li>개인정보 분쟁조정위원회 (1833-6972, kopico.go.kr)</li>"
             "<li>대검찰청 사이버수사과 (국번 없이 1301)</li>"
             "<li>경찰청 사이버수사국 (국번 없이 182)</li></ol>"),
            ("12. 방침의 변경",
             f"<p>이 개인정보처리방침은 {LEGAL_DATE}부터 적용됩니다. 법령이나 서비스의 변경에 따라 내용이 바뀌는 경우 "
             "변경 사항을 시행 7일 전부터 홈페이지에 공지합니다. 이용자에게 중대한 영향을 미치는 변경의 경우에는 "
             "30일 전부터 공지합니다.</p>"),
            '        <div class="lg-part" id="notice">운영 및 표기에 관한 안내</div>',
            ("가. 위원회의 법적 지위",
             "<p>한국AI윤리위원회는 AI 윤리 분야의 교육·연구·캠페인 활동을 수행하는 전문기관입니다. "
             "<strong>정부기관이나 공공기관이 아니며, 정부로부터 위탁받은 인증·검정 업무를 수행하지 않습니다.</strong> "
             "홈페이지에서 사용하는 “공식”이라는 표현은 위원회 자체가 발급·운영·인정한다는 뜻이며, "
             "국가나 공공기관의 인정을 의미하지 않습니다.</p>"),
            ("나. 이수증과 등록의 성격",
             "<ol><li>이수증은 위원회가 운영하는 교육과정을 이수했다는 사실을 확인하는 문서이며, "
             "국가가 신설하거나 공인한 제도가 아닙니다.</li>"
             "<li>이수자 명부 등록과 전문위원 등록은 위원회 내부의 등록 절차이며, 법령에 근거한 등록·신고·면허가 아닙니다.</li>"
             "<li>이수 사실은 교육 이력으로 활용할 수 있으나, 특정한 취업·이직·승진·채용·수주 등의 결과를 보장하지 않습니다. "
             "홈페이지의 커리어 관련 설명은 일반적인 시장 동향에 대한 견해이며 개인의 성과를 약속하는 것이 아닙니다.</li></ol>"),
            ("다. 인용한 통계와 전망치",
             "<p>홈페이지에 인용된 시장 규모, 성장률, 제도 시행 일정 등은 해당 자료를 발표한 기관의 공개 자료를 인용한 "
             "것이며, 위원회가 독자적으로 조사하거나 그 정확성을 보증하는 수치가 아닙니다. 출처는 해당 문장 옆에 "
             "표기하고 있습니다. 시장 전망치는 예측이며 실제와 다를 수 있고, 법령과 제도의 시행 일정은 이후 개정으로 "
             "변경될 수 있으므로 의사결정에 활용하실 때에는 원문과 최신 개정 사항을 직접 확인해 주시기 바랍니다.</p>"),
            ("라. 소재지 표기에 관한 안내",
             "<p>홈페이지 하단에 표기된 연구실 주소는 위원회의 연구·행정 공간이 위치한 장소를 나타내는 소재지 표기입니다. "
             "<strong>해당 건물이 소재한 대학과의 제휴, 후원, 인증, 공동 운영 관계를 의미하지 않으며, "
             "해당 대학이 위원회의 교육과정이나 이수증을 인정한다는 뜻도 아닙니다.</strong></p>"),
            ("마. 협력 기관과 제휴 서비스 표기",
             "<ol><li>홈페이지에 표기된 협력 기관·회원기관은 위원회의 활동에 협력하거나 회원으로 참여하는 기관을 뜻하며, "
             "해당 기관이 위원회의 교육과정, 이수증, 평가를 인증하거나 보증한다는 의미가 아닙니다.</li>"
             f"<li>{PAY_AGENT}는 위원회의 교육 운영과 결제를 담당하는 협력사입니다. 교육비 결제, 영수증 발행, "
             "환급 처리는 해당 사에서 이루어집니다.</li>"
             "<li>카피클린(CopyClean)은 위원회의 제휴 서비스이며 위원회의 소속 조직이나 자체 서비스가 아닙니다. "
             "해당 서비스의 이용 조건, 검사 결과, 요금은 서비스 제공자가 정하며 위원회는 그 정확성이나 결과에 대하여 "
             "책임을 지지 않습니다.</li>"
             "<li>기관명, 로고, 사업명은 각 권리자에게 귀속되며, 위원회는 사실 관계를 안내하기 위한 범위에서만 표기합니다. "
             "표기와 관련하여 정정이 필요하다고 판단되는 기관은 위원회 공식 메일로 알려 주시면 확인 후 신속히 조치하겠습니다.</li></ol>"),
            ("바. 사회공헌 활동과 무료 교육",
             "<p>어르신 AI 활용 교육, 초등학생 AI 윤리 교육 등 위원회의 무료 교육은 위원들이 보수를 받지 않고 참여하는 "
             "재능기부로 운영됩니다. 따라서 신청하신다고 해서 반드시 배정되는 것은 아니며, 위원의 일정, 강사 배정 가능 "
             "여부, 지역, 신청 순서에 따라 일정이 조정되거나 진행이 어려울 수 있습니다. 위원회는 신청을 접수한 뒤 "
             "가능 여부를 개별적으로 회신합니다.</p>"),
            ("사. 교육과 자문 내용의 성격",
             "<p>위원회가 제공하는 교육, 자료, 자문, 체크리스트, 진단 결과는 AI 윤리에 대한 일반적인 정보 제공과 "
             "교육을 목적으로 합니다. <strong>개별 사안에 대한 법률 자문, 법적 판단, 규제 준수 여부에 대한 확인을 "
             "대체하지 않습니다.</strong> 구체적인 사안은 변호사 등 해당 분야 전문가의 확인을 받으시기 바랍니다. "
             "위원회는 이용자가 제공된 정보를 근거로 내린 판단과 그 결과에 대하여 책임을 지지 않습니다.</p>"),
            ("아. 자가진단과 공개 자료",
             "<p>홈페이지에서 제공하는 자가진단은 학습 동기를 돕기 위한 참고용 도구이며, 개인의 역량이나 적성을 "
             "평가하는 검사 도구가 아닙니다. 결과는 어떠한 공식적인 효력도 갖지 않습니다. 무료로 공개한 자료는 "
             "출처를 밝히는 조건으로 누구나 활용하실 수 있으나, 활용 결과에 대해서는 위원회가 책임을 지지 않습니다.</p>"),
            ("자. 외부 링크",
             "<p>홈페이지에는 외부 사이트로 연결되는 링크가 포함될 수 있습니다. 위원회는 연결된 사이트의 내용, "
             "서비스, 개인정보 처리에 대하여 관리 권한이 없으며 책임을 지지 않습니다.</p>"),
            ("차. 게시 정보의 변경",
             "<p>교육과정의 구성, 금액, 모집 일정, 제공 자료, 평가 기준 등 홈페이지에 게시된 정보는 운영 사정에 따라 "
             "변경될 수 있습니다. 이미 결제를 완료한 수강자에게 불리한 변경이 있는 경우에는 사전에 개별 통지합니다. "
             "게시된 정보와 실제 운영이 다른 부분을 발견하신 경우 위원회 공식 메일로 알려 주시면 확인 후 정정하겠습니다.</p>"
             f"<p class=\"lg-note\">이 안내는 {LEGAL_DATE}부터 적용되며, 서비스 이용안내와 함께 하나의 안내 체계를 이룹니다.</p>"),
        ],
        "한국AI윤리위원회 개인정보·운영정책. 개인정보 수집 항목과 처리 목적, 보유 기간, 위탁과 국외 이전, 정보주체의 "
        "권리 행사 방법과 함께, 위원회의 법적 지위와 표기·인용·협력 관계에 관한 안내를 담고 있습니다.")


# --------------------------------------------------------- sitemap.xml / rss
def build_sitemap(posts):
    today = datetime.date.today().strftime("%Y-%m-%d")
    core = [("", "1.0", "weekly"), ("about.html", "0.9", "monthly"), ("business.html", "0.9", "monthly"),
            ("members.html", "0.8", "monthly"), ("lecture.html", "0.9", "monthly"),
            ("expert.html", "0.9", "monthly"), ("expert-apply.html", "0.8", "monthly"),
            ("experts.html", "0.9", "monthly"), ("join.html", "0.9", "monthly"), ("quiz.html", "0.7", "monthly"), ("exam.html", "0.7", "monthly"),
            ("partner.html", "0.9", "monthly"), ("copyclean.html", "0.8", "monthly"),
            ("news.html", "0.8", "daily"), ("mou.html", "0.8", "monthly"), ("apply.html", "0.9", "monthly"),
            ("terms.html", "0.3", "yearly"), ("privacy.html", "0.3", "yearly")]
    urls = []
    for path, pri, freq in core:
        loc = f"{SITE_URL}{url_for(path)}" if path else f"{SITE_URL}/"
        urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n"
                    f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>")
    for p in posts:
        # 게시글 본문이 아니라 공통 틀(기관명 등)이 바뀐 날짜도 반영: 발행일과 POSTS_LASTMOD 중 늦은 날짜
        lastmod = max(p['dt'].strftime('%Y-%m-%d'), POSTS_LASTMOD)
        urls.append(f"  <url>\n    <loc>{SITE_URL}{url_for(p['file'])}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
                    f"    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    io.open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    print("  ✓ sitemap.xml (게시글 포함 자동 생성)")


def build_rss(posts):
    items = []
    for p in posts[:20]:
        pub = p["dt"].strftime("%a, %d %b %Y 09:00:00 +0900")
        desc = _html.escape(p["summary"])
        items.append(f"""    <item>
      <title>{_html.escape(p["title"])}</title>
      <link>{SITE_URL}{url_for(p["file"])}</link>
      <guid>{SITE_URL}{url_for(p["file"])}</guid>
      <pubDate>{pub}</pubDate>
      <category>{_html.escape(p["category"])}</category>
      <description>{desc}</description>
    </item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_NAME} 소식</title>
    <link>{SITE_URL}</link>
    <description>한국AI윤리위원회의 캠페인, 활동 소식, AI 윤리 이슈</description>
    <language>ko</language>
{chr(10).join(items)}
  </channel>
</rss>
"""
    io.open(os.path.join(BASE, "rss.xml"), "w", encoding="utf-8").write(rss)
    print("  ✓ rss.xml (네이버 서치어드바이저 RSS 제출용)")


# ------------------------------------------------------------------ mou.html
def build_mou():
    # 사회공헌·협력 (2026.09.16): 대가 없이 여는 무료 교육을 맨 앞에 두고, 신청 항목을 직접 고르게 한 뒤
    # 마지막 선택지로 기관 협력·업무협약(MOU)·사회공헌 파트너십까지 한 양식에서 접수합니다.
    VOLUNTEER = [
        ("users-round", "어르신 AI 활용 교육", "voAged", "어르신 AI 활용 교육 (무료)",
         "경로당 · 복지관 · 평생학습관 · 주민센터",
         "스마트폰 AI 비서로 길 찾기와 번역하기, 사진 정리처럼 생활에 바로 쓰는 것부터 시작합니다. "
         "AI가 만든 가짜 사진과 목소리를 알아보는 법, 보이스피싱과 허위 정보에 속지 않는 법을 함께 익힙니다.",
         ["1회 60~90분", "10명 이상", "강사비 · 교재비 없음"]),
        ("school", "초등학생 AI 윤리 교육", "voKid", "초등학생 AI 윤리 교육 (무료)",
         "초등학교 · 지역아동센터 · 작은도서관",
         "AI에게 숙제를 통째로 맡기는 것과 도움을 받는 것이 어떻게 다른지 이야기로 풀어 줍니다. "
         "AI를 썼으면 밝히기, 답을 그대로 믿지 않고 한 번 확인하기. 두 가지 습관을 놀이처럼 익히도록 구성했습니다.",
         ["1회 40~80분", "학급 단위 가능", "강사비 · 교재비 없음"]),
    ]
    vol_html = "".join(f"""
          <article class="vol reveal">
            <span class="vol-free">KAIEC 재능기부</span>
            <div class="vol-ic"><i data-lucide="{ic}"></i></div>
            <h3>{t}</h3>
            <p class="vol-who"><i data-lucide="map-pin"></i>{who}</p>
            <p class="vol-d">{d}</p>
            <div class="chips">{"".join(f'<span class="chip">{c}</span>' for c in chips)}</div>
            <button type="button" class="btn btn-primary vol-btn" data-pick="{val}">
              {t} 신청하기 <i data-lucide="arrow-right"></i></button>
          </article>""" for ic, t, _id, val, who, d, chips in VOLUNTEER)

    GIVING = [
        ("megaphone", "AI 윤리 캠페인", "누구나 참여",
         "무분별한 AI 사용을 줄이자는 온라인 캠페인을 상시 운영합니다. 카드뉴스와 영상, 실천 수칙을 만들어 배포하고, AI 윤리위원이 함께 알립니다."),
        ("book-open", "공익 콘텐츠 무료 공개", "전면 무료",
         "AI 활용 원칙과 분야별 체크리스트, 국내외 동향 정리를 홈페이지에 모두 무료로 공개합니다. 회원 가입이나 결제 없이 누구나 보고 활용할 수 있습니다."),
        ("users", "AI 윤리위원 운영", "전공·경력 무관",
         "전공과 경력에 관계없이 누구나 AI 윤리위원으로 참여해 캠페인과 콘텐츠 제작에 함께할 수 있도록 열어 두었습니다. 참여에 드는 비용은 없습니다."),
        ("file-search", "제출 전 사전점검 문화 확산", "분쟁 예방",
         "논문·과제·보고서를 제출하기 전에 스스로 점검하는 문화를 알립니다. 적발과 제재가 아니라 오해와 분쟁을 미리 막자는 것이 위원회의 입장입니다."),
    ]
    giving_html = "".join(f"""
          <article class="card reveal">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px">
              <div class="card-icon" style="margin-bottom:0"><i data-lucide="{ic}"></i></div>
              <span class="badge badge--teal">{tag}</span>
            </div>
            <h3>{t}</h3><p>{d}</p>
          </article>""" for ic, t, tag, d in GIVING)

    # 신청·문의 항목: 무료 봉사 활동을 앞에, 기관 협력·MOU를 뒤에 둡니다
    PICKS = [
        ("어르신 AI 활용 교육 (무료)", "KAIEC 재능기부", "어르신 AI 활용 교육",
         "경로당·복지관·평생학습관·주민센터로 강사가 찾아갑니다. 강사비와 교재비는 받지 않습니다."),
        ("초등학생 AI 윤리 교육 (무료)", "KAIEC 재능기부", "초등학생 AI 윤리 교육",
         "초등학교·지역아동센터·작은도서관으로 찾아갑니다. 학급 단위로도 진행할 수 있습니다."),
        ("그 밖의 교육기부 요청 (무료)", "KAIEC 재능기부", "그 밖의 교육기부",
         "중·고등학교, 대학, 비영리기관의 AI 윤리 교육 요청입니다. 대상과 인원에 맞춰 내용을 다시 짭니다."),
        ("AI 윤리 캠페인 함께하기", "공익 활동", "AI 윤리 캠페인 함께하기",
         "무분별한 AI 사용을 줄이자는 캠페인에 기관이나 단체로 함께합니다. 공동 카드뉴스·영상·실천 수칙 배포."),
        ("공익 활동 · 공개 콘텐츠 제안", "공익 활동", "공익 활동 · 공개 콘텐츠 제안",
         "함께 만들고 싶은 공익 자료나 행사가 있다면 제안해 주세요. 결과물은 누구나 볼 수 있게 무료로 공개합니다."),
        ("기관 협력 · 업무협약(MOU)", "기관 협력", "기관 협력 · 업무협약(MOU)",
         "대학·기업·공공기관과의 공동 사업, 연구 협력, 업무협약(MOU) 체결을 논의합니다."),
        ("사회공헌 파트너십", "기관 협력", "사회공헌 파트너십",
         "기업의 사회공헌(CSR) 사업으로 위원회의 무료 교육과 캠페인을 함께 후원하거나 운영합니다."),
        ("회원기관 가입 문의", "회원기관", "회원기관 가입 문의",
         "위원회 회원기관으로 이름을 올리고 교육·자문·캠페인에 상시로 함께합니다. 혜택과 연회비는 담당자가 안내드립니다."),
    ]
    picks_html = "".join(f"""
              <label class="choice choice--role">
                <input type="radio" name="분야" value="{val}">
                <span class="choice-radio"></span>
                <span class="choice-body">
                  <span class="choice-badge">{badge}</span>
                  <strong>{title}</strong>
                  <span>{desc}</span>
                </span>
              </label>""" for val, badge, title, desc in PICKS)

    body = hero_sub("사회공헌",
                    "한국AI윤리위원회 전문위원과 AI 윤리위원이 직접 현장으로 갑니다. "
                    "어르신과 어린이를 위한 AI 교육을 대가 없이 열고, 캠페인과 공익 자료도 모두 무료로 공개합니다.",
                    "사회공헌") + f"""

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Free Education</span>
          <h2 class="h-sec">위원회가 직접 찾아가는 무료 교육</h2>
          <p class="h-sub">한국AI윤리위원회 <strong>위원회 전문위원과 AI 윤리위원이 직접 나가는 기관 재능기부</strong>입니다.
             신청 기관은 장소와 인원만 준비해 주시면 되고, 강사비와 교재비는 받지 않습니다.</p>
        </div>
        <div class="vol-grid">
{vol_html}
        </div>
        <div class="notice notice--teal" style="margin-top:26px">
          <strong>왜 무료인가요.</strong> AI를 가장 먼저 배워야 할 분들이 오히려 배울 곳이 가장 적습니다.
          위원회는 이 두 교육을 수익 사업이 아니라 위원들이 함께 나서는 공익 활동으로 봅니다.
          그 밖의 학교·비영리기관 교육 요청도 아래 <a href="#inquiry">신청 양식</a>에서 함께 받습니다.
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">Our Volunteers</span>
          <h2 class="h-sec">누가 직접 찾아가나요</h2>
          <p class="h-sub">외부 강사를 부르지 않습니다. 위원회에 등록된 <strong>전문위원과 AI 윤리위원</strong>이
             현장으로 갑니다. 모두 보수를 받지 않고 봉사로 참여하며, 지역 조직은 순차적으로 넓혀 가고 있습니다.</p>
        </div>
        <div class="grid grid-4">
          <article class="card reveal"><div class="card-icon"><i data-lucide="user-check"></i></div>
            <h3>전문위원</h3><p>AI윤리전문가 양성과정을 이수하고 위원회에 등록된 전문위원이 교안을 맡습니다</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="map-pin"></i></div>
            <h3>지역 운영위원</h3><p>권역별로 위촉되는 대로 가까운 경로당·복지관·학교를 맡습니다(현재 순차 위촉 중)</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="school"></i></div>
            <h3>캠퍼스 위원장</h3><p>대학의 캠퍼스 위원회가 지역 아동·청소년 교육에 함께 나섭니다</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="megaphone"></i></div>
            <h3>AI 윤리 캠페인위원</h3><p>전공과 경력에 관계없이 참여한 캠페인위원이 현장 진행과 자료 배포를 돕습니다</p></article>
        </div>
        <div class="notice notice--teal" style="margin-top:26px">
          <strong>강사비가 없는 이유는 간단합니다.</strong> 위원들이 봉사로 나서기 때문입니다.
          함께 나서고 싶으시다면 전공과 경력에 관계없이 <a href="join.html">위원 참여하기</a>에서
          AI 윤리위원으로 신청하실 수 있습니다. 참여에 드는 비용은 없습니다.
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Social Contribution</span>
          <h2 class="h-sec">위원회가 늘 해 오는 일</h2>
          <p class="h-sub">교육 말고도 <strong>AI 윤리를 알리는 일</strong>은 모두 공익 활동으로 봅니다.
             캠페인과 공개 자료는 대가 없이 운영합니다.</p>
        </div>
        <div class="grid grid-4">
{giving_html}
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Partnership</span>
          <h2 class="h-sec">기관과 함께할 수 있는 일</h2>
          <p class="h-sub">기관의 상황과 필요에 맞춰 협력 형태를 함께 설계합니다. 공익 목적의 협력은 대가 없이 진행합니다.</p>
        </div>
        <div class="grid grid-4">
          <article class="card reveal"><div class="card-icon"><i data-lucide="graduation-cap"></i></div>
            <h3>대학 · 학교</h3><p>학생 대상 AI 윤리 교육기부, 공동 캠페인, 제출 전 사전점검 문화 안내</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="building-2"></i></div>
            <h3>기업</h3><p>사회공헌(CSR) 파트너십, 임직원 AI 활용 가이드라인 자문, 사내 교육</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="heart-handshake"></i></div>
            <h3>공공 · 비영리</h3><p>어르신·아동 대상 무료 교육 공동 운영, 공동 캠페인과 세미나</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="flask-conical"></i></div>
            <h3>연구기관</h3><p>AI 윤리 연구 협력, 이슈 브리프 공동 발행, 업무협약(MOU)</p></article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Partners</span>
          <h2 class="h-sec">함께하는 기관</h2>
          <p class="h-sub">교육 운영과 공동 사업을 함께하는 기관입니다. 각 기관이 맡는 역할을 함께 적었습니다.</p>
        </div>
        <div class="pt-cards" id="partnerLogos"></div>
        <a class="pt-join reveal" href="#inquiry">
          <span class="pt-join-ic"><i data-lucide="handshake"></i></span>
          <span class="pt-join-body">
            <strong>함께하실 기관을 찾고 있습니다</strong>
            <span>대학 · 학교 · 기업 · 공공기관 · 비영리단체 모두 좋습니다. 연락 주시면 담당자가 협력 범위를 함께 정리해 드립니다.</span>
          </span>
          <span class="pt-join-go">협력 문의하기 <i data-lucide="arrow-right"></i></span>
        </a>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Process</span>
          <h2 class="h-sec">신청 후 진행 절차</h2>
        </div>
        <div class="grid grid-4">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">온라인 신청</h3><p style="font-size:14px">아래 양식에서 항목 선택</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">일정 협의</h3><p style="font-size:14px">담당자 회신 · 날짜와 인원 확정</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">강사 배정 · 협약</h3><p style="font-size:14px">교육은 강사 배정, 협력은 협약 체결</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">진행</h3><p style="font-size:14px">교육 · 캠페인 · 공동 활동</p></div>
        </div>
      </div>
    </section>

    <section class="section" id="inquiry">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Apply</span>
          <h2 class="h-sec">사회공헌 신청 · 문의</h2>
          <p class="h-sub" style="margin:0 auto">찾아가는 무료 교육 신청과 기관 협력 제안, 회원기관 가입 문의를 한 양식에서 받습니다.
             원하시는 항목을 고른 뒤 연락처만 남겨 주시면 담당자가 확인 후 회신드립니다.</p>
        </div>

        <form class="form" id="mouForm" action="#">
          <div class="field" id="pickBox">
            <label>어떤 일로 연락 주셨나요<span class="req">*</span></label>
            <div class="choice-list" style="margin-top:8px">
{picks_html}
            </div>
            <p class="field-hint" id="pickErr" hidden style="color:#B42318;font-weight:700">항목을 하나 선택해 주세요.</p>
            <p class="field-hint">위원회 <a href="apply.html#member" style="color:var(--blue);font-weight:700">회원기관 안내</a>와
              <a href="join.html" style="color:var(--blue);font-weight:700">AI 윤리위원 참여</a>도 함께 보실 수 있습니다.</p>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="org">기관·단체명<span class="req">*</span></label>
              <input type="text" id="org" name="기관명" required placeholder="예) ○○초등학교, ○○복지관">
            </div>
            <div class="field">
              <label for="name">담당자 성함<span class="req">*</span></label>
              <input type="text" id="name" name="담당자" required>
            </div>
          </div>
          <div class="field">
            <label for="contact">연락처<span class="req">*</span></label>
            <input type="text" id="contact" name="연락처" required placeholder="전화번호 또는 이메일">
            <p class="field-hint">회신받으실 연락처 하나만 남겨주시면 됩니다.</p>
          </div>
          <div class="field">
            <label for="plan">희망 일정 · 인원 (선택)</label>
            <input type="text" id="plan" name="일정인원" placeholder="예) 11월 중 평일 오전, 어르신 25명">
          </div>
          <div class="field">
            <label for="msg">남기실 말씀<span class="req">*</span></label>
            <textarea id="msg" name="문의내용" required placeholder="교육 장소와 대상, 또는 협력을 희망하시는 내용을 자유롭게 적어 주세요."></textarea>
          </div>
          <button type="submit" class="btn btn-primary" style="justify-self:start">
            신청 보내기 <i data-lucide="send"></i>
          </button>
          <p class="field-hint">
            버튼을 누르면 메일 앱이 열리고 작성 내용이 자동으로 담깁니다.
            직접 보내실 경우: <a href="mailto:{EMAIL}" style="color:var(--blue);font-weight:600">{EMAIL}</a>
          </p>
        </form>
      </div>
    </section>"""

    script = """  <script src="assets/js/partners-data.js"></script>
  <script>
  (function(){
    var box=document.getElementById('partnerLogos');
    if(!box||!window.KAIEC_PARTNERS)return;
    if(!window.KAIEC_PARTNERS.length){
      box.outerHTML='<p style="text-align:center;color:var(--gray-500);padding:40px 0">함께하실 기관을 기다리고 있습니다.</p>';return;
    }
    box.innerHTML=window.KAIEC_PARTNERS.map(function(p){
      var mark=p.logo
        ?'<span class="pt-mark pt-mark--img"><img src="assets/img/'+p.logo+'" alt="'+p.name+' 로고" loading="lazy"></span>'
        :'<span class="pt-mark">'+p.name.trim().charAt(0)+'</span>';
      var role=p.role?'<span class="pt-role">'+p.role+'</span>':'';
      var go=p.url?'<span class="pt-go">홈페이지 보기 <i data-lucide="arrow-right"></i></span>':'';
      var body='<article class="pt-card reveal">'+mark
        +'<span class="pt-name">'+p.name+'</span>'+role+go+'</article>';
      return p.url?'<a class="pt-link" href="'+p.url+'" target="_blank" rel="noopener">'+body+'</a>':body;
    }).join('');
  })();
  /* 무료 교육 카드의 신청 버튼: 아래 양식에서 해당 항목을 자동 선택하고 이동 */
  (function(){
    var f=document.getElementById('mouForm');
    if(!f)return;
    var err=document.getElementById('pickErr');
    function pick(v){
      var r=f.querySelector('input[name="분야"][value="'+v+'"]');
      if(r){r.checked=true; if(err)err.hidden=true;}
    }
    document.querySelectorAll('.vol-btn').forEach(function(b){
      b.addEventListener('click',function(){
        pick(b.getAttribute('data-pick'));
        var t=document.getElementById('inquiry');
        if(t)window.scrollTo({top:t.getBoundingClientRect().top+window.pageYOffset-80,behavior:'smooth'});
      });
    });
    f.querySelectorAll('input[name="분야"]').forEach(function(r){
      r.addEventListener('change',function(){ if(err)err.hidden=true; });
    });
    /* 해시로 들어온 경우(?pick=) 미리 선택 */
    var q=new URLSearchParams(location.search).get('pick');
    if(q)pick(q);
    f.addEventListener('submit',function(e){
      e.preventDefault();
      function v(n){var el=f.querySelector('[name="'+n+'"]');return el?el.value.trim():''}
      var sel=f.querySelector('input[name="분야"]:checked');
      if(!sel){
        if(err){err.hidden=false;}
        var box=document.getElementById('pickBox');
        if(box)window.scrollTo({top:box.getBoundingClientRect().top+window.pageYOffset-100,behavior:'smooth'});
        return;
      }
      var subject='[사회공헌] '+sel.value+' · '+v('기관명');
      var lines=[
        '■ 신청 항목   : '+sel.value,
        '■ 기관·단체명 : '+v('기관명'),
        '■ 담당자      : '+v('담당자'),
        '■ 연락처      : '+v('연락처'),
        '■ 희망 일정·인원 : '+(v('일정인원')||'미기재'),
        '',
        '■ 남기실 말씀',
        v('문의내용'),
        '',
        '--- 한국AI윤리위원회 홈페이지 사회공헌 신청 양식에서 작성됨 ---'
      ];
      location.href='mailto:__EMAIL__?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(lines.join('\\n'));
    });
  })();
  </script>
""".replace('__EMAIL__', EMAIL)
    page("mou.html", "사회공헌",
         "한국AI윤리위원회 전문위원과 전국 지역 AI 윤리위원이 직접 찾아가는 무료 교육 안내. 어르신 AI 활용 교육과 초등학생 AI 윤리 교육을 "
         "기관 재능기부로 지원하고, AI 윤리 캠페인·공익 콘텐츠·교육기부·기관 협력·업무협약(MOU)·사회공헌 파트너십·회원기관 가입 신청을 한 양식에서 받습니다.",
         body + cert_band("사회공헌 활동 신청하기", "#inquiry"), extra_script=script)


# -------------------------------------------------------------- lecture.html
def build_lecture():
    L_EMAIL = EMAIL                     # 출강 문의도 위원회 공식 메일로 통일 (2026.09.18)
    L_TEL = "010-9913-7771"             # 출강 문의 전화

    # ── 6개 교육 분야 (번호, 제목, 아이콘, 대상 태그, 세부 항목) ──
    CURRICULA = [
        ("01", "AI 윤리 및 책임 있는 AI 활용", "shield-check", "전 대상 공통 · 기본", [
            "생성형 AI의 이해와 한계", "책임 있는 AI 활용 원칙", "AI 결과물에 대한 인간의 책임",
            "AI 환각(Hallucination)의 이해", "AI 결과물 검증 및 팩트체크", "알고리즘 편향과 차별 문제",
            "투명성·책임성·공정성 등 AI 윤리 핵심 원칙", "실제 AI 윤리 사례 분석"]),
        ("02", "기업 AI 컴플라이언스", "building-2", "기업 · 공공기관", [
            "기업의 생성형 AI 활용과 법적·윤리적 리스크", "기업이 알아야 할 국내 AI 관련 법·제도",
            "국내 AI 기본법 등 주요 제도 이해", "EU AI Act 등 글로벌 AI 규제 동향",
            "기업 AI 활용 내부통제", "임직원 생성형 AI 사용 기준", "사내 AI 활용 가이드라인 수립",
            "AI 활용 시 책임소재", "AI 거버넌스 및 관리체계", "기업 AI 컴플라이언스 자율점검"]),
        ("03", "AI 정보보안 · 개인정보 보호", "lock", "기업 · 공공기관 · 연구기관", [
            "생성형 AI 사용과 기업 정보보안", "사내 기밀 및 영업비밀 유출 예방",
            "개인정보·고객정보의 생성형 AI 입력 위험", "연구자료·기술자료·소스코드·내부문서 보호",
            "외부 생성형 AI 서비스 사용 시 보안수칙", "프롬프트 인젝션(Prompt Injection)의 이해와 대응",
            "민감정보 입력 및 데이터 노출 위험", "AI 서비스 이용 시 데이터 처리방식 확인",
            "생성형 AI 관련 보안사고 사례", "정보 유출 발생 시 대응 절차"]),
        ("04", "생성형 AI 저작권 · 법적 리스크", "copyright", "기업 · 크리에이터 · 마케팅", [
            "생성형 AI와 저작권의 기본 이해", "AI 학습데이터와 저작권 이슈", "AI 생성물의 저작권 문제",
            "생성형 AI 산출물의 상업적 활용 시 주의사항", "AI 생성 이미지·영상·문서·코드 활용",
            "기존 저작물의 AI 입력 및 활용", "초상권·인격권 문제", "AI 음성·이미지 합성 시 주의사항",
            "기업 마케팅 콘텐츠의 AI 활용", "AI 콘텐츠 활용 시 법적 리스크 점검"]),
        ("05", "대학 · 연구자를 위한 AI 연구윤리", "book-open-check", "대학 · 대학원 · 연구기관", [
            "생성형 AI 시대의 연구윤리", "논문 작성 과정에서 생성형 AI 활용",
            "대학 과제·레포트에서의 AI 활용 범위", "아이디어·자료정리·번역·교정·코딩 등 단계별 AI 활용",
            "AI 활용 사실 및 활용 범위 표시", "AI 생성 문장과 표절·연구부정행위",
            "AI가 생성한 허위 참고문헌 및 DOI 검증", "연구데이터·설문자료·미공개 연구자료 보호",
            "논문·학술자료의 저작권", "AI 결과물의 출처 및 사실 검증", "연구자의 최종 검토와 책임"]),
        ("06", "청소년 AI 윤리 · 디지털 시민교육", "school", "초 · 중 · 고 · 교육청", [
            "생성형 AI의 원리와 올바른 활용", "AI가 항상 정답을 말하지 않는 이유", "AI 환각 체험",
            "잘못된 AI 정보 판별 및 팩트체크", "수행평가·숙제·발표에서의 AI 활용", "AI 활용과 표절 예방",
            "과제 제출 시 AI 활용 범위 표시", "딥페이크 이미지·영상·음성의 이해",
            "딥페이크를 이용한 디지털 범죄 예방", "AI 사칭·사기 콘텐츠 식별", "개인정보 및 초상권 보호",
            "친구의 사진·음성을 AI로 사용하는 행위의 문제점", "AI 사이버폭력 예방",
            "책임 있는 AI 활용과 디지털 시민의식"]),
    ]

    cu_cards = "\n".join(f"""          <article class="cu-card reveal" id="field-{num}">
            <div class="cu-head">
              <span class="cu-num">{num}</span>
              <div class="cu-title"><h3>{title}</h3><span class="cu-tag">{tag}</span></div>
              <div class="cu-icon"><i data-lucide="{icon}"></i></div>
            </div>
            <ul class="cu-list">
{chr(10).join(f'              <li>{it}</li>' for it in items)}
            </ul>
          </article>""" for num, title, icon, tag, items in CURRICULA)

    # ── 교육시간별 구성 (2026.09.21: 시간별 가격 표기를 없애고 구성·예시·적합 대상으로 안내. 비용은 문의 시 견적으로) ──
    FORMATS = [
        ("1", "특강", "핵심만 압축해 전하는 한 시간",
         "딥페이크 예방 + AI 학습윤리 + 팩트체크", "청소년 특강, 전 구성원 인식 교육"),
        ("2", "기본 교육", "원칙과 사례를 함께 다루는 구성",
         "AI 컴플라이언스 + 정보보안 + 개인정보 보호", "기업 · 공공기관 임직원 교육"),
        ("3", "집중 교육", "실습이 들어가는 구성",
         "생성형 AI 연구윤리 + 저작권 + AI 환각 · 참고문헌 검증", "대학 · 연구기관, 교직원 연수"),
        ("4", "심화 워크숍", "우리 조직의 기준까지 세우는 구성",
         "AI 윤리 + 컴플라이언스 + 정보보안 + 개인정보 + 저작권 + AI 거버넌스", "기업 심화교육, 관리자 워크숍"),
    ]
    fmt_cards = "\n".join(f"""          <article class="fmt-card reveal">
            <span class="fmt-type">{typ}</span>
            <div class="fmt-hours">{h}<small>시간</small></div>
            <h3>{title}</h3>
            <span class="fmt-ex">{combo}</span>
            <p class="fmt-fit"><b>이런 곳에</b> {fit}</p>
          </article>""" for h, typ, title, combo, fit in FORMATS)

    # ── 대상별 추천 ──
    AUD = [
        ("building-2", "기업 · 공공기관",
         "AI 윤리 + AI 컴플라이언스 + 정보보안 + 개인정보 보호 + 저작권 + AI 거버넌스",
         "실제 업무에서 생성형 AI를 안전하게 활용하기 위한 실무·보안 중심 교육으로 구성합니다."),
        ("graduation-cap", "대학 · 연구기관",
         "생성형 AI 활용 + 연구윤리 + 논문·과제 AI 활용 + 저작권 + 개인정보 + AI 결과 검증",
         "연구자와 대학(원)생이 생성형 AI를 책임 있게 활용하기 위한 연구윤리 중심 교육으로 구성합니다."),
        ("school", "초 · 중 · 고등학교",
         "AI 윤리 + 디지털 시민성 + 학습윤리 + 딥페이크 예방 + 개인정보 보호 + 팩트체크",
         "학생들이 생성형 AI를 안전하고 올바르게 활용할 수 있도록 사례와 체험 중심으로 구성합니다."),
        ("briefcase", "교직원 · 관리자",
         "AI 윤리 + 기관 AI 활용지침 + 개인정보 보호 + 정보보안 + AI 거버넌스 + 사고 대응",
         "학생·교직원 또는 조직 구성원의 AI 활용을 관리하기 위한 관리자 중심 교육으로 구성합니다."),
    ]
    aud_cards = "\n".join(f"""          <article class="card reveal">
            <div class="card-icon"><i data-lucide="{ic}"></i></div>
            <h3>{t}</h3>
            <span class="combo">{combo}</span>
            <p>{d}</p>
          </article>""" for ic, t, combo, d in AUD)

    # ── 교육이 끝난 뒤에도 기관에 남는 것 (2026.09.21) ──
    LEAVE = [
        ("file-check", "기관 맞춤 교안",
         "교육 대상과 목적을 확인한 뒤 위원회가 커리큘럼을 최종 구성합니다. 청소년, 대학생, 임직원, 연구자에게 같은 슬라이드를 쓰지 않습니다."),
        ("book-open", "위원회 표준교재와 같은 기준",
         "AI윤리전문가 양성과정 표준교재와 같은 원칙으로 가르칩니다. 강사가 바뀌어도, 어느 기관에서 들어도 같은 깊이입니다."),
        ("clipboard-list", "바로 쓰는 AI 활용 체크리스트",
         "교육이 끝나면 조직에서 그대로 쓸 수 있는 AI 활용 체크리스트를 드립니다. 강의실을 나간 뒤에도 기준이 남습니다."),
        ("award", "교육 증빙 서류 발급",
         "출강확인서, 교육 결과 요약, 교육 이수확인서를 발급합니다. 정부·지자체·공공기관 연계 프로그램의 증빙에도 쓸 수 있습니다."),
    ]
    leave_html = "".join(f"""
          <article class="bn reveal"><span class="bn-no">0{i}</span><div class="bn-ic"><i data-lucide="{ic}"></i></div><strong>{t}</strong><p>{d}</p></article>"""
                         for i, (ic, t, d) in enumerate(LEAVE, 1))

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner" style="padding-block:78px 72px">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; 강의 신청</p>
        <span class="hl-pill"><i data-lucide="badge-check"></i>한국AI윤리위원회 소속 전문 인력 2인 공동 출강 · 기관 맞춤 설계</span>
        <h1>AI 윤리교육 · 전문 출강</h1>
        <p class="ph-lead">AI 윤리부터 컴플라이언스, 정보보안, 연구윤리까지.<br>
           기관에 맞춰 <b class="t">위원회 전문 인력이 직접</b> 찾아갑니다.</p>
        <p class="ph-body">AI기본법 시행 이후 기업·공공기관·학교마다 "AI를 어디까지 어떻게 써야 하는가"를 구성원에게 설명해야 하는 때가 왔습니다.
           원칙을 나열하는 강의가 아니라, <strong>우리 조직의 기준을 함께 세우는 교육</strong>을 위원회 표준교재와 같은 기준으로 진행합니다.</p>
        <div class="hero-hooks">
          <span><i data-lucide="check"></i>1~4시간 자유 선택</span>
          <span><i data-lucide="check"></i>6개 분야 자유 조합</span>
          <span><i data-lucide="check"></i>AI기본법 반영 최신 교안</span>
          <span><i data-lucide="check"></i>전문 인력 2인 공동 출강</span>
          <span><i data-lucide="check"></i>출강확인서 · 이수확인서 발급</span>
        </div>
        <div style="display:flex;gap:11px;flex-wrap:wrap;margin-top:26px">
          <a class="btn btn-primary" href="#request">출강 문의하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-light" href="#fields">교육 분야 보기</a>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="stats reveal">
          <div class="stat"><div class="stat-num">2인</div><div class="stat-label">공동 출강</div><div class="stat-sub">강의와 실습을 나누어 진행</div></div>
          <div class="stat"><div class="stat-num" style="font-size:clamp(19px,2.2vw,24px);line-height:1.4">2026 기준</div><div class="stat-label">AI기본법 반영 교안</div><div class="stat-sub">제도와 사례를 최신으로 갱신</div></div>
          <div class="stat"><div class="stat-num">1~4시간</div><div class="stat-label">교육시간 자유 선택</div><div class="stat-sub">기관 일정에 맞춰 구성</div></div>
          <div class="stat"><div class="stat-num">6개 분야</div><div class="stat-label">자유 조합 커리큘럼</div><div class="stat-sub">필요한 주제만 골라 담기</div></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="split">
          <div class="reveal">
            <span class="eyebrow">How We Teach</span>
            <h2 class="h-sec">듣고 끝나지 않는 AI 윤리 강의</h2>
            <p class="lead" style="margin-bottom:22px">원칙을 나열하는 강의가 아니라, <strong>내일 당장 마주칠 장면</strong>으로 시작합니다.
               위원회 소속 전문 인력 2인이 강의와 실습을 나누어 진행합니다.</p>
            <ul style="display:grid;gap:12px;margin-bottom:8px">
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span><strong>실제 장면에서 출발합니다.</strong> 보고서 초안을 AI로 쓴 경우, 회의 녹취를 외부 AI에 넣은 경우처럼
                 조직에서 이미 벌어지고 있는 상황을 먼저 꺼내 놓고 기준을 함께 세웁니다</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span><strong>위원회 표준교재와 같은 기준으로 가르칩니다.</strong> 강사가 바뀌어도 전달되는 원칙이 달라지지 않습니다</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span><strong>2026년 제도를 반영합니다.</strong> AI기본법 시행과 해외 규제 동향을 교안에 계속 갱신해 반영합니다</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span><strong>대상에 맞춰 다시 짭니다.</strong> 청소년, 대학생, 임직원, 연구자에게 같은 슬라이드를 쓰지 않습니다</span></li>
              <li style="display:flex;gap:10px;align-items:flex-start"><i data-lucide="check-circle-2" style="width:19px;height:19px;color:#00B4A6;flex-shrink:0;margin-top:4px"></i><span><strong>가져갈 것을 남깁니다.</strong> 교육이 끝나면 조직에서 바로 쓸 수 있는 AI 활용 체크리스트를 드립니다</span></li>
            </ul>
          </div>
          <div class="reveal" style="display:grid;gap:14px">
            <div class="inst-card">
              <div class="inst-avatar"><i data-lucide="book-open"></i></div>
              <div>
                <div class="inst-deg">강사 1 · 메인 강의</div>
                <div class="inst-name">원칙과 사례</div>
                <div class="inst-field">AI 활용 원칙, 국내외 제도, 실제로 문제가 된 사례 분석</div>
              </div>
            </div>
            <div class="inst-card">
              <div class="inst-avatar inst-avatar--teal"><i data-lucide="user-check"></i></div>
              <div>
                <div class="inst-deg">강사 2 · 실습 · 질의</div>
                <div class="inst-name">우리 조직의 기준</div>
                <div class="inst-field">참여자의 실제 업무 상황을 받아 함께 판단해 보는 실습과 질의응답</div>
              </div>
            </div>
            <div class="notice" style="font-size:13.5px">
              <strong>위원회가 직접 책임집니다.</strong> 출강 인력은 외주·파견 강사가 아니라 한국AI윤리위원회에 소속된
              AI 윤리 전문 인력입니다. 위원회의 윤리 기준과 표준교재를 그대로 전달하므로, 어느 기관에서 들으셔도
              같은 원칙을 같은 깊이로 배우시게 됩니다.
            </div>
            <div class="notice notice--teal" style="font-size:13.5px">
              <strong>참여자가 말을 하게 만듭니다.</strong> 두 강사가 강의와 실습을 나누어 진행하기 때문에,
              대규모 인원 교육에서도 질문이 끊기지 않고 실습형 워크숍이 안정적으로 돌아갑니다.
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--gray" id="format">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Format</span>
          <h2 class="h-sec">교육시간은 1시간부터 4시간까지</h2>
          <p class="h-sub">기관의 일정과 목적에 맞춰 교육시간을 정하고, 6개 분야에서 필요한 주제만 골라 담습니다.
             모든 과정에 위원회 전문 인력 2인이 함께 출강합니다. 아래는 기관에서 가장 많이 선택하는 구성 예시입니다.</p>
        </div>
        <div class="fmt-grid">
{fmt_cards}
        </div>
        <div class="grid grid-2" style="margin-top:22px">
          <div class="notice">
            <strong>자유 조합:</strong> 교육시간에 따라 강의 내용이 고정되지 않습니다.
            아래 6개 교육 분야에서 필요한 주제를 자유롭게 선택 · 조합하실 수 있으며,
            교육 목적 · 대상 · 수준에 따라 세부 커리큘럼을 조정해 드립니다.
          </div>
          <div class="notice notice--gray">
            <strong>비용 안내:</strong> 교육비는 교육시간과 인원, 출장 지역, 교안 제작 범위에 따라 달라집니다.
            아래 양식으로 문의해 주시면 기관에 맞춘 견적을 1~3일 내 안내드립니다.
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="fields">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Curriculum</span>
          <h2 class="h-sec">교육 분야</h2>
          <p class="h-sub">6개 분야의 세부 주제 중 기관에 필요한 내용을 자유롭게 선택 · 조합하실 수 있습니다.</p>
        </div>
        <div class="grid grid-2" style="align-items:start">
{cu_cards}
        </div>
      </div>
    </section>

    <section class="section section--ink">
      <div class="wrap">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">What Remains</span>
          <h2 class="h-sec" style="color:#fff">교육이 끝난 뒤에도 기관에 남는 것</h2>
          <p class="h-sub" style="color:#9FB3D1;margin:0 auto">한 번 듣고 잊히는 강의가 아니라, 조직의 기준과 증빙으로 남는 교육입니다.</p>
        </div>
        <div class="bn-grid">{leave_html}
        </div>
        <div class="bn-foot reveal">
          <div class="bn-foot-l"><i data-lucide="sparkles"></i>
            <div><strong>공공 · 정부 연계 프로그램도 가능합니다</strong>
              <span>정부·지자체·공공기관 주관 교육과 정부지원사업 연계 프로그램은 주관 기관과 협의해 일정 · 내용 · 증빙 서류를 맞춤으로 준비해 드립니다.</span></div>
          </div>
          <a class="btn btn-white" href="#request">출강 문의하기 <i data-lucide="arrow-right"></i></a>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Recommended</span>
          <h2 class="h-sec">대상별 추천 교육</h2>
          <p class="h-sub">기관 유형별로 가장 많이 선택하는 조합입니다. 그대로 진행하거나 자유롭게 바꿔 구성하실 수 있습니다.</p>
        </div>
        <div class="grid grid-2">
{aud_cards}
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Process</span>
          <h2 class="h-sec">교육 진행 절차</h2>
        </div>
        <div class="grid grid-3">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">출강 문의</h3><p style="font-size:14px">아래 양식 또는 메일 접수</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">대상 · 목적 확인</h3><p style="font-size:14px">교육 대상과 목적 협의</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">교육시간 선택</h3><p style="font-size:14px">1~4시간 중 선택</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">교육 분야 선택</h3><p style="font-size:14px">6개 분야 자유 조합</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 05</span><h3 style="font-size:16px">커리큘럼 · 견적 안내</h3><p style="font-size:14px">위원회가 최종 구성해 견적과 함께 회신</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 06</span><h3 style="font-size:16px">전문인력 2인 출강</h3><p style="font-size:14px">교육 진행 · 증빙 발급</p></div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Advisory</span>
          <h2 class="h-sec">커리큘럼 자문 위원단</h2>
          <p class="h-sub">교육 커리큘럼은 위원회 6개 분과 전문위원의 자문과 검토를 거쳐 구성됩니다.</p>
        </div>
        <div class="member-grid" id="lecturerGrid"></div>
      </div>
    </section>

    <section class="section section--gray" id="request">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">Contact</span>
          <h2 class="h-sec">AI 윤리교육 출강 문의</h2>
          <p class="h-sub" style="margin:0 auto">우리 기관에 필요한 AI 교육을 직접 구성해 보세요.
             작성해 주시면 담당자가 확인 후 1~3일 내 회신드립니다.</p>
        </div>

        <form class="form" id="lectureForm" action="#">
          <div class="form-row">
            <div class="field">
              <label for="l-org">기관·기업명<span class="req">*</span></label>
              <input type="text" id="l-org" name="기관명" required placeholder="예) ○○대학교 · ○○주식회사 · ○○고등학교">
            </div>
            <div class="field">
              <label for="l-name">담당자 성함<span class="req">*</span></label>
              <input type="text" id="l-name" name="담당자" required>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="l-contact">연락처<span class="req">*</span></label>
              <input type="text" id="l-contact" name="연락처" required placeholder="전화번호 또는 이메일">
              <p class="field-hint">회신받으실 연락처 하나만 남겨주시면 됩니다.</p>
            </div>
            <div class="field">
              <label for="l-hours">희망 교육시간</label>
              <select id="l-hours" name="희망교육시간">
                <option value="">선택해 주세요 (미정 가능)</option>
                <option>1시간 (특강)</option>
                <option>2시간 (기본 교육)</option>
                <option>3시간 (집중 교육)</option>
                <option>4시간 (심화 워크숍)</option>
                <option>미정 · 협의</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label for="l-topic">희망 교육 분야<span class="req">*</span></label>
            <select id="l-topic" name="희망교육분야" required>
              <option value="">선택해 주세요</option>
              <option>01. AI 윤리 및 책임 있는 AI 활용</option>
              <option>02. 기업 AI 컴플라이언스</option>
              <option>03. AI 정보보안 · 개인정보 보호</option>
              <option>04. 생성형 AI 저작권 · 법적 리스크</option>
              <option>05. 대학 · 연구자를 위한 AI 연구윤리</option>
              <option>06. 청소년 AI 윤리 · 디지털 시민교육</option>
              <option>복수 분야 조합 희망 (요청사항에 기재)</option>
            </select>
          </div>
          <div class="field">
            <label for="l-msg">요청 사항 (선택)</label>
            <textarea id="l-msg" name="요청사항" style="min-height:100px" placeholder="희망 일정, 예상 인원, 조합하고 싶은 분야 등을 간단히 적어주셔도 좋습니다."></textarea>
          </div>
          <button type="submit" class="btn btn-primary" style="justify-self:start">
            출강 문의 보내기 <i data-lucide="send"></i>
          </button>
          <p class="field-hint">
            버튼을 누르면 메일 앱이 열리고 작성 내용이 자동으로 담깁니다.
            직접 보내실 경우: <a href="mailto:{L_EMAIL}" style="color:var(--blue);font-weight:600">{L_EMAIL}</a>
          </p>
        </form>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="cta-band">
          <div><h2>우리 기관에 필요한 AI 교육을 직접 구성해 보세요</h2>
            <p>기업·공공기관부터 학교·대학·연구기관까지, 교육 대상과 목적에 맞춰
               1시간부터 4시간까지 맞춤형 AI 윤리교육을 제공합니다. 문의해 주시면 1~3일 내 커리큘럼과 견적을 함께 회신드립니다.</p></div>
          <div class="btns">
            <a class="btn btn-white" href="#request">AI 윤리교육 출강 문의</a>
            <a class="btn btn-light" href="{CERT_HREF}">{CERT_CTA}</a>
          </div>
        </div>
        <p class="small-contact">출강 문의 &nbsp;|&nbsp; {L_EMAIL} &nbsp;·&nbsp; {L_TEL}</p>
      </div>
    </section>"""

    script = """  <script src="assets/js/members-data.js"></script>
  <script>
  /* 자문 위원단: 위원 명단 데이터의 '전문위원'을 자동으로 표시합니다 */
  (function(){
    var box=document.getElementById('lecturerGrid');
    if(!box||!window.KAIEC_MEMBERS)return;
    var list=window.KAIEC_MEMBERS.filter(function(m){return m.group==='전문위원'});
    if(!list.length){box.outerHTML='';return}
    box.style.maxWidth='560px';box.style.margin='0 auto';
    box.innerHTML=list.map(function(m){
      var av;
      if(m.photo){av='<div class="member-avatar member-avatar--photo"><img src="assets/img/members/'+m.photo+'" alt="'+m.name+'" loading="lazy"></div>'}
      else{var initial=(m.name||'?').replace(/[^가-힣A-Za-z]/g,'').slice(0,1)||'·';av='<div class="member-avatar">'+initial+'</div>'}
      return '<div class="member">'+av
        +'<div class="member-role">'+(m.role||'전문위원')+'</div>'
        +'<div class="member-name">'+m.name+'</div>'
        +'<div class="member-field">'+(m.field||'')+'</div></div>';
    }).join('');
  })();
  /* 출강 문의 폼: 작성 내용을 담아 메일 앱을 엽니다 */
  (function(){
    var f=document.getElementById('lectureForm');
    if(!f)return;
    f.addEventListener('submit',function(e){
      e.preventDefault();
      function v(n){var el=f.querySelector('[name="'+n+'"]');return el?el.value.trim():''}
      var subject='[출강 문의] '+v('기관명')+' / '+v('희망교육분야');
      var lines=[
        '■ 기관·기업명 : '+v('기관명'),
        '■ 담당자      : '+v('담당자'),
        '■ 연락처      : '+v('연락처'),
        '■ 희망 교육시간 : '+v('희망교육시간'),
        '■ 희망 교육 분야 : '+v('희망교육분야'),
        '',
        '■ 요청 사항',
        v('요청사항'),
        '',
        '--- 한국AI윤리위원회 AI 윤리교육 출강 문의 양식에서 작성됨 ---'
      ];
      location.href='mailto:__LEMAIL__?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(lines.join('\\n'));
    });
  })();
  </script>
""".replace('__LEMAIL__', L_EMAIL)

    page("lecture.html", "AI 윤리교육 · 전문 출강",
         "한국AI윤리위원회 소속 전문 인력 2인이 학교·기업·공공기관에 직접 출강하는 AI 윤리교육. AI 윤리, 기업 AI 컴플라이언스, 개인정보·보안, 생성형 AI 저작권, 청소년 AI 윤리를 1~4시간 맞춤 과정으로 제공합니다.",
         body, extra_script=script,
         keywords=["AI 윤리교육", "AI 교육 출강", "생성형 AI 교육", "AI 컴플라이언스 교육", "AI 연구윤리 교육",
                   "딥페이크 예방 교육", "청소년 AI 교육", "기업 AI 교육", "AI 정보보안 교육", "찾아가는 AI 교육"])


# --------------------------------------------------------------- expert.html
# expert 페이지 샘플 문항 3개 (평가응시 체험 모드 문항으로도 사용): (발문, 선택지 4개, 정답 인덱스 0~3, 해설)
SAMPLE_Q = [
    ("생성형 AI를 활용해 초안을 작성한 보고서를 고객사에 제출하려 합니다. 가장 적절한 조치는?",
     ["AI가 작성했으므로 별도 검토 없이 제출한다",
      "인용과 수치의 출처를 검증하고, 조직 기준에 따라 AI 활용 여부를 표기한다",
      "AI 활용 사실은 밝히지 않는 것이 안전하다",
      "고객사가 묻기 전까지는 어떤 조치도 필요 없다"], 1,
     "결과물의 책임은 사람에게 있습니다. 사실관계 검증과 투명한 표기가 책임 있는 AI 활용의 기본 원칙입니다."),
    ("채용 서류를 자동으로 걸러 주는 AI를 도입하려 합니다. 도입 전에 반드시 점검해야 할 것은?",
     ["처리 속도가 충분히 빠른지",
      "특정 성별·연령·출신에 불리하게 작동하는 편향이 없는지와 결정에 대한 설명 가능성",
      "경쟁사도 같은 도구를 도입했는지",
      "지원자에게 알리지 않아도 되는지"], 1,
     "자동화된 결정은 차별과 혐오를 그대로 학습할 수 있습니다. 공정성 점검과 사람의 최종 판단은 제3장이 다루는 핵심 기준입니다."),
    ("2026년 1월 시행된 AI기본법에 대한 설명으로 옳은 것은?",
     ["AI를 개발하는 기업에만 적용된다", "생성형 AI 산출물의 표시·고지 등 활용 단계의 의무도 포함한다",
      "윤리 권고일 뿐 법적 의무는 없다", "해외 기업과는 무관한 국내 지침이다"], 1,
     "AI기본법은 개발자뿐 아니라 AI를 활용하는 기업·기관에도 투명성 등 의무를 부여합니다. 기준을 아는 사람이 필요해진 이유입니다."),
]


def build_expert():
    """AI윤리전문가 양성과정: 양성 필요성과 과정 안내 (전환형 랜딩)
    - 2026.09.21 통합: 기본·심화 두 과정을 하나의 「AI윤리전문가 양성과정」으로. 허들을 낮추고(가격 하나, 선택 없음) 취업준비생·대학생에게
      바로 와닿는 '이수하면 받는 것' 8가지(BENEFITS)를 앞세움. 학습자료는 통합 교재(9개 장 + 부록) 기준, 쪽수는 자료 통합 작업 전이라 적지 않음
    - 등록된 자격 제도가 아니므로 인증(자격)·검정·급수 표현을 쓰지 않음 (2026.09.14). 2026.09.16부터 '이수 평가·이수증'으로 표기
    - 2026.09.16 학습 방식: 온라인 강의 없이 위원회 표준교재 등 학습자료 5종(PDF) 자율학습 + 온라인 이수 평가, 응시 기간 안 기준에 이를 때까지 재응시
    - 수강·이수 절차 6단계(양성과정 신청 → 학습자료 확인 → 자율학습 → 평가응시 → 이수 기준 충족 → 이수증 발급), 응시는 상단 [평가응시] 로그인"""
    pay_btns = (f'<div style="display:flex;flex-direction:column;align-items:center;gap:10px;margin-top:24px">'
                f'<a class="btn btn-primary" href="{CERT_HREF}">{CERT_CTA} <i data-lucide="arrow-right"></i></a>'
                f'<span style="font-size:13px;color:var(--gray-500)">신청을 완료하면 결제 페이지로 자동 연결됩니다</span></div>')

    # 이수하면 받는 것 8가지 (BENEFITS 상수)
    bn_html = "".join(f"""
          <div class="bn reveal">
            <span class="bn-no">{i:02d}</span>
            <div class="bn-ic"><i data-lucide="{ic}"></i></div>
            <strong>{t}</strong>
            <p>{d}</p>
          </div>""" for i, (ic, t, d) in enumerate(BENEFITS, 1))

    # 이수증이 왜 값어치가 있는지: 공신력 · 활용성 · 미래 유망
    WORTH = [
        ("scale", "위원회가 직접 확인해 주는 이력",
         f"2024년 3월 연구에 착수해 {STUDY_MONTHS}개월 넘게 산학이 함께 만든 표준교재로 공부하고, 같은 기준의 평가를 통과해야 발급됩니다. "
         f"이수증에는 이수번호가 부여되고, 채용 담당자나 기관이 문의하면 <strong>위원회가 직접 이수 사실을 확인</strong>해 드립니다.",
         [f"{STUDY_MONTHS}개월 산학 공동 연구", "이수번호 부여", "위원회 직접 확인"]),
        ("briefcase", "다음 주 업무에 바로 쓰는 역량",
         "배우고 끝나는 교육이 아닙니다. 『실무 도구집』의 <strong>실무 양식 13종</strong>을 그대로 고쳐 쓰면 사내 AI 사용 기준, "
         "AI 활용 고지문, 위험도 점검표가 바로 만들어집니다. 이력서·자기소개서에는 활용 가이드대로 한 줄이 남습니다.",
         ["이력서 · 자기소개서", "사내 AI 기준 수립", "실무 양식 13종"]),
        ("trending-up", "규제가 만드는 수요, 지금이 가장 앞자리",
         "2026년 1월 AI기본법이 시행되고 8월 EU AI Act 투명성 의무가 발효되면서, AI를 활용하는 기업·기관까지 의무의 주체가 되었습니다. "
         "AI 거버넌스 시장 규모는 연평균 45.3% 성장이 전망되는데 담당할 사람은 아직 적습니다. <strong>먼저 이수한 사람이 이 분야의 경력자</strong>로 앞서 갑니다.",
         ["2026 AI기본법 시행", "EU AI Act 적용", "AI 거버넌스 성장"]),
    ]
    worth_html = "".join(f"""
            <div class="worth reveal">
              <span class="worth-no">0{i}</span>
              <div class="worth-ic"><i data-lucide="{ic}"></i></div>
              <div class="worth-b">
                <strong>{t}</strong>
                <p>{d}</p>
                <div class="chips">{"".join(f'<span class="chip">{c}</span>' for c in chips)}</div>
              </div>
            </div>""" for i, (ic, t, d, chips) in enumerate(WORTH, 1))

    mat_html = "".join(f"""
            <li class="lec reveal">
              <div class="lec-head"><span class="lec-num">{i}</span><strong>{t}</strong><span class="lec-time"><i data-lucide="book-open"></i>{vol}</span></div>
              <p>{d}</p>
              <div class="chips">{"".join(f'<span class="chip">{c}</span>' for c in chips)}</div>
            </li>""" for i, (t, vol, d, chips) in enumerate(MATERIAL_ITEMS, 1))

    sq_html = "".join(f"""
          <div class="sq reveal" data-answer="{ans}">
            <div class="sq-q"><span class="sq-num">Q{i}</span>{q}</div>
            <div class="sq-opts">{"".join(f'<button type="button" class="sq-opt" data-i="{j}"><span>{chr(9312+j)}</span>{o}</button>' for j, o in enumerate(opts))}</div>
            <div class="sq-exp" hidden><strong>정답 {chr(9312+ans)}</strong> {exp}</div>
          </div>""" for i, (q, opts, ans, exp) in enumerate(SAMPLE_Q, 1))
    WHY = [
        ("scale", "국내 · AI기본법 시행", "2026. 1",
         "「인공지능 발전과 신뢰 기반 조성 등에 관한 기본법」(AI기본법)이 2026년 1월 22일 시행되었습니다. 고영향·생성형 AI에 대한 투명성 고지, AI 생성물 표시 등 새로운 의무가 도입되었고, AI를 <strong>개발하는 기업만이 아니라 활용하는 기업·기관도 의무의 주체</strong>가 됩니다."),
        ("building-2", "글로벌 · EU AI Act 단계 적용", "2026. 8",
         "EU AI Act는 2025년 금지 규정과 조직 구성원의 <strong>AI 리터러시 확보 의무</strong>를 시작으로, 2026년 8월 생성형 AI 표시 등 조항의 시행과 집행이 본격화되었습니다. 글로벌 기준에 맞는 AI 윤리 역량은 이제 수출·협력 기업의 실무 요건입니다."),
        ("shield-check", "현장 · 상시화된 AI 리스크", "지금",
         "기밀 정보 입력, 허위 정보(환각) 인용, 저작권 분쟁, AI 표절 논란. 생성형 AI가 업무와 학습의 일상이 되면서 사고도 일상이 되었습니다. <strong>기준을 아는 한 사람</strong>이 조직 전체의 리스크를 줄입니다."),
        ("trending-up", "기회 · 아직 소수인 전문 인력", "선점",
         "AI를 활용할 줄 아는 사람은 많지만, AI 윤리와 규제 대응을 체계적으로 배운 사람은 아직 소수입니다. 수요가 먼저 커진 시장에서 <strong>지금 시작하는 사람이 전문가 그룹의 첫 자리</strong>를 차지합니다."),
    ]
    why_cards = "\n".join(f"""          <article class="card reveal">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
              <div class="card-icon" style="margin-bottom:0"><i data-lucide="{ic}"></i></div>
              <span class="card-num" style="margin-bottom:0">{when}</span>
            </div>
            <h3>{t}</h3>
            <p>{d}</p>
          </article>""" for ic, t, when, d in WHY)

    CAREER = [
        ("file-check", "이력서의 확실한 한 줄",
         "AI를 '잘' 쓰는 사람은 많습니다. <strong>윤리적으로 다룰 줄 아는 사람</strong>임을 위원회 공식 이수증으로 증명하면, 그 한 줄이 차별화가 됩니다."),
        ("building-2", "기업·기관이 지금 찾는 스펙",
         "AI기본법 시행으로 사내 AI 기준과 임직원 교육을 맡을 사람이 필요해졌습니다. 체계적으로 배운 사람이 <strong>가장 먼저 호명</strong>됩니다."),
        ("trending-up", "앞으로가 더 유망한 분야",
         "AI가 퍼질수록 AI 윤리·컴플라이언스 수요는 커집니다. 규제가 막 시작된 지금이 <strong>가장 빠른 선점 시점</strong>입니다."),
        ("badge-check", "위원회 공식 등록으로 남는 이력",
         "홈페이지에 <strong>AI윤리전문가로 공식 등록</strong>되어 검색되고, 위원회가 이수 사실을 확인해 줍니다. 종이 한 장이 아니라 <strong>기관이 뒷받침하는 이력</strong>입니다."),
    ]
    career_cards = "\n".join(f"""          <article class="card reveal">
            <div class="card-icon"><i data-lucide="{ic}"></i></div>
            <h3>{t}</h3><p>{d}</p>
          </article>""" for ic, t, d in CAREER)

    INCLUDED = [
        ("book-open", "위원회 표준교재 등 학습자료 5종 (PDF)"),
        ("monitor-play", f"온라인 이수 평가 {EXAM[0]}문항 · {EXAM_MIN}분 (응시 기간 {EXAM_WINDOW_DAYS}일)"),
        ("check-circle-2", "응시 기간 안 기준에 이를 때까지 재응시"),
        ("award", "한국AI윤리위원회 공식 이수증 (고유 이수번호)"),
        ("file-search", "홈페이지 공식 등록 · 검색"),
        ("pen-line", "이력서 · 자기소개서 활용 가이드 (이수자 전용)"),
        ("id-card", "이력서 국문·영문 표기 안내"),
        ("user-check", "전문위원 등록 신청 자격"),
    ]
    incl_html = "".join(f'<li><i data-lucide="{ic}"></i><span>{t}</span></li>' for ic, t in INCLUDED)

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner" style="padding-block:78px 72px">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; AI윤리전문가 양성과정</p>
        <span class="hl-pill"><i data-lucide="badge-check"></i>한국AI윤리위원회 주관 · 이력에 더하는 AI 전문역량</span>
        <h1>AI윤리전문가 양성과정 <span class="hot-tag">HOT</span></h1>
        <p class="ph-lead" style="max-width:900px">2026년, 이력서에 새롭게 더할 AI 전문 이력.<br>
           취업준비생부터 대학생, 실무자까지 지금 시작하는 <b class="t">AI윤리전문가</b>.</p>
        <p class="ph-body" style="max-width:900px!important">전공이나 경력에 관계없이 온라인으로 시작할 수 있습니다.<br>
           <strong>학습자료부터 평가, 공식 이수증 발급, 한국AI윤리위원회 홈페이지 전문가 등록</strong>까지 한 번에.</p>
        <div class="hero-hooks">
          <span><i data-lucide="check"></i>전공 · 경력 제한 없음</span>
          <span><i data-lucide="check"></i>100% 온라인</span>
          <span><i data-lucide="check"></i>학습자료 제공</span>
          <span><i data-lucide="check"></i>공식 이수증 발급</span>
          <span><i data-lucide="check"></i>AI윤리전문가 공식 등록</span>
        </div>
        <div style="display:flex;gap:11px;flex-wrap:wrap;margin-top:26px">
          <a class="btn btn-primary" href="{CERT_HREF}">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-light" href="#benefits">이수 후 달라지는 것 보기 <i data-lucide="arrow-right"></i></a>
        </div>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="stats reveal">
          <div class="stat"><div class="stat-num" style="font-size:clamp(21px,2.4vw,27px);line-height:1.3">2026. 1</div><div class="stat-label">AI기본법 시행</div><div class="stat-sub">국내 AI 의무 규제 시대 개막</div></div>
          <div class="stat"><div class="stat-num" style="font-size:clamp(21px,2.4vw,27px);line-height:1.3">2026. 8</div><div class="stat-label">EU AI Act 투명성 의무</div><div class="stat-sub">고위험 의무는 2027년부터 단계 적용</div></div>
          <div class="stat"><div class="stat-num" style="font-size:clamp(21px,2.4vw,27px);line-height:1.3">{STUDY_MONTHS}개월+</div><div class="stat-label">산학 공동 연구 · 집필</div><div class="stat-sub">위원회 표준교재 + 온라인 이수 평가</div></div>
          <div class="stat"><div class="stat-num" style="font-size:clamp(21px,2.4vw,27px);line-height:1.3">100%</div><div class="stat-label">전 과정 온라인</div><div class="stat-sub">신청부터 이수증 발급까지</div></div>
        </div>
      </div>
    </section>

    <section class="section" id="why">
      <div class="wrap">
        <div class="center" style="margin-bottom:44px">
          <span class="eyebrow">Why Now</span>
          <h2 class="h-sec">왜 지금, AI윤리전문가인가 <span class="hot-tag">HOT</span></h2>
          <p class="h-sub">AI기본법 시행과 EU AI Act 적용이 같은 해에 시작됐습니다. AI 윤리는 교양에서 <strong>실무 요건</strong>이 됐고,
             먼저 준비한 사람이 첫 자리를 차지합니다.</p>
        </div>
        <div class="grid grid-2">
{why_cards}
        </div>
        <div class="notice notice--teal" style="margin-top:26px">
          <strong>핵심은 하나입니다.</strong> 조직마다 "AI를 어디까지 어떻게 써야 하는가"에 답할 사람이 필요해졌습니다.
          이 과정은 그 답을 배우고 증명하는 가장 빠른 길입니다.
        </div>
      </div>
    </section>

    <section class="section section--ink" id="benefits">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">What You Get</span>
          <h2 class="h-sec" style="color:#fff">{PRICE_SHORT}에, 이 여덟 가지가 한 번에</h2>
          <p class="h-sub" style="color:#9FB3D1">결제는 한 번, {won(PRICE)}. 이수증 발급부터 홈페이지 공식 등록, 재응시, 활용 가이드까지 한 번에.</p>
        </div>
        <div class="bn-grid">{bn_html}
        </div>
        <div class="bn-foot reveal">
          <div class="bn-foot-l"><i data-lucide="sparkles"></i>
            <div><strong>취업준비생 · 대학생이라면</strong>
              <span>경력이 없어도 됩니다. 이수증과 홈페이지 공식 등록, 활용 가이드로 자기소개서와 면접에서 "AI를 윤리적으로 다룰 줄 안다"를 근거 있게 말할 수 있습니다.</span></div>
          </div>
          <a class="btn btn-white" href="{CERT_HREF}">{CERT_CTA} <i data-lucide="arrow-right"></i></a>
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Career Value</span>
          <h2 class="h-sec">“올해 스펙은, 이거 하나로 확실합니다”</h2>
          <p class="h-sub">이수하는 순간부터 이력서와 면접, 실무에서 바로 쓰입니다.</p>
        </div>
        <div class="stat-band reveal">
          <div class="sb-num">{STAT_71["num"]}</div>
          <div class="sb-body">
            <strong>{STAT_71["head"]}</strong>
            <span>{STAT_71["body"]} AI를 윤리적으로 다룰 줄 안다는 위원회 공식 이수증과 홈페이지 공식 등록은 그 기준에 답하는 가장 확실한 한 줄입니다.</span>
            <small class="src">{STAT_71["src"]}</small>
          </div>
        </div>
        <div class="grid grid-2" style="margin-bottom:26px">
{career_cards}
        </div>
{resume_box()}
        <div class="grid grid-3" style="margin-top:26px">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">CAREER PATH 01</span><h3 style="font-size:16px">양성과정 이수</h3><p style="font-size:14px">위원회 공식 이수증과 홈페이지 공식 등록로 남는 첫 번째 이력</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">CAREER PATH 02</span><h3 style="font-size:16px">스펙 향상 · 커리어 활용</h3><p style="font-size:14px">취업 · 이직 · 승진, 사내 AI 활용 기준 담당으로</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">CAREER PATH 03</span><h3 style="font-size:16px">전문 활동으로 확장</h3><p style="font-size:14px">전문위원 등록 신청, 위원회 캠페인 · Fellowship 참여</p></div>
        </div>
      </div>
    </section>

    <section class="section" id="course">
      <div class="wrap">
        <div class="center" style="margin-bottom:44px">
          <span class="eyebrow">Program</span>
          <h2 class="h-sec">지금 기업이 원하는 스펙, 앞으로 더 유망한 직업<br>AI윤리전문가</h2>
          <p class="h-sub">AI기본법 시행 이후 기업·기관은 'AI를 윤리적으로 다룰 줄 아는 사람'을 찾기 시작했습니다. 과정은 하나, 고를 것도 나중에 더 낼 것도 없습니다.
             위원회 표준교재로 공부하고 온라인 이수 평가를 통과하면 <strong>공식 이수증과 홈페이지 공식 등록, 활용 가이드까지</strong> 한 번에 받습니다.</p>
        </div>
        <div class="one-course reveal">
          <article class="one-course-main">
            <div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap">
              <span class="badge" style="background:rgba(255,255,255,.16);color:#fff">{HOOK_ZERO} · {HOOK_START}</span>
            </div>
            <h3>AI윤리전문가 양성과정</h3>
            <p>전공·경력 제한 없이, 전 과정 온라인. 표준교재 {TEXTBOOK_CH}개 장으로 기초부터 거버넌스·법제·사례까지 공부하고
               온라인 이수 평가({EXAM[0]}문항, {EXAM[1]}점 이상)를 통과하면, <strong>한국AI윤리위원회 공식 이수증</strong>을 받고
               홈페이지에 AI윤리전문가로 공식 등록됩니다.</p>
            <div style="display:flex;gap:7px;flex-wrap:wrap">
              <span class="chip" style="background:rgba(255,255,255,.14);color:#DCE9FF">#위원회 공식 이수증</span>
              <span class="chip" style="background:rgba(255,255,255,.14);color:#DCE9FF">#홈페이지 공식 등록</span>
              <span class="chip" style="background:rgba(255,255,255,.14);color:#DCE9FF">#이력서 · 자기소개서 가이드</span>
              <span class="chip" style="background:rgba(255,255,255,.14);color:#DCE9FF">#취업 · 이직 · 직무</span>
            </div>
            <div class="price-line">
              <span class="price-list">정가 {won(LIST_PRICE)}</span>
              <span class="price-now">{won(PRICE)}</span>
              <span class="price-tag">특별가</span>
            </div>
            <div style="margin-top:4px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
              <a class="btn btn-white" href="{CERT_HREF}">{CERT_CTA} <i data-lucide="arrow-right"></i></a>
              <span style="font-size:12.5px;color:#AFC4E4">신청 완료 후 결제 페이지로 자동 연결</span>
            </div>
          </article>
          <aside class="one-course-side">
            <span class="one-course-side-t">이 금액에 모두 포함</span>
            <ul class="incl-list">{incl_html}</ul>
            <p class="one-course-side-n">결제 완료 후 학습자료 5종 내려받기 링크가 이메일로 발송되고, 같은 이메일이 [평가응시] 로그인 아이디가 됩니다.</p>
          </aside>
        </div>

        <div class="curri-block" id="curriculum">
          <div class="center" style="margin:54px 0 26px">
            <span class="eyebrow">Study Materials</span>
            <h2 class="h-sec">위원회가 직접 집필한 학습자료 5종</h2>
            <p class="h-sub" style="margin:0 auto">영상 진도율을 채우는 과정이 아닙니다. 결제 즉시 PDF 5종을 받아 원하는 속도로 공부하고, 준비되면 바로 응시합니다.</p>
          </div>
          <figure class="mat-figure reveal">
            <img src="assets/img/materials-5set.jpg" alt="AI윤리전문가 양성과정 학습자료 5종 표지: 00 이수 평가 응시 안내, 01 핵심이론, 02 실전 모의고사, 03 정답 및 해설, 04 실무 도구집" loading="lazy" width="3200" height="861">
          </figure>
          <ol class="lec-list">{mat_html}
          </ol>
          <div class="exam-grid exam-grid--one reveal">
            <div class="exam-card">
              <span class="exam-tag">이수 평가</span>
              <strong>온라인 이수 평가 {EXAM[0]}문항 · {EXAM_MIN}분</strong>
              <span>100점 만점에 <b>{EXAM[1]}점 이상</b>이면 이수 · 4지선다형 · 문항은 제공된 학습자료 범위에서만 출제 · 응시 기간 안 {RETAKE}</span>
            </div>
          </div>
          <p class="field-hint" style="margin-top:12px">학습자료 구성은 운영 상황에 따라 일부 조정될 수 있으며, 학습자료(PDF 5종)는 결제 완료 후 이메일로 발송되는 내려받기 링크로 받습니다.
             이수 평가는 학습 후 홈페이지 상단 <a href="exam.html" style="color:var(--blue);font-weight:700">[평가응시]</a>에서 로그인(아이디: 결제 이메일, 비밀번호: 휴대전화 번호 뒤 4자리)해 결제 후 {EXAM_WINDOW_DAYS}일 이내에 응시합니다.</p>
        </div>
        <div class="notice" style="margin-top:24px">
          <strong>위원회 주관 · 성균관컨설팅 운영:</strong> 본 과정은 한국AI윤리위원회(KAIEC)가 커리큘럼 구성부터 이수 평가, 이수증 발급, 이수자 공식 등록까지 직접 주관하고,
          성균관대학교 RISE사업 공식 지원기업인 성균관컨설팅(skkc.co.kr)이 접수·결제·수강 안내 등 교육 운영을 맡습니다.
          학습자료는 위원회 6개 분과 전문위원의 자문과 검토를 거쳐 집필되며, 교육비 결제 내역에는 '성균관컨설팅'으로 표기됩니다.
        </div>
      </div>
    </section>

    <section class="section section--gray" id="tutors">
      <div class="wrap">
        <div class="split" style="align-items:start">
          <div>
            <span class="eyebrow">Why It Matters</span>
            <h2 class="h-sec">이수증 한 장으로 끝나지 않습니다</h2>
            <p class="h-sub">이력서에 한 줄 더하는 것으로 끝나는 교육이 아닙니다. 위원회가 확인해 주는 이력, 바로 쓰는 실무 역량,
               그리고 규제가 만들어 내는 수요. 이 세 가지가 이수증의 값어치를 만듭니다.</p>
            <div class="worth-list">{worth_html}</div>
          </div>
          <div class="trust-col">
            <ul class="trust-list">
              <li><i data-lucide="award"></i><div><strong>한국AI윤리위원회 주관 · 공식 이수증 발급</strong><span>커리큘럼 구성, 이수 평가, 이수증 발급, 이수자 공식 등록까지 위원회가 직접 주관</span></div></li>
              <li><i data-lucide="badge-check"></i><div><strong>이수와 동시에 위원회 공식 등록</strong><span>이수번호가 부여된 이수증을 발급하고, 홈페이지에 공식 등록되어 검색됩니다</span></div></li>
              <li><i data-lucide="building-2"></i><div><strong>성균관대학교 RISE사업 공식 지원기업 성균관컨설팅 교육 운영</strong><span>접수·결제·수강 안내를 맡고, 교육비는 성균관컨설팅 안전결제로 처리</span></div></li>
              <li><i data-lucide="scale"></i><div><strong>이수 기준은 {EXAM[1]}점, 기준은 낮추지 않습니다</strong><span>대신 응시 기간 안에서는 기준에 이를 때까지 다시 응시하실 수 있습니다</span></div></li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="sample">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Sample Questions</span>
          <h2 class="h-sec">이수 평가는 이런 문항이 나옵니다</h2>
          <p class="h-sub" style="margin:0 auto">예시 문항 3개를 직접 풀어보세요. 보기를 누르면 정답과 해설이 바로 나옵니다.</p>
        </div>
        <div class="sq-list">{sq_html}</div>
        <p class="field-hint" style="text-align:center;margin-top:16px">예시 문항은 학습 내용의 방향을 보여주기 위한 것으로, 실제 평가 문항과 다를 수 있습니다.</p>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Who Should Apply</span>
          <h2 class="h-sec">이런 분께 추천합니다</h2>
        </div>
        <div class="grid grid-4">
          <article class="card reveal"><div class="card-icon"><i data-lucide="school"></i></div>
            <h3>취업준비생 · 대학(원)생</h3><p>경력이 없어도 이력서에 쓸 수 있는 전문 교육 이력입니다. AI 활용 능력에 '윤리'라는 차별화를 더하고, 자기소개서 문장까지 가이드로 받으세요.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="briefcase"></i></div>
            <h3>기업 실무자 · 관리자</h3><p>사내 AI 도입과 활용 기준을 만들어야 하는 분. 실무 도구집 양식으로 규제 대응의 첫 담당자가 되세요.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="graduation-cap"></i></div>
            <h3>강사 · 교사 · 교수자</h3><p>AI 윤리 교육 수요가 커지는 지금, 가르칠 수 있는 근거와 콘텐츠를 갖추고 전문위원 등록까지 이어 가세요.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="building-2"></i></div>
            <h3>공공 · 기관 종사자</h3><p>기관의 AI 활용 지침과 교육을 준비해야 하는 분께 실무 기준을 제공합니다.</p></article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Process</span>
          <h2 class="h-sec">수강·이수 절차</h2>
        </div>
        <div class="grid grid-3">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">양성과정 신청</h3><p style="font-size:14px">온라인 신청 후 안전결제로 교육비 납부</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">학습자료 수령</h3><p style="font-size:14px">이메일의 링크로 학습자료(PDF 5종) 내려받기</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">자율학습</h3><p style="font-size:14px">표준교재 · 실전 모의고사와 해설 별책</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">평가응시</h3><p style="font-size:14px">상단 <a href="exam.html" style="color:var(--blue);font-weight:700">[평가응시]</a>에서 로그인 · 결제 후 {EXAM_WINDOW_DAYS}일 이내</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 05</span><h3 style="font-size:16px">이수 기준 충족</h3><p style="font-size:14px">{EXAM[1]}점 이상<br>기준에 이를 때까지 재응시</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 06</span><h3 style="font-size:16px">이수증 · 공식 등록</h3><p style="font-size:14px">결과 확인 후 7일 이내 PDF 발급 · 홈페이지 공식 등록 · 활용 가이드 발송</p></div>
        </div>
        {pay_btns}
        <p class="field-hint" style="margin-top:18px;text-align:center">특별가 {won(PRICE)}(정가 {won(LIST_PRICE)}) · {HOOK_ZERO} · {HOOK_START}<br>
           교육비 결제는 성균관대학교 RISE사업 공식 지원기업 성균관컨설팅(skkc.co.kr)의 안전결제로 처리되며, 결제 내역에는 '성균관컨설팅'으로 표기됩니다.</p>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">FAQ</span>
          <h2 class="h-sec">자주 묻는 질문</h2>
        </div>
        <details class="acc">
          <summary>전공이나 경력이 없어도 수강할 수 있나요?</summary>
          <div class="acc-body">네. AI윤리전문가 양성과정은 전공·경력 제한이 없습니다. 생성형 AI를 사용해 본 경험이 있다면
            누구나 시작하실 수 있으며, 표준교재가 개념과 기초부터 다루므로 사전 지식이 없어도 충분히 따라올 수 있습니다.</div>
        </details>
        <details class="acc">
          <summary>취업준비생인데 실제로 도움이 되나요?</summary>
          <div class="acc-body">경력이 없는 분일수록 이력서에 쓸 수 있는 '근거 있는 한 줄'이 귀합니다. 이수하면 한국AI윤리위원회 공식 이수증(이수번호 기재)이 발급되고
            홈페이지에 공식 등록되어 검색되므로, 인사담당자가 바로 확인할 수 있는 이력이 됩니다.
            여기에 이수자 전용 <strong>이력서·자기소개서 활용 가이드</strong>로 어느 칸에 어떻게 쓰는지, 자기소개서 문장 예시와 면접에서 답하는 포인트까지 함께 드립니다.
            AI기본법 시행 이후 기업·기관이 'AI를 윤리적으로 다룰 줄 아는 사람'을 찾기 시작한 지금, 가장 빠르게 준비할 수 있는 스펙입니다.</div>
        </details>
        <details class="acc">
          <summary>학습과 평가는 모두 온라인인가요?</summary>
          <div class="acc-body">네. 학습자료(PDF 5종) 제공부터 이수 평가, 이수증 발급까지 전 과정이 온라인으로 진행됩니다.
            정해진 수업 시간이 없어 자료를 받은 날부터 원하는 속도로 공부할 수 있고, 준비가 되면 홈페이지 상단 [평가응시]에서 바로 응시합니다. 직장·학업과 병행하기 쉬운 구조입니다.</div>
        </details>
        <details class="acc">
          <summary>과정이 하나뿐인가요? 심화 내용은 어디에 있나요?</summary>
          <div class="acc-body">네, 하나의 과정입니다. 표준교재 한 권에 AI 윤리의 이해와 국제 규범, 핵심 쟁점, 제도화(제1~6장)부터
            AI 거버넌스·윤리영향평가 실무, 국내외 AI 법제, 사례 분석과 조직 실무(제7~9장)까지 이어지도록 구성해, 별도 과정을 추가로 결제하지 않아도 전문 영역까지 공부할 수 있습니다.
            이수 평가는 {EXAM[0]}문항으로 제공된 학습자료 범위에서만 출제되고, 이수 기준은 {EXAM[1]}점입니다.</div>
        </details>
        <details class="acc">
          <summary>이수증은 어떤 문서이고 어떻게 활용할 수 있나요?</summary>
          <div class="acc-body">한국AI윤리위원회가 주관하는 전문 교육과정을 수강하고 이수 평가를 통과했음을 증명하는 위원회의 공식 문서로, 이수번호가 부여되어 위원회 홈페이지에 공식 등록됩니다.
            국가가 인정하는 자격 제도와는 별개의 교육 이력으로, 이력서·포트폴리오의 교육·연수 항목에
            "{RESUME_KO} ({RESUME_NO})"로, 영문 이력서에는 "{PROG_EN} ({RESUME_NO})"로 기재하실 수 있습니다.
            이수 후 전문위원 등록을 신청해 등록되면 홈페이지 프로필 주소를 함께 제시할 수 있고, 전문강사·자문, Fellowship·캠페인 등 실제 활동 기회와 연계됩니다.</div>
        </details>
        <details class="acc">
          <summary>이력서·자기소개서 활용 가이드는 무엇인가요?</summary>
          <div class="acc-body">이수자에게만 드리는 안내 자료입니다. 이수 이력을 이력서의 어느 칸에 어떤 표기로 쓰는지(국문·영문), 자기소개서에서 AI 윤리 역량을 어떻게 문장으로 풀어내는지의 예시,
            면접에서 "AI를 어디까지 어떻게 써야 하는가"를 질문받았을 때 답하는 포인트를 정리했습니다. 이수증 발급과 함께 이메일로 보내 드립니다.</div>
        </details>
        <details class="acc">
          <summary>교육비 결제는 어떻게 하나요?</summary>
          <div class="acc-body">교육비는 성균관대학교 RISE사업 공식 지원기업인 성균관컨설팅(skkc.co.kr)의 안전결제(신용카드·간편결제)로
            납부하실 수 있습니다. 신청을 완료하면 결제 페이지로 자동 연결되며, 결제 내역에는 '성균관컨설팅'으로 표기됩니다.
            카드전표 등 결제 증빙은 결제 시 발급됩니다.</div>
        </details>
        <details class="acc">
          <summary>교육비는 얼마이고, 무엇이 포함되나요?</summary>
          <div class="acc-body">교육비는 정가 {won(LIST_PRICE)}에서 특별가 {won(PRICE)}입니다.
            비용에는 공식 학습자료(PDF) 5종, 온라인 이수 평가와 재응시, 이수증 발급, 홈페이지 공식 등록, 이력서·자기소개서 활용 가이드가 모두 포함됩니다.</div>
        </details>
        <details class="acc">
          <summary>이수 평가는 어떻게 응시하나요?</summary>
          <div class="acc-body">학습을 마친 뒤 홈페이지 상단 <a href="exam.html" style="color:var(--blue);font-weight:600">[평가응시]</a>에서 로그인해 응시합니다.
            아이디는 결제 때 입력한 이메일, 비밀번호는 결제 때 입력한 휴대전화 번호 뒤 4자리이며, 결제 후 {EXAM_WINDOW_DAYS}일 이내에 응시할 수 있습니다.
            {EXAM[0]}문항 4지선다형이고 시험 시간 {EXAM_MIN}분은 [시험 시작]을 누른 때부터 흐릅니다. 100점 만점에 {EXAM[1]}점 이상이면 이수입니다.
            문항은 제공된 학습자료 범위에서만 출제되므로 표준교재와 실전 모의고사를 충실히 보면 충분히 준비할 수 있습니다.</div>
        </details>
        <details class="acc">
          <summary>한 번에 통과하지 못하면 어떻게 되나요?</summary>
          <div class="acc-body">이수 기준({EXAM[1]}점)은 누구에게도 낮춰 드리지 않습니다. 대신 <strong>응시 기간({EXAM_WINDOW_DAYS}일) 안에서는 기준에 이를 때까지 다시 응시</strong>하실 수 있습니다.
            한 번의 시험으로 사람을 가르는 것이 목적이 아니라, 기준에 이른 분에게만 위원회 이름으로 이수를 확인해 드리는 것이 목적이기 때문입니다.
            제출 즉시 영역별 점수가 표시되므로 부족한 부분만 다시 보신 뒤 이어서 응시하시면 됩니다.</div>
        </details>
        <details class="acc">
          <summary>이수증은 언제 어떻게 받나요?</summary>
          <div class="acc-body">{EXAM[1]}점 이상이면 결과 화면에서 바로 이수가 확정되고, <strong>한국AI윤리위원회 홈페이지에 공식 등록</strong>됩니다. 확인 후 7일 이내에 「{DOC_FULL}」(PDF)과 이력서·자기소개서 활용 가이드를 신청하신 이메일로 발급합니다.
            이수증에는 이수번호가 부여되며, 이후 위원회를 통해 이수 사실을 확인할 수 있습니다. 전문위원 등록 신청 방법도 함께 안내합니다.
            기타 문의는 <a href="mailto:{EMAIL}" style="color:var(--blue);font-weight:600">{EMAIL}</a>로 보내주세요.</div>
        </details>
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="cta-band reveal">
          <div>
            <h2>올해 안에, 이력서에 AI윤리전문가 한 줄을 더하세요</h2>
            <p>위원회 표준교재와 온라인 이수 평가로 한국AI윤리위원회 공식 이수증과 홈페이지 공식 등록까지. {HOOK_ZERO}으로, 결제 당일 바로 학습을 시작할 수 있습니다.</p>
          </div>
          <div class="btns">
            <a class="btn btn-white" href="{CERT_HREF}">{CERT_CTA}</a>
            <a class="btn btn-light" href="mailto:{EMAIL}">문의하기</a>
          </div>
        </div>
      </div>
    </section>"""

    def course_ld(name, desc, price, url):
        return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "{name}",
  "description": "{desc}",
  "provider": {{"@type": "Organization", "name": "{SITE_NAME}", "url": "{SITE_URL}/"}},
  "inLanguage": "ko-KR",
  "educationalCredentialAwarded": "{DOC_FULL} ({SITE_NAME})",
  "offers": {{
    "@type": "Offer",
    "price": "{price}",
    "priceCurrency": "KRW",
    "availability": "https://schema.org/InStock",
    "url": "{url}"
  }},
  "hasCourseInstance": {{
    "@type": "CourseInstance",
    "courseMode": "online"
  }}
}}
</script>
"""
    ld = course_ld("AI윤리전문가 양성과정",
                   f"한국AI윤리위원회가 주관하는 AI윤리전문가 양성과정. 위원회 표준교재 등 학습자료 5종(PDF)과 온라인 이수 평가({EXAM[0]}문항, {EXAM[1]}점 이상)로 위원회 공식 이수증을 발급하고 이수자를 홈페이지 홈페이지에 공식 등록합니다. 이력서·자기소개서 활용 가이드 제공.",
                   PRICE, f"{SITE_URL}{url_for('expert-apply.html')}")
    sq_js = """  <script>
  (function(){
    document.querySelectorAll('.sq').forEach(function(q){
      var ans=parseInt(q.getAttribute('data-answer'),10), done=false;
      q.querySelectorAll('.sq-opt').forEach(function(b){
        b.addEventListener('click',function(){
          if(done)return; done=true;
          var i=parseInt(b.getAttribute('data-i'),10);
          b.classList.add(i===ans?'is-right':'is-wrong');
          q.querySelector('.sq-opt[data-i="'+ans+'"]').classList.add('is-right');
          q.querySelectorAll('.sq-opt').forEach(function(x){x.disabled=true;});
          q.querySelector('.sq-exp').hidden=false;
        });
      });
    });
  })();
  </script>
"""
    page("expert.html", "AI윤리전문가 양성과정",
         f"한국AI윤리위원회 주관 AI윤리전문가 양성과정. 위원회 표준교재 등 학습자료 5종과 온라인 이수 평가로 공식 이수증을 받고 홈페이지에 공식 등록됩니다. 이력서·자기소개서 활용 가이드 제공. {HOOK_ZERO}.",
         body, extra_head=ld, extra_script=sq_js, sticky="all",
         keywords=["AI윤리전문가", "AI윤리전문가 양성과정", "AI 윤리 교육 이수증", "AI 윤리 전문가 과정", "AI 윤리 교육", "AI기본법",
                   "AI 컴플라이언스", "인공지능 윤리 전문가", "생성형 AI 교육", "AI 리터러시", "AI 거버넌스", "취업 스펙"])


# -------------------------------------------------------- expert-apply.html
def build_expert_apply():
    """AI윤리전문가 양성과정 수강 신청 폼 (자체 코딩 · 전환·자기설득 중심 개편 2026.09, 양성과정 표기 2026.09.14)
    - 2026.09.21 통합: 과정 선택 섹션을 없애고(과정 하나) 과정 요약 카드 → 수강 목적(자기설득) → 수강자 정보 → 절차·이수 평가 안내 → 개인정보 동의 → 결제
    - 2026.09.22 간소화(구입 유도율): 필수 체크는 개인정보 동의 하나만. 절차 확인 체크와 청약철회 확인 섹션은 이탈 요인이라 폼에서 뺐고(청약철회 조건은 terms.html#refund 와 결제 페이지에서 고지),
      그 자리에 '결제가 왜 성균관컨설팅으로 넘어가는지'를 짧게 설득하는 블록을 넣음. 머리글 통계는 STAT_71(리더 71%가 경력보다 AI 역량), 홈페이지 공식 등록을 머리글·완료 화면에 다시 강조
    - 제출 시 시트 웹훅으로 접수 기록 + 위원회 알림 메일, 완료 화면에서 결제 페이지로 자동 이동"""
    PURPOSES = [
        "이력서와 포트폴리오에 AI 윤리 전문 교육 이력(이수증)을 추가하고 싶습니다.",
        "AI 역량을 증명할 공식 이수증(이수번호 · 홈페이지 공식 등록)을 갖고 싶습니다.",
        "취업·이직 경쟁력을 높이는 데 활용하고 싶습니다.",
        "현재 직무에서 AI 윤리 역량을 활용하고 싶습니다.",
        "기업·기관의 AI 윤리·컴플라이언스 관련 업무에 활용하고 싶습니다.",
        "무분별한 AI 활용의 문제와 위험성에 관심이 있어 올바른 AI 활용과 윤리를 배우고 싶습니다.",
        "AI 윤리 전문강사·교육 활동에 관심이 있습니다.",
        "책임 있는 AI 활용 문화 확산과 AI 윤리 활동에 참여하고 싶습니다.",
        "연구·교육 분야의 전문 이력으로 활용하고 싶습니다.",
        "AI 윤리 분야로 전문 활동 영역을 확장하고 싶습니다.",
        "기타",
    ]
    PURPOSE_ITEMS = "".join(
        f'<label class="check-item"><input type="checkbox" name="purpose" value="{p}">'
        f'<span class="check-box"></span><span>{p}</span></label>' for p in PURPOSES)
    JOBS = "".join(
        f'<label><input type="radio" name="job" value="{j}"><span>{j}</span></label>' for j in [
        "대학생·대학원생", "기업·기관 재직자", "교사·강사", "교수·연구자",
        "취업준비생", "프리랜서·전문직", "사업자·기업 대표", "기타"])
    USE_CARDS = [
        ("award", "위원회 공식 이수증", "고유 이수번호가 기재된 「AI윤리전문가 양성과정 이수증」(PDF) 발급"),
        ("file-search", "홈페이지 공식 등록 · 검색", "이수와 동시에 위원회 홈페이지에 공식 등록되어 기업·기관이 바로 확인"),
        ("pen-line", "이력서 · 자기소개서 활용 가이드", "이수 이력 표기법과 자기소개서 문장 예시, 면접 답변 포인트를 정리한 이수자 전용 가이드"),
        ("user-check", "전문위원 등록 신청 자격", "이수 후 전문위원 등록을 신청하면 홈페이지 프로필 공개, 전문강사·자문 활동으로 확장"),
    ]
    USE_HTML = "".join(
        f'<div class="use-card"><i data-lucide="{ic}"></i><strong>{t}</strong><span>{d}</span></div>'
        for ic, t, d in USE_CARDS)

    body = f"""    <section class="section gform-bg">
      <div class="gform-wrap">

        <div class="gform-card gform-head">
          <span class="gform-kicker">한국AI윤리위원회 주관 · AI윤리전문가 양성과정</span>
          <h1>AI윤리전문가 양성과정 수강 신청</h1>
          <p class="gform-lead">2026년, 기업·기관의 AI 활용 확대와 함께 ‘AI 윤리 전문가’의 역할이 커지고 있습니다.</p>
          <p>생성형 AI가 기업·기관·학교의 실제 업무 전반으로 확산되면서 저작권, 개인정보, 정보보안,
             할루시네이션, 편향과 차별, 결과물의 신뢰성과 책임까지 AI 윤리는 중요한 전문 영역으로 자리 잡고 있습니다.</p>
          <p>AI윤리전문가 양성과정은 이러한 변화에 필요한 AI 윤리 지식과 실무 판단 역량을 위원회 표준교재로 체계적으로 배우고 온라인 이수 평가로 확인하여,
             이력서와 커리어에 한국AI윤리위원회 공식 「{DOC_FULL}」을 더하는 전문 교육과정입니다.</p>
          <p>이수와 동시에 <strong>위원회 홈페이지에 AI윤리전문가로 공식 등록</strong>되어 이름과 이수번호로 검색되므로, 기업·기관이 바로 확인할 수 있는 이력이 됩니다.
             이력서·자기소개서 활용 가이드와 전문위원 등록 신청 자격까지 함께 드립니다.</p>
          <div class="gform-callout"><i data-lucide="trending-up"></i>
            <div><strong>{STAT_71["head"]}</strong><br>
                 {STAT_71["body"]}
                 <small class="src">{STAT_71["src"]}</small></div></div>
          <p class="gform-org-note">한국AI윤리위원회 주관 · 성균관컨설팅 교육 운영(접수·결제)</p>
        </div>

        <form id="examForm" novalidate>

          <div class="gform-card" id="secCourse">
            <div class="gform-sec">SECTION 1</div>
            <h2>신청 과정</h2>
            <p class="gform-desc">과정은 하나입니다. 따로 고르실 것 없이 아래 내용을 확인하고 다음 항목으로 넘어가 주세요.</p>
            <div class="choice-list">
              <div class="choice is-fixed">
                <span class="choice-radio is-on" aria-hidden="true"></span>
                <span class="choice-body">
                  <span class="choice-badge">{HOOK_ZERO} · {HOOK_REG}</span>
                  <strong>AI윤리전문가 양성과정</strong>
                  <span>위원회 표준교재 등 학습자료 5종(PDF)으로 공부하고 온라인 이수 평가({EXAM[0]}문항, {EXAM[1]}점 이상)를 통과하면
                    한국AI윤리위원회 공식 이수증 발급, 홈페이지 공식 등록, 이력서·자기소개서 활용 가이드까지 한 번에. 전공·경력 제한 없이 전 과정 온라인</span>
                  <span class="apply-price">
                    <span class="ap-badge">특별가</span>
                    <span class="ap-now">{won(PRICE)}</span>
                    <span class="ap-was">정가 {won(LIST_PRICE)}</span>
                  </span>
                  <span class="choice-note">학습자료 5종 + 온라인 이수 평가 {EXAM[0]}문항 + 공식 이수증 + 홈페이지 공식 등록 + 활용 가이드</span>
                </span>
              </div>
            </div>
            <figure class="mat-figure mat-figure--sm">
              <img src="assets/img/materials-5set.jpg" alt="결제 즉시 받는 학습자료 5종 표지: 이수 평가 응시 안내, 핵심이론, 실전 모의고사, 정답 및 해설, 실무 도구집" loading="lazy" width="3200" height="861">
            </figure>
          </div>

          <div class="gform-card" id="secPurpose">
            <div class="gform-sec">SECTION 2</div>
            <h2>수강 및 활용 목적 <span class="req">*</span></h2>
            <p class="gform-desc">AI윤리전문가 양성과정에 관심을 갖게 된 이유와 활용 목적을 선택해 주세요. 복수 선택할 수 있습니다.</p>
            <div class="check-grid" id="purposeGrid">{PURPOSE_ITEMS}</div>
            <p class="err-msg">활용 목적을 하나 이상 선택해 주세요.</p>
          </div>

          <div class="gform-card" id="secInfo">
            <div class="gform-sec">SECTION 3</div>
            <h2>수강자 정보</h2>
            <div class="gform-fields">
              <div class="field" id="fName">
                <label for="f-name">성명 <span class="req">*</span></label>
                <input id="f-name" type="text" name="name" autocomplete="name" placeholder="홍길동">
                <p class="err-msg">성명을 입력해 주세요.</p>
              </div>
              <div class="field" id="fEmail">
                <label for="f-email">이메일 주소 <span class="req">*</span></label>
                <input id="f-email" type="email" name="email" autocomplete="email" placeholder="example@email.com">
                <p class="field-hint">학습자료(PDF 5종)가 발송되는 이메일입니다. 결제 때에도 같은 이메일을 입력해 주세요(이수 평가 로그인 아이디가 됩니다).
                   실제 사용하시는 이메일 주소를 정확하게 입력해 주세요.</p>
                <p class="err-msg">이메일 주소를 정확히 입력해 주세요.</p>
              </div>
              <div class="field" id="fJob">
                <label>현재 직업 또는 활동 분야 <span class="req">*</span></label>
                <div class="pill-choice">{JOBS}</div>
                <p class="err-msg">직업 또는 활동 분야를 선택해 주세요.</p>
              </div>
            </div>
          </div>

          <div class="gform-card" id="secFlow">
            <div class="gform-sec">SECTION 4</div>
            <h2>교육 및 이수 평가 안내</h2>
            <p class="gform-desc">신청과 결제, 학습과 평가까지 모두 온라인으로 진행됩니다.</p>
            <ol class="gform-flow">
              <li>양성과정 신청 (수강 신청 · 교육비 결제)</li>
              <li>학습자료 확인</li>
              <li>자율학습 (표준교재 · 실전 모의고사)</li>
              <li>평가응시 (홈페이지 상단 [평가응시])</li>
              <li>이수 기준 충족 ({EXAM[1]}점 이상)</li>
              <li class="is-final">이수증 발급 · 홈페이지 공식 등록 · 활용 가이드 발송</li>
            </ol>
            <p class="gform-body">결제가 끝나면 학습자료(PDF 5종) 내려받기 링크가 이메일로 발송되고, 같은 이메일이 <b>[평가응시] 아이디</b>가 됩니다(비밀번호는 휴대전화 번호 뒤 4자리).</p>
            <div class="exam-info">
              <div><span>평가 구성</span>{EXAM[0]}문항 · 4지선다형 · 시험 시간 {EXAM_MIN}분</div>
              <div><span>이수 기준</span><b>100점 만점에 {EXAM[1]}점 이상</b></div>
              <div><span>재응시</span>응시 기간({EXAM_WINDOW_DAYS}일) 안에서 기준에 이를 때까지</div>
            </div>

            <div class="use-block">
              <div class="use-block-title"><i data-lucide="award"></i> 이수하면 받는 것</div>
              <div class="use-grid">{USE_HTML}</div>
            </div>
          </div>

          <div class="gform-card" id="secPay">
            <div class="gform-sec">SECTION 5</div>
            <h2>교육비 결제는 성균관컨설팅에서</h2>
            <p class="gform-desc">신청서를 제출하면 결제 페이지가 성균관컨설팅(skkc.co.kr)으로 연결됩니다. 한국AI윤리위원회의 공식 교육 운영사이니 그대로 진행하시면 됩니다.</p>
            <div class="gform-privacy">
              <div><span>역할</span>위원회는 표준교재 집필, 이수 평가, 이수증 발급, 홈페이지 공식 등록을 직접 주관하고, 접수·결제·수강 안내 등 운영은 공식 교육 운영사 성균관컨설팅이 맡습니다</div>
              <div><span>운영사</span>성균관대학교 RISE사업 공식 지원기업 · 한국AI윤리위원회 회원사 (결제 내역과 카드 명세서에는 '성균관컨설팅'으로 표기)</div>
              <div><span>결제</span>안전결제(신용카드 · 간편결제) · 결제 증빙 발급 · 결제 확인 즉시 학습자료 5종 자동 발송, 같은 이메일이 [평가응시] 아이디</div>
            </div>
            <p class="field-hint" style="margin-top:14px">신청과 결제 조건은 <a href="terms.html" style="color:var(--blue);font-weight:700">서비스 이용안내</a>를 따릅니다.</p>
          </div>

          <div class="gform-card" id="secPriv">
            <div class="gform-sec">SECTION 6</div>
            <h2>개인정보 수집·이용 동의</h2>
            <div class="gform-privacy">
              <div><span>수집항목</span>성명, 이메일, 직업·활동 분야, 수강 및 활용 목적, 신청정보</div>
              <div><span>이용목적</span>수강자 확인, 교육 및 이수 평가 운영, 이수자 관리 및 이수증 발급, 기관 요청 시 이수 사실 확인 회신</div>
              <div><span>보유기간</span>수집일로부터 3년. 이수자 명부는 이수 사실 확인을 위해 보관하며, 삭제를 요청하시면 즉시 파기합니다</div>
            </div>
            <label class="agree"><input type="checkbox" name="privok"><span class="agree-box"></span>
              <span>개인정보 수집·이용에 동의합니다. <span class="req">*</span></span></label>
            <p class="err-msg">개인정보 수집·이용 동의에 체크해 주세요.</p>
            <p class="field-hint" style="margin-top:14px">자세한 내용은 <a href="privacy.html" style="color:var(--blue);font-weight:700">개인정보·운영정책</a>을 확인해 주세요.</p>
          </div>

          <div class="gform-card gform-submit">
            <h2>AI윤리전문가 양성과정 수강 신청</h2>
            <p>이력서에 한 줄, 한국AI윤리위원회 공식 이수증과 홈페이지 공식 등록 이력을 더하세요.</p>
            <div class="pay-summary pay-summary--one">
              <div class="pay-mini"><div class="lv">AI윤리전문가 양성과정 · 이수증 + 홈페이지 공식 등록 + 활용 가이드</div>
                <div class="list">정가 {won(LIST_PRICE)}</div><div class="sale">특별가 {won(PRICE)}</div></div>
            </div>
            <p>신청서를 제출한 후 교육비 결제를 완료하면 수강 등록이 최종 확정됩니다.</p>
            <button type="submit" class="btn btn-primary gform-submit-btn">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></button>
            <p class="err-msg" id="topErr">입력하지 않은 필수 항목이 있습니다. 표시된 항목을 확인해 주세요.</p>
            <div class="trust-row">
              <div><i data-lucide="award"></i> 한국AI윤리위원회 공식 이수증</div>
              <div><i data-lucide="shield-check"></i> 성균관컨설팅 안전결제</div>
              <div><i data-lucide="building-2"></i> 성균관대 RISE사업 공식 지원</div>
            </div>
          </div>
        </form>

        <div class="gform-card gform-done" id="doneView" hidden>
          <div class="done-icon"><i data-lucide="check"></i></div>
          <h2>신청이 접수되었습니다</h2>
          <p class="done-lead">이제 <strong>교육비 결제</strong> 한 단계만 남았습니다.</p>
          <div class="done-pay">
            <div class="done-pay-head"><i data-lucide="shield-check"></i>
              <div><strong>성균관컨설팅 안전결제로 연결됩니다</strong>
                <span>위원회 교육 운영사 · 성균관대학교 RISE사업 공식 지원기업</span></div>
            </div>
            <a id="payBtn" class="btn btn-primary" hidden>교육비 결제하기 <i data-lucide="credit-card"></i></a>
            <p id="payCount" class="gform-count" hidden><strong>3</strong>초 후 자동으로 이동합니다</p>
            <p id="payWait" class="gform-paywait" hidden>결제 안내는 작성하신 이메일로 보내드립니다.</p>
          </div>
          <p class="gform-paynote">결제 때 입력하신 이메일과 휴대전화 번호 뒤 4자리가 그대로 [평가응시] 로그인 정보가 됩니다. 결제 확인 즉시 학습자료 5종이 발송되고, 이수하면 위원회 홈페이지에 AI윤리전문가로 공식 등록됩니다.</p>
          <div class="done-mailbox" id="mailBox">
            <p><strong>신청 내용 전송 안내</strong><br>자동 접수가 되지 않았다면 아래 신청 내용을 복사해
               <a href="mailto:{EMAIL}">{EMAIL}</a> 으로 보내주세요.</p>
            <textarea id="doneCopy" readonly aria-label="전송 내용 사본" tabindex="-1"></textarea>
            <button type="button" class="btn btn-ghost" id="copyBtn">신청 내용 복사</button>
          </div>
        </div>

      </div>
    </section>"""

    script = r"""
  <script>
  (function(){
    var form=document.getElementById('examForm');
    /* 2026.09.21 통합: 과정이 하나라 선택이 없습니다. 접수 시트의 '과정' 칸에는 아래 값이 그대로 기록됩니다 */
    var COURSE='__COURSE__';
    var PAYLINK='__PAY__';

    function bad(id,on){document.getElementById(id).classList.toggle('is-invalid',!!on);return !!on;}
    function v(n){var el=form.querySelector('[name='+n+']');return (el&&el.value?el.value:'').trim();}
    function purposes(){return Array.prototype.slice.call(form.querySelectorAll('[name=purpose]:checked')).map(function(x){return x.value;});}

    form.addEventListener('submit',function(e){
      e.preventDefault();
      var job=form.querySelector('[name=job]:checked');
      var pz=purposes();
      bad('secPurpose',pz.length===0);
      bad('fName',!v('name'));
      bad('fEmail',!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v('email')));
      bad('fJob',!job);
      bad('secPriv',!form.querySelector('[name=privok]').checked);
      var first=document.querySelector('.is-invalid');
      document.getElementById('topErr').style.display=first?'block':'none';
      if(first){first.scrollIntoView({behavior:'smooth',block:'center'});return;}

      var pstr=pz.join(', ');
      var lines=[
        '한국AI윤리위원회 AI윤리전문가 양성과정 수강 신청','',
        '■ 신청 과정 : '+COURSE,
        '■ 성명 : '+v('name'),
        '■ 이메일 : '+v('email'),
        '■ 직업/활동 분야 : '+job.value,
        '■ 수강 및 활용 목적 : '+pstr,'',
        '■ 개인정보 수집·이용 : 동의','',
        '--- kaiec.kr AI윤리전문가 양성과정 신청 페이지에서 작성됨 ---'
      ];

      /* 접수 데이터 전송: 시트 웹훅으로 GET 전송(주소에 데이터), 없으면 메일 앱 폴백 */
      var HOOK='__HOOK__';
      if(HOOK){
        var qs='course='+encodeURIComponent(COURSE)+'&name='+encodeURIComponent(v('name'))
             +'&email='+encodeURIComponent(v('email'))+'&job='+encodeURIComponent(job.value)
             +'&purpose='+encodeURIComponent(pstr)+'&t='+Date.now();
        var url=HOOK+'?'+qs; var ok=false;
        try{fetch(url,{mode:'no-cors',keepalive:true,cache:'no-store'});ok=true;}catch(e1){}
        if(!ok){try{var im=new Image();im.src=url;}catch(e2){}}
        document.getElementById('mailBox').hidden=true;
      }else{
        var mail='mailto:__FEMAIL__?subject='+encodeURIComponent('[AI윤리전문가 양성과정 신청] '+v('name'))
                +'&body='+encodeURIComponent(lines.join('\n'));
        setTimeout(function(){location.href=mail;},400);
      }

      /* 완료 화면 표시 */
      form.hidden=true;
      var done=document.getElementById('doneView'); done.hidden=false;
      document.getElementById('doneCopy').value=lines.join('\n');
      window.scrollTo({top:done.getBoundingClientRect().top+window.pageYOffset-90,behavior:'smooth'});

      /* 결제 페이지 자동 이동 (3초 카운트다운, 버튼으로 즉시 이동 가능) */
      var link=PAYLINK||'';
      if(link){
        var pb=document.getElementById('payBtn'); pb.href=link; pb.hidden=false;
        var pc=document.getElementById('payCount'); pc.hidden=false;
        var num=pc.querySelector('strong'); var cnt=3; num.textContent=cnt;
        var tick=setInterval(function(){
          cnt--;
          if(cnt<=0){clearInterval(tick);location.href=link;}
          else{num.textContent=cnt;}
        },1000);
        pb.addEventListener('click',function(){clearInterval(tick);});
      }else{
        document.getElementById('payWait').hidden=false;
      }
    });

    document.getElementById('copyBtn').addEventListener('click',function(){
      var t=document.getElementById('doneCopy'); t.select();
      var ok=false;
      try{ok=document.execCommand('copy');}catch(err){}
      if(navigator.clipboard){navigator.clipboard.writeText(t.value).catch(function(){});ok=true;}
      this.textContent=ok?'복사되었습니다':'복사 후 붙여넣어 주세요';
      var b=this; setTimeout(function(){b.textContent='신청 내용 복사';},2200);
    });
  })();
  </script>
""".replace('__FEMAIL__', EMAIL).replace('__PAY__', PAY_URL).replace('__HOOK__', SHEET_WEBHOOK).replace('__COURSE__', PROG)

    page("expert-apply.html", "AI윤리전문가 양성과정 수강 신청",
         "한국AI윤리위원회 주관 AI윤리전문가 양성과정 수강 신청 페이지입니다. 수강자 정보를 입력하면 결제 페이지로 연결되고, 결제 후 학습자료와 이수 평가 안내를 받습니다.",
         body, extra_script=script,
         keywords=["AI윤리전문가 양성과정 신청", "AI윤리전문가 수강 신청", "AI 윤리 교육 신청", "AI 윤리 이수증", "한국AI윤리위원회"])


# ---------------------------------------------------------------- experts.html
def build_experts():
    """KAIEC 공식 AI윤리전문가: '기업·기관이 원하는 스펙'과 '올해 이거 하나는 땄다'는 성취감을 훅으로 양성과정 신청으로 이끄는 페이지 (2026.09.15 카피 개편)
    - 2026.09.21 통합: 과정 하나. 이수 = 위원회 공식 이수증 + 홈페이지 공식 등록(검색) + 활용 가이드, 이수 후 전문위원 등록 신청 자격
    - 명단은 assets/js/experts-data.js 의 KAIEC_EXPERTS 배열로 관리. 비어 있으면 '공식 등록 혜택' 카드와 안내만, 있으면 명부 검색 상자와 카드 목록 표시
    - 무료 대안(KAIEC 참여) 카드는 신청 이탈을 유발해 넣지 않음 (2026.09.13 결정)"""
    APPLY = "expert-apply.html"
    WHY = [
        ("2026.1", "AI기본법 시행", "AI를 만드는 기업뿐 아니라 활용하는 기업·기관도 책임의 주체가 됩니다."),
        ("2026.8", "EU AI Act 투명성 의무 발효", "해외 거래·수출 기업에 AI 윤리·컴플라이언스 기준이 요구됩니다."),
        ("45.3%", "시장 규모 연평균 성장 전망", "AI 윤리·거버넌스는 가장 빠르게 커지는 전문 영역입니다. <small class=\"src\">출처: MarketsandMarkets, AI Governance Market 2024~2029 (CAGR 45.3%)</small>"),
    ]
    MOMENTS = [
        ("file-search", "“생성형 AI로 만든 보고서, 고객에게 그대로 보내도 될까?”", "저작권·기밀·할루시네이션을 판단할 사람이 필요합니다."),
        ("graduation-cap", "“학생 과제의 AI 활용, 어디까지 허용해야 할까?”", "학교와 교육 현장은 기준을 세우고 지도할 사람을 찾습니다."),
        ("shield-check", "“우리 조직에 AI를 도입하면 개인정보·편향 문제는 없을까?”", "도입 전 위험 점검과 내부 교육을 맡을 사람이 필요합니다."),
        ("briefcase", "“AI를 윤리적으로 다룰 줄 안다는 걸 이력서에서 어떻게 보여줄까?”", "말이 아니라 위원회 공식 이수증과 공식 등록 이력으로 보여줄 수 있어야 합니다."),
    ]
    USES = [
        ("briefcase", "이력서·포트폴리오", f"교육·연수 칸에 「한국AI윤리위원회 {PROG} 이수」 한 줄. 위원회 공식 등록이 뒷받침합니다."),
        ("shield-check", "기업·기관 AI 컴플라이언스", "AI 활용 가이드라인 수립, 위험 점검, 내부 교육. 조직의 AI 기준을 맡을 사람이 됩니다."),
        ("school", "취업·이직·승진", "자기소개서와 면접에서 'AI를 윤리적으로 다룰 줄 안다'를 근거 있게 말할 수 있습니다."),
        ("graduation-cap", "연구·교육 경력", "대학·연구기관의 교육·연구 활동에 AI 윤리 전문 이력으로 씁니다."),
        ("users", "위원회 활동 참여", "캠페인, 콘텐츠 제작, Fellowship 등 위원회 공식 활동에 참여합니다."),
        ("trending-up", "커리어 확장", "AI 윤리·거버넌스 분야로 직무를 넓히는 발판. <small class=\"adv-note\">전문위원 등록을 신청하면 전문강사·자문 활동까지</small>"),
    ]
    PATH = [
        ("AI윤리전문가 양성과정 이수",
         f"위원회 표준교재 등 학습자료 5종(PDF)으로 공부하고, 온라인 이수 평가({EXAM[0]}문항, {EXAM[1]}점 이상)를 통과합니다. 전공·경력 제한 없이 전 과정 온라인.",
         ["위원회 표준교재 5종", "온라인 이수 평가", "위원회 공식 이수증"]),
        ("홈페이지 공식 등록",
         "이수 즉시 한국AI윤리위원회 홈페이지에 AI윤리전문가로 등록되고 검색됩니다. 공식 이수증(이수번호)과 활용 가이드를 받습니다.",
         ["홈페이지 공식 등록 · 검색", "이수번호 부여", "활용 가이드"]),
        ("스펙으로, 활동으로 확장",
         "취업·이직·현재 직무에 바로 쓰고, 위원회 캠페인·Fellowship에 참여합니다. <small class=\"adv-note\">전문위원 등록을 신청해 등록되면 프로필 공개, 전문강사·자문 활동</small>",
         ["취업 · 이직 · 직무", "위원회 활동 참여", "전문위원 등록 신청"]),
    ]
    FAQ = [
        ("AI윤리전문가 양성과정은 왜 중요한가요?",
         "2026년 AI기본법 시행과 EU AI Act 적용으로 기업·기관·학교 모두 AI를 윤리적으로 쓸 기준과 사람을 요구받고 있습니다. "
         "그 역량을 위원회 표준교재로 배우고, 한국AI윤리위원회 공식 이수증과 홈페이지 공식 등록으로 증명하는 과정입니다."),
        ("AI나 윤리를 전공하지 않았는데 괜찮을까요?",
         "네. 전공·경력 제한이 없고, 표준교재가 기초부터 다룹니다. AI를 업무나 학업에 쓰고 있다면 이미 출발선에 서 있습니다."),
        ("위원회 공식 등록은 어떻게 되나요?",
         "이수 기준을 충족하면 별도 절차 없이 홈페이지에 AI윤리전문가로 등록되어 검색되고, 이수번호가 기재된 공식 이수증(PDF)과 활용 가이드가 발급됩니다. "
         "이후 전문위원 등록을 신청하면 심사를 거쳐 프로필이 공개되고 전문강사·자문 활동이 가능합니다."),
        ("경력이나 소속이 없어도 괜찮나요?",
         "네. 취업·이직 준비 중이어도 제한이 없습니다. 소속은 원할 때만 표기합니다."),
        ("이수 평가 기준에 못 미치면 어떻게 되나요?",
         f"응시 기간 안에서는 이수 기준({EXAM[1]}점)에 이를 때까지 다시 응시할 수 있습니다. 문항은 제공된 학습자료 범위에서만 출제됩니다."),
    ]
    REG = [
        ("file-search", "홈페이지 공식 등록 · 검색", "이수 즉시 등록. 이름과 이수번호로 누구나 검색할 수 있습니다."),
        ("award", "위원회 공식 이수증", f"이수번호가 기재된 「{DOC_FULL}」(PDF). 이력서에 그대로 씁니다."),
        ("shield-check", "위원회가 직접 확인", "기업·기관·학교가 문의하면 위원회가 등록 사실을 확인해 드립니다."),
    ]
    # 2026.09.22 What Is It 통계 띠: 'AI 역량 이력'이 직무 불문 필수가 됐음을 보여 주는 수치(출처는 섹션 하단 field-hint)
    STATS = [
        ("70%↑", "AI 리터러시 요구 채용 공고", "1년 새 70% 넘게 증가. 직무를 가리지 않고 AI 역량을 요구합니다. <small class=\"src\">LinkedIn Skills on the Rise 2026</small>"),
        ("46%", "국내 면접관의 2026 우선 과제", "면접관 열 명 중 다섯 명이 'AI 리터러시(이해·활용 능력) 검증'을 꼽았습니다. <small class=\"src\">한국바른채용인증원, 면접관 414명</small>"),
        ("71%", "경력보다 AI 역량을 먼저 보는 리더", "AI 역량이 없는 경력자보다 AI 역량을 갖춘 저경력자를 뽑겠다는 리더가 71%. <small class=\"src\">Microsoft · LinkedIn 2024 Work Trend Index</small>"),
    ]
    stat_html = "".join(
        f'<div><strong>{n}</strong><b>{t}</b><span>{d}</span></div>' for n, t, d in STATS)
    why_html = "".join(
        f'<div><strong>{n}</strong><b>{t}</b><span>{d}</span></div>' for n, t, d in WHY)
    moments_html = "".join(
        f'<div class="moment"><i data-lucide="{ic}"></i><div><strong>{q}</strong><span>{a}</span></div></div>'
        for ic, q, a in MOMENTS)
    uses_html = "".join(
        f'<article class="card reveal"><div class="card-icon"><i data-lucide="{ic}"></i></div><h3>{t}</h3><p>{d}</p></article>'
        for ic, t, d in USES)
    path_html = "".join(
        f'<div class="path-card reveal"><span class="path-num">0{i}</span><h3>{t}</h3><p>{d}</p>'
        f'<div class="chips">{"".join(f"<span class=chip>{c}</span>" for c in chips)}</div></div>'
        for i, (t, d, chips) in enumerate(PATH, 1))
    reg_html = "".join(
        f'<div class="card center reveal"><div class="card-icon" style="margin:0 auto 14px"><i data-lucide="{ic}"></i></div><h3 style="font-size:17px">{t}</h3><p>{d}</p></div>'
        for ic, t, d in REG)
    faq_html = "".join(
        f'<details class="acc"><summary>{q}</summary><div class="acc-body">{a}</div></details>' for q, a in FAQ)

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; AI윤리전문가</p>
        <span class="hl-pill"><i data-lucide="badge-check"></i>기업·기관이 원하는 스펙 · 한국AI윤리위원회 공식 등록</span>
        <h1>KAIEC 공식 AI윤리전문가</h1>
        <p class="ph-lead" style="max-width:900px">올해 이력서에 새로 채울 한 줄, <b class="t">AI윤리전문가</b>.<br>
           AI가 기본이 된 시대, 차이는 ‘전문가’라는 이력에서 시작됩니다.</p>
        <p class="ph-body">한국AI윤리위원회 표준교재로 공부하고 온라인 이수 평가를 통과하면 끝. AI윤리전문가 공식 이수증을 받고,<br>
           <strong>홈페이지에 AI윤리전문가로 공식 등록</strong>됩니다.</p>
        <div class="btns" style="margin-top:22px">
          <a class="btn btn-primary" href="{APPLY}">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-light" href="#what">AI윤리전문가란?</a>
        </div>
      </div>
    </section>

    <section class="section" id="why">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Why Now</span>
          <h2 class="h-sec">2026년, 가장 빠르게 떠오르는 스펙 <span class="hot-tag">HOT</span></h2>
          <p class="h-sub" style="margin:0 auto">AI기본법 시행, EU AI Act 적용, 시장 연평균 45.3% 성장.
             기업·기관·학교가 지금 가장 급하게 찾는 사람이 <strong>AI윤리전문가</strong>입니다.</p>
        </div>
        <div class="why-row">{why_html}</div>
        <div class="split" style="align-items:start;margin-top:34px">
          <div class="story">
            <h3>왜 지금 이렇게 뜨거운가</h3>
            <p>기업은 사내 AI 기준을 세울 사람을, 학교는 학생의 AI 활용을 지도할 사람을, 공공기관은 도입 전 위험을 점검할 사람을 찾기 시작했습니다.</p>
            <p>그런데 이 역량을 증명한 사람은 아직 소수입니다. 먼저 준비한 사람이 첫 자리를 차지합니다. 지금이 그때입니다.</p>
            <a class="btn btn-primary" href="{APPLY}">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
          </div>
          <div class="moment-list">
            <div class="moment-title">이런 순간에 AI윤리전문가가 필요합니다</div>
            {moments_html}
          </div>
        </div>
      </div>
    </section>

    <section class="section section--gray" id="what">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">What Is It</span>
          <h2 class="h-sec">AI윤리전문가란, 누구나 갖고 싶은 AI 역량 이력입니다</h2>
          <p class="h-sub" style="margin:0 auto">AI를 잘 쓰는 사람은 많습니다. 기업이 찾는 사람은 AI의 결과를 검증하고 <strong>책임 있게 쓸 줄 아는 사람</strong>입니다.
             그 역량을 한국AI윤리위원회가 확인해 준 이력이 AI윤리전문가입니다. 전공·경력 제한 없이, 전 과정 100% 온라인으로 시작합니다.</p>
        </div>
        <div class="why-row">{stat_html}</div>
        <div class="split" style="align-items:start;margin-top:34px">
          <div class="story reveal">
            <h3>기업이 말하는 'AI 역량'은 프롬프트 실력이 아닙니다</h3>
            <p>한국고용정보원은 2026년 직장인의 필수 역량으로 AI 리터러시를 꼽으면서, 그 뜻을 <strong>"AI의 결과를 이해하고 검증하며 책임 있게 활용하는 판단 역량"</strong>이라고 설명합니다.
               링크드인이 집계한 채용 공고에서 AI 리터러시를 요구하는 자리는 1년 새 70% 넘게 늘었고, 국내 면접관 열 명 중 다섯 명은 2026년 채용의 우선 과제로 AI 리터러시 검증을 꼽았습니다.</p>
            <p>저작권, 개인정보, 환각, 편향. AI를 쓰는 모든 자리에서 매일 마주치는 문제 앞에 "이건 되고, 이건 안 된다"를 근거 있게 말할 수 있는 판단력이 바로 그 역량이고, 그것이 AI 윤리입니다.
               직무도, 전공도, 경력도 가리지 않습니다. AI를 쓰는 사람이면 누구에게나 필요한 이력입니다.</p>
            <p>그 역량을 위원회 표준교재로 배우고 온라인 이수 평가로 확인하면, 한국AI윤리위원회가 AI윤리전문가로 공식 등록하고 이력서의 한 줄을 위원회가 뒷받침합니다.</p>
            <a class="btn btn-primary" href="{APPLY}">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
            <p class="field-hint" style="margin-top:14px">출처: 아시아경제 「2026년, 직장인은 무엇을 준비해야 하는가」(2026.1, 한국고용정보원 김동규 연구위원) · LinkedIn Skills on the Rise 2026 · 한국바른채용인증원 「2026 채용 트렌드」(면접관 414명, 2025.12) · Microsoft · LinkedIn 2024 Work Trend Index(31개국 31,000명)</p>
          </div>
          <div class="worth-list reveal" style="margin-top:0">
            <div class="worth"><span class="worth-no">01</span><div class="worth-ic"><i data-lucide="users"></i></div>
              <div class="worth-b"><strong>누구의 이력인가</strong>
                <p>기획·마케팅·개발·영업·교육·공공·연구, 그리고 취업준비생과 대학생까지. AI를 업무나 학업에 쓰는 사람이면 누구나 갖는 AI 역량 이력입니다.</p>
                <div class="chips"><span class="chip">직무 불문</span><span class="chip">전공 무관</span><span class="chip">경력 무관</span></div></div></div>
            <div class="worth"><span class="worth-no">02</span><div class="worth-ic"><i data-lucide="shield-check"></i></div>
              <div class="worth-b"><strong>무엇을 증명하는가</strong>
                <p>AI 결과를 검증하고 저작권·개인정보·환각·편향 위험을 판단해 책임 있게 활용할 수 있다는 것. 위원회 표준교재와 온라인 이수 평가로 확인합니다.</p>
                <div class="chips"><span class="chip">결과 검증</span><span class="chip">위험 판단</span><span class="chip">책임 있는 활용</span></div></div></div>
            <div class="worth"><span class="worth-no">03</span><div class="worth-ic"><i data-lucide="award"></i></div>
              <div class="worth-b"><strong>어떻게 남는가</strong>
                <p>학습자료부터 이수 평가까지 전 과정 100% 온라인. 이수하면 공식 이수증(이수번호)과 KAIEC 홈페이지 공식 등록, 이력서·자기소개서 활용 가이드가 남고, 이력서와 면접, 사내 AI 기준 수립에 바로 씁니다.</p>
                <div class="chips"><span class="chip">100% 온라인</span><span class="chip">공식 이수증</span><span class="chip">홈페이지 공식 등록</span><span class="chip">활용 가이드</span></div></div></div>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="value">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Career Value</span>
          <h2 class="h-sec">“올해 스펙은, 이거 하나로 확실합니다”</h2>
          <p class="h-sub" style="margin:0 auto">KAIEC 공식 AI윤리전문가 이력은 이렇게 쓰입니다.</p>
        </div>
        <div class="grid grid-3" style="margin-bottom:26px">{uses_html}</div>
{resume_box()}
      </div>
    </section>

    <section class="section section--gray" id="path">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Your Path</span>
          <h2 class="h-sec">KAIEC 공식 AI윤리전문가가 되는 길</h2>
          <p class="h-sub" style="margin:0 auto">양성과정 이수, 홈페이지 공식 등록, 커리어 활용. 세 단계면 됩니다.</p>
        </div>
        <div class="path-grid">{path_html}</div>
      </div>
    </section>

    <section class="section" id="list">
      <div class="wrap">
        <div class="center" style="margin-bottom:34px">
          <span class="eyebrow">Official Registration</span>
          <h2 class="h-sec">한국AI윤리위원회 AI윤리전문가 등록</h2>
          <p class="h-sub" style="margin:0 auto">이수와 동시에 홈페이지에 공식 등록되고, 누구나 검색할 수 있습니다. <span id="expertCount"></span></p>
        </div>
        <!-- 등록 조회 (2026.09.23): 등록자가 없어도 항상 보이는 공식 조회 패널. "따면 여기서 검색하면 나온다"가 바로 읽히도록 예시 카드를 같이 둠 -->
        <div class="reg-lookup" id="regLookup">
          <div class="rl-main">
            <span class="rl-kicker">REGISTRY LOOKUP</span>
            <h3>AI윤리전문가 등록 조회</h3>
            <p>성명 또는 이수번호를 입력하면 한국AI윤리위원회 공식 등록 여부를 바로 확인할 수 있습니다.</p>
            <form class="rl-form" role="search" onsubmit="return false">
              <i data-lucide="search"></i>
              <input type="search" id="regQ" placeholder="성명 또는 이수번호 (예: KAIEC-E-2026-0001)" aria-label="AI윤리전문가 등록 조회" autocomplete="off">
              <button type="button" id="regBtn">조회</button>
            </form>
            <div class="rl-meta"><span id="regN"></span><span id="regHint">이수 확정과 함께 등록되어 이 화면에서 바로 검색됩니다</span></div>
          </div>
          <div class="rl-sample" id="regSample">
            <span class="rl-sample-tag">등록 카드 예시</span>
            <div class="member expert">
              <div class="member-avatar">홍</div>
              <div class="member-role">KAIEC 공식 AI윤리전문가</div>
              <div class="member-name">홍길동</div>
              <div class="expert-no">이수번호 KAIEC-E-2026-0001</div>
              <div class="member-field">AI 윤리 · 실무 활용</div>
              <div class="expert-since">이수 즉시 등록</div>
            </div>
            <p>이수 평가를 통과하면 이런 카드가 바로 만들어져 검색에 나타납니다.</p>
          </div>
        </div>
        <div class="member-grid" id="expertGrid" hidden></div>
        <div class="grid grid-3" style="margin-top:34px">{reg_html}</div>
        <p class="field-hint expert-adv-note" id="expertEmpty" hidden>이수자는 이수 확정과 함께 이 자리에 공개됩니다. 전문위원으로 등록되면 프로필이 함께 표시됩니다.</p>
      </div>
    </section>

    <section class="section offer-sec" id="start">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Get Started</span>
          <h2 class="h-sec">지금 시작하세요</h2>
          <p class="h-sub" style="margin:0 auto">양성과정 이수가 KAIEC 공식 AI윤리전문가로 가는 첫걸음입니다.</p>
        </div>
        <div class="start-one">
          <div class="offer-card reveal">
            <div class="offer-top">
              <span class="offer-quota">{HOOK_ZERO} · {HOOK_REG}</span>
            </div>
            <h3>AI윤리전문가 양성과정</h3>
            <p>올해 이력서에 AI윤리전문가 한 줄을 더하는 가장 빠른 길. 표준교재와 온라인 이수 평가만으로 공식 이수증, 홈페이지 공식 등록, 활용 가이드까지 한 번에.</p>
            <div class="price-line price-line--light">
              <span class="price-list">정가 {won(LIST_PRICE)}</span>
              <span class="price-now">{won(PRICE)}</span>
              <span class="price-tag">특별가</span>
            </div>
            <ul class="offer-list">
              <li>학습자료 5종(PDF) + 온라인 이수 평가 · 전 과정 온라인</li>
              <li>전공·경력 제한 없음 · 이수 기준 {EXAM[1]}점(기준에 이를 때까지 재응시)</li>
              <li>공식 이수증 + 홈페이지 공식 등록 + 이력서·자기소개서 활용 가이드</li>
            </ul>
            <div class="offer-btns">
              <a class="btn btn-primary" href="{APPLY}">AI윤리전문가 양성과정 신청하기 <i data-lucide="arrow-right"></i></a>
              <a class="btn btn-ghost" href="expert.html">과정 자세히 보기</a>
            </div>
            <small class="adv-note">이수 후 전문위원 등록을 신청하면 프로필 공개, 전문강사·자문 활동으로 이어집니다.</small>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:24px">
          <span class="eyebrow">FAQ</span>
          <h2 class="h-sec">자주 묻는 질문</h2>
        </div>
        {faq_html}
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="cta-band">
          <div><h2>올해 안에, 이력서에 AI윤리전문가 한 줄을 더하세요</h2>
            <p>표준교재와 온라인 이수 평가로 공식 이수증과 홈페이지 공식 등록까지. {HOOK_ZERO}으로 진행됩니다.</p></div>
          <div class="btns">
            <a class="btn btn-white" href="{APPLY}">AI윤리전문가 양성과정 신청하기</a>
            <a class="btn btn-light" href="expert.html">양성과정 안내</a>
          </div>
        </div>
      </div>
    </section>"""

    script = """  <script src="assets/js/experts-data.js"></script>
  <script>
  (function(){
    var list=window.KAIEC_EXPERTS||[];
    var grid=document.getElementById('expertGrid'),empty=document.getElementById('expertEmpty'),cnt=document.getElementById('expertCount');
    var q=document.getElementById('regQ'),nEl=document.getElementById('regN'),btn=document.getElementById('regBtn');
    var lookup=document.getElementById('regLookup'),sample=document.getElementById('regSample'),hint=document.getElementById('regHint');
    function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
    if(!list.length){
      /* 게시된 등록자가 없을 때: 조회 패널과 예시 카드는 그대로, 검색어를 넣으면 '일치하는 등록자 없음' 안내 */
      empty.hidden=false;
      function idle(){var t=q.value.trim(); nEl.textContent=t?'일치하는 등록자 없음':''; if(t){hint.textContent='성명과 이수번호를 다시 확인해 주세요.';}else{hint.textContent='이수 확정과 함께 등록되어 이 화면에서 바로 검색됩니다';}}
      q.addEventListener('input',idle); btn.addEventListener('click',idle);
      return;
    }
    cnt.textContent='(등록 '+list.length+'명)';
    sample.hidden=true; lookup.classList.add('reg-lookup--single'); hint.textContent='현재 '+list.length+'명 등록 · 이수 즉시 자동 등록';
    function card(m){
      var av=m.photo?'<div class="member-avatar member-avatar--photo"><img src="assets/img/experts/'+esc(m.photo)+'" alt="'+esc(m.name)+'" loading="lazy"></div>'
        :'<div class="member-avatar">'+esc((m.name||'?').replace(/[^가-힣A-Za-z]/g,'').slice(0,1)||'·')+'</div>';
      var tags=(m.tags||[]).map(function(t){return '<span class="chip">'+esc(t)+'</span>';}).join('');
      var role=m.expert?'KAIEC 공식 AI윤리전문가 · 전문위원':'KAIEC 공식 AI윤리전문가';
      return '<div class="member expert">'+av
        +'<div class="member-role">'+role+'</div>'
        +'<div class="member-name">'+esc(m.name)+'</div>'
        +(m.no?'<div class="expert-no">이수번호 '+esc(m.no)+'</div>':'')
        +'<div class="member-field">'+esc(m.field||'')+(m.org?'<br>'+esc(m.org):'')+'</div>'
        +(tags?'<div class="expert-tags">'+tags+'</div>':'')
        +(m.since?'<div class="expert-since">'+esc(m.since)+' 등록</div>':'')
        +'</div>';
    }
    function render(term){
      var t=(term||'').replace(/\s+/g,'').toLowerCase();
      var rows=t?list.filter(function(m){return ((m.name||'')+(m.no||'')).replace(/\s+/g,'').toLowerCase().indexOf(t)>=0;}):list;
      grid.innerHTML=rows.length?rows.map(card).join(''):'<p class="ex-empty" style="grid-column:1/-1;text-align:center;color:var(--gray-500)">일치하는 등록자가 없습니다.</p>';
      nEl.textContent=t?rows.length+'명':'';
    }
    render('');
    grid.hidden=false;
    q.addEventListener('input',function(){render(q.value);});
    btn.addEventListener('click',function(){render(q.value);});
  })();
  </script>
"""
    page("experts.html", "KAIEC 공식 AI윤리전문가",
         f"올해 이력서에 더할 한 줄, AI윤리전문가. 위원회 표준교재와 온라인 이수 평가로 한국AI윤리위원회 공식 이수증을 받고 홈페이지에 AI윤리전문가로 공식 등록되는 길을 안내합니다.",
         body, extra_script=script, sticky="all",
         keywords=["AI윤리전문가", "AI 윤리 전문가 등록", "AI윤리전문가 양성과정", "AI 윤리 스펙", "AI 윤리 강사", "한국AI윤리위원회"])


# ---------------------------------------------------------------- join.html
def build_join():
    """위원 참여(2026.09.25 개편): AI 윤리 캠페인위원 모집이 핵심. 참여 구분은 캠페인위원 · 운영위원 · 전문위원 · 공식 파트너(기관·기업·학교) 넷으로 줄이고,
    위촉 문서 대신 '홈페이지 공식 위원 명단 등재'를 혜택으로 내세움(위촉 증서는 발급하지 않음). 직업 선택은 문턱을 낮추고, 지원 동기·자기소개 예시는 캠페인(온라인 알리기) 중심
    - 허들 최소화: 필수는 참여 구분·성명·이메일·직업·지원 동기(체크)·동의뿐, 자기소개는 선택(예시 문장 칩), 소속은 '적기' 버튼을 누른 분만(공식 파트너 선택 시 기관명 칸 자동 표시)
    - 히어로·역할 카드의 [캠페인위원 지원하기] 류 버튼은 data-pick 으로 신청서의 참여 구분을 미리 고르고 #apply 로 이동(?type= 딥링크도 유지)
    - 접수 데이터는 수강 신청과 같은 시트 웹훅(SHEET_WEBHOOK)으로 POST 전송(type=join) → 앱스 스크립트가 '위원 신청' 탭에 기록"""
    ROLES = [
        # (아이콘, 구분명, 배지, 이런 분께, 주요 역할, 강조)
        ("megaphone", "AI 윤리 캠페인위원", "누구나 · 추천",
         "SNS·블로그·커뮤니티를 쓰는 분이면 누구나. 전공·경력·나이 제한 없음",
         "위원회가 만든 AI 윤리 캠페인 콘텐츠를 온라인에 알리고, 올바른 AI 활용 문화를 확산하는 활동 (온라인·재택)", True),
        ("briefcase", "운영위원", "위원회 운영",
         "위원회 사업과 캠페인, 행사를 함께 기획하고 운영하고 싶은 분",
         "사업 기획, 프로그램 운영, 캠페인위원 활동 지원", False),
        ("monitor-play", "전문위원", "양성과정 이수자",
         "AI윤리전문가 양성과정을 이수하고 AI 윤리 교육·자문 활동에 참여하고자 하는 분 (전공·학위 제한 없음)",
         "AI 윤리 교육·전문강사 활동, 자문, 캠페인 콘텐츠 감수", False),
        ("handshake", "공식 파트너", "기관 · 기업 · 학교",
         "AI 윤리 캠페인·교육을 함께할 기업, 공공기관, 대학·학교, 교육기관, 단체",
         "공동 캠페인·교육 프로그램 운영, 협력 협약(MOU), 홈페이지 공식 파트너 명단 등재", False),
    ]
    ROLE_ITEMS = "".join(
        f'<label class="choice choice--role{" choice--hot" if hot else ""}"><input type="radio" name="jtype" value="{name}"><span class="choice-radio"></span>'
        f'<span class="choice-body"><span class="choice-badge">{badge}</span><strong><i data-lucide="{ic}"></i>{name}</strong>'
        f'<span><em>이런 분께</em> {who}</span><span><em>주요 역할</em> {role}</span></span></label>'
        for ic, name, badge, who, role, hot in ROLES)
    JOBS = "".join(
        f'<label><input type="radio" name="job" value="{j}"><span>{j}</span></label>' for j in [
        "대학생·대학원생", "취업준비생", "직장인", "프리랜서·자영업",
        "교사·강사·연구자", "기업·기관 담당자", "주부·은퇴자", "기타"])
    MOTIVES = [
        "AI 윤리 활동을 온라인(SNS·블로그·커뮤니티)에 알리는 캠페인에 참여하고 싶습니다.",
        "무분별한 AI 사용의 문제를 알리고 올바른 활용 문화를 확산하고 싶습니다.",
        "이력서·포트폴리오에 넣을 수 있는 공식 위원 활동 경력이 필요합니다.",
        "한국AI윤리위원회 홈페이지 공식 위원 명단에 이름을 올리고 싶습니다.",
        "재택·온라인으로 시간 부담 없이 의미 있는 활동을 하고 싶습니다.",
        "AI 윤리 전문가·기관과의 네트워크를 넓히고 싶습니다.",
        "교육·강의·자문 등 전문 활동 기회를 얻고 싶습니다.",
        "위원회 사업과 캠페인을 함께 기획·운영하고 싶습니다.",
        "기관·기업·학교 차원에서 AI 윤리 캠페인·교육 협력을 추진하고 싶습니다.",
        "기타",
    ]
    MOTIVE_ITEMS = "".join(
        f'<label class="check-item"><input type="checkbox" name="motive" value="{m}">'
        f'<span class="check-box"></span><span>{m}</span></label>' for m in MOTIVES)
    BENEFITS = [
        ("id-card", "홈페이지 공식 위원 명단 등재", "위촉되면 한국AI윤리위원회 홈페이지의 공식 위원 명단에 성명이 등록됩니다. 누구나 확인할 수 있는 공식 기록이라 이력서·포트폴리오·프로필에 바로 씁니다."),
        ("file-check", "활동증명서 발급", "활동 실적에 따라 위원회가 활동 기간과 내역을 담은 활동증명서를 발급합니다. 대외활동 증빙으로 활용할 수 있습니다."),
        ("monitor-play", "온라인·재택 활동", "SNS·블로그 공유부터 콘텐츠 참여까지 모든 활동이 온라인으로 진행되어 학업·직장과 병행할 수 있습니다."),
        ("trending-up", "커리어가 되는 활동", "AI기본법 시행 이후 기업·기관·학교가 요구하는 AI 윤리 이력을 실제 활동으로 만듭니다."),
        ("gift", "활동 인센티브", "캠페인 활동 실적에 따른 활동지원금과 위원회 양성과정·교육 프로그램 우대를 제공합니다."),
        ("users", "전문가 네트워크", "AI 윤리·교육·기업 실무 전문가, 공식 파트너 기관과 교류하며 활동 영역을 넓힙니다."),
    ]
    benefits_html = "".join(
        f'<article class="card reveal"><div class="card-icon"><i data-lucide="{ic}"></i></div><h3>{t}</h3><p>{d}</p></article>'
        for ic, t, d in BENEFITS)
    WANT = ["SNS·블로그·커뮤니티 활동을 하는 누구나", "취업·이직을 준비하며 공식 활동 경력이 필요한 분",
            "대학생·대학원생·취업준비생", "직장인·프리랜서·자영업자", "AI를 자주 활용하며 올바른 기준을 함께 알리고 싶은 분"]
    want_html = "".join(f'<span class="chip"><i data-lucide="check"></i>{w}</span>' for w in WANT)
    DO = [
        ("megaphone", "캠페인 콘텐츠 알리기", "위원회가 만든 AI 윤리 카드뉴스·짧은 글·행사 소식을 내 SNS·블로그·커뮤니티에 공유합니다. 만들 필요 없이 알리기만 하면 됩니다."),
        ("pen-line", "올바른 활용 기준 전하기", "보고서·과제·회의록에 AI를 쓸 때 지켜야 할 기준과 무분별한 사용의 문제를 주변에 전합니다. 전문 지식이 필요한 일이 아닙니다."),
        ("clock", "가볍게, 꾸준히", "주 1~2시간이면 충분합니다. 활동 방법과 자료는 위촉 후 온라인으로 안내하고, 활동 실적은 활동증명서와 인센티브로 돌려드립니다."),
    ]
    do_html = "".join(
        f'<article class="card reveal"><span class="card-num">0{i}</span><div class="card-icon"><i data-lucide="{ic}"></i></div><h3>{t}</h3><p>{d}</p></article>'
        for i, (ic, t, d) in enumerate(DO, 1))
    OTHERS = [
        ("briefcase", "운영위원", "위원회 사업·캠페인·행사를 함께 기획하고 운영합니다. 경력 요건 없음"),
        ("monitor-play", "전문위원", "AI윤리전문가 양성과정 이수자가 교육·자문·콘텐츠 감수로 참여합니다"),
        ("handshake", "공식 파트너", "기업·공공기관·대학·학교·교육기관이 캠페인과 교육을 함께합니다"),
    ]
    others_html = "".join(
        f'<a class="join-item" href="#apply" data-pick="{n}"><span class="join-icon"><i data-lucide="{ic}"></i></span>'
        f'<span class="join-body"><strong>{n}</strong><span>{d}</span></span><span class="join-go">신청 <i data-lucide="arrow-right"></i></span></a>'
        for ic, n, d in OTHERS)
    AFTER = [
        ("신청 접수", "제출 즉시 접수되고 위원회에 알림이 전달됩니다."),
        ("위원회 검토", "신청 내용을 검토합니다 (보통 3~5일)."),
        ("위촉 안내 · 명단 등재", "이메일로 위촉 결과와 활동 안내를 보내고, 홈페이지 공식 위원 명단에 성명을 등록합니다."),
        ("활동 시작", "온라인 안내에 따라 캠페인 콘텐츠 공유 등 역할에 맞는 활동을 시작합니다."),
    ]
    after_html = "".join(
        f'<div class="card center reveal" style="padding:24px 16px"><span class="card-num">STEP {i:02d}</span>'
        f'<h3 style="font-size:16px">{t}</h3><p style="font-size:13.5px">{d}</p></div>'
        for i, (t, d) in enumerate(AFTER, 1))
    FAQ = [
        ("경력이나 전공이 없어도 참여할 수 있나요?",
         "네. AI 윤리 캠페인위원은 전공·경력·나이에 관계없이 SNS·블로그·커뮤니티를 쓰는 분이면 누구나 참여할 수 있습니다. "
         "운영위원도 경력 요건이 없고, 전문위원만 AI윤리전문가 양성과정 이수자를 대상으로 합니다."),
        ("캠페인위원은 구체적으로 무엇을 하나요?",
         "위원회가 만든 AI 윤리 캠페인 콘텐츠(카드뉴스·짧은 글·행사 소식)를 본인의 SNS·블로그·커뮤니티에 공유하고, "
         "무분별한 AI 사용의 문제와 올바른 활용 기준을 주변에 알리는 활동입니다. 활동 방법과 자료는 위촉 후 온라인으로 안내합니다."),
        ("참여에 비용이 드나요?",
         "개인 위원 참여(캠페인위원·운영위원·전문위원)에는 가입비·교육비 등 어떠한 비용도 없습니다. 공식 파트너 협력은 내용에 따라 별도로 협의합니다."),
        ("활동 시간은 얼마나 필요한가요? 직장·학업과 병행할 수 있나요?",
         "대부분의 활동이 온라인으로 진행되며 주 1~2시간 정도로도 참여할 수 있습니다. 위촉 후 본인 상황에 맞는 활동을 함께 정합니다."),
        ("위촉되면 무엇을 받나요?",
         "홈페이지 공식 위원 명단에 성명이 등록되고, 활동 실적에 따라 활동증명서를 발급합니다. 캠페인 활동 실적에 따른 활동지원금과 위원회 양성과정·교육 프로그램 우대도 있습니다."),
        ("신청 후 언제, 어떻게 연락을 받나요?",
         "제출 후 보통 3~5일 안에 작성하신 이메일로 검토 결과와 활동 안내를 보내드립니다."),
    ]
    faq_html = "".join(
        f'<details class="acc"><summary>{q}</summary><div class="acc-body">{a}</div></details>' for q, a in FAQ)

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; 위원 참여</p>
        <span class="join-eyebrow">JOIN KAIEC · 위원 참여</span>
        <h1>AI 윤리를 온라인에 알리는 사람, <br class="br-pc">AI 윤리 캠페인위원을 모집합니다</h1>
        <p>보고서도 과제도 회의록도 AI로 만드는 시대, 무분별한 AI 사용을 막고 바르게 활용하는 문화는 알리는 사람이 많을수록 빨리 퍼집니다.
           한국AI윤리위원회(KAIEC)의 AI 윤리 캠페인위원은 SNS·블로그·커뮤니티에서 올바른 AI 활용을 알리는 온라인 활동입니다.
           전공·경력·나이 제한 없이, 비용 없이 참여하고, 위촉되면 홈페이지 공식 위원 명단에 이름이 오릅니다.</p>
        <div class="hero-hooks">
          <span><i data-lucide="check"></i>전공·경력·나이 무관</span>
          <span><i data-lucide="check"></i>100% 온라인·재택</span>
          <span><i data-lucide="check"></i>참여 비용 없음</span>
          <span><i data-lucide="check"></i>홈페이지 공식 위원 명단 등재</span>
          <span><i data-lucide="check"></i>활동증명서 · 활동 인센티브</span>
        </div>
        <div class="btns" style="margin-top:24px">
          <a class="btn btn-primary" href="#apply" data-pick="AI 윤리 캠페인위원">캠페인위원 지원하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-light" href="#why">위원 혜택 보기</a>
        </div>
      </div>
    </section>

    <section class="section" id="do">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Campaign Member</span>
          <h2 class="h-sec">캠페인위원은 이런 활동을 합니다</h2>
          <p class="h-sub" style="margin:0 auto">콘텐츠를 만드는 일이 아니라 알리는 일입니다. 위원회가 자료를 만들고, 위원은 온라인에서 퍼뜨립니다.</p>
        </div>
        <div class="grid grid-3">{do_html}</div>
      </div>
    </section>

    <section class="section section--gray" id="why">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Why KAIEC</span>
          <h2 class="h-sec">위원으로 활동하면</h2>
          <p class="h-sub" style="margin:0 auto">AI기본법 시행과 함께 기업·기관·학교 모두가 AI 윤리를 요구받는 지금,
             위원회 활동은 관심을 이력과 전문성으로 바꾸는 가장 빠른 방법입니다.</p>
        </div>
        <div class="grid grid-3">{benefits_html}</div>
        <div class="want-box">
          <strong>이런 분을 기다립니다</strong>
          <div class="chips">{want_html}</div>
        </div>
      </div>
    </section>

    <section class="section" id="others">
      <div class="wrap-narrow">
        <div class="join-group-head">
          <h3>운영위원 · 전문위원 · 공식 파트너도 함께합니다</h3>
          <p>캠페인위원 외에 세 가지 참여 경로가 있습니다. 누르면 신청서의 참여 구분이 미리 선택됩니다.</p>
        </div>
        <div class="join-grid join-grid--3">{others_html}</div>
      </div>
    </section>

    <section class="section section--gray" id="apply">
      <div class="gform-wrap">
        <form id="joinForm" novalidate>
          <div class="gform-card gform-head">
            <span class="gform-kicker">JOIN KAIEC · 위원 참여 신청</span>
            <h2 class="gform-title">위원 참여 신청서</h2>
            <p class="gform-lead">한국AI윤리위원회와 함께 올바른 AI 활용 문화를 온라인에 알릴 분을 모십니다.</p>
            <p>AI 윤리 캠페인위원을 중심으로 운영위원·전문위원, 그리고 기관·기업·학교의 공식 파트너를 모십니다.
               제출하시면 위원회가 검토 후 이메일로 안내드리며, 신청과 활동 과정에서 가입비·교육비 등 어떠한 비용도 요구하지 않습니다.</p>
            <p class="gform-org-note">한국AI윤리위원회 사무국 접수 · 검토 후 개별 안내</p>
          </div>

          <div class="gform-card" id="secType">
            <div class="gform-sec">SECTION 1</div>
            <h2>참여 구분 <span class="req">*</span></h2>
            <p class="gform-desc">참여를 희망하는 역할을 하나 선택해 주세요. 처음이라면 AI 윤리 캠페인위원을 추천합니다.</p>
            <div class="choice-list">{ROLE_ITEMS}</div>
            <p class="field-hint">전문위원은 AI윤리전문가 양성과정 이수자를 대상으로 합니다.
               아직 이수하지 않았다면 <a href="expert-apply.html" style="color:var(--blue);font-weight:700">AI윤리전문가 양성과정 신청하기</a>에서 먼저 준비하거나, AI 윤리 캠페인위원으로 시작할 수 있습니다.</p>
            <p class="err-msg">참여 구분을 선택해 주세요.</p>
          </div>

          <div class="gform-card" id="secInfo">
            <div class="gform-sec">SECTION 2</div>
            <h2>지원자 정보</h2>
            <div class="gform-fields">
              <div class="field" id="fName">
                <label for="f-name">성명 (공식 파트너는 담당자 성명) <span class="req">*</span></label>
                <input id="f-name" type="text" name="name" autocomplete="name" placeholder="홍길동">
                <p class="err-msg">성명을 입력해 주세요.</p>
              </div>
              <div class="field" id="fEmail">
                <label for="f-email">이메일 주소 <span class="req">*</span></label>
                <input id="f-email" type="email" name="email" autocomplete="email" placeholder="example@email.com">
                <p class="field-hint">검토 결과와 활동 안내가 발송되는 이메일입니다. 실제 사용하시는 주소를 정확하게 입력해 주세요.</p>
                <p class="err-msg">이메일 주소를 정확히 입력해 주세요.</p>
              </div>
              <div class="field" id="fPhone">
                <label for="f-phone">휴대전화 번호 <span class="field-opt">(선택)</span></label>
                <input id="f-phone" type="tel" name="phone" inputmode="numeric" placeholder="010-1234-5678">
                <p class="err-msg">휴대전화 번호를 정확히 입력해 주세요.</p>
              </div>
              <div class="field" id="fJob">
                <label>현재 직업 또는 활동 분야 <span class="req">*</span></label>
                <div class="pill-choice">{JOBS}</div>
                <p class="err-msg">직업 또는 활동 분야를 선택해 주세요.</p>
              </div>
              <div class="field" id="fOrg">
                <button type="button" class="org-toggle" id="orgToggle"><i data-lucide="plus"></i> 소속·기관명 적기 <span class="field-opt">(원하시는 분만)</span></button>
                <div class="org-box" id="orgBox" hidden>
                  <label id="orgLabel" for="f-org">소속 <span class="field-opt">(선택)</span></label>
                  <input id="f-org" type="text" name="org" placeholder="예: ○○대학교 / ○○기업 인사팀">
                </div>
              </div>
            </div>
          </div>

          <div class="gform-card" id="secMotive">
            <div class="gform-sec">SECTION 3</div>
            <h2>지원 동기 <span class="req">*</span></h2>
            <p class="gform-desc">위원 활동을 통해 기대하는 것을 선택해 주세요. 복수 선택할 수 있습니다.</p>
            <div class="check-grid" id="motiveGrid">{MOTIVE_ITEMS}</div>
            <p class="err-msg">기대하는 것을 하나 이상 선택해 주세요.</p>
            <div class="gform-fields" style="margin-top:18px">
              <div class="field" id="fMsg">
                <label for="f-msg">한 줄 자기소개 <span class="field-opt">(선택)</span></label>
                <div class="msg-quick" id="msgQuick" aria-label="자기소개 예시 문장">
                  <button type="button">AI 윤리 활동을 온라인에 알리고 싶습니다.</button>
                  <button type="button">SNS·블로그에 AI 윤리 캠페인 콘텐츠를 공유하며 활동하고 싶습니다.</button>
                  <button type="button">취업 준비 중이라 공식 위원 활동 경력을 쌓고 싶습니다.</button>
                  <button type="button">학교·직장에서 올바른 AI 활용 문화를 만드는 데 힘을 보태고 싶습니다.</button>
                </div>
                <textarea id="f-msg" name="msg" maxlength="600" rows="3" placeholder="예) AI 윤리 활동을 온라인에 알리고 싶습니다."></textarea>
                <p class="field-hint">한 줄이면 충분합니다. 위 문장을 누르면 그대로 들어가고, 비워 두셔도 됩니다. <span id="msgCount">0</span>/600</p>
              </div>
            </div>
          </div>

          <div class="gform-card" id="secPriv">
            <div class="gform-sec">SECTION 4</div>
            <h2>개인정보 수집·이용 동의</h2>
            <div class="gform-privacy">
              <div><span>수집항목</span>성명, 이메일, 휴대전화(선택), 직업·활동 분야, 소속(선택), 참여 구분, 지원 동기·자기소개</div>
              <div><span>이용목적</span>참여 신청 검토, 위촉 및 활동 안내, 위촉 시 홈페이지 공식 위원 명단 게시(성명)</div>
              <div><span>보유기간</span>수집일로부터 3년. 활동이 끝나거나 삭제를 요청하시면 즉시 파기합니다</div>
            </div>
            <label class="agree"><input type="checkbox" name="privok"><span class="agree-box"></span>
              <span>개인정보 수집·이용에 동의합니다. <span class="req">*</span></span></label>
            <p class="err-msg">개인정보 수집·이용 동의에 체크해 주세요.</p>
            <p class="field-hint" style="margin-top:14px">자세한 내용은 <a href="privacy.html" style="color:var(--blue);font-weight:700">개인정보·운영정책</a>을 확인해 주세요.</p>
          </div>

          <div class="gform-card gform-submit gform-submit--why">
            <span class="gform-kicker">Why KAIEC</span>
            <h2>AI 윤리는 이제 소수 전문가의 일이 아닙니다</h2>
            <p>AI기본법이 시행된 2026년, 기업·학교·기관 모두가 책임 있는 AI 활용의 기준과 그 기준을 지킬 사람을 찾고 있습니다.
               한국AI윤리위원회는 그 기준을 만들고 현장에 알리는 전문기관이고, 이 일을 함께 알릴 사람이 지금 필요합니다.
               오늘 이름을 올리는 것이 그 첫걸음입니다.</p>
            <button type="submit" class="btn btn-primary gform-submit-btn">위원 참여 신청하기 <i data-lucide="arrow-right"></i></button>
            <p class="err-msg" id="topErr">입력하지 않은 필수 항목이 있습니다. 표시된 항목을 확인해 주세요.</p>
            <p class="gform-after">제출 후 위원회 검토를 거쳐 보통 3~5일 안에 이메일로 안내드립니다.</p>
            <div class="trust-row">
              <div><i data-lucide="id-card"></i> 홈페이지 공식 위원 명단 등재</div>
              <div><i data-lucide="monitor-play"></i> 온라인·재택 활동</div>
              <div><i data-lucide="check-circle-2"></i> 참여 비용 없음</div>
            </div>
          </div>
        </form>

        <div class="gform-card gform-done" id="doneView" hidden>
          <div class="done-icon"><i data-lucide="check"></i></div>
          <h2>참여 신청이 접수되었습니다.</h2>
          <p>위원회에서 검토 후 작성하신 이메일로 보통 3~5일 안에 안내드립니다. 위촉되면 홈페이지 공식 위원 명단에 등록됩니다. 함께해 주셔서 감사합니다.</p>
          <div class="btns" style="justify-content:center">
            <a class="btn btn-primary" href="expert.html">AI윤리전문가 양성과정 보기</a>
            <a class="btn btn-ghost" href="about.html">위원회 소개 보기</a>
          </div>
          <div class="done-mailbox" id="mailBox">
            <p><strong>신청 내용 전송 안내</strong><br>자동 접수가 되지 않았다면 아래 신청 내용을 복사해
               <a href="mailto:{EMAIL}">{EMAIL}</a> 으로 보내주세요.</p>
            <textarea id="doneCopy" readonly aria-label="전송 내용 사본" tabindex="-1"></textarea>
            <button type="button" class="btn btn-ghost" id="copyBtn">신청 내용 복사</button>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="after">
      <div class="wrap">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">After Apply</span>
          <h2 class="h-sec">신청 후 진행 절차</h2>
        </div>
        <div class="grid grid-4">{after_html}</div>
        <p class="field-hint" style="text-align:center;margin-top:18px">
          개인 위원 제도의 자세한 안내는 <a href="partner.html" style="color:var(--blue);font-weight:700">AI 윤리위원 안내</a>,
          기관·기업의 협력 안내는 <a href="mou.html" style="color:var(--blue);font-weight:700">사회공헌·협력</a>을 참고하세요.</p>
      </div>
    </section>

    <section class="section section--gray">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:24px">
          <span class="eyebrow">FAQ</span>
          <h2 class="h-sec">자주 묻는 질문</h2>
        </div>
        {faq_html}
      </div>
    </section>

    <section class="section section--tight">
      <div class="wrap">
        <div class="cta-band">
          <div><h2>한국AI윤리위원회(KAIEC)와 함께하세요</h2>
            <p>무분별한 AI 사용을 막는 캠페인, AI 윤리를 온라인에 알리는 활동. 관심을 활동으로, 활동을 이력으로 만드는 자리가 여기 있습니다.</p></div>
          <div class="btns">
            <a class="btn btn-white" href="#apply" data-pick="AI 윤리 캠페인위원">캠페인위원 지원하기</a>
            <a class="btn btn-light" href="{CERT_HREF}">{CERT_CTA}</a>
          </div>
        </div>
      </div>
    </section>"""

    script = r"""
  <script>
  (function(){
    var form=document.getElementById('joinForm');
    var ORG_TYPES={'공식 파트너':1};
    function v(n){var el=form.querySelector('[name='+n+']');return (el&&el.value?el.value:'').trim();}
    function jtype(){var c=form.querySelector('[name=jtype]:checked');return c?c.value:'';}
    function bad(id,on){document.getElementById(id).classList.toggle('is-invalid',!!on);return !!on;}
    function checked(n){return Array.prototype.slice.call(form.querySelectorAll('[name='+n+']:checked')).map(function(x){return x.value;});}

    /* 소속 칸: 공식 파트너면 '기관명'으로 자동 표시, 그 외에는 원하는 분만 버튼으로 열기 */
    var orgToggle=document.getElementById('orgToggle'),orgBox=document.getElementById('orgBox'),orgLabel=document.getElementById('orgLabel'),orgIn=form.querySelector('[name=org]');
    function openOrg(isOrg){
      orgBox.hidden=false; orgToggle.hidden=true;
      orgLabel.innerHTML=isOrg?'기관명 <span class="field-opt">(기관·기업·학교)</span>':'소속 <span class="field-opt">(선택)</span>';
      orgIn.placeholder=isOrg?'예: ○○기업 / ○○대학교 / ○○기관':'예: ○○대학교 / ○○기업 인사팀';
    }
    orgToggle.addEventListener('click',function(){openOrg(false);orgIn.focus();});
    function syncType(){
      var t=jtype();
      document.getElementById('secType').classList.remove('is-invalid');
      if(ORG_TYPES[t]){openOrg(true);}
      else if(orgToggle.hidden&&!orgIn.value){orgLabel.innerHTML='소속 <span class="field-opt">(선택)</span>';orgIn.placeholder='예: ○○대학교 / ○○기업 인사팀';}
    }
    form.querySelectorAll('[name=jtype]').forEach(function(r){r.addEventListener('change',syncType);});
    function pick(t){var r=form.querySelector('[name=jtype][value="'+t+'"]');if(r){r.checked=true;syncType();}}
    var q=new URLSearchParams(location.search).get('type'); if(q){pick(q);}
    /* 히어로·역할 카드의 지원 버튼: 참여 구분을 미리 고르고 신청서로 이동 */
    document.querySelectorAll('[data-pick]').forEach(function(a){a.addEventListener('click',function(){pick(a.getAttribute('data-pick'));});});

    /* 자기소개 글자 수 + 예시 문장 칩(누르면 입력) */
    var msg=form.querySelector('[name=msg]'), mc=document.getElementById('msgCount');
    msg.addEventListener('input',function(){mc.textContent=this.value.length;});
    document.querySelectorAll('#msgQuick button').forEach(function(b){
      b.addEventListener('click',function(){
        var t=b.textContent.trim(), cur=msg.value.trim();
        if(cur.indexOf(t)>=0){return;}
        msg.value=(cur?cur+' ':'')+t; mc.textContent=msg.value.length; msg.focus();
      });
    });

    /* 휴대전화 자동 하이픈 */
    var phone=form.querySelector('[name=phone]');
    phone.addEventListener('input',function(){
      var d=this.value.replace(/[^0-9]/g,'').slice(0,11);
      if(d.length<4){this.value=d;}else if(d.length<8){this.value=d.slice(0,3)+'-'+d.slice(3);}
      else{this.value=d.slice(0,3)+'-'+d.slice(3,7)+'-'+d.slice(7);}
    });

    form.addEventListener('submit',function(e){
      e.preventDefault();
      var digits=v('phone').replace(/[^0-9]/g,'');
      var job=form.querySelector('[name=job]:checked');
      var mot=checked('motive');
      bad('secType',!jtype());
      bad('fName',!v('name'));
      bad('fEmail',!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v('email')));
      bad('fPhone',digits.length>0&&!(digits.length>=10&&digits.length<=11&&digits.slice(0,2)==='01'));
      bad('fJob',!job);
      bad('secMotive',mot.length===0);
      bad('secPriv',!form.querySelector('[name=privok]').checked);
      var first=document.querySelector('.is-invalid');
      document.getElementById('topErr').style.display=first?'block':'none';
      if(first){first.scrollIntoView({behavior:'smooth',block:'center'});return;}

      var t=jtype();
      var data={type:'join',course:'[KAIEC 참여] '+t,name:v('name'),email:v('email'),phone:v('phone'),
                job:job.value,org:v('org'),motive:mot.join(', '),purpose:v('msg'),t:String(Date.now())};
      var lines=['한국AI윤리위원회 위원 참여 신청','',
        '■ 참여 구분 : '+t,'■ 성명 : '+data.name,'■ 이메일 : '+data.email,
        '■ 휴대전화 : '+(data.phone||'(미기재)'),'■ 직업/활동 분야 : '+data.job,'■ 소속 : '+(data.org||'(미기재)'),
        '■ 기대하는 것 : '+data.motive,'■ 지원 사유·자기소개 : '+data.purpose,'',
        '■ 개인정보 수집·이용 : 동의','','--- kaiec.kr 위원 참여 신청 페이지에서 작성됨 ---'];

      /* 접수 데이터 전송: 시트 웹훅으로 POST(폼 형식) 전송, 실패 시 GET, 웹훅이 없으면 메일 앱 폴백 */
      var HOOK='__HOOK__';
      if(HOOK){
        var body=new URLSearchParams(); Object.keys(data).forEach(function(k){body.append(k,data[k]);});
        var sent=false;
        try{fetch(HOOK,{method:'POST',mode:'no-cors',keepalive:true,cache:'no-store',body:body});sent=true;}catch(e1){}
        if(!sent){try{var im=new Image();im.src=HOOK+'?'+body.toString();}catch(e2){}}
        document.getElementById('mailBox').hidden=true;
      }else{
        var mail='mailto:__FEMAIL__?subject='+encodeURIComponent('[위원 참여 신청] '+data.name+' · '+t)
                +'&body='+encodeURIComponent(lines.join('\n'));
        setTimeout(function(){location.href=mail;},400);
      }
      form.hidden=true;
      var done=document.getElementById('doneView'); done.hidden=false;
      document.getElementById('doneCopy').value=lines.join('\n');
      window.scrollTo({top:done.getBoundingClientRect().top+window.pageYOffset-90,behavior:'smooth'});
    });

    document.getElementById('copyBtn').addEventListener('click',function(){
      var ta=document.getElementById('doneCopy'); ta.select();
      var ok=false; try{ok=document.execCommand('copy');}catch(err){}
      if(navigator.clipboard){navigator.clipboard.writeText(ta.value).catch(function(){});ok=true;}
      this.textContent=ok?'복사되었습니다':'복사 후 붙여넣어 주세요';
      var b=this; setTimeout(function(){b.textContent='신청 내용 복사';},2200);
    });
  })();
  </script>
""".replace('__FEMAIL__', EMAIL).replace('__HOOK__', SHEET_WEBHOOK)

    page("join.html", "위원 참여",
         "한국AI윤리위원회(KAIEC) 위원 참여 신청. AI 윤리 캠페인위원(전공·경력·나이 무관, 온라인 활동)을 중심으로 운영위원·전문위원, 기관·기업·학교 공식 파트너까지 온라인으로 바로 지원하세요. 위촉되면 홈페이지 공식 위원 명단에 등록됩니다.",
         body, extra_script=script,
         keywords=["위원 참여", "KAIEC 참여", "한국AI윤리위원회 참여", "AI 윤리 캠페인위원 모집", "AI 윤리위원 지원",
                   "AI 윤리 전문위원 모집", "AI 윤리 공식 파트너", "AI 윤리 대외활동"])


# ---------------------------------------------------------------- quiz.html
def build_quiz():
    """AI 윤리 자가진단: 실제 업무 장면 7개를 고르며 자기 기준을 점검 → 결과 화면에서 양성과정으로 연결 (체류·자기설득 장치)"""
    QUIZ = [
        ("AI 활용 표기", "생성형 AI로 초안을 쓴 보고서를 상사나 고객에게 제출하려 합니다.",
         [("초안만 AI가 썼고 최종 문장은 직접 다듬었으므로 별도 표기는 하지 않는다", 1),
          ("AI를 썼다고 밝히면 평가가 불리해지므로 검증만 꼼꼼히 한다", 0),
          ("사실관계와 출처를 검증한 뒤, 조직 기준에 따라 AI 활용 범위를 표기한다", 2)],
         "결과물의 책임은 사람에게 있습니다. 검증과 표기는 한 쌍이며, 어느 한쪽만 해도 나중에 신뢰의 문제가 됩니다."),
        ("입력 정보 보호", "회의록 요약을 위해 외부 AI 서비스에 회의 녹취 전체를 넣으려 합니다.",
         [("조직이 승인한 도구인지 확인하고, 이름과 기밀, 개인정보를 지운 뒤 넣는다", 2),
          ("학습에 쓰지 않는다고 명시된 유료 요금제이므로 그대로 넣는다", 0),
          ("회사명과 참석자 직함만 가리고 나머지는 그대로 넣는다", 1)],
         "사고는 대부분 출력이 아니라 입력 단계에서 납니다. 약관의 학습 여부와 별개로, 무엇을 넣어도 되는지는 조직이 정해 두어야 합니다."),
        ("출처 검증", "AI가 알려준 통계 수치를 보고서에 인용하려 합니다.",
         [("AI가 출처 링크까지 제시했으므로 그 링크를 각주로 단다", 0),
          ("원 출처 문서를 직접 찾아 수치를 확인하고, 그 출처를 표기한다", 2),
          ("다른 AI에게 한 번 더 물어 같은 답이 나오면 인용한다", 1)],
         "생성형 AI는 그럴듯한 숫자와 존재하지 않는 출처를 함께 만들어냅니다. 교차 질문으로는 걸러지지 않고, 원문 확인만이 방법입니다."),
        ("저작권 · 초상권", "AI 이미지 생성으로 홍보물을 만들려 합니다.",
         [("상업적 이용이 허용된 서비스로 만들었으므로 그대로 쓴다", 1),
          ("실존 인물과 닮지 않았는지만 확인하면 된다", 0),
          ("약관이 주는 권리 범위와 인물 · 상표 유사성을 확인하고, 생성 이미지 표기 기준을 따른다", 2)],
         "서비스 약관이 허용하는 범위와 결과물이 다른 권리를 침해하는지는 별개의 문제입니다. 확인할 것이 하나가 아니라 셋입니다."),
        ("조직의 기준", "팀원이 AI 활용을 알리지 않고 제출한 결과물에서 오류가 발견됐습니다.",
         [("팀의 AI 활용 · 검증 기준을 문서로 만들어 공유하고, 제출 전 확인 절차를 둔다", 2),
          ("재발 방지를 위해 팀 내 AI 사용을 당분간 금지한다", 0),
          ("해당 팀원에게 주의를 주고 다음부터는 알리도록 한다", 1)],
         "금지는 알리지 않는 사용을 늘릴 뿐이고, 개인 주의는 다음 사람에게 반복됩니다. 기준을 만들어 공유하는 사람이 조직의 위험을 줄입니다."),
        ("공정성", "AI 채용 평가 도구가 특정 집단에 불리한 결과를 내는 것으로 보입니다.",
         [("집단별 합격선을 조정해 결과의 균형을 맞춘다", 1),
          ("편향 가능성을 점검하고 사람이 최종 판단하며, 판단 근거를 기록으로 남긴다", 2),
          ("도구 제공사에 문의하고 회신이 올 때까지 기존대로 운영한다", 0)],
         "결과만 손대면 원인은 그대로 남습니다. 사람의 최종 판단과 기록은 고영향 영역에서 특히 중요합니다."),
        ("AI기본법", "2026년 1월 시행된 AI기본법, 우리 조직과 어떤 관계일까요?",
         [("AI를 직접 개발하지 않으므로 우리 조직과는 관계가 없다", 0),
          ("AI를 활용하는 기업과 기관, 학교에도 표시 · 고지 같은 의무가 생긴다", 2),
          ("이름은 들어봤지만 우리 업무와 어떻게 연결되는지는 확인하지 못했다", 1)],
         "의무는 개발하는 쪽에만 생기지 않았습니다. 활용하는 조직에도 적용된다는 사실을 아는 것이 출발점입니다."),
    ]
    RESULTS = [
        (12, "AI 윤리 리더형", "이미 기준을 갖고 판단하고 있습니다.",
         "대부분의 장면에서 책임 있는 판단을 하고 있습니다. 이제 필요한 것은 그 판단력을 조직 밖에서도 인정받는 증명입니다. "
         "AI윤리전문가 양성과정은 지금의 감각을 한국AI윤리위원회 공식 이수증과 홈페이지 공식 등록로 남기고, 전문위원 등록과 전문강사·자문 활동으로 넓히는 가장 빠른 길입니다."),
        (7, "실무 감각형", "큰 방향은 맞지만, 상황마다 흔들리는 지점이 있습니다.",
         "판단의 방향은 옳은데 기준이 정리되어 있지 않아 장면마다 결과가 달라집니다. 체계적으로 한 번 정리하면 판단이 빨라지고, "
         "그 기준을 이수증으로 남길 수 있습니다. AI윤리전문가 양성과정이 정확히 그 역할을 합니다."),
        (0, "출발선형", "AI를 활용하고는 있지만, 기준은 아직입니다.",
         "AI를 이미 업무와 학습에 활용하고 있다면 기준이 없는 상태가 가장 위험합니다. 반대로 말하면 지금이 가장 좋은 출발점입니다. "
         "위원회 표준교재로 핵심 원칙과 안전 수칙부터 갖추고, 온라인 이수 평가로 증명하세요."),
    ]
    import json as _json
    quiz_json = _json.dumps([{"t": t, "q": q, "o": [o for o, _ in opts], "s": [sc for _, sc in opts], "e": e}
                             for t, q, opts, e in QUIZ], ensure_ascii=False)
    res_json = _json.dumps([{"min": m, "name": n, "lead": l, "desc": d} for m, n, l, d in RESULTS], ensure_ascii=False)

    body = f"""    <section class="page-hero">
      <div class="wrap page-hero-inner">
        <p class="crumb"><a href="index.html">홈</a> &nbsp;›&nbsp; AI 윤리 실무 진단</p>
        <span class="join-eyebrow">SELF CHECK · 7문항</span>
        <h1>이 7가지, 당신이라면 어떻게 판단하시겠습니까?</h1>
        <p>보기 셋이 모두 그럴듯하게 보이도록 만든 실무 장면입니다. 정답을 맞히는 시험이 아니라
           지금 내 판단 기준이 어디쯤인지 확인하는 진단이고, 고를 때마다 근거 해설이 바로 나옵니다.</p>
      </div>
    </section>

    <section class="section section--gray">
      <div class="quiz-wrap">
        <div class="quiz-card" id="quizCard">
          <div class="quiz-top">
            <span class="quiz-topic" id="qTopic"></span>
            <span class="quiz-count"><b id="qNo">1</b> / {len(QUIZ)}</span>
          </div>
          <div class="quiz-bar"><span id="qBar"></span></div>
          <h2 class="quiz-q" id="qText"></h2>
          <div class="quiz-opts" id="qOpts"></div>
          <div class="quiz-exp" id="qExp" hidden>
            <strong id="qExpTitle"></strong>
            <p id="qExpText"></p>
            <button type="button" class="btn btn-primary" id="qNext">다음 문항 <i data-lucide="arrow-right"></i></button>
          </div>
        </div>

        <div class="quiz-card quiz-result" id="quizResult" hidden>
          <span class="gform-kicker">진단 결과</span>
          <div class="quiz-score"><b id="rScore">0</b><span>/ {len(QUIZ) * 2}점</span></div>
          <div class="quiz-bar quiz-bar--big"><span id="rBar"></span></div>
          <h2 id="rName"></h2>
          <p class="quiz-lead" id="rLead"></p>
          <p class="quiz-desc" id="rDesc"></p>
          <div class="quiz-weak" id="rWeak" hidden>
            <strong>다시 볼 기준</strong>
            <div class="chips" id="rWeakChips"></div>
          </div>
          <div class="quiz-next">
            <strong>다음 단계</strong>
            <p>AI윤리전문가 양성과정: 위원회 표준교재 등 학습자료 5종 + 온라인 이수 평가, 한국AI윤리위원회 공식 이수증 · 홈페이지 공식 등록 · 이력서·자기소개서 활용 가이드.
               특별가 {won(PRICE)} (정가 {won(LIST_PRICE)}) · {HOOK_ZERO} · {HOOK_START}</p>
            <div class="btns">
              <a class="btn btn-primary" href="{CERT_HREF}">{CERT_CTA} <i data-lucide="arrow-right"></i></a>
              <a class="btn btn-ghost" href="expert.html">양성과정 안내</a>
            </div>
          </div>
          <button type="button" class="quiz-retry" id="qRetry">다시 풀기</button>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:24px">
          <span class="eyebrow">Why It Matters</span>
          <h2 class="h-sec">기준을 아는 한 사람이 조직 전체의 리스크를 줄입니다</h2>
          <p class="h-sub" style="margin:0 auto">2026년 AI기본법 시행 이후 기업·기관·학교는 AI를 어디까지 어떻게 활용해야 하는지 답할 사람을 찾고 있습니다.
             이 진단의 7개 장면이 바로 그 기준이고, AI윤리전문가 양성과정은 그 기준을 체계적으로 배우고 이수증으로 증명하는 과정입니다.</p>
        </div>
      </div>
    </section>"""

    script = """  <script>
  (function(){
    var Q=__QUIZ__, R=__RES__;
    var i=0, score=0, weak=[];
    var topic=document.getElementById('qTopic'),no=document.getElementById('qNo'),bar=document.getElementById('qBar'),
        text=document.getElementById('qText'),opts=document.getElementById('qOpts'),exp=document.getElementById('qExp'),
        expT=document.getElementById('qExpTitle'),expX=document.getElementById('qExpText'),next=document.getElementById('qNext'),
        card=document.getElementById('quizCard'),res=document.getElementById('quizResult');
    function show(){
      var q=Q[i]; topic.textContent=q.t; no.textContent=i+1; bar.style.width=((i)/Q.length*100)+'%';
      text.textContent=q.q; exp.hidden=true; opts.innerHTML='';
      q.o.forEach(function(o,k){
        var b=document.createElement('button'); b.type='button'; b.className='quiz-opt';
        b.innerHTML='<span>'+String.fromCharCode(9312+k)+'</span>'+o;
        b.addEventListener('click',function(){pick(k,b);}); opts.appendChild(b);
      });
    }
    function pick(k,b){
      var q=Q[i], sc=q.s[k], best=Math.max.apply(null,q.s);
      score+=sc; if(sc<best){weak.push(q.t);}
      opts.querySelectorAll('.quiz-opt').forEach(function(x,idx){x.disabled=true; if(q.s[idx]===best)x.classList.add('is-best');});
      b.classList.add(sc===best?'is-best':(sc>0?'is-half':'is-low'));
      expT.textContent=sc===best?'좋은 판단입니다':(sc>0?'방향은 맞지만 한 걸음 더':'여기서 사고가 납니다');
      expX.textContent=q.e; exp.hidden=false;
      next.innerHTML=(i===Q.length-1?'결과 보기':'다음 문항')+' <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>';
      exp.scrollIntoView({behavior:'smooth',block:'nearest'});
    }
    next.addEventListener('click',function(){
      i++; if(i<Q.length){show(); card.scrollIntoView({behavior:'smooth',block:'start'});} else {finish();}
    });
    function finish(){
      var max=Q.length*2, r=R[R.length-1];
      for(var k=0;k<R.length;k++){ if(score>=R[k].min){r=R[k];break;} }
      document.getElementById('rScore').textContent=score;
      document.getElementById('rBar').style.width=(score/max*100)+'%';
      document.getElementById('rName').textContent=r.name;
      document.getElementById('rLead').textContent=r.lead;
      document.getElementById('rDesc').textContent=r.desc;
      var w=document.getElementById('rWeak'), wc=document.getElementById('rWeakChips');
      wc.innerHTML=''; var seen={};
      weak.forEach(function(t){ if(seen[t])return; seen[t]=1; var s=document.createElement('span'); s.className='chip'; s.textContent=t; wc.appendChild(s); });
      w.hidden=weak.length===0;
      card.hidden=true; res.hidden=false;
      window.scrollTo({top:res.getBoundingClientRect().top+window.pageYOffset-90,behavior:'smooth'});
    }
    document.getElementById('qRetry').addEventListener('click',function(){
      i=0; score=0; weak=[]; res.hidden=true; card.hidden=false; show();
      window.scrollTo({top:card.getBoundingClientRect().top+window.pageYOffset-90,behavior:'smooth'});
    });
    show();
  })();
  </script>
""".replace('__QUIZ__', quiz_json).replace('__RES__', res_json)

    page("quiz.html", "AI 윤리 실무 진단 (7문항)",
         "AI 초안 보고서의 표기, 회의 녹취의 외부 AI 입력, AI가 준 통계의 인용. 실무에서 자주 틀리는 장면 7개로 내 AI 윤리 판단 기준을 확인하고 근거 해설과 다음 단계를 안내받으세요.",
         body, extra_script=script,
         keywords=["AI 윤리 진단", "AI 윤리 테스트", "AI 윤리 퀴즈", "AI 활용 기준", "AI기본법", "AI윤리전문가", "한국AI윤리위원회"])


# ---------------------------------------------------------------- exam.html (평가응시)
# 이수 평가 시스템 전용 추가 아이콘 (Lucide, ISC License). icons.py 공용 아이콘과 합쳐 페이지 안 SVG 스프라이트로 넣고,
# exam.js는 <svg><use href="#exi-이름"></use></svg> 로 참조합니다 (외부 아이콘 라이브러리 없음)
EXAM_ICONS = {
    "log-out": '<path d="m16 17 5-5-5-5"/><path d="M21 12H9"/><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>',
    "log-in": '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>',
    "eye-off": '<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "wifi-off": '<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',
    "printer": '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "refresh-cw": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-up": '<path d="m18 15-6-6-6 6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "monitor": '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "save": '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
    "keyboard": '<path d="M10 8h.01"/><path d="M12 12h.01"/><path d="M14 8h.01"/><path d="M16 12h.01"/><path d="M18 8h.01"/><path d="M6 8h.01"/><path d="M7 16h10"/><path d="M8 12h.01"/><rect width="20" height="16" x="2" y="4" rx="2"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "download": '<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "timer": '<path d="M10 2h4"/><path d="m12 14 3-3"/><circle cx="12" cy="14" r="8"/>',
    "list-checks": '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    "circle-x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "hourglass": '<path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/>',
    "layout-grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    "ban": '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    "copy-slash": '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/><path d="m3 3 18 18"/>',
}
EXAM_SPRITE_BASE = ["arrow-left", "arrow-right", "award", "badge-check", "bar-chart-3", "book-open", "check",
                    "check-circle-2", "chevron-right", "clipboard-list", "clock", "database", "external-link", "eye", "file-check",
                    "graduation-cap", "help-circle", "id-card", "lock", "monitor-play", "pen-line", "send",
                    "shield-check", "user-check", "users", "wifi", "x"]

# 체험 모드 문항: expert 페이지 샘플 문항(SAMPLE_Q) 3개 + 아래 예시 2개(지문형·〈보기〉형). 실제 평가 문항이 아닌 쉬운 예시입니다.
# 영역 코드·이름은 평가 운영 시트(백엔드 Code 1.5.0)의 통합 과정 출제 기준표 영역 I~V와 같게 맞춤
EXAM_DEMO_AREAS = [("II", "핵심 쟁점과 생성형 AI 활용 윤리"), ("IV", "AI 윤리 위험 사례 분석"), ("III", "국내외 AI 법제")]
EXAM_DEMO_EXTRA = [
    {"area": "V", "areaName": "거버넌스 · 영향평가 · 조직 실무",
     "stem": "다음 사례에 대한 판단으로 옳지 않은 것은?", "underline": ["않은"],
     "box": ("A기업은 고객 상담에 생성형 AI 챗봇을 도입하려 한다.\n"
             "상담 과정에서 고객의 이름·연락처·주문 내역이 함께 입력된다.\n"
             "담당자는 출시 일정을 이유로 별도 검토 없이 기본 설정을 그대로 적용하려 한다."),
     "bogi": [],
     "options": ["입력되는 개인정보의 수집·이용 범위를 먼저 확인해야 한다",
                 "고객에게 AI 챗봇과 대화하고 있다는 사실을 알리는 것이 바람직하다",
                 "출시 일정이 급하면 개인정보 검토는 출시 이후로 미루어도 된다",
                 "상담 내용을 AI 학습에 활용하려면 고지와 동의 절차를 먼저 검토해야 한다"],
     "answer": 3},
    {"area": "II", "areaName": "핵심 쟁점과 생성형 AI 활용 윤리",
     "stem": "생성형 AI 산출물의 책임 있는 활용에 대한 설명으로 옳은 것만을 〈보기〉에서 있는 대로 고른 것은?",
     "underline": [], "box": "",
     "bogi": [{"k": "ㄱ", "t": "AI가 제시한 통계와 인용은 원 출처를 확인한 뒤 사용한다."},
              {"k": "ㄴ", "t": "AI가 만든 결과물에 대한 책임은 AI 서비스 제공자에게만 있다."},
              {"k": "ㄷ", "t": "조직의 기준에 따라 AI 활용 사실을 표기한다."},
              {"k": "ㄹ", "t": "개인정보나 기밀이 담긴 자료는 조직이 승인한 도구에서만 처리한다."}],
     "options": ["ㄱ, ㄴ", "ㄱ, ㄷ", "ㄴ, ㄹ", "ㄱ, ㄷ, ㄹ"],
     "answer": 4},
]
EXAM_DEMO_MINUTES = 5


def build_exam():
    """평가응시(/exam/): AI윤리전문가 양성과정 온라인 이수 평가 시스템 (2026.09.16 신설, 같은 날 2차 개편)
    - 흐름: 로그인(결제 이메일 + 휴대전화 번호 뒤 4자리) → 대시보드 → 응시 전 확인(성명 입력·서약) → [시험 시작] 확인 창
            → 시험(전체 화면 레이어, 시험 시간 타이머 60분) → 제출 확인 → 결과. 진행 중인 시험은 [이어서 응시]로 들어감
    - 로그인 전에는 이메일·비밀번호 상자와 결제 링크 1개(PAY_URL)만 보입니다 (2026.09.21 통합).
      자세한 안내(이수 절차·평가 구성·이수 기준·응시 환경)는 로그인 뒤 대시보드에서 assets/js/exam.js가 그립니다
    - 로그인 상자와 얇은 페이지 머리(로그인 뒤 표시)만 정적 HTML이고, 나머지 화면은 exam.js가 그립니다(URL 해시로 새로고침 복원, 토큰은 sessionStorage)
    - 백엔드는 EXAM_API(평가 운영 시트의 앱스 스크립트 웹 앱). 비어 있으면 '평가 시스템 연결 준비 중' 안내와 함께 로그인을 막음
    - 체험 모드는 /exam/?demo=1 주소로만 진입(브라우저 안 모의 API)
    - 설정은 window.KAIEC_EXAM(과정별 문항 수·시험 시간·배점·이수 기준, 결제 링크 payBasic, unified 플래그), 체험 문항은 window.KAIEC_EXAM_DEMO 로 주입.
      과정은 「AI윤리전문가 양성과정」 하나(백엔드 Code 1.5.0). 백엔드가 1.4.4 이하면 계정의 과정이 옛 표기로 올 수 있어 courses 에 옛 값도 함께 넣습니다(대시보드는 계정의 과정을 서버 값으로 그림)"""
    import json as _json

    def _n(x):
        return "%g" % x

    def _ic(name, cls=""):
        return f'<svg class="ex-ico{(" " + cls) if cls else ""}" aria-hidden="true" focusable="false"><use href="#exi-{name}"></use></svg>'

    def _js(v):
        return _json.dumps(v, ensure_ascii=False)

    materials = [{"no": no, "title": t, "meta": m, "icon": ic, "mb": mb} for no, t, m, ic, mb in MATERIAL_FILES]
    cfg = ('<script>window.KAIEC_EXAM={api:%s,windowDays:%d,email:%s,unified:true,payBasic:%s,payAdv:"",materials:%s,courses:{'
           '"%s":{total:%d,minutes:%d,point:%s,passScore:%d},'
           '"기본과정":{total:%d,minutes:%d,point:%s,passScore:%d},'
           '"심화과정":{total:%d,minutes:%d,point:%s,passScore:%d}}};</script>'
           % (_js(EXAM_API), EXAM_WINDOW_DAYS, _js(EMAIL), _js(PAY_URL),
              _json.dumps(materials, ensure_ascii=False, separators=(",", ":")),
              PROG, EXAM[0], EXAM_MIN, _n(100 / EXAM[0]), EXAM[1],
              EXAM[0], EXAM_MIN, _n(100 / EXAM[0]), EXAM[1],
              EXAM_LEGACY_ADV[0], EXAM_MIN_LEGACY_ADV, _n(100 / EXAM_LEGACY_ADV[0]), EXAM_LEGACY_ADV[1]))

    demo_q, demo_key = [], []
    for (q, opts, ans, _exp), (ac, an) in zip(SAMPLE_Q, EXAM_DEMO_AREAS):
        demo_q.append({"n": len(demo_q) + 1, "area": ac, "areaName": an, "stem": q,
                       "underline": [], "box": "", "bogi": [], "options": list(opts)})
        demo_key.append(ans + 1)
    for ex in EXAM_DEMO_EXTRA:
        item = {"n": len(demo_q) + 1}
        item.update({k: v for k, v in ex.items() if k != "answer"})
        demo_q.append(item)
        demo_key.append(ex["answer"])
    demo_js = ('<script>window.KAIEC_EXAM_DEMO='
               + _json.dumps({"minutes": EXAM_DEMO_MINUTES, "questions": demo_q, "key": demo_key},
                             ensure_ascii=False, separators=(",", ":"))
               + ';</script>')

    # 아이콘 스프라이트 + KAIEC 배지 글자(벡터, 시험 화면 머리에서 사용)
    allicons = dict(ICONS)
    allicons.update(EXAM_ICONS)
    badge_vb = re.search(r'viewBox="([^"]+)"', BADGE_SVG).group(1)
    badge_inner = BADGE_SVG[BADGE_SVG.index(">") + 1:BADGE_SVG.rindex("</svg>")]
    sprite = ('<svg class="ex-sprite" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
              + "".join(f'<symbol id="exi-{n}" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" '
                        f'stroke-linecap="round" stroke-linejoin="round">{allicons[n]}</g></symbol>'
                        for n in EXAM_SPRITE_BASE + list(EXAM_ICONS))
              + f'<symbol id="exi-kaiec" viewBox="{badge_vb}">{badge_inner}</symbol>'
              + '</defs></svg>')

    # 로그인 상자 아래 결제 버튼 (성균관컨설팅 결제 페이지, 새 창). 링크가 비어 있으면 그 버튼은 만들지 않음
    # 아직 등록 전인 분을 위한 '응시 자격' 안내와 과정 등록 버튼(성균관컨설팅 결제 페이지, 새 창)
    pay_btns = (f'<a class="ex-paybtn" href="{PAY_URL}" target="_blank" rel="noopener">'
                f'<span class="ex-paybtn-t">AI윤리전문가 양성과정 등록하기{_ic("external-link")}</span>'
                f'<span class="ex-paybtn-p">{won(PRICE)}</span>'
                f'<span class="sr-only">(정가 {won(LIST_PRICE)}, 새 창)</span></a>') if PAY_URL else ""
    pay_html = f"""
            <div class="ex-lbox-pay">
              <p class="ex-lbox-q">아직 등록 전이신가요?</p>
              <div class="ex-paybtns">{pay_btns}</div>
              <p class="ex-lbox-note">결제하시면 이 화면의 아이디와 비밀번호가 자동으로 만들어집니다.</p>
            </div>""" if pay_btns else ""

    body = f"""    <div class="ex-shell" id="examApp">
      <header class="ex-phead" id="exHead" hidden>
        <div class="ex-phead-in">
          <div class="ex-phead-main">
            <p class="ex-crumb" id="exCrumb"><a href="index.html">홈</a><span class="ex-crumb-sep" aria-hidden="true">›</span><span aria-current="page">평가응시</span></p>
            <p class="ex-phead-title">평가응시</p>
          </div>
          <div class="ex-phead-side">
            <div class="ex-phead-meta">
              <span class="ex-sys" id="exSysState" data-state="check" role="status"><i class="ex-dot" aria-hidden="true"></i><b>연결 상태 확인 중</b></span>
              <span class="ex-clock" id="exClock"></span>
            </div>
            <div class="ex-phead-tools" id="exHeadTools" hidden></div>
          </div>
        </div>
      </header>

      <div class="ex-demo-bar" id="exDemoBar" hidden>
        <div class="ex-demo-bar-in">{_ic("monitor-play")}<strong>체험 모드</strong><span>실제 응시 기록이 남지 않습니다. 예시 {len(demo_q)}문항 · 시험 시간 {EXAM_DEMO_MINUTES}분</span>
          <button type="button" class="ex-demo-exit" data-act="demo-exit">체험 종료</button></div>
      </div>

      <section class="ex-login" id="exLogin" aria-labelledby="exLoginTitle">
        <div class="ex-lbox">
          <div class="ex-lbox-head">
            <p class="ex-lbox-prog">AI윤리전문가 양성과정</p>
            <h1 class="ex-lbox-title" id="exLoginTitle">이수 평가 시스템</h1>
            <p class="ex-lbox-en">KAIEC ONLINE ASSESSMENT SYSTEM</p>
          </div>
          <div class="ex-lbox-body">
            <div class="ex-ready" id="exReady" hidden>{_ic("hourglass")}<p><strong>평가 시스템 연결 준비 중</strong>연결이 끝나면 이 화면에서 로그인할 수 있습니다.</p></div>
            <div class="ex-lbox-go" id="exLoginGo" hidden>{_ic("download")}<p><strong>학습자료 다시 내려받기</strong>안내 메일의 아이디와 비밀번호로 로그인하면 학습자료 5종(PDF)을 다시 내려받을 수 있습니다.</p></div>
            <form class="ex-form" id="exLoginForm" novalidate>
              <div class="ex-field">
                <label class="ex-label" for="exEmail">이메일(아이디)</label>
                <input class="ex-text" id="exEmail" name="email" type="email" inputmode="email" autocomplete="username" autocapitalize="off" spellcheck="false" placeholder="결제 때 입력한 이메일" required>
              </div>
              <div class="ex-field">
                <label class="ex-label" for="exPin">비밀번호 <small>숫자 4자리</small></label>
                <div class="ex-pinbox">
                  <input class="ex-text" id="exPin" name="pin" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="4" autocomplete="current-password" placeholder="숫자 4자리" aria-describedby="exPinHelp" required>
                  <button type="button" class="ex-eye" id="exPinToggle" aria-label="비밀번호 보기" aria-pressed="false">{_ic("eye", "ex-eye-on")}{_ic("eye-off", "ex-eye-off")}</button>
                </div>
                <p class="ex-field-help" id="exPinHelp">결제 때 입력한 휴대전화 번호 뒤 4자리</p>
              </div>
              <p class="ex-error" id="exLoginErr" role="alert" hidden></p>
              <button type="submit" class="ex-btn ex-btn--primary ex-btn--lg ex-btn--block" id="exLoginBtn">로그인</button>
            </form>
          </div>{pay_html}
          <p class="ex-lbox-foot">결제는 성균관컨설팅 안전결제 · 이수증은 한국AI윤리위원회 발급<br>로그인 문의 <a href="mailto:{EMAIL}">{EMAIL}</a></p>
        </div>
      </section>

      <div class="ex-view" id="exView" hidden></div>
      <div class="ex-boot" id="exBoot"><span class="ex-spin" aria-hidden="true"></span><span>평가 시스템을 불러오는 중입니다</span></div>
      <noscript><p class="ex-noscript">이 페이지는 자바스크립트를 사용합니다. 브라우저 설정에서 자바스크립트를 켠 뒤 다시 열어 주십시오.</p></noscript>
    </div>

    <div class="ex-layer" id="exLayer" hidden></div>
    <div class="ex-modal" id="exModal" hidden></div>
    <div class="ex-busy" id="exBusy" hidden><div class="ex-busy-box"><span class="ex-spin" aria-hidden="true"></span><strong id="exBusyText">처리 중입니다</strong></div></div>
    <div class="ex-toasts" id="exToasts" role="status" aria-live="polite"></div>
    {sprite}"""

    page("exam.html", "평가응시",
         "한국AI윤리위원회 AI윤리전문가 양성과정 수강생 전용 온라인 이수 평가입니다. 결제 이메일과 휴대전화 번호 뒤 4자리로 로그인해 "
         f"{exam_text()} 평가에 응시하고 결과를 확인하세요.",
         body,
         extra_head=f'<link rel="stylesheet" href="assets/css/exam.css?v={BUILD_V}">\n',
         extra_script=(f"  {cfg}\n  {demo_js}\n"
                       f'  <script src="assets/js/exam.js?v={BUILD_V}"></script>\n'),
         keywords=["AI윤리전문가 평가응시", "AI윤리전문가 이수 평가", "한국AI윤리위원회 이수 평가", "AI윤리전문가 양성과정",
                   "온라인 이수 평가", "AI윤리전문가 이수증", "한국AI윤리위원회"])


# ---------------------------------------------------------------- apply.html
def build_apply():
    roles = [
        ("crown", "대표위원", "위원회를 대표해 대외 활동과 주요 의사결정에 참여합니다.", "리더십 · 대외 활동"),
        ("briefcase", "운영위원장 · 운영위원", "사업 기획과 프로그램 운영, 활동 관리를 총괄·수행합니다.", "기획 · 운영"),
        ("map-pin", "지역 운영위원", "권역별 지역 조직을 이끌며 지역 단위 캠페인과 활동을 운영합니다.", "지역 조직"),
        ("school", "캠퍼스 위원장", "소속 대학의 캠퍼스 위원회를 이끌며 교내 확산 활동을 담당합니다.", "대학 조직"),
        ("megaphone", "홍보위원", "위원회 채널과 콘텐츠를 통해 AI 윤리 캠페인을 알립니다.", "홍보 · 콘텐츠"),
        ("sparkles", "서포터즈", "대학생·대학원생 중심으로 캠페인과 콘텐츠 활동에 참여합니다.", "참여 조직"),
    ]
    role_cards = "\n".join(f"""          <article class="card reveal">
            <div class="card-icon"><i data-lucide="{ic}"></i></div>
            <h3>{t}</h3>
            <p style="margin-bottom:14px">{d}</p>
            <div class="chips"><span class="chip">{tag}</span></div>
          </article>""" for ic, t, d, tag in roles)

    body = hero_sub("위원·회원기관 신청",
                    "책임 있는 AI를 함께 실천할 개인 위원과 기업·기관 회원기관을 상시 모집합니다.",
                    "위원·회원기관 신청") + f"""

    <section class="section section--tight" style="padding-bottom:0">
      <div class="wrap-narrow">
        <div class="apply-tabs">
          <a class="atab is-on" href="#individual"><i data-lucide="users"></i>개인 위원</a>
          <a class="atab" href="#member"><i data-lucide="building-2"></i>기업·기관 회원기관</a>
        </div>
      </div>
    </section>

    <div id="individual" class="apply-block">

    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Recruitment</span>
          <h2 class="h-sec">모집 분야</h2>
          <p class="h-sub">본인의 상황과 관심에 맞는 분야를 선택해 지원하실 수 있습니다. 전공·경력 제한이 없으며, 모든 활동은 온라인 병행이 가능합니다.</p>
        </div>
        <div class="grid grid-3">
{role_cards}
        </div>
        <div class="center" style="margin-top:26px">
          <a class="btn btn-ghost btn-sm" href="partner.html">AI 윤리위원 제도 안내 보기 <i data-lucide="arrow-right"></i></a>
        </div>
      </div>
    </section>

    <section class="section section--gray section--tight">
      <div class="wrap-narrow">
        <div class="grid grid-4">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">지원서 제출</h3><p style="font-size:14px">아래 지원서 작성</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">서류 검토</h3><p style="font-size:14px">약 3~5일</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">개별 연락</h3><p style="font-size:14px">이메일 · 유선 안내</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">위촉 · 활동</h3><p style="font-size:14px">공식 명단 등재 후 시작</p></div>
        </div>
      </div>
    </section>

    <section class="section" id="form">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:30px">
          <span class="eyebrow">Application</span>
          <h2 class="h-sec">온라인 지원서</h2>
          <p class="h-sub" style="margin:0 auto 24px">개인 위원과 기관·기업·학교 공식 파트너 신청은 위원 참여 신청서에서 접수합니다.
             참여 구분을 선택하고 신청서를 제출하시면 검토 후 개별 연락드립니다.</p>
          <a class="btn btn-primary" href="join.html#apply">위원 참여 신청서 작성하기 <i data-lucide="arrow-right"></i></a>
        </div>
        <p class="field-hint" style="margin-top:14px;text-align:center">
          기타 문의는 <a href="mailto:{EMAIL}" style="color:var(--blue);font-weight:600">{EMAIL}</a>
        </p>
      </div>
    </section>

    <section class="section section--gray section--tight">
      <div class="wrap-narrow">
        <div class="notice notice--teal">
          <strong>안내:</strong> 위원 지원과 활동 과정에서 가입비, 교육비 등
          어떠한 비용도 요구하지 않습니다. 지원서 검토 결과는 개별적으로 안내드립니다.
        </div>
      </div>
    </section>
    </div>

    <div id="member" class="apply-block">
    <section class="section">
      <div class="wrap">
        <div class="center" style="margin-bottom:42px">
          <span class="eyebrow">Corporate Membership</span>
          <h2 class="h-sec">한국AI윤리위원회 회원기관</h2>
          <p class="h-sub">책임 있는 AI를 실천하는 기업·기관의 네트워크입니다. 회원기관는 위원회의 교육·자문·인증 자원을
             우선적으로 활용하고, <strong>"한국AI윤리위원회 회원기관"</strong>로서 대외 신뢰를 확보합니다.</p>
        </div>
        <div class="grid grid-3">
          <article class="card reveal"><div class="card-icon"><i data-lucide="badge-check"></i></div>
            <h3>회원기관 인증서 · 현판</h3><p>위원회 명의의 회원기관 인증서와 현판을 제공하며, 홈페이지·소개자료에 "한국AI윤리위원회 회원기관" 표기를 사용할 수 있습니다.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="monitor-play"></i></div>
            <h3>AI 윤리 교육 할인</h3><p>임직원 대상 출강 교육(1~4시간 맞춤 과정)을 회원 등급에 따라 할인된 비용으로 이용합니다.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="award"></i></div>
            <h3>양성과정 수강 우대</h3><p>임직원의 AI윤리전문가 양성과정(기본·심화) 수강 시 우선 접수와 우대 혜택이 적용됩니다.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="shield-check"></i></div>
            <h3>AI 활용 기준 자문</h3><p>사내 생성형 AI 활용 지침과 AI기본법 대응 방향에 대한 기초 자문을 제공합니다.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="megaphone"></i></div>
            <h3>공동 캠페인 · 홍보</h3><p>위원회 홈페이지 로고 게재, 캠페인·세미나 공동 참여 등 대외 홍보 기회를 함께합니다.</p></article>
          <article class="card reveal"><div class="card-icon"><i data-lucide="file-check"></i></div>
            <h3>회비 납부 증빙 발급</h3><p>납부 회비에 대한 납부확인서 등 증빙 서류를 발급합니다. 비용 처리 세부 기준은 기관의 세무 담당자와 확인해 주세요.</p></article>
        </div>
      </div>
    </section>

    <section class="section section--gray" id="fee">
      <div class="wrap">
        <div class="center" style="margin-bottom:40px">
          <span class="eyebrow">Membership</span>
          <h2 class="h-sec">회원 등급 및 연회비</h2>
          <p class="h-sub">기관 규모와 활용 범위에 맞는 등급을 선택하세요. 연회비와 혜택 구성은 협의에 따라 조정할 수 있습니다.</p>
        </div>
        <div class="price-grid fee-3">
          <div class="price-card reveal">
            <div class="price-hours">준회원</div>
            <div class="price-num">30<small>만원 / 년</small></div>
            <div class="price-note">스타트업 · 1인 기업 · 소상공인</div>
            <ul style="text-align:left;margin-top:14px;display:grid;gap:7px;font-size:13.5px;color:var(--gray-600)">
              <li>· 회원기관 인증서 발급</li>
              <li>· "위원회 회원기관" 표기 사용</li>
              <li>· AI 윤리 교육 10% 할인</li>
              <li>· AI 규제·윤리 동향 뉴스레터</li>
            </ul>
          </div>
          <div class="price-card reveal" style="position:relative;border-color:var(--blue)">
            <span class="badge" style="position:absolute;top:-13px;left:50%;transform:translateX(-50%);background:var(--blue);color:#fff">가장 많이 선택</span>
            <div class="price-hours">정회원</div>
            <div class="price-num">100<small>만원 / 년</small></div>
            <div class="price-note">기업 · 기관 · 단체</div>
            <ul style="text-align:left;margin-top:14px;display:grid;gap:7px;font-size:13.5px;color:var(--gray-600)">
              <li>· 준회원 혜택 전체 포함</li>
              <li>· 회원기관 현판 제공</li>
              <li>· AI 윤리 교육 20% 할인</li>
              <li>· 임직원 양성과정 수강 우대</li>
              <li>· 위원회 홈페이지 로고 게재</li>
            </ul>
          </div>
          <div class="price-card reveal">
            <div class="price-hours">후원회원</div>
            <div class="price-num">300<small>만원 / 년</small></div>
            <div class="price-note">파트너 기관 · 후원 기업</div>
            <ul style="text-align:left;margin-top:14px;display:grid;gap:7px;font-size:13.5px;color:var(--gray-600)">
              <li>· 정회원 혜택 전체 포함</li>
              <li>· 공동 캠페인·세미나 파트너</li>
              <li>· 사내 AI 활용 기준 기초 자문</li>
              <li>· MOU 우선 체결·공동사업 협의</li>
            </ul>
          </div>
        </div>
        <div class="notice notice--gray" style="max-width:1020px;margin:24px auto 0">
          <strong>안내:</strong> 연회비는 기관 상황에 따라 협의 조정이 가능하며, 납부 회비에 대한 증빙 서류를 발급해 드립니다.
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap-narrow">
        <div class="center" style="margin-bottom:38px">
          <span class="eyebrow">Process</span>
          <h2 class="h-sec">회원기관 가입 절차</h2>
        </div>
        <div class="grid grid-4">
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 01</span><h3 style="font-size:16px">가입 문의</h3><p style="font-size:14px">온라인 문의 또는 메일 접수</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 02</span><h3 style="font-size:16px">등급 협의</h3><p style="font-size:14px">혜택·연회비 협의</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 03</span><h3 style="font-size:16px">가입 확정</h3><p style="font-size:14px">회비 납부 · 증빙 발급</p></div>
          <div class="card center reveal" style="padding:24px 18px"><span class="card-num">STEP 04</span><h3 style="font-size:16px">활동 시작</h3><p style="font-size:14px">인증서·현판 발급 후 혜택 이용</p></div>
        </div>
        <div class="center" style="margin-top:34px;display:flex;gap:11px;justify-content:center;flex-wrap:wrap">
          <a class="btn btn-primary" href="mou.html#inquiry">회원기관 가입 문의하기 <i data-lucide="arrow-right"></i></a>
          <a class="btn btn-ghost" href="mailto:{EMAIL}">메일로 문의하기</a>
        </div>
      </div>
    </section>
    </div>
"""

    tab_js = """  <script>
  /* 상단 버튼: 해당 섹션으로 부드럽게 이동 (#individual, #member 딥링크 지원) */
  (function(){
    var tabs=document.querySelectorAll('.atab');
    function mark(h){tabs.forEach(function(b){b.classList.toggle('is-on',b.getAttribute('href')==='#'+h)});}
    tabs.forEach(function(b){b.addEventListener('click',function(e){
      e.preventDefault();
      var id=b.getAttribute('href').slice(1);
      var el=document.getElementById(id);
      if(el){el.scrollIntoView({behavior:'smooth',block:'start'});}
      mark(id);
      history.replaceState(null,'','#'+id);
    })});
    if(location.hash==='#member'){mark('member');}
  })();
  </script>
"""

    page("apply.html", "위원·회원기관 신청",
         "한국AI윤리위원회 개인 위원 지원과 기업·기관 회원기관 모집 안내. 모집 분야, 회원기관 혜택, 연회비, 가입 절차를 확인하고 온라인으로 신청하세요.",
         body + cert_band("위원 참여 신청서 작성", "join.html#apply"), extra_script=tab_js,
         keywords=["한국AI윤리위원회 회원기관", "AI 윤리 위원회 가입", "위원회 회원기관 모집", "AI 윤리 위원",
                   "AI 윤리위원", "기업 AI 윤리", "AI 윤리 위원회 회원기관 연회비"])


if __name__ == "__main__":
    print("한국AI윤리위원회 사이트 빌드 중...")
    posts = load_posts()
    print(f"  게시글 {len(posts)}건 발견")
    build_index(posts)
    build_about()
    build_business()
    build_members()
    build_lecture()
    build_expert()
    build_expert_apply()
    build_experts()
    build_join()
    build_quiz()
    build_exam()
    build_partner()
    build_copyclean()
    build_news(posts)
    build_mou()
    build_apply()
    build_legal()
    for p in posts:
        build_post(p, posts)
    build_sitemap(posts)
    build_rss(posts)
    print("완료!")
