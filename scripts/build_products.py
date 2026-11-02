# -*- coding: utf-8 -*-
"""금융상품 금리 비교 페이지(금융감독원 '금융상품한눈에' 공시) 생성 -> build_site.main() 에서 호출.
 /product/ 허브, /product/{kind}/ 목록, /product/{kind}/{id}/ 상품, /rank/... 금리 순위, /company/{코드}/ 금융사
데이터: data/finlife/{kind}.json (scripts/fetch_finlife.py). 상품 ID는 금융회사코드-상품코드로 고정하고,
공시에서 빠진 상품은 페이지를 남기되 '공시 종료' 안내 + noindex + 사이트맵 제외로 처리한다."""
import json, re
from common import *
import loan as L
from build_site import table, chips, kor, amt2, MAN, EOK, RATES, pct, rs, aslug, amt

DATA = ROOT / "data" / "finlife"
KINDS = {
    "deposit": ("정기예금", "예금"), "saving": ("적금", "적금"), "mortgage": ("주택담보대출", "주담대"),
    "rent": ("전세자금대출", "전세대출"), "credit": ("개인신용대출", "신용대출"),
}
GRP = {"020000": "은행", "030300": "저축은행", "050000": "보험사", "030200": "여신전문금융", "060000": "금융투자"}
TERMS = [6, 12, 24, 36]
GRADES = [("1", "900점 초과"), ("4", "801~900점"), ("5", "701~800점"), ("6", "601~700점"),
          ("10", "501~600점"), ("11", "401~500점"), ("12", "301~400점"), ("13", "300점 이하")]
SRC = "금융감독원 금융상품한눈에"
NOTE = ("이 정보는 금융감독원 ‘금융상품한눈에’ 공시를 그대로 정리한 것으로 금융상품의 가입·대출을 권유하지 않습니다. "
        "실제 적용 금리와 한도는 가입 시점·개인 신용·거래 실적에 따라 달라지니 계약 전 금융회사의 상품설명서를 확인하세요.")

P, MONTH, CO = {}, "", {}          # P[kind][id] = rec, CO[fin_co_no] = {name, grp}

def ym(m): return "%s년 %d월" % (m[:4], int(m[4:6])) if m and len(m) >= 6 else "-"
def ymd(s): return "%s-%s-%s" % (s[:4], s[4:6], s[6:8]) if s and len(s) >= 8 else "-"
def fr(v): return "-" if v is None else "%.2f%%" % v
def txt(s):
    s = str(s if s is not None else "").strip()
    return esc(s).replace("\n", "<br>") if s and s not in ("null", "None") else "-"

def load():
    global MONTH
    for k in KINDS:
        d = json.loads((DATA / (k + ".json")).read_text(encoding="utf-8"))
        for r in d["products"].values():       # 공시 원문의 줄바꿈·겹공백이 제목을 깨뜨리므로 이름만 정리
            for f in ("kor_co_nm", "fin_prdt_nm"):
                r["base"][f] = re.sub(r"\s+", " ", r["base"][f] or "").strip()
        usable = {i: r for i, r in d["products"].items() if r["options"]}
        cnt = {}
        for r in usable.values(): cnt[(r["base"]["fin_co_no"], r["base"]["fin_prdt_nm"])] = cnt.get((r["base"]["fin_co_no"], r["base"]["fin_prdt_nm"]), 0) + 1
        for r in usable.values():          # 같은 회사에 이름이 같은 상품이 있으면 상품코드를 붙여 구분(제목 중복 방지)
            if cnt[(r["base"]["fin_co_no"], r["base"]["fin_prdt_nm"])] > 1:
                r["base"]["fin_prdt_nm"] += " (%s)" % re.sub(r"\s+", " ", r["base"]["fin_prdt_cd"]).strip()
        if len(usable) != len(d["products"]):
            print("  [%s] 금리(옵션) 정보가 없어 제외: %d개" % (k, len(d["products"]) - len(usable)))
        P[k] = usable; MONTH = max(MONTH, d["month"])
        for r in d["products"].values():
            b = r["base"]; CO.setdefault(b["fin_co_no"], {"name": b["kor_co_nm"], "grp": b["_grp"]})

def active(r): return r["last_seen"] == MONTH
def ppath(k, i): return "/product/%s/%s/" % (k, i)
def link(k, i):
    b = P[k][i]["base"]; return '<a href="%s">%s</a>' % (ppath(k, i), esc(b["fin_prdt_nm"]))
def colink(code): return '<a href="/company/%s/">%s</a>' % (code, esc(CO[code]["name"]))

# ───────── 금리 추출 ─────────
def best_opt(rec, term):
    c = [o for o in rec["options"] if str(o["save_trm"]) == str(term)]
    return max(c, key=lambda o: (o.get("intr_rate2") or 0, o.get("intr_rate") or 0)) if c else None

def terms_of(rec): return sorted({int(o["save_trm"]) for o in rec["options"]})
def feat_term(rec):
    ts = terms_of(rec)
    if 12 in ts: return 12
    return max([t for t in ts if t <= 36], default=ts[0] if ts else 12)

def sav_rate(rec, term):
    o = best_opt(rec, term); return (o["intr_rate"], o["intr_rate2"] or o["intr_rate"]) if o else None

def loan_rates(rec):
    o = rec["options"]
    if not o: return None
    mn = min(x["lend_rate_min"] for x in o if x["lend_rate_min"] is not None)
    mx = max(x["lend_rate_max"] for x in o if x["lend_rate_max"] is not None)
    avs = [x["lend_rate_avg"] for x in o if x["lend_rate_avg"] is not None]
    return mn, mx, (sum(avs) / len(avs) if avs else (mn + mx) / 2)

def credit_row(rec):
    for o in rec["options"]:
        if o["crdt_lend_rate_type_nm"] == "대출금리": return o
    return rec["options"][0] if rec["options"] else None

def credit_rates(rec):
    o = credit_row(rec)
    if not o: return None
    vals = [o["crdt_grad_" + g] for g, _ in GRADES if o.get("crdt_grad_" + g) is not None]
    return (min(vals), max(vals), o.get("crdt_grad_avg") or (sum(vals) / len(vals))) if vals else None

# ───────── 순위 ─────────
RANK = {}      # (kind, term) -> [id...] 금리 높은 순
def build_rank():
    for k in ("deposit", "saving"):
        for t in TERMS:
            rows = []
            for i, r in P[k].items():
                if active(r):
                    x = sav_rate(r, t)
                    if x: rows.append((-x[1], -x[0], r["base"]["kor_co_nm"], r["base"]["fin_prdt_nm"], i))
            RANK[(k, t)] = [x[-1] for x in sorted(rows)]

