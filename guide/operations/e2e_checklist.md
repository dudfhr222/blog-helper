# e2e 스모크 테스트 사전 준비 체크리스트

`python -m scripts.workflows.e2e_smoke` 실행 전에 아래 항목을 모두 확인한다.

## 필수 사전 준비

- [ ] `guide/operations/operations_setup.md` §1~§4 완료 (Python, Playwright, blog_config 설정)
- [ ] `python -m scripts.platforms.naver.publisher --check-config` 실행 결과 "완료" 확인
- [ ] `python -m scripts.platforms.naver.publisher --save-session` 실행 완료 (세션 파일 존재)
- [ ] `outputs/drafts/posts/20260316_ai-agent-workflow/draft.md` 파일 존재 확인
- [ ] 네이버 블로그 카테고리 ID 매핑이 `inputs/blog_config.yaml`의 `categories[*].category_id`에 입력되어 있음
- [ ] 발행 후 삭제할 여유 — 테스트 게시글이 비공개로 발행됨

## 실행

```powershell
python -m scripts.workflows.e2e_smoke
# 또는 헤드리스 모드로
python -m scripts.workflows.e2e_smoke --headless
```

## 합격 기준

- [ ] `outputs/published/runs/YYYYMMDD/results/publish_result_YYYYMMDD.json` 생성, `status="success"`
- [ ] 발행된 비공개 URL에 브라우저로 접근 가능 (HTTP 200)
- [ ] `Logs/publisher/`에 새 작업 로그 `.md` 생성됨
- [ ] `Logs/naver_blog_auto_posting_log.md`에 호환용 1행 항목 추가됨

## 테스트 후 정리

1. 발행된 URL을 브라우저에서 열어 본문·이미지 확인
2. 네이버 블로그 → 해당 글 선택 → **삭제** (또는 임시저장으로 전환)
3. `outputs/drafts/tmp/smoke_tmp/` 디렉터리 삭제 (임시 파일)

## 실패 시 디버그

실패 시 `outputs/published/runs/YYYYMMDD/debug/` 에 스크린샷과 DOM 덤프가 저장된다.

흔한 실패 원인:
- **셀렉터 미스매치**: 네이버 UI 업데이트. `scripts/platforms/naver/selectors.py` 수정 후 재실행.
- **로그인 만료**: `--save-session` 재실행.
- **카테고리 ID 오류**: `--dump-categories`로 ID 재확인.
- **이미지 업로드 타임아웃**: 네트워크 속도 문제. 재시도.
