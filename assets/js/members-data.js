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
     - track : (선택) 'AI 윤리 위원' 무리에서 '교육'이면 AI 윤리 교육위원(2026.10.03, 캠페인위원 뒤에 표시. 백엔드 위원명단 '구분'과 같게)
     - code  : (선택) 위원 코드. 적으면 카드를 눌렀을 때 뜨는 디지털 명함에 표시됩니다.
     - cred  : (선택) 자격 표기. 직책 앞에 붙어 '변호사 · 법률고문'처럼 표시됩니다.
     - en    : (선택) 영문 이름. 디지털 명함에 대문자로 표시되고, 명함 주소(#shin-dong-bok)에도 쓰입니다.
     - since : (선택) 취임·선임·위촉 시기. 예) '2026.07'  (위원장은 '취임', 부위원장·감사·사무국은 '선임', 그 외는 '위촉'으로 표시)
     - email : (선택) 디지털 명함의 '이메일' 칸과 명함 이미지에 표시. 없으면 위원회 대표 메일(contact@kaiec.kr).
               위원회 주소는 '이름.성@kaiec.kr' 형식 (예: 조현석 → hyunseok.cho@kaiec.kr). 메일함(또는 전달 설정)을 먼저 만들어 두세요.
   ▶ 해당 group에 사람이 한 명도 없으면 그 구분은 화면에 표시되지 않습니다.
   ▶ 전문위원 명단은 '강의 신청' 페이지의 자문 위원단에도 자동으로 표시됩니다.
   ▶ 위원장 항목의 name은 '위원회 소개' 페이지 인사말 서명에도 자동으로 들어갑니다.
   ========================================================================== */

