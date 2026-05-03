# CLAUDE.md — Blog AI Team Orchestrator

## Mandatory First Step

**코딩/구현 작업 시에만** `guide/Guide.md` 읽기. 콘텐츠 생성·분석·라우팅은 스킵.
핵심 원칙: (1) 가정 말고 확인, (2) 최소 코드, (3) 요청 범위만 수정.

---

## 기본 규칙

**Language**: 모든 사용자 대면 산출물은 한국어. 기술 용어는 영어 유지.

| 원칙 | 구현 |
|------|------|
| Agent 조직 구조 | 7개 전문 agent + 오케스트레이터 |
| 성과 기반 피드백 루프 | growth_manager → 판단 트리 업데이트 |
| 실패 전제 설계 | quality_gate 통과 전 발행 차단 |
| 산출물 계약 고정 | outputs/ 하위 고정 구조 |
| 작업 로그 | agent별 `Logs/<agent>/YYYYMMDD_HHMMSS_[task_slug].md` 생성 |

## 작업 로그 규칙

각 agent는 작업 종료 시 Markdown 로그를 1개 남긴다.

- 경로: `Logs/<agent>/YYYYMMDD_HHMMSS_[task_slug].md`
- 필수 항목: 요청 요약, 입력 파일/참조, 수행 내용, 생성/수정 산출물, 후속 조치
- 실제 subagent 프로세스를 실행하지 않고 역할 명세만 참고해 직접 처리한 경우도 해당 agent 로그를 남긴다.
- 기존 `Logs/naver_blog_auto_posting_log.md`는 publisher 호환용 1줄 운영 로그로만 사용한다.

---

## 에이전트 위임 강제 규칙

오케스트레이터는 아래 작업을 **직접 수행하지 않는다**. 반드시 `Agent` 도구로 해당 에이전트를 spawn해야 한다.

| 작업 유형 | 담당 에이전트 | 직접 수행 금지 경로 |
|-----------|-------------|---------------------|
| 블로그 글 작성/SEO | content_writer | outputs/drafts/posts/ |
| 트렌드/키워드 분석 | trend_researcher | outputs/research/topics/ |
| 이미지 생성 | image_agent | outputs/drafts/posts/*/images/ |
| 품질 검증/수정 | quality_gate | outputs/drafts/posts/*/validation_report.json |
| 발행 | publisher | outputs/published/ |
| 성과 분석/배포 | growth_manager | outputs/analytics/ |
| 디자인/HTML/CSS | design_agent | outputs/design/html/, outputs/design/css/ |

**예외:** 단순 질문 응답, 파일 Read, 컨텍스트 파악은 오케스트레이터가 직접 수행할 수 있다.

> 위반 시 `scripts/hooks/check_agent_scope.py` (PreToolUse hook) 가 Edit/Write를 자동 차단한다.

---

## 디자인 에이전트 라우팅

**절대 규칙:** 오케스트레이터는 `outputs/design/html/`, `outputs/design/css/` 를 직접 Edit/Write하지 않는다. 반드시 `Agent` 도구로 design_agent를 spawn해야 한다.

**트리거:** 블로그 디자인, 스킨, HTML, CSS, 테마, 레이아웃, 폰트, 색상, 티스토리 꾸미기 요청 시 `.claude/agents/design_agent.md`를 호출한다.

**호출 전 필수 참고:**
- `guide/design_agent/reference.md`
- `guide/design_agent/prototype_notes_usage.md`
- `outputs/design/prototypes/prototype_notes.md`
- HTML 구조 변경 시 `guide/design_agent/tistory_skin_html_process.md`

디자인 에이전트 호출 시에는 사용자 요구사항과 함께 다음 컨텍스트를 전달한다.

```text
request: [사용자 디자인 요청]
mode: css-only | skin-html-css
reference_guide: guide/design_agent/reference.md
skin_process: guide/design_agent/tistory_skin_html_process.md
prototype_notes_usage: guide/design_agent/prototype_notes_usage.md
prototype_notes: outputs/design/prototypes/prototype_notes.md
backup_html: outputs/design/backups/skin_html_*.html 중 최신 파일
backup_css: outputs/design/backups/skin_css_*.css 또는 backup_*.css 중 최신 파일
structure_report: outputs/design/state/skin_structure_*.json 중 최신 파일
```

레이아웃 구조 변경은 CSS만으로 처리하지 않는다. 먼저 티스토리 `skin.html`을 백업하고 `.header`, `.area-main`, `.area-aside`, `.article-type-common` 위치를 확인한 뒤 hero, post-card, profile-card 구조를 티스토리 치환자에 맞게 이식한다.

실제 티스토리 적용은 `scripts.platforms.tistory.skin_patcher`로 HTML/CSS 백업과 dry-run을 끝낸 뒤 진행한다.

**HTML 패치 시 사이드바 컴포넌트 6종 생존 검증 필수 (누락 시 패치 중단):** 검색창(`searchInput`), 최근글(`s_rctps_rep`), 인기글(`s_rctps_popular_rep`), 카테고리(`[##_category_list_##]`), 태그(`s_random_tags`), 페이징(`s_paging`). `agent_prompts/design_agent.md` HTML 패치 규칙 참고.

---

## 하네스: 블로그 자동화

**목표:** 트렌드 리서치부터 발행·성과 분석까지 블로그 운영 전 과정을 7개 전문 에이전트가 자동화한다.

**트리거:** 블로그 관련 작업 요청 시 `blog-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력 (최근 3건):**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-03 | design_agent prototype 구조 맵 연결 | CLAUDE.md, agent_prompts/design_agent.md, guide/design_agent/prototype_notes_usage.md, guide/design_agent/tistory_skin_html_process.md | 스타일 수정·분석 시 `outputs/design/prototypes/prototype_notes.md`를 먼저 읽고 최신 백업과 대조하도록 절차 고정 |
| 2026-05-03 | 하네스 드리프트 수정 (image_agent 동기화) | CLAUDE.md, .claude/skills/blog-orchestrator/SKILL.md | image_agent가 에이전트 팀 목록에 누락됨 + 에이전트 수 카운트 5→7, 6→7 갱신 |
| 2026-05-03 | 참조 섹션 업데이트 | CLAUDE.md | operations_setup.md, e2e_checklist.md, patch_rules.md 신규 가이드 파일 추가 |

---

상세 참조: 스키마 `guide/operations/schema.md` | 에러 처리 `guide/operations/error_guide.md` | 운영 설정 `guide/operations/operations_setup.md` | E2E `guide/operations/e2e_checklist.md` | 디자인 `guide/design_agent/reference.md` | 패치 규칙 `guide/design_agent/patch_rules.md`
