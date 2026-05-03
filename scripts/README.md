# scripts/ — 자동화 보조 스크립트

## 설치

```powershell
cd c:\PJT\blog_posting
pip install -r scripts/requirements.txt
pip install pyperclip          # 클립보드 paste용 (Windows)
playwright install chromium
```

## 주요 스크립트

| 파일 | 역할 |
|------|------|
| `platforms/naver/publisher.py` | 네이버 블로그 Playwright 자동 발행 |
| `platforms/naver/selectors.py` | SmartEditor One 셀렉터 상수 |
| `platforms/tistory/publisher.py` | 티스토리 Playwright 자동 발행 |
| `platforms/tistory/css_patcher.py` | 티스토리 스킨 CSS 백업/패치 |
| `platforms/tistory/skin_patcher.py` | 티스토리 `skin.html`/CSS 백업, 구조 분석, dry-run, 패치 |
| `core/md_to_naver.py` | 마크다운 → 에디터 입력 chunk 변환 |
| `core/session_store.py` | Playwright storage_state 저장·로드 |
| `quality/image_validator.py` | quality_gate 5번째 규칙 검사기 |
| `workflows/analytics_collector.py` | 블로그 통계 수집 |
| `workflows/calendar_updater.py` | content_calendar.md 마커 영역 자동 갱신 |
| `workflows/e2e_smoke.py` | end-to-end 비공개 발행 1회 스모크 테스트 |

## 사용법 요약

```powershell
# 세션 저장 (최초 1회)
python -m scripts.platforms.naver.publisher --save-session

# 설정 완료 여부 확인
python -m scripts.platforms.naver.publisher --check-config

# dry_run (제목 입력까지, 발행 안 함)
python -m scripts.platforms.naver.publisher --mode dry_run --draft ... --meta ...

# 실제 발행 (비공개 강제)
python -m scripts.platforms.naver.publisher --mode publish --draft ... --meta ... --image-plan ...

# e2e 스모크 테스트
python -m scripts.workflows.e2e_smoke

# 티스토리 스킨 HTML/CSS 백업
python -m scripts.platforms.tistory.skin_patcher --backup --target all

# 백업된 skin.html 구조 분석
python -m scripts.platforms.tistory.skin_patcher --inspect --html outputs/design/backups/skin_html_YYYYMMDD_HHMMSS.html

# 티스토리 스킨 HTML/CSS dry-run
python -m scripts.platforms.tistory.skin_patcher --patch --html outputs/design/html/skin_custom_YYYYMMDD_HHMMSS.html --css outputs/design/css/custom_YYYYMMDD_HHMMSS.css --dry-run
```

## 첫 설정 순서

`guide/operations/operations_setup.md` 참조.
