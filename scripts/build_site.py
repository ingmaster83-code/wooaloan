# -*- coding: utf-8 -*-
"""우아대출 정적 사이트 생성기 → _site/.  사용: python scripts/build_site.py"""
import sys, shutil, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import *
import loan as L

MAN, EOK = 10_000, 100_000_000

def table(heads, rows, num=()):
    th = "".join('<th%s>%s</th>' % (' class="num"' if i in num else "", h) for i, h in enumerate(heads))
    body = "".join("<tr>%s</tr>" % "".join('<td%s>%s</td>' % (' class="num"' if i in num else "", v) for i, v in enumerate(r)) for r in rows)
    return '<div class="tbl-wrap"><table class="tbl"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (th, body)

def chips(items): return '<div class="chips">%s</div>' % "".join('<a class="chip" href="%s">%s</a>' % (u, esc(t)) for t, u in items)

def amt(n):
    n = int(round(n)); eok, rest = divmod(n, EOK); man = rest // MAN; parts = []
    if eok: parts.append("%d억" % eok)
    if man:
        ch, mn = divmod(man, 1000); s = ("%d천" % ch) if ch else ""
        if mn: s += "%d" % mn
        parts.append(s + "만원")
    return " ".join(parts) or "0원"

def amt2(n):
    n = int(round(n / MAN)) * MAN; eok, rest = divmod(n, EOK); man = rest // MAN
    return " ".join(x for x in ("%d억" % eok if eok else "", "{:,}만원".format(man) if man else ("" if eok else "0원")) if x) if (eok or man) else "0원"

def aslug(n): return amt(n).replace(" ", "").replace("만원", "")
def rs(r): return ("%g" % r)
def pct(x, d=2): return ("%." + str(d) + "f%%") % x
def near(lst, v, k=3):
    i = lst.index(v); return lst[max(0, i - k): i + k + 1]

LOAN_AMTS = [1000 * MAN, 3000 * MAN, 5000 * MAN, 7000 * MAN, EOK, 15000 * MAN, 2 * EOK, 25000 * MAN, 3 * EOK, 4 * EOK, 5 * EOK, 7 * EOK, 10 * EOK]
RATES = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0]
def years_for(a): return [1, 3, 5, 10] if a <= 7000 * MAN else [5, 10, 20, 30]
LNOTE = "원리금균등은 매월 같은 금액을 내는 방식, 원금균등은 매월 같은 원금에 줄어드는 이자를 더해 내는 방식, 만기일시는 이자만 내다 만기에 원금을 갚는 방식입니다. 거치기간·중도상환수수료·인지세·변동금리 변화는 반영하지 않은 참고용 추정입니다."

# ───────────────────────── 대출 ─────────────────────────
def page_loan(a, rate, y):
    path = "/loan/%s/%s/%d년/" % (aslug(a), rs(rate), y)
    e = L.equal_payment(a, rate, y); p = L.equal_principal(a, rate, y); b = L.bullet(a, rate, y)
    up = L.equal_payment(a, rate + 0.5, y)["monthly"] - e["monthly"]
    ratio = e["interest"] / a * 100
    lead = (f"<p class=\"lead\"><b>{amt(a)}</b>을 연 <b>{rs(rate)}%</b>로 <b>{y}년</b> 빌리면 원리금균등 기준 매월 <b>{won(e['monthly'])}원</b>을 내고 총이자는 <b>{won(e['interest'])}원</b>(원금의 {pct(ratio, 1)})입니다. "
            f"원금균등이면 첫 달 {won(p['first'])}원에서 시작해 마지막 달 {won(p['last'])}원으로 줄고 총이자는 {won(p['interest'])}원, 만기일시면 매월 이자 {won(b['monthly'])}원입니다. 금리가 0.5%p 오르면 월 상환액이 약 {won(up)}원 늘어납니다.</p>")
    t1 = table(["상환 방식", "월 납입액", "총 이자", "총 상환액"], [["원리금균등", won(e["monthly"]) + "원", won(e["interest"]) + "원", won(e["total"]) + "원"], ["원금균등", "첫 달 %s원 → 마지막 %s원" % (won(p["first"]), won(p["last"])), won(p["interest"]) + "원", won(p["total"]) + "원"], ["만기일시", won(b["monthly"]) + "원 (이자만)", won(b["interest"]) + "원", won(b["total"]) + "원"]], (1, 2, 3))
    yr = L.yearly(a, rate, y)
    pick = [r for r in yr if r[0] in (1, 2, 3, 5, 10, 15, 20, 25, 30) or r[0] == y]
    t2 = table(["연차", "그해 납부 원금", "그해 납부 이자", "연말 대출 잔액"], [[("%d년차" % r[0]), won(r[1]) + "원", won(r[2]) + "원", won(r[3]) + "원"] for r in pick], (1, 2, 3))
    n_rate = table(["금리", "월 상환액(원리금균등)", "총 이자"], [['<a href="/loan/%s/%s/%d년/">연 %s%%</a>' % (aslug(a), rs(x), y, rs(x)) if x != rate else "<b>연 %s%%</b>" % rs(x), won(L.equal_payment(a, x, y)["monthly"]) + "원", won(L.equal_payment(a, x, y)["interest"]) + "원"] for x in near(RATES, rate)], (1, 2))
    ys = years_for(a)
    n_year = table(["대출 기간", "월 상환액(원리금균등)", "총 이자"], [['<a href="/loan/%s/%s/%d년/">%d년</a>' % (aslug(a), rs(rate), x, x) if x != y else "<b>%d년</b>" % x, won(L.equal_payment(a, rate, x)["monthly"]) + "원", won(L.equal_payment(a, rate, x)["interest"]) + "원"] for x in ys], (1, 2))
    amts = [x for x in LOAN_AMTS if y in years_for(x)]
    n_amt = table(["대출 금액", "월 상환액(원리금균등)", "총 이자"], [['<a href="/loan/%s/%s/%d년/">%s</a>' % (aslug(x), rs(rate), y, amt(x)) if x != a else "<b>%s</b>" % amt(x), won(L.equal_payment(x, rate, y)["monthly"]) + "원", won(L.equal_payment(x, rate, y)["interest"]) + "원"] for x in near(amts, a)], (1, 2))
    need = a * 0  # placeholder to keep formatting simple
    inc40 = e["monthly"] * 12 / 0.40
    body = f"""
<div class="page-head"><h1>{amt(a)} 대출 이자 연 {rs(rate)}% {y}년 — 월 {won(e['monthly'])}원</h1><p>원리금균등·원금균등·만기일시 비교 · 연도별 잔액</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>월 상환액</small><b>{won(e['monthly'])}원</b></div><div class="stat"><small>총 이자</small><b>{won(e['interest'])}원</b></div><div class="stat"><small>총 상환액</small><b>{won(e['total'])}원</b></div></div>
{ad()}
<h2 class="group-title">💳 상환 방식별 비교</h2>
{t1}
<h2 class="group-title">📅 원리금균등 연도별 상환 현황</h2>
{t2}
<h2 class="group-title">📈 금리가 다르면</h2>
{n_rate}
<h2 class="group-title">⏳ 기간이 다르면</h2>
{n_year}
<h2 class="group-title">💰 금액이 다르면</h2>
{n_amt}
<h2 class="group-title">📌 알아두기</h2>
<ul class="lead" style="margin-left:20px"><li>{LNOTE}</li><li>이 대출의 연 원리금 상환액은 {won(e['monthly'] * 12)}원이라 DSR 40% 기준으로는 연소득이 약 {won(inc40)}원 이상이어야 안정적으로 받을 수 있습니다(다른 대출 없음 가정).</li><li>중도상환수수료는 보통 대출 후 3년 이내 상환 시 상환액 × 약 0.5~1.5% × 잔존기간 비율로 부과됩니다.</li></ul>
{chips([(f"{amt(a)} 대출 전체 표", "/loan/%s/" % aslug(a)), ("대출 이자 계산기", "/calculator/"), ("DSR 대출 한도", "/dsr/"), ("예금 이자", "/deposit/")])}
"""
    faq = [(f"{amt(a)} 연 {rs(rate)}% {y}년 월 상환액은?", f"원리금균등 기준 월 {won(e['monthly'])}원이며 총이자는 {won(e['interest'])}원입니다."), ("원리금균등과 원금균등 중 뭐가 유리한가요?", f"총이자는 원금균등이 적습니다({won(p['interest'])}원 vs {won(e['interest'])}원). 대신 초기 부담이 커서 원리금균등을 쓰는 경우가 많습니다."), ("금리가 오르면 얼마나 늘어나나요?", f"금리가 0.5%p 오르면 월 상환액이 약 {won(up)}원 늘어납니다.")]
    write(path, layout(path, f"{amt(a)} 대출 이자 연 {rs(rate)}% {y}년 월 상환액 {won(e['monthly'])}원", f"{amt(a)}을 연 {rs(rate)}%로 {y}년 빌리면 월 {won(e['monthly'])}원, 총이자 {won(e['interest'])}원(원리금균등). 원금균등·만기일시 비교와 연도별 잔액.", body, faq,
          [("홈", "/"), ("대출 이자", "/loan/"), (amt(a), "/loan/%s/" % aslug(a)), ("연 %s%% %d년" % (rs(rate), y), path)], coupang=(a in (EOK, 2 * EOK, 3 * EOK, 5 * EOK) and rate == 4.0)), "0.6" if rate in (4.0, 5.0) else "0.4")

def page_loan_amt(a):
    path = "/loan/%s/" % aslug(a); ys = years_for(a)
    rows = [['연 %s%%' % rs(r)] + ['<a href="/loan/%s/%s/%d년/">%s원</a>' % (aslug(a), rs(r), y, won(L.equal_payment(a, r, y)["monthly"])) for y in ys] for r in RATES]
    mid = L.equal_payment(a, 4.0, ys[-1])
    body = f"""
<div class="page-head"><h1>{amt(a)} 대출 이자 — 금리·기간별 월 상환액</h1><p>원리금균등 기준 · 연 3~7% · {ys[0]}~{ys[-1]}년</p></div>
<p class="lead"><b>{amt(a)}</b>을 빌릴 때 금리와 기간에 따른 월 상환액입니다. 예를 들어 연 4%로 {ys[-1]}년이면 월 {won(mid['monthly'])}원, 총이자 {won(mid['interest'])}원입니다. 금액을 누르면 원금균등·만기일시 비교와 연도별 잔액을 볼 수 있습니다.</p>
{ad()}
{table(['금리'] + ['%d년' % y for y in ys], rows, tuple(range(1, len(ys) + 1)))}
<p class="note">{LNOTE}</p>
{chips([("대출 이자 전체", "/loan/"), ("DSR 대출 한도", "/dsr/"), ("대출 이자 계산기", "/calculator/")])}
"""
    faq = [(f"{amt(a)} 대출 월 상환액은 얼마인가요?", f"연 4% {ys[-1]}년 원리금균등 기준 월 {won(mid['monthly'])}원입니다. 금리·기간에 따라 위 표에서 확인하세요."), ("대출 이자는 어떻게 계산하나요?", "원리금균등은 월 상환액 = 원금×월이율÷(1−(1+월이율)^−개월수)로 계산합니다.")]
    write(path, layout(path, f"{amt(a)} 대출 이자 계산 — 금리·기간별 월 상환액", f"{amt(a)} 대출의 금리 3~7%·기간별 월 상환액 표. 연 4% {ys[-1]}년 월 {won(mid['monthly'])}원. 원리금균등 기준.", body, faq, [("홈", "/"), ("대출 이자", "/loan/"), (amt(a), path)], coupang=a in (EOK, 3 * EOK, 5 * EOK)), "0.8")

