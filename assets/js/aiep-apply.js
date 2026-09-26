/* KAIEC AIEP application: explicit payment step, no unverified receipt claim. */
(function () {
  'use strict';
  var form = document.getElementById('examForm');
  if (!form) return;
  var submit = form.querySelector('[type="submit"]');
  var status = document.getElementById('applyStatus');
  var done = document.getElementById('doneView');
  var copy = document.getElementById('doneCopy');
  var copyButton = document.getElementById('copyBtn');
  var busy = false;
  var submitted = false;
  var originalButtonText = submit.textContent;
  var timeoutMs = 15000;

  function value(name) {
    var field = form.elements.namedItem(name);
    return field && field.value ? field.value.trim() : '';
  }
  function setError(name, message) {
    var field = form.elements.namedItem(name);
    var error = document.getElementById(name + 'Error');
    field.setAttribute('aria-invalid', message ? 'true' : 'false');
    error.textContent = message || '';
    error.hidden = !message;
    return message ? field : null;
  }
  function announce(message, isError) {
    status.textContent = message;
    status.classList.toggle('is-error', !!isError);
  }
  ['name', 'email', 'privok'].forEach(function (name) {
    var field = form.elements.namedItem(name);
    field.addEventListener('input', function () { setError(name, ''); });
    field.addEventListener('change', function () { setError(name, ''); });
  });

  async function requestSubmission(payload) {
    var endpoint = form.getAttribute('data-endpoint');
    if (!endpoint || typeof fetch !== 'function') throw new Error('unavailable');
    var controller = typeof AbortController === 'function' ? new AbortController() : null;
    var timer;
    var timeout = new Promise(function (_, reject) {
      timer = setTimeout(function () {
        if (controller) controller.abort();
        reject(new Error('timeout'));
      }, timeoutMs);
    });
    async function send() {
      var response = await fetch(endpoint, {
          method: 'POST', mode: 'no-cors', cache: 'no-store', redirect: 'follow',
          body: new URLSearchParams(payload),
          signal: controller ? controller.signal : undefined
        });
      // Cross-origin no-cors responses intentionally expose no receipt details.
      if (!response || typeof response.status !== 'number') throw new Error('invalid-response');
      if (response.type === 'opaque' && response.status === 0) return;
      if (!response.ok || response.status < 200 || response.status >= 300) throw new Error('http-error');
      if (typeof response.text !== 'function') throw new Error('invalid-response');
      var result = (await response.text()).trim().toLowerCase();
      if (result !== 'ok' && result !== 'duplicate') throw new Error('not-accepted');
    }
    try {
      await Promise.race([send(), timeout]);
    } finally {
      clearTimeout(timer);
    }
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (busy || submitted) return;
    var name = value('name');
    var email = value('email');
    var errors = [
      setError('name', name ? '' : '성명을 입력해 주세요.'),
      setError('email', /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) ? '' : '이메일 주소를 확인해 주세요.'),
      setError('privok', form.elements.namedItem('privok').checked ? '' : '개인정보 수집·이용 동의가 필요합니다.')
    ].filter(Boolean);
    if (errors.length) {
      announce('입력 내용을 확인해 주세요. 표시된 항목을 수정하면 계속할 수 있습니다.', true);
      errors[0].focus();
      return;
    }
    var payload = {
      course: form.getAttribute('data-course'), name: name, email: email,
      job: value('job'), purpose: value('purpose')
    };
    busy = true;
    submit.disabled = true;
    form.setAttribute('aria-busy', 'true');
    submit.textContent = '신청정보 전송 중…';
    announce('신청정보를 전송하고 있습니다. 잠시만 기다려 주세요.', false);
    try {
      await requestSubmission(payload);
      submitted = true;
      copy.value = [
        '한국AI윤리위원회 AI윤리전문가 양성과정 신청정보', '',
        '성명: ' + name, '이메일: ' + email,
        '과정: ' + payload.course,
        '직업·활동 분야: ' + (payload.job || '미입력'),
        '활용 목적: ' + (payload.purpose || '미입력'),
        '개인정보 수집·이용: 동의'
      ].join('\n');
      document.getElementById('paymentEmail').textContent = email;
      form.hidden = true;
      done.hidden = false;
      document.getElementById('doneTitle').focus();
    } catch (error) {
      announce('신청정보 전송을 확인하지 못했습니다. 입력 내용은 그대로 보관되어 있습니다. 인터넷 연결을 확인한 뒤 다시 시도해 주세요. 이미 전송되었을 수도 있으므로 문제가 반복되면 사무국으로 문의해 주세요.', true);
      submit.focus();
    } finally {
      busy = false;
      submit.disabled = false;
      form.removeAttribute('aria-busy');
      submit.textContent = originalButtonText;
    }
  });

  copyButton.addEventListener('click', async function () {
    copyButton.disabled = true;
    var success = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(copy.value);
        success = true;
      }
    } catch (_) { /* Try local selection below when clipboard permission is denied. */ }
    if (!success) {
      copy.hidden = false;
      copy.focus();
      copy.select();
      try { success = document.execCommand('copy'); } catch (_) { success = false; }
    }
    document.getElementById('copyStatus').textContent = success
      ? '신청정보가 복사되었습니다.'
      : '자동 복사가 지원되지 않습니다. 아래 선택된 내용을 직접 복사해 주세요.';
    copyButton.disabled = false;
    if (success) { copy.hidden = true; copyButton.focus(); }
  });
})();
