/* 한국AI윤리위원회 (KAIEC): 위원 참여 신청 */
(function () {
  'use strict';

  var form = document.getElementById('joinForm');
  if (!form) return;
  var hook = form.getAttribute('data-webhook') || '';
  var contact = form.getAttribute('data-contact') || '';
  var submit = form.querySelector('[type=submit]');
  var topErr = document.getElementById('topErr');
  var done = document.getElementById('doneView');
  var doneTitle = document.getElementById('doneTitle');
  var doneMessage = document.getElementById('doneMessage');
  var doneCopy = document.getElementById('doneCopy');
  var mailHint = document.getElementById('mailHint');
  var attempted = false;
  var ORG_TYPES = { '공식 파트너': 1 };
  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');

  function v(name) {
    var el = form.querySelector('[name=' + name + ']');
    return (el && el.value ? el.value : '').trim();
  }
  function jtype() {
    var selected = form.querySelector('[name=jtype]:checked');
    return selected ? selected.value : '';
  }
  function checked(name) {
    return Array.prototype.map.call(form.querySelectorAll('[name=' + name + ']:checked'), function (el) { return el.value; });
  }
  function bad(id, invalid) {
    var section = document.getElementById(id);
    var error = section.querySelector('.err-msg');
    var groups = { secType: 'jtype', fJob: 'job', secMotive: 'motive', secPriv: 'privok' };
    var controls = section.querySelectorAll(groups[id] ? '[name=' + groups[id] + ']' : 'input, textarea');
    section.classList.toggle('is-invalid', !!invalid);
    if (error && !error.id) error.id = id + 'Error';
    controls.forEach(function (el) {
      if (invalid) el.setAttribute('aria-invalid', 'true');
      else el.removeAttribute('aria-invalid');
      if (!error) return;
      var descriptions = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(function (value) { return value && value !== error.id; });
      if (invalid) descriptions.push(error.id);
      if (descriptions.length) el.setAttribute('aria-describedby', descriptions.join(' '));
      else el.removeAttribute('aria-describedby');
    });
  }
  function focusAt(el) {
    el.focus({ preventScroll: true });
    el.scrollIntoView({ behavior: reducedMotion && reducedMotion.matches ? 'auto' : 'smooth', block: 'center' });
  }

  /* 소속 칸과 기존 참여 구분 딥링크 */
  var orgToggle = document.getElementById('orgToggle');
  var orgBox = document.getElementById('orgBox');
  var orgLabel = document.getElementById('orgLabel');
  var orgIn = form.querySelector('[name=org]');
  function openOrg(isOrg) {
    orgBox.hidden = false;
    orgToggle.hidden = true;
    orgLabel.innerHTML = isOrg ? '기관명 <span class="field-opt">(기관·기업·학교)</span>' : '소속 <span class="field-opt">(선택)</span>';
    orgIn.placeholder = isOrg ? '예: ○○기업 / ○○대학교 / ○○기관' : '예: ○○대학교 / ○○기업 인사팀';
  }
  orgToggle.addEventListener('click', function () { openOrg(false); orgIn.focus(); });
  function syncType() {
    bad('secType', false);
    if (ORG_TYPES[jtype()]) openOrg(true);
    else if (orgToggle.hidden && !orgIn.value) {
      orgLabel.innerHTML = '소속 <span class="field-opt">(선택)</span>';
      orgIn.placeholder = '예: ○○대학교 / ○○기업 인사팀';
    }
  }
  form.querySelectorAll('[name=jtype]').forEach(function (radio) { radio.addEventListener('change', syncType); });
  function pick(type) {
    form.querySelectorAll('[name=jtype]').forEach(function (radio) {
      if (radio.value === type) { radio.checked = true; syncType(); }
    });
  }
  var queryType = new URLSearchParams(location.search).get('type');
  if (queryType) pick(queryType);
  document.querySelectorAll('[data-pick]').forEach(function (link) {
    link.addEventListener('click', function () { pick(link.getAttribute('data-pick')); });
  });

  var msg = form.querySelector('[name=msg]');
  var msgCount = document.getElementById('msgCount');
  msg.addEventListener('input', function () { msgCount.textContent = this.value.length; });
  document.querySelectorAll('#msgQuick button').forEach(function (button) {
    button.addEventListener('click', function () {
      var text = button.textContent.trim();
      var current = msg.value.trim();
      if (current.indexOf(text) >= 0) return;
      msg.value = ((current ? current + ' ' : '') + text).slice(0, msg.maxLength);
      msgCount.textContent = msg.value.length;
      msg.focus();
    });
  });
  var phone = form.querySelector('[name=phone]');
  phone.addEventListener('input', function () {
    var digits = this.value.replace(/[^0-9]/g, '').slice(0, 11);
    if (digits.length < 4) this.value = digits;
    else if (digits.length < 8) this.value = digits.slice(0, 3) + '-' + digits.slice(3);
    else this.value = digits.slice(0, 3) + '-' + digits.slice(3, 7) + '-' + digits.slice(7);
  });

  function showResult(title, message, hideForm) {
    form.hidden = hideForm;
    doneTitle.textContent = title;
    doneMessage.textContent = message;
    done.hidden = false;
    focusAt(doneTitle);
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (attempted) return;
    var digits = v('phone').replace(/[^0-9]/g, '');
    var job = form.querySelector('[name=job]:checked');
    var motives = checked('motive');
    bad('secType', !jtype());
    bad('fName', !v('name'));
    bad('fEmail', !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v('email')));
    bad('fPhone', digits.length > 0 && !(digits.length >= 10 && digits.length <= 11 && digits.slice(0, 2) === '01'));
    bad('fJob', !job);
    bad('secMotive', motives.length === 0);
    bad('secPriv', !form.querySelector('[name=privok]').checked);
    var first = form.querySelector('.is-invalid');
    topErr.style.display = first ? 'block' : 'none';
    if (first) {
      focusAt(first.querySelector('[aria-invalid=true]'));
      return;
    }

    var type = jtype();
    var data = {
      type: 'join', course: '[KAIEC 참여] ' + type, name: v('name'), email: v('email'), phone: v('phone'),
      job: job.value, org: v('org'), motive: motives.join(', '), purpose: v('msg'), t: String(Date.now())
    };
    var lines = ['한국AI윤리위원회 위원 참여 신청', '',
      '■ 참여 구분 : ' + type, '■ 성명 : ' + data.name, '■ 이메일 : ' + data.email,
      '■ 휴대전화 : ' + (data.phone || '(미기재)'), '■ 직업/활동 분야 : ' + data.job, '■ 소속 : ' + (data.org || '(미기재)'),
      '■ 기대하는 것 : ' + data.motive, '■ 지원 사유·자기소개 : ' + data.purpose, '',
      '■ 개인정보 수집·이용 : 동의', '', '--- kaiec.kr 위원 참여 신청 페이지에서 작성됨 ---'];
    doneCopy.value = lines.join('\n');
    attempted = true;
    submit.disabled = true;
    submit.textContent = '전송 중입니다';
    form.setAttribute('aria-busy', 'true');

    if (!hook) {
      form.removeAttribute('aria-busy');
      submit.textContent = '이메일 접수 안내를 확인해 주세요';
      mailHint.textContent = '아래 신청 내용을 복사해 ' + contact + '으로 보내주시면 접수할 수 있습니다.';
      showResult('이메일로 신청 내용을 보내주세요.', '현재 온라인 전송이 연결되어 있지 않습니다. 작성하신 내용은 그대로 보존되어 있습니다.', false);
      return;
    }

    var body = new URLSearchParams();
    Object.keys(data).forEach(function (key) { body.append(key, data[key]); });
    var controller = typeof AbortController === 'function' ? new AbortController() : null;
    var timer;
    try {
      var options = { method: 'POST', mode: 'no-cors', keepalive: true, cache: 'no-store', body: body };
      if (controller) options.signal = controller.signal;
      var response = await Promise.race([
        fetch(hook, options),
        new Promise(function (_, reject) {
          timer = setTimeout(function () {
            var error = new Error('전송 확인 시간 초과');
            error.name = 'TimeoutError';
            reject(error);
            if (controller) controller.abort();
          }, 15000);
        })
      ]);
      if (!response || (response.type !== 'opaque' && !response.ok)) throw new Error('전송 응답 확인 실패');
      /* no-cors 응답은 저장 여부를 읽을 수 없으므로 접수 완료로 표시하지 않습니다. */
      submit.textContent = '전송 요청 완료';
      showResult('참여 신청을 전송 요청했습니다.',
        '전송 요청을 마쳤으나 이 화면에서는 접수 완료 여부를 확인할 수 없습니다. 보통 3~5일 안에 이메일로 검토 안내를 드리며, 안내를 받지 못하셨다면 아래 연락처로 접수 여부를 확인해 주세요.', true);
    } catch (error) {
      submit.textContent = '접수 여부 확인이 필요합니다';
      showResult(error.name === 'TimeoutError' ? '전송 확인 시간이 초과되었습니다.' : '전송 결과를 확인하지 못했습니다.',
        '작성하신 내용은 그대로 보존되어 있습니다. 이미 접수되었을 가능성이 있어 자동으로 다시 보내지 않습니다. 아래 신청 내용 사본과 함께 접수 여부를 문의해 주세요.', false);
    } finally {
      clearTimeout(timer);
      form.removeAttribute('aria-busy');
    }
  });

  var copyButton = document.getElementById('copyBtn');
  var copyStatus = document.getElementById('copyStatus');
  copyButton.addEventListener('click', async function () {
    if (copyButton.disabled) return;
    copyButton.disabled = true;
    copyStatus.textContent = '';
    var copied = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(doneCopy.value);
        copied = true;
      }
    } catch (error) { /* 권한이 거부되면 선택한 내용을 직접 복사할 수 있도록 남깁니다. */ }
    if (!copied) {
      doneCopy.focus();
      doneCopy.select();
      try { copied = document.execCommand('copy'); } catch (error) { copied = false; }
    }
    copyStatus.textContent = copied ? '신청 내용이 복사되었습니다.' : '자동 복사를 사용할 수 없습니다. 선택된 내용을 직접 복사해 주세요.';
    copyButton.disabled = false;
  });
})();