LOAN_RANK = {  # 순위 페이지 키 -> (종류, 표시명, 필터)
    "apt-fixed": ("mortgage", "아파트 담보 고정금리", lambda o: o["mrtg_type_nm"] == "아파트" and o["lend_rate_type_nm"] == "고정금리"),
    "apt-var": ("mortgage", "아파트 담보 변동금리", lambda o: o["mrtg_type_nm"] == "아파트" and o["lend_rate_type_nm"] == "변동금리"),
    "etc-fixed": ("mortgage", "아파트 외 담보 고정금리", lambda o: o["mrtg_type_nm"] == "아파트외" and o["lend_rate_type_nm"] == "고정금리"),
    "etc-var": ("mortgage", "아파트 외 담보 변동금리", lambda o: o["mrtg_type_nm"] == "아파트외" and o["lend_rate_type_nm"] == "변동금리"),
    "fixed": ("rent", "고정금리", lambda o: o["lend_rate_type_nm"] == "고정금리"),
    "var": ("rent", "변동금리", lambda o: o["lend_rate_type_nm"] == "변동금리"),
}
def loan_rank_rows(key):
    kind, _, f = LOAN_RANK[key]; rows = []
    for i, r in P[kind].items():
        if not active(r): continue
        c = [o for o in r["options"] if f(o) and o["lend_rate_min"] is not None]
        if c:
            mn = min(o["lend_rate_min"] for o in c); mx = max(o["lend_rate_max"] for o in c)
            avs = [o["lend_rate_avg"] for o in c if o["lend_rate_avg"] is not None]
            av = sum(avs) / len(avs) if avs else (mn + mx) / 2
            rows.append((av, mn, r["base"]["kor_co_nm"], i, mn, mx, av))
    return sorted(rows)
CREDIT_RANK = {"general": ("일반신용대출", "일반 신용대출"), "minus": ("마이너스한도대출", "마이너스통장"), "card": ("장기카드대출(카드론)", "카드론")}
def credit_rank_rows(key):
    tn = CREDIT_RANK[key][0]; rows = []
    for i, r in P["credit"].items():
        if active(r) and r["base"]["crdt_prdt_type_nm"] == tn:
            x = credit_rates(r)
            if x: rows.append((x[2], x[0], r["base"]["kor_co_nm"], i, x[0], x[1], x[2]))
    return sorted(rows)

# ───────── 계산 ─────────
def dep_calc(p, r, n, comp):
    g = p * ((1 + r / 1200.0) ** n - 1) if comp else p * r / 100.0 * n / 12.0
    g = L.rnd(g); return g, g - L.rnd(g * 0.154)
def sav_calc(m, r, n, comp):
    g = (m * sum((1 + r / 1200.0) ** k for k in range(1, n + 1)) - m * n) if comp else m * (r / 1200.0) * n * (n + 1) / 2.0
    g = L.rnd(g); return g, g - L.rnd(g * 0.154)

def basis_notice(r):
    b = r["base"]
    return ('<p class="note">공시월 %s · 공시 시작 %s · 출처 %s. %s</p>' % (ym(b["dcls_month"]), ymd(b["dcls_strt_day"]), SRC, NOTE))
def ended_banner(r):
    return '<p class="lead" style="background:#FEF3C7;padding:12px;border-radius:8px">⚠️ 이 상품은 %s 공시를 마지막으로 이후 공시에서 확인되지 않습니다. 판매가 종료되었거나 이름·조건이 바뀌었을 수 있으니 아래 금리는 참고만 하세요.</p>' % ym(r["last_seen"])

