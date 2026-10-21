# -*- coding: utf-8 -*-
"""우아대출 계산 모듈 (참고용 추정). JS 쌍둥이: assets/js/loan.js
 - 원리금균등: 월 상환액 M = P·r / (1 − (1+r)^−n), r = 연이율/12
 - 원금균등: 매월 원금 P/n + 잔액×r, 총이자 = P·r·(n+1)/2
 - 만기일시: 매월 P·r(이자만), 만기에 원금
 - DSR: 연 원리금 상환액 ≤ 연소득 × 한도(은행 40%), 스트레스 DSR 가산금리는 입력 금리에 더해 계산
 - 예금: 단리 세전 이자 × (1 − 15.4%), 적금: 매월 초 납입 단리 이자 = 월납입 × r/12 × n(n+1)/2"""

import math
def rnd(x): return int(math.floor(x + 0.5))

def pmt(P, rate_pct, years):
    n = int(years * 12); r = rate_pct / 1200.0
    if r == 0: return rnd(P / n)
    return rnd(P * r / (1 - (1 + r) ** -n))

def equal_payment(P, rate_pct, years):
    n = int(years * 12); m = pmt(P, rate_pct, years); total = m * n
    return dict(monthly=m, total=total, interest=total - P, n=n)

def equal_principal(P, rate_pct, years):
    n = int(years * 12); r = rate_pct / 1200.0
    first = rnd(P / n + P * r); last = rnd(P / n + (P / n) * r)
    interest = rnd(P * r * (n + 1) / 2)
    return dict(first=first, last=last, interest=interest, total=P + interest, n=n)

def bullet(P, rate_pct, years):
    n = int(years * 12); m = rnd(P * rate_pct / 1200.0); return dict(monthly=m, interest=m * n, total=P + m * n, n=n)

def yearly(P, rate_pct, years):
    """원리금균등 연도별 (납부 원금, 납부 이자, 연말 잔액)"""
    n = int(years * 12); r = rate_pct / 1200.0; m = pmt(P, rate_pct, years)
    bal = float(P); rows = []; paid_p = paid_i = 0.0
    for mo in range(1, n + 1):
        i = bal * r; pr = m - i
        if mo == n: pr = bal
        bal -= pr; paid_p += pr; paid_i += i
        if mo % 12 == 0:
            rows.append((mo // 12, rnd(paid_p), rnd(paid_i), rnd(max(bal, 0))))
            paid_p = paid_i = 0.0
    return rows

def dsr_max(income, rate_pct, years, dsr=0.40):
    """연소득·DSR 한도로 원리금균등 최대 대출액"""
    n = int(years * 12); r = rate_pct / 1200.0
    mpay = income * dsr / 12.0
    if r == 0: return int(mpay * n)
    return rnd(mpay * (1 - (1 + r) ** -n) / r / 10000.0) * 10000

def deposit(P, rate_pct, months=12):
    gross = rnd(P * rate_pct / 100.0 * months / 12.0); tax = rnd(gross * 0.154); return dict(gross=gross, tax=tax, net=gross - tax)

def savings(m, rate_pct, months=12):
    gross = rnd(m * (rate_pct / 1200.0) * months * (months + 1) / 2.0); tax = rnd(gross * 0.154)
    return dict(principal=m * months, gross=gross, tax=tax, net=gross - tax, total=m * months + gross - tax)

if __name__ == "__main__":
    import sys; sys.stdout.reconfigure(encoding="utf-8")
    print(equal_payment(300_000_000, 4.0, 30), equal_principal(300_000_000, 4.0, 30), bullet(300_000_000, 4.0, 30))
    print(yearly(300_000_000, 4.0, 30)[:2], dsr_max(50_000_000, 4.0, 30), deposit(10_000_000, 3.5), savings(500_000, 4.0))
