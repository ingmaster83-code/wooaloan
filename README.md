# 우아대출 (wooaloan.wooahouse.com)
대출 이자(원리금·원금균등·만기일시)·DSR 한도·예금·적금 세후 이자 pSEO 정적 사이트(1,929페이지: 대출 430·DSR 17·예금 11+조합 240·적금 10·이자 401·대출한도 616·적금목표 201). 데이터 없이 계산식만 사용.
- 계산: `scripts/loan.py` ↔ `assets/js/loan.js` (test_calc.js/test_calc.py 1,416케이스 일치 확인)
- 빌드: `python scripts/build_site.py` → `_site/`, 검증: `python scripts/check_site.py`
- 스트레스 DSR 가산금리 1.5%p는 예시값(정책 변경 시 build_site.py의 STRESS 수정)
- 2026-11-02 확장: 네이버 검색어(“3억 4% 이자”, “1억 5% 이자”)가 금액×금리 형태라 `/interest/`(금액20×금리19) 추가, `/afford/`(월 상환액→대출한도 15×8×5), `/goal/`(목표금액 적금 월 납입액), `/deposit/{금액}/{금리}/{N}개월/`. 역산 함수는 loan.py(loan_from_payment·goal_monthly·deposit_principal_for)
