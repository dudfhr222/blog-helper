# 네이버 블로그 SmartEditor One 셀렉터 상수
# UI 변경 시 이 파일만 수정하면 된다.

# --- 네이버 블로그 URL ---
BLOG_WRITE_URL = "https://blog.naver.com/PostWriteForm.naver"
BLOG_LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# --- 로그인 감지 ---
LOGIN_INDICATOR_SELECTOR = "a.gnb_login"          # 로그인 버튼 (미로그인 시 표시)
USER_NICK_SELECTOR = ".MyView-module__nickname"    # 로그인 후 닉네임 (로그인 상태 확인)

# --- 글쓰기 에디터 iframe ---
# 네이버 블로그 에디터는 iframe 안에 SmartEditor가 있다.
# 버전/업데이트에 따라 달라질 수 있으므로 dry_run 스크린샷으로 확인 후 수정.
MAIN_FRAME_SELECTOR = 'iframe[name="mainFrame"]'         # 1단계 메인 프레임
EDITOR_FRAME_SELECTOR = 'iframe.se-iframe'               # 2단계 SmartEditor One iframe
EDITOR_FRAME_ALT = 'iframe[title*="에디터"]'             # 대안 셀렉터

# --- 제목 입력 ---
TITLE_INPUT_SELECTOR = '.se-title-input'                 # SmartEditor One 제목 입력란
TITLE_INPUT_ALT = '[placeholder*="제목"]'

# --- 본문 입력 ---
BODY_INPUT_SELECTOR = '.se-content'                      # SmartEditor One 본문 영역
BODY_INPUT_ALT = '.se2_inputarea'                        # SmartEditor Two 대안

# --- 이미지 업로드 ---
IMAGE_UPLOAD_BTN = 'button[data-log*="photo"]'           # 사진 추가 버튼
IMAGE_UPLOAD_BTN_ALT = 'a[href*="photo"]'                # 대안 선택
IMAGE_FILE_INPUT = 'input[type="file"][accept*="image"]' # 파일 input
IMAGE_UPLOAD_DONE = '.se-image-container img'            # 업로드 완료 표식 (이미지 태그 삽입)
IMAGE_CAPTION_INPUT = '.se-image-caption'                # 캡션 입력란

# --- 카테고리 ---
CATEGORY_SELECT = 'select[name*="category"]'             # 카테고리 셀렉트박스
CATEGORY_SELECT_ALT = '#categorySelect'

# --- 태그 ---
TAG_INPUT = '.tag_input input'                           # 태그 입력란
TAG_INPUT_ALT = 'input[placeholder*="태그"]'

# --- 공개 설정 ---
VISIBILITY_PRIVATE_BTN = 'label[for*="secret"]'          # 비공개 라디오 버튼 label
VISIBILITY_PRIVATE_RADIO = 'input[value="secret"]'       # 비공개 라디오 input
VISIBILITY_PRIVATE_ALT = 'button[data-log*="secret"]'

# --- 발행 버튼 ---
PUBLISH_BTN = 'button.publish_btn'                      # 최종 발행 버튼
PUBLISH_BTN_ALT = 'button[data-log*="publish"]'
CONFIRM_PUBLISH_BTN = '.btn_publish'                    # 발행 확인 다이얼로그 확인 버튼

# --- 발행 완료 ---
PUBLISHED_URL_PATTERN = r'https://blog\.naver\.com/[^/]+/\d+'  # 발행 완료 URL 패턴

# --- 타임아웃 (ms) ---
TIMEOUT_LOGIN = 60_000          # 로그인 대기
TIMEOUT_EDITOR_LOAD = 30_000    # 에디터 로딩
TIMEOUT_IMAGE_UPLOAD = 30_000   # 이미지 업로드 완료
TIMEOUT_PUBLISH = 30_000        # 발행 완료
