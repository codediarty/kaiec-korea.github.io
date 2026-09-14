/* 한국AI윤리위원회 (KAIEC) : main.js */
(function () {
  'use strict';

  /* 1. 모바일 네비게이션 -------------------------------------------------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* 2. 현재 페이지 메뉴 활성화 -------------------------------------------- */
  var here = location.pathname.replace(/index\.html$/, '');
  if (here === '') here = '/';
  document.querySelectorAll('.nav > a').forEach(function (a) {
    var href = a.getAttribute('href') || '';
    if (href === here) a.classList.add('is-active');
    if (here.indexOf('/news/') === 0 && href === '/news/') a.classList.add('is-active');
  });

  /* 3. 스크롤 등장 애니메이션 --------------------------------------------- */
  var targets = document.querySelectorAll('.reveal');
  if (targets.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add('is-in');
            io.unobserve(en.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
      targets.forEach(function (t, i) {
        t.style.transitionDelay = (i % 4) * 70 + 'ms';
        io.observe(t);
      });
    } else {
      targets.forEach(function (t) { t.classList.add('is-in'); });
    }
  }

  /* 4. 푸터 연도 자동 갱신 ------------------------------------------------ */
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  /* 5. 숫자 카운트업 ------------------------------------------------------ */
  var nums = document.querySelectorAll('[data-count]');
  if (nums.length && 'IntersectionObserver' in window) {
    var nio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        var end = parseFloat(el.getAttribute('data-count'));
        var suffix = el.getAttribute('data-suffix') || '';
        var start = null, dur = 1100;
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(end * eased).toLocaleString('ko-KR') + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
        nio.unobserve(el);
      });
    }, { threshold: 0.4 });
    nums.forEach(function (n) { nio.observe(n); });
  }

  /* 6. 접수 마감 D-day (data-deadline="YYYY-MM-DD" 요소 안의 [data-dday]에 표시, 마감 후엔 비움) ---- */
  document.querySelectorAll('[data-deadline]').forEach(function (box) {
    var out = box.querySelector('[data-dday]');
    if (!out) return;
    var end = new Date(box.getAttribute('data-deadline') + 'T23:59:59+09:00');
    var days = Math.ceil((end - new Date()) / 86400000);
    out.textContent = days > 0 ? 'D-' + days : (days === 0 ? 'D-DAY' : '');
  });

  /* 7. 하단 고정 접수 바: 첫 화면을 지나면 나타나고, 배너·푸터가 보이면 숨김 ----------------- */
  var sticky = document.getElementById('stickyCta');
  if (sticky) {
    var blockers = document.querySelectorAll('.site-footer, .cta-band, .gform-done');
    var visible = [];
    function sync() {
      var on = window.pageYOffset > 520 && visible.length === 0;
      sticky.classList.toggle('is-on', on);
      sticky.setAttribute('aria-hidden', on ? 'false' : 'true');
    }
    if ('IntersectionObserver' in window && blockers.length) {
      var sio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          var at = visible.indexOf(en.target);
          if (en.isIntersecting && at < 0) visible.push(en.target);
          if (!en.isIntersecting && at >= 0) visible.splice(at, 1);
        });
        sync();
      }, { threshold: 0.05 });
      blockers.forEach(function (b) { sio.observe(b); });
    }
    window.addEventListener('scroll', sync, { passive: true });
    sync();
  }

  /* 아이콘은 빌드 시 SVG로 HTML에 직접 삽입되므로 외부 스크립트가 필요 없습니다. */
})();
