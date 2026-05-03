# Publisher — Pipeline 상세

## 브라우저 발행 단계 (9단계)

```
Step 1: open_editor     → blog.naver.com 에디터 열기 (세션 재사용)
Step 2: check_login     → 로그인 상태 확인 (미로그인 시 대기 후 session_store 갱신)
Step 3: fill_title      → PostMeta.title 입력
Step 4: fill_body       → 마크다운 → SmartEditor 입력 (이미지 포함)
  Step 4a: 본문을 {{IMG:slug}} 기준으로 chunk 분할
  Step 4b: 각 chunk: paste(text) → 이미지 있으면 upload → caption 입력
  Step 4c: 업로드 실패 시 즉시 abort (부분 발행 금지)
Step 5: set_category    → PostMeta.category → blog_config.category_id_map으로 변환
Step 6: set_tags        → PostMeta.tags 입력
Step 7: set_visibility  → 항상 "비공개" 선택 (강제)
Step 8: publish         → 발행 버튼 클릭
Step 9: capture_url     → 발행된 URL 캡처 + 저장 + 로그 기록
```

## 이미지 업로드 상세 (Step 4b)

- 업로드 방식: `page.set_input_files()` — 드래그앤드롭 회피
- image_plan의 slug 순서대로 처리
- 각 이미지 업로드 후 네이버 처리 완료 표식 대기 (timeout: 30초)
- 캡션: SmartEditor 캡션 입력란에 직접 입력

## 마크다운 → SmartEditor 변환 전략

- **클립보드 paste 우선**: 한글 IME 이슈 회피
- 헤딩(#, ##, ###): SmartEditor 단축키 매핑으로 변환 후 paste
- 코드블록: SmartEditor 코드블록 삽입 버튼 클릭 → 내용 paste
- 볼드/이탤릭: paste 후 선택 → 단축키 (Ctrl+B, Ctrl+I)
- placeholder `{{IMG:slug}}`: 해당 위치에서 paste 일시 중단 → 이미지 업로드

## 네이버 SmartEditor One iframe 처리

```python
# 2단 frame_locator 체이닝 예시
main_frame = page.frame_locator('iframe[name="mainFrame"]')
editor_frame = main_frame.frame_locator('iframe.se2_inputarea')
# SmartEditor One 버전에 따라 다를 수 있음 → selectors.py 참조
```

셀렉터 변경 시: `scripts/platforms/naver/selectors.py`의 상수만 수정.

## cover_image 처리

- `cover_image` 가 null이면 image_plan의 첫 번째 entry 사용
- 네이버 블로그 대표 이미지는 첫 업로드 이미지가 자동 설정됨 — 별도 조작 불필요

## 출력 형식

### browser_steps

```json
{
  "steps": [
    {"step": 1, "action": "open_editor"},
    {"step": 2, "action": "check_login"},
    {"step": 3, "action": "fill_title"},
    {"step": 4, "action": "fill_body_with_images"},
    {"step": 5, "action": "set_category"},
    {"step": 6, "action": "set_tags"},
    {"step": 7, "action": "set_private_forced"},
    {"step": 8, "action": "publish"},
    {"step": 9, "action": "capture_url"}
  ],
  "total_steps": 9,
  "note": "항상 비공개 발행 강제. 발행 후 수동 공개 전환 필요."
}
```

### PublishResult

```json
{
  "status": "success",
  "publish_url": "https://blog.naver.com/...",
  "error": null,
  "published_at": "2026-03-09T13:00:00"
}
```

| status | 설명 |
|--------|------|
| `planned` | plan 모드 — 실행 안 함 |
| `success` | 발행 성공 |
| `fail` | 발행 실패 |
| `skipped` | 전제조건 미충족으로 스킵 |
