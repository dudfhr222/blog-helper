# 운영 환경 설정 가이드 (Operations Setup)

처음 이 시스템을 사용하기 전에 아래 순서대로 설정한다.

---

## §1. Python 환경 및 Playwright 설치

```powershell
# 1. 프로젝트 디렉터리에서
cd c:\PJT\blog_posting

# 2. 가상환경 생성 (선택, 권장)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r scripts/requirements.txt

# 4. Playwright 브라우저 설치
playwright install chromium
```

---

## §2. 네이버 카테고리 ID 확인 방법

네이버 블로그에서 직접 카테고리 ID를 추출한다.

1. Chrome/Edge 브라우저에서 `https://blog.naver.com/[blog_id]` 접속 (로그인 상태)
2. **내 블로그 관리** → **카테고리 관리** 이동
3. 개발자 도구 열기 (`F12`)
4. **Elements** 탭에서 카테고리 목록의 HTML을 확인하거나,
5. 또는 글쓰기 에디터에서 카테고리 드롭다운을 열고 Elements에서 `option value="숫자"` 확인

### 또는 dump_categories 스크립트 사용 (세션 설정 후)

```powershell
python -m scripts.platforms.naver.publisher --dump-categories
```

확인한 ID를 `inputs/blog_config.yaml`의 `categories[*].category_id`에 채워 넣는다.

---

## §3. 세션 저장 (로그인 1회 수행)

Playwright 헤드풀 모드로 브라우저를 열고 수동 로그인한 뒤 세션을 저장한다.

```powershell
python -m scripts.platforms.naver.publisher --save-session
```

1. 브라우저 창이 열리면 `https://nid.naver.com/nidlogin.login` 으로 이동
2. 네이버 ID/PW로 로그인 (2단계 인증 포함)
3. 로그인 완료 후 터미널에 "세션 저장 완료: ~/.blog_posting/naver_session.json" 메시지 확인
4. 이후 `--reuse-session` 플래그로 헤드리스 실행 가능

> 세션은 보통 30일~90일 유효. 만료 시 이 절차를 반복한다.
> `~/.blog_posting/naver_session.json`에는 쿠키가 포함되므로 **git에 커밋하지 않는다.**

---

## §4. blog_config.yaml 필수 값 채우기

`inputs/blog_config.yaml`에서 빈 문자열(`""`)과 `0`으로 표시된 항목을 채운다.

| 항목 | 어디서 찾나 | 예시 |
|------|-------------|------|
| `blog_id` | 네이버 블로그 URL에서 | `mydevblog` |
| `blog_url` | `https://blog.naver.com/[blog_id]` | `https://blog.naver.com/mydevblog` |
| `blog_owner_email` | 로그인에 쓰는 네이버 ID 또는 이메일 | `myid@naver.com` |
| 카테고리 ID | §2에서 확인 | `1234567` |
| KPI 목표 | 목표치 직접 입력 | 일 조회수 50 |

설정 완료 후 검증:

```powershell
python -m scripts.platforms.naver.publisher --check-config
```

"모든 필수 설정 완료" 메시지가 나오면 준비 완료.

---

## §5. dry_run으로 발행 흐름 확인

실제 발행 없이 로그인 → 에디터 진입 → 제목 입력까지 테스트한다.

```powershell
python -m scripts.platforms.naver.publisher \
  --mode dry_run \
  --draft outputs/drafts/posts/20260316_ai-agent-workflow/draft.md \
  --meta outputs/drafts/posts/20260316_ai-agent-workflow/post_meta.json
```

- 브라우저 창이 열리고 에디터에 제목이 입력된 상태에서 멈춤
- 스크린샷이 `outputs/published/runs/YYYYMMDD/screenshots/dry_run_YYYYMMDD_HHMMSS.png`에 저장됨
- 터미널에 `dry_run: PASS` 메시지 확인

---

## §6. e2e_smoke로 비공개 발행 1회 테스트

```powershell
python -m scripts.workflows.e2e_smoke
```

내부적으로 기존 draft(`2026-03-16 ai-agent-workflow`)에 IMG placeholder 2개를 임시 주입하고 비공개 발행까지 실행한다.

1. 발행 성공 시 `outputs/published/runs/YYYYMMDD/results/publish_result_YYYYMMDD.json`에 URL 기록
2. 해당 URL을 브라우저에서 열어 이미지 2개 + 본문 정상 확인
3. 확인 후 네이버 블로그에서 해당 글 **삭제** (테스트 게시글)
4. `Logs/publisher/`의 작업 로그와 `Logs/naver_blog_auto_posting_log.md`의 호환용 1행 항목 확인

e2e_smoke 성공 = 시스템 합격.

---

## §7. 일반 발행 워크플로우 (설정 완료 후)

```
1. trend_researcher 또는 직접 주제 지정
2. content_writer[full] → draft + image_plan 생성
3. 이미지 파일 준비 → image_plan.json의 path 필드 채우기
4. quality_gate[validate_and_fix] → passed=True 확인
5. python -m scripts.platforms.naver.publisher --mode publish --draft ... --meta ... --image-plan ...
6. 비공개 게시글 네이버에서 검토 → 수동 공개 전환
7. URL을 growth_manager에 전달하여 배포/분석
```
