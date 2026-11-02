# -*- coding: utf-8 -*-
"""금융감독원 '금융상품한눈에' 오픈API 수집 -> data/finlife/{kind}.json

종류: deposit(정기예금) saving(적금) mortgage(주택담보대출) rent(전세자금대출) credit(개인신용대출)
인증키: 환경변수 FINLIFE_AUTH 또는 ../_newdata/finlife.env (git 밖). 키를 코드·저장소에 넣지 말 것.

상품 페이지 주소를 안정적으로 유지하려고(우아장학금 slug 붕괴 사고 참고) 상품은 ID로 누적 보관한다:
 - ID = 금융회사코드-상품코드 (신용대출은 상품유형 코드를 더함). 공백 등은 _ 로 바꾼다.
 - 이번 수집에서 사라진 상품도 지우지 않고 last_seen(마지막 공시월)을 그대로 둔다 -> 페이지는 "공시 종료"로 표시.
사용: python scripts/fetch_finlife.py
"""
import json, os, re, sys, time, urllib.request, pathlib

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "finlife"
OUT.mkdir(parents=True, exist_ok=True)

def load_key():
    k = os.environ.get("FINLIFE_AUTH")
    if k: return k.strip()
    for p in (ROOT.parent / "_newdata" / "finlife.env", ROOT / ".finlife.env"):
        if p.exists():
            return p.read_text(encoding="utf-8").split("=", 1)[1].strip()
    sys.exit("FINLIFE_AUTH 환경변수 또는 _newdata/finlife.env 가 필요합니다(키를 코드에 넣지 마세요).")

KEY = load_key()
APIS = {"deposit": "depositProductsSearch", "saving": "savingProductsSearch", "mortgage": "mortgageLoanProductsSearch",
        "rent": "rentHouseLoanProductsSearch", "credit": "creditLoanProductsSearch"}
GROUPS = {"020000": "은행", "030300": "저축은행", "050000": "보험", "030200": "여신전문", "060000": "금융투자"}

def call(api, grp, page):
    u = f"http://finlife.fss.or.kr/finlifeapi/{api}.json?auth={KEY}&topFinGrpNo={grp}&pageNo={page}"
    err = None
    for _ in range(3):
        try: return json.loads(urllib.request.urlopen(u, timeout=40).read().decode("utf-8"))["result"]
        except Exception as e: err = e; time.sleep(2)
    raise err

def pid(kind, b):
    s = "%s-%s" % (b["fin_co_no"], b["fin_prdt_cd"])
    if kind == "credit": s += "-" + str(b.get("crdt_prdt_type", ""))
    return re.sub(r"[^0-9A-Za-z_\-]", "_", s)

def fetch(kind, api):
    bases, opts = [], []
    for g in GROUPS:
        r = call(api, g, 1)
        if r.get("err_cd") != "000":
            print("  ", kind, g, r.get("err_cd"), r.get("err_msg")); continue
        mp = int(r.get("max_page_no") or 1); b, o = list(r.get("baseList") or []), list(r.get("optionList") or [])
        for p in range(2, mp + 1):
            rr = call(api, g, p); b += rr.get("baseList") or []; o += rr.get("optionList") or []
        for x in b: x["_grp"] = g
        bases += b; opts += o
    return bases, opts

def main():
    for kind, api in APIS.items():
        bases, opts = fetch(kind, api)
        path = OUT / (kind + ".json")
        old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"products": {}}
        prods = old["products"]
        by_opt = {}
        for o in opts:
            k = (o["fin_co_no"], o["fin_prdt_cd"], str(o.get("crdt_prdt_type", "")) if kind == "credit" else "")
            by_opt.setdefault(k, []).append(o)
        month = max((b["dcls_month"] for b in bases), default=old.get("month", ""))
        new = 0
        for b in bases:
            i = pid(kind, b)
            k = (b["fin_co_no"], b["fin_prdt_cd"], str(b.get("crdt_prdt_type", "")) if kind == "credit" else "")
            if i not in prods: new += 1
            prods[i] = {"base": b, "options": by_opt.get(k, []), "last_seen": b["dcls_month"]}
        ended = sum(1 for p in prods.values() if p["last_seen"] != month)
        path.write_text(json.dumps({"month": month, "products": prods}, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"{kind:9s} 이번 수집 {len(bases):4d}건 (신규 {new}) / 누적 {len(prods)}건 / 공시 종료 {ended}건 / 기준월 {month}")

if __name__ == "__main__":
    main()
