/* =============================================================================
   위원 명단 데이터
   -----------------------------------------------------------------------------
   ▶ 위원을 추가하려면 아래 배열에 { } 한 줄을 복사해서 추가하세요.
     - group : 아래 6가지 중 하나 (이 순서대로 화면에 구분되어 표시됩니다)
       '위원장' | '부위원장' | '감사' | '고문·자문위원' | '사무국' | '전문위원'
     - AI 윤리 캠페인위원은 아래 KAIEC_CAMPAIGN_MEMBERS 배열에 따로 적습니다(전문위원 바로 아래 표시).
     - name을 '공석'으로 쓰면 회색 공석 카드로 표시됩니다.
     - role  : 화면에 파랗게 표시되는 직책
     - name  : 성명
     - field : 전문분야 / 담당 (한 줄로 짧게)
     - photo : (선택) assets/img/members/ 폴더에 넣은 사진 파일명. 없으면 이니셜 표시.
     - code  : (선택) 위원 코드. 적으면 카드를 눌렀을 때 뜨는 디지털 명함에 표시됩니다.
     - cred  : (선택) 자격 표기. 직책 앞에 붙어 '변호사 · 법률고문'처럼 표시됩니다.
     - en    : (선택) 영문 이름. 디지털 명함에 대문자로 표시되고, 명함 주소(#shin-dong-bok)에도 쓰입니다.
     - since : (선택) 취임·선임·위촉 시기. 예) '2026.07'  (위원장은 '취임', 부위원장·감사·사무국은 '선임', 그 외는 '위촉'으로 표시)
   ▶ 해당 group에 사람이 한 명도 없으면 그 구분은 화면에 표시되지 않습니다.
   ▶ 전문위원 명단은 '강의 신청' 페이지의 자문 위원단에도 자동으로 표시됩니다.
   ▶ 위원장 항목의 name은 '위원회 소개' 페이지 인사말 서명에도 자동으로 들어갑니다.
   ========================================================================== */

window.KAIEC_MEMBERS = [

  // ── 위원장 ─────────────────────────────────────────────────
  { group: '위원장', role: '위원장', name: '신동복', en: 'Shin Dong-bok', since: '2026.06', field: 'AI 윤리 · 정책', photo: 'shin-dongbok.jpg' },

  // ── 부위원장 ───────────────────────────────────────────────
  { group: '부위원장', role: '부위원장', name: '조현석', en: 'Cho Hyun-seok', since: '2026.07', field: '운영 총괄 · 대외 협력', photo: 'jo-hyunseok.jpg' },

  // ── 고문·자문위원 ─────────────────────────────────────────
  { group: '고문·자문위원', role: '학술고문', name: '임형택', en: 'Lim Hyung-taek', since: '2026.08', field: '과학기술정책', photo: 'im-hyungtaek.jpg' },
  { group: '고문·자문위원', role: '법률고문', cred: '변호사', name: '한수연', en: 'Han Soo-yeon', since: '2026.08', field: 'IT법 · 개인정보 법제 · 저작권', photo: 'han-sooyeon.jpg' },

  // ── 사무국 (감사 포함, 2026.09.26 사용자 지시: 감사는 사무국 안에 표시, 팀장 공석 카드는 표시하지 않음) ──
  { group: '사무국', role: '사무총장', name: '오준호', en: 'Oh Jun-ho', since: '2026.07', field: '사업 기획 · 위원회 운영 총괄', photo: 'oh-junho.jpg' },
  { group: '사무국', role: '감사', name: '윤미정', en: 'Yoon Mi-jeong', since: '2026.07', field: '운영 · 회계 감사', photo: 'yoon-mijeong.jpg' },

  // ── 전문위원 (교육·리터러시 분과 · AI 윤리 교육 담당) ────────
  { group: '전문위원', role: '전문위원 · 교육·리터러시 분과', name: '김동섭', en: 'Kim Dong-seop', since: '2026.08', field: 'AI 윤리 교육 · 성균관대 공학 박사', photo: 'kim-dongseop.jpg' },
  { group: '전문위원', role: '전문위원 · 교육·리터러시 분과', name: '이재이', en: 'Lee Jae-yi', since: '2026.08', field: 'AI 윤리 교육 · 이화여대 이학 석사', photo: 'lee-jaei.jpg' },

  // ↓ 여기에 계속 추가하세요.

];

