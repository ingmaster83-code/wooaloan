# -*- coding: utf-8 -*-
"""주택연금 월지급금 페이지 -> build_site.main() 에서 호출.
 /pension/ 허브(계산기+표), /pension/{나이}세/ , /pension/{가격}억/ , /pension/{나이}세/{가격}억/
데이터: 한국주택금융공사(HF) '월지급금 예시' 종신지급방식(정액형) 2026.03.01 기준, 단위 천원, 부부 중 연소자 나이 기준.
  https://www.hf.go.kr/ko/sub03/sub03_01_01_02.do  (일반주택 / 노인복지주택 / 주거목적 오피스텔 3표를 그대로 옮김)
표에 없는 나이·가격은 페이지로 만들지 않고, 계산기에서만 선형 보간한 '추정'으로 안내한다."""
from common import *
from build_site import table, chips

ASOF = "2026년 3월 1일"
SRC = "한국주택금융공사(HF) 월지급금 예시"
URL = "https://www.hf.go.kr/ko/sub03/sub03_01_01_02.do"
AGES = [55, 60, 65, 70, 75, 80]
PRICES = list(range(1, 13))        # 억원
T = {   # 종류 -> {나이: [1억..12억 월지급금(천원)]}
    "general": {
        55: [156, 312, 468, 624, 780, 936, 1092, 1248, 1404, 1560, 1716, 1872],
        60: [210, 421, 632, 842, 1053, 1264, 1475, 1685, 1896, 2107, 2318, 2528],
        65: [252, 505, 758, 1011, 1264, 1517, 1770, 2023, 2276, 2529, 2782, 3035],
        70: [307, 615, 923, 1231, 1539, 1847, 2155, 2462, 2770, 3078, 3386, 3414],
        75: [381, 762, 1143, 1525, 1906, 2287, 2669, 3050, 3431, 3666, 3666, 3666],
        80: [483, 966, 1449, 1932, 2416, 2899, 3382, 3865, 4060, 4060, 4060, 4060]},
    "senior": {
        55: [122, 245, 368, 491, 613, 736, 859, 982, 1104, 1227, 1350, 1473],
        60: [170, 341, 512, 682, 853, 1024, 1195, 1365, 1536, 1707, 1877, 2048],
        65: [211, 422, 633, 844, 1055, 1266, 1477, 1688, 1899, 2110, 2321, 2532],
        70: [263, 526, 789, 1052, 1316, 1579, 1842, 2105, 2368, 2632, 2895, 3158],
        75: [334, 669, 1004, 1338, 1673, 2008, 2343, 2677, 3012, 3347, 3658, 3658],
        80: [434, 869, 1303, 1738, 2172, 2607, 3041, 3476, 3910, 4054, 4054, 4054]},
    "officetel": {
        55: [112, 225, 338, 451, 564, 677, 790, 903, 1016, 1128, 1241, 1354],
        60: [158, 316, 475, 633, 792, 950, 1109, 1267, 1426, 1584, 1742, 1901],
        65: [197, 394, 591, 788, 985, 1183, 1380, 1577, 1774, 1971, 2169, 2366],
        70: [248, 497, 746, 994, 1243, 1492, 1741, 1989, 2238, 2487, 2735, 2984],
        75: [319, 638, 957, 1276, 1596, 1915, 2234, 2553, 2872, 3192, 3511, 3655],
        80: [418, 836, 1254, 1672, 2090, 2508, 2926, 3344, 3762, 4052, 4052, 4052]},
}
KIND = {"general": "일반주택(아파트·단독·연립 등)", "senior": "노인복지주택", "officetel": "주거목적 오피스텔"}
NOTE = ("월지급금은 부부 중 연소자 나이와 담보주택의 시세 또는 감정평가액을 기준으로 정해지며, 위 표는 한국주택금융공사가 공개한 종신지급방식(정액형) 예시(%s 기준)를 그대로 옮긴 것입니다. "
        "공시가격 등은 가입 가능 여부를 판단하는 기준이고 실제 월지급금은 감정평가액에 따라 달라집니다. 가입 조건·지급액은 금리와 제도 변경에 따라 바뀔 수 있으니 가입 전 주택금융공사(1688-8114)의 예상연금조회로 확인하세요." % ASOF)
