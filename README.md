# 카피체크 웹사이트 배포 가이드 (GitHub Pages)

## 구성
- `index.html` — 메인 랜딩페이지 (전체 기능 포함)
- `board/` — SEO용 커뮤니티 게시글 8편 (개별 URL)
- `sitemap.xml`, `robots.txt` — 검색엔진 수집용

## 1. GitHub Pages 배포 (5분)
1. github.com 로그인 → New repository → 이름 예: `copycheck-site` → Public → Create
2. "uploading an existing file" 클릭 → 이 폴더의 파일 전부 드래그(board 폴더 포함) → Commit
3. 리포지토리 Settings → Pages → Branch: `main`, 폴더 `/ (root)` → Save
4. 1~2분 뒤 `https://아이디.github.io/copycheck-site/` 로 접속 확인

## 2. 도메인 치환 (중요)
`sitemap.xml`, `robots.txt`, `board/*.html`(canonical) 안의 `https://YOUR-DOMAIN` 을
실제 주소로 전부 바꾸세요.
- GitHub 기본 주소면: `https://아이디.github.io/copycheck-site`
- 커스텀 도메인(예: copycheck.co.kr) 연결 시: Settings → Pages → Custom domain 입력 후 그 주소로 치환

## 3. 검색 등록 (배포 직후 필수)
- 구글 서치콘솔 search.google.com/search-console → 속성 추가 → 소유 확인 → Sitemaps에 `sitemap.xml` 제출
- 네이버 서치어드바이저 searchadvisor.naver.com → 사이트 등록 → 소유 확인 → 요청 > 사이트맵 제출
- 네이버는 개별 URL 수집 요청도 함께 넣으면 빠릅니다 (요청 > 웹 페이지 수집)

## 4. 이후 운영 팁
- 게시글은 `board/`에 같은 형식의 html을 추가하고 sitemap.xml에 한 줄 추가하면 됩니다
- 같은 글을 카피클린 네이버 블로그에 요약 + 링크로 올리면 네이버 유입이 훨씬 빠릅니다
- 사업자등록번호·통신판매업신고번호 확정 시 index.html 푸터의 TODO 주석 부분을 교체하세요
