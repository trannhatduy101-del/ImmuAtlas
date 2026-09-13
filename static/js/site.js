/* ImmuAtlas — shared interaction layer.
 *
 * One file, loaded on every page from base.html. Each behaviour finds its own
 * elements and does nothing if they are absent, so the same script serves the
 * landing, the coverage table, and the improvement ranking without per-page
 * wiring. Everything is progressive enhancement: with this file removed (or
 * with prefers-reduced-motion), the pages are complete, the numbers are the
 * server-rendered values, and the charts are static.
 */
(function () {
  var reduce = window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;

  // --- number formatters, mirroring db.py so a count-up reads the same ---
  function fmtInt(n) { return Math.round(n).toLocaleString('en-US'); }
  function fmtBig(n) {
    n = Math.abs(n);
    var units = [[1e12, 'trillion'], [1e9, 'billion'], [1e6, 'million']];
    for (var i = 0; i < units.length; i++) {
      if (n >= units[i][0]) { return (n / units[i][0]).toFixed(2) + ' ' + units[i][1]; }
    }
    return fmtInt(n);
  }
  function fmtPct(n) { return n.toFixed(1) + '%'; }
  function render(kind, n) {
    return kind === 'big' ? fmtBig(n) : kind === 'pct' ? fmtPct(n) : fmtInt(n);
  }

  // --- count a figure up from 0, then snap to the exact server-rendered text ---
  function countUp(el) {
    var target = parseFloat(el.getAttribute('data-to'));
    var kind = el.getAttribute('data-kind') || 'int';
    var finalText = el.textContent;
    if (isNaN(target)) { return; }
    var dur = 900, start = null;
    el.textContent = render(kind, 0);
    function step(ts) {
      if (!start) { start = ts; }
      var p = Math.min(1, (ts - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = render(kind, target * eased);
      if (p < 1) { requestAnimationFrame(step); }
      else { el.textContent = finalText; }
    }
    requestAnimationFrame(step);
  }

  function initCounts() {
    var figs = [].slice.call(document.querySelectorAll('.lp-count'));
    if (reduce || !hasIO || !figs.length) { return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { countUp(e.target); io.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    figs.forEach(function (f) { io.observe(f); });
  }

  // --- trend chart: self-draw on view + a tooltip on hover/focus (landing) ---
  function initChart() {
    var svg = document.querySelector('.lp-trend');
    if (!svg) { return; }
    var fig = svg.closest('.lp-chart');
    var tip = fig && fig.querySelector('.lp-tip');
    var pts = [].slice.call(svg.querySelectorAll('.lp-pt'));

    function show(pt) {
      if (!tip) { return; }
      tip.innerHTML = '<strong>' + pt.getAttribute('data-year') + '</strong> &middot; '
        + pt.getAttribute('data-cov') + ' coverage &middot; '
        + pt.getAttribute('data-report') + ' reporting &middot; '
        + pt.getAttribute('data-cases') + ' cases';
      tip.hidden = false;
      var r = pt.getBoundingClientRect(), f = fig.getBoundingClientRect();
      tip.style.left = (r.left - f.left + r.width / 2) + 'px';
      tip.style.top = (r.top - f.top) + 'px';
    }
    function hide() { if (tip) { tip.hidden = true; } }

    pts.forEach(function (pt) {
      pt.addEventListener('mouseenter', function () { show(pt); });
      pt.addEventListener('mouseleave', hide);
      pt.addEventListener('focus', function () { show(pt); });
      pt.addEventListener('blur', hide);
    });

    if (!reduce && hasIO) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { svg.classList.add('is-draw'); io.unobserve(e.target); }
        });
      }, { threshold: 0.3 });
      io.observe(svg);
    }
  }

  // --- one orchestrated entrance; default visible, only pre-hide once JS runs ---
  function initReveal() {
    var els = [].slice.call(document.querySelectorAll('.lp-reveal'));
    if (reduce || !hasIO || !els.length) { return; }
    els.forEach(function (el) { el.classList.add('lp-anim'); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  // --- coverage region bars grow from 0 to their width on first paint (2A) ---
  function initBars() {
    var bars = [].slice.call(document.querySelectorAll('.bar-fill'));
    if (reduce || !bars.length) { return; }
    bars.forEach(function (b) {
      var w = b.style.width;
      if (!w) { return; }
      b.style.width = '0%';
      b.getBoundingClientRect();                 // force a reflow before the change
      requestAnimationFrame(function () { b.style.width = w; });
    });
  }

  function boot() { initCounts(); initChart(); initReveal(); initBars(); }
  if (document.readyState !== 'loading') { boot(); }
  else { document.addEventListener('DOMContentLoaded', boot); }
})();