# ───────── 예금·적금 상품 ─────────
def page_savings_product(k, i):
    r = P[k][i]; b = r["base"]; name = KINDS[k][0]; co = b["kor_co_nm"]; nm = b["fin_prdt_nm"]
    t0 = feat_term(r); base0, max0 = sav_rate(r, t0) or (0, 0); o0 = best_opt(r, t0)
    comp = bool(o0) and o0["intr_rate_type_nm"] == "복리"
    rows = []
    for t in terms_of(r):
        for o in sorted([x for x in r["options"] if int(x["save_trm"]) == t], key=lambda x: (x["intr_rate_type_nm"], x.get("rsrv_type_nm", ""))):
            kind_txt = o["intr_rate_type_nm"] + (" · " + o["rsrv_type_nm"] if o.get("rsrv_type_nm") else "")
            rows.append(["%d개월" % t, kind_txt, fr(o["intr_rate"]), fr(o["intr_rate2"])])
    t_rate = table(["기간", "방식", "기본금리", "최고(우대 포함)"], rows, (2, 3))
    if k == "deposit":
        a, b2 = dep_calc(1000 * MAN, base0, t0, comp), dep_calc(1000 * MAN, max0, t0, comp)
        ex = table(["1천만 원 %d개월 예치" % t0, "기본금리 %s" % fr(base0), "최고금리 %s" % fr(max0)], [
            ["세전 이자", kor(a[0]), kor(b2[0])], ["세후 이자(15.4%)", kor(a[1]), kor(b2[1])], ["만기 수령액", kor(1000 * MAN + a[1]), kor(1000 * MAN + b2[1])]], (1, 2))
        ex_h = "💰 이자 예시 (1천만 원)"
    else:
        a, b2 = sav_calc(50 * MAN, base0, t0, comp), sav_calc(50 * MAN, max0, t0, comp)
        ex = table(["월 50만 원 %d개월 납입" % t0, "기본금리 %s" % fr(base0), "최고금리 %s" % fr(max0)], [
            ["세전 이자", kor(a[0]), kor(b2[0])], ["세후 이자(15.4%)", kor(a[1]), kor(b2[1])], ["만기 수령액", kor(50 * MAN * t0 + a[1]), kor(50 * MAN * t0 + b2[1])]], (1, 2))
        ex_h = "💰 이자 예시 (월 50만 원)"
    rk = RANK.get((k, t0), []); pos = rk.index(i) + 1 if i in rk else None
    grp_rank = [x for x in rk if P[k][x]["base"]["_grp"] == b["_grp"]]; gpos = grp_rank.index(i) + 1 if i in grp_rank else None
    scope = {"020000": "bank", "030300": "sb"}.get(b["_grp"])
    rank_txt = ""
    if pos:
        rank_txt = ("<p class=\"lead\">%d개월 최고금리 기준 공시된 %s %d개 중 <b>%d위</b>입니다(%s 중 %d위).</p>" % (t0, name, len(rk), pos, GRP.get(b["_grp"], "금융회사"), gpos))
    near_ids = rk[max(0, pos - 4): pos + 3] if pos else []
    near_rows = [[("<b>%s</b>" % esc(P[k][x]["base"]["fin_prdt_nm"])) if x == i else link(k, x), colink(P[k][x]["base"]["fin_co_no"]), fr((sav_rate(P[k][x], t0) or (0, 0))[1])] for x in near_ids]
    sib = [x for x, rr in P[k].items() if rr["base"]["fin_co_no"] == b["fin_co_no"] and x != i and active(rr)][:6]
    sib_rows = [[link(k, x), fr((sav_rate(P[k][x], feat_term(P[k][x])) or (0, 0))[1])] for x in sib]
    info = table(["항목", "내용"], [["가입 방법", txt(b["join_way"])], ["가입 대상", txt(b["join_member"])], ["최고 한도", (kor(b["max_limit"]) if isinstance(b["max_limit"], (int, float)) else txt(b["max_limit"])) if b["max_limit"] else "공시 없음"],
                                  ["만기 후 이자율", txt(b["mtrt_int"])], ["우대 조건", txt(b["spcl_cnd"])], ["기타 유의사항", txt(b["etc_note"])]])
    lead = ("<p class=\"lead\"><b>%s</b>의 <b>%s</b>은(는) %d개월 기준 기본금리 <b>%s</b>, 최고(우대 포함) <b>%s</b>입니다(%s, %s 공시). %s</p>" % (
        esc(co), esc(nm), t0, fr(base0), fr(max0), o0["intr_rate_type_nm"] if o0 else "-", ym(b["dcls_month"]),
        "우대금리는 %s의 조건을 모두 충족해야 받을 수 있습니다." % esc(co) if max0 > base0 else "우대금리 없이 기본금리가 그대로 적용됩니다."))
    body = f"""
<div class="page-head"><h1>{esc(co)} {esc(nm)} 금리 — {t0}개월 기본 {fr(base0)}·최고 {fr(max0)}</h1><p>{name} · {ym(b['dcls_month'])} 공시 · 출처 {SRC}</p></div>
{'' if active(r) else ended_banner(r)}
{lead}
<div class="stat-row"><div class="stat"><small>{t0}개월 기본금리</small><b>{fr(base0)}</b></div><div class="stat"><small>{t0}개월 최고금리</small><b>{fr(max0)}</b></div><div class="stat"><small>{name} 순위</small><b>{('%d위' % pos) if pos else '-'}</b></div></div>
{ad()}
<h2 class="group-title">📊 기간별 금리</h2>
{t_rate}
<h2 class="group-title">{ex_h}</h2>
{ex}
<p class="note">세후 금액은 이자소득세 15.4%를 뗀 값이며 {'월복리' if comp else '단리'}로 계산한 추정입니다. 실제 이자는 금융회사의 계산 방식에 따라 다를 수 있습니다.</p>
<h2 class="group-title">📌 가입 조건과 유의사항</h2>
{info}
{rank_txt}
{'<h2 class="group-title">🏆 비슷한 금리의 상품</h2>' + table(['상품', '금융회사', '%d개월 최고' % t0], near_rows, (2,)) if near_rows else ''}
{'<h2 class="group-title">🏦 ' + esc(co) + '의 다른 상품</h2>' + table(['상품', '최고금리'], sib_rows, (1,)) if sib_rows else ''}
{basis_notice(r)}
{chips(([("%s 금리 순위 %d개월" % (name, t0), "/rank/%s/%d/" % (k, t0))] if t0 in TERMS else [("%s 금리 순위" % name, "/rank/%s/12/" % k)]) + [(esc(co) + " 상품 전체", "/company/%s/" % b["fin_co_no"]), ("%s 전체 목록" % name, "/product/%s/" % k), ("예금 이자 계산" if k == "deposit" else "적금 이자 계산", "/deposit/" if k == "deposit" else "/savings/"), ("계산기", "/calculator/")])}
"""
    faq = [("%s %s 금리는 얼마인가요?" % (co, nm), "%d개월 기준 기본금리 %s, 최고금리 %s입니다(%s 공시)." % (t0, fr(base0), fr(max0), ym(b["dcls_month"]))),
           ("우대금리는 어떻게 받나요?", (b["spcl_cnd"] or "공시된 우대 조건이 없습니다.").strip()[:300]),
           ("가입은 어떻게 하나요?", "가입 방법: %s." % ((b["join_way"] or "공시 없음").strip()))]
    path = ppath(k, i)
    write(path, layout(path, "%s %s 금리 — %d개월 기본 %s·최고 %s" % (co, nm, t0, fr(base0), fr(max0)),
                       "%s %s: %d개월 기본금리 %s, 최고 %s (%s 공시). 기간별 금리·우대조건·가입방법·이자 계산 예시." % (co, nm, t0, fr(base0), fr(max0), ym(b["dcls_month"])),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), (name, "/product/%s/" % k), (nm, path)], noindex=not active(r)), "0.5", sitemap=active(r))

