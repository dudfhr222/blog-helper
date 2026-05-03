# 이미지 규약 (Image Rules)

> 이 파일이 이미지 placeholder·사이드카·업로드 흐름의 **단일 진실원**이다.
> content_writer, quality_gate, publisher 모두 이 규약을 따른다.

---

## 1. Placeholder 토큰 형식

```
{{IMG:slug}}
```

- **slug 규약**: `^[a-z0-9_]{3,40}$` (소문자·숫자·언더스코어, 3~40자)
- **위치**: 독립 라인에 단독 작성 (앞뒤 줄 빈 행)
- **캡션 필수**: placeholder 바로 다음 줄에 캡션 1행 (≤80자). SmartEditor에서 이미지 캡션으로 입력됨
- **한 글 최대 6개**: 네이버 모바일 가독성 기준
- **파싱 정규식**: `\{\{IMG:([a-z0-9_]{3,40})\}\}`

### 올바른 예시

```markdown
본문 내용 마지막 문장.

{{IMG:agent_workflow_overview}}
Claude Code Agent의 전체 워크플로우 개요 다이어그램

다음 섹션 내용...
```

### 잘못된 예시

```
{{IMG:}}                        ← slug 없음
{{IMG:내 사진}}                 ← 한글 slug 금지
{{img:screenshot}}              ← 대문자 IMG 아님
{{IMG:x}}                       ← 2자 이하
[IMG:screenshot]                ← 대괄호 형식 금지
<!-- IMG:screenshot -->         ← 코멘트 형식 금지
```

---

## 2. 사이드카 파일: image_plan_YYYYMMDD_[slug].json

content_writer가 draft를 생성할 때 **동시에** 생성한다.
publisher가 이 파일을 읽어 업로드 큐를 구성한다.

### 스키마

```json
{
  "draft_slug": "topic_slug",
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "images": [
    {
      "slug": "agent_workflow_overview",
      "alt": "Claude Code Agent 워크플로우 전체 구조도",
      "caption": "Claude Code Agent의 전체 워크플로우 개요 다이어그램",
      "path": "",
      "kind": "screenshot",
      "section_hint": "2번 섹션 뒤"
    }
  ]
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `slug` | string | 필수 | 본문 placeholder의 slug와 1:1 매핑 |
| `alt` | string | 필수 | 이미지 대체 텍스트 (5~120자) |
| `caption` | string | 필수 | 이미지 캡션 (≤80자) |
| `path` | string | **사용자 채움** | 실제 이미지 파일 절대 경로. content_writer는 빈 문자열로 생성, 사용자가 채운 뒤 quality_gate 재실행 |
| `kind` | string | 권장 | `screenshot` / `diagram` / `photo` / `chart` / `other` |
| `section_hint` | string | 선택 | 어느 섹션 뒤에 삽입하는지 힌트 |

### path 채우기 워크플로우

```
content_writer → image_plan 생성 (path="")
      ↓
사용자: PNG/JPG 파일 준비 (스크린샷, 직접 만든 차트, 사진 등)
      ↓
맛집/여행: images/food/[photo_set]/ 또는 images/travel/[photo_set]/에서 미사용 사진 자동 선택 가능
      ↓
사용자: image_plan.json의 path 필드에 파일 절대 경로 입력
      ↓
quality_gate[validate_and_fix] → 5번째 규칙으로 path 검증
      ↓
publisher → image_plan 읽어서 업로드 큐 구성
```

---

## 3. 카테고리별 권장 이미지 개수 및 위치

| 카테고리 | 권장 개수 | 권장 위치 |
|----------|-----------|-----------|
| 개발/AI | 2~3개 | 섹션 2 뒤(코드 흐름 다이어그램), 섹션 3 뒤(에러 스크린샷), 마지막 섹션 앞(결과 스크린샷) |
| 맛집 | 3~4개 | 섹션 1 뒤(대표 음식), 섹션 2 뒤(분위기), 섹션 3 뒤(추천 메뉴), 마지막(외관) |
| 여행 | 4~5개 | 섹션 1 뒤(대표 장소), 동선별 주요 스팟마다, 마지막(전망/분위기) |

### 맛집/여행 사진 라이브러리

- 세부 주제 폴더: `images/food/[photo_set]/`, `images/travel/[photo_set]/`
- 우선순위: `photos` 직접 지정 → `photo_set` 폴더 → topic/keywords 자동 매칭 → 사진 없음
- 사진 재사용 금지: 발행 성공 후 `outputs/analytics/photo_usage.json`에 사용 이력을 기록하고 다음 선택에서 제외
- 사진 부족 시: 있는 만큼만 사용하고 발행은 차단하지 않음

---

## 4. 이미지 파일 요건 (publisher 업로드 기준)

| 항목 | 기준 |
|------|------|
| 허용 확장자 | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` |
| 권장 해상도 | 가로 600px 이상 (네이버 모바일 기준) |
| 최대 파일 크기 | 10MB (네이버 블로그 제한) |
| 파일 존재 여부 | quality_gate가 절대 경로로 확인 |

---

## 5. quality_gate 검증 규칙 요약 (5번째 규칙)

| 규칙 | 판정 | 자동 수정 |
|------|------|-----------|
| 5-1. 본문 slug ⊆ image_plan slug | hard_fail | 없음 |
| 5-2. image_plan의 path 파일 존재 | hard_fail | 없음 |
| 5-3. placeholder 개수 ≤ 6 | soft_fail | 없음 (경고만) |
| 5-4. alt 길이 5~120자 | soft_fail | caption으로 자동 보강 |
| 5-5. image_plan slug가 본문에 미사용 | soft_fail | 경고만 |

---

## 6. publisher 업로드 흐름 요약

```
본문을 {{IMG:slug}} 기준으로 chunk 분할
for each chunk:
    paste(chunk.text)           ← 클립보드 paste (한글 IME 이슈 회피)
    if chunk.has_image:
        upload(image_plan[slug].path)   ← set_input_files()
        type(image_plan[slug].caption)  ← 캡션 입력
업로드 실패 시 → 즉시 abort, 발행 차단 (부분 발행 금지)
```