def hub_loan():
    rows = [['<a href="/loan/%s/">%s</a>' % (aslug(a), amt(a)), won(L.equal_payment(a, 4.0, years_for(a)[-1])["monthly"]) + "원 (%d년)" % years_for(a)[-1], won(L.equal_payment(a, 5.0, years_for(a)[-1])["monthly"]) + "원 (%d년)" % years_for(a)[-1]] for a in LOAN_AMTS]
    body = f"""
<div class="page-head"><h1>대출 이자 계산 — 금액·금리·기간별 월 상환액 (원리금균등)</h1><p>1천만 원~10억 원 · 연 3~7%</p></div>
<p class="lead">대출 금액, 금리, 기간을 정하면 매월 내는 돈과 총이자를 알 수 있습니다. 금액을 눌러 금리·기간별 표를 확인하고, 직접 입력하려면 <a href="/calculator/">대출 이자 계산기</a>를 이용하세요. 소액 대출은 1~10년, 주택담보 같은 큰 대출은 5~30년으로 정리했습니다.</p>
{ad()}
{table(['대출 금액', '연 4% 월 상환액', '연 5% 월 상환액'], rows, (1, 2))}
<p class="note">{LNOTE}</p>
{chips([("주택담보대출 금리 비교", "/product/mortgage/"), ("신용대출 금리 비교", "/product/credit/"), ("이자 계산 (금액×금리)", "/interest/"), ("월 상환액으로 대출 한도", "/afford/"), ("DSR 대출 한도", "/dsr/"), ("예금 이자", "/deposit/"), ("적금 이자", "/savings/"), ("대출 이자 계산기", "/calculator/")])}
"""
    faq = [("3억 대출 월 상환액은?", f"연 4% 30년 원리금균등 기준 월 {won(L.equal_payment(3 * EOK, 4.0, 30)['monthly'])}원입니다."), ("원금균등과 원리금균등의 차이는?", "원리금균등은 매월 같은 금액을 내고 원금균등은 매월 같은 원금에 줄어드는 이자를 더해 냅니다. 총이자는 원금균등이 적고 초기 부담은 큽니다.")]
    write("/loan/", layout("/loan/", "대출 이자 계산 — 금액·금리·기간별 월 상환액 (원리금균등)", "대출 금액·금리·기간별 월 상환액과 총이자 표. 3억 4% 30년 월 상환액, 원리금균등·원금균등·만기일시 비교.", body, faq, [("홈", "/"), ("대출 이자", "/loan/")], coupang=True), "0.9")

# ───────────────────────── DSR ─────────────────────────
INCOMES = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 7000, 8000, 9000, 10000, 12000, 15000, 20000]
DRATES = [3.5, 4.0, 4.5, 5.0, 6.0]
STRESS = 1.5
def page_dsr(inc):
    income = inc * MAN; path = "/dsr/%s/" % aslug(income)
    base = L.dsr_max(income, 4.0, 30); st = L.dsr_max(income, 4.0 + STRESS, 30); l40 = L.dsr_max(income, 4.0, 40)
    lead = (f"<p class=\"lead\">연소득 <b>{amt(income)}</b>이고 다른 대출이 없다면 DSR 40% 한도로 연 4% 30년 원리금균등 기준 약 <b>{amt2(base)}</b>까지 대출 가능합니다. 스트레스 금리 {STRESS}%p를 더해 심사하면 약 {amt2(st)}, 40년 만기면 약 {amt2(l40)}입니다. 금리가 높을수록, 만기가 짧을수록 한도가 줄어듭니다.</p>")
    rows = [['연 %s%%' % rs(r), amt2(L.dsr_max(income, r, 30)), amt2(L.dsr_max(income, r + STRESS, 30)), amt2(L.dsr_max(income, r, 40)), amt2(L.dsr_max(income, r, 20))] for r in DRATES]
    t = table(["금리", "30년", "30년(스트레스 +%.1f%%p)" % STRESS, "40년", "20년"], rows, (1, 2, 3, 4))
    nb = table(["연소득", "연 4% 30년 한도", "스트레스 반영"], [['<a href="/dsr/%s/">%s</a>' % (aslug(x * MAN), amt(x * MAN)) if x != inc else "<b>%s</b>" % amt(x * MAN), amt2(L.dsr_max(x * MAN, 4.0, 30)), amt2(L.dsr_max(x * MAN, 4.0 + STRESS, 30))] for x in near(INCOMES, inc)], (1, 2))
    body = f"""
<div class="page-head"><h1>연소득 {amt(income)} 대출 한도 — DSR 40% 기준 약 {amt2(base)}</h1><p>금리·만기별 대출 가능 금액 · 스트레스 금리 반영</p></div>
{lead}
{ad()}
{t}
<h2 class="group-title">📈 비슷한 연소득</h2>
{nb}
<h2 class="group-title">📌 알아두기</h2>
<ul class="lead" style="margin-left:20px"><li>DSR(총부채원리금상환비율)은 모든 대출의 연간 원리금 상환액을 연소득으로 나눈 비율이며 은행권은 40%, 비은행권은 50%가 기준입니다.</li><li>스트레스 DSR은 금리 상승 위험을 반영해 심사 금리에 가산금리를 더합니다. 가산금리 수준은 대출 종류·지역·시기에 따라 정책으로 바뀌므로 {STRESS}%p는 예시입니다.</li><li>기존 대출(신용대출·카드론·자동차 할부 등)의 원리금은 소득에서 먼저 차감되므로 실제 한도는 더 낮을 수 있습니다. 주택담보대출은 LTV·DTI 규제와 대출 규제 지역별 한도도 함께 적용됩니다.</li></ul>
{chips([("DSR 전체 표", "/dsr/"), ("대출 이자 계산", "/loan/"), ("우아연봉 실수령액", "https://wooayeonbong.wooahouse.com/salary/")])}
"""
    faq = [(f"연소득 {amt(income)}이면 대출은 얼마까지 가능한가요?", f"DSR 40%, 연 4% 30년 원리금균등 기준 약 {amt2(base)}입니다(다른 대출 없음, 스트레스 금리 미반영). 스트레스 금리를 더하면 약 {amt2(st)}입니다."), ("DSR이 뭔가요?", "연소득 대비 모든 대출의 연간 원리금 상환액 비율입니다. 은행권은 40%를 넘기 어렵습니다."), ("만기를 늘리면 한도가 늘어나나요?", f"네. 같은 소득이라도 40년 만기면 30년보다 한도가 커집니다(연 4% 기준 약 {amt2(l40)}).")]
    write(path, layout(path, f"연소득 {amt(income)} 대출 한도 — DSR 40% 약 {amt2(base)}", f"연소득 {amt(income)}의 DSR 40% 대출 가능 금액. 연 4% 30년 약 {amt2(base)}, 스트레스 금리 {STRESS}%p 반영 {amt2(st)}, 금리·만기별 표.", body, faq, [("홈", "/"), ("DSR 한도", "/dsr/"), (amt(income), path)], coupang=inc in (3000, 5000, 7000)), "0.7")

def hub_dsr():
    rows = [['<a href="/dsr/%s/">%s</a>' % (aslug(x * MAN), amt(x * MAN)), amt2(L.dsr_max(x * MAN, 4.0, 30)), amt2(L.dsr_max(x * MAN, 4.0 + STRESS, 30)), amt2(L.dsr_max(x * MAN, 4.0, 40))] for x in INCOMES]
    body = f"""
<div class="page-head"><h1>DSR 대출 한도 계산 — 연소득별 대출 가능 금액</h1><p>DSR 40% · 연 4% · 원리금균등</p></div>
<p class="lead">DSR 40% 규제에서 연소득별로 대출받을 수 있는 금액입니다. 다른 대출이 없다고 가정하며 스트레스 금리 {STRESS}%p를 더한 한도와 만기 40년 한도를 함께 비교했습니다. 연소득을 눌러 금리·만기별 표를 확인하세요.</p>
{ad()}
{table(['연소득', '30년 한도', '스트레스 반영', '40년 한도'], rows, (1, 2, 3))}
{chips([("월 상환액으로 대출 한도", "/afford/"), ("대출 이자 계산", "/loan/"), ("이자 계산", "/interest/"), ("대출 계산기", "/calculator/")])}
"""
    faq = [("연소득 5천만 원이면 주택담보대출은 얼마까지?", f"DSR 40%, 연 4% 30년 기준 약 {amt2(L.dsr_max(5000 * MAN, 4.0, 30))}입니다(다른 대출 없음)."), ("스트레스 DSR이란?", "대출 금리에 가산금리를 더해 금리 상승기에도 상환 가능한지 보는 심사 방식으로 한도가 줄어듭니다.")]
    write("/dsr/", layout("/dsr/", "DSR 대출 한도 계산 — 연소득별 대출 가능 금액 (40%)", "연소득 2천만~2억 원별 DSR 40% 대출 한도. 연 4% 30년·스트레스 금리 반영·40년 만기 비교.", body, faq, [("홈", "/"), ("DSR 한도", "/dsr/")], coupang=True), "0.9")

# ───────────────────────── 예금·적금 ─────────────────────────
DEP_AMTS = [100 * MAN, 300 * MAN, 500 * MAN, 1000 * MAN, 3000 * MAN, 5000 * MAN, EOK, 2 * EOK, 3 * EOK, 5 * EOK]
DEP_RATES = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
DEP_MONTHS = [6, 12, 24, 36]
DNOTE = "이자소득세 15.4%(소득세 14% + 지방소득세 1.4%)를 뗀 세후 이자이며 단리 정기예금 기준입니다. 비과세·세금우대 상품과 복리 상품은 반영하지 않았습니다. 이자소득이 연 2,000만 원을 넘으면 금융소득종합과세 대상입니다."