# ───────── 대출 상품 ─────────
def page_loan_product(k, i):
    r = P[k][i]; b = r["base"]; name = KINDS[k][0]; co = b["kor_co_nm"]; nm = b["fin_prdt_nm"]
    mn, mx, av = loan_rates(r) or (0, 0, 0)
    rows = [[o.get("mrtg_type_nm", "-") if k == "mortgage" else "-", o["rpay_type_nm"], o["lend_rate_type_nm"], fr(o["lend_rate_min"]), fr(o["lend_rate_max"]), fr(o["lend_rate_avg"])] for o in
            sorted(r["options"], key=lambda o: (o.get("mrtg_type_nm", ""), o["rpay_type_nm"], o["lend_rate_type_nm"]))]
    heads = ["담보", "상환 방식", "금리 유형", "최저", "최고", "평균"]
    if k == "rent":
        heads = ["담보"] + heads[1:]
    t_rate = table(heads, rows, (3, 4, 5))
    if k == "mortgage":
        c = [o for o in r["options"] if o["rpay_type_nm"] == "분할상환방식"] or r["options"]
        o = min(c, key=lambda x: x["lend_rate_min"]); lo, hi = o["lend_rate_min"], o["lend_rate_max"]
        ex = table(["3억 원 · 30년 원리금균등", "최저 연 %s" % fr(lo), "최고 연 %s" % fr(hi)], [
            ["월 상환액", kor(L.equal_payment(3 * EOK, lo, 30)["monthly"]), kor(L.equal_payment(3 * EOK, hi, 30)["monthly"])],
            ["총 이자", kor(L.equal_payment(3 * EOK, lo, 30)["interest"]), kor(L.equal_payment(3 * EOK, hi, 30)["interest"])]], (1, 2))
        ex_h = "🧮 상환 예시 (3억 원, 30년)"
        nr = min(RATES, key=lambda x: abs(x - lo)); lk = ("연 %s%% 3억 30년 상환표" % rs(nr), "/loan/3억/%s/30년/" % rs(nr))
        ex_note = "%s 분할상환 옵션의 최저·최고 금리로 계산한 추정이며 금리 유형·담보에 따라 달라집니다." % (o["mrtg_type_nm"])
    else:
        lo, hi = mn, mx
        ex = table(["2억 원 · 이자만 낼 때", "최저 연 %s" % fr(lo), "최고 연 %s" % fr(hi)], [
            ["월 이자", kor(2 * EOK * lo / 1200.0), kor(2 * EOK * hi / 1200.0)], ["1년 이자", kor(2 * EOK * lo / 100.0), kor(2 * EOK * hi / 100.0)]], (1, 2))
        ex_h = "🧮 이자 예시 (2억 원)"
        nr = min(RATES, key=lambda x: abs(x - lo)); lk = ("연 %s%% 2억 이자 계산" % rs(nr), "/interest/2억/%s/" % rs(nr)) if nr in (3.0, 4.0, 5.0, 6.0) else ("대출 이자 계산", "/loan/")
        ex_note = "만기일시상환(이자만 납부) 기준 이자이며 원금 상환은 포함하지 않았습니다."
    rk_rows = []
    for key, (kk, lab, f) in LOAN_RANK.items():
        if kk != k: continue
        rr = loan_rank_rows(key); ids = [x[3] for x in rr]
        if i in ids: rk_rows.append(["%s" % lab, "%d개 중 %d위" % (len(ids), ids.index(i) + 1), '<a href="/rank/%s/%s/">순위 보기</a>' % (k, key)])
    info = table(["항목", "내용"], [["가입 방법", txt(b["join_way"])], ["대출 한도", txt(b["loan_lmt"])], ["중도상환수수료", txt(b["erly_rpay_fee"])], ["대출 부대비용", txt(b["loan_inci_expn"])], ["연체이자율", txt(b["dly_rate"])]])
    sib = [x for x, rr in P[k].items() if rr["base"]["fin_co_no"] == b["fin_co_no"] and x != i and active(rr)][:6]
    sib_rows = [[link(k, x), "%s ~ %s" % (fr(loan_rates(P[k][x])[0]), fr(loan_rates(P[k][x])[1])) if loan_rates(P[k][x]) else "-"] for x in sib]
    body = f"""
<div class="page-head"><h1>{esc(co)} {esc(nm)} 금리 — 연 {fr(mn)} ~ {fr(mx)}</h1><p>{name} · {ym(b['dcls_month'])} 공시 · 출처 {SRC}</p></div>
{'' if active(r) else ended_banner(r)}
<p class="lead"><b>{esc(co)}</b>의 <b>{esc(nm)}</b>({name})은 {ym(b['dcls_month'])} 공시 기준 금리가 연 <b>{fr(mn)} ~ {fr(mx)}</b>(평균 약 {fr(av)})입니다. 아래 표에서 담보·상환 방식·금리 유형별 금리를 확인하세요.</p>
<div class="stat-row"><div class="stat"><small>최저 금리</small><b>{fr(mn)}</b></div><div class="stat"><small>최고 금리</small><b>{fr(mx)}</b></div><div class="stat"><small>평균(공시)</small><b>{fr(av)}</b></div></div>
{ad()}
<h2 class="group-title">📊 유형별 금리</h2>
{t_rate}
<h2 class="group-title">{ex_h}</h2>
{ex}
<p class="note">{ex_note}</p>
<h2 class="group-title">📌 대출 조건과 비용</h2>
{info}
{'<h2 class="group-title">🏆 금리 순위</h2>' + table(['구분', '순위', ''], rk_rows) if rk_rows else ''}
{'<h2 class="group-title">🏦 ' + esc(co) + '의 다른 ' + name + '</h2>' + table(['상품', '금리 범위'], sib_rows) if sib_rows else ''}
{basis_notice(r)}
{chips([(lk[0], lk[1]), ("%s 금리 비교" % name, "/product/%s/" % k), (esc(co) + " 상품 전체", "/company/%s/" % b["fin_co_no"]), ("DSR 대출 한도", "/dsr/"), ("대출 이자 계산기", "/calculator/")])}
"""
    faq = [("%s %s 금리는 얼마인가요?" % (co, nm), "%s 공시 기준 연 %s ~ %s(평균 약 %s)입니다." % (ym(b["dcls_month"]), fr(mn), fr(mx), fr(av))),
           ("중도상환수수료는 얼마인가요?", (b["erly_rpay_fee"] or "공시 없음").strip()[:300]),
           ("대출 한도는 어떻게 되나요?", (b["loan_lmt"] or "공시 없음").strip()[:300])]
    path = ppath(k, i)
    write(path, layout(path, "%s %s 금리 — 연 %s ~ %s" % (co, nm, fr(mn), fr(mx)),
                       "%s %s(%s) 금리 연 %s ~ %s, 평균 %s (%s 공시). 유형별 금리·중도상환수수료·한도·상환 예시." % (co, nm, name, fr(mn), fr(mx), fr(av), ym(b["dcls_month"])),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), (name, "/product/%s/" % k), (nm, path)], noindex=not active(r)), "0.5", sitemap=active(r))

