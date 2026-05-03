# Design Agent Reference

블로그 디자인 에이전트가 레이아웃, 타이포그래피, 색상, 컴포넌트 패턴을 뽑을 때 참고하는 레퍼런스 문서다.

## 목적

- 디자인 요청이 들어오면 먼저 실제 블로그/웹사이트 레퍼런스를 기준으로 방향을 잡는다.
- 단순히 예쁜 홈 화면이 아니라 글을 읽는 경험을 우선한다.
- 티스토리 스킨 CSS 생성 시 기존 구조를 크게 깨지 않는 범위에서 개선안을 만든다.

## 호출 기준

다음 요청은 `design_agent`로 라우팅한다.

- 블로그 디자인, 스킨, CSS, 테마, 레이아웃, 폰트, 색상 수정
- 티스토리 본문 가독성, 글 목록 카드, 헤더, 사이드바, 목차, 관련 글 영역 개선
- 특정 레퍼런스 사이트와 비슷한 분위기의 블로그 디자인 생성
- `outputs/design/css/custom_*.css` 생성 또는 기존 CSS 백업 기반 수정
- 작업 종료 시 `Logs/design_agent/YYYYMMDD_HHMMSS_[task_slug].md`에 요청, 참고 레퍼런스, 산출물, 적용 전 확인사항을 기록

호출 전에는 이 문서를 읽고, 필요한 경우 아래 레퍼런스에서 2~5개를 골라 디자인 근거로 삼는다.

## 핵심 원칙

1. 글 상세 페이지가 우선이다.
   - 홈 화면보다 본문 폭, 줄간격, 제목 계층, 이미지 캡션, 코드블록, 목차, 관련 글 영역이 중요하다.
2. 블로그는 읽기 도구다.
   - 본문 폭은 보통 600~800px 범위가 안정적이다.
   - 본문 폰트 크기는 16~20px 범위에서 결정한다.
   - 장식보다 스캔 가능성, 탐색성, 모바일 가독성을 우선한다.
3. 기존 스킨을 존중한다.
   - `outputs/design/backups/backup_*.css`가 있으면 최신 백업을 먼저 읽는다.
   - 기본은 append 방식 override다.
   - replace는 사용자가 명시하고 위험성을 확인한 경우에만 사용한다.
4. 레퍼런스는 패턴만 가져온다.
   - 특정 사이트의 시각 요소를 그대로 복제하지 않는다.
   - 레이아웃 구조, 여백감, 타이포 계층, 컴포넌트 구성만 추출한다.

## 블로그 특화 레퍼런스

| 사이트 | URL | 참고 포인트 |
|--------|-----|-------------|
| SiteBuilderReport - Blog Design Examples | https://www.sitebuilderreport.com/inspiration/blog-design-examples | 블로그 홈, 글 상세, 카드 그리드, 매거진형 구성 |
| Web3Inspiration - Blog Detail Page Examples | https://web3inspiration.com/inspirations/best-blog-post-pages | 아티클 상세 페이지, 목차, CTA, 관련 글 영역 |
| Squarespace Blog Examples | https://www.sitebuilderreport.com/inspiration/squarespace-blog-examples | 에디토리얼형 블로그, 이미지 중심 카드, 카테고리 구조 |

## 웹 디자인 갤러리

| 사이트 | URL | 참고 포인트 |
|--------|-----|-------------|
| Siteinspire | https://www.siteinspire.com/ | 미니멀, 타이포그래피, 포트폴리오/매거진 감도 |
| Awwwards Websites | https://www.awwwards.com/websites/ | 고급 인터랙션, 최신 웹 디자인 트렌드 |
| Httpster | https://httpster.net/ | 타이포그래피 중심, 미니멀/브루탈리즘 계열 |
| Land-book | https://land-book.com/ | 랜딩, SaaS, 브랜드 사이트 레이아웃 |
| Godly.design | https://godly.design/ | 실제 제품 UI와 웹 섹션 패턴 |
| Collected | https://collected.li/ | 무작위 큐레이션 기반 폭넓은 무드 탐색 |
| Landdding | https://landdding.com/ | 최신 랜딩 페이지와 템플릿 패턴 |
| TOOOLS.design | https://www.toools.design/ui-web-design-inspiration-websites | 디자인 레퍼런스 허브 |

