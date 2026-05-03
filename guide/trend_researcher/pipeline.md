# Trend Researcher — Pipeline 상세

## 트렌드 수집 소스 우선순위

| 소스 | 도구 | 우선순위 |
|------|------|----------|
| HackerNews | WebFetch (`news.ycombinator.com`) | 1 |
| Reddit | WebFetch (`reddit.com/r/programming` 등) | 2 |
| Google Trends | WebSearch | 3 |
| 기술 블로그 | WebFetch (주요 블로그 RSS) | 4 |
| 뉴스 | WebSearch | 5 |

## 주제 선정 기준 (가중치)

| 기준 | 가중치 | 설명 |
|------|--------|------|
| 시의성 | 30% | 최근 3일 이내 화제성 |
| 검색 유입 가능성 | 25% | 키워드 검색량 + 경쟁도 |
| 블로그 적합성 | 25% | 타겟 독자와의 관련성 |
| 차별화 가능성 | 20% | 기존 콘텐츠 대비 새로운 관점 |

## 중복 체크

- `outputs/drafts/posts/*/draft.md` 내 기존 파일 제목과 비교
- 동일 주제가 30일 이내 작성된 경우 → 제외 또는 "업데이트 관점" 제안

## 출력 문서 구조

```markdown
---
created: YYYY-MM-DD
mode: quick_scan / deep_research / keyword_analysis
category_filter: 개발/AI
---

# 주제 후보 — YYYY-MM-DD

## 후보 목록

### 1. [주제명]
- **카테고리**: 개발/AI
- **소스**: HackerNews (URL)
- **트렌드 근거**: 최근 3일간 500+ upvotes
- **추천 키워드**: keyword1, keyword2, keyword3
- **예상 검색 유입**: 높음 / 중간 / 낮음
- **추천 톤**: 담백한 / 친근한 / 전문적

## 분석 요약
- 이번 주 주요 트렌드: ...
- 추천 우선순위: 1 > 3 > 2 (근거: ...)

## proposed_calendar_rows
growth_manager[strategy_update] + calendar_updater가 읽는 섹션.
아래 포맷으로 최대 3행 제안:

| 날짜 | 주제 | 카테고리 | 상태 |
|------|------|----------|------|
| YYYY-MM-DD | [주제] | [카테고리] | planned |
```