def page_credit_product(i):
    k = "credit"; r = P[k][i]; b = r["base"]; co = b["kor_co_nm"]; nm = b["fin_prdt_nm"]; tn = b["crdt_prdt_type_nm"]
    cr = credit_rates(r); mn, mx, av = cr or (0, 0, 0)
    opts = sorted(r["options"], key=lambda o: ["대출금리", "기준금리", "가산금리", "가감조정금리"].index(o["crdt_lend_rate_type_nm"]) if o["crdt_lend_rate_type_nm"] in ("대출금리", "기준금리", "가산금리", "가감조정금리") else 9)
    heads = ["신용점수 구간"] + [o["crdt_lend_rate_type_nm"] for o in opts]
    rows = [[lab] + [fr(o.get("crdt_grad_" + g)) for o in opts] for g, lab in GRADES]
    rows.append(["<b>평균</b>"] + [fr(o.get("crdt_grad_avg")) for o in opts])
    t_rate = table(heads, rows, tuple(range(1, len(heads))))
    rr = credit_rank_rows([kk for kk, v in CREDIT_RANK.items() if v[0] == tn][0]) if any(v[0] == tn for v in CREDIT_RANK.values()) else []
    ids = [x[3] for x in rr]; key = [kk for kk, v in CREDIT_RANK.items() if v[0] == tn]
    pos = ids.index(i) + 1 if i in ids else None
    sib = [x for x, q in P[k].items() if q["base"]["fin_co_no"] == b["fin_co_no"] and x != i and active(q)][:6]
    sib_rows = [[link(k, x), esc(P[k][x]["base"]["crdt_prdt_type_nm"]), fr((credit_rates(P[k][x]) or (0, 0, 0))[2])] for x in sib]
    interest = L.rnd(1000 * MAN * av / 100.0)
    info = table(["항목", "내용"], [["상품 유형", esc(tn)], ["가입 방법", txt(b["join_way"])], ["신용평가사(CB)", txt(b["cb_name"])], ["공시 시작", ymd(b["dcls_strt_day"])]])
    body = f"""
<div class="page-head"><h1>{esc(co)} {esc(nm)} 금리 — 평균 {fr(av)}</h1><p>{esc(tn)} · {ym(b['dcls_month'])} 공시 · 출처 {SRC}</p></div>
{'' if active(r) else ended_banner(r)}
<p class="lead"><b>{esc(co)}</b>의 <b>{esc(nm)}</b>({esc(tn)})은 신용점수에 따라 금리가 연 <b>{fr(mn)} ~ {fr(mx)}</b>, 평균 <b>{fr(av)}</b>입니다({ym(b['dcls_month'])} 공시). 1천만 원을 평균 금리로 1년 빌리면 이자는 약 {won(interest)}원입니다.{(' 같은 유형 %d개 중 평균 금리 기준 <b>%d위</b>입니다.' % (len(ids), pos)) if pos else ''}</p>
<div class="stat-row"><div class="stat"><small>최저 금리</small><b>{fr(mn)}</b></div><div class="stat"><small>최고 금리</small><b>{fr(mx)}</b></div><div class="stat"><small>평균</small><b>{fr(av)}</b></div></div>
{ad()}
<h2 class="group-title">📊 신용점수 구간별 금리</h2>
{t_rate}
<p class="note">신용점수 구간 표기는 금융감독원 공시 구분을 따랐으며, 금융회사·평가사(CB)에 따라 적용 기준이 다를 수 있습니다. 신용점수가 높을수록 금리가 낮은 것이 일반적입니다.</p>
<h2 class="group-title">📌 상품 정보</h2>
{info}
{'<h2 class="group-title">🏦 ' + esc(co) + '의 다른 신용대출</h2>' + table(['상품', '유형', '평균 금리'], sib_rows, (2,)) if sib_rows else ''}
{basis_notice(r)}
{chips([("신용대출 금리 순위 · %s" % CREDIT_RANK[key[0]][1], "/rank/credit/%s/" % key[0]) if key else ("신용대출 금리 비교", "/product/credit/"), ("신용대출 전체 목록", "/product/credit/"), (esc(co) + " 상품 전체", "/company/%s/" % b["fin_co_no"]), ("1천만원 이자 계산", "/interest/1천/"), ("DSR 대출 한도", "/dsr/")])}
"""
    faq = [("%s %s 금리는 얼마인가요?" % (co, nm), "신용점수에 따라 연 %s ~ %s, 평균 %s입니다(%s 공시)." % (fr(mn), fr(mx), fr(av), ym(b["dcls_month"]))),
           ("신용점수가 낮으면 금리가 얼마나 오르나요?", "이 상품은 구간별 금리가 최저 %s, 최고 %s로 공시되어 있습니다. 구간별 표를 확인하세요." % (fr(mn), fr(mx))),
           ("가입은 어떻게 하나요?", "가입 방법: %s." % ((b["join_way"] or "공시 없음").strip()))]
    path = ppath(k, i)
    write(path, layout(path, "%s %s 금리 — 평균 %s (%s)" % (co, nm, fr(av), tn),
                       "%s %s(%s) 금리 연 %s ~ %s, 평균 %s (%s 공시). 신용점수 구간별 금리표." % (co, nm, tn, fr(mn), fr(mx), fr(av), ym(b["dcls_month"])),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), ("개인신용대출", "/product/credit/"), (nm, path)], noindex=not active(r)), "0.5", sitemap=active(r))

# ───────── 목록·순위·금융사·허브 ─────────
def head_cells(k, i):
    r = P[k][i]
    if k in ("deposit", "saving"):
        return [fr((sav_rate(r, t) or (None, None))[1]) for t in TERMS]
    if k == "credit":
        x = credit_rates(r); return [fr(x[0]) if x else "-", fr(x[2]) if x else "-"]
    x = loan_rates(r); return [fr(x[0]) if x else "-", fr(x[2]) if x else "-"]

def sort_key(k, i):
    r = P[k][i]
    if k in ("deposit", "saving"):
        x = sav_rate(r, feat_term(r)); return (-(x[1] if x else 0), r["base"]["kor_co_nm"])
    x = credit_rates(r) if k == "credit" else loan_rates(r); return (x[2] if x else 99, r["base"]["kor_co_nm"])

def page_kind_index(k):
    name = KINDS[k][0]; ids = sorted([i for i, r in P[k].items() if active(r)], key=lambda i: sort_key(k, i))
    if k in ("deposit", "saving"): heads = ["금융회사", "상품"] + ["%d개월 최고" % t for t in TERMS]; num = (2, 3, 4, 5)
    elif k == "credit": heads = ["금융회사", "상품", "최저", "평균"]; num = (2, 3)
    else: heads = ["금융회사", "상품", "최저", "평균"]; num = (2, 3)
    rows = [[colink(P[k][i]["base"]["fin_co_no"]), link(k, i)] + head_cells(k, i) for i in ids]
    top = ids[0] if ids else None
    topb = P[k][top]["base"] if top else {}
    ranks = {"deposit": ("deposit", 12), "saving": ("saving", 12)}
    rk = [("%s 금리 순위 12개월" % name, "/rank/%s/12/" % k)] if k in ranks else [(v[1] + " 금리 순위", "/rank/%s/%s/" % (k, kk)) for kk, v in ({"credit": CREDIT_RANK}.get(k) or {}).items()]
    if k in ("mortgage", "rent"): rk = [(v[1] + " 금리 순위", "/rank/%s/%s/" % (k, kk)) for kk, v in LOAN_RANK.items() if v[0] == k]
    body = f"""
<div class="page-head"><h1>{name} 금리 비교 — 전체 {len(ids)}개 상품 ({ym(MONTH)} 공시)</h1><p>출처 {SRC} · 금융회사 {len({P[k][i]['base']['fin_co_no'] for i in ids})}곳</p></div>
<p class="lead">금융감독원에 공시된 {name} {len(ids)}개 상품의 금리를 한 표로 모았습니다. {'기간별 최고금리가 높은 순' if k in ('deposit', 'saving') else '금리가 낮은 순'}으로 정렬했고, 상품명을 누르면 우대조건·{'가입 방법' if k in ('deposit', 'saving') else '중도상환수수료·한도'}를 볼 수 있습니다.</p>
{ad()}
{table(heads, rows, num)}
<p class="note">{NOTE}</p>
{chips(rk + [("금융상품 금리 비교 전체", "/product/"), ("계산기", "/calculator/")])}
"""
    faq = [("%s 금리는 어디서 확인하나요?" % name, "금융감독원 ‘금융상품한눈에’ 공시를 매월 정리해 보여드립니다. 가입 전 금융회사 안내를 꼭 확인하세요."),
           ("공시 기준은 언제인가요?", "%s 공시 기준입니다." % ym(MONTH))]
    path = "/product/%s/" % k
    write(path, layout(path, "%s 금리 비교 — %d개 상품 전체 (%s 공시)" % (name, len(ids), ym(MONTH)), "%s %d개 상품의 금리를 한눈에 비교. %s 금융감독원 공시 기준." % (name, len(ids), ym(MONTH)), body, faq,
                       [("홈", "/"), ("금융상품 금리", "/product/"), (name, path)]), "0.8")

