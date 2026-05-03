# Growth Manager — Pipeline 상세

## 배포 채널별 문구 규칙

| 채널 | 문구 규칙 |
|------|----------|
| Twitter/X | 140자 이내, 핵심 포인트 1개 + 해시태그 3개 + URL |
| LinkedIn | 전문적 톤, 3문장 요약 + URL |
| 커뮤니티 | 커뮤니티 규칙 준수, 자기홍보 톤 자제, 가치 제공 중심 |

## distribution_log 출력 형식

```markdown
---
created: YYYY-MM-DD
post_url: https://blog.naver.com/...
---

# 배포 로그 — YYYY-MM-DD

## Twitter/X
- 상태: 완료 / 대기
- 문구: "..."
- 해시태그: #tag1 #tag2

## LinkedIn
- 상태: 완료 / 대기
- 문구: "..."

## 커뮤니티
- 대상: velog, disquiet
- 상태: 초안 생성됨
```

## analytics_report 출력 형식

```markdown
---
created: YYYY-MM-DD
period: 7d
---

# 성과 분석 리포트 — YYYY-MM-DD

## 기간: YYYY-MM-DD ~ YYYY-MM-DD

## 카테고리별 성과

| 카테고리 | 조회수 | 체류시간 | 검색 유입 | 공감 |
|----------|--------|----------|-----------|------|
| 개발/AI | 높음 | 중간 | 높음 | 낮음 |

## 상위 콘텐츠 (조회수 기준)
1. [제목] — 조회수 X, 체류시간 Y분

## 상위 유입 키워드
1. keyword1 — N회

## 인사이트
- ...

## 다음 주 추천 전략
- ...
```

## strategy_proposal 출력 형식

```markdown
# 전략 업데이트 제안 — YYYY-MM-DD

## 현재 전략 요약
(content_calendar 기준)

## 성과 기반 변경 제안

### 1. 카테고리 비중 조정
- 개발/AI: 40% → 50% (근거: 조회수 +30%)

### 2. 키워드 전략
- 신규 타겟: keyword1, keyword2

### 3. 콘텐츠 캘린더 수정안
| 요일 | 기존 | 제안 |
|------|------|------|
| 월 | AI 트렌드 | AI 트렌드 (유지) |
```

## 전략 제안 판단 로직

| 성과 패턴 | 전략 제안 |
|-----------|----------|
| 특정 카테고리 조회수 급등 | 해당 카테고리 비중 확대 |
| 특정 키워드 유입 증가 | 관련 주제 시리즈 제안 |
| 체류시간 높은 글 | 유사 구조/톤 반복 |
| 전체 조회수 하락 | 트렌드 리서치 강화, 신규 카테고리 실험 |

## content_calendar 자동 갱신 (calendar_updater 연동)

strategy_update 모드 실행 시:
1. 성과 분석 결과 + trend_researcher의 `proposed_calendar_rows`를 종합
2. `scripts/workflows/calendar_updater.py`가 `inputs/content_calendar.md`의 `<!-- AUTO_PLAN_BEGIN -->` ~ `<!-- AUTO_PLAN_END -->` 마커 영역만 갱신
3. 마커 외부는 절대 변경하지 않음 — diff를 stdout으로 출력하여 사용자가 검토 가능

## analytics 서브모드

| 서브모드 | 설명 | 트리거 |
|----------|------|--------|
| `web_scrape` | `scripts/workflows/analytics_collector.py`로 자동 수집 | 기본값 |
| `manual_input` | 사용자에게 KPI 수치를 직접 질문하여 입력 | web_scrape 실패 시 자동 폴백 |

폴백 문구: "네이버 블로그 통계에서 다음 수치를 확인하여 입력해주세요: 조회수, 유입 키워드 Top 5, 공감 수"
