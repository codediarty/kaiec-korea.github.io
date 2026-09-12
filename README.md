# 한국AI윤리협회(KAIEC) 공식 홈페이지

- 주소: https://kaiec.kr (GitHub Pages, main 브랜치 루트에서 서빙, 커스텀 도메인은 CNAME 파일)
- 저장소: codediarty/kaiec-korea.github.io

## 구조
- `build.py`: 정적 페이지 생성기. 메뉴, 푸터, 상수(결제 링크, 웹훅, 가격)를 모두 여기서 관리합니다.
- `icons.py`: 아이콘 SVG 모음 (build.py가 HTML에 직접 삽입)
- `posts-src/*.md`: 커뮤니티 게시글 원본. 파일 1개가 게시글 1개 (`posts-src/_작성방법.txt` 참고)
- `assets/`: CSS, JS, 이미지. `assets/js/*-data.js`는 위원 명단, 연혁, 제휴 기관 데이터
- `about/`, `expert/`, `news/<slug>/` 등: build.py가 생성하는 결과물 (직접 수정하지 말 것)
- `tools/verify.py`: 빌드 결과 전체 검증 (마지막 줄에 "전체 통과"가 나와야 배포)

## 작업 순서
1. 수정 (build.py, posts-src, assets)
2. `python3 build.py`
3. `python3 tools/verify.py` 에서 "전체 통과" 확인
4. 커밋, 푸시 (GitHub Pages가 1~2분 안에 자동 배포)
5. https://kaiec.kr 에서 반영 확인

자세한 규칙과 이력은 `작업-메모.md`, 처음 배포하는 절차는 `배포-가이드.md`를 참고하세요.