def rank_table(rows_html, heads, num): return table(heads, rows_html, num)

def page_rank_savings(k, t, scope):
    name = KINDS[k][0]; sc = {"all": ("전체", None), "bank": ("은행", "020000"), "sb": ("저축은행", "030300")}[scope]
    ids = [x for x in RANK[(k, t)] if sc[1] is None or P[k][x]["base"]["_grp"] == sc[1]]
    if not ids: return
    show = ids[:100]
    rows = [[str(n + 1), colink(P[k][x]["base"]["fin_co_no"]), link(k, x), fr(sav_rate(P[k][x], t)[0]), "<b>%s</b>" % fr(sav_rate(P[k][x], t)[1])] for n, x in enumerate(show)]
    top = P[k][ids[0]]["base"]; tr = sav_rate(P[k][ids[0]], t)
    top3 = ", ".join("%s %s(%s)" % (P[k][x]["base"]["kor_co_nm"], P[k][x]["base"]["fin_prdt_nm"], fr(sav_rate(P[k][x], t)[1])) for x in ids[:3])
    path = "/rank/%s/%d/" % (k, t) + ("" if scope == "all" else scope + "/")
    other = [("전체", "/rank/%s/%d/" % (k, t)), ("은행", "/rank/%s/%d/bank/" % (k, t)), ("저축은행", "/rank/%s/%d/sb/" % (k, t))]
    terms = [("%d개월" % x, "/rank/%s/%d/%s" % (k, x, "" if scope == "all" else scope + "/")) for x in TERMS if x != t]
    body = f"""
<div class="page-head"><h1>{name} 금리 순위 {t}개월 — {sc[0]} 최고 연 {fr(tr[1])}</h1><p>{ym(MONTH)} 공시 · 상위 {len(show)}개 · 출처 {SRC}</p></div>
<p class="lead">{ym(MONTH)} 공시 기준 {sc[0]} {name} {t}개월 상품 {len(ids)}개 가운데 최고금리가 가장 높은 곳은 <b>{esc(top['kor_co_nm'])} {esc(top['fin_prdt_nm'])}</b>(연 {fr(tr[1])}, 기본 {fr(tr[0])})입니다. 상위 3개는 {esc(top3)}입니다. 최고금리는 우대조건을 모두 채웠을 때 받는 금리라서 기본금리와 함께 확인하고, 최소 가입금액·가입 대상 같은 제한은 상품 페이지의 유의사항에서 확인하세요.</p>
{ad()}
{table(['순위', '금융회사', '상품', '기본금리', '최고금리'], rows, (3, 4))}
<p class="note">{NOTE}</p>
{chips([(a, b2) for a, b2 in other if b2 != path] + terms + [("%s 전체 목록" % name, "/product/%s/" % k), ("금융상품 금리 비교", "/product/")])}
"""
    faq = [("%s %s개월 금리가 가장 높은 곳은 어디인가요?" % (name, t), "%s 공시 기준 %s %s(연 %s)입니다." % (ym(MONTH), top["kor_co_nm"], top["fin_prdt_nm"], fr(tr[1]))),
           ("최고금리와 기본금리는 뭐가 다른가요?", "기본금리는 누구나 받는 금리, 최고금리는 급여이체·카드 사용 등 우대조건을 모두 채웠을 때의 금리입니다.")]
    write(path, layout(path, "%s 금리 순위 %d개월 %s — 최고 연 %s (%s)" % (name, t, sc[0], fr(tr[1]), ym(MONTH)), "%s %d개월 %s 금리 순위 TOP %d. 1위 %s %s 연 %s (%s 공시)." % (name, t, sc[0], len(show), top["kor_co_nm"], top["fin_prdt_nm"], fr(tr[1]), ym(MONTH)),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), ("금리 순위", "/rank/"), ("%s %d개월 %s" % (name, t, sc[0]), path)]), "0.8")

def page_rank_loan(k, key):
    kind, lab, _ = LOAN_RANK[key]; name = KINDS[k][0]; rows_ = loan_rank_rows(key)
    if not rows_: return
    show = rows_[:100]
    rows = [[str(n + 1), colink(P[k][x[3]]["base"]["fin_co_no"]), link(k, x[3]), fr(x[4]), fr(x[5]), "<b>%s</b>" % fr(x[6])] for n, x in enumerate(show)]
    top = rows_[0]; tb = P[k][top[3]]["base"]
    path = "/rank/%s/%s/" % (k, key)
    sibs = [(v[1] + " 순위", "/rank/%s/%s/" % (k, kk)) for kk, v in LOAN_RANK.items() if v[0] == k and kk != key]
    body = f"""
<div class="page-head"><h1>{name} 금리 순위 — {lab} 최저 평균 연 {fr(top[6])}</h1><p>{ym(MONTH)} 공시 · 평균 금리 낮은 순 · 출처 {SRC}</p></div>
<p class="lead">{ym(MONTH)} 공시 기준 {name}({lab}) {len(rows_)}개 상품을 평균 금리가 낮은 순으로 정리했습니다. 가장 낮은 곳은 <b>{esc(tb['kor_co_nm'])} {esc(tb['fin_prdt_nm'])}</b>로 평균 연 {fr(top[6])}(최저 {fr(top[4])} ~ 최고 {fr(top[5])})입니다. 개인 신용·소득·담보에 따라 실제 금리는 달라집니다.</p>
{ad()}
{table(['순위', '금융회사', '상품', '최저', '최고', '평균'], rows, (3, 4, 5))}
<p class="note">{NOTE}</p>
{chips(sibs + [("%s 전체 목록" % name, "/product/%s/" % k), ("DSR 대출 한도", "/dsr/"), ("대출 이자 계산", "/loan/")])}
"""
    faq = [("%s %s 금리가 가장 낮은 곳은?" % (name, lab), "%s 공시 기준 %s %s(평균 연 %s)입니다." % (ym(MONTH), tb["kor_co_nm"], tb["fin_prdt_nm"], fr(top[6]))),
           ("평균 금리는 어떻게 정해지나요?", "금융회사가 공시한 직전 기간의 실제 취급 금리 평균이며 없는 경우 최저·최고의 중간값으로 표시했습니다.")]
    write(path, layout(path, "%s 금리 순위 — %s (%s)" % (name, lab, ym(MONTH)), "%s(%s) 금리 순위. 1위 %s %s 평균 연 %s (%s 공시, 상품 %d개)." % (name, lab, tb["kor_co_nm"], tb["fin_prdt_nm"], fr(top[6]), ym(MONTH), len(rows_)),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), ("금리 순위", "/rank/"), ("%s %s" % (name, lab), path)]), "0.8")

