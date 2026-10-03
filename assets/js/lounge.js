/* 한국AI윤리위원회 (KAIEC) : 위원 라운지 (/lounge/)  2026.09.29
   캠페인위원 화면(위원 코드 + 비밀번호 한 번에 로그인, 첫 로그인만 이메일 인증 · 나의 임팩트 · AI 윤리 확산 도구 · 실적 · 정산 · 정산 정보 등록)과
   운영자 모드(/lounge/?admin: 분석 대시보드 · 정산 · 명단 · 공지 · 설정, 2026.09.29 밤 분석 탭 추가). 백엔드는 window.KAIEC_LOUNGE.api (위원 활동 시스템 앱스 스크립트 웹 앱).
   위원 로그인 토큰은 localStorage(30일), 운영자 토큰은 sessionStorage(창 닫으면 끝).
   서버(앱스 스크립트 웹 앱)가 가끔 수십 초 걸리는 일에 대비: 요청 60초, 읽기 요청은 7초 뒤 같은 요청을 하나 더 보내 먼저 오는 쪽을 쓰고,
   마지막으로 본 대시보드를 localStorage 에 두었다가 먼저 보여 주고 뒤에서 새로 고침(로그아웃하면 지움). */
(function () {
  'use strict';
  var CFG = window.KAIEC_LOUNGE || {};
  var API = CFG.api || '';
  var SITE = CFG.site || 'https://kaiec.kr';
  var MANUAL_URL = SITE + '/assets/docs/kaiec-campaign-member-manual.pdf';   // 캠페인위원 활동 매뉴얼(PDF, 2026.09.29 밤 사용자 요청. 위촉 메일에도 첨부)
  var EMAIL = CFG.email || 'contact@kaiec.kr';
  var ICONS = CFG.icons || {};
  var ADMIN = /[?&]admin(=|&|$)/.test(location.search);
  var KEY_TOKEN = 'kaiec_lounge_token', KEY_ADMIN = 'kaiec_lounge_admin';
  var NET_MSG = '서버 응답이 늦어 연결하지 못했습니다. 잠시 뒤 [다시 시도]를 눌러 주세요(인터넷 연결도 확인).';
  var KEY_DASH = 'kaiec_lounge_dash';
  /* 1.4.4 운영자 화면: 마지막 대시보드 · 보던 탭을 이 탭(sessionStorage)에만 둠. 창을 닫으면 로그인과 함께 사라짐 */
  var KEY_ADMIN_DASH = 'kaiec_lounge_admin_dash', KEY_ADMIN_TAB = 'kaiec_lounge_admin_tab', ADMIN_TABS = ['insight', 'pay', 'roster', 'notice', 'settings'];
  var KEY_BULK_N = 'kaiec_lounge_bulk_n';   /* 1.4.14 일괄 메일 대상(하위 10 · 20 · 30 · 전체), 이 탭에만 */
  var TIMEOUT_MS = 60000, HEDGE_MS = 7000;
  var HEDGE_OK = { 'me.dashboard': 1, 'admin.dashboard': 1, 'admin.member': 1, 'auth.login': 1, 'auth.start': 1, 'auth.verify': 1, 'auth.setPassword': 1, 'me.payinfo': 1, 'me.prefs': 1 };   /* 두 번 가도 결과가 같은 요청만(공지 · 정산 · 링크 등록은 제외) */
  var S = { data: null, admin: null, tab: 'insight', roster: { q: '', st: '' }, kitTab: 0, rank: { key: 'score', dir: 1, all: false }, tax: { month: '', data: null }, paying: {}, bulkN: '20', nudgeI: 0 };
  (function () { var v = read(KEY_BULK_N, true); if (/^(10|20|30|all)$/.test(v)) S.bulkN = v; })();   /* rank.dir 1 = 그 열의 기본 방향(점수 · 건수는 많은 순, 마지막 활동은 최근 순), -1 = 반대 */

  /* ---------- 작은 도구 ---------- */
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function ic(name, cls) { var d = ICONS[name]; if (!d) return ''; return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"' + (cls ? ' class="' + cls + '"' : '') + '>' + d + '</svg>'; }
  function won(n) { n = Math.round(Number(n) || 0); return n.toLocaleString('ko-KR') + '원'; }
  function num(n) { return (Number(n) || 0).toLocaleString('ko-KR'); }
  var DAYS = ['일', '월', '화', '수', '목', '금', '토'];
  function dateOf(s) { var m = String(s || '').match(/(\d{4})-(\d{2})-(\d{2})/); if (m) return new Date(+m[1], +m[2] - 1, +m[3], 12); var d = s ? new Date(s) : null; return d && !isNaN(d.getTime()) ? new Date(d.getFullYear(), d.getMonth(), d.getDate(), 12) : null; }   /* 'yyyy-MM-dd…' 또는 자바스크립트 Date 문자열 · ISO 도 받음 */
  function fmtMD(s, wd) { var d = dateOf(s); if (!d) return String(s || ''); return (d.getMonth() + 1) + '.' + ('0' + d.getDate()).slice(-2) + (wd ? '(' + DAYS[d.getDay()] + ')' : ''); }
  function fmtKo(s, wd) { var d = dateOf(s); if (!d) return String(s || ''); return (d.getMonth() + 1) + '월 ' + d.getDate() + '일' + (wd ? '(' + DAYS[d.getDay()] + ')' : ''); }
  /* 1.3.3 정산 규칙: 결제 즉시 확정(confirmDays 0) · 정산 요일(기본 목) 0시 마감. 결제일 다음 날부터 처음 오는 정산 요일이 지급일(수요일 결제 → 다음 날 목요일, 목요일 결제 → 다음 주 목요일) */
  var PAY_WD = 4, CONFIRM_D = 0;
  function payDayFor(s) { var d = dateOf(s); if (!d) return null; for (var i = 1; i <= 7; i++) { var x = new Date(d.getFullYear(), d.getMonth(), d.getDate() + i, 12); if (x.getDay() === PAY_WD) return x; } return null; }
  function cutDay() { return DAYS[(PAY_WD + 6) % 7]; }
  function ruleShort() { return CONFIRM_D > 0 ? '결제 뒤 ' + CONFIRM_D + '일 확정 · ' + DAYS[PAY_WD] + '요일 정산' : '결제 즉시 확정 · ' + cutDay() + '요일 24시 마감 · ' + DAYS[PAY_WD] + '요일 정산'; }
  function fmtDot(s) { var d = dateOf(s); if (!d) return String(s || ''); return d.getFullYear() + '.' + ('0' + (d.getMonth() + 1)).slice(-2) + '.' + ('0' + d.getDate()).slice(-2); }
  function store(k, v, session) { var st = session ? sessionStorage : localStorage; try { if (v === null) st.removeItem(k); else st.setItem(k, v); } catch (e) { /* 저장 불가 */ } }
  function read(k, session) { try { return (session ? sessionStorage : localStorage).getItem(k) || ''; } catch (e) { return ''; } }
  function short(u) { return String(u || '').replace(/^https?:\/\//, ''); }
  function copyText(t, btn) {
    function done() { flash(btn, '복사됨'); toast('복사했습니다', 'ok'); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function () { legacy(); });
    else legacy();
    function legacy() { try { var ta = document.createElement('textarea'); ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(); } catch (e) { toast('복사하지 못했습니다. 길게 눌러 복사해 주세요.', 'warn'); } }
  }
  function flash(btn, txt) { if (!btn) return; if (!btn._label) btn._label = btn.innerHTML; btn.innerHTML = txt; clearTimeout(btn._t); btn._t = setTimeout(function () { btn.innerHTML = btn._label; }, 1800); }
  function busy(btn, on) { if (!btn) return; if (on) { btn._html = btn.innerHTML; btn.classList.add('is-busy'); btn.innerHTML = '<span class="lg-spin"></span> 처리 중'; btn.disabled = true; } else { btn.classList.remove('is-busy'); btn.disabled = false; if (btn._html) btn.innerHTML = btn._html; } }
  function toast(msg, kind) {
    var box = $('lgToasts'); if (!box) return;
    var t = document.createElement('div'); t.className = 'lg-toast' + (kind ? ' lg-toast--' + kind : ''); t.textContent = msg; box.appendChild(t);
    setTimeout(function () { t.classList.add('is-out'); setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 300); }, 2600);
  }
  function modal(title, sub, bodyHtml, foot) {
    var m = $('lgModal');
    m.innerHTML = '<div class="lg-dialog" role="dialog" aria-modal="true" aria-labelledby="lgDlgT"><div class="lg-dialog-head"><div><h2 id="lgDlgT">' + esc(title) + '</h2>' + (sub ? '<p>' + esc(sub) + '</p>' : '') + '</div><button type="button" class="lg-dialog-x" data-act="close" aria-label="닫기">' + ic('x') + '</button></div><div class="lg-dialog-body">' + bodyHtml + '</div>' + (foot ? '<div class="lg-dialog-foot">' + foot + '</div>' : '') + '</div>';
    m.hidden = false; document.documentElement.classList.add('mp-lock');
    return m;
  }
  function closeModal() { var m = $('lgModal'); m.hidden = true; m.innerHTML = ''; document.documentElement.classList.remove('mp-lock'); }
  function confirmBox(title, text, okLabel, danger) {
    return new Promise(function (res) {
      var m = modal(title, '', '<p>' + esc(text) + '</p>', '<button type="button" class="btn btn-ghost btn-sm" data-act="close">취소</button><button type="button" class="btn btn-sm ' + (danger ? 'btn-ghost" style="color:#991B12;border-color:#EEC3BF' : 'btn-primary') + '" data-act="ok">' + esc(okLabel || '확인') + '</button>');
      m.onclick = function (e) { var b = e.target.closest('[data-act]'); if (!b) { if (e.target === m) { closeModal(); res(false); } return; } if (b.getAttribute('data-act') === 'ok') { closeModal(); res(true); } else { closeModal(); res(false); } };
    });
  }

  /* ---------- API ---------- */
  function apiError(code, msg, extra) { var e = new Error(msg); e.code = code; if (extra) for (var k in extra) e[k] = extra[k]; return e; }
  function httpPost(payload) {
    var ctl = ('AbortController' in window) ? new AbortController() : null, timer = ctl ? setTimeout(function () { ctl.abort(); }, TIMEOUT_MS) : null;
    var p = fetch(API, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: JSON.stringify(payload), redirect: 'follow', cache: 'no-store', signal: ctl ? ctl.signal : undefined })
      .then(function (res) { return res.text().then(function (txt) { var j = null; try { j = JSON.parse(txt); } catch (e) { j = null; } if (!j || typeof j !== 'object') throw apiError(res.ok ? 'SERVER' : 'NETWORK', res.ok ? '서버 응답을 읽지 못했습니다. 잠시 뒤 다시 시도해 주세요.' : NET_MSG); return j; }); }, function () { throw apiError('NETWORK', NET_MSG); })
      .then(function (j) { if (timer) clearTimeout(timer); return j; }, function (e) { if (timer) clearTimeout(timer); throw (e && e.code) ? e : apiError('NETWORK', NET_MSG); });
    p.abort = function () { try { if (ctl) ctl.abort(); } catch (e) { /* 무시 */ } };
    return p;
  }
  /* 페이지 머리(head)의 작은 스크립트가 CSS 를 기다리지 않고 먼저 띄운 대시보드 요청(window.__lgPre)을 같은 모양의 약속으로 */
  function adoptPre(pre) {
    var r = pre.p.then(function (x) { if (!x || !x.j || typeof x.j !== 'object') throw apiError(x && x.ok ? 'SERVER' : 'NETWORK', x && x.ok ? '서버 응답을 읽지 못했습니다. 잠시 뒤 다시 시도해 주세요.' : NET_MSG); return x.j; }, function () { throw apiError('NETWORK', NET_MSG); });
    r.abort = pre.abort || function () {};
    return r;
  }
  /* 읽기 요청: HEDGE_MS 안에 응답이 없으면 같은 요청을 하나 더 보내 먼저 오는 쪽을 씀(다른 쪽은 끊음). 둘 다 실패하면 실패. pre 가 있으면 그 요청을 첫 번째로 씀 */
  function httpPostHedged(payload, pre) {
    return new Promise(function (resolve, reject) {
      var settled = false, pending = 0, all = [], hedge = null;
      function start(first) {
        var r = first ? adoptPre(first) : httpPost(payload); all.push(r); pending++;
        r.then(function (j) { if (settled) return; settled = true; if (hedge) clearTimeout(hedge); all.forEach(function (x) { if (x !== r) x.abort(); }); resolve(j); },
          function (e) { pending--; if (settled) return; if (pending > 0) return; if (hedge) { clearTimeout(hedge); hedge = null; } settled = true; reject(e); });
      }
      start(pre || null);
      hedge = setTimeout(function () { hedge = null; if (!settled) start(); }, pre ? Math.max(400, HEDGE_MS - (Date.now() - (pre.at || Date.now()))) : HEDGE_MS);
    });
  }
  function call(action, data) {
    if (!API) return Promise.reject(apiError('READY', '위원 라운지 연결이 아직 준비되지 않았습니다. 곧 열립니다.'));
    var p = { action: action };
    if (action.indexOf('admin.') === 0 && action !== 'admin.login') p.adminToken = read(KEY_ADMIN, true);
    else if (action.indexOf('me.') === 0) p.token = read(KEY_TOKEN);
    if (data) for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) p[k] = data[k];
    var pre = null;
    if (window.__lgPre && window.__lgPre.action === action && window.__lgPre.token === (p.token || p.adminToken || '')) { pre = window.__lgPre; }
    if (window.__lgPre && window.__lgPre.action === action) window.__lgPre = null;   /* 한 번만 씀 */
    return (HEDGE_OK[action] ? httpPostHedged(p, pre) : httpPost(p)).then(function (j) {
      if (j.ok) return j;
      var e = apiError(j.code || 'SERVER', j.message || '오류가 났습니다.', j);
      if (j.relogin) { if (action.indexOf('admin.') === 0) { store(KEY_ADMIN, null, true); } else { store(KEY_TOKEN, null); } }
      throw e;
    });
  }

  /* ---------- 화면 틀 ---------- */
  var hero = $('lgHero'), login = $('lgLogin'), main = $('lgMain'), boot = $('lgBoot');
  function show(which) { hero.hidden = which !== 'main'; login.hidden = which !== 'login'; main.hidden = which !== 'main'; boot.hidden = which !== 'boot'; bootNote(which === 'boot'); }
  var bootTimer = null;
  function bootNote(on) {
    var el = boot ? boot.querySelector('span:last-child') : null; if (!el) return;
    if (bootTimer) { clearTimeout(bootTimer); bootTimer = null; }
    if (!on) { el.textContent = '위원 라운지를 여는 중입니다'; return; }
    el.textContent = '위원 라운지를 여는 중입니다';
    bootTimer = setTimeout(function () { el.textContent = '서버를 깨우는 중입니다. 처음 열 때는 20~30초까지 걸릴 수 있어요. 잠시만 기다려 주세요.'; }, 6000);
  }
  function refreshing(on, note) {
    var box = $('lgToasts'); if (!box) return;
    var old = box.querySelector('.lg-toast--sticky'); if (old) old.parentNode.removeChild(old);
    if (!on) return;
    var t = document.createElement('div'); t.className = 'lg-toast lg-toast--sticky'; t.innerHTML = '<span class="lg-spin" style="width:14px;height:14px;border-width:2px;vertical-align:-2px;margin-right:6px"></span>최신 정보를 불러오는 중' + (note ? ' <small class="lg-toast-note">' + esc(note) + '</small>' : ''); box.appendChild(t);
  }
  function heroHTML(crumb, h1, sub, right) {
    return '<div class="wrap lg-hero-inner"><div><p class="crumb"><a href="' + SITE + '/">홈</a> &nbsp;›&nbsp; ' + crumb + '</p><h1>' + h1 + '</h1><p>' + sub + '</p></div>' + (right || '') + '</div>';
  }

  /* ---------- 위원: 로그인 ---------- */
  var L = { step: 'code', code: '', emailMasked: '', setupToken: '', minutes: 10, purpose: 'first', resendAt: 0 };   /* step: code(코드 + 비밀번호 한 화면) → otp → setpw */
  function loginBox(inner, stepIdx) {
    var steps = stepIdx == null ? '' : '<div class="lg-steps-nav" aria-hidden="true">' + [0, 1, 2].map(function (i) { return '<span class="' + (i <= stepIdx ? 'on' : '') + '"></span>'; }).join('') + '</div>';
    return '<div class="lg-lbox"><div class="lg-lhead"><div class="lg-eyebrow">KAIEC MEMBER LOUNGE</div><h1>위원 라운지</h1><p>AI 윤리 캠페인위원 전용 · 나의 임팩트와 정산을 한눈에</p></div><div class="lg-lbody">' + steps + inner + '</div>' +
      '<div class="lg-lfoot">위원 코드는 위촉 안내 메일과 위원 명함에 있습니다.<br>로그인 문의 <a href="mailto:' + EMAIL + '">' + EMAIL + '</a></div></div>';
  }
  function renderLogin() {
    var html = '';
    if (!API) {
      html = loginBox('<div class="lg-ready">' + ic('clock') + '<div><b>위원 라운지 연결 준비 중</b><br>연결이 끝나면 이 화면에서 위원 코드로 로그인할 수 있습니다. 위촉 안내 메일로 다시 알려 드립니다.</div></div><a class="btn btn-ghost btn-sm" href="' + SITE + '/members/">위원 명단으로 돌아가기</a>');
    } else if (L.step === 'code') {
      html = loginBox('<form id="lgForm" novalidate>' +
        '<div class="lg-field"><label for="lgCode">위원 코드</label><input class="lg-input lg-input--code" id="lgCode" autocomplete="username" autocapitalize="characters" spellcheck="false" placeholder="예 PKH3185" maxlength="8" value="' + esc(L.code) + '"></div>' +
        '<div class="lg-field"><label for="lgPw">비밀번호 <small>처음이면 비워 두세요</small></label><input class="lg-input" id="lgPw" type="password" autocomplete="current-password" maxlength="64" placeholder="첫 로그인은 이메일 인증으로 만듭니다"></div>' +
        '<p class="lg-err" id="lgErr"></p><div class="lg-btnrow"><button type="submit" class="btn btn-primary" id="lgGo">로그인</button></div>' +
        '<p class="lg-help" style="margin-top:12px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><button type="button" class="lg-link" data-act="first">처음이신가요? 이메일 인증으로 시작</button><button type="button" class="lg-link" data-act="reset">비밀번호를 잊으셨나요?</button></p>' +
        '<p class="lg-help" style="margin-top:10px">위원 코드는 영문 머리글자 2~4자 + 숫자 4자리(위원 명함의 MEMBER CODE). 첫 로그인 때 이메일 인증 뒤 비밀번호를 직접 정하고, 그 다음부터는 코드와 비밀번호만 넣으면 바로 열립니다.</p></form>', null);
    } else if (L.step === 'otp') {
      html = loginBox('<form id="lgForm" novalidate><p class="lg-ok">' + esc(L.emailMasked) + ' 로 인증번호 6자리를 보냈습니다 (' + L.minutes + '분 안에 입력). 메일이 안 보이면 스팸함도 확인해 주세요.</p><div class="lg-field"><label for="lgOtp">인증번호</label><input class="lg-input lg-input--otp" id="lgOtp" inputmode="numeric" pattern="[0-9]*" maxlength="6" autocomplete="one-time-code" placeholder="000000"></div><p class="lg-err" id="lgErr"></p><div class="lg-btnrow"><button type="submit" class="btn btn-primary" id="lgGo">확인</button></div><p class="lg-help" style="margin-top:12px;display:flex;justify-content:space-between;gap:10px"><button type="button" class="lg-link" data-act="back">코드 다시 입력</button><button type="button" class="lg-link" data-act="resend">인증번호 다시 보내기</button></p></form>', 1);
    } else if (L.step === 'setpw') {
      html = loginBox('<form id="lgForm" novalidate><p class="lg-ok">인증되었습니다. 앞으로 쓸 비밀번호를 정해 주세요.</p><div class="lg-field"><label for="lgPw1">새 비밀번호 <small>6자 이상</small></label><input class="lg-input" id="lgPw1" type="password" autocomplete="new-password" minlength="6" maxlength="64"></div><div class="lg-field"><label for="lgPw2">비밀번호 확인</label><input class="lg-input" id="lgPw2" type="password" autocomplete="new-password" maxlength="64"></div><p class="lg-err" id="lgErr"></p><div class="lg-btnrow"><button type="submit" class="btn btn-primary" id="lgGo">비밀번호 정하고 시작하기</button></div></form>', 2);
    } else { L.step = 'code'; renderLogin(); return; }
    login.innerHTML = html; show('login');
    var f = $('lgForm'); if (!f) return;
    var first = f.querySelector('input:not([disabled])'); if (first && !(L.step === 'code' && L.code)) setTimeout(function () { first.focus(); }, 50);
    else if (L.step === 'code' && L.code && $('lgPw')) setTimeout(function () { $('lgPw').focus(); }, 50);
    f.addEventListener('submit', onLoginSubmit);
    f.addEventListener('click', function (e) {
      var b = e.target.closest('[data-act]'); if (!b) return;
      var act = b.getAttribute('data-act');
      if (act === 'back') { L.step = 'code'; renderLogin(); }
      if (act === 'first' || act === 'reset') { if (!takeCode()) return; L.purpose = act === 'reset' ? 'reset' : 'first'; startOtp(b); }
      if (act === 'resend') { if (Date.now() < L.resendAt) { toast('1분 뒤에 다시 보낼 수 있습니다', 'warn'); return; } startOtp(b); }
    });
  }
  /* 코드 칸의 값을 읽어 L.code 로(형식이 아니면 안내) */
  function takeCode() {
    var el = $('lgCode'); if (!el) return !!L.code;
    var code = (el.value || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (!/^[A-Z]{2,4}\d{4}$/.test(code)) { err('위원 코드 형식이 아닙니다. 예 PKH3185'); el.focus(); return false; }
    L.code = code; return true;
  }
  function err(msg) { var e = $('lgErr'); if (!e) { toast(msg, 'danger'); return; } e.textContent = msg; e.classList.add('is-on'); }
  function startOtp(btn) {
    busy(btn, true);
    call('auth.start', { code: L.code, purpose: L.purpose }).then(function (j) {
      busy(btn, false);
      if (j.mode === 'password' && L.purpose !== 'reset') { err('이미 비밀번호를 정한 코드입니다. 비밀번호를 넣고 [로그인]을 눌러 주세요. 잊으셨으면 [비밀번호를 잊으셨나요?]로 다시 정할 수 있습니다.'); if ($('lgPw')) $('lgPw').focus(); return; }
      L.step = 'otp'; L.emailMasked = j.emailMasked; L.minutes = j.minutes || 10; L.resendAt = Date.now() + 60000; renderLogin();
    }, function (e) { busy(btn, false); if (e.code === 'TOO_SOON' && L.step !== 'otp') { L.step = 'otp'; L.resendAt = Date.now() + 60000; renderLogin(); err(e.message); } else err(e.message); });
  }
  function onLoginSubmit(e) {
    e.preventDefault();
    var btn = $('lgGo');
    if (L.step === 'code') {
      if (!takeCode()) return;
      var pw0 = ($('lgPw') && $('lgPw').value) || '';
      if (!pw0) { L.purpose = 'first'; startOtp(btn); return; }   /* 비밀번호가 비어 있으면 첫 로그인(이메일 인증)으로 */
      busy(btn, true);
      call('auth.login', { code: L.code, password: pw0, withDash: 1 }).then(function (j) { store(KEY_DASH, null); store(KEY_TOKEN, j.token); if (!takeDash(j)) loadDash(); }, function (e4) { busy(btn, false); if (e4.code === 'NEED_SETUP') { L.purpose = 'first'; startOtp(btn); return; } err(e4.message); if ($('lgPw')) { $('lgPw').value = ''; $('lgPw').focus(); } });
      return;
    }
    if (L.step === 'otp') {
      var otp = ($('lgOtp').value || '').replace(/\D/g, '');
      if (otp.length !== 6) { err('인증번호 6자리를 입력해 주세요.'); return; }
      busy(btn, true);
      call('auth.verify', { code: L.code, otp: otp }).then(function (j) { busy(btn, false); L.setupToken = j.setupToken; L.step = 'setpw'; renderLogin(); }, function (e2) { busy(btn, false); err(e2.message); if (e2.code === 'EXPIRED' || e2.code === 'NO_OTP' || e2.code === 'LOCKED') L.resendAt = 0; });
      return;
    }
    if (L.step === 'setpw') {
      var p1 = $('lgPw1').value || '', p2 = $('lgPw2').value || '';
      if (p1.length < 6) { err('비밀번호는 6자 이상으로 정해 주세요.'); return; }
      if (p1 !== p2) { err('비밀번호 확인이 다릅니다.'); return; }
      busy(btn, true);
      call('auth.setPassword', { setupToken: L.setupToken, password: p1, withDash: 1 }).then(function (j) { store(KEY_DASH, null); store(KEY_TOKEN, j.token); toast('환영합니다! 비밀번호가 저장되었습니다', 'ok'); if (!takeDash(j)) loadDash(); }, function (e3) { busy(btn, false); err(e3.message); if (e3.code === 'BAD_TOKEN') { L.step = 'code'; setTimeout(renderLogin, 1200); } });
      return;
    }
    L.step = 'code'; renderLogin();
  }

  /* ---------- 위원: 대시보드 ---------- */
  /* 1.4.4 로그인 응답에 함께 온 대시보드(withDash)를 바로 씀: 로그인 → 대시보드 두 번 오가던 것을 한 번에 */
  function takeDash(j) { var d = j && j.dash; if (!(d && d.ok && d.member && d.member.code)) return false; S.data = d; store(KEY_DASH, JSON.stringify(d)); lastLoadAt = Date.now(); renderDash(); return true; }
  function cachedDash() { try { var j = JSON.parse(read(KEY_DASH) || 'null'); return j && j.ok && j.member && j.member.code ? j : null; } catch (e) { return null; } }
  function loadDash() {
    lastLoadAt = Date.now();
    var shown = false;
    if (S.data) { shown = true; }                                   /* 이미 열려 있으면 그대로 두고 뒤에서 새로 고침 */
    else { var c = cachedDash(); if (c) { S.data = c; renderDash(); shown = true; } }
    if (shown) refreshing(true); else show('boot');
    call('me.dashboard').then(function (j) { refreshing(false); S.data = j; store(KEY_DASH, JSON.stringify(j)); renderDash(); }, function (e) {
      refreshing(false);
      if (e.relogin || e.code === 'AUTH' || e.code === 'ENDED') { store(KEY_TOKEN, null); store(KEY_DASH, null); S.data = null; L.step = 'code'; renderLogin(); if (e.code === 'ENDED') setTimeout(function () { err(e.message); }, 60); return; }
      if (shown && S.data) { toast('최신 정보를 불러오지 못했습니다. 마지막으로 본 내용을 보여 드립니다.', 'warn'); return; }
      show('login'); login.innerHTML = loginBox('<p class="lg-err is-on">' + esc(e.message) + '</p><div class="lg-btnrow"><button type="button" class="btn btn-primary" id="lgRetry">다시 시도</button><button type="button" class="btn btn-ghost" id="lgOut">로그아웃</button></div>');
      $('lgRetry').onclick = loadDash; $('lgOut').onclick = logout;
    });
  }
  function logout() { store(KEY_TOKEN, null); store(KEY_DASH, null); S.data = null; L.step = 'code'; L.code = ''; renderLogin(); toast('로그아웃했습니다'); }
  /* 공유 문안(2026.09.30): '전 과정 온라인'이 온라인 강의로 읽혀 구매자 · 위원이 되묻는다는 사용자 말에 따라, 강의가 아니라 표준교재로 내 속도에 맞춰 공부하고
     온라인 평가로 이수하는 과정이라는 점을 부담이 없다는 장점으로 적음(블로그 문안은 이미 '표준교재로 자율 학습'이라 그대로)
     2026.10.01 AIEP 전용 영상관 홍보(사용자: '우리 영상인 것처럼, 구매 전환율이 높아지게'): 네 문안 모두 '표준교재와 한국어 자막 애니메이션 영상관(N편)'으로.
     편 수는 빌드 때 영상관 데이터에서 넣은 KAIEC_LOUNGE.vids(없으면 숫자 없이). 해외 애니메이션을 위원회가 만들었다고 쓰지 않음(엄선 · 한국어 자막).
     2026.10.02 6판: 위원회 영상은 '전문위원이 기획하고 위원회가 자체 제작한 영상(한국어 내레이션)'으로 자랑스럽게(사용자 요청), 이름은 'AIEP 영상관' */
  var VIDS = 'AIEP 영상관' + (CFG.vids && CFG.vids.n ? '(' + CFG.vids.n + '편)' : '');
  var MSG_TPL = [
    ['카카오톡', 'AI를 쓰는 건 이제 기본이고, 바르게 쓰는 기준을 아는 사람은 드물어요. 한국AI윤리위원회 AI윤리전문가(AIEP) 과정을 추천드려요. 진도율 채우는 강의 대신 위원회 표준교재와 ' + VIDS + '으로 내 속도에 맞춰 공부하고 온라인 평가로 이수해서 부담이 없고, 이수하면 공식 명단에 등록됩니다. 제 추천 링크로 신청하면 위원 추천 할인이 자동 적용돼요 👉 {intro}'],
    ['인스타그램', '요즘 AI 안 쓰는 사람 없죠. 그런데 \'바르게\' 쓰는 기준을 배운 사람은 많지 않아요.\n한국AI윤리위원회 AI윤리전문가(AIEP) 과정, 진도율 채우는 강의 대신 위원회 표준교재와 ' + VIDS + '으로 내 속도에 맞춰 공부하고 온라인 평가로 이수해 공식 명단에 이름을 올릴 수 있어요.\n결제한 날 바로 영상관이 열려요 🎬\n프로필 링크로 신청하면 위원 추천 할인 적용 ✔\n#AI윤리 #AI윤리전문가 #AIEP #한국AI윤리위원회\n{intro}'],
    ['쓰레드', 'AI를 쓰는 건 이제 기본. 그런데 바르게 쓰는 기준은 배운 적 있나요?\n한국AI윤리위원회 AI윤리전문가(AIEP) 과정은 진도율 채우는 강의 대신 위원회 표준교재와 ' + VIDS + '으로 내 속도에 맞춰 공부하고 온라인 평가로 이수하는 과정이고, 이수하면 위원회 공식 명단에 이름이 올라갑니다.\n아래 링크로 신청하면 위원 추천 할인이 자동 적용돼요 🧵\n{intro}'],
    ['블로그 · 커뮤니티', '[추천] 한국AI윤리위원회 AI윤리전문가(AIEP) 양성과정\n생성형 AI를 쓰는 학생 · 직장인이라면 한 번은 정리해 둘 만한 내용입니다. 표준교재와 ' + VIDS + '으로 자율 학습하고 온라인 이수 평가를 통과하면 위원회 공식 명단에 등록됩니다. 영상관은 결제한 날 AIEP 전용관에서 바로 열리고, 편마다 AI윤리 분야 전문위원이 기획하고 위원회가 자체 제작한 영상(한국어 내레이션)으로 시작해 교재 장과 생각해 볼 질문이 함께 나옵니다.\n아래 링크(AI 윤리 캠페인위원 추천)로 신청하면 위원 추천 할인이 적용됩니다.\n{intro}']
  ];
  /* 직함(등급, 2026.09.29 사용자 결정): 확정 크레딧 0~2 AI 윤리 캠페인위원 · 3 선임 · 10 책임 · 30 수석.
     2026.09.30 사용자: 승격하면 '윤리'를 빼고 AI 선임위원 · AI 책임위원 · AI 수석위원(명단 · 명함 · 라운지 · 메일 모두). 옛 이름 'AI 윤리 선임위원'도 새 이름으로 읽음 */
  var TIER_WORD = { '선임': 'AI 선임위원', '책임': 'AI 책임위원', '수석': 'AI 수석위원' };
  function tierFull(name) { name = String(name || '').replace(/^AI 윤리 (선임|책임|수석)위원$/, 'AI $1위원'); return TIER_WORD[name] || (/앰버서더/.test(name) ? TIER_WORD['수석'] : /^수석 캠페인위원$/.test(name) ? TIER_WORD['책임'] : /^선임 캠페인위원$/.test(name) ? TIER_WORD['선임'] : name === '캠페인위원' ? 'AI 윤리 캠페인위원' : name); }
  function shortTier(name) { return tierFull(name).replace(/^AI (윤리 )?/, ''); }
  function tierBadgeOf(name) { var f = tierFull(name); for (var k in TIER_WORD) if (TIER_WORD[k] === f) return k; return ''; }
  /* 라운지 머리 카드의 직함: '한국AI윤리위원회(KAIEC)' 아래 직함을 등급별 색으로(선임 은청색 · 책임 자주 · 수석 금색) */
  function tierChip(badge, tier, hero) { var b = badge || tierBadgeOf(tier), full = hero ? heroTier(tier) : tierFull(tier); return '<span class="lg-tier' + (b ? ' lg-tier--' + b : ' lg-tier--base') + '">' + (b ? ic('award') : '') + esc(full) + '</span>'; }
  /* 라운지 머리 카드는 기본 직함도 '윤리'를 뺀 'AI 캠페인위원'(2026.09.29 사용자: 이 화면에서는 윤리를 빼 달라). 승격 직함은 1.4.1 부터 어디서나 'AI 선임위원' 식 */
  function heroTier(name) { return tierFull(name).replace(/^AI 윤리 /, 'AI '); }
  function statusChip(st) { var map = { '활동': ['ok', '활동 중'], '휴면예정': ['wait', '휴면 예정'], '휴면': ['x', '휴면'], '종료': ['x', '종료'] }; var m = map[st] || ['x', st]; return '<span class="lg-chip lg-chip--' + m[0] + '">' + esc(m[1]) + '</span>'; }
  function creditRow(r) {
    var chip = { '대기': ['wait', '확정 대기'], '확정': ['ok', '확정'], '취소': ['x', '취소'], '차감': ['red', '차감(환불)'], '미인정': ['x', '미인정'] }[r.status] || ['x', r.status];
    var pay = r.status === '확정' || r.status === '차감' ? won(r.pay) : '-';
    var when = r.status === '대기' ? fmtMD(r.confirmAt) + ' 확정 예정' : r.status === '확정' ? (r.payStatus === '지급완료' ? fmtMD(r.payDay) + ' 지급 완료' : r.payStatus === '보류' ? '정산 정보 등록 후' : r.payStatus === '지급예정' ? fmtMD(r.payDay, true) + ' 지급 예정' : (payDayFor(r.day) ? fmtMD(payDayFor(r.day), true) + ' 정산 예정' : '다음 ' + DAYS[PAY_WD] + '요일')) : r.status === '차감' ? '다음 정산에서 차감' : '-';
    return '<tr><td>' + fmtDot(r.day) + (r.self ? ' <span class="lg-chip lg-chip--blue">본인</span>' : '') + '</td><td><span class="lg-chip lg-chip--' + chip[0] + '">' + chip[1] + '</span></td><td class="num">' + pay + '</td><td class="num">' + when + '</td></tr>';
  }
  /* 기간 문구: 30 → '30일', 60 이상 30의 배수 → 'N개월' */
  function periodTxt(days) { days = Number(days) || 0; return days >= 60 && days % 30 === 0 ? (days / 30) + '개월' : days + '일'; }
  /* 위원 자격 유지 기준(2026.09.29 · 30일마다 1건): 화면 맨 아래 '위원 자격 · 활동 기준' 카드(사용자: 앞에 대놓고 보여 주지 말고 맨 마지막에). 다음 기한과 남은 날, 유예 중이면 안내 */
  function rulesHTML(d) {
    var mc = d.minCredit || {}, set = d.settings, first = mc.firstDays || 30, period = periodTxt(mc.periodDays || 30), grace = mc.graceDays || 7, notice = mc.noticeDays || 7;
    /* 2026.09.29 사용자: 다음 실적 기한은 실적일부터 다시 30일로 갱신되는 것을 맨 아래에 적어 달라(서버 creditRule_ 이 마지막 실적일 + 30일로 계산하므로 그대로 설명) */
    var std = '위촉 뒤 ' + first + '일 안에 첫 추천 실적 1건, 그 뒤로는 ' + period + '마다 1건 이상이면 유지됩니다. 실적이 들어올 때마다 그날부터 ' + period + '이 새로 시작되며, 본인 결제도 실적으로 인정됩니다.';
    var dorm = mc.dormantDays || 10, full = set.gaugeFullDays || 10, due;
    if (!mc.deadline) due = '<div class="lg-min"><b>다음 실적 기한</b> 아직 계산되지 않았습니다.</div>';
    else if (mc.reason === '최소활동') due = '<div class="lg-min lg-min--soon"><b>' + (d.member && d.member.status === '휴면예정' ? '유예 기간' : '휴면 중') + '</b> ' + (mc.graceEnd ? fmtKo(mc.graceEnd, true) + '까지' : '휴면 기간 안에') + ' 위원 코드로 결제 1건이 들어오면 바로 복귀하고 명단에 다시 올라갑니다. 로그인만으로는 복귀하지 않고, 본인 결제도 인정됩니다.</div>';
    else { var left = Number(mc.daysLeft), tone = isFinite(left) && left <= notice ? ' lg-min--soon' : ''; due = '<div class="lg-min' + tone + '"><b>다음 실적 기한</b> ' + fmtKo(mc.deadline, true) + (mc.first ? ' · 첫 실적을 기다리는 중' : (mc.base && mc.last && mc.base > mc.last) ? ' · ' + fmtDot(mc.base) + '부터 ' + period + '(기준 시작일)' : mc.last ? ' · 마지막 실적 ' + fmtDot(mc.last) + '부터 ' + period : '') + '<span>결제 1건이 들어오면 그날부터 ' + period + '이 다시 시작됩니다.</span></div>'; }
    /* 2026.09.30 사용자: 30일 동안 0건이면 휴면, 휴면 10일 뒤에도 실적이 없으면 자동 해제. 게이지도 같은 일정(조급하지 않게), 남은 날 카운트다운은 빼고 날짜만 */
    return '<div class="lg-card lg-rules" id="lgRules"><h2>' + ic('shield-check') + '위원 자격 · 활동 기준<span class="sub">활동하시는 위원으로 명단을 유지하기 위한 기준입니다</span></h2>' +
      '<div class="lg-rules-grid"><div><b>자격 유지 기준</b><p>' + esc(std) + '</p></div>' +
      '<div><b>기한이 지나면</b><p>기한 ' + notice + '일 전에 메일로 미리 알려 드립니다. 기한까지 실적이 없으면 휴면(명단 · 명함 잠시 숨김)이 되고, 휴면 ' + dorm + '일 안에 추천 결제 1건이 들어오면 바로 복귀합니다. 그 뒤에도 실적이 없으면 위촉이 자동 해제됩니다. 크레딧과 직함은 휴면 중에도 그대로입니다.</p></div>' +
      '<div><b>활동 게이지</b><p>추천 결제 1건마다 가득 차고, ' + full + '일 동안 그대로 유지된 뒤 휴면 · 해제 일정에 맞춰 천천히 줄어듭니다. 로그인 · 공유만으로는 채워지지 않고, 결제 1건이면 언제든 다시 가득 찹니다.</p></div></div>' + due + '</div>';
  }
  /* 활동 흐름(2026.09.29 사용자: 기준 대신 더 유의미한 데이터를 → 같은 날 저녁: '추천 결제'는 결제 느낌이 강하니 '추천 성과'로, 열람은 많은데 성과가 적으면 허탈하지 않게
     더 유의미하고 기분 좋은 시각화로): 최근 8주 추천 성과 막대 + 'AI 윤리 확산'(2026.09.30 전 이름 'AI 윤리 확산 도달')(30일 동안 명함 · 링크로 AI 윤리를 접한 사람, 주별 물결 그림, 이번 주 · 지난주)
     + 확산 단계(누적 확산 이정표 10 · 50 · 100 · 300 · 1,000명). 확산은 같은 브라우저를 하루 한 번만 세므로 '명'으로 읽어도 무리가 없음 */
  /* 2026.09.30 이름 변경(사용자: '리치(도달)'는 표현이 이상하다, 자연스럽고 자긍심 느껴지게): 위원 화면은 '누적 확산'(명함 · 링크로 접한 사람, 누적) · 'AI 윤리 확산'(30일). 결제한 사람은 '임팩트'(크레딧)로 따로(같은 날 사용자: '누적 임팩트' 같은 말 → 임팩트는 결제 실적이라 '확산'으로),
     위원장 화면은 1.4.7 부터 '명함 · 링크 열람(회)' · '명함 · 링크 방문(명)'(사용자: '확산은 확 와닿지 않는데'). 서버 · 시트 이름(reach · 누적리치)은 그대로 */
  var REACH_STAGES = [[10, '첫 물결'], [50, '퍼지는 물결'], [100, '큰 물결'], [300, '넓은 물결'], [1000, '사회적 물결']];
  function reachStage(total) {
    var idx = -1, next = null;
    for (var i = 0; i < REACH_STAGES.length; i++) { if (total >= REACH_STAGES[i][0]) idx = i; else if (!next) next = REACH_STAGES[i]; }
    var from = idx >= 0 ? REACH_STAGES[idx][0] : 0, to = next ? next[0] : from, seg = 100 / REACH_STAGES.length;
    var pct = next ? seg * (idx + 1) + seg * Math.min(1, Math.max(0, (total - from) / Math.max(1, to - from))) : 100;
    return { cur: idx >= 0 ? REACH_STAGES[idx] : null, next: next, pct: Math.round(pct * 10) / 10 };
  }
  function reachHTML(d) {
    var st = d.stats, tr = d.trend || {}, reach = (tr.reach || []).map(Number), n = reach.length, rsum = Number(tr.reach30 || 0);
    var wk = [0, 0, 0, 0], peakIdx = -1, peakV = 0;
    for (var j = 0; j < n; j++) { var ago = n - 1 - j, b = Math.min(3, Math.floor(ago / 7)); wk[b] += reach[j] || 0; if ((reach[j] || 0) > peakV) { peakV = reach[j]; peakIdx = j; } }
    var wmax = Math.max.apply(null, wk.concat([1])), radii = [11, 20, 29, 38], rings = '';
    for (var i = 3; i >= 0; i--) rings += '<circle class="r" cx="42" cy="42" r="' + radii[i] + '" stroke-width="' + (wk[i] ? (1.2 + 1.3 * wk[i] / wmax).toFixed(1) : '1') + '" style="opacity:' + (wk[i] ? (0.35 + 0.65 * wk[i] / wmax).toFixed(2) : '0.14') + ';animation-delay:' + (i * 0.45) + 's"><title>' + (i === 0 ? '이번 주' : i === 3 ? '3주 전과 그 이전' : i + '주 전') + ' ' + wk[i] + '명</title></circle>';
    var up = wk[0] > wk[1] && wk[0] > 0;
    var stage = reachStage(Number(st.reachAll || 0)), ticks = '', labels = '';
    REACH_STAGES.forEach(function (s, k) { var at = (k + 1) * (100 / REACH_STAGES.length); ticks += '<b class="' + (Number(st.reachAll || 0) >= s[0] ? 'on' : '') + '" style="left:' + at + '%"></b>'; labels += '<span style="left:' + at + '%">' + num(s[0]) + '</span>'; });
    var peakDay = ''; if (peakIdx >= 0 && tr.reachFrom) { var pd = dateOf(tr.reachFrom); if (pd) { pd.setDate(pd.getDate() + peakIdx); peakDay = fmtMD(pd); } }
    return '<div class="lg-trend-box lg-reach"><div class="lg-trend-h"><span>AI 윤리 확산</span><em>' + num(rsum) + '<small>명</small></em></div>' +
      '<div class="lg-reach-body"><svg class="lg-ripple" viewBox="0 0 84 84" aria-hidden="true">' + rings + '<circle class="c" cx="42" cy="42" r="4.5"/></svg>' +
      '<div class="lg-reach-txt"><p>최근 30일, 위원님의 명함 · 링크로 AI 윤리를 접한 사람</p><div class="lg-reach-wk"><span>이번 주 <b>' + num(wk[0]) + '</b></span><span>지난주 <b>' + num(wk[1]) + '</b></span>' + (up ? '<i>상승</i>' : '') + '</div>' +
      (rsum ? (peakDay ? '<small>가장 많이 닿은 날 ' + esc(peakDay) + ' · ' + num(peakV) + '명</small>' : '') : '<small>명함 · 링크가 열릴 때마다 한 사람에게 더 닿습니다</small>') + '</div></div></div>' +
      '<div class="lg-reach-ms"><div class="lg-reach-ms-h"><span>확산 단계 · <b>' + (stage.cur ? stage.cur[1] : '첫 물결을 준비 중') + '</b></span><em>누적 ' + num(st.reachAll || 0) + '명' + (stage.next ? ' · ' + esc(stage.next[1]) + '(' + num(stage.next[0]) + '명)까지 ' + num(stage.next[0] - Number(st.reachAll || 0)) + '명' : ' · 최고 단계') + '</em></div>' +
      '<div class="lg-ms-track"><i style="width:' + stage.pct + '%"></i>' + ticks + '</div><div class="lg-ms-labels">' + labels + '</div></div>';
  }
  function trendHTML(d) {
    var st = d.stats, m = d.member, tr = d.trend || {}, today = new Date();
    var weeks = [0, 0, 0, 0, 0, 0, 0, 0], wsum = 0, t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    (d.credits || []).forEach(function (r) { if (r.status !== '대기' && r.status !== '확정') return; var dt = new Date(String(r.day).replace(/-/g, '/')); if (isNaN(dt)) return; var ago = Math.floor((t0 - dt.getTime()) / 86400000); if (ago < 0) ago = 0; var w = Math.floor(ago / 7); if (w < 8) { weeks[7 - w]++; wsum++; } });
    var max = Math.max.apply(null, weeks.concat([1])), bars = '';
    for (var i = 0; i < 8; i++) { var h = weeks[i] ? Math.max(6, Math.round(weeks[i] / max * 44)) : 2; bars += '<rect x="' + (4 + i * 30) + '" y="' + (50 - h) + '" width="22" height="' + h + '" rx="3" class="' + (weeks[i] ? (i === 7 ? 'on now' : 'on') : 'off') + '"><title>' + (7 - i === 0 ? '이번 주' : (7 - i) + '주 전') + ' ' + weeks[i] + '건</title></rect>'; }
    return '<div class="lg-trend"><div class="lg-trend-box"><div class="lg-trend-h"><span>최근 8주 추천 성과</span><em>' + num(wsum) + '건</em></div>' +
      '<svg class="lg-bars" viewBox="0 0 240 56" preserveAspectRatio="none" aria-hidden="true"><line x1="0" y1="50.5" x2="240" y2="50.5"/>' + bars + '</svg><div class="lg-trend-x"><span>8주 전</span><span>이번 주</span></div>' +
      (wsum ? '<p class="lg-trend-empty">추천으로 시작한 사람 · ' + (CONFIRM_D > 0 ? '결제 뒤 ' + CONFIRM_D + '일 확정' : '결제 즉시 확정') + '</p>' : '<p class="lg-trend-empty">첫 추천 성과가 생기면 여기에 쌓입니다</p>') + '</div>' +
      reachHTML(d) +
      '<div class="lg-trend-kpis"><span>위촉 ' + num(tr.joinedDays || 0) + '일째</span>' + (CONFIRM_D > 0 || m.pending ? '<span>확정 대기 ' + num(m.pending || 0) + '건</span>' : '<span>확정 ' + num(m.credits || 0) + '건</span>') + '<span>7일 확산 ' + num(st.reach7 || 0) + '명</span><span>다음 정산 ' + (st.nextPayDay ? fmtKo(st.nextPayDay, true) : '목요일') + '</span></div></div>';
  }
  function renderDash() {
    var d = S.data, m = d.member, st = d.stats, set = d.settings, code = m.code;
    PAY_WD = set && set.payWeekday != null && !isNaN(+set.payWeekday) ? +set.payWeekday : 4; CONFIRM_D = set && set.confirmDays != null && !isNaN(+set.confirmDays) ? +set.confirmDays : 0;   /* 1.3.3 */
    var first = (m.name || '?').replace(/[^가-힣A-Za-z]/g, '').slice(0, 1) || '·';
    var title = heroTier(m.title || m.tier), org = m.org || '한국AI윤리위원회(KAIEC)';
    /* 머리 카드 동그라미: 위원 본인 사진(명단과 같은 사진, 2026.09.30 사용자 '최가 아니라 각각 위원 본인의 사진'). 사진이 없거나 못 불러오면 이름 첫 글자 */
    var photo = (CFG.photos || {})[code];
    var avatar = '<div class="lg-avatar' + (m.badge ? ' lg-avatar--' + esc(m.badge) : '') + (photo ? ' lg-avatar--photo' : '') + '" data-first="' + esc(first) + '">' +
      (photo ? '<img src="/assets/img/members/' + encodeURIComponent(photo) + (CFG.photoV ? '?v=' + encodeURIComponent(CFG.photoV) : '') + '" alt="' + esc(m.name) + ' 위원 사진" width="64" height="64" decoding="async">' : esc(first)) + '</div>';
    hero.innerHTML = heroHTML('위원 라운지', esc(m.name) + ' 위원님, 반갑습니다', esc(title) + ' · 위촉 ' + esc(m.since) + ' · 위원 코드 ' + esc(code),
      '<div class="lg-who">' + avatar + '<div><b>' + esc(m.name) + ' <small class="lg-who-t">위원</small></b><span>' + esc(org) + '</span><br>' + tierChip(m.badge, m.title || m.tier, true) + '</div><button type="button" class="btn btn-light btn-sm" id="lgLogout" style="margin-left:8px">로그아웃</button></div>');
    var avImg = hero.querySelector('.lg-avatar img');
    if (avImg) avImg.addEventListener('error', function () { var a = avImg.parentNode; if (!a) return; a.classList.remove('lg-avatar--photo'); a.textContent = a.getAttribute('data-first') || ''; });
    /* 활동 게이지(2026.09.30 사용자: 30일 0건 → 휴면 → 10일 뒤 자동 해제에 맞추되 너무 조급한 느낌은 없게): 서버가 자격 기준 날짜로 계산(추천 결제 뒤 처음 10일은 100%,
       그 뒤 해제일까지 천천히). 남은 날 카운트다운 · 빨간 경고 없이 '여유 있음 → 다음 추천을 기다리는 중 → 휴면(추천 1건이면 바로 복귀)' */
    var gv = Math.max(0, Math.min(100, Number(m.gauge) || 0)), mcx = d.minCredit || {};
    var gaugeCls = m.status === '종료' ? 'is-off' : (m.status === '휴면' || m.status === '휴면예정') ? 'is-low' : '';
    /* 2026.10.03 사용자 '라운지에 막 여유 있음 이런 것보다는 활동을 자연스럽게 유도하는 그런 게 좀 있어야 될 것 같아, 기분 좋게': 게이지 옆 말은 긍정형
       (최근 추천이 있으면 '좋은 흐름이에요', 아니면 '지금 시작하기 좋은 때', 낮으면 '한 걸음이면 다시 가득'), 아래 설명 줄 자리에는 '오늘의 한 걸음'(nudgeHTML).
       게이지 기준 설명은 '활동 게이지' 글자에 마우스를 올리면 보이고, 자세한 기준은 맨 아래 카드 그대로 */
    var gaugeTxt = m.status === '활동' ? gv + '% · ' + (gv < 60 ? '한 걸음이면 다시 가득' : recentCredit(d) ? '좋은 흐름이에요' : '지금 시작하기 좋은 때') : m.status === '휴면' ? '휴면 · 추천 1건이면 바로 복귀' : m.status === '휴면예정' ? '휴면 예정 · 추천 1건이면 그대로' : '종료';
    var gaugeTip = (mcx.first ? '첫 추천을 기다리는 중입니다. ' : mcx.last ? '마지막 추천 실적 ' + fmtKo(mcx.last, true) + '. ' : '') + '추천 결제 1건마다 게이지가 가득 차고, 그 뒤 ' + (set.gaugeFullDays || 10) + '일은 그대로 유지됩니다. 자세한 기준은 맨 아래 \'위원 자격 · 활동 기준\'에 있습니다.';
    var nt = st.next, tiers = set.tiers, cur = m.credits;
    var stepFrom = nt ? (nt.at === tiers[0] ? 0 : nt.at === tiers[1] ? tiers[0] : tiers[1]) : tiers[2], stepTo = nt ? nt.at : tiers[2];
    var stepsN = Math.max(1, Math.min(10, stepTo - stepFrom)), stepsOn = nt ? Math.round((cur - stepFrom) / (stepTo - stepFrom) * stepsN) : stepsN;
    var stepsHtml = ''; for (var i = 0; i < stepsN; i++) stepsHtml += '<i class="' + (i < stepsOn ? 'on' : '') + '"></i>';
    var lastSig = m.lastSignal ? fmtKo(m.lastSignal) + '(' + esc(m.lastKind || '활동') + ')' : '아직 없음';
    var intro = d.links.intro, card = d.links.card, go = d.links.go, experts = d.links.experts || (SITE + '/experts/?ref=' + m.code);
    var tpl = MSG_TPL[S.kitTab][1].replace(/\{intro\}/g, intro);
    var payNeeded = d.payinfo.needed && !d.payinfo.registered;
    var payCard = payNeeded ? payinfoFormHTML(d, true) :
      '<div class="lg-card" id="lgPayCard"><h2>' + ic('credit-card') + '정산</h2><div class="lg-pay"><div><span>다음 정산 예정</span><b>' + won(st.nextPay) + '</b><i>' + (st.nextPay > 0 ? fmtKo(st.nextPayDay, true) : '확정 실적이 생기면 표시') + '</i></div><div><span>누적 지급</span><b>' + won(st.totalPaid) + '</b><i>' + (st.lastPaid ? st.lastPaid.count + '건 · 마지막 ' + fmtKo(st.lastPaid.day, true) : '아직 없음') + '</i></div></div>' +
      '<p style="margin-top:14px">' + (d.payinfo.registered ? '정산 정보 <b>' + esc(d.payinfo.bankMasked) + '</b> 등록됨 · <button type="button" class="lg-link" data-act="payinfo-edit">변경</button><br>' : '') + (CONFIRM_D > 0 ? '결제 뒤 ' + CONFIRM_D + '일이 지나고 취소가 없으면 확정되며, 확정 건은 <b>매주 ' + DAYS[PAY_WD] + '요일</b>에 지급됩니다. ' : '위원 코드로 결제가 들어오면 <b>그 자리에서 확정</b>되고, <b>' + cutDay() + '요일 24시</b>까지 결제된 건을 모아 <b>매주 ' + DAYS[PAY_WD] + '요일</b>에 지급합니다. 환불된 건은 지급에서 빠집니다. ') + '활동지원금은 건당 ' + won(st.payRate) + (m.badge === '앰버서더' ? '(앰버서더)' : '') + '입니다.</p>' +
      '<span class="lg-note">활동지원금은 세금 없이 그대로 받습니다. 소득 처리 · 신고 · 원천징수는 성균관컨설팅이 맡고 세액도 위원회가 부담합니다. 활동에만 집중하세요.</span>' +
      '<div id="lgPayForm" hidden></div>' +
      '<div class="lg-cert"><h2>' + ic('file-check') + '활동증명서</h2><p>위촉 뒤 ' + Math.round(set.certDays / 30) + '개월 이상 활동한 위원에게 위원장 명의 · 위원장 직인의 활동증명서를 발급합니다.</p>' +
      (d.cert.eligible ? '<button type="button" class="btn btn-ghost btn-sm" data-act="cert" style="margin-top:10px">활동증명서 발급 요청</button>' : '<button type="button" class="btn btn-ghost btn-sm" disabled style="margin-top:10px;color:var(--gray-400);border-color:#E5E9F0">활동증명서 발급 요청</button> <span style="font-size:12px;color:var(--gray-500);margin-left:6px">' + esc(d.cert.from) + '부터 발급됩니다</span>') + '</div></div>';
    var notices = (d.notices || []).map(function (n) { return '<div class="lg-notice"><b>' + esc(n.title) + '</b><p>' + esc(n.body) + (n.link ? ' <a href="' + esc(n.link) + '" target="_blank" rel="noopener" style="color:var(--blue);font-weight:700">자세히 →</a>' : '') + '</p><small>공지 · ' + fmtMD(n.at) + '</small></div>'; }).join('');
    // 2026.09.30 운영자 미리보기(백엔드 1.3.2 preview): 위원 화면을 읽기 전용으로 볼 때 맨 위에 띠
    var pvBar = d.preview ? '<div class="lg-preview" role="note">' + ic('eye') + '<span><b>위원장 미리보기</b> · ' + esc(d.preview.name || m.name) + ' 위원(' + esc(d.preview.code || code) + ') 화면입니다. 읽기 전용이라 바꿀 수 없고, 위원 활동 기록과 통계에 남지 않습니다.</span></div>' : '';
    main.innerHTML = pvBar +
      '<div class="lg-grid">' +
      '<div class="lg-card"><h2>' + ic('trending-up') + '나의 임팩트</h2><div class="lg-big">당신의 추천으로 AI 윤리를 배우기 시작한 사람<strong>' + num(m.credits) + '<small>명</small></strong><span class="lg-sub">누적 임팩트 크레딧 ' + num(m.credits) + (m.pending ? ' · 확정 대기 ' + m.pending : '') + (m.canceled ? ' · 취소 ' + m.canceled : '') + '</span></div>' +
      '<div class="lg-stats"><div class="lg-stat"><span>이달 크레딧</span><b>' + num(st.thisMonth) + '</b><i>' + (m.credits === 0 ? '첫 임팩트를 기다립니다' : '확정 기준') + '</i></div><div class="lg-stat"><span>누적 확산</span><b>' + num(st.reachAll) + '</b><i>명함 · 링크로 접한 사람 · 최근 7일 ' + num(st.reach7) + '명</i></div><div class="lg-stat"><span>다음 등급까지</span><b>' + (nt ? num(nt.need) : '-') + '</b><i>' + (nt ? esc(heroTier(nt.name)) + ' (' + nt.at + ')' : '최고 등급입니다') + '</i></div></div>' +
      '<div class="lg-tierline"><span>' + esc(nt ? (stepFrom === 0 ? 'AI 캠페인위원' : stepFrom === tiers[0] ? 'AI 선임위원' : 'AI 책임위원') : 'AI 책임위원') + '</span><div class="lg-steps">' + stepsHtml + '</div><span>' + esc(nt ? heroTier(nt.name) : 'AI 수석위원') + '</span></div>' +
      '<div class="lg-gauge"><div class="lg-gauge-h"><span title="' + esc(gaugeTip) + '">활동 게이지</span><em class="' + gaugeCls + '">' + gaugeTxt + '</em></div><div class="lg-bar"><i style="width:' + (m.status === '활동' || m.status === '휴면' || m.status === '휴면예정' ? gv : 0) + '%"></i></div>' + (m.status === '종료' ? '' : nudgeHTML(d)) + '</div>' + trendHTML(d) + '</div>' +
      '<div class="lg-card lg-kit" id="kit"><h2>' + ic('send') + 'AI 윤리 확산 도구</h2>' +
      '<div class="row"><span class="lab">위원 명함</span><code>' + esc(short(card)) + '</code><button type="button" class="btn btn-ghost" data-copy="' + esc(card) + '">복사</button></div>' +
      '<div class="row"><span class="lab">바로 결제 링크</span><code>' + esc(short(go)) + '</code><button type="button" class="btn btn-ghost" data-copy="' + esc(go) + '">복사</button></div>' +
      '<div class="row"><span class="lab">소개 페이지</span><code>' + esc(short(intro)) + '</code><button type="button" class="btn btn-ghost" data-copy="' + esc(intro) + '">복사</button></div>' +
      '<div class="row"><span class="lab">AIEP 안내 페이지</span><code>' + esc(short(experts)) + '</code><button type="button" class="btn btn-ghost" data-copy="' + esc(experts) + '">복사</button></div>' +
      '<div class="row"><span class="lab">위원 명함 · QR</span><code>명단의 내 명함에서 [명함 이미지 저장]</code><a class="btn btn-primary" href="' + esc(card.replace('#', '?save=1#')) + '" target="_blank" rel="noopener" data-track="open:qr">열기</a></div>' +
      '<div class="lg-tabs" id="lgKitTabs">' + MSG_TPL.map(function (t, i) { return '<button type="button" class="' + (i === S.kitTab ? 'on' : '') + '" data-tab="' + i + '">' + t[0] + '</button>'; }).join('') + '</div>' +
      '<div class="lg-msg" id="lgMsg"><button type="button" class="btn btn-ghost" data-copy-msg="1">복사</button>' + esc(tpl) + '</div></div></div>' +
      '<div class="lg-two"><div class="lg-card"><h2>' + ic('clipboard-list') + '실적 내역<span class="sub">결제 시 메일 알림 · ' + ruleShort() + '</span></h2>' +
      (d.credits.length ? '<table class="lg-tbl"><thead><tr><th>결제일</th><th>상태</th><th class="num">활동지원금</th><th class="num">정산</th></tr></thead><tbody>' + d.credits.map(creditRow).join('') + '</tbody></table>' : '<p class="lg-empty" style="text-align:center;padding:26px 0">아직 실적이 없습니다. 명함이나 추천 링크를 공유해 보세요. 첫 결제가 들어오면 이메일로 알려 드립니다.</p>') + '</div>' + payCard + '</div>' +
      '<div class="lg-two"><div class="lg-card"><h2>' + ic('external-link') + '활동 공유 <span style="font-size:12px;color:var(--gray-500);font-weight:600">(선택)</span></h2><p>AI 윤리와 관련해 올리신 글 · 영상 링크를 남겨 주세요. 위원회 소식에 인용될 수 있습니다.</p><form class="lg-share-in" id="lgShare"><input class="lg-input" id="lgShareUrl" type="url" placeholder="https://" maxlength="300"><button type="submit" class="btn btn-ghost btn-sm">등록</button></form></div>' +
      '<div class="lg-card"><h2>' + ic('help-circle') + '안내 · 공지</h2>' + (notices || '<p class="lg-muted" style="font-size:13px">새 공지가 없습니다.</p>') +
      '<ul class="lg-list" style="margin-top:10px"><li><a href="' + MANUAL_URL + '" target="_blank" rel="noopener" data-track="manual">캠페인위원 활동 매뉴얼(PDF) 내려받기</a> · 라운지 사용법 · 활동 · 정산 · 자격 기준을 한 권에<span>매뉴얼</span></li><li>위원 코드로 결제가 들어오면 바로 확정되고 이메일로 알려 드리며, 지급 때도 메일이 갑니다<span>안내</span></li><li>' + cutDay() + '요일 24시까지 결제된 건을 매주 ' + DAYS[PAY_WD] + '요일에 정산하며, 세금은 위원회에서 부담하여 전액 지급됩니다.<span>안내</span></li><li>위원 자격 · 활동 기준은 이 화면 맨 아래에 있습니다<span>기준</span></li><li>문의는 <a href="mailto:' + EMAIL + '">' + EMAIL + '</a><span>1일 안 회신</span></li></ul>' +
      '<label class="lg-toggle" style="margin-top:14px"><input type="checkbox" id="lgLetter"' + (m.letter ? ' checked' : '') + '> 월간 임팩트 리포트 메일 받기</label></div></div>' +
      rulesHTML(d) +
      '<p class="lg-foot">이 화면의 숫자는 본인에게만 보입니다. 다른 위원의 실적 · 정산은 서로 볼 수 없습니다.</p>';
    show('main');
    $('lgLogout').onclick = logout;
    main.onclick = onDashClick;
    $('lgShare').addEventListener('submit', function (e) {
      e.preventDefault(); var u = $('lgShareUrl').value.trim(), b = e.target.querySelector('button');
      if (!/^https?:\/\/\S+$/i.test(u)) { toast('https:// 로 시작하는 주소를 넣어 주세요', 'warn'); return; }
      busy(b, true); call('me.link', { url: u }).then(function () { busy(b, false); $('lgShareUrl').value = ''; toast('링크를 등록했습니다', 'ok'); }, function (er) { busy(b, false); toast(er.message, 'danger'); });
    });
    $('lgLetter').addEventListener('change', function () { var on = this.checked; call('me.prefs', { letter: on }).then(function () { toast(on ? '리포트 메일을 받습니다' : '리포트 메일을 받지 않습니다'); }, function (er) { toast(er.message, 'danger'); }); });
    var pf = $('lgPayFormEl'); if (pf) bindPayForm(pf);
  }
  /* 오늘의 한 걸음(2026.10.03 사용자 '활동을 자연스럽게 유도하는 그런 게, 기분 좋게'): 위원 상황에 맞는 제안 하나 + 바로 하기 버튼(확산 도구와 같은 복사 · 사용 기록).
     최근 추천 · 다음 직함이 가까움 · 첫 추천 전이면 그 제안을 먼저, 아니면 날마다 바뀌는 제안(같은 날은 같은 것). [다른 제안]으로 넘겨 봄. 휴면 중이면 복귀 안내 */
  function recentCredit(d) { var mc = d.minCredit || {}, last = dateOf(mc.last), today = dateOf(new Date()); return !!(last && today && (today - last) / 86400000 <= ((d.settings || {}).gaugeFullDays || 10)); }
  function nudgeList(d) {
    /* 2판(2026.10.03 사용자 '카톡 프로필에 누가 명함을 올려 부담스럽게 · 준비된 문안도 별로 · 충분이라는 말을 함부로 쓰지 마'): 일상에서 자연스럽게 알리는 제안으로 */
    var m = d.member, st = d.stats || {}, mc = d.minCredit || {}, L = d.links || {}, nt = st.next, reach = Number(st.reachAll) || 0, top = [], out = [];
    var experts = L.experts || (SITE + '/experts/?ref=' + m.code);
    if (m.status === '휴면' || m.status === '휴면예정') return [
      { t: '명단 · 명함이 잠시 숨겨져 있어요. ' + (mc.graceEnd ? fmtKo(mc.graceEnd, true) + '까지 ' : '') + '위원 코드로 결제 1건(본인 결제 포함)이면 바로 돌아옵니다. 필요한 분께 바로 신청 링크를 건네 보세요.', b: ['바로 신청 링크 복사', 'copy', L.go] },
      { t: 'AIEP 안내 페이지를 함께 보내면 처음 듣는 분도 과정을 쉽게 이해합니다.', b: ['안내 페이지 링크 복사', 'copy', experts] }];
    if (recentCredit(d)) top.push({ t: '최근 추천 감사합니다! 소개받은 분이 지금 AI 윤리를 공부하고 있어요. 주변에 도움이 될 분이 또 계신지 떠올려 보세요.', b: ['바로 신청 링크 복사', 'copy', L.go] });
    if (nt && nt.need <= 2 && m.credits > 0) top.push({ t: heroTier(nt.name) + '까지 ' + nt.need + '건 남았어요. 가까운 분께 가볍게 소개해 보세요.', b: ['바로 신청 링크 복사', 'copy', L.go] });
    if (mc.first) top.push({ t: '첫 소개는 가장 가까운 분부터 시작해 보세요. 위원으로 활동하게 된 소식을 전하며 명함 링크를 함께 보내면 자연스럽습니다.', b: ['명함 링크 복사', 'copy', L.card] });
    out.push({ t: '요즘 AI 이야기가 나오면 \'AI도 바르게 쓰는 법을 배우는 과정이 있더라\' 하고 가볍게 이야기해 보세요. 안내 페이지를 함께 보내면 이해가 쉽습니다.', b: ['안내 페이지 링크 복사', 'copy', experts] });
    if (!mc.first) out.push({ t: '가까운 분들께 한국AI윤리위원회 위원으로 활동하게 된 소식을 전하며 명함 링크를 함께 보내 보세요.', b: ['명함 링크 복사', 'copy', L.card] });   /* 첫 소개 제안과 겹치지 않게 */
    out.push({ t: reach > 0 ? '내 명함 · 링크로 ' + num(reach) + '명이 AI 윤리를 만났어요. 관심을 보인 분께 바로 신청 링크를 건네 보세요.' : '취업을 준비하는 대학생, 업무에 AI를 쓰는 지인 한 분께 바로 신청 링크를 건네 보세요.', b: ['바로 신청 링크 복사', 'copy', L.go] });
    if (!top.length) { var h = 0, c = String(m.code || ''); for (var i = 0; i < c.length; i++) h = (h * 31 + c.charCodeAt(i)) % 997; var k = (Math.floor(Date.now() / 86400000) + h) % out.length; out = out.slice(k).concat(out.slice(0, k)); }
    return top.concat(out);
  }
  function nudgeHTML(d) {
    var list = nudgeList(d); if (!list.length) return '';
    var n = list[(S.nudgeI || 0) % list.length];
    var btn = '<button type="button" class="btn btn-primary btn-xs" ' + (n.b[1] === 'tpl' ? 'data-copy-tpl="' + n.b[2] + '"' : 'data-copy="' + esc(n.b[2]) + '"') + '>' + esc(n.b[0]) + '</button>';
    return '<div class="lg-nudge" id="lgNudge"><span class="lg-nudge-ic">' + ic('sparkles') + '</span><div class="lg-nudge-t"><b>오늘의 한 걸음</b><span>' + esc(n.t) + '</span></div>' +
      '<div class="lg-nudge-act">' + btn + (list.length > 1 ? '<button type="button" class="lg-nudge-next" data-act="nudge-next" title="다른 제안 보기" aria-label="다른 제안 보기">' + ic('refresh-cw') + '</button>' : '') + '</div></div>';
  }
  /* 도구 사용 기록(2026.09.29 밤, 백엔드 1.3.0 me.event): 어떤 링크 · 문안을 쓰는지 운영자 분석에 쌓임(항목별 하루 1회, 실패해도 조용히) */
  function track(kind) { try { call('me.event', { kind: kind }).catch(function () {}); } catch (e) { /* 무시 */ } }
  function linkKind(url) { var l = (S.data && S.data.links) || {}; return url === l.card ? 'card' : url === l.go ? 'go' : url === l.intro ? 'intro' : url === l.experts ? 'experts' : ''; }
  function onDashClick(e) {
    var b = e.target.closest('button,a'); if (!b) return;
    if (b.hasAttribute('data-track')) { track(b.getAttribute('data-track')); return; }
    if (b.hasAttribute('data-copy')) { var u = b.getAttribute('data-copy'); copyText(u, b); if (linkKind(u)) track('copy:' + linkKind(u)); return; }
    if (b.hasAttribute('data-copy-msg')) { copyText(MSG_TPL[S.kitTab][1].replace(/\{intro\}/g, S.data.links.intro), b); track('copy:msg:' + MSG_TPL[S.kitTab][0]); return; }
    if (b.hasAttribute('data-copy-tpl')) { var ti = +b.getAttribute('data-copy-tpl') || 0; copyText(MSG_TPL[ti][1].replace(/\{intro\}/g, S.data.links.intro), b); track('copy:msg:' + MSG_TPL[ti][0]); return; }
    if (b.hasAttribute('data-tab')) { S.kitTab = +b.getAttribute('data-tab'); var tabs = $('lgKitTabs'); Array.prototype.forEach.call(tabs.children, function (c) { c.classList.toggle('on', +c.getAttribute('data-tab') === S.kitTab); }); var box = $('lgMsg'); box.innerHTML = '<button type="button" class="btn btn-ghost" data-copy-msg="1">복사</button>' + esc(MSG_TPL[S.kitTab][1].replace(/\{intro\}/g, S.data.links.intro)); return; }
    var act = b.getAttribute('data-act');
    if (act === 'nudge-next') { S.nudgeI = (S.nudgeI || 0) + 1; var nb = $('lgNudge'); if (nb) { nb.outerHTML = nudgeHTML(S.data); var nb2 = $('lgNudge'); if (nb2) nb2.classList.add('is-new'); } return; }
    if (act === 'cert') { busy(b, true); call('me.cert').then(function (j) { busy(b, false); toast(j.message || '발급 요청을 받았습니다', 'ok'); }, function (er) { busy(b, false); toast(er.message, 'danger'); }); }
    if (act === 'payinfo-edit') { var box2 = $('lgPayForm'); box2.hidden = false; box2.innerHTML = payinfoFormHTML(S.data, false); bindPayForm($('lgPayFormEl')); box2.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    if (act === 'payinfo-cancel') { var box3 = $('lgPayForm'); if (box3) { box3.hidden = true; box3.innerHTML = ''; } }
  }
  var BANKS = ['국민', '신한', '우리', '하나', '농협', '기업', 'SC제일', '씨티', '카카오뱅크', '토스뱅크', '케이뱅크', '새마을금고', '신협', '우체국', '수협', '부산', '대구', '경남', '광주', '전북', '제주', '산업', '저축은행', '기타'];
  function payinfoFormHTML(d, first) {
    var st = d.stats, opts = BANKS.map(function (b) { return '<option value="' + b + '">' + b + '</option>'; }).join('');
    var head = first ? '<h2>' + ic('credit-card') + '정산 정보 등록 <span class="lg-chip lg-chip--wait" style="margin-left:auto">지급 대기 ' + won(st.nextPay) + '</span></h2><p style="font-size:14.5px;font-weight:700;color:var(--ink)">첫 활동지원금 ' + won(st.nextPay) + '이 목요일 지급을 기다리고 있습니다.</p>' : '<h2 style="font-size:15px">정산 정보 변경</h2>';
    return '<div class="' + (first ? 'lg-card lg-card--hi' : '') + '" style="' + (first ? '' : 'margin-top:14px;padding-top:14px;border-top:1px solid #EEF1F6') + '">' + head +
      '<p style="margin-top:6px">지급을 위해 계좌와 주민등록번호를 <b>한 번만</b> 등록해 주세요. 주민등록번호는 세금 신고(원천징수 지급명세서)에만 쓰이고 암호화되어 보관되며 정산 담당자 외에는 볼 수 없습니다. <b>세금은 위원회가 부담하므로 위원님이 내실 세금은 없습니다.</b> 등록이 끝나면 ' + (st.nextPayDay ? fmtKo(st.nextPayDay, true) : '다음 목요일') + '에 지급됩니다.</p>' +
      '<form id="lgPayFormEl" novalidate><div class="lg-form-grid"><div class="lg-field"><label for="pfHolder">예금주</label><input class="lg-input" id="pfHolder" maxlength="40" value="' + esc(d.member.name) + '"></div><div class="lg-field"><label for="pfBank">은행</label><select class="lg-input" id="pfBank"><option value="">선택</option>' + opts + '</select></div><div class="lg-field"><label for="pfAcct">계좌번호</label><input class="lg-input" id="pfAcct" inputmode="numeric" placeholder="숫자만 입력" maxlength="30"></div><div class="lg-field"><label for="pfRrn">주민등록번호</label><input class="lg-input" id="pfRrn" inputmode="numeric" placeholder="000000-0000000" maxlength="14" autocomplete="off"></div></div>' +
      '<label class="lg-consent"><input type="checkbox" id="pfConsent"><span>활동지원금 지급과 세금 신고를 위한 개인정보 수집 · 이용에 동의합니다. 항목: 예금주 · 은행 · 계좌번호 · 주민등록번호 / 목적: 활동지원금 지급, 원천징수 신고 / 보유: 위촉 종료 뒤 세법상 보존 기간(5년)까지, 이후 자동 삭제 / 근거: 소득세법의 지급명세서 제출 의무. 자세한 내용은 <a href="' + SITE + '/privacy/" target="_blank" rel="noopener" style="color:var(--blue);font-weight:700">개인정보처리방침</a></span></label>' +
      '<p class="lg-err" id="pfErr"></p><div class="lg-btnrow" style="margin-top:12px"><button type="submit" class="btn btn-primary btn-sm" style="flex:0 1 auto">' + (first ? '등록하고 목요일에 받기' : '저장') + '</button>' + (first ? '' : '<button type="button" class="btn btn-ghost btn-sm" data-act="payinfo-cancel" style="flex:0 1 auto">취소</button>') + '</div></form></div>';
  }
  function bindPayForm(f) {
    var rrn = f.querySelector('#pfRrn');
    rrn.addEventListener('input', function () { var v = this.value.replace(/\D/g, '').slice(0, 13); this.value = v.length > 6 ? v.slice(0, 6) + '-' + v.slice(6) : v; });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var holder = f.querySelector('#pfHolder').value.trim(), bank = f.querySelector('#pfBank').value, acct = f.querySelector('#pfAcct').value.trim(), r = rrn.value.replace(/\D/g, ''), ok = f.querySelector('#pfConsent').checked, er = f.querySelector('#pfErr');
      function fail(msg) { er.textContent = msg; er.classList.add('is-on'); }
      er.classList.remove('is-on');
      if (!holder) return fail('예금주를 입력해 주세요.');
      if (!bank) return fail('은행을 골라 주세요.');
      if (acct.replace(/\D/g, '').length < 8) return fail('계좌번호를 확인해 주세요.');
      if (r.length !== 13) return fail('주민등록번호 13자리를 입력해 주세요.');
      if (!ok) return fail('개인정보 수집 · 이용에 동의해 주세요.');
      var b = f.querySelector('button[type="submit"]'); busy(b, true);
      call('me.payinfo', { holder: holder, bank: bank, account: acct, rrn: r, consent: true }).then(function (j) { toast('정산 정보를 등록했습니다 · ' + fmtKo(j.nextPayDay, true) + ' 지급', 'ok'); loadDash(); }, function (e2) { busy(b, false); fail(e2.message); });
    });
  }

  /* ---------- 운영자 ---------- */
  function renderAdminLogin(msg) {
    hero.hidden = true;
    login.innerHTML = '<div class="lg-lbox"><div class="lg-lhead"><div class="lg-eyebrow">KAIEC CHAIR</div><h1>위원장 대시보드</h1><p>위원 활동 시스템 · 정산 · 명단 · 공지</p></div><div class="lg-lbody"><form id="lgAForm" novalidate><div class="lg-field"><label for="lgAPw">위원장 비밀번호</label><input class="lg-input" id="lgAPw" type="password" autocomplete="current-password" maxlength="64"></div><p class="lg-err' + (msg ? ' is-on' : '') + '" id="lgErr">' + esc(msg || '') + '</p><div class="lg-btnrow"><button type="submit" class="btn btn-primary" id="lgGo">로그인</button></div><p class="lg-help" style="margin-top:12px"><a href="' + SITE + '/lounge/" style="color:var(--blue);font-weight:700">위원 라운지로</a></p></form></div><div class="lg-lfoot">위원장 전용 화면입니다(아이디 없이 비밀번호만). 위원 정보와 계좌가 보이므로 공용 컴퓨터에서는 쓰지 마세요.<br>비밀번호를 잊으셨으면 파트너 관리 시트 메뉴 [위원 활동 시스템] → [위원장 비밀번호 바꾸기…]에서 새로 정할 수 있습니다.</div></div>';
    show('login');
    if (!API) { login.innerHTML = loginBox('<div class="lg-ready">' + ic('clock') + '<div><b>연결 준비 중</b><br>웹 앱 주소를 사이트에 넣은 뒤 열립니다.</div></div>'); return; }
    setTimeout(function () { $('lgAPw').focus(); }, 50);
    $('lgAForm').addEventListener('submit', function (e) {
      e.preventDefault(); var pw = $('lgAPw').value; if (!pw) { err('비밀번호를 입력해 주세요.'); return; }
      var b = $('lgGo'); busy(b, true);
      call('admin.login', { password: pw, withDash: 1 }).then(function (j) { store(KEY_ADMIN, j.adminToken, true); var d = j.dash; if (d && d.ok && d.tiles && d.roster) { adSeq++; setAdmin(d, false); } else loadAdmin(); }, function (er) { busy(b, false); err(er.message); });
    });
  }
  /* 1.4.4 운영자 화면 속도(사용자 2026.09.30 '관리자 모드 원래 이렇게 오래 걸려? 접속도 새로 고침도'): 위원 라운지처럼 마지막 대시보드를 이 탭에 두었다가
     새로 고침 · 다시 열 때 바로 그리고, 최신 숫자는 뒤에서 받아 바꿈(그동안 화면은 그대로 쓸 수 있음). 계좌번호는 저장하지 않음(새 응답이 오면 채워짐).
     입력 중인 칸이 있는 탭은 다시 그리지 않고 위쪽 타일만 바꿈. 로그인이 끝났거나 12시간 넘은 것은 쓰지 않음 */
  var adSeq = 0;
  function tokenLeft(tok) { try { var b = String(tok || '').split('.')[0].replace(/-/g, '+').replace(/_/g, '/'); while (b.length % 4) b += '='; var e = Number(JSON.parse(atob(b)).e); return isFinite(e) ? e - Date.now() : null; } catch (x) { return null; } }
  function cachedAdmin() {
    try {
      var j = JSON.parse(read(KEY_ADMIN_DASH, true) || 'null'); if (!(j && j.ok && j.tiles && j.roster && j.cachedAt)) return null;
      var left = tokenLeft(read(KEY_ADMIN, true)); if ((left !== null && left < 60000) || Date.now() - j.cachedAt > 12 * 3600000) { store(KEY_ADMIN_DASH, null, true); return null; }
      return j;
    } catch (e) { return null; }
  }
  function saveAdmin(j) {
    try {
      var c = {}; for (var k in j) if (Object.prototype.hasOwnProperty.call(j, k)) c[k] = j[k];
      c.payouts = (j.payouts || []).map(function (p) { var q = {}; for (var x in p) if (Object.prototype.hasOwnProperty.call(p, x)) q[x] = p[x]; if (q.account) { q.account = ''; q.acctWait = 1; } return q; });
      c.cachedAt = Date.now(); store(KEY_ADMIN_DASH, JSON.stringify(c), true);
    } catch (e) { /* 못 두어도 화면은 그대로 */ }
  }
  function hhmm(ms) { var d = new Date(ms); return pad2(d.getHours()) + ':' + pad2(d.getMinutes()); }
  /* 그 영역 안에서 글자를 입력 중이거나 고친 칸이 있으면 true(체크 상자는 누르면 곧바로 처리되므로 보지 않음) */
  function adTabEditing() { return editingIn($('adTab')); }
  function editingIn(t) {
    if (!t) return false;
    var txt = function (el) { return el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || (el.tagName === 'INPUT' && !/^(checkbox|radio|button|submit|reset|hidden|file)$/i.test(el.type || '')); };
    var a = document.activeElement; if (a && t.contains(a) && txt(a)) return true;
    var els = t.querySelectorAll('input, textarea, select');
    for (var i = 0; i < els.length; i++) {
      var el = els[i]; if (!txt(el)) continue;
      if (el.tagName === 'SELECT') { var def = 0; for (var k = 0; k < el.options.length; k++) if (el.options[k].defaultSelected) def = k; if (el.options.length && el.selectedIndex !== def) return true; }
      else if (el.value !== el.defaultValue) return true;
    }
    return false;
  }
  function setAdmin(j, soft) {
    S.admin = j; saveAdmin(j); lastLoadAt = Date.now();
    if (soft && !main.hidden && main.querySelector('#adTab') && adTabEditing()) { renderAdminTop(); return; }
    renderAdmin();
  }
  function loadAdmin(force) {   /* force: 공지 · 설정 · 지급 같은 작업 뒤라 입력 칸까지 모두 새로 그림 */
    lastLoadAt = Date.now();
    var shown = !!S.admin && !main.hidden;
    if (!shown) { var c = cachedAdmin(); if (c) { S.admin = c; renderAdmin(); shown = true; } }
    if (shown) refreshing(true, S.admin.cachedAt ? '지금 화면은 ' + hhmm(S.admin.cachedAt) + ' 기준' : ''); else show('boot');
    var my = ++adSeq;
    return call('admin.dashboard').then(function (j) {
      if (my !== adSeq) return;
      refreshing(false); setAdmin(j, shown && !force);
    }, function (e) {
      if (my !== adSeq) return;
      refreshing(false);
      if (e.relogin || e.code === 'AUTH') { store(KEY_ADMIN_DASH, null, true); S.admin = null; renderAdminLogin(shown ? '로그인 시간이 지났습니다. 다시 로그인해 주세요.' : ''); return; }
      if (shown && S.admin) { renderAdminTop(); toast('최신 정보를 불러오지 못했습니다' + (S.admin.cachedAt ? '(지금 화면은 ' + hhmm(S.admin.cachedAt) + ' 기준)' : '') + ' · ' + e.message, 'danger'); return; }
      renderAdminLogin(e.message);
    });
  }
  function adminLogout() { store(KEY_ADMIN, null, true); store(KEY_ADMIN_DASH, null, true); store(KEY_ADMIN_TAB, null, true); adSeq++; refreshing(false); S.admin = null; S.tab = 'insight'; renderAdminLogin(); }
  /* 1.4.9 메일 칸(사용자 2026.10.01 '여기 20통이라는 게 20통이 남았다는 거야 20통을 사용했다는 거야? 잔여가 안 나와서'): 큰 숫자는 지메일 잔여(남음).
     1.4.11 짧게(사용자 '글씨가 너무 길어져서 못생겨졌잖아'): 아래 한 줄은 오늘 보냄 · 대기, 그 아래 다시 차는 때 · 멈춤 버튼. 자세한 설명은 마우스를 올리면(title).
     무료 지메일은 24시간 100통, 보낸 지 24시간이 지나면 그만큼 다시 생김 */
  function mailTileHTML(a, t) {
    var q = t.mailQuota != null && t.mailQuota >= 0 ? t.mailQuota : null, rf = t.mailRefill, today = a.today || '';
    var refill = rf && rf.at ? String(rf.at).slice(11, 16) : '', refillTxt = refill ? (String(rf.at).slice(0, 10) === today ? '' : '내일 ') + refill + '에 ' + num(rf.n) + '통 다시 생김' : '';
    var tip = '무료 지메일은 24시간 동안 100통까지 보낼 수 있고, 보낸 지 24시간이 지나면 그만큼 다시 생깁니다(0시에 한꺼번에 초기화되지 않음).' + (refillTxt ? '\n다음: ' + refillTxt : '') +
      '\n오늘 보냄은 0시부터 위원 활동 시스템이 보낸 수, 대기는 아직 안 나간 메일입니다.' + (t.mailPaused ? '\n일시정지 중에도 결제 · 정산 알림과 위원장 알림은 바로 나갑니다.' : '');
    var head = '<span>메일 발송' + (t.mailPaused ? ' · <strong class="ad-tile-pause">일시정지</strong>' : '') + '</span>';
    var big = q == null ? num(t.mailToday) + '통 <small class="ad-tile-unit">오늘 보냄</small>' : num(q) + '통 <small class="ad-tile-unit">남음</small>';
    var l1 = q == null ? '대기 ' + num(t.mailWait) + '통' : '오늘 ' + num(t.mailToday) + '통 보냄 · 대기 ' + num(t.mailWait) + '통';
    var acts = t.mailPaused ?
      (t.mailResumeAt ? '<button type="button" class="lg-link" data-act="mailschedule">' + esc(fmtResumeAt(t.mailResumeAt)) + ' 시작</button> · <button type="button" class="lg-link" data-act="mailresume">지금 시작</button>'
        : '<button type="button" class="lg-link" data-act="mailresume">지금 시작</button> · <button type="button" class="lg-link" data-act="mailschedule">시작 예약</button>') :
      (refill && q != null ? refill + ' +' + num(rf.n) + '통 · ' : '') + '<button type="button" class="lg-link" data-act="mailpause">잠시 멈춤</button>';
    return '<div class="ad-tile' + (t.mailPaused ? ' is-paused' : '') + (q != null && q <= 10 ? ' is-low' : '') + '" title="' + esc(tip) + '">' + head + '<b>' + big + '</b><i>' + l1 + '</i><i class="ad-tile-acts">' + acts + '</i></div>';
  }
  function fmtResumeAt(s) { var d = dateOf(s); return d ? (d.getMonth() + 1) + '/' + d.getDate() + '(' + DAYS[d.getDay()] + ') ' + String(s).slice(11, 16) : String(s || ''); }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  /* 발송 시작 예약: 기본값 내일 10:00. 그때까지 대기열은 멈춰 있고, 시각이 지나면 위촉 메일부터 보냄 */
  function scheduleMailResume() {
    var d = new Date(); d.setDate(d.getDate() + 1); d.setHours(10, 0, 0, 0);
    var v = d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + 'T10:00';
    var m = modal('위원 메일 발송 시작 예약', '그 시각까지는 위촉 · 안내 · 공지 메일을 보내지 않고, 시각이 지나면 위촉 메일부터 하루 한도 안에서 순서대로 보냅니다. 결제 · 정산 알림과 위원장 알림 메일은 그동안에도 바로 나갑니다.',
      '<div class="lg-field"><label for="adResumeAt">시작 시각</label><input class="lg-input" id="adResumeAt" type="datetime-local" value="' + v + '" step="600"></div>',
      '<button type="button" class="btn btn-ghost btn-sm" data-act="close">취소</button><button type="button" class="btn btn-primary btn-sm" data-act="ok">예약</button>');
    m.onclick = function (e) {
      var b = e.target.closest('[data-act]'); if (!b) { if (e.target === m) closeModal(); return; }
      if (b.getAttribute('data-act') !== 'ok') { closeModal(); return; }
      var at = ($('adResumeAt').value || '').replace('T', ' ').slice(0, 16);
      if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(at)) { toast('시작 시각을 골라 주세요', 'warn'); return; }
      busy(b, true);
      call('admin.mailResume', { at: at }).then(function (j) { closeModal(); toast(j.result || '예약했습니다', 'ok'); loadAdmin(true); }, function (er) { busy(b, false); toast(er.message, 'danger'); });
    };
  }
  function badgeChip(b) { b = TIER_WORD[b] ? b : tierBadgeOf(b); return b ? '<span class="lg-chip lg-chip--gold">' + esc(TIER_WORD[b] || b) + '</span>' : '<span class="lg-muted" style="font-size:12.5px">AI 윤리 캠페인위원</span>'; }
  function stChip(r) {
    if (r.status === '활동') return '<span class="lg-chip lg-chip--ok">활동</span>';
    var why = r.reason === '최소활동' ? ' · 기준' : '';
    if (r.status === '휴면예정') return '<span class="lg-chip lg-chip--wait">휴면 예정' + why + '</span>';
    if (r.status === '휴면') return '<span class="lg-chip lg-chip--x">휴면' + why + '</span>';
    return '<span class="lg-chip lg-chip--x">종료 ' + fmtMD(r.ended || r.changed) + '</span>';
  }
  function adHeroHTML(a) {
    var todayD = dateOf(a.today), todayTxt = todayD ? todayD.getFullYear() + '년 ' + (todayD.getMonth() + 1) + '월 ' + todayD.getDate() + '일 ' + DAYS[todayD.getDay()] + '요일' : a.today;
    /* 1.4.14 머리 줄 = 위원 일괄 메일 도구(사용자 2026.10.03 '로그아웃은 굳이 없애도 거기에 다 만들어 줘, 위원장 모드도 지워도 되고 … 저기에 잘 구성해야 돼,
       다른 데 공간이 늘어나면 안 되고'): 위 줄은 대상(활동 점수 하위 10 · 20 · 30명 · 전체) + 운영 시트 · 새로 고침, 아래 줄은 세 가지 메일. 누르면 미리 보기 창(화면 위에 떠서 자리를 늘리지 않음).
       로그아웃 단추는 없앰(위원장 로그인은 이 탭에만 있어 창을 닫으면 끝남) */
    var aud = BULK_AUD.map(function (x) { return '<option value="' + x[0] + '"' + (String(S.bulkN) === x[0] ? ' selected' : '') + '>' + x[1] + '</option>'; }).join('');
    var dock = '<div class="ad-dock" role="group" aria-label="위원 일괄 메일">' +
      '<div class="ad-dock-top"><span class="ad-dock-t">' + ic('mail') + '위원 일괄 메일</span>' +
      '<select class="ad-dock-sel" id="adBulkAud" aria-label="보낼 대상" title="활동 점수가 낮은 순(같으면 마지막 활동이 오래된 순)">' + aud + '</select>' +
      '<span class="ad-dock-sys">' + (a.sheetUrl ? '<a href="' + esc(a.sheetUrl) + '" target="_blank" rel="noopener" title="운영 시트 열기">' + ic('database') + '<span>운영 시트</span></a>' : '') +
      '<button type="button" data-act="reload" title="최신 숫자로 새로 고침">' + ic('refresh-cw') + '<span>새로 고침</span></button></span></div>' +
      '<div class="ad-dock-kinds">' + BULK_KINDS.map(function (k, i) { return '<button type="button" data-bulk="' + k[0] + '" title="' + esc(k[2]) + '"><b>' + (i + 1) + '</b>' + k[1] + '</button>'; }).join('') + '</div></div>';
    return heroHTML('위원 라운지 &nbsp;›&nbsp; 위원장', '위원장 대시보드', todayTxt + (a.isPayoutToday ? ' · 오늘 정산일' : ' · 다음 정산 ' + fmtKo(a.nextPayoutDay, true)) + (a.payoutDay && !a.isPayoutToday ? ' · 최근 정산표 ' + fmtMD(a.payoutDay, true) : ''), dock);
  }
  function adTabsBarHTML(a) {
    var tabs = [['insight', '분석 대시보드'], ['pay', '정산 · 실적'], ['roster', '위원 명단 (' + a.roster.length + ')'], ['notice', '공지 보내기'], ['settings', '설정']];
    return '<div class="ad-tabs">' + tabs.map(function (x) { return '<button type="button" class="' + (S.tab === x[0] ? 'on' : '') + '" data-tab="' + x[0] + '">' + x[1] + '</button>'; }).join('') + '<span class="sub">v' + esc(a.version) + '</span></div>';
  }
  function adTilesHTML(a) {
    var t = a.tiles, stt = t.status || {};
    /* 1.4.3 상단 타일: ① 정산(정산일이면 오늘 정산표, 아니면 다음 정산 미리 보기) ② 누적 추천 결제 ③ 최근 7일 ④ 위원 ⑤ 메일.
       1.4.10 오늘 지급예정을 모두 지급 완료하면 첫 칸은 다음 정산(모이는 금액)으로.
       1.4.11 사용자 2026.10.01 '글씨가 너무 길어져서 못생겨졌잖아. 정산표 보기 이건 늘리고 … 잘 요약해서 해 줘. 하단은 누적 추천 결제, 맨 하단은 지금까지 추천으로
       한 사람 금액, 우측에는 추천 아니고도 전체 아임웹 결제 금액(양성과정) 적어 주고 99,000원짜리도 포함해서 … 디자인이 밑으로 너무 길어졌어':
       칸마다 큰 숫자 + 짧은 한두 줄, 자세한 설명은 마우스를 올리면(title). 정산 칸 오른쪽 위에 [정산표 보기] 버튼, 누적 칸 아래에 추천 결제 | 전체 양성과정 결제 */
    var nx = t.next || null, payTile, tip, lines;
    var md = function (s) { var d = dateOf(s); return d ? (d.getMonth() + 1) + '/' + d.getDate() : String(s || ''); };
    var mdw = function (s) { var d = dateOf(s); return d ? md(s) + '(' + DAYS[d.getDay()] + ')' : String(s || ''); };
    var line = function (txt, cls) { return '<i' + (cls ? ' class="' + cls + '"' : '') + '>' + txt + '</i>'; };
    var tileHi = function (label, big, body, title) {
      return '<div class="ad-tile hi"' + (title ? ' title="' + esc(title) + '"' : '') + '><div class="ad-tile-head"><span>' + label + '</span><button type="button" class="ad-tile-go" data-tab="pay">' + ic('clipboard-list') + '정산표 보기</button></div><b>' + big + '</b>' + body + '</div>';
    };
    var totSum = a.isPayoutToday ? a.payouts.reduce(function (x, p) { return x + (Number(p.amount) || 0); }, 0) : 0, todayDone = a.isPayoutToday && !t.dueN;
    var paidSum = a.isPayoutToday ? a.payouts.reduce(function (x, p) { return x + (p.status === '지급완료' ? Number(p.amount) || 0 : 0); }, 0) : 0;
    if (a.isPayoutToday && !todayDone) {
      tip = '오늘 ' + fmtKo(a.today, true) + ' 정산 ' + a.payouts.length + '명 ' + won(totSum) + ' · 지급 완료 ' + t.paidN + '명 · 남은 ' + t.dueN + '명' + (t.holdN ? ' · 정산 정보 미등록(보류) ' + t.holdN + '명' : '') + (nx ? '\n다음 정산 ' + fmtKo(nx.day, true) + '까지 모이는 금액 ' + won(nx.amount) : '');
      lines = line(a.payouts.length + '명 · 지급 완료 ' + t.paidN + ' · 남은 ' + t.dueN + (t.holdN ? ' · 보류 ' + t.holdN : '')) + (nx ? line('다음 ' + md(nx.day) + ' 정산 모이는 중 ' + won(nx.amount)) : '');
      payTile = tileHi('오늘 정산 · ' + mdw(a.today), won(totSum), lines, tip);
    } else if (nx) {
      var nd = dateOf(nx.day), cutTxt = nd ? DAYS[(nd.getDay() + 6) % 7] + '요일 24시' : '전날 24시';
      tip = '다음 정산 ' + fmtKo(nx.day, true) + ' 지급 예정 ' + won(nx.amount) + ' · ' + cutTxt + '까지 결제된 추천 실적' + (nx.members ? '(' + nx.members + '명 · 추천 ' + num(nx.credits) + '건)' : '') +
        (nx.holdN ? '\n정산 정보 미등록 ' + nx.holdN + '명(' + won(nx.holdAmount) + ')은 등록하면 지급' : '') + (nx.overdueN ? '\n지난 정산 미지급 ' + nx.overdueN + '명 · ' + won(nx.overdueSum) : '') +
        (todayDone ? '\n오늘 ' + fmtKo(a.today, true) + ' 정산 ' + won(paidSum) + ' · ' + t.paidN + '명 지급 완료' + (t.holdN ? ' · 보류 ' + t.holdN + '명(' + won(totSum - paidSum) + ')은 다음 정산에 합쳐짐' : '') : '');
      lines = line(nx.members ? nx.members + '명 · 추천 ' + num(nx.credits) + '건' + (nx.holdN ? ' · 미등록 ' + nx.holdN + '명' : '') : '아직 없음 · ' + cutTxt + ' 마감') +
        (nx.overdueN ? line('지난 정산 미지급 ' + nx.overdueN + '명 · ' + won(nx.overdueSum), 'ad-tile-warn') : '') +
        (todayDone ? line(ic('check') + '오늘 ' + won(paidSum) + ' 지급 완료(' + t.paidN + '명)', 'ad-tile-ok') : '');   // 보류는 위 줄 '미등록'과 title 에
      payTile = tileHi('다음 정산 · ' + mdw(nx.day), won(nx.amount), lines, tip);
    } else payTile = tileHi('최근 정산', won(t.dueSum), line(t.dueN + '명 · 지급 완료 ' + t.paidN + ' · 보류 ' + t.holdN), '');
    /* 누적 추천 결제: 큰 숫자 건수, 아래 왼쪽 추천 결제 금액(실결제액) · 오른쪽 전체 양성과정 결제(추천 아닌 99,000원 결제 포함, 백엔드 1.4.11 결제 장부) */
    var sa = t.sales || null, refAmt = t.amountAll != null ? t.amountAll : null;
    var sumTip = '추천 결제: 위원 코드(쿠폰)로 들어온 양성과정 결제 ' + num(t.creditsAll) + '건' + (refAmt != null ? ' ' + won(refAmt) : '') + ' · 이번 달 ' + num(t.creditsMonth || 0) + '건' + (t.amountMonth != null ? ' ' + won(t.amountMonth) : '') + ' · 실적 있는 위원 ' + num(t.creditedN || 0) + '명' +
      (t.supportAll != null ? '\n활동지원금 누적 ' + won(t.supportAll) + (t.paidAll != null ? ' · 지급 완료 ' + won(t.paidAll) : '') : '') +
      (sa ? '\n전체 양성과정: 추천이 아닌 결제(99,000원)까지 아임웹 양성과정 결제 ' + num(sa.n) + '건' + (sa.from ? '(' + fmtKo(sa.from) + '부터)' : '') + ' · 이번 달 ' + num(sa.monthN) + '건 ' + won(sa.monthSum) + ' · 환불 ' + num(sa.refundN) + '건 제외' + (sa.ready ? '' : '\n지난 주문을 모으는 중이라 곧 채워집니다') : '');
    var allTxt = !sa ? '-' : sa.ready ? won(sa.sum) : '집계 중';
    var sumTile = '<div class="ad-tile" title="' + esc(sumTip) + '"><span>누적 추천 결제</span><b>' + num(t.creditsAll != null ? t.creditsAll : t.paid7) + '건</b>' +
      '<div class="ad-split"><div><small>추천 결제</small><strong>' + (refAmt != null ? won(refAmt) : '-') + '</strong></div><div><small>전체 양성과정</small><strong>' + allTxt + '</strong></div></div></div>';
    var p7 = t.paid7 || 0, pp7 = t.paidPrev7 || 0, d7 = p7 - pp7;
    var restN = (stt['휴면예정'] || 0) + (stt['휴면'] || 0), endN = stt['종료'] || 0;
    var memTip = ['활동', '휴면예정', '휴면', '종료'].map(function (x) { return (x === '휴면예정' ? '휴면 예정' : x) + ' ' + (stt[x] || 0) + '명'; }).join(' · ') + (t.loggedInN != null ? '\n라운지에 로그인한 적이 있는 위원 ' + num(t.loggedInN) + '명' : '');
    return '<div class="ad-tiles">' + payTile + sumTile +
      '<div class="ad-tile" title="' + esc('최근 7일(오늘 포함) 추천 결제 ' + p7 + '건 · 그 전 7일 ' + pp7 + '건 · 최근 7일 취소 · 환불 ' + (t.canc7 || 0) + '건') + '"><span>최근 7일 추천 결제</span><b>' + num(p7) + '건' + (d7 ? ' <small class="ad-tile-d ' + (d7 > 0 ? 'up' : 'down') + '">' + (d7 > 0 ? '▲' : '▼') + num(Math.abs(d7)) + '</small>' : '') + '</b>' + line('그 전 7일 ' + num(pp7) + '건 · 환불 ' + num(t.canc7) + '건') + '</div>' +
      '<div class="ad-tile" title="' + esc(memTip) + '"><span>위원</span><b>' + num(t.members) + '명</b>' + line('활동 ' + num(stt['활동'] || 0) + (restN ? ' · 휴면 ' + restN : '') + (endN && !restN ? ' · 종료 ' + endN : '') + (t.loggedInN != null ? ' · 로그인 ' + num(t.loggedInN) : '')) + '</div>' +
      mailTileHTML(a, t) + '</div>';
  }
  function renderAdmin() {
    var a = S.admin;
    hero.innerHTML = adHeroHTML(a);
    main.innerHTML = adTilesHTML(a) + adTabsBarHTML(a) +
      '<div id="adTab">' + adminTabHTML() + '</div>' +
      '<p class="lg-foot">계좌 · 주민등록번호는 위원장에게만 보이며 위원 화면에는 다른 위원의 정보가 나오지 않습니다. 이 창을 닫으면 자동으로 로그아웃됩니다. 새로 고침할 때는 마지막 화면을 먼저 보여 드리고 최신 숫자로 바꿉니다(계좌번호는 이 컴퓨터에 두지 않음).</p>';
    show('main');
    hero.onclick = onAdminHero;
    hero.onchange = function (e) { if (e.target && e.target.id === 'adBulkAud') { S.bulkN = e.target.value; store(KEY_BULK_N, S.bulkN, true); } };
    main.onclick = onAdminClick;
    main.onchange = onAdminChange;
    bindAdminForms();
  }
  /* 위쪽만 다시 그림(머리 · 타일 · 탭 줄): 입력 중인 탭은 그대로 두고 숫자만 바꿀 때 */
  function renderAdminTop() {
    var a = S.admin; hero.innerHTML = adHeroHTML(a);
    var tl = main.querySelector(':scope > .ad-tiles'), tb = main.querySelector(':scope > .ad-tabs');
    if (tl) tl.outerHTML = adTilesHTML(a); if (tb) tb.outerHTML = adTabsBarHTML(a);
  }
  function onAdminHero(e) {
    var b = e.target.closest('[data-act],[data-bulk]'); if (!b) return;
    if (b.hasAttribute('data-bulk')) { openBulk(b.getAttribute('data-bulk')); return; }
    if (b.getAttribute('data-act') === 'logout') { adminLogout(); return; }
    if (b.getAttribute('data-act') === 'reload') { b.disabled = true; b.classList.add('is-busy'); b.innerHTML = '<span class="lg-spin"></span> 불러오는 중'; loadAdmin(); }
  }
  /* ---------- 1.4.14 위원 일괄 메일(머리 줄 → 미리 보기 창) ----------
     사용자 2026.10.03 '활동이 적은 사람들 일괄로 독려하는 메일 … 하위 20명이라든지 1. 독려 2. 자기설득 및 자긍심 3. 전체적인 사용법 및 안내 … 내가 일괄로 하위 사람들에게'.
     대상은 분석 탭과 같은 활동 점수로 낮은 순(같으면 마지막 활동이 오래된 순 · 누적 추천 적은 순 · 누적 확산 적은 순 · 이름). 창에서 위원을 빼거나 넣고(위촉 3일 안의 새 위원은
     독려 · 자긍심에서 처음엔 빠져 있음), 눈 단추로 그 위원이 받을 메일을 보고, [나에게 테스트] → [N명에게 보내기]. 서버(admin.bulk)가 종료 · 수신 거부 · 최근 7일 같은 메일을
     다시 걸러 대기열로 보냄(10분마다 나눠서 · 하루 한도 안) */
  var BULK_KINDS = [['cheer', '독려', '부담 없이 바로 해 볼 수 있는 세 가지와 내 명함 · 바로 신청 링크'], ['pride', '자긍심', '왜 지금 AI 윤리인지, 위원 활동의 의미와 함께 만든 변화(자기설득 · 자긍심)'],
    ['guide', '사용 안내', '위원 라운지 · AIEP 과정 소개하는 법 · 전용관(영상관 · 이수 평가) · 이수증 활용 · 명함과 활동지원금']];
  var BULK_AUD = [['10', '하위 10명'], ['20', '하위 20명'], ['30', '하위 30명'], ['all', '전체 위원']], BULK_NEW_DAYS = 3, BK = null;
  function bulkTargets(n) {
    var a = S.admin, an = a.analytics, t0 = dateOf(a.today) || dateOf(new Date()), list;
    var days = function (s) { var d = dateOf(s); return d ? Math.round((t0 - d) / 86400000) : 999; };
    if (an && an.rank && !an.error) list = an.rank.filter(function (r) { return r.status !== '종료'; }).map(function (r) { return { code: r.code, name: r.name, badge: r.badge, status: r.status, score: Number(r.score) || 0, silentDays: Number(r.silentDays), credits: Number(r.credits) || 0, reachAll: Number(r.reachAll) || 0, sinceDays: Number(r.sinceDays) }; });
    else list = (a.roster || []).filter(function (r) { return r.status !== '종료'; }).map(function (r) { return { code: r.code, name: r.name, badge: r.badge, status: r.status, score: 0, silentDays: days(r.lastSignal), credits: Number(r.credits) || 0, reachAll: 0, sinceDays: days(r.since) }; });
    list.forEach(function (r) { if (!isFinite(r.silentDays)) r.silentDays = 999; if (!isFinite(r.sinceDays)) r.sinceDays = 999; });
    list.sort(function (x, y) { return (x.score - y.score) || (y.silentDays - x.silentDays) || (x.credits - y.credits) || (x.reachAll - y.reachAll) || String(x.name).localeCompare(String(y.name), 'ko'); });
    return n === 'all' ? list : list.slice(0, +n || 20);
  }
  function openBulk(kind) {
    var k = BULK_KINDS.filter(function (x) { return x[0] === kind; })[0]; if (!k || !S.admin) return;
    var n = String(S.bulkN || '20'), list = bulkTargets(n);
    if (!list.length) { toast('보낼 위원이 없습니다', 'warn'); return; }
    BK = { kind: kind, label: k[1], n: n, list: list, sel: {}, why: {}, sample: '', seq: 0 };
    list.forEach(function (r) { BK.sel[r.code] = kind === 'guide' || r.sinceDays > BULK_NEW_DAYS; });
    var md = modal(k[1] + ' 메일 · ' + (n === 'all' ? '전체 위원 ' + list.length + '명' : '하위 ' + list.length + '명'), '활동 점수가 낮은 순 · 최근 7일 안에 같은 메일을 받은 위원은 자동으로 빠집니다',
      '<div class="bk-wrap"><div class="bk-col"><div class="bk-listhead"><b id="bkCount"></b><button type="button" class="lg-link" data-bk="all">모두 선택</button><button type="button" class="lg-link" data-bk="none">모두 해제</button></div><ul class="bk-list" id="bkList">' + bulkListHTML() + '</ul></div>' +
      '<div class="bk-col bk-col--mail" id="bkMail">' + bulkLoadingHTML() + '</div></div>',
      '<span class="bk-info" id="bkInfo">' + esc(k[2]) + '</span><button type="button" class="btn btn-ghost btn-sm" data-bk="test">나에게 테스트</button><button type="button" class="btn btn-primary btn-sm" data-bk="send" id="bkSend">보내기</button>');
    var dlg = md.querySelector('.lg-dialog'); if (dlg) dlg.classList.add('lg-dialog--wide');
    md.onclick = onBulkClick; md.onchange = onBulkChange;
    bulkSync(); bulkPreview('');
  }
  function bulkLoadingHTML() { return '<div class="bk-loading"><span class="lg-spin"></span> 위원이 받을 메일을 만드는 중…</div>'; }
  function bulkListHTML() {
    return BK.list.map(function (r) {
      var why = BK.why[r.code], on = !why && BK.sel[r.code], st = r.status === '활동' ? '' : ' · ' + (r.status === '휴면예정' ? '휴면 예정' : r.status);
      var tag = why ? '<em class="bk-tag bk-tag--x">' + esc(why) + '</em>' : r.sinceDays <= BULK_NEW_DAYS ? '<em class="bk-tag">위촉 ' + Math.max(0, r.sinceDays) + '일째</em>' : '';
      return '<li class="bk-row' + (why ? ' is-off' : '') + (BK.sample === r.code ? ' is-sample' : '') + '"><label><input type="checkbox" data-code="' + esc(r.code) + '"' + (on ? ' checked' : '') + (why ? ' disabled' : '') + '>' +
        '<span class="bk-who"><b>' + esc(r.name) + '</b><small>' + esc(r.code) + (r.badge ? ' · ' + esc(TIER_WORD[r.badge] || r.badge) : '') + '</small></span></label>' +
        '<button type="button" class="bk-eye" data-sample="' + esc(r.code) + '" title="이 위원이 받을 메일 보기" aria-label="' + esc(r.name) + ' 위원이 받을 메일 보기">' + ic('eye') + '</button>' +
        '<span class="bk-meta">활동 점수 ' + r.score + ' · 마지막 활동 ' + agoTxt(r.silentDays) + st + (tag ? ' ' + tag : '') + '</span></li>';
    }).join('');
  }
  function bulkPicked() { return BK.list.filter(function (r) { return BK.sel[r.code] && !BK.why[r.code]; }).map(function (r) { return r.code; }); }
  function bulkSync() {
    var c = bulkPicked().length, b = $('bkSend'), h = $('bkCount');
    if (h) h.textContent = '선택 ' + c + '명 / ' + BK.list.length + '명';
    if (b && !b.classList.contains('is-busy')) { b.textContent = c ? c + '명에게 보내기' : '보낼 위원을 고르세요'; b.disabled = !c; }
  }
  function bulkPreview(sample) {
    if (!BK) return; var my = ++BK.seq, box = $('bkMail'); if (box) box.innerHTML = bulkLoadingHTML();
    call('admin.bulk', { step: 'preview', kind: BK.kind, codes: BK.list.map(function (r) { return r.code; }), sample: sample || '' }).then(function (j) {
      if (!BK || my !== BK.seq) return;
      BK.why = {}; (j.list || []).forEach(function (x) { if (!x.ok) BK.why[x.code] = x.why; });
      BK.sample = j.sample || ''; var ul = $('bkList'); if (ul) ul.innerHTML = bulkListHTML();
      var mb = $('bkMail'); if (mb) mb.innerHTML = '<div class="ad-mailmeta"><div><span>미리 보기</span><b>' + esc(j.sampleName || '') + ' 위원이 받을 메일</b></div><div><span>제목</span><b>' + esc(j.subject) + '</b></div></div>' +
        '<iframe class="ad-mailframe bk-frame" sandbox="" title="' + esc(BK.label) + ' 메일 미리 보기" srcdoc="' + esc('<!doctype html><meta charset="utf-8"><body style="margin:0">' + j.html + '</body>') + '"></iframe>';
      var inf = $('bkInfo'); if (inf) inf.textContent = (j.quota >= 0 ? '지메일 잔여 ' + num(j.quota) + '통 · ' : '') + '대기 ' + num(j.wait) + '통' + (j.paused ? ' · 지금 발송 멈춤' : '') + ' · ' + (j.everyMin || 10) + '분마다 ' + (j.perRun || 20) + '통씩 나감';
      bulkSync();
    }, function (er) { if (!BK || my !== BK.seq) return; var mb = $('bkMail'); if (mb) mb.innerHTML = '<p class="lg-err is-on">' + esc(er.message) + '</p>'; });
  }
  function onBulkClick(e) {
    var md = $('lgModal');
    if (e.target === md || e.target.closest('[data-act="close"]')) { closeModal(); BK = null; return; }
    if (!BK) return;
    var sb = e.target.closest('[data-sample]'); if (sb) { bulkPreview(sb.getAttribute('data-sample')); return; }
    var b = e.target.closest('[data-bk]'); if (!b) return;
    var act = b.getAttribute('data-bk'), foot = md.querySelector('.lg-dialog-foot');
    if (act === 'all' || act === 'none') { BK.list.forEach(function (r) { if (!BK.why[r.code]) BK.sel[r.code] = act === 'all'; }); $('bkList').innerHTML = bulkListHTML(); bulkSync(); return; }
    if (act === 'test') {
      busy(b, true);
      call('admin.bulk', { step: 'test', kind: BK.kind, codes: BK.sample ? [BK.sample] : [], sample: BK.sample || '' }).then(function (j) { busy(b, false); toast((j.sampleName ? j.sampleName + ' 위원 기준 ' : '') + BK.label + ' 메일을 위원장 메일로 보냈습니다(' + (j.to || []).join(', ') + ')', 'ok'); }, function (er) { busy(b, false); toast(er.message, 'danger'); });
      return;
    }
    if (act === 'send') {
      var c = bulkPicked().length; if (!c) return;
      BK.foot = foot.innerHTML;
      foot.innerHTML = '<span class="bk-info bk-ask">체크한 ' + c + '명에게 ' + esc(BK.label) + ' 메일을 보낼까요? 대기열로 들어가 10분마다 나눠서 나갑니다.</span><button type="button" class="btn btn-ghost btn-sm" data-bk="cancel">취소</button><button type="button" class="btn btn-primary btn-sm" data-bk="go">' + c + '명에게 보내기</button>';
      return;
    }
    if (act === 'cancel') { foot.innerHTML = BK.foot || ''; bulkSync(); return; }
    if (act === 'go') {
      var codes = bulkPicked(), label = BK.label; busy(b, true);
      call('admin.bulk', { step: 'send', kind: BK.kind, codes: codes }).then(function (j) {
        closeModal(); BK = null;
        toast((j.result || label + ' 메일을 대기열에 올렸습니다') + (j.skipped && j.skipped.length ? ' 제외 ' + j.skipped.length + '명(최근에 받았거나 받을 수 없는 위원).' : ''), 'ok');
        loadAdmin(true);
      }, function (er) { busy(b, false); toast(er.message, 'danger'); });
    }
  }
  function onBulkChange(e) { var c = e.target.closest('input[data-code]'); if (!c || !BK) return; BK.sel[c.getAttribute('data-code')] = c.checked; bulkSync(); }
  function adminTabHTML() {
    var a = S.admin;
    if (S.tab === 'insight') return insightTabHTML(a);
    if (S.tab === 'pay') return payTabHTML(a);
    if (S.tab === 'roster') return rosterTabHTML(a);
    if (S.tab === 'notice') return noticeTabHTML(a);
    return settingsTabHTML(a);
  }
  /* 1.4.6 정산표 표만 따로 그림: [지급 완료] 체크 뒤 그 표와 위쪽 숫자만 바꿈(화면 전체를 다시 불러오지 않아 연달아 체크해도 표가 흔들리지 않음) */
  function payTableHTML(a) {
    var rows = a.payouts.map(function (p) {
      var paid = p.status === '지급완료', hold = p.status === '보류';
      var acct = hold ? '<span class="lg-chip lg-chip--wait">정산 정보 없음</span>' : (p.account ? '<span class="acct">' + esc(p.account) + '</span> <button type="button" class="btn btn-ghost btn-xs" data-copy="' + esc(p.account) + '">복사</button>' : p.acctWait ? '<span class="lg-muted">계좌 불러오는 중…</span>' : '-');
      var stc = hold ? '<span class="lg-chip lg-chip--x">보류 · 다음 주 이월</span>' : S.paying[p.id] ? '<span class="ad-paying"><span class="lg-spin"></span> 기록 중</span>' : '<label class="cb"><input type="checkbox" data-paid="' + esc(p.id) + '"' + (paid ? ' checked' : '') + '>지급 완료' + (paid ? ' <span class="lg-muted" style="font-weight:500">' + esc(String(p.paidAt).slice(5)) + '</span>' : '') + '</label>';
      return '<tr class="' + (paid ? 'done' : '') + '"><td><b>' + esc(p.name) + '</b> · ' + esc(p.code) + '</td><td>' + badgeChip(p.tier) + '</td><td class="num">' + p.count + '</td><td class="num">' + won(p.amount) + '</td><td>' + acct + '</td><td>' + stc + '</td><td class="lg-muted" style="font-size:12.5px">' + esc(p.memo || '') + '</td></tr>';
    }).join('');
    var sum = a.payouts.reduce(function (s, p) { s.n += p.count; s.amt += p.amount; if (p.status === '지급완료') { s.paidN++; s.paid += p.amount; } else if (p.status === '보류') { s.holdN++; s.hold += p.amount; } else { s.dueN++; s.due += p.amount; } return s; }, { n: 0, amt: 0, paidN: 0, paid: 0, holdN: 0, hold: 0, dueN: 0, due: 0 });
    var dueLeft = a.payouts.filter(function (p) { return p.status === '지급예정' && !S.paying[p.id]; }).length;
    var bar = sum.dueN ? '<div class="ad-paybar"><span>남은 지급 ' + sum.dueN + '명 · ' + won(sum.due) + '</span>' + (dueLeft ? '<button type="button" class="btn btn-primary btn-sm" data-act="payall">' + ic('check') + '지급예정 ' + dueLeft + '명 모두 지급 완료</button>' : '') + '</div>' : '';
    return '<div id="adPayTbl">' + bar + '<div class="ad-scroll">' + (a.payouts.length ? '<table class="lg-tbl"><thead><tr><th>위원</th><th>등급</th><th class="num">확정 건수</th><th class="num">지원금</th><th>계좌</th><th>상태</th><th>메모</th></tr></thead><tbody>' + rows + '</tbody><tfoot><tr><td colspan="2">합계</td><td class="num">' + sum.n + '</td><td class="num">' + won(sum.amt) + '</td><td colspan="3" style="padding-left:16px;font-weight:600">지급 완료 ' + sum.paidN + '명 ' + won(sum.paid) + ' · 남은 ' + sum.dueN + '명 ' + won(sum.due) + ' · 보류 ' + sum.holdN + '명 ' + won(sum.hold) + '</td></tr></tfoot></table>' : '<p class="lg-empty">아직 정산표가 없습니다. 목요일 00:05에 자동으로 만들어지고, 아래 [정산표 지금 만들기]로 미리 만들 수도 있습니다.</p>') + '</div></div>';
  }
  function payTabHTML(a) {
    var weekly = a.roster.slice().sort(function (x, y) { return (y.weeks[3] - x.weeks[3]) || (y.weeks[2] - x.weeks[2]) || (y.credits - x.credits); });
    var top = weekly.filter(function (r) { return r.weeks.some(function (w) { return w > 0; }); }).slice(0, 15);
    var rest = weekly.length - top.length, restSum = weekly.slice(top.length).reduce(function (s, r) { s.w1 += r.weeks[3]; s.w2 += r.weeks[2]; s.c += r.credits; return s; }, { w1: 0, w2: 0, c: 0 });
    var mx = Math.max(1, Math.max.apply(null, weekly.map(function (r) { return Math.max.apply(null, r.weeks); })));
    var wrows = top.map(function (r) { return '<tr class="ad-row" data-code="' + esc(r.code) + '"><td>' + esc(r.name) + ' · ' + esc(r.code) + '</td><td class="num">' + r.weeks[3] + '</td><td class="num">' + r.weeks[2] + '</td><td style="padding-left:16px"><span class="bars">' + r.weeks.map(function (w, i) { return '<i class="' + (i === 3 ? 'now' : '') + '" style="height:' + Math.max(3, Math.round(w / mx * 22)) + 'px"></i>'; }).join('') + '</span></td><td class="num">' + r.credits + '</td></tr>'; }).join('') + (rest > 0 ? '<tr><td class="lg-muted">나머지 ' + rest + '명</td><td class="num">' + restSum.w1 + '</td><td class="num">' + restSum.w2 + '</td><td style="padding-left:16px"></td><td class="num">' + restSum.c + '</td></tr>' : '');
    var cum = a.roster.slice().sort(function (x, y) { return y.credits - x.credits; }).filter(function (r) { return r.credits > 0 || r.paid > 0 || r.unpaid !== 0; }).slice(0, 15);
    var crows = cum.map(function (r) { return '<tr class="ad-row" data-code="' + esc(r.code) + '"><td>' + esc(r.name) + ' · ' + esc(r.code) + '</td><td class="num">' + r.credits + '</td><td class="num">' + won(r.paid) + '</td><td class="num">' + won(r.unpaid) + '</td><td class="num">' + r.canceled + '</td></tr>'; }).join('');
    var changes = a.changes.map(function (c) { return '<li>' + esc(c) + '<span>이번 주</span></li>'; }).join('') + a.newbies.map(function (c) { return '<li>신규 위촉 ' + esc(c) + '<span>이번 주</span></li>'; }).join('');
    var links = a.links.map(function (l) { return '<li><a href="' + esc(l.url) + '" target="_blank" rel="noopener">' + esc(l.code) + ' · ' + esc(short(l.url).slice(0, 48)) + '</a><span>' + fmtMD(l.at) + '</span></li>'; }).join('');
    var coupons = a.endedCoupons.length ? '<div class="lg-card lg-card--warn"><h2>' + ic('x') + '쿠폰 삭제 대기 <span class="sub">위촉이 종료된 위원의 아임웹 쿠폰은 직접 지워야 합니다</span></h2><p><b>' + a.endedCoupons.map(esc).join(' · ') + '</b></p><p style="margin-top:8px"><a class="btn btn-ghost btn-sm" href="' + esc(a.couponAdminUrl || '#') + '" target="_blank" rel="noopener">아임웹 쿠폰 관리 열기</a></p></div>' : '';
    return '<div class="lg-card"><h2>' + ic('credit-card') + (a.isPayoutToday ? '오늘 정산표' : '최근 정산표') + (a.payoutDay ? ' · ' + fmtMD(a.payoutDay, true) : '') + '<span class="sub">송금 뒤 [지급 완료]를 체크하면 정산관리 · 활동내역(정산상태)에 지급완료로 기록되고 위원에게 안내 메일이 나갑니다. 잘못 체크했으면 풀면 되고, 아직 안 나간 안내 메일도 함께 취소됩니다</span></h2>' +
      payTableHTML(a) +
      '<div class="ad-actions"><button type="button" class="btn btn-ghost" data-act="settle">정산표 지금 만들기</button><button type="button" class="btn btn-ghost" data-act="poll">아임웹 주문 지금 확인</button><button type="button" class="btn btn-ghost" data-act="mailq">대기 메일 지금 보내기</button><button type="button" class="btn btn-ghost" data-act="sync">파트너 시트에서 위원 가져오기</button></div></div>' +
      coupons + taxCardHTML() +
      '<div class="ad-two"><div class="lg-card"><h2>' + ic('bar-chart-3') + '주간 실적 <span class="sub">확정 기준 · 이번 주 · 지난주 · 4주 흐름 · 누적</span></h2><div class="ad-scroll"><table class="lg-tbl"><thead><tr><th>위원</th><th class="num">이번 주</th><th class="num">지난주</th><th style="padding-left:16px">4주</th><th class="num">누적</th></tr></thead><tbody>' + (wrows || '<tr><td colspan="5" class="lg-empty">최근 4주 확정 실적이 없습니다</td></tr>') + '</tbody></table></div></div>' +
      '<div class="lg-card"><h2>' + ic('users') + '위원 상태 <span class="sub">이번 주 변경</span></h2><div class="st"><div><span>활동 중</span><b>' + (a.tiles.status['활동'] || 0) + '</b></div><div><span>휴면 예정</span><b>' + (a.tiles.status['휴면예정'] || 0) + '</b></div><div><span>휴면</span><b>' + (a.tiles.status['휴면'] || 0) + '</b></div><div><span>종료</span><b>' + (a.tiles.status['종료'] || 0) + '</b></div></div><ul class="lg-list">' + (changes || '<li class="lg-muted">이번 주 상태 변경 없음</li>') + '</ul></div></div>' +
      '<div class="ad-two"><div class="lg-card"><h2>' + ic('trending-up') + '누적 <span class="sub">전체 크레딧 ' + a.totals.credits + ' · 지급 ' + won(a.totals.paid) + ' · 미지급 ' + won(a.totals.unpaid) + '</span></h2><div class="ad-scroll"><table class="lg-tbl"><thead><tr><th>위원</th><th class="num">누적 크레딧</th><th class="num">지급 완료</th><th class="num">미지급</th><th class="num">취소</th></tr></thead><tbody>' + (crows || '<tr><td colspan="5" class="lg-empty">아직 실적이 없습니다</td></tr>') + '</tbody></table></div></div>' +
      '<div class="lg-card"><h2>' + ic('external-link') + '활동 링크 · 자동 작업</h2><ul class="lg-list">' + (links || '<li class="lg-muted">등록된 활동 링크 없음</li>') + '</ul><p style="margin-top:12px;font-size:12.5px;line-height:1.8">자동: 5분마다 아임웹 주문 확인(결제 즉시 확정 · 결제마다 위원장 알림) · 매시간 새 위원 가져오기 · 매일 03:00 게이지 · 상태 계산(리마인드 · 휴면 예정 · 휴면 · 종료 메일) · 추천 결제 10일 재대조 · 목요일 00:05 정산표(수요일 24시까지 결제분) · 08:00 위원장 요약 메일 · 대기열 메일 하루 ' + a.settings.MAIL_DAILY_LIMIT + '통 · 매월 1일 임팩트 리포트</p></div></div>';
  }
  /* 세금 신고용 목록(1.4.2, 2026.09.30 사용자 '주민등록번호는 왜 수집 안 돼? 시트에 수집되어야 원천징수 3.3% 세금 신고 가능한 거 아니야?'):
     주민등록번호는 법에 따라 시트(활동_정산정보)에 암호화되어 있어 시트에서는 읽히지 않음 → 운영자 화면에서 지급 월을 골라 불러오면 서버가 풀어서 위원별로 합쳐 줌.
     화면에는 뒷자리를 가리고, [CSV 내려받기] 파일에만 전체 번호. 위원 지급액은 그대로 두고 세금은 위원회가 부담하므로 신고 지급액(세전)은 서버가 거꾸로 계산 */
  function taxMonthNow() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2); }
  function rrnFmt(v) { v = String(v || '').replace(/\D/g, ''); return v.length === 13 ? v.slice(0, 6) + '-' + v.slice(6) : v; }
  function rrnMask(v) { v = String(v || '').replace(/\D/g, ''); return v.length === 13 ? v.slice(0, 6) + '-' + v.charAt(6) + '******' : ''; }
  function taxCardHTML() {
    var t = S.tax; if (!t.month) t.month = taxMonthNow();
    return '<div class="lg-card" id="adTax"><h2>' + ic('file-check') + '세금 신고용 목록 <span class="sub">원천징수 3.3% · 지급 완료 기준 · 위원별 월 합계</span></h2>' +
      '<div class="ad-taxbar"><label for="adTaxMonth">지급 월</label><input type="month" class="lg-input" id="adTaxMonth" value="' + esc(t.month) + '" max="' + esc(taxMonthNow()) + '">' +
      '<button type="button" class="btn btn-ghost btn-sm" data-act="taxload">불러오기</button>' + (t.data && t.data.rows.length ? '<button type="button" class="btn btn-primary btn-sm" data-act="taxcsv">CSV 내려받기</button>' : '') + '</div>' +
      taxBodyHTML() + '</div>';
  }
  function taxBodyHTML() {
    var t = S.tax.data;
    if (!t) return '<p class="ad-note">월을 고르고 [불러오기]를 누르면 그 달에 [지급 완료]로 체크한 활동지원금이 위원별로 합쳐져 나옵니다. 주민등록번호는 시트에 암호화되어 있어 시트에서는 읽히지 않고, 여기서 불러올 때만 풀립니다.</p>';
    var mo = t.month.split('-'), moTxt = mo[0] + '년 ' + Number(mo[1]) + '월';
    if (!t.rows.length) return '<p class="lg-empty">' + moTxt + '에 지급 완료한 활동지원금이 없습니다. 정산표에서 [지급 완료]를 체크한 뒤 다시 불러오세요.</p>';
    var sum = { n: 0, net: 0, gross: 0, it: 0, lt: 0 };
    var rows = t.rows.map(function (r) {
      sum.n += r.count; sum.net += r.net; sum.gross += r.gross; sum.it += r.incomeTax; sum.lt += r.localTax;
      return '<tr><td><b>' + esc(r.name) + '</b> · ' + esc(r.code) + '</td><td>' + (r.rrn ? '<span class="acct">' + esc(rrnMask(r.rrn)) + '</span>' : '<span class="lg-chip lg-chip--wait">정산 정보 없음</span>') + '</td><td class="num">' + r.count + '</td><td class="num">' + won(r.net) + '</td><td class="num"><b>' + won(r.gross) + '</b></td><td class="num">' + won(r.incomeTax) + '</td><td class="num">' + won(r.localTax) + '</td><td class="lg-muted" style="font-size:12.5px">' + esc(String(r.dates || '').split(' ').map(function (x) { return x.slice(5).replace('-', '.'); }).join(' · ')) + '</td></tr>';
    }).join('');
    return '<div class="ad-scroll"><table class="lg-tbl"><thead><tr><th>위원</th><th>주민등록번호</th><th class="num">건수</th><th class="num">위원 수령액</th><th class="num">신고 지급액(세전)</th><th class="num">소득세 3%</th><th class="num">지방소득세 0.3%</th><th>지급일</th></tr></thead><tbody>' + rows + '</tbody>' +
      '<tfoot><tr><td colspan="2">' + moTxt + ' 합계 · ' + t.rows.length + '명</td><td class="num">' + sum.n + '</td><td class="num">' + won(sum.net) + '</td><td class="num">' + won(sum.gross) + '</td><td class="num">' + won(sum.it) + '</td><td class="num">' + won(sum.lt) + '</td><td style="padding-left:16px;font-weight:600">세액 합계 ' + won(sum.it + sum.lt) + '</td></tr></tfoot></table></div>' +
      '<p class="ad-note">위원 수령액은 그대로 두고 세금은 위원회가 부담하는 방식이라, 신고 지급액(세전)은 수령액에서 거꾸로 계산한 금액입니다(소득세 · 지방소득세는 10원 미만 절사). 화면에는 주민등록번호 뒷자리를 가렸고, 전체 번호는 [CSV 내려받기] 파일에만 들어 있습니다. 신고를 마치면 내려받은 파일은 지워 주세요. 신고 · 납부 방식은 세무 담당자와 한 번 확인하세요.</p>';
  }
  function loadTax(b) {
    var inp = $('adTaxMonth'), mo = inp ? String(inp.value || '').trim() : S.tax.month;
    if (!/^\d{4}-\d{2}$/.test(mo)) { toast('지급 월을 2026-10 처럼 골라 주세요', 'danger'); return; }
    S.tax.month = mo; busy(b, true);
    call('admin.taxList', { month: mo }).then(function (j) {
      S.tax.data = { month: j.month, rate: j.rate, rows: j.rows || [] };
      var box = $('adTax'); if (box) box.outerHTML = taxCardHTML();
      toast(j.rows && j.rows.length ? j.month + ' · ' + j.rows.length + '명 불러왔습니다' : j.month + ' 지급 완료 내역이 없습니다', j.rows && j.rows.length ? 'ok' : undefined);
    }, function (er) { busy(b, false); toast(er.message, 'danger'); });
  }
  function taxCSV() {
    var t = S.tax.data; if (!t || !t.rows.length) return;
    var q = function (v) { v = String(v == null ? '' : v); return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    var head = ['지급월', '위원코드', '성명', '주민등록번호', '지급건수', '위원수령액', '신고지급액(세전)', '세율', '소득세', '지방소득세', '세액합계', '지급일'];
    var lines = [head.join(',')].concat(t.rows.map(function (r) { return [t.month, r.code, r.name, rrnFmt(r.rrn), r.count, r.net, r.gross, (Math.round(t.rate * 1000) / 10) + '%', r.incomeTax, r.localTax, r.incomeTax + r.localTax, String(r.dates || '').replace(/ /g, ' · ')].map(q).join(','); }));
    var blob = new Blob(['﻿' + lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'), url = URL.createObjectURL(blob); a.href = url; a.download = '원천징수_목록_' + t.month + '.csv'; a.style.display = 'none';
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(url); if (a.parentNode) a.parentNode.removeChild(a); }, 1500);
    toast('원천징수_목록_' + t.month + '.csv 를 내려받았습니다', 'ok');
  }
  function rosterTabHTML(a) {
    var q = S.roster.q.toLowerCase().replace(/\s+/g, ''), stf = S.roster.st;
    var list = a.roster.filter(function (r) { return (!stf || r.status === stf) && (!q || (r.name + r.code + r.email).toLowerCase().replace(/\s+/g, '').indexOf(q) >= 0); });
    var counts = { '': a.roster.length }; a.roster.forEach(function (r) { counts[r.status] = (counts[r.status] || 0) + 1; });
    var chips = [['', '전체'], ['활동', '활동'], ['휴면예정', '휴면 예정'], ['휴면', '휴면'], ['종료', '종료']].map(function (c) { return '<button type="button" class="lg-chip ' + (stf === c[0] ? 'lg-chip--blue' : 'lg-chip--x') + '" data-st="' + c[0] + '">' + c[1] + ' ' + (counts[c[0]] || 0) + '</button>'; }).join('');
    var rows = list.map(function (r) {
      var last = r.lastSignal ? fmtMD(r.lastSignal) + ' ' + esc(r.lastKind) : '-';
      return '<tr class="ad-row' + (r.status === '종료' ? ' done' : '') + '" data-code="' + esc(r.code) + '"><td><b>' + esc(r.name) + '</b> · ' + esc(r.code) + '</td><td>' + badgeChip(r.badge) + '</td><td>' + stChip(r) + '</td><td>' + fmtDot(r.since) + '</td><td>' + last + '</td><td class="num">' + (r.status === '활동' ? r.gauge + '%' : '-') + '</td><td class="num">' + r.credits + '</td><td>' + (r.payinfo ? '<span class="lg-chip lg-chip--ok">등록</span>' : (r.credits || r.pending ? '<span class="lg-chip lg-chip--wait">미등록</span>' : '-')) + '</td><td class="lg-muted" style="font-size:12.5px">' + (r.firstLogin ? '로그인 완료' : '첫 로그인 전') + '</td></tr>';
    }).join('');
    return '<div class="lg-card"><h2>' + ic('users-round') + '위원 명단 <span class="sub">행을 누르면 상세와 조치(크레딧 조정 · 휴면 · 복귀 · 종료 · 메모 · 비밀번호 초기화)</span></h2>' +
      '<div class="ad-filter"><input class="lg-input" id="adQ" placeholder="검색: 성명 · 코드 · 이메일" value="' + esc(S.roster.q) + '">' + chips + '</div>' +
      '<div class="ad-scroll"><table class="lg-tbl"><thead><tr><th>위원</th><th>등급</th><th>상태</th><th>위촉일</th><th>마지막 활동</th><th class="num">게이지</th><th class="num">누적</th><th>정산 정보</th><th>라운지</th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="lg-empty">일치하는 위원이 없습니다</td></tr>') + '</tbody></table></div></div>';
  }
  function noticeTabHTML(a) {
    var list = a.notices.map(function (n) { return '<li>' + fmtMD(n.at) + ' ' + esc(n.title) + ' · ' + esc(n.audience) + '<span>' + (n.mail === 'Y' ? '메일 ' + n.sent + '통' : '라운지만') + ' <button type="button" class="lg-link" data-hide="' + esc(n.id) + '">내리기</button></span></li>'; }).join('');
    return '<div class="ad-two"><div class="lg-card"><h2>' + ic('megaphone') + '공지 보내기 <span class="sub">라운지 공지 칸에 즉시 + 메일은 대기열로(하루 ' + a.settings.MAIL_DAILY_LIMIT + '통씩)</span></h2>' +
      '<form id="adNotice" novalidate><div class="lg-field"><label for="nTitle">제목</label><input class="lg-input" id="nTitle" maxlength="120"></div><div class="lg-field"><label for="nBody">본문</label><textarea class="lg-input ad-textarea" id="nBody" maxlength="4000"></textarea></div><div class="lg-form-grid" style="margin-top:0"><div class="lg-field"><label for="nLink">링크 (선택)</label><input class="lg-input" id="nLink" placeholder="https://" maxlength="300"></div><div class="lg-field"><label for="nAud">대상</label><select class="lg-input" id="nAud"><option value="전체">전체 위원 (종료 제외)</option><option value="활동">활동 중 위원</option><option value="선임이상">선임위원 이상</option><option value="개별">개별 (코드 입력)</option></select></div></div><div class="lg-field" id="nCodesBox" hidden><label for="nCodes">위원 코드 (쉼표로 구분)</label><input class="lg-input" id="nCodes" placeholder="PKH3185, LSM0738"></div>' +
      '<label class="lg-toggle" style="margin:8px 0 12px"><input type="checkbox" id="nMail" checked> 메일로도 보내기 (레터 수신 거부 위원 제외)</label><p class="lg-err" id="nErr"></p><div class="lg-btnrow"><button type="submit" class="btn btn-primary btn-sm" style="flex:0 1 auto">보내기</button></div></form></div>' +
      '<div class="lg-card"><h2>' + ic('clipboard-list') + '보낸 공지</h2><ul class="lg-list">' + (list || '<li class="lg-muted">아직 없음</li>') + '</ul></div></div>';
  }
  function settingsTabHTML(a) {
    var s = a.settings, desc = CFG.settingDesc || {};
    var keys = Object.keys(s);
    var inputs = keys.map(function (k) { return '<label>' + esc(k) + '<span>' + esc(desc[k] || '') + '</span><input class="lg-input" name="' + esc(k) + '" value="' + esc(s[k]) + '" inputmode="decimal"></label>'; }).join('');
    return '<div class="lg-card"><h2>' + ic('database') + '설정 <span class="sub">운영 시트 \'설정\' 탭과 같은 값 · 바꾸면 다음 자동 작업부터 적용</span></h2><form id="adSettings" novalidate><div class="ad-set">' + inputs + '</div><p class="lg-err" id="sErr" style="margin-top:12px"></p><div class="lg-btnrow" style="margin-top:14px"><button type="submit" class="btn btn-primary btn-sm" style="flex:0 1 auto">저장</button></div></form>' +
      '<p style="margin-top:16px;font-size:12.5px;line-height:1.8">PAYOUT_WEEKDAY 는 0 일 · 1 월 · 2 화 · 3 수 · 4 목 · 5 금 · 6 토. 정산 요일을 바꾸면 앱스 스크립트 편집기에서 setup 을 한 번 더 실행해 트리거를 다시 만들어야 합니다. 위원장 비밀번호는 파트너 관리 시트 메뉴 [위원 활동 시스템] → [위원장 비밀번호 바꾸기…]에서 바꿉니다(바꾸면 열려 있던 위원장 화면은 다시 로그인).</p></div>';
  }
  /* ---------- 운영자 · 분석 대시보드(2026.09.29 밤, 백엔드 1.3.0 analytics) ----------
     사용자: 전체 위원 관리 · 정산 연동 · 누가 활동을 많이/안 하는지 시각화 · 수치화된 데이터 · 통계 · 순위 · 더 모을 데이터.
     서버가 admin.dashboard 에 함께 보내는 analytics(활동 점수 · 순위 · KPI · 12주 · 6개월 · 퍼널 · 분포 · 채널 · 히트맵 · 통계 · 코호트 · 점검 · 메일 · 타임라인)를 그림.
     차트는 외부 라이브러리 없이 인라인 SVG */
  var KIND_KO = { reach: '명함 · 링크 열람', '로그인': '로그인', '라운지': '라운지 방문', link: '활동 링크', '링크등록': '링크 등록', kit: '도구 사용', save: '명함 저장', share: '명함 공유', payinfo: '정산 정보 등록', cert: '증명서 요청', '결제': '결제', '확정': '확정', '리치': '열람 신호', '위촉': '위촉', '활동확인': '활동 확인', '복귀링크': '복귀', '운영자복귀': '위원장 복귀' };
  var KIT_KO = { 'copy:card': '위원 명함 링크 복사', 'copy:go': '바로 결제 링크 복사', 'copy:intro': '소개 페이지 링크 복사', 'copy:experts': 'AIEP 안내 링크 복사', 'open:qr': '명함 · QR 열기', manual: '매뉴얼 내려받기' };
  var CHANNEL_KO = { card: ['위원 명함', '#1F5FE0'], go: ['바로 결제 링크', '#0B8F84'], intro: ['소개 페이지', '#7C3AED'], experts: ['AIEP 안내 페이지', '#F0A24A'], other: ['기타', '#A0AEC0'] };
  var SCORE_BANDS = [[80, '매우 활발', '#0B8F84'], [50, '활발', '#1F5FE0'], [20, '보통', '#7FA6EE'], [1, '저조', '#C9D8F5'], [0, '무활동', '#E5EAF2']];
  function scoreBand(score) { for (var i = 0; i < SCORE_BANDS.length; i++) if (score >= SCORE_BANDS[i][0]) return SCORE_BANDS[i]; return SCORE_BANDS[SCORE_BANDS.length - 1]; }
  function kitLabel(k) { k = String(k || ''); if (KIT_KO[k]) return KIT_KO[k]; if (k.indexOf('copy:msg:') === 0) return k.slice(9) + ' 문안 복사'; return k; }
  function kindLabel(k) { return KIND_KO[k] || k; }
  function mailKind(k) { return k === '승급' ? '승격' : k === '관리자' ? '위원장 알림' : k; }   /* 1.4.5 사용자 '승급이 아니라 승격' · '운영자 말고 위원장' */
  function pct(a, b) { return b > 0 ? Math.round(1000 * a / b) / 10 : 0; }
  function agoTxt(days) { days = Number(days); if (!isFinite(days) || days >= 999) return '기록 없음'; if (days <= 0) return '오늘'; if (days === 1) return '어제'; return days + '일 전'; }
  function delta(now, prev, unit, span) {
    span = span || '이전 7일'; now = Number(now) || 0; prev = Number(prev) || 0; var d = now - prev;
    if (!now && !prev) return '<span class="ad-delta flat">아직 없음</span>';
    if (d === 0) return '<span class="ad-delta flat">' + span + '과 같음</span>';
    return '<span class="ad-delta ' + (d > 0 ? 'up' : 'down') + '">' + (d > 0 ? '▲' : '▼') + ' ' + num(Math.abs(d)) + (unit || '') + ' <small>' + span + ' ' + num(prev) + (unit || '') + '</small></span>';
  }
  function kpiTile(label, value, unit, deltaHtml, sub, cls, tip) { return '<div class="ad-kpi' + (cls ? ' ' + cls : '') + '"' + (tip ? ' title="' + esc(tip) + '"' : '') + '><span>' + label + '</span><b>' + num(value) + '<small>' + (unit || '') + '</small></b>' + (deltaHtml || '') + (sub ? '<i>' + sub + '</i>' : '') + '</div>'; }
  /* 막대 + 꺾은선 겹친 12주 차트. bars: 실적(건, 왼쪽 축), line: 명함 · 링크 열람(회, 오른쪽 축) */
  function niceMax(v) { v = Math.max(1, v); if (v <= 4) return 4; var step = Math.pow(10, Math.floor(Math.log(v / 4) / Math.LN10)), c = [1, 2, 2.5, 5, 10]; for (var i = 0; i < c.length; i++) if (4 * c[i] * step >= v) return 4 * c[i] * step; return 40 * step; }   /* 눈금 4칸이 정수가 되게 */
  function comboChart(weeks, bars, line, opts) {
    opts = opts || {}; var vw = document.documentElement.clientWidth || 640, W = Math.max(320, Math.min(640, vw - 76)), Hh = 180, padL = 30, padR = 36, padT = 14, padB = 26, n = weeks.length, iw = (W - padL - padR) / n, skip = W < 420 ? 3 : n > 8 ? 2 : 1;   /* 좁은 화면에서는 viewBox 를 화면 폭에 맞춰 글자가 작아지지 않게 */
    var bmax = niceMax(Math.max.apply(null, bars)), lmax = niceMax(Math.max.apply(null, line)), out = '';
    var gy = function (v, max) { return padT + (Hh - padT - padB) * (1 - v / max); };
    for (var g = 0; g <= 4; g++) { var y = padT + (Hh - padT - padB) * g / 4; out += '<line class="grid" x1="' + padL + '" y1="' + y.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + y.toFixed(1) + '"/>'; out += '<text class="ax" x="' + (padL - 6) + '" y="' + (y + 4).toFixed(1) + '" text-anchor="end">' + Math.round(bmax * (1 - g / 4)) + '</text>'; out += '<text class="ax ax2" x="' + (W - padR + 6) + '" y="' + (y + 4).toFixed(1) + '">' + Math.round(lmax * (1 - g / 4)) + '</text>'; }
    for (var i = 0; i < n; i++) {
      var x = padL + i * iw, bw = Math.max(6, iw * 0.46), bx = x + (iw - bw) / 2, bh = bars[i] ? Math.max(3, (Hh - padT - padB) * bars[i] / bmax) : 0;
      out += '<rect class="bar' + (i === n - 1 ? ' now' : '') + '" x="' + bx.toFixed(1) + '" y="' + (Hh - padB - bh).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + bh.toFixed(1) + '" rx="3"><title>' + esc(fmtMD(weeks[i])) + ' 주 · 추천 실적 ' + bars[i] + '건 · 명함 · 링크 열람 ' + line[i] + '회</title></rect>';
      if ((n - 1 - i) % skip === 0) out += '<text class="ax" x="' + (x + iw / 2).toFixed(1) + '" y="' + (Hh - 8) + '" text-anchor="middle">' + esc(fmtMD(weeks[i])) + '</text>';
    }
    var pts = line.map(function (v, i) { return (padL + i * iw + iw / 2).toFixed(1) + ',' + gy(v, lmax).toFixed(1); });
    out += '<polyline class="ln" points="' + pts.join(' ') + '"/>';
    line.forEach(function (v, i) { out += '<circle class="dot' + (i === n - 1 ? ' now' : '') + '" cx="' + (padL + i * iw + iw / 2).toFixed(1) + '" cy="' + gy(v, lmax).toFixed(1) + '" r="3.2"><title>' + esc(fmtMD(weeks[i])) + ' 주 · 명함 · 링크 열람 ' + v + '회</title></circle>'; });
    return '<svg class="ad-combo" viewBox="0 0 ' + W + ' ' + Hh + '" preserveAspectRatio="none" role="img" aria-label="' + esc(opts.label || '12주 추이') + '">' + out + '</svg>';
  }
  function sparkline(vals, color) {
    var W = 120, Hh = 34, n = vals.length, max = Math.max(1, Math.max.apply(null, vals)), pts = vals.map(function (v, i) { return (2 + i * (W - 4) / (n - 1)).toFixed(1) + ',' + (Hh - 3 - (Hh - 8) * v / max).toFixed(1); });
    return '<svg class="ad-spark" viewBox="0 0 ' + W + ' ' + Hh + '" preserveAspectRatio="none" aria-hidden="true"><polyline points="' + pts.join(' ') + '" style="stroke:' + color + '"/><circle cx="' + pts[n - 1].split(',')[0] + '" cy="' + pts[n - 1].split(',')[1] + '" r="2.6" style="fill:' + color + '"/></svg>';
  }
  function sparkTile(label, vals, unit, color) { var sum = vals.reduce(function (a, b) { return a + b; }, 0); return '<div class="ad-sparkbox"><div><span>' + label + '</span><b>' + num(vals[vals.length - 1]) + '<small>' + unit + ' 이번 주</small></b><i>12주 합계 ' + num(sum) + unit + '</i></div>' + sparkline(vals, color) + '</div>'; }
  function segBar(parts, total) {   /* parts: [[label, value, color]] */
    var t = total || parts.reduce(function (a, p) { return a + p[1]; }, 0); if (!t) return '<div class="ad-seg ad-seg--empty"><i style="width:100%"></i></div>';
    return '<div class="ad-seg">' + parts.filter(function (p) { return p[1] > 0; }).map(function (p) { return '<i style="width:' + (100 * p[1] / t).toFixed(1) + '%;background:' + p[2] + '"><title>' + esc(p[0]) + ' ' + num(p[1]) + ' (' + pct(p[1], t) + '%)</title></i>'; }).join('') + '</div>';
  }
  function legend(parts, total) { var t = total || parts.reduce(function (a, p) { return a + p[1]; }, 0); return '<div class="ad-legend">' + parts.map(function (p) { return '<span><i style="background:' + p[2] + '"></i>' + esc(p[0]) + ' <b>' + num(p[1]) + '</b>' + (t ? ' <small>' + pct(p[1], t) + '%</small>' : '') + '</span>'; }).join('') + '</div>'; }
  function scoreBar(r) {
    var p = r.parts || {}, segs = [['실적', p.credit || 0, '#0B8F84'], ['열람', p.reach || 0, '#1F5FE0'], ['라운지 이용', p.visit || 0, '#7C3AED'], ['활동 링크', p.link || 0, '#F0A24A'], ['도구 사용', p.kit || 0, '#E06B8A']];
    return '<div class="ad-score"><b>' + r.score + '</b><div class="ad-seg ad-seg--score">' + segs.filter(function (s) { return s[1] > 0; }).map(function (s) { return '<i style="width:' + s[1] + '%;background:' + s[2] + '"><title>' + s[0] + ' ' + s[1] + '점</title></i>'; }).join('') + '</div></div>';
  }
  function trendIcon(t) { return t === 'up' ? '<span class="ad-tr up" title="최근 4주 실적이 그 전 4주보다 많음">▲</span>' : t === 'down' ? '<span class="ad-tr down" title="최근 4주 실적이 그 전 4주보다 적음">▼</span>' : t === 'flat' ? '<span class="ad-tr flat" title="최근 4주와 그 전 4주가 같음">━</span>' : '<span class="ad-tr none">·</span>'; }
  function who(r) { return '<button type="button" class="ad-who" data-member="' + esc(r.code) + '"><b>' + esc(r.name) + '</b><small>' + esc(r.code) + '</small>' + (r.badge ? '<em class="lg-chip lg-chip--gold">' + esc(r.badge) + '</em>' : '') + '</button>'; }
  function funnelHTML(f) {
    var steps = [['위촉', f.members], ['첫 로그인', f.loggedIn], ['공유 시작', f.spread], ['첫 실적', f.credited], ['확정 실적', f.confirmed], ['지급 받음', f.paid]];
    var max = Math.max(1, f.members);
    return '<div class="ad-funnel">' + steps.map(function (s, i) { var prev = i ? steps[i - 1][1] : s[1]; return '<div class="ad-fstep"><span>' + s[0] + '</span><div class="ad-fbar"><i style="width:' + Math.max(2, 100 * s[1] / max).toFixed(1) + '%"></i></div><b>' + num(s[1]) + '<small>명 · ' + pct(s[1], max) + '%</small></b>' + (i ? '<em>' + (prev ? pct(s[1], prev) : 0) + '%</em>' : '<em>기준</em>') + '</div>'; }).join('') + '</div><p class="ad-fnote">막대는 전체 위원(종료 제외) 대비 비율, 오른쪽 %는 바로 앞 단계에서 넘어온 비율. 공유 시작 = 명함 · 링크가 한 번이라도 열렸거나 도구 · 활동 링크를 쓴 위원</p>';
  }
  function heatmapHTML(heat) {
    var days = ['일', '월', '화', '수', '목', '금', '토'], max = 1, total = 0, blocks = [];
    for (var d = 0; d < 7; d++) { blocks.push([]); for (var b = 0; b < 12; b++) { var v = (heat[d][b * 2] || 0) + (heat[d][b * 2 + 1] || 0); blocks[d].push(v); if (v > max) max = v; total += v; } }
    var bestD = -1, bestB = -1, bestV = -1; blocks.forEach(function (row, d) { row.forEach(function (v, b) { if (v > bestV) { bestV = v; bestD = d; bestB = b; } }); });
    var html = '<div class="ad-heat"><div class="ad-heat-row ad-heat-x"><span></span>' + [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22].map(function (h) { return '<i>' + (h % 4 === 0 ? h + '시' : '') + '</i>'; }).join('') + '</div>';
    for (var r = 0; r < 7; r++) { var order = (r + 1) % 7; html += '<div class="ad-heat-row"><span>' + days[order] + '</span>' + blocks[order].map(function (v, b) { var a = v ? 0.12 + 0.88 * v / max : 0; return '<i style="background:rgba(31,95,224,' + a.toFixed(2) + ')" title="' + days[order] + ' ' + (b * 2) + '~' + (b * 2 + 2) + '시 · ' + v + '명"></i>'; }).join('') + '</div>'; }
    html += '</div>';
    return { html: html, total: total, best: bestV > 0 ? days[bestD] + '요일 ' + (bestB * 2) + '~' + (bestB * 2 + 2) + '시' : '' };
  }
  function statCell(label, value, sub) { return '<div class="ad-statc"><span>' + label + '</span><b>' + value + '</b>' + (sub ? '<i>' + sub + '</i>' : '') + '</div>'; }
  function riskList(title, items, render, icon, empty) {
    return '<div class="ad-risk"><h3>' + ic(icon || 'clock') + title + '<b class="' + (items.length ? 'n' : 'n zero') + '">' + items.length + '</b></h3>' + (items.length ? '<ul>' + items.slice(0, 12).map(function (it) { return '<li>' + who(it) + '<span>' + render(it) + '</span></li>'; }).join('') + (items.length > 12 ? '<li class="more">외 ' + (items.length - 12) + '명</li>' : '') + '</ul>' : '<p class="ok">' + ic('check') + (empty || '해당 위원 없음') + '</p>') + '</div>';
  }
  var RANK_KEYS = { score: ['score', -1], credits30: ['credits30', -1], credits: ['credits', -1], reach30: ['reach30', -1], visits30: ['visits30', -1], kit: ['kitDays30', -1], recent: ['silentDays', 1], since: ['sinceDays', -1] };
  function rankRows(an) {
    var st = S.rank, key = RANK_KEYS[st.key] || RANK_KEYS.score, list = an.rank.filter(function (r) { return st.all || r.status !== '종료'; });
    list.sort(function (a, b) { var d = (Number(a[key[0]]) || 0) - (Number(b[key[0]]) || 0); if (d) return d * key[1] * (st.dir || 1); return a.rank - b.rank; });
    return list;
  }
  function insightTabHTML(a) {
    var an = a.analytics;
    if (!an || an.error) return '<div class="lg-card"><h2>' + ic('bar-chart-3') + '분석</h2><p>분석 데이터를 만들지 못했습니다' + (an && an.error ? ': ' + esc(an.error) : '. 서버를 새 판(1.3.0)으로 올리면 이 탭이 채워집니다.') + '</p></div>';
    var k = an.kpi, s = an.stats, f = an.funnel, sr = an.series, mo = an.monthly, risk = an.risk, dist = an.dist;
    /* 1) KPI */
    var payAlert = a.isPayoutToday && a.tiles.dueN > 0 ? '<div class="ad-alert">' + ic('credit-card') + '<b>오늘 정산일</b> 지급 대상 ' + a.tiles.dueN + '명 · ' + won(a.tiles.dueSum) + ' <button type="button" class="lg-link" data-tab="pay">정산표 열기</button></div>' : '';
    /* 1.4.3 KPI(사용자: '누적 건수도 나와야지 · 라운지 이용도 9회가 아니고 9명이어야지'): 결제 즉시 확정이라 '확정' 칸은 뺌(추천 결제와 같음),
       '활동 위원(7일 안 활동 신호)'은 위촉 · 로그인만으로도 100%가 돼 뜻이 약해 '실적 있는 위원'으로 바꿈 */
    var kv = k.visitors || { now: 0, prev: 0, m30: 0, loggedIn: 0, of: 0 }, kc = k.credited || { all: 0, m30: 0, of: 0 }, kcr = pct(kc.all, kc.of);
    var rpp = k.reach.people || null, c7 = k.reach.ch7 || null;
    var kpis = '<div class="ad-kpis">' +
      kpiTile('누적 추천 결제', k.credits.all, '건', '<span class="ad-delta ' + (k.credits.now ? 'up' : 'flat') + '">' + (k.credits.now ? '▲ ' + num(k.credits.now) + '건 <small>최근 7일</small>' : '최근 7일 추천 없음') + '</span>', (k.credits.amount != null ? '누적 결제 ' + won(k.credits.amount) + ' · ' : '') + '이번 달 ' + num(k.credits.month || 0) + '건 · 지난달 ' + num(k.credits.prevMonth || 0) + '건', 'hi') +
      kpiTile('최근 7일 추천 결제', k.credits.now, '건', delta(k.credits.now, k.credits.prev, '건'), '30일 ' + num(k.credits.m30) + '건 · 취소 · 환불 30일 ' + num(k.canceled.m30) + '건') +
      /* 1.4.7 사용자 '최근 7일 확산은 뭐야? 확 와닿지 않는데': 위원 명함 · 추천 링크 · QR 을 연 사람(같은 브라우저는 한 사람)으로, 열람 횟수와 경로를 아래에 */
      kpiTile('최근 7일 명함 · 링크 방문', rpp ? rpp.now : k.reach.now, '명', delta(rpp ? rpp.now : k.reach.now, rpp ? rpp.prev : k.reach.prev, '명'),
        '열람 ' + num(k.reach.now) + '회' + (c7 ? '(명함 ' + num(c7.card || 0) + ' · 링크 ' + num(Math.max(0, k.reach.now - (c7.card || 0))) + ')' : '') + ' · 누적 ' + num(k.reach.all || 0) + '회', '',
        '위원 명함 페이지와 추천 링크(신청 페이지 · 바로 결제 QR)를 열어 본 사람 수입니다. 같은 브라우저는 한 사람으로 세고, 열람 횟수는 같은 사람이라도 날이 다르거나 다른 위원 것을 열면 따로 셉니다. 로그인한 위원 본인 열람은 빠지고, 위원 라운지에서는 확산으로 보입니다') +
      kpiTile('라운지 이용 위원', kv.now, '명', delta(kv.now, kv.prev, '명'), '최근 7일 라운지를 연 위원 · 30일 ' + num(kv.m30) + '명 · 첫 로그인 ' + num(kv.loggedIn) + '/' + num(kv.of) + '명') +
      kpiTile('실적 있는 위원', kc.all, '명', '<span class="ad-delta ' + (kcr >= 30 ? 'up' : 'flat') + '">' + kcr + '% <small>' + num(kc.of) + '명 중</small></span>', '최근 30일 실적 ' + num(kc.m30) + '명') +
      kpiTile('신규 위촉', k.joined.m30, '명', delta(k.joined.m30, k.joined.prev30, '명', '그 전 30일'), '최근 30일 · 7일 ' + num(k.joined.now) + '명') +
      '</div>';
    /* 2) 추이 */
    var trend = '<div class="lg-card"><h2>' + ic('line-chart') + '12주 활동 추이<span class="sub">막대 추천 결제(건) · 선 명함 · 링크 열람(회) · 월요일 시작 주</span></h2>' +
      comboChart(sr.weeks, sr.credits, sr.reach, { label: '12주 추천 실적과 명함 · 링크 열람' }) +
      '<div class="ad-legend ad-legend--chart"><span><i style="background:#1F5FE0"></i>추천 결제 <b>' + num(sr.credits.reduce(function (x, y) { return x + y; }, 0)) + '건</b></span><span><i style="background:#0B8F84;border-radius:2px;height:3px"></i>명함 · 링크 열람 <b>' + num(sr.reach.reduce(function (x, y) { return x + y; }, 0)) + '회</b></span><span><i style="background:#F0A24A"></i>취소 · 환불 <b>' + num(sr.canceled.reduce(function (x, y) { return x + y; }, 0)) + '건</b></span><span class="lg-muted" style="font-weight:500">마지막 막대 · 점은 진행 중인 이번 주</span></div>' +
      '<div class="ad-sparks">' + sparkTile('라운지 이용 위원', sr.visitors || sr.visits, '명', '#7C3AED') + sparkTile('도구 사용 · 저장', sr.kit, '회', '#E06B8A') + sparkTile('활동 링크', sr.links, '건', '#F0A24A') + sparkTile('신규 위촉', sr.joined, '명', '#0B8F84') + '</div></div>';
    /* 3) 순위 */
    var top3 = an.rank.filter(function (r) { return r.status !== '종료' && r.score > 0; }).slice(0, 3);
    var podium = top3.length ? '<div class="ad-podium">' + top3.map(function (r, i) { var b = scoreBand(r.score); return '<button type="button" class="ad-pod p' + (i + 1) + '" data-member="' + esc(r.code) + '"><span class="medal">' + (i + 1) + '</span><b>' + esc(r.name) + '</b><small>' + esc(r.code) + (r.badge ? ' · ' + esc(TIER_WORD[r.badge] || r.badge) : '') + '</small><em style="color:' + b[2] + '">' + r.score + '점 · ' + b[1] + '</em><i>30일 실적 ' + r.credits30 + ' · 열람 ' + num(r.reach30) + ' · 이용 ' + r.visits30 + '일</i></button>'; }).join('') + '</div>' : '<p class="lg-empty" style="text-align:center;padding:14px 0">아직 활동 점수가 있는 위원이 없습니다. 명함 · 링크 열람 · 실적 · 라운지 이용이 기록되면 순위가 생깁니다.</p>';
    var list = rankRows(an), rk = S.rank;
    function th(key, label, cls) { var on = rk.key === key, sign = (RANK_KEYS[key] || RANK_KEYS.score)[1] * (rk.dir || 1); return '<th class="' + (cls || '') + (on ? ' on' : '') + '"><button type="button" data-sort="' + key + '">' + label + (on ? (sign < 0 ? ' ▼' : ' ▲') : '') + '</button></th>'; }
    var rows = list.map(function (r, i) {
      var band = scoreBand(r.score), ended = r.status === '종료';
      return '<tr class="ad-row' + (ended ? ' done' : '') + '" data-code="' + esc(r.code) + '"><td class="num"><span class="ad-rank r' + (r.rank <= 3 && !ended && r.score > 0 ? r.rank : 0) + '">' + (ended ? '-' : r.rank) + '</span></td><td>' + who(r) + (r.status !== '활동' ? ' ' + statusChip(r.status) : '') + '</td><td>' + (ended ? '<span class="lg-muted">-</span>' : scoreBar(r)) + '</td><td class="num">' + r.credits30 + (r.pending ? ' <small class="lg-muted">(대기 ' + r.pending + ')</small>' : '') + '</td><td class="num">' + r.credits + ' ' + trendIcon(r.trend) + '</td><td class="num">' + num(r.reach30) + (r.reachPrev30 !== undefined && r.reach30 !== r.reachPrev30 ? ' <small class="' + (r.reach30 > r.reachPrev30 ? 'up' : 'down') + '">' + (r.reach30 > r.reachPrev30 ? '▲' : '▼') + num(Math.abs(r.reach30 - r.reachPrev30)) + '</small>' : '') + '</td><td class="num">' + r.visits30 + '</td><td class="num">' + (r.kitDays30 + r.links30) + (r.saves30 ? ' <small class="lg-muted">저장 ' + r.saves30 + '</small>' : '') + '</td><td>' + agoTxt(r.silentDays) + (r.lastKind ? ' <small class="lg-muted">' + esc(kindLabel(r.lastKind)) + '</small>' : '') + '</td><td><span class="ad-band" style="background:' + band[2] + (band[0] >= 50 ? ';color:#fff' : '') + '">' + band[1] + '</span></td></tr>';
    }).join('');
    var ranking = '<div class="lg-card"><h2>' + ic('trophy') + '위원 활동 순위<span class="sub">활동 점수 100점: 최근 30일 실적 ' + an.scoreRule.credit + '점/건(최대 ' + an.scoreRule.creditMax + ') · 명함 · 링크 열람 ' + an.scoreRule.reach + '점/회(최대 ' + an.scoreRule.reachMax + ') · 라운지 이용 ' + an.scoreRule.visit + '점/일(최대 ' + an.scoreRule.visitMax + ') · 활동 링크 ' + an.scoreRule.link + '점/건(최대 ' + an.scoreRule.linkMax + ') · 도구 사용 ' + an.scoreRule.kit + '점/일(최대 ' + an.scoreRule.kitMax + ')</span></h2>' + podium +
      '<div class="ad-filter" style="margin-top:14px"><span class="lg-muted" style="font-size:12.5px">' + list.length + '명 · 열 제목을 누르면 정렬</span><label class="lg-toggle" style="margin-left:auto"><input type="checkbox" id="adRankAll"' + (rk.all ? ' checked' : '') + '> 종료 위원 포함</label></div>' +
      '<div class="ad-scroll"><table class="lg-tbl ad-ranktbl"><thead><tr>' + th('score', '순위', 'num') + '<th>위원</th>' + th('score', '활동 점수') + th('credits30', '30일 실적', 'num') + th('credits', '누적 확정', 'num') + th('reach30', '30일 열람', 'num') + th('visits30', '이용일', 'num') + th('kit', '도구 · 링크', 'num') + th('recent', '마지막 활동') + '<th>활동 온도</th></tr></thead><tbody>' + (rows || '<tr><td colspan="10" class="lg-empty">위원이 없습니다</td></tr>') + '</tbody></table></div>' +
      '<p class="ad-fnote">누적 확정 옆 ▲▼ 는 최근 4주 실적을 그 전 4주와 비교. 30일 열람 옆 ▲▼ 는 그 전 30일과 비교. 행을 누르면 위원 상세 · 조치</p></div>';
    /* 4) 활동 온도 격자 */
    var grid = an.rank.filter(function (r) { return r.status !== '종료'; }).slice().sort(function (x, y) { return y.score - x.score || x.name.localeCompare(y.name, 'ko'); });
    var tiles = grid.map(function (r) { var b = scoreBand(r.score), paused = r.status !== '활동'; return '<button type="button" class="ad-tile-m' + (paused ? ' paused' : '') + '" data-member="' + esc(r.code) + '" style="background:' + b[2] + (b[0] >= 50 ? ';color:#fff' : '') + '" title="' + esc(r.name) + ' · ' + r.score + '점 · ' + b[1] + (paused ? ' · ' + esc(r.status) : '') + ' · 마지막 활동 ' + agoTxt(r.silentDays) + '"><b>' + esc(r.name) + '</b><small>' + r.score + '</small></button>'; }).join('');
    var bandCounts = SCORE_BANDS.map(function (b, i) { var lo = b[0], hi = i ? SCORE_BANDS[i - 1][0] - 1 : 100; return [b[1] + (lo ? ' ' + lo + (hi > lo ? '~' + hi : '+') : ' 0') + '점', grid.filter(function (r) { return r.score >= lo && r.score <= hi; }).length, b[2]]; });
    var heatGrid = '<div class="lg-card"><h2>' + ic('layout-grid') + '활동 온도<span class="sub">위원 ' + grid.length + '명(종료 제외) · 색이 진할수록 최근 30일 활동이 많음 · 빗금은 휴면 예정 · 휴면</span></h2><div class="ad-grid">' + tiles + '</div>' + legend(bandCounts, grid.length) + '</div>';
    /* 5) 점검 목록 */
    var risks = '<div class="lg-card"><h2>' + ic('alert-triangle') + '점검이 필요한 위원<span class="sub">누르면 상세 · 조치(메모 · 위촉 메일 다시 · 휴면 · 복귀 · 종료)</span></h2><div class="ad-risks">' +
      riskList('실적 기한 임박 · 경과', risk.deadline, function (it) { return it.daysLeft < 0 ? '<b class="bad">기한 ' + Math.abs(it.daysLeft) + '일 지남</b>' : it.daysLeft === 0 ? '<b class="bad">오늘까지</b>' : '<b>D-' + it.daysLeft + '</b>' + ' · ' + fmtMD(it.deadline) + (it.first ? ' · 첫 실적' : ''); }, 'clock', '기한 7일 안에 든 위원 없음') +
      riskList('활동 게이지 낮음(30% 이하)', risk.lowGauge, function (it) { return '<b>' + it.gauge + '%</b> · 마지막 신호 ' + agoTxt(it.silentDays); }, 'gauge') +
      riskList('첫 로그인 전', risk.noLogin, function (it) { return '위촉 ' + it.sinceDays + '일째 · 아직 로그인 전'; }, 'user-check', '모든 위원이 라운지에 들어왔습니다') +
      riskList(an.silentDays + '일 이상 무신호(활동 중)', risk.silent, function (it) { return '<b>' + it.silentDays + '일</b>' + (it.lastKind ? ' · 마지막 ' + esc(kindLabel(it.lastKind)) : ''); }, 'clock') +
      riskList('정산 정보 미등록(실적 있음)', risk.noPayinfo, function (it) { var xs = []; if (it.unpaid) xs.push('<b>' + won(it.unpaid) + '</b> 보류'); if (it.pending) xs.push('확정 대기 ' + it.pending + '건'); return xs.join(' · ') || '실적 있음'; }, 'credit-card') +
      riskList('휴면 예정 · 휴면', risk.paused, function (it) { return statusChip(it.status) + (it.reason ? ' <small>' + esc(it.reason) + '</small>' : '') + (it.changed ? ' · ' + fmtMD(it.changed) + '부터' : ''); }, 'users') +
      '</div></div>';
    /* 6) 퍼널 · 통계 */
    var statsGrid = '<div class="ad-stats">' +
      statCell('위원당 확정 실적', num(s.creditsMean) + '<small>건</small>', '중앙값 ' + num(s.creditsMedian) + '건 · 0건 위원 ' + s.zeroShare + '%') +
      statCell('위원당 누적 열람', num(s.reachMean) + '<small>회</small>', '중앙값 ' + num(s.reachMedian) + '회') +
      statCell('활동 점수 평균', num(s.scoreMean) + '<small>점</small>', '중앙값 ' + num(s.scoreMedian) + '점') +
      statCell('상위 20% 실적 점유율', s.top20Share + '<small>%</small>', '상위 ' + s.top20N + '명이 낸 확정 실적 비율') +
      statCell('첫 실적까지', (s.firstCreditN ? num(s.firstCreditMean) + '<small>일</small>' : '-'), s.firstCreditN ? '중앙값 ' + num(s.firstCreditMedian) + '일 · ' + s.firstCreditN + '명 기준' : '아직 첫 실적이 없습니다') +
      statCell('첫 로그인까지', (s.firstLoginN ? num(s.firstLoginMean) + '<small>일</small>' : '-'), s.firstLoginN ? '중앙값 ' + num(s.firstLoginMedian) + '일 · ' + s.firstLoginN + '명 기준' : '아직 로그인한 위원이 없습니다') +
      statCell('열람 → 추천 결제(90일)', (s.reachToCredit90 === null ? '-' : s.reachToCredit90 + '<small>%</small>'), '명함 · 링크가 열린 수 대비 결제') +
      statCell('취소 · 환불율', s.cancelRate + '<small>%</small>', '본인 결제 비율 ' + s.selfRate + '%') +
      '</div>';
    var funnelCard = '<div class="ad-two"><div class="lg-card"><h2>' + ic('filter') + '위원 여정 퍼널<span class="sub">전체 ' + f.members + '명</span></h2>' + funnelHTML(f) + '</div>' +
      '<div class="lg-card"><h2>' + ic('bar-chart-3') + '통계<span class="sub">종료 위원 제외</span></h2>' + statsGrid + '</div></div>';
    /* 7) 채널 · 시간대 · 도구 */
    var chParts = ['card', 'go', 'intro', 'experts', 'other'].map(function (c) { return [CHANNEL_KO[c][0], an.channel[c] || 0, CHANNEL_KO[c][1]]; }), chTotal = chParts.reduce(function (x, p) { return x + p[1]; }, 0);
    var hm = heatmapHTML(an.heat);
    var kitKeys = Object.keys(an.kit).sort(function (x, y) { return an.kit[y] - an.kit[x]; }), kitMax = Math.max(1, kitKeys.length ? an.kit[kitKeys[0]] : 1);
    var kitRows = kitKeys.map(function (kk) { return '<div class="ad-hrow"><span>' + esc(kitLabel(kk)) + '</span><div class="ad-hbar"><i style="width:' + (100 * an.kit[kk] / kitMax).toFixed(1) + '%"></i></div><b>' + num(an.kit[kk]) + '</b></div>'; }).join('');
    var channelCard = '<div class="ad-two"><div class="lg-card"><h2>' + ic('radar') + '어디서 열렸나<span class="sub">최근 30일 명함 · 링크 열람 ' + num(chTotal) + '회의 경로</span></h2>' + segBar(chParts, chTotal) + legend(chParts, chTotal) +
      '<h3 class="ad-h3">언제 열리나 <small>요일 × 2시간 · 30일 열람' + (hm.best ? ' · 가장 많이 열린 때 <b>' + esc(hm.best) + '</b>' : '') + '</small></h3>' + hm.html + '</div>' +
      '<div class="lg-card"><h2>' + ic('mouse-pointer-click') + '확산 도구 사용<span class="sub">최근 30일 · 위원이 라운지에서 복사 · 연 횟수(항목별 하루 1회)</span></h2>' + (kitRows || '<p class="lg-empty">아직 기록이 없습니다. 위원이 라운지에서 링크 · 문안을 복사하면 여기에 쌓입니다.</p>') +
      '<div class="ad-mini"><div><span>명함 이미지 저장</span><b>' + num(k.tools.saves30) + '</b></div><div><span>명함 공유</span><b>' + num(k.tools.shares30) + '</b></div><div><span>활동 링크 등록</span><b>' + num(k.tools.links30) + '</b></div><div><span>증명서 요청</span><b>' + num(k.tools.cert30) + '</b></div></div></div></div>';
    /* 8) 월별 · 코호트 · 분포 · 정산 */
    var moMax = { c: Math.max(1, Math.max.apply(null, mo.credits)), r: Math.max(1, Math.max.apply(null, mo.reach)), p: Math.max(1, Math.max.apply(null, mo.paid)) };
    var moRows = mo.months.map(function (m, i) { var isNow = i === mo.months.length - 1; return '<tr' + (isNow ? ' class="now"' : '') + '><td>' + esc(m.replace('-', '.')) + (isNow ? ' <small class="lg-muted">진행 중</small>' : '') + '</td><td class="num">' + num(mo.joined[i]) + '</td><td><div class="ad-cell"><i style="width:' + (100 * mo.credits[i] / moMax.c).toFixed(1) + '%"></i><b>' + num(mo.credits[i]) + '</b></div></td><td><div class="ad-cell teal"><i style="width:' + (100 * mo.reach[i] / moMax.r).toFixed(1) + '%"></i><b>' + num(mo.reach[i]) + '</b></div></td><td class="num">' + num(mo.visitors ? mo.visitors[i] : mo.visits[i]) + '</td><td><div class="ad-cell gold"><i style="width:' + (100 * mo.paid[i] / moMax.p).toFixed(1) + '%"></i><b>' + won(mo.paid[i]) + (mo.paidN[i] ? ' <small>' + mo.paidN[i] + '건</small>' : '') + '</b></div></td></tr>'; }).join('');
    var payKpi = '<div class="ad-mini ad-mini--pay"><div><span>누적 지급</span><b>' + won(k.pay.paidTotal) + '</b><i>' + k.pay.paidMembers + '명 · ' + k.pay.paidRows + '회</i></div><div><span>최근 30일 지급</span><b>' + won(k.pay.paid30) + '</b><i>그 전 30일 ' + won(k.pay.paidPrev30) + '</i></div><div><span>지급 예정</span><b>' + won(k.pay.dueTotal) + '</b><i>' + k.pay.dueN + '건</i></div><div><span>보류(정산 정보 없음)</span><b>' + won(k.pay.holdTotal) + '</b><i>' + k.pay.holdN + '건</i></div><div><span>지급 위원당 평균</span><b>' + won(k.pay.avgPerPaidMember) + '</b><i>지급 위원 ' + num(k.pay.paidMembers) + '명 기준</i></div></div>';
    var monthlyCard = '<div class="lg-card"><h2>' + ic('calendar') + '월별 흐름과 정산<span class="sub">최근 ' + an.months + '개월</span></h2>' + payKpi + '<div class="ad-scroll"><table class="lg-tbl ad-motbl"><thead><tr><th>월</th><th class="num">신규 위촉</th><th>추천 결제</th><th>명함 · 링크 열람</th><th class="num">라운지 이용 위원</th><th>지급액</th></tr></thead><tbody>' + moRows + '</tbody></table></div></div>';
    var cohortRows = an.cohorts.slice().reverse().map(function (c) { return '<tr><td>' + esc(c.month.replace('-', '.')) + '</td><td class="num">' + c.n + '</td><td class="num">' + c.active + '</td><td class="num">' + c.loggedInRate + '%</td><td class="num">' + c.creditedRate + '%</td><td class="num">' + num(c.creditsAvg) + '</td><td class="num">' + num(c.reachAvg) + '</td></tr>'; }).join('');
    var tierParts = [['캠페인위원', dist.tier.base || 0, '#C9D8F5'], ['선임위원', dist.tier['선임'] || 0, '#7FA6EE'], ['책임위원', dist.tier['책임'] || 0, '#7C3AED'], ['수석위원', dist.tier['수석'] || 0, '#F0A24A']];
    var stParts = [['활동', dist.status['활동'] || 0, '#0B8F84'], ['휴면 예정', dist.status['휴면예정'] || 0, '#F0A24A'], ['휴면', dist.status['휴면'] || 0, '#E06B8A'], ['종료', dist.status['종료'] || 0, '#A0AEC0']];
    var crParts = [['0건', dist.credits[0], '#E5EAF2'], ['1~2건', dist.credits[1], '#C9D8F5'], ['3~9건', dist.credits[2], '#7FA6EE'], ['10~29건', dist.credits[3], '#1F5FE0'], ['30건+', dist.credits[4], '#0F2A5F']];
    var gaParts = [['0~30%', dist.gauge[0], '#E06B8A'], ['31~60%', dist.gauge[1], '#F0A24A'], ['61~100%', dist.gauge[2], '#0B8F84']];
    var distCard = '<div class="ad-two"><div class="lg-card"><h2>' + ic('users-round') + '위촉 월별 정착<span class="sub">코호트 · 종료 제외</span></h2><div class="ad-scroll"><table class="lg-tbl ad-fit"><thead><tr><th>위촉 월</th><th class="num">인원</th><th class="num">활동 중</th><th class="num">로그인율</th><th class="num">실적 보유율</th><th class="num">평균 확정</th><th class="num">평균 열람</th></tr></thead><tbody>' + (cohortRows || '<tr><td colspan="7" class="lg-empty">아직 없음</td></tr>') + '</tbody></table></div></div>' +
      '<div class="lg-card"><h2>' + ic('pie-chart') + '분포</h2><div class="ad-dist"><div><span>등급(직함)</span>' + segBar(tierParts) + legend(tierParts) + '</div><div><span>상태(전체 ' + a.roster.length + '명)</span>' + segBar(stParts) + legend(stParts) + '</div><div><span>누적 확정 실적 구간</span>' + segBar(crParts) + legend(crParts) + '</div><div><span>활동 게이지(활동 중)</span>' + segBar(gaParts) + legend(gaParts) + '</div></div></div></div>';
    /* 9) 메일 · 타임라인 */
    var mk = Object.keys(an.mail.byKind).sort(function (x, y) { return (an.mail.byKind[y].sent + an.mail.byKind[y].wait) - (an.mail.byKind[x].sent + an.mail.byKind[x].wait); });
    var mailRows = mk.map(function (kk) { var b = an.mail.byKind[kk]; return '<tr><td>' + esc(mailKind(kk)) + '</td><td class="num">' + num(b.sent) + '</td><td class="num">' + (b.failed ? '<b style="color:#991B12">' + num(b.failed) + '</b>' : '0') + '</td><td class="num">' + num(b.wait) + '</td></tr>'; }).join('');
    var tl = an.timeline.map(function (t) { return '<li><span class="at">' + esc(String(t.at).slice(5, 16)) + '</span>' + (t.name ? '<button type="button" class="lg-link" data-member="' + esc(t.code) + '">' + esc(t.name) + '</button>' : '<span>' + esc(t.code) + '</span>') + ' <b>' + esc(kindLabel(t.kind)) + '</b>' + (t.kind === 'kit' ? ' <small>' + esc(kitLabel(t.path)) + '</small>' : t.kind === 'link' ? ' <small><a href="' + esc(t.path) + '" target="_blank" rel="noopener">' + esc(short(t.path).slice(0, 40)) + '</a></small>' : t.detail && t.kind !== 'save' && t.kind !== 'share' && t.kind !== '라운지' ? ' <small>' + esc(String(t.detail).slice(0, 40)) + '</small>' : '') + '</li>'; }).join('');
    var tailCards = '<div class="ad-two"><div class="lg-card"><h2>' + ic('mail') + '메일 30일<span class="sub">대기 ' + num(an.mail.wait) + '통 · 발송 ' + num(an.mail.sent30) + ' · 실패 ' + num(an.mail.failed30) + '</span></h2>' + (mailRows ? '<table class="lg-tbl ad-fit"><thead><tr><th>종류</th><th class="num">발송</th><th class="num">실패</th><th class="num">대기</th></tr></thead><tbody>' + mailRows + '</tbody></table>' : '<p class="lg-empty">최근 30일에 만들어진 메일이 없습니다</p>') +
      '<h3 class="ad-h3">무엇을 모으나</h3><ul class="ad-collect"><li><b>명함 · 링크 열람</b> 위원 명함 · 바로 결제 · 소개 · AIEP 링크가 열린 수(같은 브라우저는 위원마다 하루 1회, 경로 · 시각 · 방문자 표식으로 사람 수도 셈). 위원 라운지에서는 같은 기록이 &lsquo;확산&rsquo;으로 보임</li><li><b>라운지 이용</b> 위원이 라운지를 연 날(하루 1회 활동 신호로도 인정)</li><li><b>도구 사용</b> 링크 · 문안 복사, QR 열기, 매뉴얼 내려받기(항목별 하루 1회)</li><li><b>명함 저장 · 공유</b> 명단의 명함 이미지 저장 · 공유 버튼</li><li><b>실적 · 정산</b> 결제 · 확정 · 취소 · 지급(아임웹 5분 폴링)</li><li><b>상태 · 메일</b> 게이지 · 휴면 · 종료 · 발송 결과</li></ul></div>' +
      '<div class="lg-card"><h2>' + ic('clock') + '최근 활동 타임라인<span class="sub">명함 · 링크 열람 제외 · 최근 ' + an.timeline.length + '건</span></h2><ul class="ad-tl">' + (tl || '<li class="lg-muted">아직 기록이 없습니다</li>') + '</ul></div></div>';
    return payAlert + kpis + trend + ranking + heatGrid + risks + funnelCard + channelCard + monthlyCard + distCard + tailCards +
      '<p class="lg-foot">계산 시각 ' + esc(an.at) + ' · 이 화면의 숫자는 운영 시트의 위원명단 · 활동내역 · 정산관리 · 활동_로그(120일 보관) · 활동_메일에서 요청 때마다 다시 셉니다. 개인정보(계좌 · 주민등록번호)는 이 탭에 나오지 않습니다.</p>';
  }
  function bindAdminForms() {
    var q = $('adQ'); if (q) q.addEventListener('input', function () { S.roster.q = q.value; var box = $('adTab'); var pos = q.selectionStart; box.innerHTML = rosterTabHTML(S.admin); var q2 = $('adQ'); q2.focus(); try { q2.setSelectionRange(pos, pos); } catch (e) { /* 무시 */ } });
    var nf = $('adNotice'); if (nf) {
      $('nAud').addEventListener('change', function () { $('nCodesBox').hidden = this.value !== '개별'; });
      nf.addEventListener('submit', function (e) {
        e.preventDefault(); var er = $('nErr'); er.classList.remove('is-on');
        var title = $('nTitle').value.trim(), body = $('nBody').value.trim(), link = $('nLink').value.trim(), aud = $('nAud').value, codes = $('nCodes').value.split(/[,\s]+/).filter(Boolean), mail = $('nMail').checked;
        if (!title || !body) { er.textContent = '제목과 본문을 입력해 주세요.'; er.classList.add('is-on'); return; }
        if (aud === '개별' && !codes.length) { er.textContent = '위원 코드를 입력해 주세요.'; er.classList.add('is-on'); return; }
        confirmBox('공지를 보낼까요?', '대상: ' + aud + (mail ? ' · 라운지 게시 + 메일' : ' · 라운지 게시만'), '보내기').then(function (ok) {
          if (!ok) return; var b = nf.querySelector('button[type="submit"]'); busy(b, true);
          call('admin.notice', { title: title, body: body, link: link, audience: aud, codes: codes, mail: mail }).then(function (j) { toast('공지를 게시했습니다 · 대상 ' + j.targets + '명' + (mail ? ' · 메일 ' + j.queued + '통 대기열' : ''), 'ok'); loadAdmin(true); }, function (e2) { busy(b, false); er.textContent = e2.message; er.classList.add('is-on'); });
        });
      });
    }
    var sf = $('adSettings'); if (sf) sf.addEventListener('submit', function (e) {
      e.preventDefault(); var set = {}, er = $('sErr'); er.classList.remove('is-on');
      Array.prototype.forEach.call(sf.querySelectorAll('input[name]'), function (i) { var v = Number(i.value); if (!isFinite(v)) return; if (v !== Number(S.admin.settings[i.name])) set[i.name] = v; });
      if (!Object.keys(set).length) { toast('바뀐 값이 없습니다'); return; }
      var b = sf.querySelector('button[type="submit"]'); busy(b, true);
      call('admin.settings', { set: set }).then(function () { toast('설정을 저장했습니다', 'ok'); loadAdmin(true); }, function (e2) { busy(b, false); er.textContent = e2.message; er.classList.add('is-on'); });
    });
  }
  /* 1.4.6 지급 완료 관리(사용자 2026.09.30 '이게 관리가 편해야 돼') */
  var payRefreshT = null;
  function payLater() { if (payRefreshT) clearTimeout(payRefreshT); payRefreshT = setTimeout(function () { payRefreshT = null; if (!Object.keys(S.paying).length) loadAdmin(); }, 5000); }
  function payApply(id, status, paidAt) {
    var a = S.admin; if (!a || !status) return;
    a.payouts.forEach(function (p) {
      if (p.id !== id || p.status === status) return;
      var t = a.tiles || {};
      if (status === '지급완료') { t.paidN = (t.paidN || 0) + 1; if (p.status === '지급예정') { t.dueN = Math.max(0, (t.dueN || 0) - 1); t.dueSum = (t.dueSum || 0) - p.amount; } }
      else if (p.status === '지급완료') { t.paidN = Math.max(0, (t.paidN || 0) - 1); if (status === '지급예정') { t.dueN = (t.dueN || 0) + 1; t.dueSum = (t.dueSum || 0) + p.amount; } }
      p.status = status; p.paidAt = paidAt || '';
    });
  }
  function payRedraw() { var a = S.admin; if (!a) return; var w = $('adPayTbl'); if (w) w.outerHTML = payTableHTML(a); renderAdminTop(); }
  function payAll() {
    var due = (S.admin && S.admin.payouts || []).filter(function (p) { return p.status === '지급예정' && !S.paying[p.id]; });
    if (!due.length) return;
    var total = due.reduce(function (x, p) { return x + p.amount; }, 0), names = due.slice(0, 10).map(function (p) { return p.name; }).join(', ') + (due.length > 10 ? ' 외 ' + (due.length - 10) + '명' : '');
    confirmBox('지급예정 ' + due.length + '명을 모두 지급 완료로 기록할까요?', '합계 ' + won(total) + ' · ' + names + '. 송금을 모두 마친 뒤에 눌러 주세요. 위원마다 지급 완료 안내 메일이 나가고, 잘못 기록한 줄은 체크를 풀면 됩니다(아직 안 나간 메일도 취소).', '모두 지급 완료').then(function (ok) {
      if (!ok) return;
      var ids = due.map(function (p) { return p.id; }), chunks = [], doneN = 0, failN = 0;
      ids.forEach(function (x) { S.paying[x] = 1; }); payRedraw();
      for (var i = 0; i < ids.length; i += 20) chunks.push(ids.slice(i, i + 20));
      (function next(k) {
        if (k >= chunks.length) { refreshing(false); toast('지급 완료 ' + doneN + '명 기록' + (failN ? ' · ' + failN + '명은 기록하지 못했습니다(그 줄만 다시 체크해 주세요)' : ' · 위원에게 안내 메일이 나갑니다'), failN ? 'warn' : 'ok'); loadAdmin(true); return; }
        refreshing(true, '지급 완료 기록 중 ' + doneN + '/' + ids.length);
        call('admin.paid', { ids: chunks[k] }).then(function (j) {
          (j.results || []).forEach(function (r) { payApply(r.id, r.status, r.paidAt); if (r.status === '지급완료') doneN++; });
          failN += (j.failed || []).length; chunks[k].forEach(function (x) { delete S.paying[x]; }); payRedraw(); next(k + 1);
        }, function (er) { chunks[k].forEach(function (x) { delete S.paying[x]; }); failN += chunks[k].length; payRedraw(); toast(er.message, 'danger'); next(k + 1); });
      })(0);
    });
  }
  function onAdminChange(e) {
    var cb = e.target;
    if (cb.id === 'adRankAll') { S.rank.all = cb.checked; $('adTab').innerHTML = adminTabHTML(); bindAdminForms(); return; }
    if (cb.id === 'adTaxMonth') { S.tax.month = String(cb.value || '').trim(); return; }
    if (!cb.hasAttribute || !cb.hasAttribute('data-paid')) return;
    var id = cb.getAttribute('data-paid'), undo = !cb.checked;
    S.paying[id] = 1; payRedraw();
    call('admin.paid', { id: id, undo: undo }).then(function (j) {
      delete S.paying[id]; payApply(id, j.status, j.paidAt); payRedraw(); payLater();
      toast(undo ? '지급 완료를 취소했습니다' + (j.mailCanceled ? ' · 아직 안 나간 안내 메일도 취소했습니다' : '') : '지급 완료로 기록했습니다 · 위원에게 안내 메일이 나갑니다', 'ok');
    }, function (er) { delete S.paying[id]; payRedraw(); toast(er.message, 'danger'); });
  }
  function onAdminClick(e) {
    var b = e.target.closest('button,a,tr'); if (!b) return;
    if (b.tagName === 'A') return;
    if (b.hasAttribute('data-copy')) { e.preventDefault(); copyText(b.getAttribute('data-copy'), b); return; }
    if (b.hasAttribute('data-tab')) { S.tab = b.getAttribute('data-tab'); store(KEY_ADMIN_TAB, S.tab, true); renderAdmin(); return; }
    if (b.hasAttribute('data-member')) { openMember(b.getAttribute('data-member')); return; }
    if (b.hasAttribute('data-sort')) { var sk = b.getAttribute('data-sort'); if (S.rank.key === sk) S.rank.dir = -S.rank.dir; else { S.rank.key = sk; S.rank.dir = 1; } var tb = $('adTab'); tb.innerHTML = adminTabHTML(); bindAdminForms(); var tbl = tb.querySelector('.ad-ranktbl'); if (tbl) tbl.scrollIntoView({ block: 'nearest' }); return; }
    if (b.hasAttribute('data-st')) { S.roster.st = b.getAttribute('data-st'); $('adTab').innerHTML = rosterTabHTML(S.admin); bindAdminForms(); return; }
    if (b.hasAttribute('data-hide')) { var id = b.getAttribute('data-hide'); confirmBox('공지를 내릴까요?', '라운지 공지 칸에서 사라집니다(이미 보낸 메일은 그대로).', '내리기').then(function (ok) { if (ok) call('admin.noticeHide', { id: id }).then(function () { toast('공지를 내렸습니다', 'ok'); loadAdmin(true); }, function (er) { toast(er.message, 'danger'); }); }); return; }
    if (b.tagName === 'TR' && b.hasAttribute('data-code')) { if (e.target.closest('button,input,label,a')) return; openMember(b.getAttribute('data-code')); return; }
    var act = b.getAttribute('data-act'); if (!act) return;
    if (act === 'taxload') { loadTax(b); return; }
    if (act === 'payall') { payAll(); return; }
    if (act === 'taxcsv') { taxCSV(); return; }
    if (act === 'mailschedule') { scheduleMailResume(); return; }
    if (act === 'mailresume' || act === 'mailpause') {
      var pause = act === 'mailpause';
      confirmBox(pause ? '위원 메일 발송을 잠시 멈출까요?' : '위원 메일 발송을 시작할까요?', pause ? '대기열의 위촉 · 안내 · 리마인드 · 공지 메일을 보내지 않습니다(인증번호 · 결제 · 정산 알림 · 위원장 알림 메일은 계속 바로 나감). 다시 시작할 때까지 대기열에 쌓입니다.' : '대기열의 메일을 10분마다 조금씩, 하루 ' + S.admin.settings.MAIL_DAILY_LIMIT + '통까지 보냅니다. 처음이라면 사이트에 라운지가 열렸는지 먼저 확인하세요.', pause ? '멈춤' : '시작').then(function (ok) {
        if (!ok) return; call('admin.mailResume', { pause: pause }).then(function (j) { toast(j.result || '처리했습니다', 'ok'); loadAdmin(true); }, function (er) { toast(er.message, 'danger'); });
      });
      return;
    }
    var map = { settle: ['admin.settle', '정산표를 지금 만들까요?', '정산 요일 0시(수요일 24시) 전에 결제된 확정 실적 중 아직 정산표에 없는 것을 위원별 미지급 정산표에 합칩니다(지급 완료된 줄은 그대로). 목요일 0시에 자동으로 됩니다.'], poll: ['admin.poll', '아임웹 주문을 지금 확인할까요?', '최근 주문에서 위원 쿠폰이 쓰인 결제를 실적으로 기록하고(결제 즉시 확정), 환불된 건을 확인합니다.'], mailq: ['admin.mailQueue', '대기 메일을 지금 보낼까요?', '하루 한도 안에서 우선순위 순으로 보냅니다.'], sync: ['admin.sync', '파트너 시트에서 위원을 가져올까요?', '위원등록_응답 탭의 새 코드를 들여오고 환영 메일을 대기열에 넣습니다. 매시간 자동으로도 됩니다.'] };
    if (map[act]) { confirmBox(map[act][1], map[act][2], '실행').then(function (ok) { if (!ok) return; busy(b, true); call(map[act][0]).then(function (j) { busy(b, false); var r = j.result || j; toast(typeof r === 'string' ? r : (r.added ? '새 위원 ' + r.added.length + '명' : r.created != null ? '정산 ' + r.created + '건' : '완료'), 'ok'); loadAdmin(true); }, function (er) { busy(b, false); toast(er.message, 'danger'); }); }); }
  }
  function openMember(code) {
    var m = modal('위원 상세', code, '<p class="lg-muted">불러오는 중…</p>');
    m.onclick = function (e) { if (e.target === m || e.target.closest('[data-act="close"]')) closeModal(); };
    call('admin.member', { code: code }).then(function (j) { renderMember(j); }, function (er) { closeModal(); toast(er.message, 'danger'); });
  }
  function renderMember(j) {
    var m = j.member, pi = j.payinfo;
    var rrnMasked = pi ? String(pi.rrn).slice(0, 6) + '-' + String(pi.rrn).charAt(6) + '******' : '';
    var credits = j.credits.slice(0, 20).map(function (c) { return '<div>' + esc(String(c.at).slice(0, 10)) + ' · ' + esc(c.status) + (c.pay ? ' · ' + won(c.pay) : '') + (c.payStatus ? ' · ' + esc(c.payStatus) : '') + (c.self === 'Y' ? ' · 본인' : '') + (c.note ? ' · ' + esc(c.note) : '') + (c.status === '확정' && c.payStatus !== '지급완료' ? ' <button type="button" class="lg-link" data-cancel="' + esc(c.id) + '">취소</button>' : c.status === '대기' ? ' <button type="button" class="lg-link" data-cancel="' + esc(c.id) + '">취소</button>' : '') + '</div>'; }).join('');
    var logs = j.logs.slice(0, 30).map(function (l) { return '<div>' + esc(l.at) + ' · ' + esc(l.kind) + (l.path ? ' · ' + esc(mailKind(String(l.path)).slice(0, 60)) : '') + (l.detail ? ' · ' + esc(l.detail) : '') + '</div>'; }).join('');
    var mails = j.mails.slice(0, 15).map(function (x) { return '<div>' + esc(x.at) + ' · ' + esc(mailKind(x.kind)) + ' · ' + esc(x.subject) + ' · ' + esc(x.status) + '</div>'; }).join('');
    var body = '<div class="ad-detail"><dl><dt>성명 · 코드</dt><dd><b>' + esc(m.name) + '</b> · ' + esc(m.code) + ' ' + badgeChip(j.member.badge || tierBadgeOf(j.member.tier)) + '</dd><dt>상태</dt><dd>' + esc(m.status) + (m.changed ? ' (' + esc(m.changed) + ')' : '') + (m.ended ? ' · 종료 ' + esc(m.ended) : '') + '</dd><dt>이메일</dt><dd>' + esc(m.email || '-') + '</dd><dt>휴대전화</dt><dd>' + esc(m.phone || '-') + '</dd><dt>위촉일</dt><dd>' + esc(m.since) + '</dd><dt>마지막 활동</dt><dd>' + esc(m.lastSignal || '-') + ' ' + esc(m.lastKind || '') + '</dd><dt>크레딧</dt><dd>확정 ' + m.credits + ' · 대기 ' + m.pending + ' · 취소 ' + m.canceled + ' · 누적 지급 ' + won(m.paid) + '</dd><dt>라운지</dt><dd>' + (m.firstLogin ? '첫 로그인 ' + esc(m.firstLogin) : '첫 로그인 전') + '</dd><dt>정산 정보</dt><dd>' + (pi ? esc(pi.bank) + ' ' + esc(pi.account) + ' (' + esc(pi.holder) + ')<br><span id="adRrn">' + esc(rrnMasked) + '</span> <button type="button" class="lg-link" data-rrn="' + esc(pi.rrn) + '">전체 보기</button><br><small class="lg-muted">동의 ' + esc(pi.consentAt) + '</small>' : '미등록') + '</dd><dt>메모</dt><dd><input class="lg-input" id="adMemo" value="' + esc(m.memo || '') + '" maxlength="300" style="padding:7px 10px;font-size:13.5px"></dd></dl>' +
      '<div class="ad-actions">' + (m.status !== '종료' && m.email ? '<button type="button" class="btn btn-ghost ad-cheer" data-mact="cheer" title="부담 없는 응원과 바로 쓸 수 있는 확산 팁을 보냅니다(미리 보기 뒤 발송)">' + ic('send') + '응원 메일</button>' : '') + '<button type="button" class="btn btn-ghost" data-mact="memo">메모 저장</button><button type="button" class="btn btn-ghost" data-mact="credit_add">크레딧 +1 (수동)</button>' + (m.status === '활동' || m.status === '휴면예정' ? '<button type="button" class="btn btn-ghost" data-mact="dormant">휴면 처리</button>' : '') + (m.status !== '활동' ? '<button type="button" class="btn btn-ghost" data-mact="restore">활동으로 복귀</button>' : '') + (m.status !== '종료' ? '<button type="button" class="btn btn-ghost" data-mact="end" style="color:#991B12;border-color:#EEC3BF">위촉 종료</button>' : '') + '<button type="button" class="btn btn-ghost" data-mact="resend_welcome">위촉 메일 다시</button><button type="button" class="btn btn-ghost" data-mact="reset_pw">비밀번호 초기화</button></div>' +
      '<h3 style="font-size:14px;margin:16px 0 4px">실적 ' + j.credits.length + '건</h3><div class="ad-log">' + (credits || '<div class="lg-muted">없음</div>') + '</div>' +
      '<h3 style="font-size:14px;margin:14px 0 4px">활동 기록</h3><div class="ad-log">' + (logs || '<div class="lg-muted">없음</div>') + '</div>' +
      '<h3 style="font-size:14px;margin:14px 0 4px">보낸 메일</h3><div class="ad-log">' + (mails || '<div class="lg-muted">없음</div>') + '</div></div>';
    var md = modal(m.name + ' 위원', m.code, body, '<button type="button" class="btn btn-ghost btn-sm" data-act="close">닫기</button>');
    md.onclick = function (e) {
      if (e.target === md || e.target.closest('[data-act="close"]')) { closeModal(); return; }
      var b = e.target.closest('button'); if (!b) return;
      if (b.hasAttribute('data-rrn')) { $('adRrn').textContent = b.getAttribute('data-rrn').replace(/(\d{6})(\d{7})/, '$1-$2'); b.remove(); return; }
      if (b.hasAttribute('data-cancel')) { var id = b.getAttribute('data-cancel'); confirmBox('이 실적을 취소할까요?', '확정 실적이면 크레딧이 1 줄고 지급 대상에서 빠집니다.', '취소 처리', true).then(function (ok) { if (ok) memberAct(m.code, 'credit_cancel', { id: id }); }); return; }
      var act = b.getAttribute('data-mact'); if (!act) return;
      var memo = $('adMemo').value.trim();
      if (act === 'memo') { memberAct(m.code, 'memo', { memo: memo }); return; }
      if (act === 'cheer') { openCheer(m); return; }
      var ask = { credit_add: ['크레딧을 1 더할까요?', '수동 실적(확정)으로 기록되고 다음 정산에 들어갑니다. 메모 칸의 내용이 사유로 남습니다.'], dormant: ['휴면 처리할까요?', '명단에서 숨겨지고 위원이 로그인하면 다시 활동으로 돌아옵니다.'], restore: ['활동으로 복귀시킬까요?', '게이지가 100%로 채워지고 명단에 다시 보입니다.'], end: ['위촉을 종료할까요?', '명단에서 내려가고 안내 메일이 나갑니다. 아임웹 쿠폰은 삭제 대기 목록에 오릅니다.'], resend_welcome: ['위촉 안내 메일을 다시 보낼까요?', '대기열에 넣어 곧 발송합니다.'], reset_pw: ['비밀번호를 초기화할까요?', '위원이 다음 로그인 때 이메일 인증으로 다시 정하게 됩니다.'] }[act];
      confirmBox(ask[0], ask[1], '실행', act === 'end').then(function (ok) { if (ok) memberAct(m.code, act, { memo: memo, mail: act === 'end' }); });
    };
  }
  /* 1.4.3 응원 메일(사용자 2026.09.30 '저성과자 독려 메일 보내기 같은 것, 거부감 없이 적절하게'): 서버가 만든 메일을 그대로 미리 보여 주고 [보내기]를 눌러야 발송. 같은 위원 7일에 한 번 */
  function openCheer(m) {
    var md = modal('응원 메일 미리 보기', m.name + ' 위원 · ' + m.code, '<p class="lg-muted">메일을 만드는 중…</p>');
    md.onclick = function (e) { if (e.target === md || e.target.closest('[data-act="close"]')) closeModal(); };
    call('admin.memberAction', { code: m.code, act: 'cheer_preview' }).then(function (j) {
      var last = j.last ? String(j.last).slice(0, 16) : '', gap = Number(j.gapDays) || 7, wait = Number(j.waitDays) || 0;   /* 남은 날은 서버가 계산(시간대 차이 없게) */
      var body = '<div class="ad-mailmeta"><div><span>받는 사람</span><b>' + esc(j.to) + '</b></div><div><span>제목</span><b>' + esc(j.subject) + '</b></div>' + (last ? '<div><span>지난 응원 메일</span><b>' + esc(last) + '</b></div>' : '') + '</div>' +
        '<iframe class="ad-mailframe" sandbox="" title="응원 메일 미리 보기" srcdoc="' + esc('<!doctype html><meta charset="utf-8"><body style="margin:0">' + j.html + '</body>') + '"></iframe>' +
        '<p class="ad-note">위원의 실적 · 명함 · 링크 열람 · 라운지 로그인 여부에 맞춰 문장이 달라집니다. 실적 부족 · 기한 · 휴면 같은 말은 넣지 않았고, 같은 위원에게는 ' + gap + '일에 한 번만 보낼 수 있습니다. 메일 대기열이 멈춰 있어도 바로 나갑니다.</p>';
      var foot = '<button type="button" class="btn btn-ghost btn-sm" data-act="close">닫기</button>' + (wait > 0 ? '<button type="button" class="btn btn-primary btn-sm" disabled>' + wait + '일 뒤에 다시 보낼 수 있음</button>' : '<button type="button" class="btn btn-primary btn-sm" data-act="send">이 메일 보내기</button>');
      var md2 = modal('응원 메일 미리 보기', m.name + ' 위원 · ' + m.code, body, foot);
      md2.onclick = function (e) {
        if (e.target === md2 || e.target.closest('[data-act="close"]')) { closeModal(); openMember(m.code); return; }
        var b = e.target.closest('[data-act="send"]'); if (!b) return; busy(b, true);
        call('admin.memberAction', { code: m.code, act: 'cheer' }).then(function (r) { toast(r.sent ? m.name + ' 위원에게 응원 메일을 보냈습니다' : '응원 메일을 대기열에 넣었습니다(오늘 메일 한도가 적어 곧 이어서 발송)', 'ok'); closeModal(); openMember(m.code); }, function (er) { busy(b, false); toast(er.message, 'danger'); });
      };
    }, function (er) { closeModal(); toast(er.message, 'danger'); });
  }
  function memberAct(code, act, extra) {
    var p = { code: code, act: act }; if (extra) for (var k in extra) p[k] = extra[k];
    call('admin.memberAction', p).then(function () { toast('처리했습니다', 'ok'); closeModal(); loadAdmin(true).then(function () { if (act !== 'end') openMember(code); }); }, function (er) { toast(er.message, 'danger'); });
  }

  /* 1.4.5 다른 창 · 탭에 5분 넘게 있다가 돌아오면 최신 숫자를 뒤에서 받아 바꿈(사용자 2026.09.30 '새로 고침 안 해도 숫자 바뀌는 거야?').
     운영자 화면은 입력 중인 탭은 두고 위쪽 숫자만, 위원 화면은 입력 중인 칸이 있으면(정산 정보 등록 등) 건너뜀 */
  var lastLoadAt = 0, BACK_REFRESH_MS = 5 * 60000;
  function backRefresh() {
    if (document.hidden || !API || main.hidden || Date.now() - lastLoadAt < BACK_REFRESH_MS) return;
    if (ADMIN) { if (S.admin && read(KEY_ADMIN, true)) loadAdmin(); return; }
    if (S.data && read(KEY_TOKEN) && !editingIn(main) && $('lgModal').hidden) loadDash();
  }
  document.addEventListener('visibilitychange', backRefresh);
  window.addEventListener('focus', backRefresh);

  /* ---------- 시작 ---------- */
  if (!hero || !login || !main) return;
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !$('lgModal').hidden) closeModal(); });
  if (ADMIN) { try { document.title = '위원장 대시보드 | 한국AI윤리위원회'; } catch (e) { /* 무시 */ } var tab0 = read(KEY_ADMIN_TAB, true); if (ADMIN_TABS.indexOf(tab0) >= 0) S.tab = tab0; if (read(KEY_ADMIN, true) && API) loadAdmin(); else renderAdminLogin(); }
  else if (read(KEY_TOKEN) && API) loadDash();
  else renderLogin();
})();
