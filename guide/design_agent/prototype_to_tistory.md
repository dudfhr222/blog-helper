# prototype → 티스토리 변환 가이드

> design_agent가 `prototype_skin.html` / `prototype_skin.css`를 티스토리 `skin.html` / `style.css`로 변환할 때, **다른 가이드에 명시되지 않은 두 가지 빈 칸**만 다룬다 — mock 전용 코드 제거, CSS 특이도 충돌. 그 외(DOM 매핑, 사이드바 6종 보존, 패치 절차)는 아래 사전 참조로 위임한다.

---

## 사전 참조 (작업 시작 전 반드시 읽기)

| 알아야 할 것 | 참조 |
|-------------|------|
| prototype 구조 맵, mock data → DOM 매핑표 | `outputs/design/prototypes/prototype_notes.md` |
| 사이드바 6종 + 치환자 필수 보존 목록 | `guide/design_agent/prototype_notes_usage.md` "필수 생존 항목" |
| 패치 절차, HTML/CSS 금지 패턴, 실패 코드 → 조치 | `guide/design_agent/patch_rules.md` |
| HTML 구조 변경 6단계 절차 | `guide/design_agent/tistory_skin_html_process.md` |
| 디자인 토큰·브레이크포인트 (source of truth) | `outputs/design/prototypes/prototype_skin.css` (`:root` 변수, `@media` 쿼리) |

이 문서를 적용하기 전 위 5개 문서의 해당 섹션을 먼저 읽는다.

---

## 1. 제거 규칙 (Strip List)

이식 시 반드시 제거해야 하는 항목. 잔존 시 dry-run이 통과해도 티스토리 운영 환경에서 오동작한다.

### HTML 제거

| 항목 | prototype_skin.html 위치 | 이유 |
|------|------------------------|------|
| `<link rel="stylesheet" href="./prototype_skin.css" />` | L18 | 티스토리는 `./style.css`로 교체 |
| `<script src="./prototype_tistory_mock.js" defer></script>` | L19 | 로컬 preview 전용. 티스토리에서 mock 데이터 주입 불가 |

### CSS 제거

| 항목 | prototype_skin.css 위치 | 이유 |
|------|------------------------|------|
| Live Server fallback 블록: `body[id="[##_body_id_##]"] s_t3, ...` | L9233~9261 | `body id`가 placeholder일 때만 동작. 티스토리에서는 `tt-body-*`로 치환되므로 dead code |

### 보존 대상 (제거하지 말 것)

prototype_tistory_mock.js와 별개로, **prototype_skin.html 끝부분의 인라인 `<script>` 두 개는 이식 대상**이다:

- `.post-card`에 `data-cat` 속성 부여 스크립트 (L1035~1042) — 카테고리 컬러 매핑
- 최근글/인기글 탭 전환 스크립트 (L1046~1065) — 사이드바 동작

이 둘은 mock JS와 달리 실제 DOM에서 동작한다.

### 검증 grep

```powershell
# HTML — 결과 0건이어야 통과
Select-String -Path "outputs\design\html\skin_*.html" `
  -Pattern "prototype_tistory_mock|##_body_id_##"

# CSS — 결과 0건이어야 통과
Select-String -Path "outputs\design\css\custom_*_integrated.css" `
  -Pattern 'body\[id="'
```

bash 환경:

```bash
rg -n 'data-local-view|prototype_tistory_mock|##_body_id_##' \
  outputs/design/html/skin_*.html \
  outputs/design/css/custom_*_integrated.css
```

0건이 아니면 수동 삭제 후 재검증한다.

---

## 2. CSS 특이도 상향 사다리 (3단계)

dry-run에서 `css_specificity_ok=false` 가 뜨면 아래 순서로 특이도를 올린다. **prototype의 단일 클래스 셀렉터는 base CSS의 ID 기반 셀렉터에 진다**는 점이 핵심.

실제 실패 이력: 20260503_154500 dry-run 74개 충돌 → 3단계 적용 후 0개 통과.

### 단계 1 — 클래스+자손 (특이도 0,2,0)

```css
.post-card .post-card__title {
  font-size: 1.05rem;
  color: var(--yrbe-text);
}
```

base CSS의 단순 요소 셀렉터는 이긴다. 단, ID 기반(`#container`, `#tt-body-page`)에는 진다.

### 단계 2 — `#container` 자손 (특이도 1,2,0)

```css
#container .post-card .post-card__title {
  font-size: 1.05rem;
}
```

대부분의 base CSS ID 셀렉터를 이긴다. **여기서 먼저 시도한다.**

### 단계 3 — `html body#tt-body-page #container` 풀앵커 (특이도 2,1,2 이상)

`body#tt-body-page .article-view` 등 ID+class 조합 base 규칙을 이겨야 할 때만 사용. 20260503_154500 통과 형태:

```css
html body#tt-body-page #container .yrbe-article-body .yrbe-toc {
  display: block !important;
}

html body#tt-body-page #container .yrbe-article-hero {
  left: 0 !important;
  margin-left: calc(-50vw + 50%) !important;
  width: 100vw !important;
}

html body#tt-body-page #container .page {
  max-width: var(--yrbe-page-w) !important;
}
```

### `!important` 정책

- **3단계 풀앵커에서, 기존 base CSS에 `!important`가 선언된 속성을 override할 때만** 허용.
- 새 속성에 습관적으로 붙이는 것은 금지 (`patch_rules.md` "CSS 금지 패턴" 참조).
- 사용 시 인라인 주석으로 충돌 대상 셀렉터를 명시:

```css
/* !important: body#tt-body-page .article-view (특이도 1,2,1) override */
html body#tt-body-page #container .yrbe-article-body { padding: 0 !important; }
```

### 검증 기준

`outputs/design/state/last_run.json` 의 `gates.css_specificity_ok=true`. 자체 선언 금지.

---

## 3. 자기검증 체크리스트

→ `guide/design_agent/prototype_notes_usage.md` § 자기검증 체크리스트 참조. 4개 PASS 후 보고서 작성.
