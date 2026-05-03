# Tistory Skin HTML/CSS Process

이 문서는 디자인 에이전트가 CSS만 수정하는 단계를 넘어, 티스토리 `skin.html` 구조까지 변경할 때 따르는 작업 순서다.

## 목표

프로토타입의 `hero`, `post-card`, `profile-card` 구조를 티스토리 치환자 구조에 맞게 이식하고, 해당 HTML에 맞춰 CSS를 다시 작성한다. 실제 적용은 백업, dry-run, 화면 확인 이후에만 진행한다.

## 산출물 위치

| 유형 | 경로 |
|------|------|
| HTML 백업 | `outputs/design/backups/skin_html_YYYYMMDD_HHMMSS.html` |
| CSS 백업 | `outputs/design/backups/skin_css_YYYYMMDD_HHMMSS.css` |
| 수정 HTML | `outputs/design/html/skin_custom_YYYYMMDD_HHMMSS.html` |
| 수정 CSS | `outputs/design/css/custom_YYYYMMDD_HHMMSS.css` |
| 구조 분석 | `outputs/design/state/skin_structure_YYYYMMDD_HHMMSS.json` |
| 검증 스크린샷 | `outputs/design/screenshots/` |

## 전체 흐름

### 1. 현재 티스토리 `skin.html` 백업

CSS만 백업하지 말고 HTML/CSS를 한 번에 백업한다.

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m scripts.platforms.tistory.skin_patcher --backup --target all
```

HTML만 다시 백업해야 할 때:

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m scripts.platforms.tistory.skin_patcher --backup --target html
```

### 2. 실제 구조 위치 확인

먼저 `outputs/design/prototypes/prototype_notes.md`를 읽어 요청 영역이 어느 HTML 블록과 CSS 구간에 연결되는지 확인한다. 이 문서는 탐색 지도이므로, 아래 백업/inspect 결과와 반드시 대조한다.

백업된 HTML에서 아래 위치를 먼저 찾는다.

- `.header`
- `.area-main`
- `.area-aside`
- `.article-type-common`
- 티스토리 치환자: `<s_t3>`, `<s_article_rep>`, `<s_permalink_article_rep>`, `<s_sidebar>`
- `prototype_notes.md`에서 요청 영역에 연결된 selector와 보존 필수 컴포넌트

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m scripts.platforms.tistory.skin_patcher --inspect --html outputs/design/backups/skin_html_YYYYMMDD_HHMMSS.html
```

구조 분석 결과는 `outputs/design/state/skin_structure_*.json`에 저장한다.

문서와 실제 백업이 다르면 실제 백업과 `skin_structure_*.json`을 우선한다. 보고서에는 `prototype_notes.md`와 달랐던 selector 또는 구간을 기록한다.

### 3. 프로토타입 구조 이식

프로토타입 HTML을 그대로 복사하지 않는다. 티스토리 치환자 바깥 구조만 재배치한다.

| 프로토타입 요소 | 티스토리 이식 위치 |
|----------------|-------------------|
| `hero` | `.header` 아래 또는 `.area-main` 시작 전 |
| `post-card` | `<s_article_rep>` 반복 영역 내부의 글 목록 카드 |
| `profile-card` | `.area-aside` 또는 `<s_sidebar>` 내부 |
| category/tag UI | 기존 티스토리 category/tag 치환자 주변 |
| article detail layout | `.article-type-common` 또는 `<s_permalink_article_rep>` 내부 |

주의사항:

- `<s_...>` 티스토리 치환자 태그는 삭제하지 않는다.
- `[##_..._##]` 치환자는 이름을 바꾸지 않는다.
- 목록 화면과 글 상세 화면의 조건부 블록을 섞지 않는다.
- 프로토타입의 더미 텍스트는 모두 티스토리 치환자로 교체한다.

### 4. HTML 구조에 맞춘 CSS 재작성

HTML 구조가 확정된 뒤 CSS를 새로 작성한다.

기본 원칙:

- 기존 CSS append override가 아니라, 변경 HTML을 기준으로 selector를 정리한다.
- 전역 selector(`*`, `body`, `a`) 변경은 최소화한다.
- PC 기준, 모바일 기준을 모두 작성한다.
- 목록 카드, 글 상세 본문, 사이드바, 코드 블록, 태그/카테고리를 각각 분리한다.

### 5. PC/모바일/글목록/글상세 확인

적용 전 dry-run으로 에디터에만 주입하고 저장하지 않는다.

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m scripts.platforms.tistory.skin_patcher --patch --html outputs/design/html/skin_custom_YYYYMMDD_HHMMSS.html --css outputs/design/css/custom_YYYYMMDD_HHMMSS.css --dry-run
```

확인해야 할 화면:

- PC 글목록
- PC 글상세
- 모바일 글목록
- 모바일 글상세
- 사이드바 노출/접힘
- 코드 블록 가로 스크롤
- 이미지/썸네일 없는 글 카드
- 카테고리/태그/검색 영역

### 6. 실제 적용

dry-run 스크린샷과 HTML/CSS 백업을 확인한 뒤에만 저장한다.

```powershell
$env:PYTHONIOENCODING='utf-8'; python -m scripts.platforms.tistory.skin_patcher --patch --html outputs/design/html/skin_custom_YYYYMMDD_HHMMSS.html --css outputs/design/css/custom_YYYYMMDD_HHMMSS.css
```

적용 후 문제가 있으면 가장 최근 `skin_html_*.html`, `skin_css_*.css` 백업을 사용해 되돌린다.

## 디자인 에이전트 호출 시 필수 컨텍스트

```text
request: [사용자 디자인 요청]
mode: skin-html-css
reference_guide: guide/design_agent/reference.md
skin_process: guide/design_agent/tistory_skin_html_process.md
prototype_notes_usage: guide/design_agent/prototype_notes_usage.md
prototype_notes: outputs/design/prototypes/prototype_notes.md
backup_html: outputs/design/backups/skin_html_*.html 중 최신
backup_css: outputs/design/backups/skin_css_*.css 또는 backup_*.css 중 최신
required_checks:
  - .header
  - .area-main
  - .area-aside
  - .article-type-common
  - PC/mobile list/detail
```