/* ── AI 윤리 캠페인위원 ─────────────────────────────────────
   위원 명단에서 전문위원 바로 아래, 같은 크기의 카드로 표시됩니다.
   위촉되면 아래에 한 줄씩 추가하세요. 적은 순서대로(위촉 순) 표시됩니다.
     - name  : 성명
     - en    : 영문 이름 (위원 코드 이니셜과 맞춰 적기, 예: 박근호 → Park Keun-ho)
     - code  : 위원 코드 = 성명 영문 이니셜 + 휴대전화 뒷자리 4개 (예: 박근호, 휴대전화 뒷자리 3185 → PKH3185)
     - since : 위촉 시기 (예: '2026.09')
     - field : 활동 분야 (한 줄로 짧게)
     - photo : (선택) assets/img/members/ 폴더의 사진 파일명. 없으면 이니셜 표시.
   ▶ 카드를 누르면 디지털 명함(사진·영문 이름·위원 코드·위촉 시기·소속·활동 분야·QR)이 열립니다.
     kaiec.kr/members/#PKH3185 처럼 위원 코드를 붙인 주소로 들어오면 그 위원의 명함이 바로 열립니다. */
window.KAIEC_CAMPAIGN_MEMBERS = [
  { name: '박근호', en: 'Park Keun-ho', code: 'PKH3185', since: '2026.09', field: 'AI 리터러시 교육 · 확산', photo: 'park-geunho.jpg' },
  { name: '조성희', en: 'Cho Sung-hee', code: 'CSH7321', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 확산', photo: 'jo-seonghee.jpg' },
  { name: '지정인', en: 'Ji Jung-in', code: 'JJI0046', since: '2026.09', field: 'AI 창업 · 책임 있는 AI 비즈니스', photo: 'ji-jeongin.jpg' },
  { name: '서완석', en: 'Seo Wan-seok', code: 'SWS7351', since: '2026.09', field: 'AI · 디지털 교육 혁신', photo: 'seo-wanseok.jpg' },
  { name: '양대산', en: 'Yang Dae-san', code: 'YDS5505', since: '2026.09', field: 'AI 교육 · 미래 인재 양성', photo: 'yang-daesan.jpg' },
  { name: '허윤영', en: 'Heo Yun-young', code: 'HYY6754', since: '2026.09', field: 'AI 디지털 교육 · 에듀테크 활용', photo: 'heo-yunyoung.jpg' },
  { name: '한효주', en: 'Han Hyo-ju', code: 'HHJ6913', since: '2026.09', field: 'AI 교육 · 차세대 인재 육성', photo: 'han-hyoju.jpg' },
  { name: '임호용', en: 'Lim Ho-yong', code: 'LHY6444', since: '2026.09', field: '생성형 AI 활용 · 실무 역량 강화', photo: 'lim-hoyong.jpg' },
  { name: '안지희', en: 'Ahn Ji-hee', code: 'AJH4650', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 거버넌스', photo: 'ahn-jihee.jpg' },
  // 예) { name: '홍길동', en: 'Hong Gil-dong', code: 'HGD1234', since: '2026.10', field: 'AI 윤리 캠페인 · 확산', photo: 'hong-gildong.jpg' },
];

/* ── 공식 파트너 ────────────────────────────────────────────
   위원 명단 페이지 맨 아래 '공식 파트너'에 표시됩니다. 계속 추가 가능.
   logo: assets/img/ 폴더의 로고 파일명 (없으면 기관명 텍스트로 표시) */
window.KAIEC_OFFICIAL_PARTNERS = [
  { name: '성균관대학교 RISE사업단', logo: 'partner-rise.jpg', url: '' },
  { name: '성균관컨설팅', logo: '', url: 'https://www.skkc.co.kr' },
  { name: '카피클린 (CopyClean)', logo: '', url: '/copyclean/' },
  // ↓ 여기에 계속 추가하세요.
];
