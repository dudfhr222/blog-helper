# Prototype Skin Notes

## 로컬 mock preview

- Live Server에서 `outputs/design/prototypes/prototype_skin.html`을 연다.
- body id가 `[##_body_id_##]` placeholder일 때만 `prototype_tistory_mock.js`가 실행된다.
- 홈/목록 preview는 기본 URL에서 확인하고, 게시글 카드를 클릭하면 같은 HTML에서 `?post=slug` 상세 preview로 전환된다.
- 뒤로가기와 새로고침은 `history.pushState` 기반 URL로 최소 동작한다.
- 실제 티스토리 적용 시 body id가 `tt-body-*`로 렌더링되므로 mock JS는 실행되지 않는다.

## 로컬 mock 구분자별 데이터 구조

`prototype_tistory_mock.js`는 아래 구분을 기준으로 mock data와 DOM 처리를 나눈다.

| 구분 | 대상 치환자/블록 | mock data key | DOM 처리 |
|------|------------------|---------------|----------|
| 블로그 공통 | `[##_title_##]`, `[##_desc_##]`, `[##_blog_link_##]`, `[##_page_title_##]` | `mockData.blogPlaceholders` | 문서 title, meta, brand/link 텍스트와 href 치환 |
| 목록 반복 | `<s_list_rep>`, `[##_list_rep_title_##]`, `[##_list_rep_summary_##]`, `[##_list_rep_category_##]`, `[##_list_rep_regdate_##]`, `[##_list_rep_link_##]`, `[##_list_rep_thumbnail_url_##]` | `mockData.listRep` | `.area-common .post-list`의 원본 카드 template을 clone해 `data-local-post`, `.js-local-post-link` 부여 |
| 게시글 상세 | `<s_article_rep>`, `<s_permalink_article_rep>`, `[##_article_rep_title_##]`, `[##_article_rep_category_##]`, `[##_article_rep_author_##]`, `[##_article_rep_date_##]`, `[##_article_rep_desc_##]` | `mockData.articleRep` | `.yrbe-article-hero`, `.area-view`, `.yrbe-article-body`에 현재 post data 주입 |
| 사이드바 | `searchInput`, `[##_category_list_##]`, `<s_random_tags>`, `<s_rctps_rep>`, `<s_rctps_popular_rep>` | `mockData.sidebar` | 검색 placeholder, 카테고리, 태그, 최근글, 인기글 링크를 mock data로 렌더링 |
| 페이징/라우팅 | `<s_paging>`, `[##_list_rep_link_##]`, article prev/next link | `mockData.routing` | `?post=slug` URL과 `history.pushState`/`popstate`로 목록/상세 전환 |

`prototype_skin.html`과 `prototype_skin.css`는 Live Server로 함께 열어보는 티스토리 스킨 검증용 self-contained pair다.

## 현재 구성

| 파일 | 역할 |
|------|------|
| `prototype_skin.html` | 티스토리 통합 skin template. `[##_..._##]` 치환자와 `<s_...>` 블록을 보존한다. |
| `prototype_skin.css` | 루트 `ytbe.css` 전체를 기준으로 한 self-contained CSS. 별도 `style.css` 없이 직접 연결된다. |

## Live Server 확인 범위

- HTML은 `./prototype_skin.css`만 로컬 stylesheet로 참조한다.
- `prototype_skin.css`에는 티스토리 기본 CSS와 YRBE override가 함께 들어 있다.
- 파일 끝의 fallback CSS는 `body[id="[##_body_id_##]"]` placeholder 상태에서만 작동한다.
- fallback은 Live Server에서 상세/공지/페이지/태그/방명록/커버 블록이 한꺼번에 보이는 문제를 줄이고, 목록/홈 중심으로 preview되게 한다.

## 주의사항

- `[##_..._##]` 값과 `<s_...>` 조건 블록은 티스토리 서버에서만 실제 데이터와 페이지 상태로 치환된다.
- Live Server preview는 레이아웃/CSS 연결 확인용이며, 실제 데이터 렌더링 검증은 티스토리 적용 후 확인해야 한다.
- 실제 적용 파일인 `ytbe.html`, `ytbe.css`는 이 prototype 정리 작업에서 수정하지 않는다.

## 필수 보존 컴포넌트

- 검색창: `searchInput`
- 최근글: `s_rctps_rep`
- 인기글: `s_rctps_popular_rep`
- 카테고리: `[##_category_list_##]`
- 태그: `s_random_tags`
- 페이징: `s_paging`
