# Prototype Notes Usage Guide

이 문서는 `design_agent`가 스타일 수정, CSS 분석, HTML 구조 변경을 시작할 때 `outputs/design/prototypes/prototype_notes.md`를 어떻게 사용할지 정의한다.

## 목적

`prototype_notes.md`는 긴 `ytbe.html`, `ytbe.css`를 바로 훑기 전에 보는 구조 지도다. 작업 대상 영역, 관련 selector, 기존 override 구간, 보존 필수 티스토리 컴포넌트를 빠르게 찾기 위해 사용한다.

단, 이 문서는 source of truth가 아니다. 실제 패치 기준은 항상 최신 백업 파일과 `outputs/design/state/skin_structure_*.json`이다.

## 언제 읽는가

아래 작업에서는 요구사항 분석 직후 반드시 읽는다.

- 스타일 수정
- CSS 충돌 분석
- HTML/CSS selector 매핑 분석
- 티스토리 스킨 레이아웃 변경
- 글 목록, 글 상세, 사이드바, 헤더, footer, paging 수정
- `ytbe.html`, `ytbe.css`, `prototype_skin.*`, `prototype_article_detail.*` 기반 분석

단순 레퍼런스 조사나 새 시안 brainstorming만 할 때는 생략할 수 있다.

## 사용 순서

1. `guide/design_agent/patch_rules.md`를 먼저 읽어 패치 금지 조건을 확인한다.
2. `outputs/design/prototypes/prototype_notes.md`를 읽고 요청 영역이 어느 HTML 블록과 CSS 구간에 연결되는지 찾는다.
3. 최신 `outputs/design/backups/skin_html_*.html`, `outputs/design/backups/skin_css_*.css`를 읽어 현재 실제 상태와 맞는지 대조한다.
4. 최신 `outputs/design/state/skin_structure_*.json`이 있으면 selector 위치를 재확인한다.
5. 문서와 실제 백업이 다르면 백업과 구조 리포트를 우선하고, 보고서에 `prototype_notes.md stale 가능성`을 기록한다.

## 분석 출력 형식

스타일 수정 전 분석에는 아래 블록을 포함한다.

```text
prototype_notes 매핑:
- 대상 HTML 블록:
- 관련 티스토리 치환자:
- 관련 CSS 구간:
- 기존 override / fix 구간:
- 보존 필수 컴포넌트:
- 최신 백업과의 차이:
```

## 수정 설계 원칙

- `prototype_notes.md`의 라인대는 탐색 힌트로만 쓴다. 실제 수정 전에는 반드시 현재 파일에서 selector를 다시 검색한다.
- HTML 구조 변경이 필요한 경우 `tistory_skin_html_process.md` 절차를 따른다.
- CSS만으로 충분한 경우 HTML을 건드리지 않고 기존 override 구간 뒤에 scoped selector를 추가한다.
- 기존 `YRBE Custom Override CSS` 구간과 같은 selector를 수정할 때는 cascade 순서와 specificity를 먼저 계산한다.
- 목록 카드, 글 상세 본문, sidebar 컴포넌트는 같은 selector를 공유하는 경우가 많으므로 영향 범위를 문서에 남긴다.

## 패치 전 체크

`patch_rules.md` § 사이드바 컴포넌트 생존 체크리스트 + § 치환자/s_블록 생존 체크리스트를 따른다.

## Fix 8: Live Server Preview의 구조 은폐 경고

`prototype_skin.html`을 Live Server로 열 때 `prototype_tistory_mock.js`가 아래 두 가지 방식으로 실제 구조 결함을 은폐한다.

### 문제 1: `<s_article_rep>` 중복 감지 불가

mock JS는 `<s_article_rep>` 블록을 `display:contents`로 렌더링하거나 내부 콘텐츠만 DOM에 주입한다. 따라서 HTML에 `<s_article_rep>`가 두 번 존재해도 Live Server에서는 한 번 렌더링된 것처럼 보인다. 실제 티스토리 서버에서는 두 번 렌더링되어 글 상세 페이지에 hero 영역이 두 번 나타나거나 레이아웃이 깨진다.

**확인 방법**: HTML 파일에서 `grep -c "<s_article_rep>"` 결과가 1이어야 한다.

### 문제 2: `<s_sidebar_element>` 슬롯 의존성 은폐

티스토리 관리자 패널에서 등록된 모듈 수에 따라 `<s_sidebar_element>` 렌더링 수가 달라진다. mock JS는 미리 정의된 mock data로 사이드바를 채우므로 `<s_sidebar_element>`가 없어도 사이드바 위젯이 정상 보인다. 실제 티스토리에서는 등록 모듈이 없으면 `<s_sidebar_element>` 내부 콘텐츠가 렌더링되지 않는다.

**해결**: `<s_sidebar_element>`에 의존하지 않고 `<s_sidebar>` 내부에 위젯을 직접 배치하는 Fix 3 방식을 사용한다. mock JS는 이 방식에서도 올바르게 동작한다.

### 주의

위 두 문제는 Local Server에서 정상 보여도 티스토리에 적용하면 결함이 나타난다. `prototype_notes.md`와 Live Server는 CSS/레이아웃 확인용이며, 구조 검증은 반드시 `grep`과 `skin_patcher --dry-run`으로 수행한다.

---

## 보고서 포함 항목

작업 보고서에는 다음을 포함한다.

- `prototype_notes.md`에서 참고한 섹션명
- 실제 백업 파일에서 재확인한 selector
- 문서와 실제 파일이 달랐던 부분
- 최종 수정한 HTML/CSS 구간
- 패치 전 보존 체크 결과

## 자기검증 체크리스트 (이식 완료 후)

이식 작업 종료 후 4개 모두 PASS여야 보고서 작성:

1. **제거 검증** — `prototype_to_tistory.md` § 1 grep 명령 결과 0건
2. **사이드바·치환자 생존** — 위 "패치 전 체크" 항목 grep 명령 (전부 1건 이상)
3. **dry-run 통과** — `last_run.json.gates_passed=true`, 특히 `css_specificity_ok=true`
4. **시각 확인** — PC 목록 / PC 상세 / 모바일 목록 / 모바일 상세 4화면 스크린샷에 사용자 OK

하나라도 FAIL이면 해당 단계로 돌아간다. apply는 4번 OK 수령 후에만 진행 (`patch_rules.md` "패치 절차" 참조).