def page_dep(a):
    path = "/deposit/%s/" % aslug(a)
    d = L.deposit(a, 3.5, 12)
    rows = [['연 %s%%' % rs(r)] + ['<a href="%s">%s원</a>' % (dpath(a, r, m), won(L.deposit(a, r, m)["net"])) for m in DEP_MONTHS] for r in DEP_RATES]
    t = table(["금리"] + ["%d개월" % m for m in DEP_MONTHS], rows, (1, 2, 3, 4))
    nb = table(["예치 금액", "연 3.5% 1년 세후 이자", "연 4% 1년 세후 이자"], [['<a href="/deposit/%s/">%s</a>' % (aslug(x), amt(x)) if x != a else "<b>%s</b>" % amt(x), won(L.deposit(x, 3.5)["net"]) + "원", won(L.deposit(x, 4.0)["net"]) + "원"] for x in near(DEP_AMTS, a)], (1, 2))
    body = f"""
<div class="page-head"><h1>예금 이자 {amt(a)} — 연 3.5% 1년 세후 {won(d['net'])}원</h1><p>정기예금 금리·기간별 세후 이자 (이자소득세 15.4%)</p></div>
<p class="lead"><b>{amt(a)}</b>을 연 3.5% 정기예금에 1년 맡기면 세전 이자 {won(d['gross'])}원에서 이자소득세 {won(d['tax'])}원을 뗀 <b>세후 {won(d['net'])}원</b>을 받습니다. 금리 2.5~5%, 6~36개월별 세후 이자는 아래 표와 같습니다.</p>
{ad()}
{t}
<h2 class="group-title">📈 다른 금액</h2>
{nb}
<p class="note">{DNOTE}</p>
{chips([("예금 이자 전체", "/deposit/"), ("적금 이자", "/savings/"), ("목표 금액 모으기", "/goal/"), ("예금 계산기", "/calculator/")])}
"""
    faq = [(f"{amt(a)} 예금 이자는 얼마인가요?", f"연 3.5% 1년 기준 세후 {won(d['net'])}원입니다(세전 {won(d['gross'])}원, 이자소득세 15.4%)."), ("예금 이자에 세금이 붙나요?", "일반 과세 시 이자소득세 14%와 지방소득세 1.4%를 합친 15.4%가 원천징수됩니다.")]
    write(path, layout(path, f"예금 이자 {amt(a)} — 연 3.5% 1년 세후 {won(d['net'])}원", f"{amt(a)} 정기예금 이자. 금리 2.5~5%·6~36개월별 세후 이자 표(이자소득세 15.4%). 연 3.5% 1년 세후 {won(d['net'])}원.", body, faq, [("홈", "/"), ("예금 이자", "/deposit/"), (amt(a), path)], coupang=a in (1000 * MAN, EOK)), "0.6")

def hub_dep():
    rows = [['<a href="/deposit/%s/">%s</a>' % (aslug(a), amt(a)), won(L.deposit(a, 3.5)["net"]) + "원", won(L.deposit(a, 4.0)["net"]) + "원"] for a in DEP_AMTS]
    body = f"""
<div class="page-head"><h1>예금 이자 계산 — 예치 금액별 세후 이자표</h1><p>정기예금 1년 · 이자소득세 15.4%</p></div>
<p class="lead">정기예금 이자는 예치 금액 × 금리 × 기간에서 이자소득세 15.4%를 뺀 금액입니다. 금액을 눌러 금리·기간별 세후 이자를 확인하세요.</p>
<div class="tool-box"><div class="tool-row"><div><label for="e-p">예치 금액(원)</label><input id="e-p" type="number" value="10000000" style="width:150px"></div><div><label for="e-r">연 금리(%)</label><input id="e-r" type="number" step="0.1" value="3.5" style="width:80px"></div><div><label for="e-m">기간(개월)</label><input id="e-m" type="number" value="12" style="width:70px"></div><button class="btn-p" id="e-go">계산</button></div><div class="tool-out" id="e-out">계산 결과가 여기에 표시됩니다.</div></div>
{ad()}
{table(['예치 금액', '연 3.5% 세후 이자', '연 4% 세후 이자'], rows, (1, 2))}
<p class="note">{DNOTE}</p>
{chips([("예금 금리 순위", "/rank/deposit/12/"), ("정기예금 금리 비교", "/product/deposit/"), ("적금 이자", "/savings/"), ("목표 금액 모으기", "/goal/"), ("이자 계산", "/interest/"), ("대출 이자", "/loan/")])}
<script src="/assets/js/loan.js"></script>
"""
    faq = [("1천만 원 예금 1년 이자는?", f"연 3.5% 기준 세후 {won(L.deposit(1000 * MAN, 3.5)['net'])}원입니다."), ("이자소득세율은?", "일반 과세 15.4%(소득세 14% + 지방소득세 1.4%)입니다.")]
    write("/deposit/", layout("/deposit/", "예금 이자 계산 — 예치 금액별 세후 이자표 (정기예금)", "정기예금 이자 계산기와 금액별 세후 이자표. 이자소득세 15.4% 반영, 금리·기간별 비교.", body, faq, [("홈", "/"), ("예금 이자", "/deposit/")], coupang=True), "0.9")

SAV_AMTS = [10 * MAN, 20 * MAN, 30 * MAN, 50 * MAN, 70 * MAN, 100 * MAN, 150 * MAN, 200 * MAN, 300 * MAN]
SAV_RATES = [3.0, 3.5, 4.0, 4.5, 5.0, 6.0]
SAV_MONTHS = [12, 24, 36]
def page_sav(a):
    path = "/savings/%s/" % aslug(a)
    d = L.savings(a, 4.0, 12)
    rows = [['연 %s%%' % rs(r)] + [won(L.savings(a, r, m)["total"]) + "원 (이자 %s)" % won(L.savings(a, r, m)["net"]) for m in SAV_MONTHS] for r in SAV_RATES]
    t = table(["금리"] + ["%d개월 만기 수령액" % m for m in SAV_MONTHS], rows, (1, 2, 3))
    nb = table(["월 납입액", "연 4% 12개월 수령액", "연 4% 24개월 수령액"], [['<a href="/savings/%s/">%s</a>' % (aslug(x), amt(x)) if x != a else "<b>%s</b>" % amt(x), won(L.savings(x, 4.0, 12)["total"]) + "원", won(L.savings(x, 4.0, 24)["total"]) + "원"] for x in near(SAV_AMTS, a)], (1, 2))
    body = f"""
<div class="page-head"><h1>적금 이자 월 {amt(a)} — 연 4% 12개월 만기 {won(d['total'])}원</h1><p>정기적금 금리·기간별 만기 수령액 (이자소득세 15.4%)</p></div>
<p class="lead">매월 <b>{amt(a)}</b>씩 연 4% 적금에 12개월 넣으면 원금 {won(d['principal'])}원에 세후 이자 {won(d['net'])}원이 붙어 만기에 <b>{won(d['total'])}원</b>을 받습니다. 적금은 매달 넣는 돈마다 예치 기간이 달라 같은 금리의 예금보다 이자가 약 절반입니다.</p>
{ad()}
{t}
<h2 class="group-title">📈 다른 납입액</h2>
{nb}
<p class="note">매월 초 납입하는 단리 정기적금 기준이며 이자소득세 15.4%를 뗀 세후 금액입니다. 우대금리·비과세·복리 상품은 반영하지 않았습니다. 이자는 월 납입액 × 월이율 × n(n+1)/2로 계산합니다.</p>
{chips([("적금 이자 전체", "/savings/"), ("목표 금액 모으기", "/goal/"), ("예금 이자", "/deposit/"), ("적금 계산기", "/calculator/")])}
"""
    faq = [(f"월 {amt(a)} 적금 이자는?", f"연 4% 12개월 기준 세후 이자 {won(d['net'])}원, 만기 수령액 {won(d['total'])}원입니다."), ("적금 이자가 예금보다 적은 이유는?", "매월 나눠 넣어 평균 예치 기간이 짧기 때문입니다. 12개월 적금의 평균 예치 기간은 약 6.5개월입니다.")]
    write(path, layout(path, f"적금 이자 월 {amt(a)} — 연 4% 12개월 만기 {won(d['total'])}원", f"월 {amt(a)} 정기적금 만기 수령액. 연 4% 12개월 {won(d['total'])}원(세후 이자 {won(d['net'])}원), 금리·기간별 표.", body, faq, [("홈", "/"), ("적금 이자", "/savings/"), (amt(a), path)], coupang=a in (30 * MAN, 50 * MAN)), "0.6")

def hub_sav():
    rows = [['<a href="/savings/%s/">%s</a>' % (aslug(a), amt(a)), won(L.savings(a, 4.0, 12)["total"]) + "원", won(L.savings(a, 4.0, 12)["net"]) + "원"] for a in SAV_AMTS]
    body = f"""
<div class="page-head"><h1>적금 이자 계산 — 월 납입액별 만기 수령액</h1><p>정기적금 연 4% 12개월 · 이자소득세 15.4%</p></div>
<p class="lead">매월 일정 금액을 넣는 적금의 만기 수령액입니다. 월 납입액을 눌러 금리·기간별 표를 확인하세요. 같은 금리라도 적금은 예금보다 이자가 적게 붙습니다.</p>
<div class="tool-box"><div class="tool-row"><div><label for="s-p">월 납입액(원)</label><input id="s-p" type="number" value="500000" style="width:140px"></div><div><label for="s-r">연 금리(%)</label><input id="s-r" type="number" step="0.1" value="4" style="width:80px"></div><div><label for="s-m">기간(개월)</label><input id="s-m" type="number" value="12" style="width:70px"></div><button class="btn-p" id="s-go">계산</button></div><div class="tool-out" id="s-out">계산 결과가 여기에 표시됩니다.</div></div>
{ad()}
{table(['월 납입액', '연 4% 12개월 만기 수령액', '세후 이자'], rows, (1, 2))}
{chips([("적금 금리 순위", "/rank/saving/12/"), ("적금 금리 비교", "/product/saving/"), ("목표 금액 모으기", "/goal/"), ("예금 이자", "/deposit/"), ("이자 계산", "/interest/"), ("대출 이자", "/loan/")])}
<script src="/assets/js/loan.js"></script>
"""
    faq = [("월 50만 원 적금 1년이면?", f"연 4% 기준 만기 수령액 약 {won(L.savings(50 * MAN, 4.0, 12)['total'])}원입니다."), ("적금도 이자소득세를 떼나요?", "일반 과세는 15.4%입니다. 비과세종합저축 등은 제외됩니다.")]
    write("/savings/", layout("/savings/", "적금 이자 계산 — 월 납입액별 만기 수령액 (정기적금)", "정기적금 이자 계산기와 월 납입액별 만기 수령액. 연 4% 12개월, 이자소득세 15.4% 반영.", body, faq, [("홈", "/"), ("적금 이자", "/savings/")], coupang=True), "0.9")