COND = "부부 중 연소자가 만 55세 이상이고 보유 주택의 공시가격 등이 12억 원 이하인 경우 가입할 수 있습니다(주택금융공사 안내 기준, 제도 변경 가능)."

def v(kind, age, price): return T[kind][age][price - 1] * 1000          # 원
def w(n): return "{:,}".format(int(n))
def mw(x): return "{:,}".format(int(round(x / 10000)))                  # 만원
def age_row(age, kind="general"):
    return [['<a href="/pension/%d세/%d억/">%d억원</a>' % (age, p, p), w(v(kind, age, p)) + "원", mw(v(kind, age, p) * 12) + "만원"] for p in PRICES]

def price_row(price, kind="general"):
    return [['<a href="/pension/%d세/%d억/">%d세</a>' % (a, price, a), w(v(kind, a, price)) + "원", mw(v(kind, a, price) * 12) + "만원"] for a in AGES]

def cap_note(kind, age, price):
    arr = T[kind][age]
    if price >= 2 and arr[price - 1] == arr[price - 2]: return "이 구간은 월지급금 상한에 도달해 주택가격이 올라도 지급액이 더 늘지 않습니다."
    if price == 12 and arr[11] < arr[10] * 1.0 + 100 and arr[11] - arr[10] < arr[9] - arr[8] - 100: return "12억 원 구간은 상한 적용으로 증가폭이 줄었습니다."
    return ""

def page_ap(age, price):
    path = "/pension/%d세/%d억/" % (age, price)
    m = v("general", age, price); y = m * 12
    ages_cmp = [[("<b>%d세</b>" % a) if a == age else '<a href="/pension/%d세/%d억/">%d세</a>' % (a, price, a), w(v("general", a, price)) + "원", ("+" if v("general", a, price) >= m else "") + w(v("general", a, price) - m) + "원" if a != age else "-"] for a in AGES]
    kinds = [[KIND[k], w(v(k, age, price)) + "원"] for k in ("general", "senior", "officetel")]
    pmv = [['<a href="/pension/%d세/%d억/">%d억원</a>' % (age, p, p) if p != price else "<b>%d억원</b>" % p, w(v("general", age, p)) + "원"] for p in PRICES if abs(p - price) <= 3]
    cn = cap_note("general", age, price)
    body = f"""
<div class="page-head"><h1>주택연금 월지급금 — {age}세 · {price}억원 주택</h1><p>종신지급방식 정액형 · 부부 중 연소자 {age}세 · {ASOF} 기준</p></div>
<p class="lead">부부 중 연소자가 <b>{age}세</b>이고 주택(시세·감정평가액)이 <b>{price}억 원</b>일 때 일반주택 종신지급방식(정액형) 월지급금은 <b>{w(m)}원</b>(연 약 {mw(y)}만 원)입니다. {cn}</p>
{ad()}
<div class="stat-row"><div class="stat"><small>월 수령액</small><b>{w(m)}원</b></div><div class="stat"><small>연 환산</small><b>{mw(y)}만원</b></div><div class="stat"><small>20년 단순 합계</small><b>{mw(y * 20)}만원</b></div></div>
<h2>주택 종류별 월지급금 ({age}세 · {price}억원)</h2>
{table(['주택 종류', '월지급금'], kinds, (1,))}
<h2>가입 나이별 비교 ({price}억원 주택)</h2>
<p class="lead">같은 집이라도 가입 나이가 많을수록 월지급금이 커집니다. 표는 {price}억 원 주택 기준입니다.</p>
{table(['부부 중 연소자 나이', '월지급금', f'{age}세 대비 차이'], ages_cmp, (1, 2))}
<h2>주택가격별 월지급금 ({age}세)</h2>
{table(['주택가격', '월지급금'], pmv, (1,))}
<p class="note">20년 단순 합계는 월지급금 × 12개월 × 20년으로 단순 곱한 값이며 이자·정산·실제 수령 기간은 반영하지 않았습니다. {NOTE}</p>
{chips([("주택연금 계산기", "/pension/"), (f"{age}세 월지급금 전체", f"/pension/{age}세/"), (f"{price}억 주택 연령별", f"/pension/{price}억/"), ("월 상환액으로 대출 한도", "/afford/"), ("대출 이자 계산", "/loan/")])}
<p class="note">출처: <a href="{URL}" target="_blank" rel="noopener">{SRC}</a></p>
"""
    faq = [(f"{age}세에 {price}억 원 주택으로 주택연금을 받으면 월 얼마인가요?", f"일반주택 종신지급방식(정액형) 기준 월 {w(m)}원입니다(한국주택금융공사 {ASOF} 예시). 부부 중 연소자 나이와 감정평가액으로 정해지며 실제 금액은 예상연금조회로 확인하세요."),
           ("주택연금 월지급금은 무엇으로 정해지나요?", "부부 중 연소자의 나이, 담보주택의 시세 또는 감정평가액, 지급방식(종신·확정기간, 정액·증가·감소형 등)에 따라 달라집니다."),
           ("주택연금은 누가 가입할 수 있나요?", COND)]
    write(path, layout(path, f"주택연금 {age}세 {price}억 월지급금 — 월 {w(m)}원 (종신 정액형)", f"부부 중 연소자 {age}세, {price}억 원 주택의 주택연금 월지급금은 {w(m)}원(종신지급방식 정액형, 한국주택금융공사 {ASOF} 기준). 나이·주택종류별 비교.",
                       body, faq, [("우아대출", "/"), ("주택연금", "/pension/"), (f"{age}세", f"/pension/{age}세/"), (f"{price}억", path)]), "0.6")

