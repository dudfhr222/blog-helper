# Blog AI Team — 블로그 자동화 시스템

Claude Agent 조직 구조 기반 블로그 자동화 시스템.  
트렌드 리서치부터 Playwright 브라우저 발행, 성과 분석까지 7개 전문 Agent가 파이프라인을 구성한다.

**지원 플랫폼**: 네이버 블로그, 티스토리

---

## 목차

- [시작하기](#시작하기)
- [아키텍처](#아키텍처)
- [사용법](#사용법)
- [운영 규칙](#운영-규칙)
- [참조](#참조)

---

## 시작하기

### 1. 환경 설치

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r scripts/requirements.txt
playwright install chromium
```

### 2. 설정 파일 작성

```powershell
copy inputs\blog_config.example.yaml inputs\blog_config.yaml
```

`inputs/blog_config.yaml`을 열어 `(설정 필요)` 항목을 채운다.

| 항목 | 위치 | 설명 |
|------|------|------|
| `active_platform` | 최상단 | `"naver"` \| `"tistory"` \| `["naver","tistory"]` |
| `naver.blog_id` | `platforms.naver` | blog.naver.com/[blog_id] |
| `tistory.blog_name` | `platforms.tistory` | [blog_name].tistory.com |
| `category_ids` | 각 플랫폼 | 플랫폼별 카테고리 번호/명 |

### 3. 세션 초기화 (최초 1회)

```powershell
# 카테고리 ID 확인
python -m scripts.platforms.naver.publisher --dump-categories

# 브라우저 수동 로그인 → 세션 저장
python -m scripts.platforms.naver.publisher --save-session

# 설정 검증
python -m scripts.platforms.naver.publisher --check-config
```

### 4. E2E 스모크 테스트

```powershell
python -m scripts.workflows.e2e_smoke        # 브라우저 표시
python -m scripts.workflows.e2e_smoke --headless
```

비공개 테스트 게시글이 발행되면 네이버/티스토리에서 수동 삭제한다.  
상세 절차: `guide/operations/operations_setup.md` §1~§7

---

## 아키텍처

### Agent 구성

오케스트레이터(`CLAUDE.md`)가 7개 전문 Agent를 조율한다.  
Agent 프롬프트 정의(`.claude/agents/`)는 시스템 IP로 공개 저장소에서 제외된다.

| Agent | 역할 | 관련 스크립트 |
|-------|------|-------------|
| `trend_researcher` | 트렌드 수집, 주제 후보, 키워드 분석 | — |
| `content_writer` | 아웃라인 → 초안 → SEO 최적화 | — |
| `image_agent` | `image_plan.json` 기반 이미지 자동 생성 | `scripts/core/image_generator.py` |
| `quality_gate` | 5-rule 검증, 자동 수정, 이미지 플랜 | `scripts/quality/image_validator.py` |
| `publisher` | Playwright 브라우저 발행, URL 검증 | `scripts/platforms/*/publisher.py` |
| `growth_manager` | SNS 배포, 성과 분석, 전략 피드백 | `scripts/workflows/analytics_collector.py` |
| `design_agent` | 티스토리 skin.html + CSS 설계 | `scripts/platforms/tistory/skin_patcher.py` |

### 파이프라인 플로우

| Flow | 체인 | 사용 시점 |
|------|------|----------|
| `content_pipeline_flow` | trend_researcher → content_writer → quality_gate → publisher → growth_manager | 주제 미정, 전체 자동화 |
| `quick_post_flow` | content_writer → quality_gate → publisher | 주제 확정, 빠른 발행 |
| `analysis_flow` | growth_manager[analytics] → 전략 피드백 → content_calendar 업데이트 | 성과 리뷰 |
| `e2e_validation_flow` | draft 재활용 → quality_gate → publisher[비공개] → URL 확인 → 수동 삭제 | 셀렉터 변경/세션 만료 의심 시 |

`e2e_validation_flow` 체크리스트: `guide/operations/e2e_checklist.md`

### 전제조건 가드

Agent는 전제조건이 미충족되면 자동으로 선행 Agent를 체이닝한다.

| Agent | 전제조건 | 미충족 시 |
|-------|----------|-----------|
| `content_writer` | topic 필수 | 주제 요청 또는 trend_researcher 자동 호출 |
| `quality_gate` | `draft.md` 존재 | `content_writer[draft_only]` 자동 체이닝 |
| `publisher` | `quality_gate passed=true` | `quality_gate` 자동 체이닝 |
| `growth_manager[distribute]` | `publish_result.status="success"` | `publisher` 자동 체이닝 |

---

## 사용법

Claude Code에서 아래 문구로 대화하면 해당 Agent/Flow가 실행된다.

### 콘텐츠 생성

| 요청 예시 | 실행 |
|----------|------|
| `"[주제] 블로그 글 써줘"` | content_pipeline_flow (전체) |
| `"[주제] 바로 글 써줘"` | quick_post_flow (트렌드 스킵) |
| `"아웃라인만"` | content_writer[outline_only] |
| `"초안만"` | content_writer[draft_only] |
| `"SEO 최적화"` | content_writer[seo_only] |

### 리서치

| 요청 예시 | 실행 |
|----------|------|
| `"트렌드 분석"` / `"주제 찾아줘"` | trend_researcher[quick_scan] |
| `"키워드 분석"` | trend_researcher[keyword_analysis] |
| `"심층 리서치"` | trend_researcher[deep_research] |

### 발행 및 성과

| 요청 예시 | 실행 |
|----------|------|
| `"발행해줘"` / `"올려줘"` | publisher[publish] |
| `"테스트 발행"` | publisher[dry_run] |
| `"성과 분석"` / `"조회수"` | growth_manager[analytics] |
| `"SNS 공유"` | growth_manager[distribute] |
| `"전략 업데이트"` | growth_manager[strategy_update] |
| `"이번 주 전략"` | content_calendar 기반 직접 처리 |

> publisher는 항상 비공개로 발행한다. 검토 후 플랫폼에서 수동으로 공개 전환할 것.

---

## 운영 규칙

### 카테고리 및 글 구조

| 카테고리 | 글 구조 | 분량 | 트리거 예시 |
|----------|---------|------|-------------|
| `개발/AI` | 문제 정의 → 해결 (코드 포함) → 초보 함정 3가지 → 체크리스트 | 2000~3000자 | `"Claude Agent 비교 글 써줘"` |
| `맛집` | 한 줄 결론 → 맛/분위기/가성비 → 추천 조합 → 주의사항 | 1800~2500자 | `"강남 스시집 리뷰 써줘"` |
| `여행` | 추천 동선 → 현지 팁 → 비용 정리 → 반나절/하루 일정 | 2000~3000자 | `"제주도 당일치기 글 써줘"` |
| `기타` | 6섹션 고정 아웃라인 | — | — |

카테고리 정규화: `"AI"`, `"개발"`, `"개발/ai"` → `"개발/AI"`  
카테고리별 상세 구조: `Templates/dev_ai.md`, `Templates/food.md`, `Templates/travel.md`

### 이미지 워크플로우

```
# 본문 플레이스홀더 형식 (slug: a-z0-9_, 3~40자)
{{IMG:solution_diagram}}
solution_diagram 설명 캡션 (최대 80자)
```

1. **content_writer** — 본문에 `{{IMG:slug}}` 삽입, `image_plan.json` 생성 (path 빈 값)
2. **image_agent** — AI 생성으로 path 자동 채움 (활성화 시) / 또는 수동으로 경로 입력
3. **quality_gate** — `image_validator.py`로 플레이스홀더-플랜 일관성 검증
4. **publisher** — 텍스트 청크 분할 → 이미지 업로드 → 캡션 입력

이미지 제한: 포스트당 최대 6장, `.jpg/.png/.gif/.webp`, 최소 600px, 최대 10MB

맛집/여행 글은 `images/food/[photo_set]/`, `images/travel/[photo_set]/` 폴더에서 미사용 사진을 자동 선택한다. 발행 성공 후 `outputs/analytics/photo_usage.json`에 사용 이력을 기록해 재사용을 방지한다.

### Quality Gate 규칙

발행 전 5-rule 자동 검증. `hard_fail` 시 발행 차단, `soft_fail` 시 자동 수정 후 재검증.

| 규칙 | 기준 | 실패 유형 | 자동 수정 |
|------|------|----------|----------|
| 텍스트 길이 | ≥ 1800자 | soft_fail | 체크리스트 섹션 추가 |
| 이모지 수 | ≤ 2개 | hard_fail | 수동 수정 필요 |
| 광고 톤 | 금지어 없음 (`무조건`, `최고의`, `완벽한`, `혁신적` 등) | warning | — |
| 키워드 배치 | 첫 200자 내 primary keyword | soft_fail | 도입부 문장 삽입 |
| 이미지 일관성 | slug 일치, 파일 존재, ≤ 6장, alt text 5-120자 | hard_fail / soft_fail | 조건부 자동 수정 |

---

## 참조

### 스크립트 CLI

```powershell
# 설정 검증
python -m scripts.platforms.naver.publisher --check-config

# 카테고리 ID 추출
python -m scripts.platforms.naver.publisher --dump-categories

# 세션 저장
python -m scripts.platforms.naver.publisher --save-session

# Dry-run (브라우저 시뮬레이션, 실제 발행 없음)
python -m scripts.platforms.naver.publisher --mode dry_run `
  --draft outputs/drafts/posts/YYYYMMDD_[slug]/draft.md `
  --meta  outputs/drafts/posts/YYYYMMDD_[slug]/post_meta.json

# 실제 발행
python -m scripts.platforms.naver.publisher --mode publish `
  --draft      outputs/drafts/posts/YYYYMMDD_[slug]/draft.md `
  --meta       outputs/drafts/posts/YYYYMMDD_[slug]/post_meta.json `
  --image-plan outputs/drafts/posts/YYYYMMDD_[slug]/image_plan.json

# E2E 스모크 테스트
python -m scripts.workflows.e2e_smoke
python -m scripts.workflows.e2e_smoke --headless
```

### 산출물 경로

| 산출물 | 경로 |
|--------|------|
| 주제 후보 | `outputs/research/topics/topic_candidates_YYYYMMDD.md` |
| 글 작업 폴더 | `outputs/drafts/posts/YYYYMMDD_[slug]/` |
| 아웃라인 | `…/outline.md` |
| 초안 | `…/draft.md` |
| SEO 메타 | `…/post_meta.json` |
| 이미지 플랜 | `…/image_plan.json` |
| 검증 리포트 | `…/validation_report.json` |
| 발행 완료 아카이브 | `outputs/published/posts/post_YYYYMMDD_[slug].md` |
| 발행 결과 JSON | `outputs/published/runs/YYYYMMDD/results/publish_result_YYYYMMDD.json` |
| 배포 로그 | `outputs/published/distribution/distribution_log_YYYYMMDD.md` |
| 성과 리포트 | `outputs/analytics/reports/analytics_YYYYMMDD.md` |
| 전략 제안 | `outputs/analytics/strategy/strategy_proposal_YYYYMMDD.md` |
| Agent 작업 로그 | `Logs/<agent>/YYYYMMDD_HHMMSS_[task_slug].md` |

### 프로젝트 구조

```
blog-helper/
├── CLAUDE.md                    # 오케스트레이터 (판단 트리 + Agent 라우팅)
├── AGENTS.md                    # 외부 도구용 오케스트레이터 사본
│
├── inputs/
│   ├── blog_config.example.yaml # 설정 템플릿 (blog_config.yaml 은 gitignore)
│   └── content_calendar.md      # 주간/월간 콘텐츠 계획
│
├── Templates/                   # 카테고리별 글 구조 템플릿
├── rules/                       # 문체·이미지·발행·SEO 운영 규칙
│
├── scripts/
│   ├── core/                    # 공통 유틸 (설정, 변환, 로그, 세션)
│   ├── platforms/
│   │   ├── naver/               # 발행, 셀렉터
│   │   └── tistory/             # 발행, 스킨 패치, CSS 패치
│   ├── quality/                 # image_validator.py
│   ├── hooks/                   # check_agent_scope.py (PreToolUse)
│   ├── workflows/               # analytics_collector, calendar_updater, e2e_smoke
│   ├── schemas/                 # image_plan_schema.json
│   └── requirements.txt
│
├── guide/
│   ├── Guide.md                 # 코딩 가이드라인
│   ├── operations/              # setup, e2e_checklist, schema, error_guide
│   ├── design_agent/            # reference, patch_rules, tistory_skin_html_process
│   └── <agent>/pipeline.md      # 각 Agent 파이프라인 상세
│
├── outputs/
│   ├── drafts/                  # 글 작성 산출물 (gitignore)
│   ├── research/                # 주제 후보 (gitignore)
│   ├── published/               # 발행 산출물 (gitignore)
│   ├── analytics/               # 성과 분석 (gitignore)
│   └── design/
│       ├── css/                 # 적용된 CSS 스냅샷 (추적)
│       ├── html/                # 적용된 skin.html 스냅샷 (추적)
│       └── prototypes/          # 프로토타입 설계 파일 (추적)
│
├── images/                      # 로컬 사진 라이브러리 (맛집/여행)
└── Logs/                        # Agent 작업 로그 (날짜 prefix 파일은 gitignore)
```

> `agent_prompts/`, `.claude/agents/`, `.claude/skills/` — 시스템 IP, gitignore  
> `inputs/blog_config.yaml` — 개인 정보 포함, gitignore
