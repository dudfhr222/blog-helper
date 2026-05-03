# 트렌드 데이터 소스

## 소스 목록

| 소스 | URL | 카테고리 | 우선순위 | 수집 방법 |
|------|-----|----------|----------|----------|
| HackerNews | `news.ycombinator.com` | 개발/AI | 1 | WebFetch (Front Page) |
| Reddit r/programming | `reddit.com/r/programming` | 개발/AI | 2 | WebFetch (Hot Posts) |
| Reddit r/MachineLearning | `reddit.com/r/MachineLearning` | 개발/AI | 2 | WebFetch (Hot Posts) |
| Google Trends | `trends.google.com` | 전체 | 3 | WebSearch |
| TechCrunch | `techcrunch.com` | 개발/AI | 4 | WebFetch (RSS) |
| The Verge | `theverge.com` | 개발/AI | 4 | WebFetch |
| GeekNews | `news.hada.io` | 개발/AI | 1 | WebFetch (한국어 기술 트렌드) |

## 카테고리별 소스

### 개발/AI
- HackerNews, Reddit, GeekNews (1순위)
- TechCrunch, The Verge (보조)
- Google Trends (검색 트렌드 확인)

### 맛집
- 네이버 블로그 검색 (인기글)
- 망고플레이트 / 다이닝코드
- Google Trends (로컬 검색)

### 여행
- 네이버 블로그 검색 (인기글)
- 트립어드바이저
- Google Trends (여행 키워드)

## 수집 규칙

| 규칙 | 설명 |
|------|------|
| 시의성 | 최근 3일 이내 게시/업데이트된 콘텐츠 우선 |
| 인기도 | upvotes/likes 기준 상위 20% 필터 |
| 중복 제거 | 동일 주제 30일 이내 기존 포스팅과 비교 |
| 언어 | 영어 + 한국어 소스 모두 수집, 산출물은 한국어 |
