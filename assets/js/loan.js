/* 우아대출 계산기 — scripts/loan.py 와 같은 식 */
var LN = (function () {
  function rnd(x) { return Math.round(x); }
  function pmt(P, rate, years) { var n = Math.floor(years * 12), r = rate / 1200; return r === 0 ? rnd(P / n) : rnd(P * r / (1 - Math.pow(1 + r, -n))); }
  function equalPayment(P, rate, years) { var n = Math.floor(years * 12), m = pmt(P, rate, years); return { monthly: m, total: m * n, interest: m * n - P, n: n }; }
  function equalPrincipal(P, rate, years) {
    var n = Math.floor(years * 12), r = rate / 1200, interest = rnd(P * r * (n + 1) / 2);
    return { first: rnd(P / n + P * r), last: rnd(P / n + (P / n) * r), interest: interest, total: P + interest, n: n };
  }
  function bullet(P, rate, years) { var n = Math.floor(years * 12), m = rnd(P * rate / 1200); return { monthly: m, interest: m * n, total: P + m * n, n: n }; }
  function dsrMax(income, rate, years, dsr) {
    dsr = dsr || 0.40; var n = Math.floor(years * 12), r = rate / 1200, mp = income * dsr / 12;
    return r === 0 ? Math.floor(mp * n) : rnd(mp * (1 - Math.pow(1 + r, -n)) / r / 10000) * 10000;
  }
  function deposit(P, rate, months) { months = months || 12; var g = rnd(P * rate / 100 * months / 12), t = rnd(g * 0.154); return { gross: g, tax: t, net: g - t }; }
  function savings(m, rate, months) { months = months || 12; var g = rnd(m * (rate / 1200) * months * (months + 1) / 2), t = rnd(g * 0.154); return { principal: m * months, gross: g, tax: t, net: g - t, total: m * months + g - t }; }
  return { pmt: pmt, equalPayment: equalPayment, equalPrincipal: equalPrincipal, bullet: bullet, dsrMax: dsrMax, deposit: deposit, savings: savings };
})();

(function () {
  if (typeof document === 'undefined') return;
  function w(x) { return Math.round(x).toLocaleString('ko-KR'); }
  function $(i) { return document.getElementById(i); }
  if ($('l-go')) $('l-go').onclick = function () {
    var P = +$('l-p').value, rate = +$('l-r').value, y = +$('l-y').value, a = LN.equalPayment(P, rate, y), b = LN.equalPrincipal(P, rate, y), c = LN.bullet(P, rate, y);
    $('l-out').innerHTML = '<b>원리금균등 월 ' + w(a.monthly) + '원</b> · 총이자 ' + w(a.interest) + '원<br>원금균등 첫 달 ' + w(b.first) + '원(마지막 ' + w(b.last) + '원) · 총이자 ' + w(b.interest) + '원<br>만기일시 월이자 ' + w(c.monthly) + '원 · 총이자 ' + w(c.interest) + '원';
  };
  if ($('d-go')) $('d-go').onclick = function () {
    var inc = +$('d-i').value, rate = +$('d-r').value, y = +$('d-y').value, add = +$('d-s').value;
    $('d-out').innerHTML = '<b>대출 가능 약 ' + w(LN.dsrMax(inc, rate + add, y)) + '원</b> (DSR 40%, 금리 ' + (rate + add).toFixed(2) + '% 원리금균등 ' + y + '년)';
  };
  if ($('e-go')) $('e-go').onclick = function () {
    var r = LN.deposit(+$('e-p').value, +$('e-r').value, +$('e-m').value);
    $('e-out').innerHTML = '<b>세후 이자 약 ' + w(r.net) + '원</b><br>세전 ' + w(r.gross) + ' · 이자소득세 15.4% ' + w(r.tax) + ' (원)';
  };
  if ($('s-go')) $('s-go').onclick = function () {
    var r = LN.savings(+$('s-p').value, +$('s-r').value, +$('s-m').value);
    $('s-out').innerHTML = '<b>만기 수령액 약 ' + w(r.total) + '원</b> (세후 이자 ' + w(r.net) + '원)<br>원금 ' + w(r.principal) + ' · 세전 이자 ' + w(r.gross) + ' · 세금 ' + w(r.tax) + ' (원)';
  };
})();
if (typeof module !== 'undefined') module.exports = LN;
