# 티스토리 글쓰기 에디터 셀렉터 상수
# UI 변경 시 이 파일만 수정. dry_run 스크린샷으로 검증 후 수정.
#
# ⚠️ Tistory Open API 2024년 종료 → Playwright 브라우저 자동화로 대체
# 카카오 계정으로 로그인 (blog_config.yaml의 owner_email)

# --- URL ---
TISTORY_WRITE_URL_TMPL = "https://{blog_name}.tistory.com/manage/newpost/"
TISTORY_LOGIN_URL = "https://www.tistory.com/auth/login"

# --- 로그인 감지 ---
# 에디터 페이지 접근 성공 여부로 로그인 상태 확인 (에디터 로드 = 로그인 성공)
TISTORY_LOGGED_IN_SELECTOR = "textarea#post-title-inp"    # 제목 textarea (에디터 로드 완료 지표)
TISTORY_LOGGED_IN_ALT = ".userblog_set"                   # 관리 사이드바 (구버전)
TISTORY_LOGGED_IN_ALT2 = "#category-btn"                  # 카테고리 버튼
TISTORY_LOGGED_IN_EDITOR = "textarea#post-title-inp"      # 동일 (폴백용)
TISTORY_LOGGED_IN_EDITOR_ALT = "#post-title-inp"          # ID 선택자

# --- 카카오 로그인 버튼 ---
TISTORY_KAKAO_BTN = "a.btn_login.kakao_account"
TISTORY_KAKAO_BTN_ALT = "button.btn-kakao"
TISTORY_KAKAO_BTN_ALT2 = "a[href*='kakao']"

# --- 제목 입력 ---
TISTORY_TITLE_INPUT = "textarea#post-title-inp"           # Kakao Editor 제목 textarea
TISTORY_TITLE_INPUT_ALT = "#post-title-inp"               # ID 선택자
TISTORY_TITLE_INPUT_ALT2 = "textarea.textarea_tit"        # class 선택자

# --- HTML 편집기 모드 전환 ---
# 기본 에디터 대신 HTML 모드를 사용해 본문을 안정적으로 주입한다.
TISTORY_HTML_BTN = "button[data-entry-type='html']"
TISTORY_HTML_BTN_ALT = "button[title='HTML 편집']"
TISTORY_HTML_BTN_ALT2 = ".toolbar-more button:last-child"

# --- HTML 편집기 입력 영역 ---
TISTORY_HTML_EDITOR = ".CodeMirror"
TISTORY_HTML_EDITOR_LINE = ".CodeMirror-line"
TISTORY_HTML_TEXTAREA = "textarea.CodeMirror-scroll"  # CodeMirror hidden textarea

# --- 본문 에디터 (기본 모드 — contenteditable) ---
TISTORY_BODY_EDITOR = ".ProseMirror"
TISTORY_BODY_EDITOR_ALT = "[contenteditable='true'].editor-content"
TISTORY_BODY_EDITOR_ALT2 = "[contenteditable='true']"

# --- 이미지 업로드 ---
TISTORY_IMAGE_BTN = "button[data-type='image']"
TISTORY_IMAGE_BTN_ALT = "button[title*='사진']"
TISTORY_IMAGE_FILE_INPUT = "input[type='file']"
TISTORY_IMAGE_DONE = ".imageblock img"              # 업로드 완료 표식

# --- 카테고리 ---
TISTORY_CATEGORY_SELECT = "select[name='category']"
TISTORY_CATEGORY_SELECT_ALT = "#category"
TISTORY_CATEGORY_SELECT_ALT2 = "select.category-select"

# --- 태그 ---
TISTORY_TAG_INPUT = "input.tag-input"
TISTORY_TAG_INPUT_ALT = "input[placeholder*='태그']"
TISTORY_TAG_INPUT_ALT2 = "#tagText"

# --- 공개 설정 (비공개 강제) ---
# visibility 값: 0=비공개, 1=보호, 3=발행
TISTORY_VISIBILITY_PRIVATE_RADIO = "input[id='open0']"
TISTORY_VISIBILITY_PRIVATE_LABEL = "label[for='open0']"
TISTORY_VISIBILITY_PRIVATE_BTN = "button[data-visibility='private']"

# --- 발행 버튼 (완료 버튼) ---
TISTORY_PUBLISH_BTN = "#publish-layer-btn"            # 완료 버튼 (모달 열기)
TISTORY_PUBLISH_BTN_ALT = "button.btn-default"        # 폴백
TISTORY_PUBLISH_BTN_ALT2 = "button:has-text('완료')" # 텍스트 매칭

# --- 발행 모달 내부 ---
TISTORY_MODAL_PRIVATE_RADIO = "input#open0"           # 비공개 라디오 (기본값으로 이미 선택됨)
TISTORY_MODAL_PRIVATE_LABEL = "label[for='open0']"   # 비공개 라디오 레이블
# 비공개 저장 버튼 — 모달에서 실제 발행을 트리거하는 버튼
TISTORY_MODAL_PUBLISH_CONFIRM = "button:has-text('비공개 저장')"
TISTORY_MODAL_PUBLISH_CONFIRM_ALT = "button.btn-primary, .mce-btn-type1.select_btn"
TISTORY_CONFIRM_PUBLISH_BTN = ".btn-primary"          # 확인 다이얼로그

# --- 발행 완료 URL 패턴 ---
TISTORY_PUBLISHED_URL_PATTERN = r"https://[^/]+\.tistory\.com/\d+"

# --- 타임아웃 (ms) ---
TISTORY_TIMEOUT_LOGIN = 120_000          # 카카오 로그인 대기 (충분히 길게)
TISTORY_TIMEOUT_EDITOR_LOAD = 30_000
TISTORY_TIMEOUT_IMAGE_UPLOAD = 30_000
TISTORY_TIMEOUT_PUBLISH = 30_000
