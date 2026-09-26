/* 한국AI윤리위원회 (KAIEC) : main.js */
(function () {
  'use strict';

  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');

  /* 1. 모바일 네비게이션 -------------------------------------------------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav');
  if (toggle && nav) {
    function setNavOpen(open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
    }
    toggle.addEventListener('click', function () {
      setNavOpen(!nav.classList.contains('is-open'));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a')) setNavOpen(false);
    });
    document.addEventListener('click', function (e) {
      if (!nav.contains(e.target) && !toggle.contains(e.target)) setNavOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        setNavOpen(false);
        toggle.focus();
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
    if ('IntersectionObserver' in window && !(reducedMotion && reducedMotion.matches)) {
      try {
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
          t.classList.add('is-ready');
        });
      } catch (error) {
        if (io) io.disconnect();
        targets.forEach(function (t) { t.classList.remove('is-ready'); });
      }
    } else {
      targets.forEach(function (t) { t.classList.add('is-in'); });
    }
  }

  /* 4. 푸터 연도 자동 갱신 ------------------------------------------------ */
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  /* 5. 숫자 카운트업 ------------------------------------------------------ */
  var nums = document.querySelectorAll('[data-count]');
  if (nums.length && 'IntersectionObserver' in window && !(reducedMotion && reducedMotion.matches)) {
    var nio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        var end = parseFloat(el.getAttribute('data-count'));
        var suffix = el.getAttribute('data-suffix') || '';
        var start = null, dur = 1100;
        function step(ts) {
          if (!start) start = ts;
          var p = reducedMotion && reducedMotion.matches ? 1 : Math.min((ts - start) / dur, 1);
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

  /* 6. (2026.09.23 삭제) 접수 마감 D-day 표시: 기수·마감 표기를 사이트에서 쓰지 않기로 해 코드를 뺐습니다. */

  /* 7. 하단 고정 접수 바: 첫 화면을 지나면 나타나고, 배너·푸터가 보이면 숨김 ----------------- */
  var sticky = document.getElementById('stickyCta');
  if (sticky) {
    var blockers = document.querySelectorAll('.site-footer, .cta-band, .aiep-final, .gform-done');
    var visible = [];
    var stickyControls = Array.prototype.map.call(
      sticky.querySelectorAll('a[href], button, input, select, textarea, [tabindex]'),
      function (el) { return { el: el, tabindex: el.getAttribute('tabindex') }; }
    );
    var stickyOn = null;
    function sync() {
      var on = window.pageYOffset > 520 && visible.length === 0;
      if (on === stickyOn) return;
      stickyOn = on;
      sticky.classList.toggle('is-on', on);
      if (on) sticky.removeAttribute('inert');
      else sticky.setAttribute('inert', '');
      sticky.setAttribute('aria-hidden', on ? 'false' : 'true');
      stickyControls.forEach(function (control) {
        if (!on) control.el.setAttribute('tabindex', '-1');
        else if (control.tabindex === null) control.el.removeAttribute('tabindex');
        else control.el.setAttribute('tabindex', control.tabindex);
      });
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
