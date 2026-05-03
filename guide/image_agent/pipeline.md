# Image Agent 파이프라인 가이드

## 역할 요약

`image_plan.json`의 `path=""` 항목을 읽어 외부 이미지 생성 API를 호출하고, 생성된 파일 경로를 image_plan에 채워 quality_gate가 통과할 수 있게 한다.

파이프라인 위치: `content_writer` → **`image_agent`** → `quality_gate`

---

## 실행 흐름

```text
1. image_plan_path 파일 존재 확인
   └─ 없으면 즉시 중단 → content_writer 실행 안내

2. blog_config.yaml image_generation 섹션 확인
   ├─ enabled=false  → 경고 출력 후 종료 (path="" 유지)
   └─ API 키 환경변수 미설정 → 경고 출력 후 종료 (path="" 유지)

3. path="" 항목 필터링
   └─ 없으면 "이미 완료" 후 종료

4. [dry_run] → 생성 예정 목록 출력, API 호출 없음

5. [generate / regenerate]
   a. outputs/drafts/posts/YYYYMMDD_[topic_slug]/images/ 디렉토리 생성
   b. 각 항목 → 프롬프트 조립 → image_generator.py 호출
   c. 이미지 저장: outputs/drafts/posts/YYYYMMDD_[topic_slug]/images/[slug].png
   d. image_plan.json path 필드 업데이트 (절대 경로)

6. 결과 리포트 출력
   └─ 성공/실패 개수, 경로 목록

7. 작업 로그 생성: Logs/image_agent/YYYYMMDD_HHMMSS_[topic_slug].md
```

---

## blog_config.yaml 설정

```yaml
image_generation:
  enabled: false            # true로 변경해야 실행됨
  provider: "dalle3"        # dalle3 | replicate_sd
  dalle3:
    api_key_env: "OPENAI_API_KEY"   # 환경변수명 (값 아님)
    size: "1024x1024"               # 1024x1024 | 1792x1024 | 1024x1792
    quality: "standard"             # standard | hd  (hd는 2배 비용)
    style: "natural"                # natural | vivid
  replicate_sd:
    api_key_env: "REPLICATE_API_TOKEN"
    model: "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a"
  prompt:
    prefix: "Clean, minimal, professional illustration for Korean tech blog."
    suffix: "Flat design, no text overlay, white or light background."
```

### 활성화 방법

1. 원하는 provider의 API 키를 환경변수에 등록
   ```
   # Windows PowerShell
   $env:OPENAI_API_KEY = "sk-..."
   ```
2. `blog_config.yaml`의 `image_generation.enabled`를 `true`로 변경
3. `image_agent[generate]` 호출

---

## image_generator.py 직접 실행

```bash
# 전체 생성 (path="" 항목 모두)
python -m scripts.core.image_generator \
  --image-plan outputs/drafts/posts/20260502_my-topic/image_plan.json

# 단일 slug 재생성
python -m scripts.core.image_generator \
  --image-plan outputs/drafts/posts/20260502_my-topic/image_plan.json \
  --slug my-slug-1

# dry-run (API 호출 없이 프롬프트 확인)
python -m scripts.core.image_generator \
  --image-plan outputs/drafts/posts/20260502_my-topic/image_plan.json \
  --dry-run
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 성공 (전체 또는 일부 성공) |
| 1 | image_plan 파일 없음 |
| 2 | API 키 미설정 또는 enabled=false |
| 3 | 전체 이미지 생성 실패 |

---

## 프롬프트 조립 규칙

이미지 생성 API에 전달하는 프롬프트는 아래 필드를 결합한다:

```
[prompt.prefix]
Subject: [alt] — [caption]
Context: [section_hint]
Style hint: [kind별 스타일]
[prompt.suffix]
```

### kind별 스타일 힌트

| kind | 스타일 |
|------|--------|
| `diagram` | clean flowchart, minimal nodes, flat design, no decorative elements |
| `screenshot` | professional UI mockup, clean interface, realistic layout |
| `photo` | professional photography, bright natural lighting, sharp focus |
| `infographic` | data visualization, flat icons, clear hierarchy, pastel palette |
| (기타) | clean minimal illustration, professional |

---

## 출력 구조

```
outputs/drafts/posts/
└── [topic_slug]/
    ├── [img_slug_1].png
    ├── [img_slug_2].png
    └── ...
```

image_plan.json의 `path` 필드는 절대 경로로 채워진다:
```json
{
  "slug": "agent-workflow-1",
  "path": "C:/PJT/blog_posting/outputs/drafts/posts/20260502_my-topic/images/agent-workflow-1.png"
}
```

---

## 에러 코드 대응

| 상황 | 대응 |
|------|------|
| `enabled=false` | blog_config.yaml의 `image_generation.enabled`를 `true`로 변경 |
| API 키 미설정 | 해당 환경변수 등록 후 재실행 |
| `openai` 패키지 없음 | `pip install openai` |
| `replicate` 패키지 없음 | `pip install replicate` |
| API quota 초과 | 잠시 후 재시도 또는 `regenerate` 모드로 실패 slug만 재생성 |
| 개별 실패 | 로그에서 실패 slug 확인 → `image_agent[regenerate, slug=...]` 호출 |
