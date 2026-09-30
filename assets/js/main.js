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

  /* 6. (2026.09.23 삭제) 접수 마감 D-day 표시: 기수·마감 표기를 사이트에서 쓰지 않기로 해 코드를 뺐습니다. */

  /* 7. 하단 고정 접수 바: 첫 화면을 지나면 나타나고, 배너·푸터가 보이면 숨김 ----------------- */
  var sticky = document.getElementById('stickyCta');
  if (sticky) {
    var blockers = document.querySelectorAll('.site-footer, .cta-band, .gform-done, .offer-card');   /* 2026.09.26: 가격 카드(같은 버튼)가 보이면 하단 바를 숨김 */
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

  /* 8. 성균관컨설팅 주문서로 가는 버튼(주소에 kaiec_buy=1): 누르는 즉시 로딩 화면 (2026.09.26)
        상대 사이트가 뜰 때까지 화면이 멈춘 것처럼 보이지 않게 하고, 손가락을 대는 순간 미리 연결해 둡니다.
        skkc.co.kr 쪽 Header Code(tools/skkc-kaiec-head.html)가 같은 모양의 로딩 화면을 이어서 보여 줍니다. */
  var warmed = false;
  function warmSkkc() {
    if (warmed) return; warmed = true;
    try { var l = document.createElement('link'); l.rel = 'preconnect'; l.href = 'https://skkc.co.kr'; document.head.appendChild(l); } catch (e) {}
  }
  window.kaiecWarmSkkc = warmSkkc;
  function buyLink(t) {
    var a = t && t.closest ? t.closest('a[href*="kaiec_buy=1"]') : null;
    return a && (!a.target || a.target === '_self') ? a : null;
  }
  document.addEventListener('pointerdown', function (e) { if (buyLink(e.target)) warmSkkc(); }, true);
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (!buyLink(e.target)) return;
    var ov = document.getElementById('buyGo');
    if (!ov) {
      ov = document.createElement('div');
      ov.id = 'buyGo'; ov.className = 'buy-go'; ov.setAttribute('role', 'status');
      ov.innerHTML = '<span class="buy-go__spin" aria-hidden="true"></span><span>주문서를 여는 중입니다</span>';
      document.body.appendChild(ov);
    }
    ov.hidden = false;
  });
  /* 뒤로 가기로 돌아오면 로딩 화면을 걷음 */
  window.addEventListener('pageshow', function () { var ov = document.getElementById('buyGo'); if (ov) ov.hidden = true; });

  /* 9. 위원 활동 시스템 (2026.09.29): 추천 링크 ?ref=위원코드 를 이 방문 동안 기억해 주문서 링크(kaiec_buy=1)에 코드를 붙이고,
        명함 · 추천 링크 · QR 열람을 '리치' 신호로 라운지 서버에 보냅니다 (window.KAIEC_LOUNGE_API 가 있을 때만).
        위원 본인 브라우저(라운지 로그인 상태)와 같은 코드의 같은 날 반복 열람은 보내지 않습니다. 개인정보는 담지 않습니다. */
  var LAPI = window.KAIEC_LOUNGE_API || '';
  var CODE_RE = /^[A-Z]{2,4}\d{4}$/;
  function refParam() {
    try { return (new URLSearchParams(location.search).get('ref') || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); } catch (e) { return ''; }
  }
  var ref = refParam();
  if (CODE_RE.test(ref)) { try { sessionStorage.setItem('kaiec_ref', ref); } catch (e) {} }
  else { ref = ''; try { ref = sessionStorage.getItem('kaiec_ref') || ''; } catch (e) {} if (!CODE_RE.test(ref)) ref = ''; }
  if (ref) {
    document.querySelectorAll('a[href*="kaiec_buy=1"]').forEach(function (a) {
      if (a.href.indexOf('kaiec_ref=') < 0) a.href += '&kaiec_ref=' + ref;
    });
  }
  function visitorId() {
    var v = '';
    try { v = localStorage.getItem('kaiec_vid') || ''; if (!v) { v = Math.random().toString(36).slice(2, 10) + Date.now().toString(36); localStorage.setItem('kaiec_vid', v); } } catch (e) { v = 'anon'; }
    return v;
  }
  window.kaiecReach = function (code, path) {
    if (!LAPI || !window.fetch || !CODE_RE.test(code || '')) return;
    try { if (localStorage.getItem('kaiec_lounge_token')) return; } catch (e) {}
    var d = new Date(), day = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(), k = 'kaiec_reach_' + code + '_' + day;
    try { if (sessionStorage.getItem(k)) return; sessionStorage.setItem(k, '1'); } catch (e) {}
    try {
      fetch(LAPI, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ action: 'reach', code: code, vid: visitorId(), path: String(path || (location.pathname + location.hash)).slice(0, 80) }),
        keepalive: true, redirect: 'follow', cache: 'no-store' }).catch(function () {});
    } catch (e) {}
  };
  /* 명함 이미지 저장 · 공유 기록(위원 활동 시스템 1.3.0, 운영자 분석용): 리치와 달리 로그인한 위원 본인도 기록(하루 1회는 서버가 가림) */
  window.kaiecEvent = function (code, kind, path) {
    if (!LAPI || !window.fetch || !CODE_RE.test(code || '') || !/^(save|share)$/.test(kind || '')) return;
    try {
      fetch(LAPI, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ action: 'reach', kind: kind, code: code, vid: visitorId(), path: String(path || (location.pathname + location.hash)).slice(0, 80) }),
        keepalive: true, redirect: 'follow', cache: 'no-store' }).catch(function () {});
    } catch (e) {}
  };
  if (ref && CODE_RE.test(refParam())) window.kaiecReach(ref, location.pathname + '?ref');

  /* 아이콘은 빌드 시 SVG로 HTML에 직접 삽입되므로 외부 스크립트가 필요 없습니다. */
})();
