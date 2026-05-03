# Quality Gate — Pipeline 상세

## 검증 규칙 상세

### 규칙 1: 본문 길이

- 기준: `constraints.min_chars` (기본 1800자)
- 미달 시 `issue` (soft fail)
- 자동 수정: 운영 체크리스트 섹션 추가

### 규칙 2: 이모지 수

- 기준: `constraints.emoji_max` (기본 2개)
- 초과 시 `hard_fail`, 자동 수정 없음
- 이모지 카운트: 유니코드 이모지 범위 정규식 기반

### 규칙 3: 광고/과장 톤

탐지 패턴: `무조건`, `최고의`, `완벽한`, `혁신적`, `지금 바로`, `혜택`, `무료.*제공`, `광고`, `협찬`

- 발견 시 `issue` (경고), 자동 수정 없음

### 규칙 4: 핵심 키워드 상단 배치

- 기준: primary keyword가 본문 첫 200자 이내 등장
- 미등장 시 `issue` (soft fail)
- 자동 수정: 키워드 포함 문장을 본문 상단에 삽입

### 규칙 5: 이미지 Placeholder 정합성

전체 규칙 상세: `rules/image_rules.md` §5

| 하위 규칙 | 기준 | 판정 | 자동 수정 |
|-----------|------|------|-----------|
| 5-1 | 본문 slug 집합 ⊆ image_plan slug 집합 | `hard_fail` | 없음 |
| 5-2 | image_plan 모든 entry의 `path` 파일 존재 확인 | `hard_fail` | 없음 |
| 5-3 | 한 글 placeholder 개수 ≤ 6 | `soft_fail` | 없음 (경고) |
| 5-4 | alt 텍스트 길이 5~120자 | `soft_fail` | caption 재사용으로 자동 보강 |
| 5-5 | image_plan에 있지만 본문에 미사용된 slug | `soft_fail` | 경고만 |

**전제조건**: image_plan 사이드카 없으면 규칙 5-1~5 전체 skip (본문에 `{{IMG:` 가 1개 이상 있으면 hard_fail).

image_plan 경로 탐색: `meta_path`와 동일한 날짜+slug의 `image_plan_*.json` 파일.

## ValidationReport 출력 형식

```json
{
  "passed": true,
  "issues": ["본문 길이 부족 (1500/1800)"],
  "fixes_applied": ["운영 체크리스트 섹션 추가 (+350자)"],
  "stats": {
    "chars_before": 1500,
    "chars_after": 1850,
    "emojis_before": 1,
    "emojis_after": 1,
    "min_chars": 1800,
    "emoji_max": 2,
    "hard_fail": [],
    "image_placeholders": 2,
    "image_plan_slugs": 2,
    "missing_image_paths": []
  }
}
```

- `passed=True`: hard fail 없으면 통과 (soft fail은 자동 수정 후 통과)
- `passed=False`: hard fail 존재 → 발행 차단

## 이미지 배치 로직

| photos 상태 | mode | 배치 |
|-------------|------|------|
| 사진 1장 | `use_uploads` | 첫 문단 뒤 1장 |
| 사진 2장+ | `use_uploads` | 첫 문단 뒤 1장, 3번째 섹션 뒤 1장 |
| 사진 없음 | `none` | "이미지 없이도 이해되도록" 안내 |

```json
{
  "mode": "use_uploads",
  "placements": [
    {"photo": "photo1.jpg", "position": "after_section_1"},
    {"photo": "photo2.jpg", "position": "after_section_3"}
  ],
  "note": "이미지가 본문 흐름을 보조하도록 배치"
}
```