window.KAIEC_MEMBERS = [

  // ── 위원장 ─────────────────────────────────────────────────
  { group: '위원장', role: '위원장', name: '신동복', en: 'Shin Dong-bok', since: '2026.06', field: 'AI 윤리 · 정책', photo: 'shin-dongbok.jpg' },

  // ── 부위원장 ───────────────────────────────────────────────
  { group: '부위원장', role: '부위원장', name: '조현석', en: 'Cho Hyun-seok', email: 'hyunseok.cho@kaiec.kr', since: '2026.07', field: '운영 총괄 · 대외 협력', photo: 'jo-hyunseok.jpg' },

  // ── 고문·자문위원 ─────────────────────────────────────────
  { group: '고문·자문위원', role: '학술고문', name: '임형택', en: 'Lim Hyung-taek', email: 'hyungtaek.lim@kaiec.kr', since: '2026.08', field: '과학기술정책', photo: 'im-hyungtaek.jpg' },
  { group: '고문·자문위원', role: '법률고문', cred: '변호사', name: '한수연', en: 'Han Soo-yeon', email: 'sooyeon.han@kaiec.kr', since: '2026.08', field: 'IT법 · 개인정보 법제 · 저작권', photo: 'han-sooyeon.jpg' },

  // ── 사무국 (감사 포함, 2026.09.26 사용자 지시: 감사는 사무국 안에 표시, 팀장 공석 카드는 표시하지 않음) ──
  { group: '사무국', role: '사무총장', name: '오준호', en: 'Oh Jun-ho', since: '2026.07', field: '사업 기획 · 위원회 운영 총괄', photo: 'oh-junho.jpg' },
  { group: '사무국', role: '감사', name: '윤미정', en: 'Yoon Mi-jeong', email: 'mijeong.yoon@kaiec.kr', since: '2026.07', field: '운영 · 회계 감사', photo: 'yoon-mijeong.jpg' },

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
     - email : (선택) 위원 본인 이메일. 디지털 명함의 '이메일' 칸과 명함 이미지에 표시됩니다(없으면 위원회 대표 메일).
     - since : 위촉 시기 (예: '2026.09')
     - field : 활동 분야 (한 줄로 짧게)
     - photo : (선택) assets/img/members/ 폴더의 사진 파일명. 없으면 이니셜 표시.
   ▶ 카드를 누르면 디지털 명함(사진·영문 이름·위원 코드·위촉 시기·소속·활동 분야·QR)이 열립니다.
     kaiec.kr/members/#PKH3185 처럼 위원 코드를 붙인 주소로 들어오면 그 위원의 명함이 바로 열립니다. */
window.KAIEC_CAMPAIGN_MEMBERS = [
  { name: '박근호', en: 'Park Keun-ho', code: 'PKH3185', email: 'cocopark84@gmail.com', since: '2026.09', field: 'AI 리터러시 교육 · 확산', photo: 'park-geunho.jpg', track: '교육' },
  { name: '조성희', en: 'Cho Sung-hee', code: 'CSH7321', email: 'leonfan@naver.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 확산', photo: 'jo-seonghee.jpg', track: '교육' },
  { name: '지정인', en: 'Ji Jung-in', code: 'JJI0046', email: 'jguy12@hanmail.net', since: '2026.09', field: 'AI 창업 · 책임 있는 AI 비즈니스', photo: 'ji-jeongin.jpg', track: '교육' },
  { name: '안지희', en: 'Ahn Ji-hee', code: 'AJH4650', email: 'cleoahn@naver.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 거버넌스', photo: 'ahn-jihee.jpg', track: '교육' },
  { name: '윤민혜', en: 'Yoon Min-hye', code: 'YMH3271', email: 'ycreator90@naver.com', since: '2026.09', field: 'AI · 미디어 콘텐츠', photo: 'yoon-minhye.jpg', track: '교육' },
  { name: '한선혜', en: 'Han Sun-hye', code: 'HSH1728', email: 'pinehsh728@gmail.com', since: '2026.09', field: 'AX · 디지털 전환 전략', photo: 'han-seonhye.jpg' },
  { name: '한효주', en: 'Han Hyo-ju', code: 'HHJ6913', email: 'coolomo@gmail.com', since: '2026.09', field: 'AI 교육 · 차세대 인재 육성', photo: 'han-hyoju.jpg', track: '교육' },
  { name: '박의진', en: 'Park Ui-jin', code: 'PEJ8661', email: 'uijiny@nate.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 활용', photo: 'park-uijin.jpg', track: '교육' },
  { name: '서완석', en: 'Seo Wan-seok', code: 'SWS7351', email: 'redoxi@naver.com', since: '2026.09', field: 'AI · 디지털 교육 혁신', photo: 'seo-wanseok.jpg' },
  { name: '최재영', en: 'Choi Jae-young', code: 'CJY1882', email: 'kthigh11@naver.com', since: '2026.09', field: 'AI 윤리 · 개인정보 · 저작권 · 정보보안', photo: 'choi-jaeyoung.jpg', track: '교육' },
  { name: '신현정', en: 'Shin Hyun-jung', code: 'SHJ4416', email: 'leafz4@gmail.com', since: '2026.09', field: 'AI 창업 · 비즈니스 혁신', photo: 'shin-hyunjung.jpg', track: '교육' },
  { name: '지하은', en: 'Ji Ha-eun', code: 'JHE6954', email: 'jihaeun070904@naver.com', since: '2026.09', field: '생성형 AI 활용', photo: 'ji-haeun.jpg' },
  { name: '유인호', en: 'Yoo In-ho', code: 'YIH0881', email: 'will.be.ai.data@gmail.com', since: '2026.09', field: 'AI 엔지니어링 · AI 교육', photo: 'yoo-inho.jpg' },
  { name: '이한', en: 'Lee Han', code: 'LH2185', email: 'pastorhanlee@gmail.com', since: '2026.09', field: 'AI · 디지털 교육 확산', photo: 'lee-han.jpg', track: '교육' },
  { name: '김지연', en: 'Kim Ji-yeon', code: 'KJY9275', email: 'jiji8012@naver.com', since: '2026.09', field: 'AI · 디지털 교육', photo: 'kim-jiyeon.jpg', track: '교육' },
  { name: '양대산', en: 'Yang Dae-san', code: 'YDS5505', email: 'tonyment@naver.com', since: '2026.09', field: 'AI 교육 · 미래 인재 양성', photo: 'yang-daesan.jpg' },
  { name: '이찬미', en: 'Lee Chan-mi', code: 'LCM8153', email: 'chanchi-333@naver.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI', photo: 'lee-chanmi.jpg' },
  { name: '안용인', en: 'Ahn Yong-in', code: 'AYI8183', email: 'anyongin@naver.com', since: '2026.09', field: 'AI 디지털 교육 · 리터러시 확산', photo: 'ahn-yongin.jpg' },
  { name: '허윤영', en: 'Heo Yun-young', code: 'HYY6754', email: 'afturn@naver.com', since: '2026.09', field: 'AI 디지털 교육 · 에듀테크 활용', photo: 'heo-yunyoung.jpg', track: '교육' },
  { name: '남가영', en: 'Nam Ka-young', code: 'NKY1125', email: 'movie7414@naver.com', since: '2026.09', field: 'AI · 디지털 교육', photo: 'nam-gayoung.jpg' },
  { name: '김홍석', en: 'Kim Hong-seok', code: 'KHS5076', email: 'iyandi@naver.com', since: '2026.09', field: 'AI 공익 · 사회적 가치', photo: 'kim-hongseok.jpg' },
  { name: '노창희', en: 'Noh Chang-hee', code: 'NCH1080', email: 'mbc1406@naver.com', since: '2026.09', field: 'AI 교육 · 인재 양성', photo: 'noh-changhee.jpg', track: '교육' },
  { name: '정지원', en: 'Chung Ji-won', code: 'JJW3568', email: 'chung356833@gmail.com', since: '2026.09', field: 'AI 인재 양성 · 교육', photo: 'chung-jiwon.jpg', track: '교육' },
  { name: '백형진', en: 'Baek Hyung-jin', code: 'BHJ3169', email: 'prehabex@naver.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 실천', photo: 'baek-hyungjin.jpg', track: '교육' },
  { name: '이종석', en: 'Lee Jong-seok', code: 'LJS9417', email: 'traumhaus@gmail.com', since: '2026.09', field: 'AI 비즈니스 · 창업', photo: 'lee-jongseok.jpg', track: '교육' },
  { name: '김설화', en: 'Kim Sul-hwa', code: 'KSH7667', email: 'sulhwa.kim38@gmail.com', since: '2026.09', field: 'AI 서비스 · 기획', photo: 'kim-sulhwa.jpg' },
  { name: '문정수', en: 'Moon Jung-soo', code: 'MJS9974', email: 'ailiteracy2026@naver.com', since: '2026.09', field: 'AI 리터러시 · 디지털 교육', photo: 'moon-jungsoo.jpg', track: '교육' },
  { name: '진아영', en: 'Jin Ah-young', code: 'JAY3243', email: 'wlsdkdud@icloud.com', since: '2026.09', field: 'AI 안전 · 신뢰', photo: 'jin-ahyoung.jpg' },
  { name: '김민지', en: 'Kim Min-ji', code: 'KMJ2333', email: 'intmkt@naver.com', since: '2026.09', field: 'AI 마케팅 · 커뮤니케이션', photo: 'kim-minji.jpg' },
  { name: '편경석', en: 'Pyun Kyung-seok', code: 'PKS8290', email: 'dreamel@naver.com', since: '2026.09', field: 'AI 교육 · 인재 개발', photo: 'pyun-kyungseok.jpg', track: '교육' },
  { name: '이채만', en: 'Lee Chae-man', code: 'LCM2004', email: 'leechaeman1225@gmail.com', since: '2026.09', field: '생성형 AI 활용 · 업무 혁신', photo: 'lee-chaeman.jpg' },
  { name: '천예준', en: 'Chun Ye-jun', code: 'CYJ8854', email: 'yje10007@gmail.com', since: '2026.09', field: 'AI 스타트업 · 창업', photo: 'chun-yejun.jpg', track: '교육' },
  { name: '김나경', en: 'Kim Na-kyung', code: 'KNK0581', email: 'ngim53369@gmail.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 문화', photo: 'kim-nakyung.jpg' },
  { name: '위희선', en: 'Wi Hee-sun', code: 'WHS1023', email: 'heyum138@naver.com', since: '2026.09', field: 'AI 비즈니스 · 창업 전략', photo: 'wi-heesun.jpg', track: '교육' },
  { name: '조용민', en: 'Cho Yong-min', code: 'CYM7991', email: 'cym1144@naver.com', since: '2026.09', field: 'AI 윤리 · 연구 데이터 · 디지털 교육', photo: 'cho-yongmin.jpg', track: '교육' },
  { name: '임호용', en: 'Lim Ho-yong', code: 'LHY6444', email: 'imyong7@hanmail.net', since: '2026.09', field: '생성형 AI 활용 · 실무 역량 강화', photo: 'lim-hoyong.jpg' },
  { name: '이선미', en: 'Lee Sun-mi', code: 'LSM0738', email: 'soranu@naver.com', since: '2026.09', field: 'AI 윤리 · 디지털 리터러시 교육', photo: 'lee-sunmi.jpg', track: '교육' },
  { name: '전재의', en: 'Jeon Jae-ui', code: 'JJE2931', email: 'jayee72@naver.com', since: '2026.09', field: 'AI 교육 · 전문 인재 양성', photo: 'jeon-jaeui.jpg', track: '교육' },
  { name: '이세라', en: 'Lee Se-ra', code: 'LSR6527', email: 'srluxury17@gmail.com', since: '2026.09', field: 'AI 윤리 · AI 교육 · 인재 양성 · AI 콘텐츠 기획', photo: 'lee-sera.jpg' },
  { name: '한상호', en: 'Han Sang-ho', code: 'HSH4977', email: 'shan@ysu.ac.kr', since: '2026.09', field: '생성형 AI 활용 · 확산', photo: 'han-sangho.jpg', track: '교육' },
  { name: '김효정', en: 'Kim Hyo-jung', code: 'KHJ7342', email: 'khj1000sa@hanmail.net', since: '2026.09', field: 'AI 디지털 교육', photo: 'kim-hyojung.jpg', track: '교육' },
  { name: '박경림', en: 'Park Kyung-rim', code: 'PKR4193', email: 'seconew.studio@gmail.com', since: '2026.09', field: 'AI 교육 · AI 인재 양성', photo: 'park-kyungrim.jpg' },
  { name: '이현지', en: 'Lee Hyun-ji', code: 'LHJ0645', email: 'hjl9918@gmail.com', since: '2026.09', field: 'AI 미디어 · 콘텐츠', photo: 'lee-hyunji.jpg' },
  { name: '이인아', en: 'Lee In-a', code: 'LIA3545', email: 'ainorinuri@gmail.com', since: '2026.09', field: 'AI 창업 · 비즈니스', photo: 'lee-ina.jpg', track: '교육' },
  { name: '서유미', en: 'Seo Yu-mi', code: 'SYM2503', email: 'seoyoume77@gmail.com', since: '2026.09', field: 'AI 공익 · 사회적 가치 실현', photo: 'seo-yumi.jpg', track: '교육' },
  { name: '배윤주', en: 'Bae Yun-ju', code: 'BYJ8478', email: 'globalcode77@gmail.com', since: '2026.09', field: 'AI 디지털 교육 · 역량 강화', photo: 'bae-yunju.jpg', track: '교육' },
  { name: '김진영', en: 'Kim Jin-young', code: 'KJY0902', email: 'jin00902@gmail.com', since: '2026.09', field: 'AI 공익 · 사회적 가치 확산', photo: 'kim-jinyoung.jpg', track: '교육' },
  { name: '이채연', en: 'Lee Chae-yeon', code: 'LCY3431', email: 'chaeyeon4898@naver.com', since: '2026.09', field: 'AI 서비스 · 기획 실무', photo: 'lee-chaeyeon.jpg' },
  { name: '김은혜', en: 'Kim Eun-hye', code: 'KEH1225', email: 'eh44mo@naver.com', since: '2026.09', field: 'AI 윤리 교육 · 디지털 리터러시', photo: 'kim-eunhye.jpg', track: '교육' },
  { name: '송성인', en: 'Song Sung-in', code: 'SSI9133', email: 'song.sinn0917@gmail.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 인식 제고', photo: 'song-seongin.jpg' },
  { name: '강지예', en: 'Kang Ji-ye', code: 'KJY9139', email: 'yeah.kang@gmail.com', since: '2026.09', field: 'AI 디지털 교육 · 미래 역량', photo: 'kang-jiye.jpg' },
  { name: '박기화', en: 'Park Ki-hwa', code: 'PKH5517', email: 'pgw1001@naver.com', since: '2026.09', field: '생성형 AI 활용 · 교육', photo: 'park-kihwa.jpg', track: '교육' },
  { name: '김소정', en: 'Kim So-jung', code: 'KSJ5700', email: 'misqm@naver.com', since: '2026.09', field: 'AI 윤리 · 책임 있는 AI 소통', photo: 'kim-sojung.jpg', track: '교육' },
  { name: '최상미', en: 'Choi Sang-mi', code: 'CSM1130', email: 'miya3204@naver.com', since: '2026.09', field: 'AI 디지털 교육 · AI 에듀테크', photo: 'choi-sangmi.jpg', track: '교육' },
  { name: '윤지희', en: 'Yoon Ji-hee', code: 'YJH7807', email: 'hopefulearth@gmail.com', since: '2026.09', field: '생성형 AI 활용 · 리터러시', photo: 'yoon-jihee.jpg' },
  { name: '이은미', en: 'Lee Eun-mi', code: 'LEM9135', email: 'newayssister@naver.com', since: '2026.10', field: 'AI 윤리 · 책임 있는 AI 실현', photo: 'lee-eunmi.jpg' },
  { name: '김세희', en: 'Kim Se-hee', code: 'KSH1859', email: 'wintersnow3@naver.com', since: '2026.10', field: 'AI 저작권 · 콘텐츠 윤리', photo: 'kim-sehee.jpg' },
  { name: '조아라', en: 'Cho Ah-ra', code: 'CAR3312', email: 'keunissaem@gmail.com', since: '2026.10', field: 'AI 윤리 · 디지털 교육 · 미디어 콘텐츠 기획', photo: 'cho-ahra.jpg' },
  { name: '김범수', en: 'Kim Bum-soo', code: 'KBS9649', email: 'ogg812@naver.com', since: '2026.10', field: 'AI 윤리 · 책임 있는 AI 구현', photo: 'kim-bumsoo.jpg' },
  { name: '왕정미', en: 'Wang Jung-mi', code: 'WJM2133', email: 'wang-j-m@hanmail.net', since: '2026.10', field: 'AI · 디지털 교육 활성화', photo: 'wang-jungmi.jpg', track: '교육' },
  { name: '김다혜', en: 'Kim Da-hye', code: 'KDH0601', email: 'ekgp0601@naver.com', since: '2026.10', field: 'AI 디자인 · 크리에이티브', photo: 'kim-dahye.jpg' },
  { name: '김경숙', en: 'Kim Kyung-sook', code: 'KKS0629', email: 'itel76@naver.com', since: '2026.10', field: 'AI · 디지털 역량 교육', photo: 'kim-kyungsook.jpg', track: '교육' },
  { name: '정희영', en: 'Jung Hee-young', code: 'JHY0531', email: 'hyjung@deepnoid.com', since: '2026.10', field: 'AI 개인정보 · 데이터 윤리', photo: 'jung-heeyoung.jpg' },
  { name: '김용주', en: 'Kim Yong-ju', code: 'KYJ4247', email: 'funny7465@naver.com', since: '2026.10', field: 'AI 윤리 · 책임 있는 AI 생태계', photo: 'kim-yongju.jpg' },
  { name: '이숙영', en: 'Lee Sook-young', code: 'LSY4033', email: 'kikikibook@naver.com', since: '2026.10', field: 'AI 에듀테크', photo: 'lee-sookyoung.jpg', track: '교육' },
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