def page_rank_credit(key):
    tn, lab = CREDIT_RANK[key]; rows_ = credit_rank_rows(key)
    if not rows_: return
    show = rows_[:100]; k = "credit"
    rows = [[str(n + 1), colink(P[k][x[3]]["base"]["fin_co_no"]), link(k, x[3]), fr(x[4]), fr(x[5]), "<b>%s</b>" % fr(x[6])] for n, x in enumerate(show)]
    top = rows_[0]; tb = P[k][top[3]]["base"]; path = "/rank/credit/%s/" % key
    sibs = [(v[1] + " 순위", "/rank/credit/%s/" % kk) for kk, v in CREDIT_RANK.items() if kk != key]
    body = f"""
<div class="page-head"><h1>{lab} 금리 순위 — 최저 평균 연 {fr(top[6])}</h1><p>{ym(MONTH)} 공시 · 평균 금리 낮은 순 · 출처 {SRC}</p></div>
<p class="lead">{ym(MONTH)} 공시 기준 {lab} {len(rows_)}개 상품을 평균 금리가 낮은 순으로 정리했습니다. 가장 낮은 곳은 <b>{esc(tb['kor_co_nm'])} {esc(tb['fin_prdt_nm'])}</b>(평균 연 {fr(top[6])})입니다. 신용점수 구간별 금리는 상품명을 눌러 확인하세요. 최저·최고는 구간별 금리 중 가장 낮은 값과 높은 값입니다.</p>
{ad()}
{table(['순위', '금융회사', '상품', '최저', '최고', '평균'], rows, (3, 4, 5))}
<p class="note">{NOTE}</p>
{chips(sibs + [("개인신용대출 전체 목록", "/product/credit/"), ("1천만원 이자 계산", "/interest/1천/"), ("DSR 대출 한도", "/dsr/")])}
"""
    faq = [("%s 금리가 가장 낮은 곳은?" % lab, "%s 공시 기준 %s %s(평균 연 %s)입니다." % (ym(MONTH), tb["kor_co_nm"], tb["fin_prdt_nm"], fr(top[6]))), ("신용점수가 낮으면 금리가 어떻게 되나요?", "구간이 낮을수록 금리가 높아집니다. 상품별 구간 금리표를 확인하세요.")]
    write(path, layout(path, "%s 금리 순위 — 평균 최저 연 %s (%s)" % (lab, fr(top[6]), ym(MONTH)), "%s 금리 순위. 1위 %s %s 평균 연 %s (%s 공시, 상품 %d개)." % (lab, tb["kor_co_nm"], tb["fin_prdt_nm"], fr(top[6]), ym(MONTH), len(rows_)),
                       body, faq, [("홈", "/"), ("금융상품 금리", "/product/"), ("금리 순위", "/rank/"), (lab, path)]), "0.8")

def page_rank_hub():
    items = []
    for k in ("deposit", "saving"):
        for t in TERMS:
            ids = RANK[(k, t)]
            if ids:
                b = P[k][ids[0]]["base"]; items.append(['<a href="/rank/%s/%d/">%s %d개월</a>' % (k, t, KINDS[k][0], t), esc(b["kor_co_nm"]), fr(sav_rate(P[k][ids[0]], t)[1])])
    loans = []
    for key, (kk, lab, _) in LOAN_RANK.items():
        rr = loan_rank_rows(key)
        if rr: loans.append(['<a href="/rank/%s/%s/">%s · %s</a>' % (kk, key, KINDS[kk][0], lab), esc(P[kk][rr[0][3]]["base"]["kor_co_nm"]), fr(rr[0][6])])
    for key, (tn, lab) in CREDIT_RANK.items():
        rr = credit_rank_rows(key)
        if rr: loans.append(['<a href="/rank/credit/%s/">%s</a>' % (key, lab), esc(P["credit"][rr[0][3]]["base"]["kor_co_nm"]), fr(rr[0][6])])
    body = f"""
<div class="page-head"><h1>금리 순위 — 예금·적금·대출 금리 TOP ({ym(MONTH)} 공시)</h1><p>출처 {SRC}</p></div>
<p class="lead">예금·적금은 최고금리가 높은 순, 대출은 평균 금리가 낮은 순으로 순위를 매겼습니다. 순위를 누르면 상위 100개 상품이 나옵니다.</p>
{ad()}
<h2 class="group-title">💰 예금·적금 (1위 최고금리)</h2>
{table(['순위표', '1위 금융회사', '최고금리'], items, (2,))}
<h2 class="group-title">🏦 대출 (1위 평균 금리)</h2>
{table(['순위표', '1위 금융회사', '평균 금리'], loans, (2,))}
<p class="note">{NOTE}</p>
{chips([("금융상품 금리 비교", "/product/"), ("대출 이자 계산", "/loan/"), ("예금 이자", "/deposit/"), ("적금 이자", "/savings/")])}
"""
    faq = [("금리 순위는 어떤 기준인가요?", "예금·적금은 공시된 최고(우대 포함) 금리, 대출은 공시된 평균 금리 기준입니다."), ("순위는 얼마나 자주 바뀌나요?", "금융감독원 공시가 매월 갱신될 때마다 바뀝니다.")]
    write("/rank/", layout("/rank/", "금리 순위 — 예금·적금·대출 금리 TOP (%s)" % ym(MONTH), "예금·적금 최고금리 순위와 주택담보·전세·신용대출 금리 순위. %s 금융감독원 공시 기준." % ym(MONTH), body, faq, [("홈", "/"), ("금리 순위", "/rank/")]), "0.9")

