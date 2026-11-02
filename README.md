# 우아대출 (wooaloan.wooahouse.com)
대출 이자(원리금·원금균등·만기일시)·DSR 한도·예금·적금 세후 이자 pSEO 정적 사이트(1,929페이지: 대출 430·DSR 17·예금 11+조합 240·적금 10·이자 401·대출한도 616·적금목표 201). 데이터 없이 계산식만 사용.
- 계산: `scripts/loan.py` ↔ `assets/js/loan.js` (test_calc.js/test_calc.py 1,416케이스 일치 확인)
- 빌드: `python scripts/build_site.py` → `_site/`, 검증: `python scripts/check_site.py`
- 스트레스 DSR 가산금리 1.5%p는 예시값(정책 변경 시 build_site.py의 STRESS 수정)
- 2026-11-02 확장: 네이버 검색어(“3억 4% 이자”, “1억 5% 이자”)가 금액×금리 형태라 `/interest/`(금액20×금리19) 추가, `/afford/`(월 상환액→대출한도 15×8×5), `/goal/`(목표금액 적금 월 납입액), `/deposit/{금액}/{금리}/{N}개월/`. 역산 함수는 loan.py(loan_from_payment·goal_monthly·deposit_principal_for)
- 2026-11-02 금융상품 금리 비교 추가(금융감독원 금융상품한눈에 오픈API, 3,151페이지): `/product/`(예금436·적금337·주담대107·전세57·신용110 상품 상세) `/rank/`(금리 순위 34) `/company/`(금융사 133). 수집 `python scripts/fetch_finlife.py`(키는 환경변수 FINLIFE_AUTH 또는 ../_newdata/finlife.env, 저장소에 넣지 않음) → data/finlife/*.json 누적 → `python scripts/build_site.py`. 상품 ID=금융회사코드-상품코드로 고정, 공시에서 빠진 상품은 페이지를 남기고 noindex·사이트맵 제외(우아장학금 URL 붕괴 사고 방지). 매월 20일경 공시 갱신 때 재수집·재배포.