## UI/패턴 참고

| 사이트 | URL | 참고 포인트 |
|--------|-----|-------------|
| Mobbin | https://mobbin.com/ | 실제 웹/앱 화면, 필터, 리스트, 카드, 내비게이션 패턴 |
| DevInspo | https://www.devinspo.com/ | 여러 inspiration 사이트를 찾기 위한 허브 |

## 국내 블로그 레퍼런스

| 사이트 | URL | 참고 포인트 |
|--------|-----|-------------|
| 토스 기술 블로그 | https://toss.tech/ | 큰 카드, 명확한 카테고리, 기술/디자인/제품 분류 |
| 카카오테크 블로그 | https://tech.kakao.com/blog | 태그 탐색, 기술 블로그형 정보 구조 |
| 카카오벤처스 블로그 | https://blog.kakao.vc/ | VC/인사이트형 에디토리얼 톤 |
| 네이버 D2 | https://d2.naver.com/ | 개발자 대상 기술 글 아카이브 |
| 우아한형제들 기술블로그 | https://techblog.woowahan.com/ | 조직 문화와 기술 글을 함께 다루는 구조 |
| 요즘IT | https://yozm.wishket.com/magazine/ | 매거진형 썸네일, 태그, 제목 구조 |
| 브런치스토리 | https://brunch.co.kr/ | 글 중심 독서 경험, 간결한 본문 스타일 |

## 추출 스키마

디자인 레퍼런스를 분석할 때는 URL만 나열하지 말고 아래 형태로 패턴을 추출한다.

```json
{
  "page_type": "blog_home | article_detail | category_page",
  "layout": "grid | list | magazine | sidebar | single-column",
  "typography": {
    "title_style": "",
    "body_width": "",
    "line_height": ""
  },
  "color_palette": [],
  "components": ["hero", "post_card", "tag_filter", "toc", "newsletter", "related_posts"],
  "interaction": ["hover", "scroll", "sticky_toc"],
  "notable_patterns": []
}
```

## CSS 생성 체크리스트

- 최신 `outputs/design/backups/backup_*.css`를 확인했는가?
- 본문 상세 페이지 가독성이 개선되는가?
- 모바일 `@media (max-width: 768px)` 대응이 필요한 변경인가?
- 전역 셀렉터 수정이 과하지 않은가?
- 외부 폰트를 쓰면 `@import` 또는 로딩 전략이 포함되어 있는가?
- `position: fixed`, 과도한 `z-index`, 광범위한 `!important`를 피했는가?
- 결과 파일은 `outputs/design/css/custom_YYYYMMDD_HHMMSS.css`에 생성되는가?

## 에이전트 출력 기준

디자인 에이전트는 완료 시 다음을 포함한다.

- 참고한 레퍼런스 2~5개
- 적용한 디자인 패턴 요약
- 생성된 CSS 파일 경로
- dry-run 명령어
- 실제 적용 명령어

예시:

```text
생성 완료: outputs/design/css/custom_YYYYMMDD_HHMMSS.css

참고 레퍼런스:
- 토스 기술 블로그: 카드형 목록과 명확한 카테고리 구조
- SiteBuilderReport Blog Examples: 본문 폭과 글 상세 레이아웃 기준

테스트 먼저:
python -m scripts.platforms.tistory.css_patcher --patch --css outputs/design/css/custom_YYYYMMDD_HHMMSS.css --dry-run

적용:
python -m scripts.platforms.tistory.css_patcher --patch --css outputs/design/css/custom_YYYYMMDD_HHMMSS.css
```