def page_age(age):
    path = "/pension/%d세/" % age
    rows = age_row(age); m3 = v("general", age, 3); m5 = v("general", age, 5)
    body = f"""
<div class="page-head"><h1>주택연금 {age}세 월지급금 — 주택가격별</h1><p>종신지급방식 정액형 · 부부 중 연소자 {age}세 · {ASOF} 기준</p></div>
<p class="lead">부부 중 연소자 {age}세가 일반주택으로 주택연금(종신지급방식, 정액형)에 가입하면 3억 원 주택은 월 약 <b>{w(m3)}원</b>, 5억 원 주택은 월 약 <b>{w(m5)}원</b>을 받습니다. 주택가격을 눌러 자세히 보세요.</p>
{ad()}
{table(['주택가격', '월지급금', '연 환산'], rows, (1, 2))}
<h2>노인복지주택 · 주거목적 오피스텔</h2>
{table(['주택가격', '노인복지주택', '주거목적 오피스텔'], [['%d억원' % p, w(v('senior', age, p)) + '원', w(v('officetel', age, p)) + '원'] for p in PRICES], (1, 2))}
<p class="note">{NOTE}</p>
{chips([("주택연금 계산기", "/pension/")] + [(f"{a}세", f"/pension/{a}세/") for a in AGES if a != age])}
<p class="note">출처: <a href="{URL}" target="_blank" rel="noopener">{SRC}</a></p>
"""
    faq = [(f"{age}세 주택연금 월지급금은 얼마인가요?", f"일반주택 3억 원 기준 월 {w(m3)}원, 5억 원 기준 월 {w(m5)}원입니다(종신지급방식 정액형, {ASOF} 기준)."), ("주택연금은 몇 세부터 가입하나요?", COND)]
    write(path, layout(path, f"주택연금 {age}세 월지급금 — 1억~12억 주택가격별 표", f"부부 중 연소자 {age}세 주택연금 월지급금: 3억 {w(m3)}원, 5억 {w(m5)}원. 주택가격 1억~12억 표(한국주택금융공사 {ASOF} 기준).", body, faq, [("우아대출", "/"), ("주택연금", "/pension/"), (f"{age}세", path)]), "0.7")

