# 에러 핸들링

## 검증 실패 (quality_gate passed=False)

- `hard_fail` (이모지 초과) → 사용자에게 수동 수정 안내
- `soft_fail` (길이 부족/키워드 누락) → 자동 수정 후 재검증 (최대 2회)

## 발행 실패 (publisher status="fail")

- 브라우저 미설치 → Playwright 설치 안내
- 로그인 실패 → 수동 로그인 안내
- 기타 → draft 보존 + 수동 발행 URL 안내

## 트렌드 수집 실패

- 기본 주제 목록(content_calendar)에서 fallback 선택
