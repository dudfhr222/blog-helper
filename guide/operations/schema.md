# 데이터 스키마

## BlogRequest

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `topic` | str | (필수) | 글 주제 |
| `category` | str | `"개발/AI"` | 카테고리 |
| `tone` | str | `"담백한"` | 글 어조 |
| `target_audience` | str | `"일반 독자"` | 타겟 독자 |
| `purpose` | str | `"검색 유입 + 체류시간 + 개인 브랜딩"` | 글 목적 |
| `keywords` | List[str] | `[]` | 키워드 리스트 |
| `constraints` | Constraints | 기본값 | 품질 제약조건 |
| `photos` | List[str] | `[]` | 사진 경로 |

## Constraints

| 필드 | 기본값 | 설명 |
|------|--------|------|
| `min_chars` | 1800 | 본문 최소 글자 수 |
| `emoji_max` | 2 | 이모지 최대 허용 수 |
| `no_ad_tone` | True | 광고/과장 톤 금지 |

## PostMeta

| 필드 | 설명 |
|------|------|
| `title` | 최종 게시글 제목 |
| `tags` | 태그 리스트 (최대 10) |
| `summary` | 요약 (검색/미리보기용) |
| `category` | 카테고리 |