def page_price(price):
    path = "/pension/%d억/" % price
    rows = price_row(price); m70 = v("general", 70, price)
    body = f"""
<div class="page-head"><h1>{price}억 원 주택 주택연금 월지급금 — 나이별</h1><p>종신지급방식 정액형 · {ASOF} 기준</p></div>
<p class="lead">시세 {price}억 원 주택으로 주택연금에 가입하면 부부 중 연소자 70세 기준 월 약 <b>{w(m70)}원</b>을 받습니다. 가입 나이별 금액을 비교해 보세요.</p>
{ad()}
{table(['부부 중 연소자 나이', '월지급금', '연 환산'], rows, (1, 2))}
<h2>노인복지주택 · 주거목적 오피스텔</h2>
{table(['나이', '노인복지주택', '주거목적 오피스텔'], [['%d세' % a, w(v('senior', a, price)) + '원', w(v('officetel', a, price)) + '원'] for a in AGES], (1, 2))}
<p class="note">{NOTE}</p>
{chips([("주택연금 계산기", "/pension/")] + [(f"{p}억", f"/pension/{p}억/") for p in PRICES if p != price and abs(p - price) <= 3])}
<p class="note">출처: <a href="{URL}" target="_blank" rel="noopener">{SRC}</a></p>
"""
    faq = [(f"{price}억 원 집으로 주택연금을 받으면 월 얼마인가요?", f"일반주택 기준 55세 {w(v('general', 55, price))}원, 65세 {w(v('general', 65, price))}원, 75세 {w(v('general', 75, price))}원입니다({ASOF} 기준 예시)."), ("주택연금은 누가 가입할 수 있나요?", COND)]
    write(path, layout(path, f"{price}억 주택 주택연금 월지급금 — 55세~80세 나이별 표", f"시세 {price}억 원 주택의 주택연금 월지급금: 70세 {w(m70)}원 등 나이별 표(한국주택금융공사 {ASOF} 기준).", body, faq, [("우아대출", "/"), ("주택연금", "/pension/"), (f"{price}억", path)]), "0.7")

CALC_JS = """<script>
(function(){
var A=%s,T=%s;
function $(i){return document.getElementById(i);}
function f(n){return Math.round(n).toLocaleString('ko-KR');}
function pay(kind,age,price){var t=T[kind],i=0;while(i<A.length-2&&age>A[i+1])i++;var a0=A[i],a1=A[i+1],k=(age-a0)/(a1-a0);
 function at(a){var arr=t[a];if(price<=1)return arr[0]*price;if(price>=12)return arr[11];var j=Math.floor(price)-1,fr=price-Math.floor(price);return arr[j]+(arr[j+1]-arr[j])*fr;}
 return (at(a0)+(at(a1)-at(a0))*k)*1000;}
$('pn-go').addEventListener('click',function(){var age=+$('pn-age').value,price=+$('pn-price').value,kind=$('pn-kind').value,o=$('pn-out');
 if(!(age>=55&&age<=80)||!(price>=0.5&&price<=12)){o.textContent='나이는 55~80세, 주택가격은 0.5~12억 사이로 입력하세요.';return;}
 var m=pay(kind,age,price),exact=(A.indexOf(age)>=0&&price===Math.floor(price));
 o.innerHTML='월 예상 지급액 <b>'+f(m)+'원</b> (연 '+f(m*12/10000)+'만원)'+(exact?'':' <small>· 표에 없는 나이·가격은 인접 값으로 보간한 추정입니다</small>');});
})();
</script>"""

