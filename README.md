# 우아대출 (wooaloan.wooahouse.com)
대출 이자(원리금·원금균등·만기일시)·DSR 한도·예금·적금 세후 이자 pSEO 정적 사이트(471페이지). 데이터 없이 계산식만 사용.
- 계산: `scripts/loan.py` ↔ `assets/js/loan.js` (test_calc.js/test_calc.py 1,416케이스 일치 확인)
- 빌드: `python scripts/build_site.py` → `_site/`, 검증: `python scripts/check_site.py`
- 스트레스 DSR 가산금리 1.5%p는 예시값(정책 변경 시 build_site.py의 STRESS 수정)
