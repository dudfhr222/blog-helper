# 포스팅 운영 규칙

## 발행 전 체크리스트

- [ ] 본문 길이 1800자 이상
- [ ] 이모지 2개 이하
- [ ] 광고/과장 표현 없음
- [ ] primary keyword 상단 200자 내 배치
- [ ] 제목 40자 이내
- [ ] 태그 10개 이내
- [ ] 메타 설명 150자 이내
- [ ] quality_gate passed=True
- [ ] 본문의 모든 `{{IMG:slug}}`에 대응하는 image_plan 항목 존재
- [ ] image_plan 모든 항목의 path에 실제 파일 존재 확인
- [ ] 이미지 파일 확장자 허용 목록 내 (.jpg/.jpeg/.png/.gif/.webp)

## 발행 모드

| 모드 | 설명 | 기본값 |
|------|------|--------|
| `draft-only` | 글 생성 + 검증까지만, 발행 안 함 | 기본 |
| `publish` | 실제 발행 수행 | 명시적 요청 시 |

### 왜 draft-only가 기본인가

- 블로그는 **누적 자산** → 잘못된 발행은 되돌리기 어려움
- 검증 게이트를 통과해야만 발행 가능 → 안전망
- 글만 뽑아도 가치가 큼 (발행은 수동으로도 가능)

## 발행 후 필수 작업

1. 발행 URL 확인 및 접근 검증
2. 초안 → `outputs/published/`로 아카이브
3. 배포 문구 생성 (growth_manager)
4. 24시간 후 초기 성과 확인

## 산출물 관리

### 파일 명명 규칙

| 산출물 | 형식 | 예시 |
|--------|------|------|
| 초안 | `draft_YYYYMMDD_[slug].md` | `draft_20260309_claude_agent.md` |
| 아웃라인 | `outline_YYYYMMDD_[slug].md` | `outline_20260309_claude_agent.md` |
| PostMeta | `post_meta_YYYYMMDD_[slug].json` | `post_meta_20260309_claude_agent.json` |
| 발행 글 | `post_YYYYMMDD_[slug].md` | `post_20260309_claude_agent.md` |
| 분석 리포트 | `analytics_YYYYMMDD.md` | `analytics_20260309.md` |

### slug 생성 규칙

- 주제에서 핵심 단어 2~3개 추출
- 소문자, 영문, 언더스코어
- 예: "Claude Code Agent 아키텍처" → `claude_agent_architecture`

## 재실행 규칙

- 동일 run_id 폴더 내 파일은 덮어쓰지 않음
- 재실행 시 새로운 날짜 기반 파일 생성
- 이전 버전은 보존 (비교 가능)