# ───────────────────────── 이자 (금액×금리) ─────────────────────────
def kor(n):
    """원 → '41만 6,667원', '1,200만원', '1억 2,000만원'"""
    n = int(round(n)); eok, rest = divmod(n, EOK); mn, w = divmod(rest, MAN); p = []
    if eok: p.append("%d억" % eok)
    if mn: p.append("{:,}만".format(mn))
    if w: p.append("{:,}".format(w))
    return (" ".join(p) or "0") + "원"

INT_AMTS = [500 * MAN, 1000 * MAN, 2000 * MAN, 3000 * MAN, 4000 * MAN, 5000 * MAN, 6000 * MAN, 7000 * MAN, 8000 * MAN, 9000 * MAN,
            EOK, 15000 * MAN, 2 * EOK, 25000 * MAN, 3 * EOK, 4 * EOK, 5 * EOK, 7 * EOK, 10 * EOK, 20 * EOK]
INT_RATES = [x / 2 for x in range(2, 21)]          # 1.0 ~ 10.0 (0.5 단위)
INT_SHARE_INC = [3000, 5000, 7000, 10000]           # 이자 부담 비교용 연소득(만원)
INOTE = "대출 이자는 이자만 내는 만기일시 기준이며 원금 상환분은 포함하지 않았습니다. 예금 세후 이자는 단리 정기예금에 이자소득세 15.4%를 적용한 값입니다. 실제 이자는 금융기관의 일수 계산·우대금리·세금 혜택에 따라 달라집니다."

def ipath(a, r=None): return "/interest/%s/" % aslug(a) if r is None else "/interest/%s/%s/" % (aslug(a), rs(r))

def page_int(a, r):
    path = ipath(a, r)
    yr = L.rnd(a * r / 100.0); mo = L.rnd(a * r / 1200.0); dy = L.rnd(a * r / 100.0 / 365)
    net = L.deposit(a, r, 12)["net"]; net_m = L.rnd(net / 12.0)
    ys = years_for(a); y_mid = ys[-1]; e = L.equal_payment(a, r, y_mid)
    lead = (f"<p class=\"lead\"><b>{amt(a)}</b>에 연 <b>{rs(r)}%</b> 이자가 붙으면 1년 이자는 <b>{won(yr)}원</b>, 한 달 이자는 <b>{won(mo)}원</b>, 하루 이자는 약 {won(dy)}원입니다. "
            f"대출이라면 이자만 내는 동안 매월 {won(mo)}원을 내고, 정기예금이라면 이자소득세 15.4%를 떼고 1년에 {won(net)}원(월 약 {won(net_m)}원)을 받습니다. "
            f"원금까지 나눠 갚는 원리금균등으로 {y_mid}년 동안 갚는다면 월 {won(e['monthly'])}원이 듭니다.</p>")
    t1 = table(["구분", "1년", "한 달", "하루"], [
        ["대출 이자 (이자만 낼 때)", kor(yr), kor(mo), kor(dy)],
        ["예금 이자 (세전)", kor(yr), kor(mo), kor(dy)],
        ["예금 이자 (세후 15.4%)", kor(net), kor(net_m), kor(L.rnd(net / 365.0))]], (1, 2, 3))
    t2 = table(["금리", "1년 이자", "한 달 이자", "예금 세후 1년"], [
        [('<a href="%s">연 %s%%</a>' % (ipath(a, x), rs(x))) if x != r else "<b>연 %s%%</b>" % rs(x), kor(a * x / 100.0), kor(a * x / 1200.0), kor(L.deposit(a, x, 12)["net"])] for x in near(INT_RATES, r)], (1, 2, 3))
    t3 = table(["금액", "1년 이자", "한 달 이자", "예금 세후 1년"], [
        [('<a href="%s">%s</a>' % (ipath(x, r), amt(x))) if x != a else "<b>%s</b>" % amt(x), kor(x * r / 100.0), kor(x * r / 1200.0), kor(L.deposit(x, r, 12)["net"])] for x in near(INT_AMTS, a)], (1, 2, 3))
    t4 = table(["갚는 기간", "월 상환액(원리금균등)", "총 이자"], [["%d년" % y, kor(L.equal_payment(a, r, y)["monthly"]), kor(L.equal_payment(a, r, y)["interest"])] for y in ys], (1, 2))
    t5 = table(["연소득", "연 이자가 차지하는 비중"], [[amt(i * MAN), pct(yr / (i * MAN) * 100, 1)] for i in INT_SHARE_INC], (1,))
    chips_ = [(f"{amt(a)} 이자 금리별 표", ipath(a)), ("이자 전체표", "/interest/")]
    if a in LOAN_AMTS and r in RATES: chips_.insert(1, (f"{amt(a)} 연 {rs(r)}% {y_mid}년 상환", "/loan/%s/%s/%d년/" % (aslug(a), rs(r), y_mid)))
    if a in DEP_AMTS and r in DEP_RATES: chips_.insert(1, (f"예금 {amt(a)} 연 {rs(r)}% 12개월", dpath(a, r, 12)))
    chips_ += [("대출 이자 계산기", "/calculator/")]
    body = f"""
<div class="page-head"><h1>{amt(a)} {rs(r)}% 이자 — 연 {kor(yr)}, 월 {kor(mo)}</h1><p>대출·예금 이자를 한 번에 · 1년·한 달·하루 이자</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>1년 이자</small><b>{kor(yr)}</b></div><div class="stat"><small>한 달 이자</small><b>{kor(mo)}</b></div><div class="stat"><small>예금 세후 1년</small><b>{kor(net)}</b></div></div>
{ad()}
<h2 class="group-title">💳 대출과 예금, 이자는 이렇게 달라요</h2>
{t1}
<h2 class="group-title">📈 금리가 다르면</h2>
{t2}
<h2 class="group-title">💰 금액이 다르면</h2>
{t3}
<h2 class="group-title">⏳ 원금까지 갚는다면</h2>
{t4}
<h2 class="group-title">📊 내 소득 대비 이자 부담</h2>
{t5}
<p class="note">{INOTE}</p>
{chips(chips_)}
"""
    faq = [(f"{amt(a)} {rs(r)}% 이자는 한 달에 얼마인가요?", f"한 달 이자는 {won(mo)}원, 1년 이자는 {won(yr)}원입니다(이자만 낼 때)."),
           (f"{amt(a)} {rs(r)}% 예금 이자는 세금 떼고 얼마인가요?", f"이자소득세 15.4%를 떼면 1년에 {won(net)}원(월 약 {won(net_m)}원)입니다."),
           (f"{amt(a)}을(를) {rs(r)}%로 {y_mid}년 갚으면 월 얼마인가요?", f"원리금균등 기준 월 {won(e['monthly'])}원이고 총이자는 {won(e['interest'])}원입니다.")]
    write(path, layout(path, f"{amt(a)} {rs(r)}% 이자 — 연 {kor(yr)}, 월 {kor(mo)}", f"{amt(a)} {rs(r)}% 이자는 1년 {kor(yr)}, 한 달 {kor(mo)}. 대출 이자와 예금 세후 이자({kor(net)}), {y_mid}년 상환 시 월 상환액까지 한 번에 확인.",
          body, faq, [("홈", "/"), ("이자 계산", "/interest/"), (amt(a), ipath(a)), ("연 %s%%" % rs(r), path)], coupang=(a in (EOK, 3 * EOK, 5 * EOK) and r in (4.0, 5.0))), "0.7" if r in (3.0, 4.0, 5.0) else "0.5")

def page_int_amt(a):
    path = ipath(a)
    rows = [['<a href="%s">연 %s%%</a>' % (ipath(a, x), rs(x)), kor(a * x / 100.0), kor(a * x / 1200.0), kor(L.deposit(a, x, 12)["net"])] for x in INT_RATES]
    y4, m4 = L.rnd(a * 4 / 100.0), L.rnd(a * 4 / 1200.0)
    body = f"""
<div class="page-head"><h1>{amt(a)} 이자 — 금리별 1년·한 달 이자</h1><p>연 1~10% · 대출 이자와 예금 세후 이자</p></div>
<p class="lead"><b>{amt(a)}</b>의 금리별 이자입니다. 예를 들어 연 4%면 1년 이자 {won(y4)}원, 한 달 이자 {won(m4)}원입니다. 금리를 누르면 상환 기간별 월 상환액과 소득 대비 이자 부담까지 볼 수 있습니다.</p>
{ad()}
{table(['금리', '1년 이자', '한 달 이자', '예금 세후 1년'], rows, (1, 2, 3))}
<p class="note">{INOTE}</p>
{chips([("이자 전체표", "/interest/"), ("대출 이자 계산", "/loan/"), ("예금 이자", "/deposit/"), ("계산기", "/calculator/")])}
"""
    faq = [(f"{amt(a)} 이자는 얼마인가요?", f"연 4% 기준 1년 {won(y4)}원, 한 달 {won(m4)}원입니다. 금리별 값은 위 표를 확인하세요."), ("이자는 어떻게 계산하나요?", "1년 이자 = 금액 × 연 금리, 한 달 이자 = 금액 × 연 금리 ÷ 12입니다.")]
    write(path, layout(path, f"{amt(a)} 이자 계산 — 금리별 1년·한 달 이자", f"{amt(a)}의 연 1~10% 금리별 1년·한 달 이자표. 연 4%면 1년 {kor(y4)}, 대출 이자와 예금 세후 이자 비교.", body, faq,
          [("홈", "/"), ("이자 계산", "/interest/"), (amt(a), path)]), "0.8")

