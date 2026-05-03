# Agent 작업 로그 규칙

각 agent는 작업을 마칠 때마다 자기 폴더에 Markdown 로그를 1개 남긴다.

## 폴더

| Agent | 로그 경로 |
|---|---|
| trend_researcher | `Logs/trend_researcher/` |
| content_writer | `Logs/content_writer/` |
| quality_gate | `Logs/quality_gate/` |
| publisher | `Logs/publisher/` |
| growth_manager | `Logs/growth_manager/` |
| design_agent | `Logs/design_agent/` |

## 파일명

`YYYYMMDD_HHMMSS_[task_slug].md`

예: `20260502_143012_ai-agent-workflow.md`

## 템플릿

```markdown
---
created: YYYY-MM-DD HH:MM:SS
agent: agent_name
mode: mode_name
task: task_slug
status: success | fail | skipped
---

# agent_name 작업 로그

## 요청
- 요약:
- 입력:

## 수행
- 핵심 판단:
- 처리 단계:

## 산출물
- `outputs/...`

## 후속 조치
- 없음
```

기존 `Logs/naver_blog_auto_posting_log.md`는 publisher 호환용 1줄 운영 로그로만 유지한다.
