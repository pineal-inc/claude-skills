/* pineal-slide-html / viewer
   スクロール確認・プレゼン表示・印刷だけを担当する 100 行程度のスクリプト。
   スライドの内容には触らない。読み込むだけで動く。 */
(function () {
  var deck, slides = [], cur = 0;

  function zoom() {
    var z;
    if (document.body.classList.contains('present')) {
      z = Math.min((innerWidth - 24) / 1280, (innerHeight - 24) / 720);
    } else {
      z = Math.min(1, (innerWidth - 90) / 1280);
    }
    document.documentElement.style.setProperty('--zoom', Math.max(0.2, z));
  }

  function show(i) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach(function (s, n) { s.classList.toggle('current', n === cur); });
    var c = document.querySelector('.deck-bar .count');
    if (c) c.textContent = (cur + 1) + ' / ' + slides.length;
    if (!document.body.classList.contains('present')) {
      slides[cur].scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
  }

  function present(on) {
    document.body.classList.toggle('present', on);
    var btn = document.querySelector('.deck-bar [data-a="mode"]');
    if (btn) btn.textContent = on ? '一覧' : 'プレゼン';
    zoom(); show(cur);
  }

  function bar() {
    var b = document.createElement('div');
    b.className = 'deck-bar no-print';
    b.innerHTML =
      '<button data-a="prev">←</button>' +
      '<span class="count"></span>' +
      '<button data-a="next">→</button>' +
      '<button data-a="mode">プレゼン</button>' +
      '<button data-a="print">PDF</button>';
    b.addEventListener('click', function (e) {
      var a = e.target.getAttribute('data-a');
      if (a === 'prev') show(cur - 1);
      if (a === 'next') show(cur + 1);
      if (a === 'print') print();
      if (a === 'mode') present(!document.body.classList.contains('present'));
    });
    document.body.appendChild(b);
  }

  function init() {
    deck = document.querySelector('.deck');
    if (!deck) return;
    document.body.classList.add('deck-view');
    slides = [].slice.call(deck.querySelectorAll(':scope > .slide'));
    slides.forEach(function (s, n) { s.setAttribute('data-n', n + 1); });
    bar(); zoom(); show(0);
    addEventListener('resize', zoom);
    addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { show(cur + 1); e.preventDefault(); }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { show(cur - 1); e.preventDefault(); }
      else if (e.key === 'p') { present(!document.body.classList.contains('present')); }
      else if (e.key === 'f') { document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); }
      else if (e.key === 'Escape') { present(false); }
    });
  }

  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', init);
  else init();
})();