def hub_int():
    cols = [3.0, 4.0, 5.0, 6.0]
    rows = [['<a href="%s">%s</a>' % (ipath(a), amt(a))] + ['<a href="%s">월 %s</a>' % (ipath(a, x), kor(a * x / 1200.0)) for x in cols] for a in INT_AMTS]
    body = f"""
<div class="page-head"><h1>이자 계산 — 금액·금리별 1년·한 달 이자</h1><p>예: 3억 4% 이자, 1억 5% 이자</p></div>
<p class="lead">금액과 금리만 알면 이자는 간단히 구할 수 있습니다. 1년 이자는 금액 × 연 금리, 한 달 이자는 그 값을 12로 나눈 값입니다. 아래에서 금액을 누르면 금리별 이자표, 칸을 누르면 그 금액·금리의 상세 계산(대출 이자와 예금 세후 이자, 상환 기간별 월 상환액)이 나옵니다.</p>
{ad()}
{table(['금액'] + ['연 %s%% 월 이자' % rs(x) for x in cols], rows, tuple(range(1, len(cols) + 1)))}
<p class="note">{INOTE}</p>
{chips([("대출 이자 계산", "/loan/"), ("월 상환액으로 대출 한도", "/afford/"), ("예금 이자", "/deposit/"), ("계산기", "/calculator/")])}
"""
    faq = [("3억 4% 이자는 얼마인가요?", f"1년 {won(3 * EOK * 4 / 100)}원, 한 달 {won(3 * EOK * 4 / 1200)}원입니다."), ("1억 5% 이자는 한 달에 얼마인가요?", f"한 달 약 {won(L.rnd(EOK * 5 / 1200.0))}원입니다(1년 {won(EOK * 5 / 100)}원).")]
    write("/interest/", layout("/interest/", "이자 계산 — 금액·금리별 1년·한 달 이자표 (3억 4%, 1억 5%)", "금액과 금리별 이자표. 3억 4% 이자, 1억 5% 이자 등 1년·한 달·하루 이자와 예금 세후 이자를 한눈에 확인.", body, faq, [("홈", "/"), ("이자 계산", "/interest/")], coupang=True), "0.9")

# ───────────────────────── 월 상환액 → 대출 한도 ─────────────────────────
AFF_PAY = [30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 200, 250, 300, 400, 500]   # 만원
AFF_YEARS = [5, 10, 20, 30, 40]
def apath(p, r=None, y=None):
    s = "/afford/%s/" % aslug(p * MAN)
    return s if r is None else s + "%s/%d년/" % (rs(r), y)
def nearest_inc(income_man):
    b = min(INCOMES, key=lambda x: abs(x - income_man))
    return b if abs(b - income_man) / income_man <= 0.35 else None

def page_aff(p, r, y):
    M = p * MAN; P = L.loan_from_payment(M, r, y); e = L.equal_payment(P, r, y)
    need = M * 12 / 0.40; P_st = L.loan_from_payment(M, r + STRESS, y)
    lead = (f"<p class=\"lead\">매월 <b>{amt(M)}</b>을 갚을 수 있다면 연 <b>{rs(r)}%</b>, <b>{y}년</b> 원리금균등 기준 최대 약 <b>{amt2(P)}</b>까지 대출받을 수 있습니다. "
            f"이때 총이자는 약 {amt2(e['interest'])}이고 총 상환액은 약 {amt2(e['total'])}입니다. 이 대출의 연 원리금 {amt2(M * 12)}을 DSR 40%로 보면 연소득이 약 {amt2(need)} 이상이어야 하며, "
            f"스트레스 금리 {STRESS}%p를 더해 심사받으면 한도가 약 {amt2(P_st)}으로 줄어듭니다.</p>")
    t1 = table(["금리", "대출 가능 금액", "총 이자"], [[('<a href="%s">연 %s%%</a>' % (apath(p, x, y), rs(x))) if x != r else "<b>연 %s%%</b>" % rs(x),
              amt2(L.loan_from_payment(M, x, y)), amt2(L.equal_payment(L.loan_from_payment(M, x, y), x, y)["interest"])] for x in near(RATES, r)], (1, 2))
    t2 = table(["대출 기간", "대출 가능 금액", "총 이자"], [[('<a href="%s">%d년</a>' % (apath(p, r, x), x)) if x != y else "<b>%d년</b>" % x,
              amt2(L.loan_from_payment(M, r, x)), amt2(L.equal_payment(L.loan_from_payment(M, r, x), r, x)["interest"])] for x in AFF_YEARS], (1, 2))
    t3 = table(["월 상환액", "대출 가능 금액"], [[('<a href="%s">%s</a>' % (apath(x, r, y), amt(x * MAN))) if x != p else "<b>%s</b>" % amt(x * MAN), amt2(L.loan_from_payment(x * MAN, r, y))] for x in near(AFF_PAY, p)], (1,))
    chips_ = [(f"월 {amt(M)} 대출 한도 전체표", apath(p)), ("월 상환액별 한도", "/afford/")]
    inc = nearest_inc(need / MAN)
    if inc: chips_.append((f"연소득 {amt(inc * MAN)} DSR 한도", "/dsr/%s/" % aslug(inc * MAN)))
    chips_.append(("대출 이자 계산기", "/calculator/"))
    body = f"""
<div class="page-head"><h1>월 {amt(M)} 갚으면 대출 얼마? — 연 {rs(r)}% {y}년 약 {amt2(P)}</h1><p>월 상환액으로 거꾸로 구하는 대출 한도 (원리금균등)</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>대출 가능 금액</small><b>{amt2(P)}</b></div><div class="stat"><small>총 이자</small><b>{amt2(e['interest'])}</b></div><div class="stat"><small>필요 연소득(DSR 40%)</small><b>{amt2(need)}</b></div></div>
{ad()}
<h2 class="group-title">📈 금리가 다르면</h2>
{t1}
<h2 class="group-title">⏳ 기간이 다르면</h2>
{t2}
<h2 class="group-title">💰 월 상환액이 다르면</h2>
{t3}
<h2 class="group-title">📌 알아두기</h2>
<ul class="lead" style="margin-left:20px"><li>월 상환액 × 월이율 공식을 거꾸로 푼 값으로, 대출액 = 월 상환액 × (1 − (1+월이율)^−개월수) ÷ 월이율 입니다.</li><li>실제 한도는 소득·기존 대출·담보(LTV)와 DSR 심사로 정해지므로 위 금액보다 낮을 수 있습니다. 금리는 변동될 수 있습니다.</li><li>{LNOTE}</li></ul>
{chips(chips_)}
"""
    faq = [(f"월 {amt(M)} 갚으면 대출은 얼마까지 가능한가요?", f"연 {rs(r)}% {y}년 원리금균등 기준 약 {amt2(P)}입니다."), ("월 상환액으로 대출 한도를 어떻게 계산하나요?", "월 상환액 × (1 − (1+월이율)^−개월수) ÷ 월이율로 계산합니다. 금리가 낮고 기간이 길수록 한도가 커집니다."),
           (f"월 {amt(M)}이면 연소득이 얼마나 필요한가요?", f"DSR 40% 기준으로 연 원리금 {amt2(M * 12)}을 40%로 나눈 약 {amt2(need)} 이상이 필요합니다(다른 대출 없음).")]
    write(apath(p, r, y), layout(apath(p, r, y), f"월 {amt(M)} 갚으면 대출 얼마? 연 {rs(r)}% {y}년 약 {amt2(P)}", f"월 상환액 {amt(M)}으로 연 {rs(r)}% {y}년 원리금균등 대출 가능 금액은 약 {amt2(P)}, 총이자 약 {amt2(e['interest'])}. 필요 연소득과 스트레스 금리 한도까지.",
          body, faq, [("홈", "/"), ("월 상환액별 한도", "/afford/"), (f"월 {amt(M)}", apath(p)), (f"연 {rs(r)}% {y}년", apath(p, r, y))]), "0.5")

def page_aff_amt(p):
    M = p * MAN
    rows = [['연 %s%%' % rs(r)] + ['<a href="%s">%s</a>' % (apath(p, r, y), amt2(L.loan_from_payment(M, r, y))) for y in AFF_YEARS] for r in RATES]
    mid = L.loan_from_payment(M, 4.0, 30)
    body = f"""
<div class="page-head"><h1>월 {amt(M)} 갚으면 대출 얼마 — 금리·기간별 한도</h1><p>월 상환액 기준 대출 가능 금액 · 연 3~7% · 5~40년</p></div>
<p class="lead">매월 <b>{amt(M)}</b>을 갚을 수 있을 때 금리와 기간에 따라 받을 수 있는 대출 금액입니다. 연 4% 30년이면 약 {amt2(mid)}입니다. 칸을 누르면 총이자와 필요 연소득까지 확인할 수 있습니다.</p>
{ad()}
{table(['금리'] + ['%d년' % y for y in AFF_YEARS], rows, tuple(range(1, len(AFF_YEARS) + 1)))}
<p class="note">{LNOTE}</p>
{chips([("월 상환액별 한도", "/afford/"), ("DSR 한도", "/dsr/"), ("대출 이자 계산", "/loan/"), ("계산기", "/calculator/")])}
"""
    faq = [(f"월 {amt(M)} 갚으면 대출은 얼마까지?", f"연 4% 30년 원리금균등 기준 약 {amt2(mid)}입니다."), ("금리가 오르면 한도가 줄어드나요?", "네. 같은 월 상환액이라도 금리가 높을수록 빌릴 수 있는 금액이 줄어듭니다.")]
    write(apath(p), layout(apath(p), f"월 {amt(M)} 갚으면 대출 얼마 — 금리·기간별 대출 한도", f"월 {amt(M)}을 갚을 수 있을 때 금리 3~7%, 5~40년별 대출 가능 금액. 연 4% 30년 약 {amt2(mid)}.", body, faq,
          [("홈", "/"), ("월 상환액별 한도", "/afford/"), (f"월 {amt(M)}", apath(p))]), "0.7")

