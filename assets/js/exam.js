/* 한국AI윤리위원회 (KAIEC) : 평가응시 시스템 (/exam/)  2026.09.16 2차 개편
   화면: 로그인(이메일·비밀번호만) → 대시보드(응시자 정보·이수 절차·과정별 평가·결과 이력·평가 안내)
         → 응시 전 확인(성명 입력·시험 안내·서약·환경 점검) → 시험 시작 확인 창 → 시험(전체 화면 레이어, 시험 시간 타이머: 기본 60분·심화 75분)
         → 제출 확인 → 결과
   진행 중인 시험은 자동으로 열지 않고, 대시보드의 [이어서 응시] → 확인 창(서버 기준 남은 시간)을 거쳐 들어갑니다.
   API: POST text/plain JSON {action: login | status | start | save | submit}, GET ?action=ping
        (이수 평가 API 계약서 + 1.1.0 추가 사항: start 요청의 name, attempt.name, Result.name)
   체험 모드: /exam/?demo=1 로만 진입 (브라우저 안 모의 API, 기록이 남지 않음)
   외부 라이브러리 없이 동작하며, 아이콘은 페이지 안 SVG 스프라이트(#exi-이름)를 씁니다. */
(function () {
  'use strict';

  var CFG = window.KAIEC_EXAM || {};
  var DEMO = window.KAIEC_EXAM_DEMO || { minutes: 5, questions: [], key: [] };
  var root = document.getElementById('examApp');
  if (!root) return;

  function $(id) { return document.getElementById(id); }
  var el = {
    head: $('exHead'), crumb: $('exCrumb'), tools: $('exHeadTools'), sys: $('exSysState'), clock: $('exClock'),
    login: $('exLogin'), view: $('exView'), boot: $('exBoot'), layer: $('exLayer'), modal: $('exModal'),
    busy: $('exBusy'), busyText: $('exBusyText'), toasts: $('exToasts'), demoBar: $('exDemoBar'),
    form: $('exLoginForm'), email: $('exEmail'), pin: $('exPin'), pinToggle: $('exPinToggle'),
    err: $('exLoginErr'), loginBtn: $('exLoginBtn'), ready: $('exReady')
  };

  /* ---------------------------------------------------------------- 1. 공통 도구 */
  var NET_MSG = '네트워크 연결을 확인한 뒤 다시 시도해 주십시오.';
  var SESSION_MSG = '로그인 시간이 지났습니다. 다시 로그인해 주세요.';
  var READY_MSG = '평가 시스템 연결 준비 중입니다. 잠시 후 다시 이용해 주십시오.';
  var KEY = {
    session: 'kaiecExamSession', demoSession: 'kaiecExamDemoSession', demoDb: 'kaiecExamDemoDb',
    backup: 'kaiecExamBackup', cur: 'kaiecExamCur', fs: 'kaiecExamFontScale'
  };
  // 2026.09.21 통합: 과정은 「AI윤리전문가 양성과정」 하나. 백엔드 1.4.x(기본과정·심화과정 표기)와도 호환
  var MAIN_COURSE = 'AI윤리전문가 양성과정';
  var COURSE_KEY = { 'AI윤리전문가 양성과정': 'main', '기본과정': 'basic', '심화과정': 'adv' };
  var KEY_COURSE = { main: 'AI윤리전문가 양성과정', basic: '기본과정', adv: '심화과정' };
  function courseKey(name) { return COURSE_KEY[name] || 'main'; }
  var FORM_LABEL = { A: '1차 A형', B: '재응시 B형' };
  // 응시 이름: 이 과정의 첫 응시(A형)는 '1차 A형', 그다음부터는 '재응시 A형/B형' (무제한 재응시, A형·B형 번갈아)
  function formName(c, form) {
    var used = c && c.results ? c.results.length : 0;
    return !used && form === 'A' ? '1차 A형' : '재응시 ' + form + '형';
  }
  function retakeRule(ex) {
    var n = ex && ex.retakes;
    if (n === 0) return '재응시 없음';
    if (n > 0) return '이수하지 못하면 재응시 ' + n + '회(추가 비용 없음)';
    return '응시 기간 안에서는 이수할 때까지 재응시(추가 비용 없음, A형·B형 번갈아 출제)';
  }
  var ROMAN = { I: 'Ⅰ', II: 'Ⅱ', III: 'Ⅲ', IV: 'Ⅳ', V: 'Ⅴ', VI: 'Ⅵ', VII: 'Ⅶ', VIII: 'Ⅷ' };
  var FS_STEPS = [0.9, 1, 1.12, 1.25, 1.4];
  var DAY = 86400000, KST = 9 * 3600000;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function ico(name, cls) {
    return '<svg class="ex-ico' + (cls ? ' ' + cls : '') + '" aria-hidden="true" focusable="false"><use href="#exi-' + name + '"></use></svg>';
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  // 시각 표시는 기기 시간대와 관계없이 한국 시각(Asia/Seoul) 기준
  function kst(ms) {
    var d = new Date(ms + KST);
    return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate(), h: d.getUTCHours(), mi: d.getUTCMinutes(), s: d.getUTCSeconds() };
  }
  function fmtDT(ms) { if (!ms) return '-'; var k = kst(ms); return k.y + '.' + pad(k.m) + '.' + pad(k.d) + ' ' + pad(k.h) + ':' + pad(k.mi); }
  function fmtClock(ms) { var k = kst(ms); return pad(k.h) + ':' + pad(k.mi) + ':' + pad(k.s); }
  function fmtDay(ms) { var k = kst(ms); return k.y + '.' + pad(k.m) + '.' + pad(k.d); }
  function ymd(ms) { var k = kst(ms); return k.y + '-' + pad(k.m) + '-' + pad(k.d); }
  function dotDate(s) { return String(s || '-').replace(/-/g, '.'); }
  // 서버 안내문 속 날짜(YYYY-MM-DD)를 화면 표기(YYYY.MM.DD)로
  function dotDates(s) { return String(s == null ? '' : s).replace(/(\d{4})-(\d{2})-(\d{2})/g, '$1.$2.$3'); }
  function dayStart(s) { var p = String(s).split('-'); return Date.UTC(+p[0], +p[1] - 1, +p[2]) - KST; }
  function fmtMS(sec) { return pad(Math.floor(sec / 60)) + ':' + pad(sec % 60); }
  // 남은 시간은 올림, 경과 시간은 내림: 두 값의 합이 늘 시험 시간과 같습니다 (60:00 = 59:59 + 00:01)
  function fmtLeft(ms) { return isFinite(ms) ? fmtMS(Math.max(0, Math.ceil(ms / 1000))) : '--:--'; }
  function fmtSpent(ms) { return isFinite(ms) ? fmtMS(Math.max(0, Math.floor(ms / 1000))) : '--:--'; }
  function leftText(ms) {
    var s = Math.round(ms / 1000), m = Math.floor(s / 60);
    return m ? m + '분' + (s % 60 ? ' ' + (s % 60) + '초' : '') : s + '초';
  }
  function fmtNum(x) { x = +x || 0; return String(Math.round(x * 10) / 10); }
  function circ(v) { return String.fromCharCode(9311 + v); }   // 1 → ①
  function dday(n) { n = +n || 0; return n > 0 ? 'D-' + n : 'D-DAY'; }
  function maskEmail(e) {
    e = String(e || '');
    var at = e.indexOf('@');
    if (at < 1) return e;
    var id = e.slice(0, at);
    return id.slice(0, id.length > 3 ? 2 : 1) + '***' + e.slice(at);
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function copy(o) { return JSON.parse(JSON.stringify(o)); }
  function courseCfg(name) { var cs = CFG.courses || {}; return cs[name] || cs[MAIN_COURSE] || {}; }

  // 응시자 성명: 백엔드 cleanName_ 과 같은 규칙 (앞뒤 공백 제거, 연속 공백은 하나로, 2~30자,
  // 한글·영문(악센트 포함)·띄어쓰기·가운뎃점·마침표·하이픈·작은따옴표, 첫 글자는 한글·영문, 끝 글자는 한글·영문·마침표)
  var NAME_RE = /^[가-힣A-Za-zÀ-ɏ][가-힣A-Za-zÀ-ɏ .·'\-]*[가-힣A-Za-zÀ-ɏ.]$/;
  var NAME_CHARS = /^[가-힣A-Za-zÀ-ɏ .·'\-]*$/;
  var NAME_FIRST = /^[가-힣A-Za-zÀ-ɏ]/;
  var NAME_MSG = '성명을 정확히 입력해 주십시오(한글 또는 영문 2~30자, 숫자와 기호 제외).';
  function cleanName(v) {
    var s = String(v == null ? '' : v).replace(/^\s+|\s+$/g, '').replace(/\s+/g, ' ');
    if (s.length < 2 || s.length > 30 || !NAME_RE.test(s)) return '';
    return s;
  }
  // 입력 중 검사. hard: 글자를 더 입력해도 맞출 수 없는 오류(허용하지 않는 글자, 30자 초과, 첫 글자)라 바로 표시
  function nameState(raw) {
    var t = String(raw == null ? '' : raw).replace(/\s+/g, ' ').replace(/^ | $/g, '');
    if (!t) return { ok: false, empty: true, hard: false, value: '' };
    var v = cleanName(t);
    if (v) return { ok: true, empty: false, hard: false, value: v };
    return { ok: false, empty: false, hard: !NAME_CHARS.test(t) || t.length > 30 || !NAME_FIRST.test(t), value: t };
  }

  // 저장소: 사생활 보호 모드 등으로 막히면 메모리에만 보관
  var MEM = {};
  function area(local) { return local ? window.localStorage : window.sessionStorage; }
  function sget(k, local) {
    try { var v = area(local).getItem(k); if (v != null) return JSON.parse(v); } catch (e) { /* 저장소 사용 불가 */ }
    return MEM[k] == null ? null : JSON.parse(MEM[k]);
  }
  function sset(k, v, local) {
    MEM[k] = JSON.stringify(v);
    try { area(local).setItem(k, MEM[k]); } catch (e) { /* 메모리 보관 */ }
  }
  function sdel(k, local) {
    delete MEM[k];
    try { area(local).removeItem(k); } catch (e) { /* 무시 */ }
  }

  /* ---------------------------------------------------------------- 2. 상태·서버 시각 */
  // live: 진행 중인 응시의 남은 시간(대시보드 표시용, start 응답으로 확인), nameDraft: 응시 전 확인에서 입력 중인 성명
  var S = { demo: false, session: null, data: null, loadedAt: 0, offset: 0, view: '', exam: null,
            live: {}, nameDraft: null, viewTimer: null, lastPing: 0 };
  var E = null;   // 진행 중인 응시

  function now() { return Date.now() + S.offset; }
  function syncClock(serverNow, t0) {
    if (typeof serverNow !== 'number' || !isFinite(serverNow)) return;
    var t1 = Date.now();
    S.offset = serverNow - (t0 ? (t0 + t1) / 2 : t1);
  }
  function setData(j) {
    S.data = j;
    S.loadedAt = now();
  }

  /* ---------------------------------------------------------------- 3. API */
  function apiError(code, message, result) {
    var e = new Error(dotDates(message) || NET_MSG);
    e.code = code;
    if (result) e.result = result;
    return e;
  }

  function withTimeout(ms) {
    var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, ms);
    return { signal: ctrl ? ctrl.signal : undefined, done: function () { clearTimeout(timer); } };
  }

  function httpPost(payload) {
    var t = withTimeout(20000), t0 = Date.now();
    return fetch(CFG.api, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(payload),
      redirect: 'follow',
      cache: 'no-store',
      signal: t.signal
    }).then(function (res) {
      return res.text().then(function (txt) {
        var j = null;
        try { j = JSON.parse(txt); } catch (e) { j = null; }
        if (!j || typeof j !== 'object') {
          throw apiError(res.ok ? 'SERVER' : 'NETWORK', res.ok ? '평가 서버의 응답을 읽지 못했습니다. 잠시 후 다시 시도해 주십시오.' : NET_MSG);
        }
        return j;
      });
    }, function () {
      throw apiError('NETWORK', NET_MSG);
    }).then(function (j) {
      t.done();
      syncClock(j.serverNow != null ? j.serverNow : (j.attempt && j.attempt.serverNow), t0);
      return j;
    }, function (e) {
      t.done();
      throw (e && e.code) ? e : apiError('NETWORK', NET_MSG);
    });
  }

  function call(action, data, opt) {
    opt = opt || {};
    var payload = { action: action };
    if (action !== 'login' && S.session) payload.token = S.session.token;
    if (data) {
      for (var k in data) if (Object.prototype.hasOwnProperty.call(data, k)) payload[k] = data[k];
    }
    var req;
    if (S.demo) req = Demo.request(payload);
    else if (!CFG.api) req = Promise.reject(apiError('SERVER', READY_MSG));
    else req = httpPost(payload);
    return req.then(function (j) {
      if (j && j.ok === true) return j;
      throw apiError((j && j.code) || 'SERVER', (j && j.message) || '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주십시오.', j && j.result);
    }).catch(function (e) {
      if (!e || !e.code) e = apiError('SERVER', '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주십시오.');
      if (e.code === 'BUSY' && !opt.retried) {   // 동시 요청 잠금: 한 번만 자동 재시도
        return wait(1500).then(function () { return call(action, data, { retried: true }); });
      }
      if (e.code === 'SESSION' && action !== 'login') sessionExpired(e.message);
      throw e;
    });
  }

  function ping() {
    if (S.demo) return Demo.ping();
    if (!CFG.api) return Promise.reject(apiError('SERVER', READY_MSG));
    var t = withTimeout(10000), t0 = Date.now();
    var url = CFG.api + (CFG.api.indexOf('?') < 0 ? '?' : '&') + 'action=ping&t=' + t0;
    return fetch(url, { method: 'GET', redirect: 'follow', cache: 'no-store', signal: t.signal })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        t.done();
        if (!j || !j.ok) throw apiError('SERVER', '평가 서버 상태를 확인하지 못했습니다.');
        syncClock(j.serverNow, t0);
        j.latency = Date.now() - t0;
        return j;
      }, function (e) {
        t.done();
        throw (e && e.code) ? e : apiError('NETWORK', NET_MSG);
      });
  }

  /* ---------------------------------------------------------------- 4. 체험 모드 모의 서버 (백엔드 1.2.0과 같은 응답 형식: 성명 입력, 무제한 재응시) */
  var Demo = (function () {
    var PASS = 70;
    var MSG = {
      pass: '이수 기준을 충족했습니다. 실제 평가에서는 위원회 확인 후 7일 이내에 「AI윤리전문가 이수증」을 이메일(PDF)로 보내 드립니다.',
      fail: '이번 평가는 이수 기준에 미치지 못했습니다. 재응시({form}형)가 열렸습니다. 응시 기간 안에서는 이수할 때까지 추가 비용 없이 다시 응시할 수 있습니다.'
    };
    function rand() { return Math.random().toString(36).slice(2, 10).toUpperCase(); }
    function load() { return sget(KEY.demoDb); }
    function save(db) { sset(KEY.demoDb, db); }
    function total() { return DEMO.questions.length || 1; }
    function point() { return 100 / total(); }
    function fresh() {
      var start = dayStart(ymd(Date.now())) - 3 * DAY;   // 체험 계정의 결제일: 사흘 전
      return {
        token: 'DEMO' + rand() + rand(), name: '체험 응시자', email: 'demo@kaiec.kr',
        start: ymd(start), end: ymd(start + (CFG.windowDays || 30) * DAY),
        forms: { A: '응시 가능', B: '대기' }, attempt: null, results: []
      };
    }
    function courseState(db) {
      var t = Date.now(), endMs = dayStart(db.end) + DAY - 1000, open = t <= endMs;
      var completed = db.forms.A === '이수' || db.forms.B === '이수';
      var next;
      var used = db.results.length;
      var nameOf = function (f) { return !used && f === 'A' ? '1차 A형' : '재응시 ' + f + '형'; };
      if (db.attempt) next = { action: 'resume', form: db.attempt.form, note: nameOf(db.attempt.form) + ' 평가가 진행 중입니다. 남은 시간 안에 이어서 응시해 주십시오.' };
      else if (completed) next = { action: 'none', form: null, note: '이수 기준을 충족했습니다. 실제 평가에서는 위원회 확인 후 이수증이 발급됩니다.' };
      else if (!open) next = { action: 'none', form: null, note: '응시 기간이 끝났습니다.' };
      else if (db.forms.A === '응시 가능' && !used) next = { action: 'start', form: 'A', note: '1차 A형 평가를 시작할 수 있습니다. 체험 모드는 예시 ' + total() + '문항, 시험 시간 ' + DEMO.minutes + '분입니다.' };
      else if (db.forms.A === '응시 가능' || db.forms.B === '응시 가능') {
        var f = db.forms.A === '응시 가능' ? 'A' : 'B';
        next = { action: 'start', form: f, note: '재응시 ' + f + '형 평가를 시작할 수 있습니다. 응시 기간 안에서는 이수할 때까지 다시 응시할 수 있습니다.' };
      }
      else next = { action: 'none', form: null, note: '지금 응시할 수 있는 평가지가 없습니다.' };
      return {
        course: MAIN_COURSE,
        exam: { total: total(), minutes: DEMO.minutes, point: point(), passScore: PASS, passCount: Math.ceil(PASS / point() - 1e-9), retakes: -1 },
        window: { start: db.start, end: db.end, daysLeft: Math.max(0, Math.round((dayStart(db.end) - dayStart(ymd(t))) / DAY)), state: open ? 'open' : 'expired' },
        forms: [{ form: 'A', label: 'A형', status: db.forms.A }, { form: 'B', label: 'B형', status: db.forms.B }],
        next: next, completed: completed, results: db.results.slice().reverse()
      };
    }
    function publicAttempt(a) {
      return {
        id: a.id, name: a.name || '', course: MAIN_COURSE, form: a.form, label: a.label || FORM_LABEL[a.form], startedAt: a.startedAt, deadline: a.deadline,
        serverNow: Date.now(), minutes: DEMO.minutes, total: total(), point: point(), passScore: PASS
      };
    }
    function grade(db, type) {
      var a = db.attempt, correct = 0, answered = 0, areas = [], map = {};
      DEMO.questions.forEach(function (q, i) {
        var v = +a.answers[String(q.n)] || 0, hit = v === DEMO.key[i];
        if (v) answered++;
        if (hit) correct++;
        if (!map[q.area]) { map[q.area] = { code: q.area, name: q.areaName, correct: 0, total: 0 }; areas.push(map[q.area]); }
        map[q.area].total++;
        if (hit) map[q.area].correct++;
      });
      var order = { I: 1, II: 2, III: 3, IV: 4, V: 5 };
      areas.sort(function (p, q) { return (order[p.code] || 9) - (order[q.code] || 9); });
      var t = Date.now(), score = Math.round(correct * point() * 10) / 10, passed = score >= PASS;
      var retake = { available: false, form: null }, msg;
      if (passed) { db.forms[a.form] = '이수'; msg = MSG.pass; }
      else {
        var other = a.form === 'A' ? 'B' : 'A';
        db.forms[a.form] = '미이수'; db.forms[other] = '응시 가능';
        retake = { available: true, form: other }; msg = MSG.fail.replace('{form}', other);
      }
      var r = {
        attemptId: a.id, name: a.name || '', course: MAIN_COURSE, form: a.form, label: a.label || FORM_LABEL[a.form], submittedAt: t, startedAt: a.startedAt,
        durationMin: Math.max(1, Math.round((Math.min(t, a.deadline) - a.startedAt) / 60000)),
        total: total(), answered: answered, correct: correct, score: score, passScore: PASS, passed: passed,
        areas: areas, submitType: type, retake: retake, message: msg
      };
      db.results.push(r);
      db.attempt = null;
      return r;
    }
    function findResult(db, id) {
      for (var i = 0; i < db.results.length; i++) if (db.results[i].attemptId === id) return db.results[i];
      return null;
    }
    function ok(o) { o.ok = true; if (o.serverNow == null) o.serverNow = Date.now(); return o; }
    function fail(code, message, result) { var o = { ok: false, code: code, message: message }; if (result) o.result = result; return o; }
    function cleanAnswers(src) {
      var out = {};
      if (src) for (var k in src) { var v = +src[k]; if (v >= 1 && v <= 4) out[String(+k)] = v; }
      return out;
    }
    function handle(p) {
      var db = load(), a, r, form, t, nm;
      if (p.action === 'login') {
        db = fresh();
        save(db);
        return ok({ token: db.token, name: db.name, email: db.email, courses: [courseState(db)] });
      }
      if (!db || !p.token || p.token !== db.token) return fail('SESSION', SESSION_MSG);
      var expired = false;
      if (db.attempt && Date.now() > db.attempt.deadline + 60000) {   // 마감 + 유예 60초가 지난 응시는 마지막 저장본으로 자동 제출
        grade(db, '시간 종료');
        expired = true;
        save(db);
      }
      a = db.attempt;
      switch (p.action) {
        case 'status':
          save(db);
          return ok({ name: db.name, email: db.email, courses: [courseState(db)] });
        case 'start':
          // 백엔드와 같은 순서: 진행 중이면 이어서(성명·서약 불필요) → 평가지 → 서약 → 성명
          if (a) return ok({ attempt: publicAttempt(a), questions: DEMO.questions, answers: a.answers, flags: a.flags, blurCount: a.blurCount, resumed: true });
          form = db.forms.A === '응시 가능' ? 'A' : (db.forms.B === '응시 가능' ? 'B' : null);
          if (!form) return fail('NOT_AVAILABLE', '지금 응시할 수 있는 평가지가 없습니다.');
          if (p.agree !== true) return fail('PLEDGE', '응시 전 확인 사항에 모두 동의해 주십시오.');
          nm = cleanName(p.name);
          if (!nm) return fail('NAME', NAME_MSG);
          if (!db.name) db.name = nm;
          t = Math.floor(Date.now() / 1000) * 1000;
          a = db.attempt = { id: 'DEMO-' + form + '-' + rand(), name: nm, form: form, label: !db.results.length && form === 'A' ? '1차 A형' : '재응시 ' + form + '형',
            startedAt: t, deadline: t + DEMO.minutes * 60000, answers: {}, flags: [], blurCount: 0 };
          db.forms[form] = '응시 중';
          save(db);
          return ok({ attempt: publicAttempt(a), questions: DEMO.questions, answers: {}, flags: [], blurCount: 0, resumed: false });
        case 'save':
        case 'submit':
          if (!a || a.id !== p.attemptId) {
            r = findResult(db, p.attemptId);
            if (!r) return fail('NOT_FOUND', '응시 정보를 찾을 수 없습니다. 대시보드에서 다시 확인해 주십시오.');
            if (expired && p.action === 'submit') return ok({ result: r });
            return fail('FINISHED', expired ? '시험 시간이 끝나 답안이 제출되었습니다.' : '이미 제출된 평가입니다.', r);
          }
          if (p.action === 'save') {
            a.answers = cleanAnswers(p.answers);
            a.flags = (p.flags || []).slice(0, 300);
            a.blurCount = +p.blurCount || 0;
            a.savedAt = Date.now();
            save(db);
            return ok({ savedAt: a.savedAt, deadline: a.deadline });
          }
          a.answers = cleanAnswers(p.answers);
          a.blurCount = +p.blurCount || 0;
          r = grade(db, p.reason === 'timeout' ? '시간 종료' : '직접 제출');
          save(db);
          return ok({ result: r });
      }
      return fail('SERVER', '알 수 없는 요청입니다.');
    }
    return {
      request: function (p) {
        return wait(160 + Math.random() * 240).then(function () { return copy(handle(p)); });
      },
      ping: function () {
        var t0 = Date.now();
        return wait(80 + Math.random() * 90).then(function () {
          return { ok: true, service: 'KAIEC-EXAM', version: 'demo', serverNow: Date.now(), latency: Date.now() - t0 };
        });
      },
      reset: function () { sdel(KEY.demoDb); }
    };
  })();

  /* ---------------------------------------------------------------- 5. 화면 도구 */
  var TOAST_ICON = { ok: 'check-circle-2', info: 'info', warn: 'alert-triangle', danger: 'alert-triangle' };
  function toast(msg, type, ms) {
    type = type || 'info';
    var t = document.createElement('div');
    t.className = 'ex-toast ex-toast--' + type;
    t.innerHTML = ico(TOAST_ICON[type] || 'info') + '<span>' + esc(msg) + '</span>';
    el.toasts.appendChild(t);
    while (el.toasts.children.length > 3) el.toasts.removeChild(el.toasts.firstChild);
    setTimeout(function () {
      t.classList.add('is-out');
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 260);
    }, ms || 4200);
  }
  function clearToasts() { el.toasts.innerHTML = ''; }
  function toTop() {
    try { window.scrollTo({ top: 0, left: 0, behavior: 'instant' }); } catch (e) { window.scrollTo(0, 0); }
  }
  function busy(msg) {
    if (!msg) { el.busy.hidden = true; return; }
    el.busyText.textContent = msg;
    el.busy.hidden = false;
  }
  var modalState = null;
  function openModal(html, opts) {
    closeModal();
    modalState = opts || {};
    clearToasts();
    el.modal.innerHTML = '<div class="ex-dialog' + (modalState.wide ? ' ex-dialog--wide' : '') + '" role="dialog" aria-modal="true" aria-labelledby="exDlgTitle">' + html + '</div>';
    el.modal.hidden = false;
    var f = el.modal.querySelector('[data-autofocus]') || el.modal.querySelector('button');
    if (f) f.focus();
    if (modalState.tick) {
      modalState.tick();
      modalState.timer = setInterval(modalState.tick, 500);
    }
  }
  function closeModal() {
    if (modalState && modalState.timer) clearInterval(modalState.timer);
    modalState = null;
    el.modal.hidden = true;
    el.modal.innerHTML = '';
  }
  function setBtnBusy(btn, on, text) {
    if (!btn) return;
    if (on) {
      btn._html = btn.innerHTML;
      btn.classList.add('is-busy');
      btn.disabled = true;
      btn.innerHTML = '<span class="ex-spin ex-spin--sm" aria-hidden="true"></span>' + esc(text || '처리 중');
    } else {
      if (btn._html != null) btn.innerHTML = btn._html;
      btn.classList.remove('is-busy');
      btn.disabled = false;
    }
  }
  function errBox(node, msg) {
    if (!node) return;
    if (!msg) { node.hidden = true; node.innerHTML = ''; return; }
    node.innerHTML = ico('alert-triangle') + '<span>' + esc(msg) + '</span>';
    node.hidden = false;
  }
  function setSys(state, text) {
    if (!el.sys) return;
    el.sys.setAttribute('data-state', state);
    el.sys.querySelector('b').textContent = text;
  }
  function checkSys() {
    S.lastPing = Date.now();
    if (S.demo) return setSys('demo', '체험 모드로 연결됨');
    if (!CFG.api) return setSys('ready', '연결 준비 중');
    setSys('check', '연결 상태 확인 중');
    ping().then(function () { if (!S.demo) setSys('ok', '정상 운영 중'); },
      function () { if (!S.demo) { setSys('warn', '연결 확인 필요'); S.lastPing = 0; } });
  }
  function startClock() {
    function t() {
      if (el.clock && !el.head.hidden) {
        var n = now();
        el.clock.innerHTML = '<span class="ex-clock-k">현재 시각</span> <b>' + fmtDay(n) + ' ' + fmtClock(n) + '</b> <small>KST</small>';
      }
    }
    t();
    setInterval(t, 1000);
  }
  function stopViewTimer() {
    if (S.viewTimer) { clearInterval(S.viewTimer); S.viewTimer = null; }
  }
  function hideAll() {
    stopViewTimer();
    el.boot.hidden = true;
    el.login.classList.remove('is-on');
    el.view.hidden = true;
  }
  // 로그인 뒤 화면의 얇은 페이지 머리: 빵 조각·시스템 상태·현재 시각·새로고침·로그아웃
  function showHead(opt) {
    opt = opt || {};
    el.head.hidden = false;
    var sep = '<span class="ex-crumb-sep" aria-hidden="true">›</span>';
    el.crumb.innerHTML = '<a href="/">홈</a>' + sep +
      (opt.trail ? '<a href="#dashboard" data-act="dashboard">평가응시</a>' + sep + '<span aria-current="page">' + esc(opt.trail) + '</span>'
        : '<span aria-current="page">평가응시</span>');
    var tools = '';
    if (opt.refresh) tools += '<button type="button" class="ex-btn ex-btn--secondary ex-btn--sm" data-act="refresh">' + ico('refresh-cw') + '새로고침</button>';
    if (!S.demo && S.session) tools += '<button type="button" class="ex-btn ex-btn--secondary ex-btn--sm" data-act="logout">' + ico('log-out') + '로그아웃</button>';
    el.tools.innerHTML = tools;
    el.tools.hidden = !tools;
    if (Date.now() - S.lastPing > 60000) checkSys();
    var n = now();
    el.clock.innerHTML = '<span class="ex-clock-k">현재 시각</span> <b>' + fmtDay(n) + ' ' + fmtClock(n) + '</b> <small>KST</small>';
  }
  function showBoot(msg) {
    hideAll();
    if (S.session) showHead({});
    el.boot.hidden = false;
    el.boot.lastElementChild.textContent = msg || '평가 시스템을 불러오는 중입니다';
  }
  function setView(html, name, head) {
    hideAll();
    S.view = name;
    showHead(head);
    el.view.innerHTML = html;
    el.view.hidden = false;
    el.demoBar.hidden = !S.demo;
    toTop();
  }
  function setHash(h) {
    var url = location.pathname + location.search + (h ? '#' + h : '');
    if (location.pathname + location.search + location.hash === url) return;
    try { history.replaceState(null, '', url); } catch (e) { /* 무시 */ }
  }
  function parseHash() {
    var parts = location.hash.replace(/^#/, '').split('/');
    var arg = '';
    try { arg = decodeURIComponent(parts[1] || ''); } catch (e) { arg = ''; }
    return { name: parts[0] || '', arg: arg };
  }
  function stepper(step) {
    var names = ['응시 전 확인', '시험', '결과'];
    return '<ol class="ex-stepper" aria-label="응시 단계">' + names.map(function (n, i) {
      var k = i + 1, cls = k < step ? 'is-done' : (k === step ? 'is-on' : '');
      return '<li class="' + cls + '"' + (k === step ? ' aria-current="step"' : '') + '><b>' + (k < step ? ico('check') : k) + '</b><span>' + n + '</span></li>';
    }).join('') + '</ol>';
  }
  function panel(title, body, opt) {
    opt = opt || {};
    return '<section class="ex-panel' + (opt.cls ? ' ' + opt.cls : '') + '"' + (opt.attrs || '') + '>' +
      '<header class="ex-panel-head"><h2 class="ex-h">' + title + '</h2>' + (opt.aside || '') + '</header>' + body + '</section>';
  }
  // 공문서형 표: [머리 칸, 내용(HTML), 내용 칸 클래스]
  function kv(rows, cls) {
    return '<dl class="ex-kv' + (cls ? ' ' + cls : '') + '">' + rows.map(function (r) {
      return '<dt>' + r[0] + '</dt><dd' + (r[2] ? ' class="' + r[2] + '"' : '') + '>' + r[1] + '</dd>';
    }).join('') + '</dl>';
  }
  var TONE = { '응시 가능': 'open', '대기': 'wait', '응시 중': 'progress', '이수': 'done', '미이수': 'fail', '무효': 'danger' };
  function badge(text, tone) {
    return '<span class="ex-badge ex-badge--' + (tone || TONE[text] || 'wait') + '">' + esc(text) + '</span>';
  }

  /* ---------------------------------------------------------------- 6. 로그인·세션·체험 모드 */
  function sessKey() { return S.demo ? KEY.demoSession : KEY.session; }
  function saveSession() { sset(sessKey(), S.session); }
  function clearSession() {
    sdel(sessKey());
    S.session = null;
    S.data = null;
    S.live = {};
    S.nameDraft = null;
  }

  function sessionExpired(msg) {
    if (E) stopExam(true);   // 답안은 이 기기에 남겨 두고 다시 로그인하면 이어서 응시
    closeModal();
    busy(false);
    clearSession();
    if (S.demo) Demo.reset();
    showLogin(msg || SESSION_MSG);
  }

  function exitDemoUrl() {
    S.demo = false;
    var q = location.search.replace(/([?&])demo=1(&|$)/, function (m, a, b) { return b ? a : ''; });
    if (q === '?') q = '';
    try { history.replaceState(null, '', location.pathname + q); } catch (e) { /* 무시 */ }
  }

  function showLogin(msg) {
    if (S.demo) exitDemoUrl();
    hideAll();
    S.view = 'login';
    el.head.hidden = true;
    el.demoBar.hidden = true;
    el.view.innerHTML = '';
    el.login.classList.add('is-on');
    var ready = !!CFG.api;
    el.ready.hidden = ready;
    [el.email, el.pin, el.pinToggle, el.loginBtn].forEach(function (x) { if (x) x.disabled = !ready; });
    errBox(el.err, msg || '');
    setHash('');
    toTop();
  }

  function bindLogin() {
    el.pin.addEventListener('input', function () {
      var v = el.pin.value.replace(/\D/g, '').slice(0, 4);
      if (v !== el.pin.value) el.pin.value = v;
      el.pin.classList.remove('is-invalid');
    });
    el.email.addEventListener('input', function () { el.email.classList.remove('is-invalid'); });
    el.pinToggle.addEventListener('click', function () {
      var show = el.pin.type === 'password';
      el.pin.type = show ? 'text' : 'password';
      el.pinToggle.setAttribute('aria-pressed', show ? 'true' : 'false');
      el.pinToggle.setAttribute('aria-label', show ? '비밀번호 숨기기' : '비밀번호 보기');
      el.pin.focus();
    });
    el.form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!CFG.api) return errBox(el.err, READY_MSG);
      var email = el.email.value.trim().toLowerCase(), pin = el.pin.value.replace(/\D/g, '');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        el.email.classList.add('is-invalid');
        el.email.focus();
        return errBox(el.err, '이메일(아이디)을 정확히 입력해 주십시오.');
      }
      if (pin.length !== 4) {
        el.pin.classList.add('is-invalid');
        el.pin.focus();
        return errBox(el.err, '비밀번호는 결제 때 입력하신 휴대전화 번호 뒤 4자리 숫자입니다.');
      }
      errBox(el.err, '');
      S.demo = false;
      setBtnBusy(el.loginBtn, true, '로그인 확인 중');
      call('login', { email: email, pin: pin }).then(function (j) {
        S.session = { token: j.token, name: j.name, email: j.email || email, at: Date.now() };
        saveSession();
        S.live = {};
        S.nameDraft = null;
        setData(j);
        el.pin.value = '';
        setBtnBusy(el.loginBtn, false);
        showDashboard();
        toast((j.name || '수강생') + '님, 로그인되었습니다.', 'ok');
      }, function (e) {
        setBtnBusy(el.loginBtn, false);
        errBox(el.err, e.message);
        if (e.code === 'INVALID') { el.pin.value = ''; el.pin.focus(); }
      });
    });
  }

  function enterDemo() {
    if (E) return;
    S.demo = true;
    if (!/[?&]demo=1(&|$)/.test(location.search)) {
      try {
        history.replaceState(null, '', location.pathname + (location.search ? location.search + '&' : '?') + 'demo=1' + location.hash);
      } catch (e) { /* 무시 */ }
    }
    checkSys();
    var sess = sget(KEY.demoSession);
    if (sess && sess.token) { S.session = sess; return restore(); }
    showBoot('체험 모드를 준비하고 있습니다');
    call('login', { email: 'demo@kaiec.kr', pin: '0000' }).then(function (j) {
      S.session = { token: j.token, name: j.name, email: j.email, demo: true, at: Date.now() };
      saveSession();
      setData(j);
      route(parseHash());
      toast('체험 모드입니다. 실제 응시 기록은 남지 않습니다.', 'info');
    }, function (e) { showLogin(e.message); });
  }

  function exitDemo() {
    if (E) stopExam(false);
    closeModal();
    sdel(KEY.demoSession);
    Demo.reset();
    S.session = null;
    S.data = null;
    S.live = {};
    S.nameDraft = null;
    exitDemoUrl();
    var real = sget(KEY.session);
    if (real && real.token && CFG.api) { S.session = real; checkSys(); restore(); }
    else showLogin();
    toast('체험 모드를 마쳤습니다.', 'info');
  }

  function restartDemo() {
    if (E) stopExam(false);
    sdel(KEY.demoSession);
    Demo.reset();
    S.session = null;
    S.data = null;
    S.live = {};
    S.nameDraft = null;
    enterDemo();
  }

  function logout() {
    if (E) return;
    closeModal();
    clearSession();
    sdel(KEY.cur);
    showLogin();
    toast('로그아웃되었습니다.', 'info');
  }

  function restore() {
    showBoot();
    call('status').then(function (j) {
      setData(j);
      route(parseHash());
    }, function (e) {
      if (e.code === 'SESSION') return;
      showError(e.message);
    });
  }

  function refresh() {
    return call('status').then(function (j) { setData(j); return j; });
  }

  function showError(msg) {
    setView('<section class="ex-panel ex-fail">' + ico('wifi-off') +
      '<h2 class="ex-h">평가 시스템에 연결하지 못했습니다</h2><p>' + esc(msg) + '</p>' +
      '<div class="ex-actions"><button type="button" class="ex-btn ex-btn--primary" data-act="retry">' + ico('refresh-cw') + '다시 시도</button>' +
      (S.demo ? '<button type="button" class="ex-btn ex-btn--secondary" data-act="demo-exit">체험 종료</button>' : '') +
      '</div></section>', 'error', {});
  }

  /* ---------------------------------------------------------------- 7. 경로(URL 해시) */
  function courses() { return (S.data && S.data.courses) || []; }
  function courseBy(name) {
    var list = courses();
    for (var i = 0; i < list.length; i++) if (list[i].course === name) return list[i];
    return null;
  }
  function findResult(id) {
    var list = courses();
    for (var i = 0; i < list.length; i++) {
      var rs = list[i].results || [];
      for (var k = 0; k < rs.length; k++) if (rs[k].attemptId === id) return rs[k];
    }
    return null;
  }
  // 진행 중인 시험(#exam/…)으로 새로고침해도 곧장 시험 화면을 열지 않고 대시보드의 [이어서 응시]로 들어갑니다
  function route(r) {
    if (!S.session) return showLogin();
    var c = KEY_COURSE[r.arg] ? courseBy(KEY_COURSE[r.arg]) : null;
    if (r.name === 'pledge' && c && c.next && c.next.action === 'start') return showPledge(c.course);
    if (r.name === 'result') {
      var res = findResult(r.arg);
      if (res) return showResult(res);
    }
    showDashboard();
  }

  /* ---------------------------------------------------------------- 8. 대시보드 */
  var NOTES = [
    '시험 시작을 누르면 시험 시간이 바로 흐르기 시작하며, 창을 닫아도 멈추지 않습니다.',
    '답안은 자동 저장됩니다. 연결이 끊기면 시험 시간 안에 다시 로그인해 [이어서 응시]로 계속할 수 있습니다.',
    '응시 중 다른 창이나 탭으로 이동하면 화면 이탈로 기록되어 위원회가 검토합니다.',
    '평가 문항은 한국AI윤리위원회의 저작물입니다. 촬영·복제·공유를 금합니다.'
  ];

  function isLive(c) { return !!(c && c.next && c.next.action === 'resume'); }
  function passOf(ex) { return ex.passScore || 70; }
  function passCountOf(ex) {
    var point = ex.point || (ex.total ? 100 / ex.total : 0);
    return ex.passCount || (point ? Math.ceil(passOf(ex) / point - 1e-9) : 0);
  }

  function courseStatus(c) {
    var n = c.next || {}, w = c.window || {}, rs = c.results || [];
    if (c.completed) return ['done', '이수 완료'];
    if (n.action === 'resume') return ['progress', '응시 중'];
    if (w.state === 'expired') return ['closed', '기간 만료'];
    if (w.state === 'before') return ['closed', '응시 기간 전'];
    if (n.action === 'start') return rs.length || n.form === 'B' ? ['open', '재응시 가능'] : ['open', '응시 가능'];
    if (rs.length && !rs[0].passed) return ['fail', '미이수'];
    return ['closed', '확인 중'];
  }

  function liveAlerts(list) {
    return list.filter(isLive).map(function (c) {
      var key = courseKey(c.course), f = c.next.form;
      return '<div class="ex-alert ex-alert--live" data-live-box="' + key + '">' + ico('timer') +
        '<div class="ex-alert-txt"><strong class="ex-live-title">진행 중인 시험이 있습니다</strong>' +
          '<span>' + esc(c.course) + ' · ' + esc(f ? formName(c, f) : '') + ' · 남은 시간 <b class="ex-num ex-left" data-left="' + key + '">확인 중</b></span>' +
          '<small class="ex-live-note">시험 시간은 서버 시각 기준으로 계속 흐르고 있습니다.</small></div>' +
        '<button type="button" class="ex-btn ex-btn--primary" data-act="resume" data-course="' + key + '">' + ico('rotate-ccw') + '<span class="ex-live-btn">이어서 응시</span></button></div>';
    }).join('');
  }

  function candPanel() {
    var d = S.data || {}, s = S.session || {}, list = courses();
    var name = d.name || '';
    return panel('응시자 정보', kv([
      ['성명', name ? '<b>' + esc(name) + '</b>' : '<span class="ex-muted">응시 전 확인에서 입력</span>'],
      ['아이디(이메일)', '<span class="ex-break">' + esc(d.email || s.email || '-') + '</span>'],
      ['신청 과정', list.length ? list.map(function (c) { return esc(c.course); }).join(' · ') : '-'],
      ['조회 시각', '<span class="ex-num">' + fmtDT(S.loadedAt || now()) + '</span> (KST)']
    ], 'ex-kv--4'), { cls: 'ex-cand' });
  }

  function flowPanel() {
    var list = courses();
    var done = list.length > 0 && list.every(function (c) { return c.completed; });
    var cur = done ? 5 : 4, pass = passOf(courseCfg(MAIN_COURSE));
    var FLOW = [
      ['양성과정 신청', '수강 신청·교육비 결제'],
      ['학습자료 확인', '메일로 자료 5종 수령'],
      ['자율학습', '표준교재 · 모의고사 학습'],
      ['평가응시', '온라인 이수 평가 응시'],
      ['이수 기준 충족', pass + '점 이상'],
      ['이수증 발급', '결과 확인 후 7일 이내 PDF']
    ];
    return panel('이수 절차', '<ol class="ex-steps">' + FLOW.map(function (f, i) {
      var k = i + 1, st = k < cur ? 'is-done' : (k === cur ? 'is-now' : '');
      return '<li class="' + st + '"' + (k === cur ? ' aria-current="step"' : '') + '>' +
        '<span class="ex-step-no">' + (k < cur ? ico('check') : k) + '</span>' +
        '<span class="ex-step-t">' + f[0] + '</span><span class="ex-step-d">' + f[1] + '</span>' +
        (k === cur ? '<em class="ex-step-now">현재 단계</em>' : '') + '</li>';
    }).join('') + '</ol>', { cls: 'ex-flow' });
  }

  function coursePanel(c, wide) {
    var key = courseKey(c.course), ex = c.exam || {}, w = c.window || {}, n = c.next || {}, rs = c.results || [];
    var st = courseStatus(c), t = now();
    var point = ex.point || (ex.total ? 100 / ex.total : 0);
    var startMs = w.start ? dayStart(w.start) : 0, endMs = w.end ? dayStart(w.end) + DAY : 0;
    var totalDays = startMs && endMs ? Math.round((endMs - DAY - startMs) / DAY) : (CFG.windowDays || 30);
    var pct = startMs && endMs > startMs ? Math.max(0, Math.min(100, (t - startMs) / (endMs - startMs) * 100)) : 0;
    var dd, ddCls = '', foot;
    if (w.state === 'expired') { dd = '기간 종료'; ddCls = ' is-off'; pct = 100; foot = dotDate(w.end) + '에 응시 기간이 끝났습니다'; }
    else if (w.state === 'before') { dd = '시작 전'; ddCls = ' is-off'; pct = 0; foot = dotDate(w.start) + '부터 응시할 수 있습니다'; }
    else {
      dd = dday(w.daysLeft);
      if ((+w.daysLeft || 0) <= 5) ddCls = ' is-soon';
      foot = '남은 기간 ' + (+w.daysLeft || 0) + '일 · 전체 ' + totalDays + '일 (결제일부터)';
    }
    var period = '<div class="ex-period"><span class="ex-num">' + dotDate(w.start) + ' ~ ' + dotDate(w.end) + '</span>' +
        '<span class="ex-dday' + ddCls + '">' + dd + '</span></div>' +
      '<div class="ex-bar" role="progressbar" aria-label="응시 기간 경과" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + Math.round(pct) + '">' +
        '<span style="width:' + pct.toFixed(1) + '%"></span></div>' +
      '<p class="ex-period-foot">' + foot + '</p>';
    var forms = '<ul class="ex-formlist">' + (c.forms || []).map(function (f) {
      return '<li><span>' + esc(f.label || FORM_LABEL[f.form]) + '</span>' + badge(f.status) + '</li>';
    }).join('') + '</ul>';
    // 한 과정만 있으면 넓은 4열 표(머리·내용·머리·내용), 두 과정이면 과정마다 2열 표
    var rows = [
      ['응시 기간', period],
      ['평가 구성', '<b>' + (ex.total || '-') + '문항</b> · 4지선다형 · 문항당 ' + fmtNum(point) + '점 · 100점 만점'],
      ['시험 시간', '<b>' + (ex.minutes || '-') + '분</b><span class="ex-sub-line">시험 시작을 누른 때부터 흐르며, 끝나면 답안이 자동 제출됩니다</span>'],
      ['이수 기준', '<b>' + passOf(ex) + '점 이상</b><span class="ex-sub-line">' + (ex.total || '-') + '문항 중 ' + passCountOf(ex) + '문항 이상 정답</span>'],
      ['평가지', forms, wide ? 'is-full' : '']
    ];
    var act = '';
    if (isLive(c)) {
      act += '<div class="ex-live" data-live-box="' + key + '"><span class="ex-live-k ex-live-title">' + esc(n.form ? formName(c, n.form) : '') + ' 진행 중</span>' +
        '<span class="ex-live-v">남은 시간 <b class="ex-num ex-left" data-left="' + key + '">확인 중</b></span>' +
        '<p class="ex-live-note">' + esc(dotDates(n.note)) + '</p></div>';
    } else if (n.note) {
      act += '<p class="ex-note">' + ico('info') + '<span>' + esc(dotDates(n.note)) + '</span></p>';
    } else {
      act += '<span></span>';
    }
    var btns = '';
    if (n.action === 'start') {
      btns += '<button type="button" class="ex-btn ex-btn--primary" data-act="pledge" data-course="' + key + '">' + ico('pen-line') +
        (rs.length || n.form === 'B' ? '재응시 ' + n.form + '형 응시하기' : '응시하기') + '</button>';
    } else if (isLive(c)) {
      btns += '<button type="button" class="ex-btn ex-btn--primary" data-act="resume" data-course="' + key + '">' + ico('rotate-ccw') + '<span class="ex-live-btn">이어서 응시</span></button>';
    }
    if (rs.length) {
      btns += '<button type="button" class="ex-btn ex-btn--secondary" data-act="result" data-id="' + esc(rs[0].attemptId) + '">' + ico('bar-chart-3') + '결과 보기</button>';
    }
    if (!btns && !c.completed) {
      btns = '<a class="ex-btn ex-btn--secondary" href="mailto:' + esc(CFG.email || '') + '?subject=' + encodeURIComponent('[이수 평가 문의] ' + c.course) + '">' +
        ico('mail') + '위원회에 문의하기</a>';
    }
    if (btns) act += '<div class="ex-actions">' + btns + '</div>';
    return '<section class="ex-panel ex-course' + (wide ? ' is-wide' : '') + '" data-course="' + key + '">' +
      '<header class="ex-panel-head"><h2 class="ex-h">' + esc(c.course) + ' 이수 평가</h2>' + badge(st[1], st[0]) + '</header>' +
      '<div class="ex-course-body">' + kv(rows, wide ? 'ex-kv--4' : '') + '<div class="ex-course-act">' + act + '</div></div></section>';
  }

  function upsellBox(list) {
    if (CFG.unified || list.length !== 1) return '';   // 2026.09.21 통합: 다른 과정 결제 안내 없음
    var has = list[0].course, b = courseCfg('기본과정'), a = courseCfg('심화과정'), o;
    if (has === '기본과정' && CFG.payAdv) {
      o = { t: '심화과정도 함께 준비하시나요?', d: '심화과정은 ' + (a.total || 50) + '문항 심화 범위 이수 평가이며, 이수하면 위원회 전문위원으로 등록됩니다.', b: '심화과정 결제하기', h: CFG.payAdv };
    } else if (has === '심화과정' && CFG.payBasic) {
      o = { t: '기본과정도 함께 응시하시나요?', d: '기본과정 이수 평가(' + (b.total || 40) + '문항)는 별도 과정입니다. 함께 응시하려면 기본과정을 결제해 주십시오.', b: '기본과정 결제하기', h: CFG.payBasic };
    }
    if (!o) return '';
    return '<aside class="ex-upsell">' + ico('graduation-cap') + '<div class="ex-upsell-txt"><strong>' + o.t + '</strong><span>' + o.d +
      ' 결제는 성균관컨설팅 안전결제로 진행됩니다.</span></div>' +
      '<a class="ex-btn ex-btn--secondary" href="' + esc(o.h) + '" target="_blank" rel="noopener">' + o.b + ico('external-link') + '<span class="sr-only">(새 창)</span></a></aside>';
  }

  function historyPanel() {
    var rows = [];
    courses().forEach(function (c) { (c.results || []).forEach(function (r) { rows.push(r); }); });
    rows.sort(function (a, b) { return (b.submittedAt || 0) - (a.submittedAt || 0); });
    var body = rows.length
      ? '<div class="ex-table-wrap"><table class="ex-table"><thead><tr><th scope="col">제출 일시</th><th scope="col">과정</th><th scope="col">평가지</th>' +
        '<th scope="col" class="is-num">정답 수</th><th scope="col" class="is-num">점수</th><th scope="col">결과</th><th scope="col">제출 방식</th><th scope="col">상세</th></tr></thead><tbody>' +
        rows.map(function (r) {
          return '<tr><td data-th="제출 일시" class="ex-num">' + fmtDT(r.submittedAt) + '</td>' +
            '<td data-th="과정">' + esc(r.course) + '</td>' +
            '<td data-th="평가지">' + esc(r.label || FORM_LABEL[r.form]) + '</td>' +
            '<td data-th="정답 수" class="is-num">' + r.correct + ' / ' + r.total + '</td>' +
            '<td data-th="점수" class="is-num"><b>' + fmtNum(r.score) + '</b>점</td>' +
            '<td data-th="결과">' + badge(r.passed ? '이수' : '미이수') + '</td>' +
            '<td data-th="제출 방식">' + esc(r.submitType || '-') + '</td>' +
            '<td data-th="상세"><button type="button" class="ex-link" data-act="result" data-id="' + esc(r.attemptId) + '">결과 보기</button></td></tr>';
        }).join('') + '</tbody></table></div>'
      : '<p class="ex-empty">아직 제출한 평가가 없습니다.</p>';
    return panel('응시 결과 이력', body, { cls: 'ex-history', aside: '<small class="ex-panel-note">문항별 정답은 공개하지 않습니다</small>' });
  }

  function guidePanel() {
    // 2026.09.21 통합: 이 계정에 등록된 과정 기준으로 안내합니다(과정이 둘이면 각각 표기)
    var mine = courses().map(function (c) { return c.course; });
    if (!mine.length) mine = [MAIN_COURSE];
    var comp = mine.map(function (name) {
      var c = courseCfg(name);
      return (mine.length > 1 ? esc(name) + ' ' : '') + (c.total || 40) + '문항 · ' + (c.minutes || 60) + '분';
    }).join(' / ');
    var passTxt = passOf(courseCfg(mine[0]));
    return panel('평가 안내', kv([
      ['응시 기간', '<b>결제일부터 ' + (CFG.windowDays || 30) + '일</b><span class="ex-sub-line">재응시를 포함한 모든 응시를 이 기간 안에 마칩니다.</span>'],
      ['평가 구성', '<b>' + comp + '</b><span class="ex-sub-line">4지선다형 100점 만점, 시험 시간은 [시험 시작]을 누른 때부터 흐릅니다.</span>'],
      ['이수 기준', '<b>' + passTxt + '점 이상</b><span class="ex-sub-line">이수하지 못하면 응시 기간 안에서 이수할 때까지 추가 비용 없이 재응시합니다(A형·B형 번갈아 출제). 이수증은 결과 확인 후 7일 이내 PDF로 발급합니다.</span>'],
      ['응시 환경', '<b>PC·태블릿 권장</b><span class="ex-sub-line">최신 크롬·엣지·사파리에서 응시해 주십시오. 다른 창이나 탭으로 이동하면 화면 이탈로 기록됩니다.</span>']
    ]), { cls: 'ex-guide' });
  }

  function notesPanel() {
    return panel('응시 전 유의사항', '<ul class="ex-notes">' + NOTES.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' +
      '<p class="ex-contact">' + ico('mail') + '<span>문의 <a href="mailto:' + esc(CFG.email || '') + '">' + esc(CFG.email || '') + '</a> (성명과 아이디를 함께 적어 주십시오)</span></p>',
      { cls: 'ex-notes-panel' });
  }

  function showDashboard() {
    if (!S.session) return showLogin();
    if (!S.data) return restore();
    var list = courses(), keep = {};
    list.forEach(function (c) { if (isLive(c)) keep[courseKey(c.course)] = true; });
    Object.keys(S.live).forEach(function (k) { if (!keep[k]) delete S.live[k]; });
    var wide = list.length === 1;
    var html = liveAlerts(list) + candPanel() + flowPanel() +
      (list.length
        ? '<div class="ex-courses' + (wide ? ' is-single' : '') + '">' + list.map(function (c) { return coursePanel(c, wide); }).join('') + '</div>'
        : panel('신청 과정', '<p class="ex-empty">응시할 수 있는 과정이 없습니다. ' + esc(CFG.email || '') + ' 로 문의해 주십시오.</p>')) +
      upsellBox(list) + historyPanel() +
      '<div class="ex-cols">' + guidePanel() + notesPanel() + '</div>';
    setView(html, 'dashboard', { refresh: true });
    setHash('dashboard');
    startLive(list);
  }

  // 진행 중인 응시의 남은 시간: start(진행 중이면 새 응시를 만들지 않고 그대로 돌려줌)로 확인해 1초마다 표시
  function startLive(list) {
    var keys = list.filter(isLive).map(function (c) { return courseKey(c.course); });
    if (!keys.length) return;
    keys.forEach(function (k) { if (!S.live[k]) fetchLive(k); });
    paintLive();
    S.viewTimer = setInterval(paintLive, 1000);
  }
  function rememberLive(j) {
    var a = (j && j.attempt) || {}, k = a.course ? courseKey(a.course) : '';
    if (k && a.deadline) S.live[k] = { id: a.id, deadline: a.deadline, startedAt: a.startedAt, at: Date.now() };
  }
  function fetchLive(k) {
    S.live[k] = { pending: true };   // 한 번만 조회 (새로고침을 누르면 다시 조회)
    call('start', { course: KEY_COURSE[k] }).then(function (j) {
      if (j.resumed) rememberLive(j);
      else S.live[k] = { failed: true };
      if (S.view === 'dashboard') paintLive();
    }, function (e) {
      S.live[k] = { failed: true };
      if (S.view === 'dashboard') paintLive();
      if (e.code === 'SESSION' || e.code === 'NETWORK' || e.code === 'SERVER' || e.code === 'BUSY') return;
      refresh().then(function () { if (S.view === 'dashboard') showDashboard(); }, function () { /* 무시 */ });
    });
  }
  // 시험 시간이 끝났으면 안내를 바꾸고 버튼은 [답안 제출](이 기기에 남은 답안까지 유예 시간 안에 제출)로
  var OVER_TEXT = {
    alert: ['시험 시간이 끝났습니다', '[답안 제출]을 누르면 이 기기에 남은 답안까지 바로 제출합니다. 누르지 않아도 잠시 후 저장된 답안으로 자동 제출됩니다.'],
    panel: ['시험 시간 종료', '저장된 답안으로 자동 제출됩니다. 결과는 잠시 후 이 화면에 표시됩니다.']
  };
  function markOver(k) {
    var boxes = el.view.querySelectorAll('[data-live-box="' + k + '"]');
    for (var i = 0; i < boxes.length; i++) {
      var t = OVER_TEXT[boxes[i].classList.contains('ex-alert') ? 'alert' : 'panel'];
      boxes[i].classList.add('is-over');
      boxes[i].querySelector('.ex-live-title').textContent = t[0];
      boxes[i].querySelector('.ex-live-note').textContent = t[1];
    }
    var btns = el.view.querySelectorAll('[data-act="resume"][data-course="' + k + '"] .ex-live-btn');
    for (var j = 0; j < btns.length; j++) btns[j].textContent = '답안 제출';
  }
  function paintLive() {
    if (S.view !== 'dashboard') return;
    var nodes = el.view.querySelectorAll('[data-left]'), over = {};
    for (var i = 0; i < nodes.length; i++) {
      var k = nodes[i].getAttribute('data-left'), L = S.live[k];
      if (!L || L.pending) continue;
      if (!L.deadline) { nodes[i].textContent = '--:--'; continue; }
      var left = L.deadline - now();
      nodes[i].textContent = fmtLeft(left);
      nodes[i].classList.toggle('is-over', left <= 300000);
      if (left <= 0) over[k] = true;
    }
    Object.keys(over).forEach(function (k) {
      if (!el.view.querySelector('[data-live-box="' + k + '"].is-over')) markOver(k);
    });
    // 유예 시간(60초)까지 지나면 서버가 저장된 답안으로 제출 처리하므로 상태를 다시 불러옴
    Object.keys(S.live).forEach(function (k) {
      var L = S.live[k];
      if (L.deadline && !L.reloaded && now() > L.deadline + 62000) {
        L.reloaded = true;
        refresh().then(function () { if (S.view === 'dashboard') showDashboard(); }, function () { /* 다음 새로고침 때 */ });
      }
    });
  }

  function resumeDialog(j) {
    var a = j.attempt || {}, total = a.total || (j.questions || []).length;
    var span = (a.deadline - a.startedAt) || (a.minutes || courseCfg(a.course).minutes || 60) * 60000;
    var saved = Object.keys(j.answers || {}).length;
    return '<div class="ex-dialog-head"><h2 id="exDlgTitle">진행 중인 시험이 있습니다</h2>' +
        '<p>' + esc(a.course) + ' · ' + esc(a.label || FORM_LABEL[a.form] || '') + '</p></div>' +
      '<div class="ex-dialog-body">' +
        '<div class="ex-bigtime"><span>남은 시간</span><strong class="ex-num" id="exResLeft">' + fmtLeft(Math.min(a.deadline - now(), span)) + '</strong>' +
          '<small>시험 시간 ' + Math.round(span / 60000) + '분</small></div>' +
        kv([
          ['응시자', esc(a.name || (S.data && S.data.name) || '-')],
          ['저장된 답안', saved + ' / ' + total + '문항'],
          ['시작 시각', '<span class="ex-num">' + fmtDT(a.startedAt) + '</span>'],
          ['종료 시각', '<span class="ex-num">' + fmtDT(a.deadline) + '</span>']
        ]) +
        '<p class="ex-callout">' + ico('info') + '<span>시험 시간은 서버 시각 기준으로 계속 흐르고 있습니다. 이어서 응시하면 저장된 답안을 불러와 계속 풀 수 있습니다.</span></p>' +
      '</div>' +
      '<div class="ex-dialog-foot">' +
        '<button type="button" class="ex-btn ex-btn--secondary" data-act="modal-close">취소</button>' +
        '<button type="button" class="ex-btn ex-btn--primary" data-act="resume-go" data-autofocus>' + ico('rotate-ccw') + '이어서 응시</button>' +
      '</div>';
  }

  function resumeConfirm(courseName) {
    if (E || !courseName) return;
    busy('진행 중인 시험을 확인하고 있습니다');
    call('start', { course: courseName }).then(function (j) {
      busy(false);
      if (!j.resumed) return openExam(j);
      rememberLive(j);
      var a = j.attempt || {}, span = (a.deadline - a.startedAt) || 0;
      if (a.deadline - now() <= 0) return openExam(j);   // 시간이 끝났으면 확인 창 없이 곧바로 제출(시험 화면이 열리자마자 시간 종료 제출)
      openModal(resumeDialog(j), {
        kind: 'resume', data: j,
        tick: function () {
          var o = $('exResLeft');
          if (o) o.textContent = fmtLeft(Math.min(a.deadline - now(), span || Infinity));
        }
      });
    }, function (e) {
      busy(false);
      if (e.code === 'SESSION') return;
      if (e.code === 'FINISHED' && e.result) return afterFinish(e.result, e.message);
      toast(e.message, 'danger', 6000);
      if (e.code === 'NETWORK' || e.code === 'SERVER') return;
      refresh().then(showDashboard, function () { showDashboard(); });
    });
  }

  /* ---------------------------------------------------------------- 9. 응시 전 확인(성명·서약)·환경 점검 */
  var PLEDGES = [
    '본인이 직접 응시합니다.',
    '문항을 촬영·복제·공유하지 않으며 문항이 한국AI윤리위원회의 저작물임을 확인합니다.',
    '시험 시간과 자동 제출 규칙을 이해했습니다.'
  ];

  function showPledge(courseName) {
    var c = courseBy(courseName);
    if (!c || !c.next || c.next.action !== 'start') return showDashboard();
    var key = courseKey(c.course), ex = c.exam || {}, form = c.next.form || 'A';
    var d = S.data || {}, s = S.session || {};
    var point = ex.point || 100 / (ex.total || 1);
    var nameVal = S.nameDraft != null ? S.nameDraft : (d.name || '');
    var cand = kv([
      ['<label for="exName">성명 <em class="ex-req">필수</em></label>',
        '<input class="ex-text ex-name" id="exName" type="text" autocomplete="name" maxlength="30" spellcheck="false" value="' + esc(nameVal) + '"' +
          ' placeholder="예: 홍길동" aria-describedby="exNameHelp exNameErr" aria-required="true">' +
        '<p class="ex-field-help" id="exNameHelp">이수증에 표기될 성명입니다. 실명을 정확히 입력해 주십시오.</p>' +
        '<p class="ex-field-err" id="exNameErr" role="alert" hidden></p>', 'ex-kv-field'],
      ['아이디(이메일)', '<span class="ex-break">' + esc(d.email || s.email || '-') + '</span>'],
      ['과정', esc(c.course)],
      ['평가지', esc(formName(c, form))]
    ]);
    var rules = kv([
      ['문항 수', '4지선다형 <b>' + ex.total + '문항</b>'],
      ['시험 시간', '<b>' + ex.minutes + '분</b> · 시험 시작을 누른 때부터 흐릅니다'],
      ['배점', '문항당 ' + fmtNum(point) + '점 · 100점 만점'],
      ['이수 기준', '<b>' + passOf(ex) + '점 이상</b> · ' + ex.total + '문항 중 ' + passCountOf(ex) + '문항 이상 정답'],
      ['응시 횟수', '<b>' + esc(formName(c, form)) + '</b> · ' + esc(retakeRule(ex))],
      ['시간 종료', '시험 시간이 끝나면 그때까지 표기한 답안이 <b>자동 제출</b>됩니다'],
      ['답안 저장', '답안은 자동 저장되며, 연결이 끊겨도 시험 시간 안에 다시 로그인해 이어서 응시할 수 있습니다'],
      ['화면 이탈', '응시 중 다른 창이나 탭으로 이동하면 <b>횟수가 기록</b>되어 위원회가 검토합니다'],
      ['최종 제출', '제출한 답안은 수정하거나 다시 제출할 수 없습니다']
    ]);
    var checks = '<div class="ex-checks">' + PLEDGES.map(function (t, i) {
      return '<label class="ex-check"><input type="checkbox" data-pledge="' + i + '"><span class="ex-check-box">' + ico('check') + '</span>' +
        '<span class="ex-check-t">' + esc(t) + '</span><em>필수</em></label>';
    }).join('') + '</div>';
    var html = stepper(1) +
      '<div class="ex-pledge">' +
        '<div class="ex-pledge-main">' +
          '<section class="ex-panel ex-pledge-intro"><header class="ex-panel-head"><h2 class="ex-h">응시 전 확인</h2>' + badge(c.course + ' · ' + formName(c, form), 'open') + '</header>' +
            '<p class="ex-panel-lead">시험을 시작하기 전에 응시자 정보를 확인하고, 시험 안내를 읽은 뒤 응시 서약에 동의해 주십시오.</p></section>' +
          panel('<span class="ex-h-no">1</span>응시자 확인', cand) +
          panel('<span class="ex-h-no">2</span>시험 안내', rules) +
          panel('<span class="ex-h-no">3</span>응시 서약', checks + '<p class="ex-error" id="exPledgeErr" role="alert" hidden></p>') +
          '<div class="ex-actionbar">' +
            '<button type="button" class="ex-btn ex-btn--secondary" data-act="dashboard">' + ico('arrow-left') + '대시보드로</button>' +
            '<div class="ex-actionbar-go">' +
              '<p class="ex-actionbar-note">' + ico('timer') + '<span>시험 시작을 누르면 <b>' + ex.minutes + '분</b> 시험 시간이 바로 시작됩니다.</span></p>' +
              '<button type="button" class="ex-btn ex-btn--primary ex-btn--lg" id="exStartBtn" data-act="start" data-course="' + key + '" disabled>' + ico('pen-line') + '시험 시작</button>' +
            '</div>' +
            '<p class="ex-actionbar-hint" id="exStartHint" aria-live="polite"></p>' +
          '</div>' +
        '</div>' +
        '<aside class="ex-pledge-side">' +
          panel('응시 환경 점검', '<ul class="ex-env" id="exEnvList"></ul>' +
            '<p class="ex-env-hint">PC·태블릿의 최신 크롬·엣지·사파리를 권장합니다. 응시 중에는 알림과 다른 프로그램을 닫아 주십시오.</p>' +
            '<div class="ex-env-foot"><button type="button" class="ex-btn ex-btn--secondary ex-btn--sm ex-btn--block" data-act="env">' + ico('refresh-cw') + '다시 점검</button></div>', { cls: 'ex-env-panel' }) +
        '</aside>' +
      '</div>';
    setView(html, 'pledge', { trail: '응시 전 확인' });
    setHash('pledge/' + key);
    var input = $('exName');
    input.addEventListener('input', function (ev) {
      S.nameDraft = input.value;
      syncStart(ev && ev.isComposing ? 0 : 1);
    });
    input.addEventListener('compositionend', function () { S.nameDraft = input.value; syncStart(1); });
    input.addEventListener('blur', function () { S.nameDraft = input.value; syncStart(2); });
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' && !ev.isComposing) { ev.preventDefault(); startConfirm(c.course); }
    });
    syncStart(nameVal ? 2 : 0);
    runEnvCheck();
  }

  // 성명 형식 + 서약 3개가 모두 맞아야 [시험 시작] 활성
  // level 0: 오류 표시 상태 유지(한글 조합 중·서약 변경), 1: 입력 중(확정 오류만 바로 표시),
  //       2: 칸을 벗어남(길이·끝 글자 오류도 표시), 3: 시험 시작을 누름(빈칸도 표시)
  function syncStart(level) {
    var input = $('exName'), btn = $('exStartBtn'), hint = $('exStartHint');
    if (!input || !btn) return false;
    var ns = nameState(input.value);
    var boxes = document.querySelectorAll('[data-pledge]'), n = 0;
    for (var i = 0; i < boxes.length; i++) {
      boxes[i].parentNode.classList.toggle('is-checked', boxes[i].checked);
      if (boxes[i].checked) n++;
    }
    var all = boxes.length > 0 && n === boxes.length;
    var show = null;
    if (ns.ok) show = false;
    else if (level === 3) show = true;
    else if (level === 2) show = !ns.empty;
    else if (level === 1) show = ns.hard ? true : (ns.empty ? false : null);
    if (show !== null) setNameErr(show ? NAME_MSG : '');
    btn.disabled = !(ns.ok && all);
    if (hint) {
      var ht = !ns.ok ? (ns.empty ? '성명을 입력해 주십시오.' : '성명을 정확히 입력해 주십시오.')
        : !all ? '응시 서약 ' + boxes.length + '개 항목에 모두 동의해 주십시오. (' + n + '/' + boxes.length + ')'
        : '준비가 끝났습니다. 시험 시작을 눌러 주십시오.';
      if (hint.textContent !== ht) hint.textContent = ht;   // 같은 문장을 다시 쓰면 화면 낭독기가 반복해 읽으므로 바뀔 때만
      hint.classList.toggle('is-ready', ns.ok && all);
    }
    return ns.ok && all;
  }

  function setNameErr(msg) {
    var input = $('exName'), err = $('exNameErr');
    if (!input || !err) return;
    err.hidden = !msg;
    err.innerHTML = msg ? ico('alert-triangle') + '<span>' + esc(msg) + '</span>' : '';
    input.classList.toggle('is-invalid', !!msg);
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  }

  function showNameError(msg) {
    var input = $('exName');
    if (!input) return toast(msg || NAME_MSG, 'danger', 6000);
    setNameErr(msg || NAME_MSG);
    try { input.focus({ preventScroll: true }); } catch (e) { input.focus(); }
    try { input.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) { input.scrollIntoView(); }
  }

  function startDialog(c, name) {
    var ex = c.exam || {}, form = c.next.form || 'A';
    return '<div class="ex-dialog-head"><h2 id="exDlgTitle">시험을 시작하시겠습니까?</h2>' +
        '<p>아래 내용을 확인한 뒤 시험 시작을 눌러 주십시오.</p></div>' +
      '<div class="ex-dialog-body">' +
        kv([
          ['성명', '<b>' + esc(name) + '</b>'],
          ['과정', esc(c.course)],
          ['평가지', esc(formName(c, form))],
          ['문항 수', ex.total + '문항'],
          ['시험 시간', '<b>' + ex.minutes + '분</b>']
        ]) +
        '<div class="ex-callout ex-callout--warn">' + ico('alert-triangle') +
          '<span><b>시작하면 시간이 멈추지 않습니다.</b> 창을 닫거나 연결이 끊겨도 ' + ex.minutes + '분 시험 시간은 계속 흐르며, 시간이 끝나면 그때까지의 답안이 자동 제출됩니다.</span></div>' +
      '</div>' +
      '<div class="ex-dialog-foot">' +
        '<button type="button" class="ex-btn ex-btn--secondary" data-act="modal-close" data-autofocus>취소</button>' +
        '<button type="button" class="ex-btn ex-btn--primary" data-act="start-go">' + ico('pen-line') + '시험 시작</button>' +
      '</div>';
  }

  function startConfirm(courseName) {
    var c = courseBy(courseName);
    if (!c || !c.next || c.next.action !== 'start') return showDashboard();
    var input = $('exName'), ns = nameState(input ? input.value : '');
    if (!ns.ok) {
      syncStart(3);
      showNameError(NAME_MSG);
      return;
    }
    if (!syncStart(3)) {
      toast('응시 서약 세 항목에 모두 동의해 주십시오.', 'warn');
      return;
    }
    S.nameDraft = ns.value;
    input.value = ns.value;
    errBox($('exPledgeErr'), '');
    openModal(startDialog(c, ns.value), { kind: 'start', course: c.course, name: ns.value });
  }

  function startExam(courseName, name) {
    if (E) return;
    busy('평가지를 준비하고 있습니다');
    call('start', { course: courseName, agree: true, name: name }).then(function (j) {
      busy(false);
      openExam(j);
    }, function (e) {
      busy(false);
      if (e.code === 'SESSION') return;
      if (e.code === 'FINISHED' && e.result) return afterFinish(e.result, e.message);
      if (e.code === 'NAME') {
        if (S.view === 'pledge') showNameError(e.message);
        else toast(e.message, 'danger', 6000);
        return;
      }
      if (S.view === 'pledge') errBox($('exPledgeErr'), e.message);
      toast(e.message, 'danger', 6000);
      if (e.code === 'NETWORK' || e.code === 'SERVER' || e.code === 'BUSY') return;
      refresh().then(showDashboard, function () { showDashboard(); });
    });
  }

  function browserInfo() {
    var ua = navigator.userAgent || '', m, name = '', ver = '';
    var inApp = /KAKAOTALK|NAVER\(inapp|Instagram|FBAN|FBAV|FB_IAB|Line\/|DaumApps|everytimeApp/i.test(ua);
    if ((m = ua.match(/Edg(?:A|iOS)?\/(\d+)/))) { name = 'Microsoft Edge'; ver = m[1]; }
    else if ((m = ua.match(/Whale\/(\d+)/))) { name = '네이버 웨일'; ver = m[1]; }
    else if ((m = ua.match(/SamsungBrowser\/(\d+)/))) { name = '삼성 인터넷'; ver = m[1]; }
    else if ((m = ua.match(/(?:Chrome|CriOS)\/(\d+)/))) { name = 'Chrome'; ver = m[1]; }
    else if ((m = ua.match(/(?:Firefox|FxiOS)\/(\d+)/))) { name = 'Firefox'; ver = m[1]; }
    else if ((m = ua.match(/Version\/(\d+)[\d.]*.*Safari/))) { name = 'Safari'; ver = m[1]; }
    var modern = typeof fetch === 'function' && typeof Promise === 'function' && !!(window.CSS && CSS.supports && CSS.supports('display', 'grid'));
    if (!modern) return { st: 'bad', label: name || '오래된 브라우저', tip: '지원하지 않는 브라우저입니다. 최신 크롬으로 열어 주십시오.', badge: '불가' };
    if (inApp) return { st: 'warn', label: '앱 안의 브라우저', tip: '크롬·사파리로 열어 응시해 주십시오.', badge: '주의' };
    if (!name) return { st: 'warn', label: '확인되지 않은 브라우저', tip: '최신 크롬·엣지를 권장합니다.', badge: '주의' };
    return { st: 'ok', label: name + (ver ? ' ' + ver : ''), tip: '', badge: '권장' };
  }

  function envRow(id, icon, k, v, st, label) {
    var mark = st === 'check' ? '<span class="ex-spin ex-spin--sm" aria-hidden="true"></span>' : '';
    return '<li id="' + id + '"><span class="ex-env-ic">' + ico(icon) + '</span>' +
      '<div class="ex-env-txt"><span class="ex-env-k">' + k + '</span><span class="ex-env-v">' + v + '</span></div>' +
      '<span class="ex-env-st" data-st="' + st + '">' + mark + label + '</span></li>';
  }

  function runEnvCheck() {
    var list = $('exEnvList');
    if (!list) return;
    var b = browserInfo(), w = window.innerWidth || document.documentElement.clientWidth || 0;
    var ws = w >= 1024 ? ['ok', 'PC 화면', '적합'] : w >= 768 ? ['ok', '태블릿 화면', '적합'] : w >= 360 ? ['warn', '모바일 화면 · PC 권장', '확인'] : ['bad', '화면이 좁습니다', '주의'];
    list.innerHTML =
      envRow('exEnvB', 'globe', '브라우저', esc(b.label) + (b.tip ? '<small>' + esc(b.tip) + '</small>' : ''), b.st, b.badge) +
      envRow('exEnvW', 'monitor', '화면 너비', w + 'px · ' + ws[1], ws[0], ws[2]) +
      envRow('exEnvN', 'wifi', '네트워크', '평가 서버 연결 확인 중', 'check', '확인 중');
    function setNet(st, v, label) {
      var li = $('exEnvN');
      if (li) li.outerHTML = envRow('exEnvN', st === 'bad' ? 'wifi-off' : 'wifi', '네트워크', v, st, label);
    }
    if (navigator.onLine === false) return setNet('bad', '인터넷 연결이 끊겼습니다', '오프라인');
    ping().then(function (j) {
      var ms = j.latency || 0;
      setNet(ms > 1500 ? 'warn' : 'ok', (S.demo ? '체험 서버' : '평가 서버') + ' 응답 ' + ms + 'ms', ms > 1500 ? '느림' : '양호');
    }, function () {
      setNet('bad', '평가 서버에 연결할 수 없습니다', '확인 필요');
    });
  }

  /* ---------------------------------------------------------------- 10. 시험 */
  // 경고 색: 30분 이상 시험은 10분(주황)·5분(빨강), 짧은 체험 시험은 비율로. 알림: 경고·위험·마지막 1분
  function thresholds(minutes) {
    var total = (minutes || 90) * 60000, long = total >= 30 * 60000;
    var warn = long ? 600000 : total * 0.4, danger = long ? 300000 : total * 0.2;
    return {
      warn: warn, danger: danger,
      alerts: [
        { at: warn, tone: 'warn', text: '답안을 점검해 주십시오.' },
        { at: danger, tone: 'danger', text: '안 푼 문항이 없는지 확인해 주십시오.' },
        { at: Math.min(60000, danger / 2), tone: 'danger', text: '시간이 끝나면 답안이 자동 제출됩니다.' }
      ]
    };
  }
  function fsIndex() {
    var v = sget(KEY.fs, true);
    return (typeof v === 'number' && FS_STEPS[v] != null) ? v : 1;
  }
  // 워터마크(성명 · 가린 이메일 · KAIEC): 타일 하나에 글자 두 줄을 엇갈려 놓아 잘리지 않고 고르게 반복
  function wmUrl(text) {
    var t = esc(text) + '  ·  KAIEC';
    var attr = ' text-anchor="middle" dominant-baseline="middle" font-family="Pretendard, Apple SD Gothic Neo, Malgun Gothic, sans-serif"' +
      ' font-size="13" font-weight="600" fill="#0B2A4A" fill-opacity="0.07"';
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="300" viewBox="0 0 560 300">' +
      '<text x="140" y="80"' + attr + ' transform="rotate(-22 140 80)">' + t + '</text>' +
      '<text x="420" y="230"' + attr + ' transform="rotate(-22 420 230)">' + t + '</text></svg>';
    return 'url("data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg) + '")';
  }

  function openExam(j) {
    var a = j.attempt || {}, qs = j.questions || [];
    if (!a.id || !qs.length) {
      toast('평가지를 불러오지 못했습니다. 잠시 후 다시 시도해 주십시오.', 'danger');
      return showDashboard();
    }
    closeModal();
    var server = {}, sFlags = [], k;
    for (k in (j.answers || {})) { var v = +j.answers[k]; if (v >= 1 && v <= 4) server[String(+k)] = v; }
    (j.flags || []).forEach(function (n) { sFlags.push(+n); });
    var answers = copy(server), flags = sFlags.slice(), blur = +j.blurCount || 0, restored = 0;
    // 이 기기에 임시 보관된 답안과 3방향 병합: 서버 값이 마지막 저장 확인 값과 같을 때만 이 기기의 값을 적용
    var bk = sget(KEY.backup, true);
    if (bk && bk.id === a.id) {
      var acked = (bk.acked && bk.acked.answers) || {}, local = bk.answers || {};
      var keys = {};
      Object.keys(local).concat(Object.keys(acked), Object.keys(server)).forEach(function (x) { keys[x] = 1; });
      Object.keys(keys).forEach(function (x) {
        if ((server[x] || 0) === (acked[x] || 0) && (local[x] || 0) !== (server[x] || 0)) {
          if (local[x]) answers[x] = local[x]; else delete answers[x];
          restored++;
        }
      });
      var ackedFlags = ((bk.acked && bk.acked.flags) || []).join(',');
      if (sFlags.slice().sort(function (p, q) { return p - q; }).join(',') === ackedFlags) flags = (bk.flags || []).slice();
      blur = Math.max(blur, +bk.blur || 0);
    } else if (bk) {
      sdel(KEY.backup, true);
    }
    var flagMap = {};
    flags.forEach(function (n) { flagMap[n] = true; });
    var d = S.data || {}, s = S.session || {};
    E = S.exam = {
      id: a.id, course: a.course, form: a.form, label: a.label || FORM_LABEL[a.form] || '',
      name: a.name || d.name || S.nameDraft || '', email: d.email || s.email || '',
      minutes: a.minutes || Math.round((a.deadline - a.startedAt) / 60000) || courseCfg(a.course).minutes || 60,
      point: a.point || 100 / (a.total || qs.length), passScore: a.passScore || 70,
      total: a.total || qs.length, questions: qs, answers: answers, flags: flagMap, blur: blur,
      acked: { answers: server, flags: sFlags.slice().sort(function (p, q) { return p - q; }) },
      startedAt: a.startedAt, deadline: a.deadline, cur: 0, rev: 0, savedRev: 0, saving: false, failCount: 0,
      timers: {}, submitting: false, done: false, hold: false, away: false, onlyEmpty: false,
      prevLeft: null, tst: null, savedAt: 0, fs: fsIndex()
    };
    E.span = (E.deadline - E.startedAt) || E.minutes * 60000;
    E.th = thresholds(E.minutes);
    delete S.live[courseKey(E.course)];
    var cur = sget(KEY.cur);
    if (cur && cur.id === E.id && qs[cur.cur]) E.cur = cur.cur;
    else if (j.resumed) {
      for (var i = 0; i < qs.length; i++) { if (!answers[String(qs[i].n)]) { E.cur = i; break; } }
    }
    clearToasts();
    stopViewTimer();
    renderExam();
    lockPage(true);
    E.timers.tick = setInterval(tick, 250);
    E.timers.beat = setInterval(doSave, 30000);   // 30초마다 자동 저장
    tick();
    setHash('exam/' + courseKey(E.course));
    setSave('idle');
    var left = Math.min(E.deadline - now(), E.span), over = left <= 0;   // over: 시간이 이미 끝나 곧바로 제출되므로 안내 알림 생략
    if (over) { /* 제출 결과 알림만 표시 */ }
    else if (j.resumed) {
      toast('이어서 응시합니다. 남은 시간 ' + fmtLeft(left) + ' · 답안 ' + Object.keys(answers).length + '개', 'info', 6000);
    } else {
      toast('시험이 시작되었습니다. 시험 시간 ' + E.minutes + '분', 'ok');
    }
    if (restored) {
      if (!over) toast('이 기기에 임시 보관된 답안 ' + restored + '개를 복원했습니다.', 'info', 6000);
      markDirty();
    } else {
      backup();
    }
    if (navigator.onLine === false) netState(false);
  }

  function lockPage(on) {
    document.body.classList.toggle('ex-lock', on);
    el.layer.hidden = !on;
    if (!on) el.layer.classList.remove('is-sheet');
  }

  function stopExam(keepBackup) {
    if (!E) return;
    if (keepBackup) backup();
    else { sdel(KEY.backup, true); sdel(KEY.cur); }
    E.done = true;
    for (var k in E.timers) { clearTimeout(E.timers[k]); clearInterval(E.timers[k]); }
    E = S.exam = null;
    lockPage(false);
    el.layer.innerHTML = '';
    closeModal();
  }

  function renderExam() {
    var who = E.name ? esc(E.name) : '응시자';
    E.wm = wmUrl((E.name ? E.name + ' · ' : '') + maskEmail(E.email));
    el.layer.innerHTML =
      '<header class="ex-top">' +
        '<span class="ex-top-badge" role="img" aria-label="KAIEC"><svg viewBox="0 0 59.04 10.66" aria-hidden="true"><use href="#exi-kaiec"></use></svg></span>' +
        '<div class="ex-top-title"><span class="ex-top-prog">AI윤리전문가 양성과정</span>' +
          '<strong><span class="ex-top-pre">이수 평가 · </span>' + esc(E.course) + ' · ' + esc(E.label) + '</strong>' +
          '<span class="ex-top-who">' + who + ' · ' + esc(maskEmail(E.email)) + '</span></div>' +
        (S.demo ? '<span class="ex-top-demo">체험 모드</span>' : '') +
        '<div class="ex-top-cand"><span>응시자</span><strong>' + who + '</strong><em>' + esc(maskEmail(E.email)) + '</em></div>' +
        '<div class="ex-timer" id="exTimer" role="timer" aria-label="남은 시간">' +
          '<div class="ex-timer-row"><span class="ex-timer-k">남은 시간</span><strong class="ex-timer-v" id="exTimerVal">--:--</strong></div>' +
          '<div class="ex-timer-sub">경과 <b id="exTimerSpent">00:00</b> / ' + fmtLeft(E.span) + '</div>' +
          '<div class="ex-timer-bar" aria-hidden="true"><span id="exTimerBar"></span></div>' +
        '</div>' +
        '<button type="button" class="ex-btn ex-top-submit" data-act="submit">' + ico('send') + '답안 제출</button>' +
      '</header>' +
      '<div class="ex-body">' +
        '<div class="ex-main" id="exMain">' +
          '<div class="ex-banners" id="exBanners">' +
            (S.demo ? '<div class="ex-banner ex-banner--demo" id="exBn-demo">' + ico('monitor-play') + '<span>체험 모드: 실제 응시 기록이 남지 않습니다. 예시 ' + E.total + '문항 · 시험 시간 ' + E.minutes + '분</span>' +
              '<button type="button" data-act="banner-close" aria-label="안내 닫기">' + ico('x') + '</button></div>' : '') +
          '</div>' +
          '<article class="ex-qcard" id="exQ" aria-label="문항"></article>' +
          '<div class="ex-qmeta"><div class="ex-kbd"><span><kbd>1</kbd>~<kbd>4</kbd> 답 선택</span><span><kbd>←</kbd><kbd>→</kbd> 문항 이동</span><span><kbd>F</kbd> 다시 보기 표시</span></div>' +
            '<span>문항 저작권 한국AI윤리위원회 · 무단 촬영·복제·공유 금지</span></div>' +
        '</div>' +
        '<aside class="ex-side" id="exSide" aria-label="답안 표기란">' +
          '<div class="ex-side-head"><div class="ex-side-title"><h3>' + ico('layout-grid') + '답안 표기란</h3>' +
            '<span class="ex-side-count" id="exAnsCount"></span>' +
            '<button type="button" class="ex-sheet-x" data-act="sheet-close" aria-label="답안 표기란 닫기">' + ico('x') + '</button></div>' +
            '<div class="ex-bar" role="progressbar" aria-label="답한 문항 비율"><span id="exAnsBar"></span></div>' +
            '<label class="ex-switch"><input type="checkbox" id="exOnlyEmpty"><span class="ex-switch-ui"></span><span>안 푼 문항만 보기</span></label></div>' +
          '<div class="ex-side-scroll"><div class="ex-grid" id="exGrid"></div>' +
            '<ul class="ex-legend"><li><i class="lg-ans"></i>답한 문항</li><li><i></i>안 푼 문항</li><li><i class="lg-cur"></i>현재 문항</li><li><i class="lg-flag"></i>다시 보기</li></ul></div>' +
          '<div class="ex-side-foot">' +
            '<div class="ex-fs"><span>글자 크기</span><div class="ex-fs-btns" role="group" aria-label="글자 크기">' +
              '<button type="button" data-act="fs-" aria-label="글자 작게">가-</button><output id="exFsVal">100%</output>' +
              '<button type="button" data-act="fs+" aria-label="글자 크게">가+</button></div></div>' +
            '<div class="ex-save" id="exSave" data-state="idle" aria-live="polite"><i class="ex-save-dot"></i><span id="exSaveText"></span></div>' +
            '<div class="ex-side-meta"><span id="exNetBox">' + ico('wifi') + '연결 <b id="exNet">정상</b></span>' +
              '<span>' + ico('eye') + '화면 이탈 <b id="exBlur">' + E.blur + '</b>회</span></div>' +
          '</div>' +
        '</aside>' +
      '</div>' +
      '<nav class="ex-mbar" aria-label="문항 이동">' +
        '<button type="button" class="ex-mbtn" id="exMPrev" data-act="prev">' + ico('chevron-left') + '이전</button>' +
        '<button type="button" class="ex-mbtn ex-mbtn--sheet" data-act="sheet-open">' + ico('layout-grid') + '<span>답안 표기란</span><b id="exMCount"></b></button>' +
        '<button type="button" class="ex-mbtn" id="exMNext" data-act="next">다음' + ico('chevron-right') + '</button>' +
      '</nav>' +
      '<div class="ex-sheet-dim" data-act="sheet-close"></div>';
    applyFs();
    renderQ();
    renderGrid();
    updateProgress();
  }

  function stemHtml(q) {
    var h = esc(q.stem || '');
    (q.underline || []).forEach(function (w) {
      w = esc(String(w == null ? '' : w).trim());
      if (w) h = h.split(w).join('<u>' + w + '</u>');
    });
    return h;
  }

  function renderQ() {
    var box = $('exQ');
    if (!E || !box) return;
    var focusAct = document.activeElement && box.contains(document.activeElement) ? document.activeElement.getAttribute('data-act') : null;
    if (focusAct === 'pick') focusAct = null;   // 선택지는 문항마다 달라 초점을 옮기지 않음
    var q = E.questions[E.cur], n = String(q.n), sel = E.answers[n] || 0, flagged = !!E.flags[q.n], last = E.cur === E.questions.length - 1;
    var bogi = q.bogi || [];
    box.innerHTML =
      '<div class="ex-qhead"><span class="ex-qno">문항 <b>' + esc(q.n) + '</b> / ' + E.total + '</span>' +
        (q.areaName ? '<span class="ex-area" title="평가 영역">' + esc(q.areaName) + '</span>' : '') +
        (flagged ? '<span class="ex-qflag">' + ico('flag') + '다시 보기</span>' : '') +
        '<span class="ex-qpt">배점 ' + fmtNum(E.point) + '점</span></div>' +
      '<div class="ex-qbody"><div class="ex-wm" aria-hidden="true" style="background-image:' + E.wm.replace(/"/g, '&quot;') + '"></div>' +
        '<h2 class="ex-stem"><span class="ex-stem-no">' + esc(q.n) + '.</span><span>' + stemHtml(q) + '</span></h2>' +
        (q.box ? '<div class="ex-box">' + esc(q.box) + '</div>' : '') +
        (bogi.length ? '<div class="ex-bogi"><span class="ex-bogi-label">〈보기〉</span><ul>' + bogi.map(function (b) {
          return '<li><b>' + esc(b.k) + '.</b><span>' + esc(b.t) + '</span></li>';
        }).join('') + '</ul></div>' : '') +
        '<div class="ex-opts" role="radiogroup" aria-label="문항 ' + esc(q.n) + ' 선택지">' + (q.options || []).map(function (o, i) {
          var v = i + 1, on = sel === v;
          return '<button type="button" class="ex-opt' + (on ? ' is-on' : '') + '" role="radio" aria-checked="' + on + '" data-act="pick" data-v="' + v + '">' +
            '<span class="ex-opt-no" aria-hidden="true">' + v + '</span><span class="ex-opt-t"><span class="sr-only">' + circ(v) + ' </span>' + esc(o) + '</span></button>';
        }).join('') + '</div>' +
      '</div>' +
      '<div class="ex-qfoot">' +
        '<button type="button" class="ex-btn ex-btn--secondary ex-qprev" data-act="prev"' + (E.cur === 0 ? ' disabled' : '') + '>' + ico('arrow-left') + '이전</button>' +
        '<button type="button" class="ex-btn ex-btn--secondary ex-flag-btn' + (flagged ? ' is-on' : '') + '" data-act="flag" aria-pressed="' + flagged + '">' + ico('flag') +
          (flagged ? '다시 보기 해제' : '다시 보기 표시') + '</button>' +
        (last
          ? '<button type="button" class="ex-btn ex-btn--primary ex-qnext" data-act="submit">답안 제출' + ico('send') + '</button>'
          : '<button type="button" class="ex-btn ex-btn--primary ex-qnext" data-act="next">다음' + ico('arrow-right') + '</button>') +
      '</div>';
    if (focusAct) {
      var f = box.querySelector('[data-act="' + focusAct + '"]:not([disabled])');
      if (f) { try { f.focus({ preventScroll: true }); } catch (e) { f.focus(); } }
    }
    var mp = $('exMPrev'), mn = $('exMNext');
    if (mp) mp.disabled = E.cur === 0;
    if (mn) {
      mn.setAttribute('data-act', last ? 'submit' : 'next');
      mn.innerHTML = last ? '제출' + ico('send') : '다음' + ico('chevron-right');
    }
  }

  function renderGrid() {
    var g = $('exGrid');
    if (!E || !g) return;
    var shown = 0;
    g.innerHTML = E.questions.map(function (q, i) {
      var v = E.answers[String(q.n)], f = !!E.flags[q.n], hide = E.onlyEmpty && v;
      if (!hide) shown++;
      return '<button type="button" class="ex-cell' + (v ? ' is-ans' : '') + (f ? ' is-flag' : '') + (i === E.cur ? ' is-cur' : '') + '"' +
        ' data-act="go" data-i="' + i + '"' + (hide ? ' hidden' : '') + (i === E.cur ? ' aria-current="true"' : '') +
        ' aria-label="문항 ' + esc(q.n) + (v ? ', ' + circ(v) + ' 선택' : ', 안 푼 문항') + (f ? ', 다시 보기 표시' : '') + '">' +
        '<span class="ex-cell-n">' + esc(q.n) + '</span><span class="ex-cell-a">' + (v ? '<i>' + v + '</i>' : '') + '</span></button>';
    }).join('') + (E.onlyEmpty && !shown ? '<p class="ex-grid-empty">모든 문항에 답했습니다.</p>' : '');
  }

  function answeredCount() {
    var c = 0;
    E.questions.forEach(function (q) { if (E.answers[String(q.n)]) c++; });
    return c;
  }
  function updateProgress() {
    var c = answeredCount(), t = E.questions.length;
    var ac = $('exAnsCount'), ab = $('exAnsBar'), mc = $('exMCount');
    if (ac) ac.innerHTML = '답한 문항 <b>' + c + '</b> / ' + t;
    if (ab) ab.style.width = (c / t * 100).toFixed(1) + '%';
    if (mc) mc.textContent = c + '/' + t;
  }

  var autoNext = null;                       // 보기를 고르면 잠시 뒤 다음 문항으로 (2026.09.16)
  function cancelAuto() { if (autoNext) { clearTimeout(autoNext); autoNext = null; } }

  function pick(v) {
    if (!E || E.submitting || !(v >= 1 && v <= 4)) return;
    var q = E.questions[E.cur], n = String(q.n);
    if (!q.options || v > q.options.length) return;
    if (E.answers[n] === v) return;
    E.answers[n] = v;
    var opts = $('exQ').querySelectorAll('.ex-opt');
    for (var i = 0; i < opts.length; i++) {
      var on = i + 1 === v;
      opts[i].classList.toggle('is-on', on);
      opts[i].setAttribute('aria-checked', on ? 'true' : 'false');
    }
    renderGrid();
    updateProgress();
    markDirty();
    cancelAuto();
    if (E.cur < E.questions.length - 1) {          // 마지막 문항에서는 제출 버튼을 직접 누르게 둡니다
      var at = E.cur;
      autoNext = setTimeout(function () {
        autoNext = null;
        if (E && !E.submitting && E.cur === at) go(at + 1);
      }, 300);
    }
  }

  function go(i) {
    if (!E || E.submitting) return;
    cancelAuto();
    i = Math.max(0, Math.min(E.questions.length - 1, i));
    if (i === E.cur) return;
    E.cur = i;
    sset(KEY.cur, { id: E.id, cur: i });
    renderQ();
    renderGrid();
    var m = $('exMain');
    if (m) m.scrollTop = 0;
  }

  function toggleFlag() {
    if (!E || E.submitting) return;
    var n = E.questions[E.cur].n;
    if (E.flags[n]) delete E.flags[n];
    else E.flags[n] = true;
    renderQ();
    renderGrid();
    markDirty();
  }

  function fontStep(d) {
    if (!E) return;
    E.fs = Math.max(0, Math.min(FS_STEPS.length - 1, E.fs + d));
    sset(KEY.fs, E.fs, true);
    applyFs();
  }
  function applyFs() {
    el.layer.style.setProperty('--ex-scale', String(FS_STEPS[E.fs]));
    var o = $('exFsVal');
    if (o) o.textContent = Math.round(FS_STEPS[E.fs] * 100) + '%';
    var minus = el.layer.querySelector('[data-act="fs-"]'), plus = el.layer.querySelector('[data-act="fs+"]');
    if (minus) minus.disabled = E.fs === 0;
    if (plus) plus.disabled = E.fs === FS_STEPS.length - 1;
  }
  function closeSheet() { el.layer.classList.remove('is-sheet'); }

  /* 자동 저장: 답 변경 후 1.5초 디바운스 + 30초 주기, 실패하면 간격을 늘려 재시도 */
  function answerMap() {
    var o = {};
    for (var k in E.answers) if (E.answers[k]) o[k] = E.answers[k];
    return o;
  }
  function flagList() {
    return Object.keys(E.flags).map(Number).filter(function (n) { return E.flags[n]; }).sort(function (p, q) { return p - q; });
  }
  function payload() { return { attemptId: E.id, answers: answerMap(), flags: flagList(), blurCount: E.blur }; }
  function backup() {
    if (!E) return;
    sset(KEY.backup, { id: E.id, answers: answerMap(), flags: flagList(), blur: E.blur, acked: E.acked, at: Date.now() }, true);
  }
  function markDirty() {
    if (!E) return;
    E.rev++;
    backup();
    clearTimeout(E.timers.debounce);
    E.timers.debounce = setTimeout(doSave, 1500);
  }
  function setSave(st) {
    var box = $('exSave'), txt = $('exSaveText');
    if (!box || !E) return;
    box.setAttribute('data-state', st);
    txt.textContent = st === 'saved' ? '자동 저장됨 ' + fmtClock(E.savedAt || now())
      : st === 'saving' ? '답안을 저장하고 있습니다'
      : st === 'retry' ? '저장 대기 · 잠시 후 다시 저장합니다'
      : st === 'offline' ? '저장 대기 · 인터넷 연결이 끊겼습니다'
      : '답안은 자동으로 저장됩니다';
  }
  function doSave() {
    if (!E || E.submitting || E.done) return;
    if (E.saving) return;
    clearTimeout(E.timers.debounce);
    clearTimeout(E.timers.retry);
    if (navigator.onLine === false) { setSave('offline'); return; }
    var rev = E.rev, snap = payload(), id = E.id;
    E.saving = true;
    setSave('saving');
    call('save', snap).then(function (j) {
      if (!E || E.id !== id) return;
      E.saving = false;
      E.failCount = 0;
      if (typeof j.deadline === 'number') { E.deadline = j.deadline; E.span = (E.deadline - E.startedAt) || E.span; }
      E.savedRev = Math.max(E.savedRev, rev);
      E.acked = { answers: snap.answers, flags: snap.flags };
      E.savedAt = j.savedAt || now();
      backup();
      if (E.rev > rev) { setSave('saving'); E.timers.debounce = setTimeout(doSave, 700); }
      else setSave('saved');
    }, function (e) {
      if (!E || E.id !== id) return;
      E.saving = false;
      if (e.code === 'FINISHED') return afterFinish(e.result, e.message);
      if (e.code === 'SESSION') return;
      if (e.code === 'NOT_FOUND') {
        stopExam(true);
        toast(e.message, 'danger', 6000);
        refresh().then(showDashboard, function () { showDashboard(); });
        return;
      }
      E.failCount++;
      setSave(navigator.onLine === false ? 'offline' : 'retry');
      E.timers.retry = setTimeout(doSave, Math.min(30000, 2000 * Math.pow(2, Math.min(E.failCount, 4))));
    });
  }

  // 타이머: 남은 시간(크게) + 경과/전체 + 진행 막대. 서버 시각 보정(now) 기준으로 1초마다 줄어듦
  function tick() {
    if (!E || E.done) return;
    var span = E.span, left = Math.min(E.deadline - now(), span), spent = span - left;
    var tv = $('exTimerVal'), ts = $('exTimerSpent'), tb = $('exTimerBar');
    if (tv) tv.textContent = fmtLeft(left);
    if (ts) ts.textContent = fmtSpent(Math.min(spent, span));
    if (tb) tb.style.transform = 'scaleX(' + Math.max(0, Math.min(1, spent / span)).toFixed(4) + ')';
    var st = left <= E.th.danger ? 'danger' : (left <= E.th.warn ? 'warn' : '');
    if (st !== E.tst) {
      E.tst = st;
      var te = $('exTimer');
      if (te) te.className = 'ex-timer' + (st ? ' is-' + st : '');
    }
    var dl = $('exDlgLeft');
    if (dl) dl.textContent = fmtLeft(left);
    if (E.prevLeft != null && left > 0) {
      E.th.alerts.forEach(function (al) {
        if (E.prevLeft > al.at && left <= al.at) {
          toast('남은 시간이 ' + leftText(al.at) + '입니다. ' + al.text, al.tone, 6500);
        }
      });
    }
    E.prevLeft = left;
    if (left <= 0 && !E.submitting && !E.hold) submit('timeout');
  }

  /* ---------------------------------------------------------------- 11. 제출 */
  function openSubmit() {
    if (!E || E.submitting) return;
    closeSheet();
    var un = [], fl = [];
    E.questions.forEach(function (q, i) {
      if (!E.answers[String(q.n)]) un.push([q.n, i]);
      if (E.flags[q.n]) fl.push([q.n, i]);
    });
    var t = E.questions.length;
    function chips(arr, cls) {
      if (!arr.length) return '<p class="ex-none">없음</p>';
      return '<div class="ex-numchips">' + arr.map(function (x) {
        return '<button type="button" class="ex-numchip' + (cls ? ' ' + cls : '') + '" data-act="jump" data-i="' + x[1] + '" aria-label="문항 ' + x[0] + '으로 이동">' + x[0] + '</button>';
      }).join('') + '</div>';
    }
    openModal(
      '<div class="ex-dialog-head"><h2 id="exDlgTitle">답안을 제출하시겠습니까?</h2>' +
        '<p>제출한 뒤에는 답안을 수정할 수 없습니다. 남은 시간 <b class="ex-num" id="exDlgLeft">' + fmtLeft(Math.min(E.deadline - now(), E.span)) + '</b></p></div>' +
      '<div class="ex-dialog-body">' +
        '<div class="ex-sum"><div><span>답한 문항</span><strong>' + (t - un.length) + '<small> / ' + t + '</small></strong></div>' +
          '<div class="' + (un.length ? 'is-alert' : '') + '"><span>안 푼 문항</span><strong>' + un.length + '</strong></div>' +
          '<div class="' + (fl.length ? 'is-flag' : '') + '"><span>다시 보기</span><strong>' + fl.length + '</strong></div></div>' +
        '<div class="ex-numset"><div class="ex-numset-k">안 푼 문항 <small>번호를 누르면 그 문항으로 이동합니다</small></div>' + chips(un, '') + '</div>' +
        '<div class="ex-numset"><div class="ex-numset-k">다시 보기 표시 문항</div>' + chips(fl, 'ex-numchip--flag') + '</div>' +
        '<div id="exDlgWarn"></div>' +
      '</div>' +
      '<div class="ex-dialog-foot">' +
        '<button type="button" class="ex-btn ex-btn--secondary" data-act="modal-close" data-autofocus>계속 풀기</button>' +
        '<button type="button" class="ex-btn ex-btn--primary" data-act="final-submit" data-unanswered="' + un.length + '">' + ico('send') + '최종 제출</button>' +
      '</div>', { kind: 'submit', stage: 0 });
  }

  function finalSubmit(btn) {
    var un = +btn.getAttribute('data-unanswered') || 0;
    if (un > 0 && modalState && modalState.stage === 0) {   // 안 푼 문항이 있으면 한 번 더 확인
      modalState.stage = 1;
      $('exDlgWarn').innerHTML = '<div class="ex-callout ex-callout--danger" role="alert">' + ico('alert-triangle') +
        '<span>안 푼 문항이 ' + un + '개 있습니다. 안 푼 문항은 점수에 포함되지 않습니다. 그래도 제출하려면 버튼을 한 번 더 눌러 주십시오.</span></div>';
      btn.className = 'ex-btn ex-btn--danger';
      btn.innerHTML = ico('send') + '안 푼 문항이 있어도 제출';
      return;
    }
    closeModal();
    submit('manual');
  }

  function submit(reason) {
    if (!E || E.submitting) return;
    E.submitting = true;
    cancelAuto();
    clearTimeout(E.timers.debounce);
    clearTimeout(E.timers.retry);
    closeModal();
    closeSheet();
    backup();
    var id = E.id, tries = 0;
    busy(reason === 'timeout' ? '시험 시간이 끝나 답안을 제출하고 있습니다' : '답안을 제출하고 있습니다');
    (function attempt() {
      if (!E || E.id !== id) return;
      tries++;
      var p = payload();
      p.reason = reason;
      call('submit', p).then(function (j) {
        afterFinish(j.result);
      }, function (e) {
        if (!E || E.id !== id) return;
        if (e.code === 'FINISHED' && e.result) return afterFinish(e.result, e.message);
        if (e.code === 'SESSION') { busy(false); return; }
        if (e.code === 'NOT_FOUND') {
          busy(false);
          stopExam(true);
          toast(e.message, 'danger', 6000);
          refresh().then(showDashboard, function () { showDashboard(); });
          return;
        }
        if (tries < 3 && (e.code === 'NETWORK' || e.code === 'SERVER')) {
          busy('연결이 불안정해 다시 제출하고 있습니다 (' + (tries + 1) + '/3)');
          setTimeout(attempt, 2500 * tries);
          return;
        }
        busy(false);
        E.submitting = false;
        E.hold = reason === 'timeout';
        openModal(
          '<div class="ex-dialog-head"><h2 id="exDlgTitle">답안을 제출하지 못했습니다</h2><p>' + esc(e.message) + '</p></div>' +
          '<div class="ex-dialog-body"><p class="ex-callout">' + ico('wifi-off') + '<span>답안은 이 기기에 보관되어 있습니다. 인터넷 연결을 확인한 뒤 다시 제출해 주십시오.' +
            (reason === 'timeout' ? ' 시험 시간이 지난 경우 마지막으로 저장된 답안으로 채점될 수 있습니다.' : '') + '</span></p></div>' +
          '<div class="ex-dialog-foot">' +
            (reason === 'timeout' ? '' : '<button type="button" class="ex-btn ex-btn--secondary" data-act="modal-close">계속 풀기</button>') +
            '<button type="button" class="ex-btn ex-btn--primary" data-act="retry-submit" data-reason="' + reason + '" data-autofocus>' + ico('refresh-cw') + '다시 제출</button>' +
          '</div>', { kind: 'submit-fail', lock: reason === 'timeout' });
      });
    })();
  }

  function afterFinish(result, msg) {
    busy(false);
    stopExam(false);
    S.live = {};
    if (!result) { refresh().then(showDashboard, function () { showDashboard(); }); return; }
    if (!msg && result.submitType === '시간 종료') msg = '시험 시간이 끝나 답안이 자동 제출되었습니다.';
    toast(msg || '답안이 제출되었습니다.', msg ? 'info' : 'ok', 5000);
    S.reveal = true;                       // 방금 제출한 결과에만 판정 연출을 보여 줍니다
    showResult(result);
    refresh().catch(function () { /* 대시보드로 갈 때 다시 불러옴 */ });
  }

  /* ---------------------------------------------------------------- 12. 결과 */
  function gaugeSvg(score, pass, passed) {
    var R = 100, C = 2 * Math.PI * R, pct = Math.max(0, Math.min(100, +score || 0));
    var ang = (pass / 100) * 2 * Math.PI - Math.PI / 2;
    function pt(r) { return (120 + r * Math.cos(ang)).toFixed(2) + ' ' + (120 + r * Math.sin(ang)).toFixed(2); }
    var lx = 120 + (R + 25) * Math.cos(ang), ly = 120 + (R + 25) * Math.sin(ang);
    return '<svg viewBox="-16 -16 272 272" role="img" aria-label="점수 ' + fmtNum(score) + '점, 이수 기준 ' + pass + '점">' +
      '<circle cx="120" cy="120" r="' + R + '" fill="none" stroke="#E6EAF0" stroke-width="14"/>' +
      '<circle class="ex-gauge-arc" cx="120" cy="120" r="' + R + '" fill="none" stroke="' + (passed ? '#0F766E' : '#6B7482') + '" stroke-width="14"' +
        ' stroke-dasharray="' + C.toFixed(2) + '" stroke-dashoffset="' + C.toFixed(2) + '"' +
        ' data-off="' + (C * (1 - pct / 100)).toFixed(2) + '" transform="rotate(-90 120 120)"/>' +
      '<path d="M' + pt(R - 11) + ' L' + pt(R + 11) + '" stroke="#0B2A4A" stroke-width="3"/>' +
      '<text x="' + lx.toFixed(1) + '" y="' + (ly - 2).toFixed(1) + '" text-anchor="middle" font-size="10" font-weight="600" fill="#5B6573">기준</text>' +
      '<text x="' + lx.toFixed(1) + '" y="' + (ly + 11).toFixed(1) + '" text-anchor="middle" font-size="13" font-weight="700" fill="#0B2A4A">' + pass + '</text>' +
    '</svg>';
  }

  function nextBox(tone, title, items, action) {
    return '<div class="ex-next-box" data-tone="' + tone + '"><h4>' + esc(title) + '</h4><ul>' +
      items.filter(Boolean).map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' + (action || '') + '</div>';
  }

  function showResult(r) {
    if (!r) return showDashboard();
    var d = S.data || {}, s = S.session || {};
    var key = courseKey(r.course), pass = r.passScore || 70;
    var name = r.name || d.name || s.name || '', email = d.email || s.email || '';
    var facts = [
      ['정답 수', r.correct + '<small> / ' + r.total + '</small>'],
      ['점수', fmtNum(r.score) + '<small>점</small>'],
      ['이수 기준', pass + '<small>점 이상</small>'],
      ['소요 시간', r.durationMin == null ? '-' : (+r.durationMin < 1 ? '1<small>분 미만</small>' : r.durationMin + '<small>분</small>')],
      ['제출 방식', esc(r.submitType || '-')]
    ];
    var areas = (r.areas || []).map(function (a) {
      var p = a.total ? a.correct / a.total * 100 : 0;
      return '<li><span class="ex-area-code">' + esc(ROMAN[a.code] || a.code) + '</span><span class="ex-area-name">' + esc(a.name) + '</span>' +
        '<span class="ex-area-val">' + a.correct + ' / ' + a.total + '</span>' +
        '<div class="ex-bar" role="img" aria-label="' + esc(a.name) + ' ' + a.total + '문항 중 ' + a.correct + '문항 정답"><span style="width:' + p.toFixed(1) + '%"></span></div></li>';
    }).join('');
    var demoNote = S.demo ? '체험 모드 결과는 저장되지 않으며 실제 이수와 관계가 없습니다.' : '';
    var next;
    if (r.passed) {
      next = nextBox('pass', '이수증 발급 안내', [
        '위원회가 응시 기록을 확인한 뒤 7일 이내에 「AI윤리전문가 양성과정 이수증」(PDF)을 이메일로 보내 드립니다.',
        '이수번호가 부여되어 한국AI윤리위원회 홈페이지에 AI윤리전문가로 공식 등록·검색됩니다.',
        '이수자는 위원회 전문위원 등록을 신청할 수 있으며, 이수 사실은 위원회를 통해 확인할 수 있습니다.',
        demoNote
      ], S.demo ? '<button type="button" class="ex-btn ex-btn--secondary" data-act="demo-restart">' + ico('rotate-ccw') + '체험 처음부터 다시 하기</button>' : '');
    } else if (r.retake && r.retake.available) {
      var rf = r.retake.form || 'B';
      next = nextBox('retake', '재응시 ' + rf + '형이 열렸습니다', [
        '응시 기간 안에서는 이수할 때까지 다시 응시할 수 있고, 추가 비용은 없습니다.',
        '재응시는 방금 응시한 평가지와 다른 문항(' + rf + '형)으로 출제됩니다.',
        '재응시에서도 이수 기준은 ' + pass + '점 이상입니다.',
        demoNote
      ], '<button type="button" class="ex-btn ex-btn--primary" data-act="retake" data-course="' + key + '">' + ico('pen-line') + '재응시 ' + rf + '형 응시하기</button>');
    } else {
      next = nextBox('wait', '위원회 안내를 기다려 주십시오', [
        /기회를 모두 사용/.test(r.message || '') ? '재응시 기회를 모두 사용했습니다.' : (/기간이 끝나/.test(r.message || '') ? '응시 기간이 끝나 재응시를 시작할 수 없습니다.' : '지금은 재응시할 수 있는 평가지가 없습니다.'),
        '이후 절차는 위원회가 이메일로 안내해 드립니다.',
        '문의: ' + (CFG.email || ''),
        demoNote
      ], S.demo
        ? '<button type="button" class="ex-btn ex-btn--secondary" data-act="demo-restart">' + ico('rotate-ccw') + '체험 처음부터 다시 하기</button>'
        : '<a class="ex-btn ex-btn--secondary" href="mailto:' + esc(CFG.email || '') + '">' + ico('mail') + '위원회에 문의하기</a>');
    }
    var meta = [name ? '응시자 ' + esc(name) : '', esc(r.course) + ' · ' + esc(r.label || FORM_LABEL[r.form]), '제출 ' + fmtDT(r.submittedAt)]
      .filter(Boolean).map(function (t) { return '<span class="ex-meta-i">' + t + '</span>'; })
      .join('<span class="ex-dot-sep" aria-hidden="true">·</span>');
    var html = stepper(3) +
      '<article class="ex-panel ex-result" data-result="' + esc(r.attemptId) + '" data-passed="' + (r.passed ? 1 : 0) + '">' +
        '<div class="ex-print-only ex-print-head"><strong>한국AI윤리위원회 · AI윤리전문가 양성과정 이수 평가 결과</strong>' +
          '<span>출력 ' + fmtDT(now()) + '</span></div>' +
        '<header class="ex-result-head"><h2 class="ex-h ex-h--lg">평가 결과</h2><p class="ex-result-meta">' + meta + '</p></header>' +
        '<div class="ex-result-top">' +
          '<div class="ex-gauge">' + gaugeSvg(r.score, pass, r.passed) +
            '<div class="ex-gauge-val"><span>점수</span><strong>' + fmtNum(r.score) + '</strong><em>100점 만점</em></div></div>' +
          '<div class="ex-result-sum">' +
            '<span class="ex-verdict ex-verdict--' + (r.passed ? 'pass' : 'fail') + '">' + ico(r.passed ? 'badge-check' : 'circle-x') + (r.passed ? '이수' : '미이수') + '</span>' +
            '<h3>' + (r.passed ? esc(r.course) + ' 이수 기준을 충족했습니다' : '이수 기준까지 ' + fmtNum(Math.max(0, pass - (+r.score || 0))) + '점이 부족합니다') + '</h3>' +
            (r.message ? '<p class="ex-result-msg">' + esc(r.message) + '</p>' : '') +
            '<dl class="ex-facts">' + facts.map(function (f) { return '<div><dt>' + f[0] + '</dt><dd>' + f[1] + '</dd></div>'; }).join('') + '</dl>' +
          '</div></div>' +
        '<div class="ex-result-grid">' +
          '<section class="ex-areas"><h3 class="ex-h">영역별 정답</h3><ul>' + areas + '</ul>' +
            '<p class="ex-areas-note">문항 보호를 위해 문항별 정답과 해설은 공개하지 않습니다.</p></section>' +
          '<section class="ex-next"><h3 class="ex-h">다음 단계</h3>' + next + '</section>' +
        '</div>' +
        '<footer class="ex-result-foot ex-noprint"><small>응시 ID ' + esc(r.attemptId) + '</small><div class="ex-actions">' +
          '<button type="button" class="ex-btn ex-btn--secondary" data-act="dashboard">' + ico('arrow-left') + '대시보드로</button>' +
          '<button type="button" class="ex-btn ex-btn--primary" data-act="print">' + ico('printer') + '결과 인쇄</button></div></footer>' +
        '<div class="ex-print-only ex-print-foot">응시자 ' + esc(name) + ' (' + esc(email) + ') · 응시 ID ' + esc(r.attemptId) +
          ' · 시작 ' + fmtDT(r.startedAt) + ' · 제출 ' + fmtDT(r.submittedAt) + (S.demo ? ' · 체험 모드 결과(기록 없음)' : '') + '</div>' +
      '</article>';
    setView(html, 'result', { trail: '평가 결과' });
    setHash('result/' + encodeURIComponent(r.attemptId));
    var arc = el.view.querySelector('.ex-gauge-arc');
    if (arc) {
      arc.getBoundingClientRect();
      requestAnimationFrame(function () { arc.style.strokeDashoffset = arc.getAttribute('data-off'); });
    }
    var reveal = S.reveal; S.reveal = false;
    if (!reduceMotion()) {
      countUp(el.view.querySelector('.ex-gauge-val strong'), +r.score || 0);
      if (reveal) showVerdict(r);
    }
  }

  function reduceMotion() {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  }

  /* 점수 0 → 실제 점수 카운트업 */
  function countUp(node, to) {
    if (!node || !(to > 0)) return;
    var t0 = 0, dur = 1000;
    node.textContent = '0';
    requestAnimationFrame(function step(ts) {
      if (!t0) t0 = ts;
      var k = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      node.textContent = fmtNum(Math.round(to * e * 10) / 10);
      if (k < 1) requestAnimationFrame(step);
      else node.textContent = fmtNum(to);
    });
  }

  /* 제출 직후 이수·미이수 판정 연출 (클릭하거나 잠시 뒤 사라집니다) */
  function showVerdict(r) {
    var pass = !!r.passed;
    var c = courseBy(r.course), lim = c && c.exam ? c.exam.retakes : -1;
    var rf = r.retake && r.retake.available ? (r.retake.form || 'B') : '';
    var sub = pass
      ? '「AI윤리전문가 양성과정 이수증」이 이메일로 발급되고<br>한국AI윤리위원회 홈페이지에 AI윤리전문가로 공식 등록됩니다'
      : (!rf ? '이후 절차는 결과 화면의<br>안내를 확인해 주십시오'
        : (lim == null || lim < 0 ? '응시 기간 안에는 횟수 제한 없이<br>다시 응시할 수 있습니다'
          : '재응시 ' + rf + '형이 열렸습니다<br>추가 비용 없이 다시 응시할 수 있습니다'));
    var spark = '';
    if (pass) for (var i = 0; i < 12; i++) spark += '<i style="--i:' + i + '"></i>';
    var box = document.createElement('div');
    box.className = 'ex-reveal' + (pass ? ' is-pass' : ' is-fail');
    box.setAttribute('role', 'status');
    box.innerHTML =
      '<div class="ex-reveal-in">' +
        '<div class="ex-reveal-badge">' +
          '<svg class="ex-reveal-ring" viewBox="0 0 132 132" aria-hidden="true">' +
            '<circle class="ex-reveal-trk" cx="66" cy="66" r="58"/>' +
            '<circle class="ex-reveal-arc" cx="66" cy="66" r="58"/></svg>' +
          '<span class="ex-reveal-ic">' + ico(pass ? 'badge-check' : 'rotate-ccw') + '</span>' +
        '</div>' +
        '<strong class="ex-reveal-word">' + (pass ? '이 수' : '미 이 수') + '</strong>' +
        '<span class="ex-reveal-meta">' + esc(r.course || '') + ' · ' + fmtNum(r.score) + '점</span>' +
        '<span class="ex-reveal-sub">' + sub + '</span>' +
        (spark ? '<div class="ex-reveal-spark" aria-hidden="true">' + spark + '</div>' : '') +
      '</div>';
    document.body.appendChild(box);
    var done = false;
    function close() {
      if (done) return;
      done = true;
      box.classList.add('is-out');
      setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 460);
    }
    box.addEventListener('click', close);
    requestAnimationFrame(function () { box.classList.add('is-on'); });
    setTimeout(close, pass ? 3200 : 2600);
  }

  /* ---------------------------------------------------------------- 13. 이벤트 */
  document.addEventListener('click', function (ev) {
    var t = ev.target && ev.target.closest ? ev.target.closest('[data-act]') : null;
    if (!t) {
      if (ev.target === el.modal && modalState && !modalState.lock) closeModal();
      return;
    }
    if (t.disabled) return;
    var act = t.getAttribute('data-act'), course = KEY_COURSE[t.getAttribute('data-course')];
    if (t.tagName === 'A' && /^#/.test(t.getAttribute('href') || '')) ev.preventDefault();
    switch (act) {
      case 'demo': ev.preventDefault(); enterDemo(); break;
      case 'demo-exit': exitDemo(); break;
      case 'demo-restart': restartDemo(); break;
      case 'logout': logout(); break;
      case 'retry': restore(); break;
      case 'refresh':
        setBtnBusy(t, true, '불러오는 중');
        refresh().then(function () { S.live = {}; showDashboard(); toast('최신 상태를 불러왔습니다.', 'ok', 2500); },
          function (e) { setBtnBusy(t, false); if (e.code !== 'SESSION') toast(e.message, 'danger'); });
        break;
      case 'dashboard': showDashboard(); break;
      case 'pledge': showPledge(course); break;
      case 'resume': resumeConfirm(course); break;
      case 'resume-go':
        var rj = modalState && modalState.data;
        closeModal();
        if (rj) openExam(rj);
        break;
      case 'result': showResult(findResult(t.getAttribute('data-id'))); break;
      case 'retake':
        busy('재응시 정보를 확인하고 있습니다');
        refresh().then(function () { busy(false); showPledge(course); },
          function (e) { busy(false); if (e.code !== 'SESSION') toast(e.message, 'danger'); });
        break;
      case 'print': window.print(); break;
      case 'env': runEnvCheck(); break;
      case 'start': startConfirm(course); break;
      case 'start-go':
        var sc = modalState && modalState.course, sn = modalState && modalState.name;
        closeModal();
        if (sc && sn) startExam(sc, sn);
        break;
      case 'pick': pick(+t.getAttribute('data-v')); break;
      case 'prev': if (E) go(E.cur - 1); break;
      case 'next': if (E) go(E.cur + 1); break;
      case 'go': go(+t.getAttribute('data-i')); closeSheet(); break;
      case 'flag': toggleFlag(); break;
      case 'submit': openSubmit(); break;
      case 'final-submit': finalSubmit(t); break;
      case 'retry-submit':
        closeModal();
        if (E) { E.hold = false; submit(t.getAttribute('data-reason') || 'manual'); }
        break;
      case 'jump': closeModal(); go(+t.getAttribute('data-i')); break;
      case 'modal-close': closeModal(); break;
      case 'sheet-open': clearToasts(); el.layer.classList.add('is-sheet'); break;
      case 'sheet-close': closeSheet(); break;
      case 'fs-': fontStep(-1); break;
      case 'fs+': fontStep(1); break;
      case 'banner-close':
        var b = t.closest('.ex-banner');
        if (b && b.parentNode) b.parentNode.removeChild(b);
        break;
    }
  });

  document.addEventListener('change', function (ev) {
    var t = ev.target;
    if (!t || !t.getAttribute) return;
    if (t.hasAttribute('data-pledge')) { syncStart(0); errBox($('exPledgeErr'), ''); }
    if (t.id === 'exOnlyEmpty' && E) { E.onlyEmpty = t.checked; renderGrid(); }
  });

  document.addEventListener('keydown', function (ev) {
    if (!el.modal.hidden) {
      if (ev.key === 'Escape' && modalState && !modalState.lock) { ev.preventDefault(); closeModal(); }
      return;
    }
    if (!E) return;
    var k = ev.key || '', code = ev.code || '';
    if ((ev.ctrlKey || ev.metaKey) && /^(KeyP|KeyS|KeyC|KeyX|KeyA|KeyU)$/.test(code)) {
      ev.preventDefault();
      toast('시험 중에는 복사·저장·인쇄 기능을 사용할 수 없습니다.', 'warn', 2600);
      return;
    }
    if (ev.ctrlKey || ev.metaKey || ev.altKey || E.submitting) return;
    var tag = ev.target && ev.target.tagName ? ev.target.tagName : '';
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag) && ev.target.type !== 'checkbox') return;
    var m = /^(?:Digit|Numpad)([1-4])$/.exec(code);
    if (m || /^[1-4]$/.test(k)) { ev.preventDefault(); pick(+(m ? m[1] : k)); }
    else if (k === 'ArrowLeft') { ev.preventDefault(); go(E.cur - 1); }
    else if (k === 'ArrowRight') { ev.preventDefault(); go(E.cur + 1); }
    else if (code === 'KeyF' || k === 'f' || k === 'F') { ev.preventDefault(); toggleFlag(); }
    else if (k === 'Escape') closeSheet();
  });

  // 문항 보호: 시험 화면에서 복사·잘라내기·우클릭·끌기·선택 막기
  ['copy', 'cut', 'contextmenu', 'dragstart', 'selectstart'].forEach(function (type) {
    el.layer.addEventListener(type, function (ev) {
      if (!E) return;
      ev.preventDefault();
      if (type === 'copy' || type === 'cut') toast('평가 문항은 복사할 수 없습니다.', 'warn', 2400);
    });
  });

  // 화면 이탈 기록: 다른 탭·창으로 이동한 뒤 돌아오면 1회로 셉니다
  function showBanner(id, tone, icon, text, sticky) {
    var box = $('exBanners');
    if (!box) return;
    var old = $('exBn-' + id);
    if (old) old.parentNode.removeChild(old);
    var d = document.createElement('div');
    d.className = 'ex-banner ex-banner--' + tone;
    d.id = 'exBn-' + id;
    d.setAttribute('role', 'alert');
    d.innerHTML = ico(icon) + '<span>' + esc(text) + '</span>' +
      (sticky ? '' : '<button type="button" data-act="banner-close" aria-label="안내 닫기">' + ico('x') + '</button>');
    box.insertBefore(d, box.firstChild);
  }
  function hideBanner(id) { var o = $('exBn-' + id); if (o && o.parentNode) o.parentNode.removeChild(o); }
  function away() {
    if (!E || E.done || E.submitting || E.away) return;
    if (E.unloadAt && Date.now() - E.unloadAt < 2500) return;
    E.away = true;
    E.blur++;
    backup();
  }
  function back() {
    if (!E || !E.away) return;
    E.away = false;
    var b = $('exBlur');
    if (b) b.textContent = E.blur;
    showBanner('blur', 'warn', 'alert-triangle', '화면 이탈이 기록되었습니다 (총 ' + E.blur + '회). 응시 중에는 시험 화면을 벗어나지 마십시오.');
    toast('화면 이탈이 기록되었습니다.', 'warn');
    markDirty();
  }
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') away(); else if (document.hasFocus()) back();
  });
  window.addEventListener('blur', away);
  window.addEventListener('focus', back);

  function netState(online) {
    var nb = $('exNetBox'), nv = $('exNet');
    if (nb) nb.classList.toggle('is-off', !online);
    if (nv) nv.textContent = online ? '정상' : '끊김';
    if (online) hideBanner('net');
    else {
      showBanner('net', 'danger', 'wifi-off', '인터넷 연결이 끊겼습니다. 답안은 이 기기에 임시 보관되며, 연결되면 자동으로 저장됩니다. 창을 닫지 마십시오.', true);
      setSave('offline');
    }
  }
  window.addEventListener('offline', function () { if (E) netState(false); });
  window.addEventListener('online', function () {
    if (!E) return;
    netState(true);
    toast('인터넷에 다시 연결되었습니다. 답안을 저장합니다.', 'ok');
    doSave();
  });

  // 시험 중 페이지를 떠나려 하면 경고하고, 저장되지 않은 답안은 가능한 범위에서 전송
  window.addEventListener('beforeunload', function (ev) {
    if (!E || E.done) return;
    E.unloadAt = Date.now();
    backup();
    ev.preventDefault();
    ev.returnValue = '';
    return '';
  });
  window.addEventListener('pagehide', function () {
    if (!E || E.done || S.demo || !CFG.api || !navigator.sendBeacon || E.rev <= E.savedRev) return;
    try {
      var p = payload();
      p.action = 'save';
      p.token = S.session.token;
      navigator.sendBeacon(CFG.api, new Blob([JSON.stringify(p)], { type: 'text/plain;charset=utf-8' }));
    } catch (e) { /* 무시 */ }
  });

  window.addEventListener('hashchange', function () {
    if (E) {
      setHash('exam/' + courseKey(E.course));
      toast('시험 중에는 다른 화면으로 이동할 수 없습니다. 답안을 제출한 뒤 이동해 주십시오.', 'warn');
      return;
    }
    if (S.session && S.data) route(parseHash());
  });

  /* ---------------------------------------------------------------- 14. 시작 */
  function init() {
    bindLogin();
    startClock();
    if (/[?&]demo=1(&|$)/.test(location.search) || CFG.demo === true) return enterDemo();
    var sess = sget(KEY.session);
    if (sess && sess.token && CFG.api) {
      S.session = sess;
      checkSys();
      return restore();
    }
    showLogin();
  }
  init();
})();
