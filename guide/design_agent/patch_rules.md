# 패치 규칙 — HTML / CSS 필수 체크리스트

> design_agent는 HTML 또는 CSS를 수정하기 전 이 문서를 항상 먼저 읽는다.

> **자동 검증**: 아래 사이드바 6종·치환자·CSS 특이도 규칙은 `scripts/platforms/tistory/patch_validator.py`로 자동 강제된다. `skin_patcher.py --patch --dry-run` 호출 시 정적 검증을 통과하지 못하면 브라우저를 열기 전에 차단되며, 결과는 `outputs/design/state/last_run.json`에 게이트 boolean으로 기록된다. 에이전트는 이 파일의 `gates_passed=true`일 때만 보고를 작성할 수 있다.

## 실패 코드 매핑 (last_run.json.errors → 원인 / 조치)

| 에러 prefix | 원인 | 조치 |
|---|---|---|
| `sidebar:components missing` | 6종 컴포넌트 마커 중 하나 이상 누락 | 누락 컴포넌트를 `<s_sidebar_element>` 내부에 복원 |
| `sidebar:widgets outside <s_sidebar_element>` | 위젯이 sidebar element 밖에 배치됨 | 해당 위젯을 sidebar element 내부로 이동 |
| `tokens:missing` | base의 `[##_*_##]` 또는 `<s_*>` 블록이 new에서 제거됨 | base에서 토큰 복원 (이름·위치 변경 금지) |
| `html:line count collapsed` | new HTML이 base의 50% 미만 | base 전체를 base로 사용했는지 확인. 부분 파일 차단. |
| `css:base lines lost` | new CSS가 base의 95% 미만 | custom CSS만 단독 전달 금지. base + custom 통합본만 전달. |
| `specificity:` (specificity/important_override) | cascade에서 의도된 override가 패배 | selector 재작성 또는 specificity 끌어올림 (`!important` 남발 금지) |
| `specificity:shorthand_longhand` | 후행 shorthand가 선행 longhand를 덮어씀 | 순서 조정 또는 shorthand 제거 |
| `roundtrip:* mismatch` | Monaco 에디터 set 후 get 값 불일치 | 특수문자 escape 점검 후 재시도 |
| `playwright:timeout` | Monaco 에디터 로딩/저장 타임아웃 | `pending_manual.json` 자동 적재됨. 수동 적용 후 항목 resolve. |
| `save_confirmed:* reload mismatch` | apply 후 reload하니 값이 다름 | 저장 미실행 의심. 재시도 또는 수동 저장. |

---

## HTML 패치 규칙

`skin_patcher --html` 옵션은 티스토리 skin.html **전체를 교체**한다.
신규 구조만 담긴 파일을 단독으로 넘기면 나머지 HTML이 전부 소실된다.

**순서 (반드시 준수):**

1. 최신 skin.html 백업(`outputs/design/backups/skin_html_*.html` 중 가장 최신)을 읽는다.
2. 백업 기반으로 수정한 **전체 파일**을 만든다.
3. `outputs/design/html/skin_YYYYMMDD_HHMMSS.html`로 저장한다.
4. 이 파일만 skin_patcher에 넘긴다.

```
# 올바른 방법
백업 skin.html 전체 → 구조 수정 → 완전한 skin.html → skin_patcher --html 전체파일

# 금지
skin_patcher --html 신규_섹션_only.html   ← 나머지 HTML 전체 소실
```

---

## 패치 전 필수 diff 체크

수정 파일을 skin_patcher에 넘기기 전, 백업 파일과 diff 비교하여 아래 항목 누락 여부를 확인한다.

### 사이드바 컴포넌트 생존 체크리스트 (6개 전부 있어야 함)

| 컴포넌트 | 확인할 마커 |
|----------|------------|
| 프로필 카드 | `profile-card` 또는 `box-profile` |
| 검색창 | `searchInput` 또는 `search-box` |
| 카테고리 | `[##_category_list_##]` |
| 태그 | `s_random_tags` |
| 최근글/인기글 | `s_rctps_rep` 및 `s_rctps_popular_rep` |
| 페이징 | `s_paging` |

### 치환자/s_블록 생존 체크리스트 (누락 시 즉시 중단)

- `[##_page_title_##]`, `[##_title_##]`, `[##_blog_link_##]`, `[##_skin_url_##]`
- `s_t3`, `s_list`, `s_article_rep`, `s_sidebar`, `s_sidebar_element`
- `[##_revenue_list_upper_##]`, `[##_revenue_list_lower_##]`

**체크리스트 항목 하나라도 누락되면 패치를 즉시 중단하고 원인 파악 후 재작성한다.**

---

## 사이드바 컴포넌트 배치 규칙

위젯형 컴포넌트(검색창·최근글·인기글·태그 등)는 반드시 `<s_sidebar_element>` 내부에 배치한다.
외부에 하드코딩하면 위젯 비활성화 시 렌더링이 불안정해진다.

```html
<!-- 안전한 배치 (권장) -->
<s_sidebar>
  <s_sidebar_element>
    <div class="sidebar-card search-sidebar">...</div>
    <div class="sidebar-card box-recent">...</div>
  </s_sidebar_element>
</s_sidebar>

<!-- 주의 필요 — 항상 표시되지만 CSS 없으면 숨겨짐 -->
<s_sidebar>
  <div class="sidebar-card search-sidebar">...</div>
  <s_sidebar_element>...</s_sidebar_element>
</s_sidebar>
```

---

## CSS 패치 규칙

`skin_patcher --css` 옵션은 티스토리 CSS 에디터 **전체를 교체**한다.
신규 항목만 담긴 파일을 단독으로 넘기면 base CSS 전체가 소실된다.

**순서 (반드시 준수):**

1. 최신 CSS 백업(`outputs/design/backups/skin_css_*.css` 중 가장 최신)을 읽는다.
2. 신규 custom CSS를 base CSS 끝에 append한 **통합 파일**을 만든다.
3. `outputs/design/css/custom_YYYYMMDD_integrated.css`로 저장한다.
4. 이 통합 파일만 skin_patcher에 넘긴다.

```
# 올바른 방법
base CSS (N줄) + custom CSS (M줄) → 통합 파일 → skin_patcher --css 통합파일

# 금지
skin_patcher --css custom_only.css   ← base CSS 전체 소실
```

---

## CSS 금지 패턴

- 불필요한 `!important` 남발
- 과도한 `z-index`
- 전체 레이아웃을 깨는 `position: fixed`
- 확인되지 않은 전역 selector 대량 수정
- HTML 구조와 맞지 않는 프로토타입 selector 유지
- custom CSS만 단독으로 skin_patcher에 넘기기 (base CSS 소실)

---

## 패치 실패 시 수동 적용

skin_patcher가 Monaco 에디터 타임아웃 등으로 실패하면 아래 방법으로 수동 적용한다.

**CSS 실패:**
1. `outputs/design/css/custom_YYYYMMDD_integrated.css` 전체 복사
2. 티스토리 관리자 > 꾸미기 > 스킨 편집 > CSS 탭 > 전체 교체 후 저장

**HTML 실패:**
1. `outputs/design/html/skin_YYYYMMDD_HHMMSS.html` 전체 복사
2. 티스토리 관리자 > 꾸미기 > 스킨 편집 > HTML 탭 > 전체 교체 후 저장