def hub_aff():
    rows = [['<a href="%s">%s</a>' % (apath(p), amt(p * MAN)), amt2(L.loan_from_payment(p * MAN, 4.0, 30)), amt2(L.loan_from_payment(p * MAN, 5.0, 30)), amt2(L.loan_from_payment(p * MAN, 4.0, 10))] for p in AFF_PAY]
    body = f"""
<div class="page-head"><h1>월 상환액으로 대출 한도 계산 — 월 얼마 갚으면 대출 얼마?</h1><p>월 30만~500만 원 · 원리금균등</p></div>
<p class="lead">매달 갚을 수 있는 금액을 정하면 빌릴 수 있는 대출 금액을 알 수 있습니다. 월 상환액을 누르면 금리·기간별 한도 표가 나오고, 표의 칸을 누르면 총이자와 필요 연소득까지 확인할 수 있습니다. 소득 기준 한도는 <a href="/dsr/">DSR 한도</a>에서 볼 수 있습니다.</p>
{ad()}
{table(['월 상환액', '연 4% 30년', '연 5% 30년', '연 4% 10년'], rows, (1, 2, 3))}
<p class="note">{LNOTE}</p>
{chips([("DSR 대출 한도", "/dsr/"), ("대출 이자 계산", "/loan/"), ("이자 계산", "/interest/"), ("계산기", "/calculator/")])}
"""
    faq = [("월 100만 원 갚으면 대출은 얼마까지 가능한가요?", f"연 4% 30년 원리금균등 기준 약 {amt2(L.loan_from_payment(100 * MAN, 4.0, 30))}입니다."), ("월 상환액으로 대출 한도를 어떻게 구하나요?", "월 상환액 × (1 − (1+월이율)^−개월수) ÷ 월이율로 계산합니다.")]
    write("/afford/", layout("/afford/", "월 상환액으로 대출 한도 계산 — 월 100만원 갚으면 대출 얼마?", f"월 상환액 30만~500만 원별 대출 가능 금액. 월 100만원이면 연 4% 30년 약 {amt2(L.loan_from_payment(100 * MAN, 4.0, 30))}. 금리·기간별 표.", body, faq, [("홈", "/"), ("월 상환액별 한도", "/afford/")], coupang=True), "0.9")

# ───────────────────────── 적금 목표 금액 ─────────────────────────
GOAL_T = [500 * MAN, 1000 * MAN, 2000 * MAN, 3000 * MAN, 5000 * MAN, EOK, 2 * EOK, 3 * EOK]
GOAL_N = [12, 24, 36, 48, 60]
def gpath(g, r=None, n=None):
    s = "/goal/%s/" % aslug(g)
    return s if r is None else s + "%s/%d개월/" % (rs(r), n)
GOAL_SET = {(g, r, n) for g in GOAL_T for r in SAV_RATES for n in GOAL_N if 50000 <= L.goal_monthly(g, r, n) <= 5_000_000}
def glink(g, r, n, text):
    return '<a href="%s">%s</a>' % (gpath(g, r, n), text) if (g, r, n) in GOAL_SET else text

