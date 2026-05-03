# outputs 디렉토리 구조

`outputs`는 agent 산출물을 단계별로 보관한다. 글 하나에 딸린 파일은 `drafts/posts/YYYYMMDD_slug/` 한 폴더에 모은다.

```text
outputs/
  drafts/
    posts/
      YYYYMMDD_slug/
        outline.md              # content_writer 아웃라인
        draft.md                # content_writer 초안
        post_meta.json          # 제목, 태그, 요약, 공개 설정
        seo_suggestions.json    # SEO 제안
        image_plan.json         # 이미지 토큰/생성 계획
        validation_report.json  # quality_gate 결과
        images/                 # image_agent 생성 이미지
    tmp/                        # smoke test 등 임시 파일

  research/
    topics/                     # trend_researcher 주제 후보

  published/
    posts/                      # 발행 글 사본
    distribution/               # 배포 로그
    runs/
      YYYYMMDD/
        results/                # 발행 결과 JSON
        screenshots/            # dry-run/검증 스크린샷
        debug/                  # 실패 시 DOM/screenshot 덤프

  analytics/
    raw/                        # 원본 성과 데이터
    reports/                    # 분석 리포트
    strategy/                   # 전략 제안

  design/
    backups/                    # skin.html/CSS 백업
    html/                       # 수정 skin.html
    css/                        # 수정 CSS
    prototypes/                 # 디자인 프로토타입
    reports/                    # 구현 보고서
    screenshots/                # 디자인 검증 스크린샷
    state/                      # 스킨 구조/상태 JSON
    debug/                      # 스킨 패치 실패 시 DOM/screenshot 덤프
```

새 글 산출물은 유형별 폴더에 흩어 저장하지 않는다. 예: `outputs/drafts/posts/20260503_bfs/draft.md`.
