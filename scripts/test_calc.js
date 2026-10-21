const fs = require('fs'), path = require('path');
const LN = require(path.join(__dirname, '..', 'assets', 'js', 'loan.js'));
const out = [];
for (const P of [1e7, 3e7, 5e7, 1e8, 1.5e8, 3e8, 5e8, 1e9]) for (const r of [0, 2.5, 3.65, 4, 5.5, 7]) for (const y of [1, 3, 5, 10, 20, 30, 40]) {
  out.push(['pmt', P, r, y, LN.equalPayment(P, r, y).monthly]);
  out.push(['eq', P, r, y, LN.equalPrincipal(P, r, y).interest]);
  out.push(['bl', P, r, y, LN.bullet(P, r, y).interest]);
  out.push(['dsr', P / 10, r, y, LN.dsrMax(P / 10, r, y)]);
}
for (const P of [1e6, 1e7, 3e7]) for (const r of [2.5, 3.5, 5]) for (const m of [6, 12, 24, 36]) {
  out.push(['dep', P, r, m, LN.deposit(P, r, m).net]);
  out.push(['sav', P / 20, r, m, LN.savings(P / 20, r, m).total]);
}
fs.writeFileSync(path.join(__dirname, '_calc_js.json'), JSON.stringify(out));
console.log('cases', out.length);