def page_goal(g, r, n):
    m = L.goal_monthly(g, r, n); s = L.savings(m, r, n); dp = L.deposit_principal_for(g, r, n)
    yrs = ("%d년" % (n // 12)) if n % 12 == 0 else "%d개월" % n
    lead = (f"<p class=\"lead\"><b>{amt(g)}</b>을 모으려면 연 <b>{rs(r)}%</b> 정기적금(단리)에 <b>{yrs}</b> 동안 매월 약 <b>{won(m)}원</b>을 넣어야 합니다. "
            f"원금은 {won(s['principal'])}원이고 세후 이자 {won(s['net'])}원이 붙어 만기에 {won(s['total'])}원을 받습니다. "
            f"같은 금리로 한 번에 맡기는 정기예금이라면 약 {amt2(dp)}을 {yrs}간 맡기면 같은 금액이 됩니다.</p>")
    t1 = table(["금리", "월 납입액", "세후 이자", "만기 수령액"], [[glink(g, x, n, "연 %s%%" % rs(x)) if x != r else "<b>연 %s%%</b>" % rs(x), won(L.goal_monthly(g, x, n)) + "원", won(L.savings(L.goal_monthly(g, x, n), x, n)["net"]) + "원", won(L.savings(L.goal_monthly(g, x, n), x, n)["total"]) + "원"] for x in SAV_RATES], (1, 2, 3))
    t2 = table(["기간", "월 납입액", "세후 이자"], [[glink(g, r, k, ("%d개월" % k)) if k != n else "<b>%d개월</b>" % k, won(L.goal_monthly(g, r, k)) + "원", won(L.savings(L.goal_monthly(g, r, k), r, k)["net"]) + "원"] for k in GOAL_N if (g, r, k) in GOAL_SET or k == n], (1, 2))
    t3 = table(["목표 금액", "월 납입액"], [[glink(x, r, n, amt(x)) if x != g else "<b>%s</b>" % amt(x), won(L.goal_monthly(x, r, n)) + "원"] for x in near(GOAL_T, g, 2) if (x, r, n) in GOAL_SET or x == g], (1,))
    near_sav = min(SAV_AMTS, key=lambda x: abs(x - m)); chips_ = [(f"{amt(g)} 모으기 전체표", gpath(g)), ("목표 금액별 적금", "/goal/")]
    if abs(near_sav - m) / m <= 0.35: chips_.append((f"월 {amt(near_sav)} 적금 이자", "/savings/%s/" % aslug(near_sav)))
    chips_.append(("적금 계산기", "/calculator/"))
    body = f"""
<div class="page-head"><h1>{amt(g)} 모으기 적금 — 연 {rs(r)}% {yrs} 월 {won(m)}원</h1><p>목표 금액에서 거꾸로 구하는 월 적금 납입액 (세후)</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>월 납입액</small><b>{won(m)}원</b></div><div class="stat"><small>세후 이자</small><b>{won(s['net'])}원</b></div><div class="stat"><small>만기 수령액</small><b>{won(s['total'])}원</b></div></div>
{ad()}
<h2 class="group-title">📈 금리가 다르면</h2>
{t1}
<h2 class="group-title">⏳ 기간이 다르면</h2>
{t2}
<h2 class="group-title">🎯 목표 금액이 다르면</h2>
{t3}
<p class="note">매월 초 납입하는 단리 정기적금에 이자소득세 15.4%를 적용한 세후 만기 수령액이 목표 금액 이상이 되는 최소 월 납입액(100원 단위 올림)입니다. 우대금리·비과세·복리 상품은 반영하지 않았습니다.</p>
{chips(chips_)}
"""
    faq = [(f"{amt(g)} 모으려면 적금을 매달 얼마 넣어야 하나요?", f"연 {rs(r)}% {yrs} 단리 정기적금 기준 월 약 {won(m)}원입니다(세후)."), ("적금과 예금 중 목표 달성에 어느 쪽이 유리한가요?", f"같은 금리라면 한 번에 맡기는 예금이 이자가 더 붙지만 목돈이 필요합니다. 이 조건의 예금은 약 {amt2(dp)}이 필요합니다."),
           ("금리가 오르면 월 납입액이 얼마나 줄어드나요?", f"연 {rs(SAV_RATES[-1])}%면 월 {won(L.goal_monthly(g, SAV_RATES[-1], n))}원으로 줄어드는 식으로 금리가 높을수록 부담이 줄지만 차이는 크지 않습니다.")]
    write(gpath(g, r, n), layout(gpath(g, r, n), f"{amt(g)} 모으기 적금 연 {rs(r)}% {yrs} — 월 {won(m)}원", f"{amt(g)}을 모으려면 연 {rs(r)}% 적금 {yrs} 동안 월 약 {won(m)}원. 세후 이자 {won(s['net'])}원, 만기 수령액 {won(s['total'])}원.",
          body, faq, [("홈", "/"), ("적금 목표", "/goal/"), (amt(g), gpath(g)), (f"연 {rs(r)}% {yrs}", gpath(g, r, n))]), "0.5")

def page_goal_amt(g):
    rows = [['연 %s%%' % rs(r)] + [glink(g, r, n, won(L.goal_monthly(g, r, n)) + "원") if (g, r, n) in GOAL_SET else "—" for n in GOAL_N] for r in SAV_RATES]
    ns = [n for n in GOAL_N if (g, 4.0, n) in GOAL_SET]; n0 = ns[0] if ns else GOAL_N[-1]
    body = f"""
<div class="page-head"><h1>{amt(g)} 모으기 — 월 적금 납입액 (금리·기간별)</h1><p>정기적금 단리 · 이자소득세 15.4% 반영 세후</p></div>
<p class="lead"><b>{amt(g)}</b>을 적금으로 모으려면 매월 얼마를 넣어야 하는지 금리와 기간별로 정리했습니다. 연 4% {n0}개월이면 월 약 {won(L.goal_monthly(g, 4.0, n0))}원입니다. 칸을 누르면 세후 이자와 예금으로 모을 때의 필요 원금을 볼 수 있습니다. 월 부담이 너무 큰 조합(월 500만 원 초과)이나 너무 작은 조합(월 5만 원 미만)은 표시하지 않았습니다.</p>
{ad()}
{table(['금리'] + ['%d개월' % n for n in GOAL_N], rows, tuple(range(1, len(GOAL_N) + 1)))}
{chips([("목표 금액별 적금", "/goal/"), ("적금 이자", "/savings/"), ("예금 이자", "/deposit/"), ("계산기", "/calculator/")])}
"""
    faq = [(f"{amt(g)} 모으려면 월 얼마씩 저축해야 하나요?", f"연 4% {n0}개월 적금 기준 월 약 {won(L.goal_monthly(g, 4.0, n0))}원입니다."), ("이자를 포함해 계산한 건가요?", "네. 세후 만기 수령액이 목표 금액 이상이 되도록 이자소득세 15.4%를 뗀 이자를 포함해 계산했습니다.")]
    write(gpath(g), layout(gpath(g), f"{amt(g)} 모으기 적금 — 월 납입액 금리·기간별 표", f"{amt(g)}을 모으기 위한 월 적금 납입액을 금리 3~6%, 12~60개월별로 계산. 연 4% {n0}개월 월 약 {won(L.goal_monthly(g, 4.0, n0))}원.", body, faq,
          [("홈", "/"), ("적금 목표", "/goal/"), (amt(g), gpath(g))]), "0.7")

def hub_goal():
    cols = [(24, 4.0), (36, 4.0), (60, 4.0)]
    rows = [['<a href="%s">%s</a>' % (gpath(g), amt(g))] + [glink(g, r, n, "월 " + won(L.goal_monthly(g, r, n)) + "원") if (g, r, n) in GOAL_SET else "—" for n, r in cols] for g in GOAL_T]
    body = f"""
<div class="page-head"><h1>목표 금액 모으기 적금 계산 — 1억 모으려면 월 얼마?</h1><p>목표 금액에서 거꾸로 구하는 월 적금 납입액 (세후)</p></div>
<p class="lead">모으고 싶은 목표 금액을 정하면 적금에 매달 얼마를 넣어야 하는지 알 수 있습니다. 이자소득세 15.4%를 뗀 세후 만기 수령액이 목표 금액이 되도록 계산했습니다. 목표 금액을 누르면 금리·기간별 표가 나옵니다.</p>
{ad()}
{table(['목표 금액', '연 4% 24개월', '연 4% 36개월', '연 4% 60개월'], rows, (1, 2, 3))}
{chips([("적금 이자", "/savings/"), ("예금 이자", "/deposit/"), ("이자 계산", "/interest/"), ("계산기", "/calculator/")])}
"""
    faq = [("1억 모으려면 적금을 월 얼마 넣어야 하나요?", f"연 4% 60개월 단리 적금 기준 월 약 {won(L.goal_monthly(EOK, 4.0, 60))}원입니다(세후)."), ("적금 5년은 이자가 얼마나 붙나요?", "월 납입액 × 월이율 × n(n+1)/2로 계산한 단리 이자에 15.4%를 뗍니다. 기간이 길수록 이자 비중이 커집니다.")]
    write("/goal/", layout("/goal/", "목표 금액 모으기 적금 계산 — 1억 모으려면 월 얼마?", f"500만~3억 원 목표별 월 적금 납입액. 1억을 연 4% 60개월 적금으로 모으려면 월 약 {won(L.goal_monthly(EOK, 4.0, 60))}원.", body, faq, [("홈", "/"), ("적금 목표", "/goal/")], coupang=True), "0.9")

# ───────────────────────── 예금 금액×금리×기간 ─────────────────────────
def dpath(a, r, m): return "/deposit/%s/%s/%d개월/" % (aslug(a), rs(r), m)

def page_dep_combo(a, r, m):
    d = L.deposit(a, r, m); total = a + d["net"]; mo_net = L.rnd(d["net"] / m)
    x = L.rnd(a / float(m)); s = L.savings(x, r, m); ratio = s["net"] / d["net"] * 100 if d["net"] else 0
    ann = d["net"] / a * 12.0 / m * 100
    lead = (f"<p class=\"lead\"><b>{amt(a)}</b>을 연 <b>{rs(r)}%</b> 정기예금에 <b>{m}개월</b> 맡기면 세전 이자 {won(d['gross'])}원에서 이자소득세 {won(d['tax'])}원을 뗀 <b>세후 {won(d['net'])}원</b>을 받고, 만기 수령액은 {won(total)}원입니다. "
            f"월평균 이자는 약 {won(mo_net)}원이며 세후 연 수익률은 {pct(ann)}입니다. 같은 돈을 매달 {won(x)}원씩 적금으로 나눠 넣으면 세후 이자는 {won(s['net'])}원으로 예금의 {pct(ratio, 0)} 수준입니다.</p>")
    t1 = table(["금리", "세후 이자", "만기 수령액"], [[('<a href="%s">연 %s%%</a>' % (dpath(a, x, m), rs(x))) if x != r else "<b>연 %s%%</b>" % rs(x), won(L.deposit(a, x, m)["net"]) + "원", won(a + L.deposit(a, x, m)["net"]) + "원"] for x in DEP_RATES], (1, 2))
    t2 = table(["기간", "세후 이자", "만기 수령액"], [[('<a href="%s">%d개월</a>' % (dpath(a, r, k), k)) if k != m else "<b>%d개월</b>" % k, won(L.deposit(a, r, k)["net"]) + "원", won(a + L.deposit(a, r, k)["net"]) + "원"] for k in DEP_MONTHS], (1, 2))
    t3 = table(["예치 금액", "세후 이자", "만기 수령액"], [[('<a href="%s">%s</a>' % (dpath(x_, r, m), amt(x_))) if x_ != a else "<b>%s</b>" % amt(x_), won(L.deposit(x_, r, m)["net"]) + "원", won(x_ + L.deposit(x_, r, m)["net"]) + "원"] for x_ in near(DEP_AMTS, a, 2)], (1, 2))
    chips_ = [(f"예금 {amt(a)} 금리·기간별 표", "/deposit/%s/" % aslug(a)), ("예금 이자 전체", "/deposit/")]
    if a in INT_AMTS and r in INT_RATES: chips_.append((f"{amt(a)} {rs(r)}% 이자", ipath(a, r)))
    chips_ += [("적금 이자", "/savings/"), ("예금 계산기", "/calculator/")]
    body = f"""
<div class="page-head"><h1>예금 {amt(a)} 연 {rs(r)}% {m}개월 — 세후 이자 {won(d['net'])}원</h1><p>정기예금 세후 이자·만기 수령액 (이자소득세 15.4%)</p></div>
{lead}
<div class="stat-row"><div class="stat"><small>세후 이자</small><b>{won(d['net'])}원</b></div><div class="stat"><small>만기 수령액</small><b>{won(total)}원</b></div><div class="stat"><small>월평균 이자</small><b>{won(mo_net)}원</b></div></div>
{ad()}
<h2 class="group-title">📈 금리가 다르면</h2>
{t1}
<h2 class="group-title">⏳ 기간이 다르면</h2>
{t2}
<h2 class="group-title">💰 예치 금액이 다르면</h2>
{t3}
<p class="note">{DNOTE}</p>
{chips(chips_)}
"""
    faq = [(f"{amt(a)} 연 {rs(r)}% {m}개월 예금 이자는 얼마인가요?", f"세전 {won(d['gross'])}원, 이자소득세 15.4%를 뗀 세후 {won(d['net'])}원입니다."), ("예금 만기 수령액은 얼마인가요?", f"원금 {won(a)}원에 세후 이자를 더한 {won(total)}원입니다."),
           ("같은 금액을 적금으로 나눠 넣으면 이자가 얼마나 줄어드나요?", f"매달 {won(x)}원씩 넣으면 세후 이자가 {won(s['net'])}원으로 예금의 약 {pct(ratio, 0)}입니다. 매월 넣은 돈의 예치 기간이 짧기 때문입니다.")]
    write(dpath(a, r, m), layout(dpath(a, r, m), f"예금 {amt(a)} 연 {rs(r)}% {m}개월 이자 — 세후 {won(d['net'])}원", f"{amt(a)}을 연 {rs(r)}% 정기예금에 {m}개월 맡기면 세후 이자 {won(d['net'])}원, 만기 수령액 {won(total)}원(이자소득세 15.4%).",
          body, faq, [("홈", "/"), ("예금 이자", "/deposit/"), (amt(a), "/deposit/%s/" % aslug(a)), (f"연 {rs(r)}% {m}개월", dpath(a, r, m))]), "0.5")

# ───────────────────────── 계산기·기타 ─────────────────────────
def page_calc():
    body = """
<div class="page-head"><h1>대출·예적금 계산기 — 대출 이자, DSR, 예금, 적금</h1><p>입력한 값은 서버로 전송되지 않습니다</p></div>
<p class="lead">금액은 <b>원 단위</b>로 입력하세요(예: 3억 원 → 300000000). 계산 결과는 참고용 추정입니다.</p>
<div class="tool-box"><h3 style="margin-top:0">🏦 대출 이자</h3>
<div class="tool-row"><div><label for="l-p">대출 금액(원)</label><input id="l-p" type="number" value="300000000" style="width:160px"></div><div><label for="l-r">연 금리(%)</label><input id="l-r" type="number" step="0.01" value="4" style="width:80px"></div><div><label for="l-y">기간(년)</label><input id="l-y" type="number" value="30" style="width:70px"></div><button class="btn-p" id="l-go">계산</button></div><div class="tool-out" id="l-out">계산 결과가 여기에 표시됩니다.</div></div>
<div class="tool-box"><h3 style="margin-top:0">📏 DSR 대출 한도</h3>
<div class="tool-row"><div><label for="d-i">연소득(원)</label><input id="d-i" type="number" value="50000000" style="width:160px"></div><div><label for="d-r">연 금리(%)</label><input id="d-r" type="number" step="0.01" value="4" style="width:80px"></div><div><label for="d-s">스트레스 가산(%p)</label><input id="d-s" type="number" step="0.1" value="0" style="width:80px"></div><div><label for="d-y">만기(년)</label><input id="d-y" type="number" value="30" style="width:70px"></div><button class="btn-p" id="d-go">계산</button></div><div class="tool-out" id="d-out">계산 결과가 여기에 표시됩니다.</div></div>
<div class="tool-box"><h3 style="margin-top:0">💰 예금 이자</h3>
<div class="tool-row"><div><label for="e-p">예치 금액(원)</label><input id="e-p" type="number" value="10000000" style="width:150px"></div><div><label for="e-r">연 금리(%)</label><input id="e-r" type="number" step="0.1" value="3.5" style="width:80px"></div><div><label for="e-m">기간(개월)</label><input id="e-m" type="number" value="12" style="width:70px"></div><button class="btn-p" id="e-go">계산</button></div><div class="tool-out" id="e-out">계산 결과가 여기에 표시됩니다.</div></div>
<div class="tool-box"><h3 style="margin-top:0">🐷 적금 이자</h3>
<div class="tool-row"><div><label for="s-p">월 납입액(원)</label><input id="s-p" type="number" value="500000" style="width:140px"></div><div><label for="s-r">연 금리(%)</label><input id="s-r" type="number" step="0.1" value="4" style="width:80px"></div><div><label for="s-m">기간(개월)</label><input id="s-m" type="number" value="12" style="width:70px"></div><button class="btn-p" id="s-go">계산</button></div><div class="tool-out" id="s-out">계산 결과가 여기에 표시됩니다.</div></div>
""" + ad() + """
<script src="/assets/js/loan.js"></script>
"""
    faq = [("계산 결과는 정확한가요?", "입력한 조건으로 계산한 참고용 추정입니다. 실제 금리·수수료·한도는 금융기관과 개인 조건에 따라 달라집니다."), ("입력한 금액은 저장되나요?", "아니요. 모든 계산은 브라우저 안에서만 이루어지고 서버로 전송되지 않습니다.")]
    write("/calculator/", layout("/calculator/", "대출·예적금 계산기 — 대출 이자, DSR 한도, 예금, 적금", "대출 월 상환액, DSR 대출 한도, 예금·적금 세후 이자를 한 곳에서 계산합니다. 입력값은 서버로 전송되지 않습니다.", body, faq, [("홈", "/"), ("계산기", "/calculator/")]), "0.9")

def page_home():
    body = f"""
<div class="hero"><h1>🏦 대출 이자 · DSR 한도 · 예금 · 적금 계산</h1><p>금액·금리·기간별 월 상환액과 세후 이자를 표로 바로 확인하세요.</p></div>
{ad()}
<div class="card-grid">
<a class="card" href="/loan/"><b>🏦 대출 이자</b><span>금액·금리·기간별 월 상환액</span></a>
<a class="card" href="/dsr/"><b>📏 DSR 한도</b><span>연소득별 대출 가능 금액</span></a>
<a class="card" href="/deposit/"><b>💰 예금 이자</b><span>금액별 세후 이자</span></a>
<a class="card" href="/savings/"><b>🐷 적금 이자</b><span>월 납입액별 만기 수령액</span></a>
<a class="card" href="/interest/"><b>💸 이자 계산</b><span>금액×금리 1년·한 달 이자</span></a>
<a class="card" href="/afford/"><b>🧾 대출 한도</b><span>월 상환액으로 거꾸로 계산</span></a>
<a class="card" href="/goal/"><b>🎯 목표 모으기</b><span>1억 모으려면 월 얼마?</span></a>
<a class="card" href="/pension/"><b>🏠 주택연금</b><span>나이·집값별 월 수령액</span></a>
<a class="card" href="/product/"><b>🏷️ 금융상품 금리</b><span>예금·적금·대출 공시 비교</span></a>
<a class="card" href="/rank/"><b>🏆 금리 순위</b><span>예금·적금·대출 TOP</span></a>
<a class="card" href="/calculator/"><b>🧮 계산기</b><span>직접 입력</span></a>
</div>
<h2 class="group-title">🔥 많이 찾는 계산</h2>
{chips([("예금 금리 순위", "/rank/deposit/12/"), ("주담대 금리 비교", "/product/mortgage/"), ("3억 4% 이자", "/interest/3억/4/"), ("1억 5% 이자", "/interest/1억/5/"), ("월 100만원 대출한도", "/afford/100/4/30년/"), ("1억 모으기 적금", "/goal/1억/4/60개월/"), ("3억 4% 30년", "/loan/3억/4/30년/"), ("2억 4.5% 20년", "/loan/2억/4.5/20년/"), ("5억 4% 30년", "/loan/5억/4/30년/"), ("1억 5% 10년", "/loan/1억/5/10년/"), ("연소득 5천 한도", "/dsr/5천/"), ("예금 1천만원", "/deposit/1천/"), ("적금 월 50만원", "/savings/50/")])}
<p class="lead">우아대출은 대출 원리금 상환액과 총이자, DSR 대출 한도, 예금·적금 세후 이자를 금액별로 계산해 둔 사이트입니다. 모든 결과는 입력 조건으로 계산한 참고용 추정이며 대출·투자 권유가 아닙니다. 자세한 기준은 <a href="/about/">계산 기준</a>을 참고하세요. 연봉 실수령액과 세금은 <a href="https://wooayeonbong.wooahouse.com">우아연봉</a>·<a href="https://wooatax.wooahouse.com">우아세금</a>에서 확인하세요.</p>
"""
    faq = [("계산 결과를 믿어도 되나요?", "입력한 조건으로 계산한 참고용 추정입니다. 실제 금리와 한도는 금융기관 심사 결과에 따릅니다."), ("원리금균등이 무엇인가요?", "매월 같은 금액(원금+이자)을 내는 상환 방식입니다.")]
    write("/", layout("/", "우아대출 — 대출 이자 계산, DSR 한도, 예금·적금 이자", "대출 월 상환액과 총이자, 연소득별 DSR 대출 한도, 예금·적금 세후 이자를 금액별로 정리한 계산 사이트. 계산기 제공.", body, faq), "1.0")

def page_about():
    body = """
<div class="page-head"><h1>계산 기준</h1><p>어떤 식으로 계산했는지 공개합니다 (2026년 10월 기준)</p></div>
<h2 class="group-title">🏦 대출 이자</h2><p class="lead">원리금균등: 월 상환액 = 원금 × 월이율 ÷ (1 − (1+월이율)^−개월수), 월이율 = 연이율 ÷ 12. 원금균등: 매월 원금 = 대출액 ÷ 개월수, 이자 = 잔액 × 월이율, 총이자 = 대출액 × 월이율 × (개월수+1) ÷ 2. 만기일시: 매월 이자 = 대출액 × 월이율. 거치기간, 중도상환수수료, 인지세, 변동금리 변화는 반영하지 않았습니다.</p>
<h2 class="group-title">📏 DSR</h2><p class="lead">연소득 × 40%(은행권 기준)를 연간 원리금 상환 가능액으로 보고 원리금균등으로 환산한 최대 대출액입니다. 다른 대출이 없다고 가정하며 스트레스 DSR 가산금리는 예시(1.5%p)입니다. 실제 한도는 LTV·DTI·지역별 규제와 금융기관 심사에 따릅니다.</p>
<h2 class="group-title">💰 예금·적금</h2><p class="lead">단리 정기예금: 원금 × 연이율 × 개월수/12. 정기적금(매월 초 납입 단리): 월 납입액 × 월이율 × n(n+1)/2. 이자소득세 15.4%(소득세 14% + 지방소득세 1.4%)를 뗀 세후 금액이며 우대금리·비과세·복리는 반영하지 않았습니다.</p>
<h2 class="group-title">💸 이자·한도·목표 계산</h2><p class="lead">이자: 1년 이자 = 금액 × 연 금리, 한 달 이자 = 금액 × 연 금리 ÷ 12(이자만 내는 만기일시 기준). 월 상환액 → 대출 한도: 월 상환액 × (1 − (1+월이율)^−개월수) ÷ 월이율(원리금균등, 만원 단위 내림). 목표 금액 적금: 세후 만기 수령액이 목표 이상이 되는 최소 월 납입액(단리, 이자소득세 15.4%, 100원 단위 올림). 예금 금리·기간 조합은 단리 세후 이자입니다.</p>
<h2 class="group-title">⚠️ 한계</h2><p class="lead">이 사이트의 계산은 입력 조건에 따른 참고용 추정이며 특정 금융상품의 가입·대출을 권유하지 않습니다. 계약 전 금융기관의 상품설명서와 금융감독원 금융소비자 정보포털에서 확인하세요.</p>
<h2 class="group-title">📬 문의·정정</h2><p class="lead">오류 제보는 <a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a> 으로 보내 주세요.</p>
"""
    write("/about/", layout("/about/", "계산 기준 — 대출·DSR·예적금 계산식과 한계", "우아대출의 대출 이자, DSR, 예금·적금 계산식과 반영하지 않은 항목을 공개합니다.", body, None, [("홈", "/"), ("계산 기준", "/about/")]), "0.5")

def page_privacy():
    body = """
<div class="page-head"><h1>개인정보처리방침</h1></div>
<p class="lead">우아대출(wooaloan.wooahouse.com, 이하 “서비스”)은 회원가입·로그인을 요구하지 않으며 이용자의 개인정보를 직접 수집하지 않습니다. 계산기에 입력한 값은 브라우저 안에서만 처리되고 서버로 전송되지 않습니다.</p>
<h3>자동 수집 정보</h3><p class="lead">서비스 개선을 위해 Google Analytics로 방문자 수·페이지뷰 등 익명 통계를 수집하며, Google AdSense와 쿠팡 파트너스는 맞춤 광고를 위해 쿠키를 사용할 수 있습니다. 쿠키는 브라우저 설정에서 비활성화할 수 있습니다. (<a href="https://policies.google.com/privacy">Google 개인정보처리방침</a>, <a href="https://policies.google.com/technologies/ads">Google 광고 정책</a>)</p>
<h3>쿠팡 파트너스</h3><p class="lead">일부 페이지에는 쿠팡 파트너스 활동의 일환으로 광고가 포함되어 있으며 이에 따른 수수료를 제공받을 수 있습니다.</p>
<h3>문의</h3><p class="lead"><a href="mailto:ingmaster83@gmail.com">ingmaster83@gmail.com</a></p>
<p class="note">최종 수정일: 2026년 10월 21일</p>
"""
    write("/privacy/", layout("/privacy/", "개인정보처리방침", "우아대출 개인정보처리방침", body, None, [("홈", "/"), ("개인정보처리방침", "/privacy/")]), sitemap=False)

def make_og():
    f = ROOT / "assets" / "og-image.png"
    if f.exists(): return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return
    im = Image.new("RGB", (1200, 630), (30, 64, 175)); dr = ImageDraw.Draw(im)
    def font(sz):
        for n in ("malgunbd.ttf", "malgun.ttf", "NanumGothicBold.ttf"):
            try: return ImageFont.truetype(n, sz)
            except Exception: pass
        return ImageFont.load_default()
    dr.rounded_rectangle((90, 90, 1110, 540), 40, fill=(255, 255, 255))
    dr.text((150, 150), "우아대출", font=font(110), fill=(30, 58, 138))
    dr.text((150, 300), "대출 이자 · DSR 한도 · 예금 · 적금", font=font(54), fill=(31, 41, 55))
    dr.text((150, 380), "금액별 계산표", font=font(54), fill=(31, 41, 55))
    dr.text((150, 470), "wooaloan.wooahouse.com", font=font(34), fill=(107, 114, 128))
    im.save(f)

def main():
    t0 = time.time(); make_og()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    for nf in ROOT.glob("naver*.html"): shutil.copy(nf, OUT / nf.name)
    for a in LOAN_AMTS:
        page_loan_amt(a)
        for r in RATES:
            for y in years_for(a): page_loan(a, r, y)
    hub_loan()
    for i in INCOMES: page_dsr(i)
    hub_dsr()
    for a in DEP_AMTS: page_dep(a)
    hub_dep()
    for a in SAV_AMTS: page_sav(a)
    hub_sav()
    for a in INT_AMTS:
        page_int_amt(a)
        for r in INT_RATES: page_int(a, r)
    hub_int()
    for p in AFF_PAY:
        page_aff_amt(p)
        for r in RATES:
            for y in AFF_YEARS: page_aff(p, r, y)
    hub_aff()
    for g in GOAL_T:
        page_goal_amt(g)
    for (g, r, n) in sorted(GOAL_SET): page_goal(g, r, n)
    hub_goal()
    for a in DEP_AMTS:
        for r in DEP_RATES:
            for m in DEP_MONTHS: page_dep_combo(a, r, m)
    import build_products
    build_products.main()
    import build_pension
    build_pension.main()
    page_calc(); page_home(); page_about(); page_privacy()
    today = time.strftime("%Y-%m-%d")
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (BASE, q(p), today, pr) for p, pr in WRITTEN)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls, encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE, encoding="utf-8")
    (OUT / "CNAME").write_text("wooaloan.wooahouse.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    nf = layout("/404.html", "페이지를 찾을 수 없습니다", "요청한 페이지를 찾을 수 없습니다.", '<div class="page-head"><h1>페이지를 찾을 수 없습니다</h1></div><div class="chips"><a class="chip" href="/">홈</a><a class="chip" href="/calculator/">계산기</a></div>', None, None, noindex=True)
    (OUT / "404.html").write_text(nf, encoding="utf-8")
    print("pages", len(WRITTEN), "elapsed", round(time.time() - t0), "s")

if __name__ == "__main__":
    main()