def page_company(code):
    c = CO[code]; sections = []; cnt = 0; best = []
    for k in KINDS:
        ids = sorted([i for i, r in P[k].items() if r["base"]["fin_co_no"] == code and active(r)], key=lambda i: sort_key(k, i))
        if not ids: continue
        cnt += len(ids)
        if k in ("deposit", "saving"):
            rows = [[link(k, i)] + head_cells(k, i) for i in ids]; t = table(["상품"] + ["%d개월 최고" % x for x in TERMS], rows, (1, 2, 3, 4))
            x = sav_rate(P[k][ids[0]], feat_term(P[k][ids[0]])); best.append("%s 최고 %s" % (KINDS[k][0], fr(x[1] if x else None)))
        else:
            rows = [[link(k, i)] + head_cells(k, i) for i in ids]; t = table(["상품", "최저", "평균"], rows, (1, 2))
            x = (credit_rates if k == "credit" else loan_rates)(P[k][ids[0]]); best.append("%s 최저 %s" % (KINDS[k][0], fr(x[0] if x else None)))
        sections.append('<h2 class="group-title">%s (%d개)</h2>%s' % (KINDS[k][0], len(ids), t))
    if not cnt: return
    path = "/company/%s/" % code
    body = f"""
<div class="page-head"><h1>{esc(c['name'])} 예금·적금·대출 금리 — 공시 상품 {cnt}개</h1><p>{GRP.get(c['grp'], '금융회사')} · {ym(MONTH)} 공시 · 출처 {SRC}</p></div>
<p class="lead"><b>{esc(c['name'])}</b>({GRP.get(c['grp'], '금융회사')})이 {ym(MONTH)}에 공시한 상품은 {cnt}개입니다. {esc(', '.join(best))}. 상품명을 누르면 우대조건과 상세 금리를 볼 수 있습니다.</p>
{ad()}
{''.join(sections)}
<p class="note">{NOTE}</p>
{chips([("금융상품 금리 비교", "/product/"), ("금리 순위", "/rank/"), ("대출 이자 계산", "/loan/")])}
"""
    faq = [("%s의 예금·적금·대출 금리는 얼마인가요?" % c["name"], "%s 공시 기준 %s." % (ym(MONTH), ", ".join(best))), ("공시 정보는 언제 갱신되나요?", "금융감독원 공시가 매월 갱신될 때 함께 반영합니다.")]
    write(path, layout(path, "%s 금리 — 예금·적금·대출 상품 %d개 (%s)" % (c["name"], cnt, ym(MONTH)), "%s 공시 상품 %d개의 금리 비교. %s. %s 금융감독원 공시." % (c["name"], cnt, ", ".join(best), ym(MONTH)), body, faq,
                       [("홈", "/"), ("금융상품 금리", "/product/"), (c["name"], path)]), "0.6")

def page_company_index():
    groups = {}
    for code, c in CO.items():
        n = sum(1 for k in KINDS for r in P[k].values() if r["base"]["fin_co_no"] == code and active(r))
        if n: groups.setdefault(c["grp"], []).append((c["name"], code, n))
    secs = ""
    for g in GRP:
        if g in groups:
            secs += '<h2 class="group-title">%s (%d곳)</h2>%s' % (GRP[g], len(groups[g]), chips([("%s · %d개" % (n, cnt), "/company/%s/" % code) for n, code, cnt in sorted(groups[g])]))
    total = sum(len(v) for v in groups.values())
    body = f"""
<div class="page-head"><h1>금융회사별 금리 — 예금·적금·대출 공시 상품</h1><p>{total}곳 · {ym(MONTH)} 공시</p></div>
<p class="lead">금융감독원에 상품을 공시한 은행·저축은행·보험사·여신전문금융회사 {total}곳을 모았습니다. 회사명을 누르면 그 회사의 예금·적금·대출 금리를 볼 수 있습니다.</p>
{ad()}
{secs}
<p class="note">{NOTE}</p>
"""
    write("/company/", layout("/company/", "금융회사별 금리 비교 — 은행·저축은행 예금 적금 대출 (%s)" % ym(MONTH), "은행·저축은행·보험사 %d곳의 예금·적금·대출 공시 금리를 회사별로 확인. %s 금융감독원 공시." % (total, ym(MONTH)), body, None, [("홈", "/"), ("금융회사별", "/company/")]), "0.7")

def page_product_hub():
    cards = ""
    for k in KINDS:
        ids = [i for i, r in P[k].items() if active(r)]
        cards += '<a class="card" href="/product/%s/"><b>%s</b><span>%d개 상품 비교</span></a>' % (k, KINDS[k][0], len(ids))
    body = f"""
<div class="page-head"><h1>금융상품 금리 비교 — 예금·적금·주택담보·전세·신용대출</h1><p>{ym(MONTH)} 금융감독원 공시 · 매월 갱신</p></div>
<p class="lead">금융감독원 ‘금융상품한눈에’에 공시된 예금·적금·대출 상품 {sum(1 for k in KINDS for r in P[k].values() if active(r)):,}개의 금리를 정리했습니다. 종류를 고르거나 <a href="/rank/">금리 순위</a>, <a href="/company/">금융회사별</a>로 찾아보세요.</p>
{ad()}
<div class="card-grid">{cards}<a class="card" href="/rank/"><b>🏆 금리 순위</b><span>예금·적금·대출 TOP</span></a><a class="card" href="/company/"><b>🏦 금융회사별</b><span>은행·저축은행·보험사</span></a></div>
<p class="note">{NOTE}</p>
{chips([("대출 이자 계산", "/loan/"), ("DSR 대출 한도", "/dsr/"), ("이자 계산", "/interest/"), ("계산기", "/calculator/")])}
"""
    faq = [("금융상품 금리는 어디서 가져오나요?", "금융감독원 금융상품한눈에 오픈API 공시 데이터를 매월 반영합니다."), ("금리가 실제와 다를 수 있나요?", "공시 시점의 금리이며 실제 적용 금리는 가입 시점과 개인 조건에 따라 다릅니다.")]
    write("/product/", layout("/product/", "금융상품 금리 비교 — 예금 적금 주택담보대출 전세대출 신용대출 (%s)" % ym(MONTH), "예금·적금·주택담보·전세·신용대출 금리를 금융감독원 공시로 비교. %s 기준 전 금융회사." % ym(MONTH), body, faq, [("홈", "/"), ("금융상품 금리", "/product/")]), "0.9")

def main():
    load(); build_rank()
    for k in KINDS:
        page_kind_index(k)
        for i, r in P[k].items():
            if k in ("deposit", "saving"): page_savings_product(k, i)
            elif k == "credit": page_credit_product(i)
            else: page_loan_product(k, i)
    for k in ("deposit", "saving"):
        for t in TERMS:
            for sc in ("all", "bank", "sb"): page_rank_savings(k, t, sc)
    for key in LOAN_RANK: page_rank_loan(LOAN_RANK[key][0], key)
    for key in CREDIT_RANK: page_rank_credit(key)
    page_rank_hub()
    for code in CO: page_company(code)
    page_company_index(); page_product_hub()
    return MONTH
