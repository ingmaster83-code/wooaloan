import json, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import loan as L
rows = json.load(open(here / "_calc_js.json", encoding="utf-8"))
bad = 0
for kind, p, r, y, js in rows:
    if kind == "pmt": py = L.equal_payment(p, r, y)["monthly"]
    elif kind == "eq": py = L.equal_principal(p, r, y)["interest"]
    elif kind == "bl": py = L.bullet(p, r, y)["interest"]
    elif kind == "dsr": py = L.dsr_max(p, r, y)
    elif kind == "dep": py = L.deposit(p, r, y)["net"]
    else: py = L.savings(p, r, y)["total"]
    if int(py) != int(js):
        bad += 1
        if bad < 6: print("불일치", kind, p, r, y, py, js)
print("py vs js 불일치", bad, "/", len(rows))