def hub():
    import json as _j
    js = CALC_JS % (_j.dumps(AGES), _j.dumps({k: {str(a): v_ for a, v_ in d.items()} for k, d in T.items()}))
    # JS 에서 T[kind][age] 접근을 위해 숫자키 사용: JSON 키는 문자열이지만 JS 객체 인덱싱은 숫자도 허용됨
    calc = ('<div class="calc-box"><div class="calc-row">'
            '<label>부부 중 연소자 나이(세)<input id="pn-age" type="number" value="70" min="55" max="80"></label>'
            '<label>주택가격(억원)<input id="pn-price" type="number" step="0.1" value="3" min="0.5" max="12"></label>'
            '<label>주택 종류<select id="pn-kind"><option value="general">일반주택</option><option value="senior">노인복지주택</option><option value="officetel">주거목적 오피스텔</option></select></label>'
            '<button class="btn-p" id="pn-go" type="button">계산</button></div><div class="calc-out" id="pn-out">값을 입력하고 계산을 누르세요.</div></div>' + js)
    rows = [['<a href="/pension/%d세/">%d세</a>' % (a, a)] + ['<a href="/pension/%d세/%d억/">%s</a>' % (a, p, w(v("general", a, p))) for p in (2, 3, 5, 7, 9)] for a in AGES]
    body = f"""
<div class="page-head"><h1>주택연금 월지급금 계산 — 나이·주택가격별 표</h1><p>한국주택금융공사 종신지급방식 정액형 · {ASOF} 기준</p></div>
<p class="lead">주택연금은 만 55세 이상이 집을 담보로 맡기고 평생(또는 정한 기간) 매달 연금을 받는 제도입니다. 부부 중 연소자 나이와 주택가격을 넣어 월지급금을 확인하세요. 표는 한국주택금융공사 공개 예시를 그대로 옮긴 것입니다.</p>
{ad()}
<h2>🧮 주택연금 계산기</h2>
{calc}
<h2>일반주택 월지급금 요약 (원)</h2>
{table(['나이', '2억', '3억', '5억', '7억', '9억'], rows, (1, 2, 3, 4, 5))}
<h2>주택가격별 · 나이별 전체 표</h2>
{chips([(f"{a}세", f"/pension/{a}세/") for a in AGES])}
{chips([(f"{p}억 주택", f"/pension/{p}억/") for p in PRICES])}
<h2>가입 조건</h2>
<p class="lead">{COND}</p>
<p class="note">{NOTE}</p>
{chips([("대출 이자 계산", "/loan/"), ("월 상환액으로 대출 한도", "/afford/"), ("DSR 한도", "/dsr/")])}
<p class="note">출처: <a href="{URL}" target="_blank" rel="noopener">{SRC}</a></p>
"""
    faq = [("주택연금 월지급금은 어떻게 정해지나요?", "부부 중 연소자의 나이와 담보주택의 시세·감정평가액, 지급방식에 따라 정해집니다. 나이가 많을수록, 집값이 높을수록 많이 받습니다(상한 있음)."),
           ("70세에 3억 원 집이면 월 얼마인가요?", f"일반주택 종신지급방식 정액형 기준 월 {w(v('general', 70, 3))}원입니다({ASOF} 기준 예시)."),
           ("주택연금은 누가 가입할 수 있나요?", COND)]
    write("/pension/", layout("/pension/", "주택연금 월지급금 계산 — 나이·주택가격별 수령액 표", f"주택연금 월지급금 계산기와 55~80세·1~12억 주택가격별 표. 70세 3억 월 {w(v('general', 70, 3))}원 (한국주택금융공사 {ASOF} 기준 종신 정액형).", body, faq, [("우아대출", "/"), ("주택연금", "/pension/")]), "0.8")

def main():
    for a in AGES:
        page_age(a)
        for p in PRICES: page_ap(a, p)
    for p in PRICES: page_price(p)
    hub()
    print("pension pages", 1 + len(AGES) + len(PRICES) + len(AGES) * len(PRICES))
