/* Browser regression tests. All requests are mocked; no form data leaves this process.
   Set AIEP_TEST_HTML to a rendered proposal fixture before the site is rebuilt.
   NODE_PATH may point to the bundled runtime's node_modules directory. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(process.env.AIEP_TEST_HTML || path.join(root, 'expert-apply/index.html'), 'utf8');
const script = fs.readFileSync(path.join(root, 'assets/js/aiep-apply.js'), 'utf8');

(async function () {
  const browser = await chromium.launch({
    ...(process.env.AIEP_TEST_BROWSER ? { executablePath: process.env.AIEP_TEST_BROWSER } : {}),
    headless: true
  });
  let passed = 0;
  async function scenario(name, mock, test) {
    const page = await browser.newPage();
    try {
      await page.route('**/*', route => route.abort());
      // The dedicated script is added exactly once; strip every source/inline script.
      await page.setContent(html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ''));
      await page.evaluate(mode => {
        window.calls = [];
        window.fetch = function (url, options) {
          window.calls.push({ url: String(url), method: options.method, mode: options.mode,
            body: Object.fromEntries(options.body.entries()) });
          if (mode === 'network') return Promise.reject(new TypeError('Failed to fetch'));
          if (mode === 'timeout') return new Promise(() => {});
          if (mode === 'body-timeout') return Promise.resolve({ type: 'basic', status: 200, ok: true,
            text: () => new Promise(() => {}) });
          if (mode === 'missing') return Promise.resolve({ type: 'opaque' });
          if (mode === 'http') return Promise.resolve({ type: 'basic', status: 500, ok: false });
          if (mode === 'server') return Promise.resolve({ type: 'basic', status: 200, ok: true,
            text: async () => 'error: spreadsheet is unavailable' });
          if (mode === 'ok') return Promise.resolve({ type: 'basic', status: 200, ok: true, text: async () => 'ok' });
          if (mode === 'pending') return new Promise(resolve => { window.finishRequest = () => resolve({ type: 'opaque', status: 0 }); });
          return Promise.resolve({ type: 'opaque', status: 0 });
        };
        if (mode === 'timeout' || mode === 'body-timeout') {
          const nativeTimeout = window.setTimeout.bind(window);
          window.setTimeout = (fn, ms, ...args) => nativeTimeout(fn, ms === 15000 ? 25 : ms, ...args);
        }
      }, mock);
      await page.addScriptTag({ content: script });
      await test(page);
      passed++;
      console.log('PASS ' + name);
    } finally { await page.close(); }
  }
  async function fill(page) {
    await page.locator('[name=name]').fill('신청 테스트');
    await page.locator('[name=email]').fill('test@example.invalid');
    await page.locator('[name=privok]').check({ force: true });
  }
  async function send(page) {
    await page.locator('#examForm').evaluate(f => f.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  }
  async function expectFailure(page) {
    await page.waitForFunction(() => document.getElementById('applyStatus').textContent.includes('전송을 확인하지 못했습니다'));
    assert.equal(await page.locator('#examForm').evaluate(f => f.hidden), false);
    assert.equal(await page.locator('#doneView').evaluate(f => f.hidden), true);
    assert.equal(await page.locator('[name=email]').inputValue(), 'test@example.invalid');
    assert.equal(await page.locator('#examForm [type=submit]').isDisabled(), false);
  }
  try {
    await scenario('invalid fields announce errors and focus first input', 'opaque', async page => {
      await send(page);
      assert.equal(await page.evaluate(() => window.calls.length), 0);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'f-name');
      assert.equal(await page.locator('[name=name]').getAttribute('aria-invalid'), 'true');
      await page.locator('[name=name]').fill('신청 테스트');
      await page.locator('[name=email]').fill('incorrect');
      await send(page);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'f-email');
      assert.equal(await page.locator('[name=privok]').getAttribute('aria-invalid'), 'true');
    });
    await scenario('minimal required fields send POST; opaque stays unconfirmed; no auto navigation', 'opaque', async page => {
      await fill(page); await send(page);
      await page.waitForFunction(() => !document.getElementById('doneView').hidden);
      const calls = await page.evaluate(() => window.calls);
      assert.equal(calls.length, 1); assert.equal(calls[0].method, 'POST');
      assert.equal(calls[0].mode, 'no-cors'); assert.equal(calls[0].body.job, '');
      assert.equal(calls[0].body.purpose, ''); assert.equal(calls[0].url.includes('test%40'), false);
      assert.equal(await page.locator('#doneTitle').innerText(), '교육비 결제를 진행해 주세요');
      assert.equal((await page.locator('#doneView').innerText()).includes('신청정보 전송을 요청했습니다'), true);
      assert.equal((await page.locator('#doneView').innerText()).includes('최종 수강 등록은 결제 확인 후 확정됩니다'), true);
      assert.equal(await page.locator('#paymentEmail').innerText(), 'test@example.invalid');
      const before = page.url(); await page.waitForTimeout(3250); assert.equal(page.url(), before);
      assert.equal(await page.evaluate(() => window.calls.length), 1);
    });
    await scenario('duplicate submissions while request pending are ignored', 'pending', async page => {
      await fill(page); await send(page); await send(page);
      assert.equal(await page.evaluate(() => window.calls.length), 1);
      assert.equal(await page.locator('#examForm [type=submit]').isDisabled(), true);
      await page.evaluate(() => window.finishRequest());
      await page.waitForFunction(() => !document.getElementById('doneView').hidden);
      await send(page); assert.equal(await page.evaluate(() => window.calls.length), 1);
    });
    for (const mode of ['network', 'timeout', 'body-timeout', 'missing', 'http', 'server']) {
      await scenario(mode + ' failure preserves input and blocks payment step', mode, async page => {
        await fill(page); await send(page); await expectFailure(page);
      });
    }
    await scenario('explicit ok response also requires deliberate payment action', 'ok', async page => {
      await fill(page); await send(page);
      await page.waitForFunction(() => !document.getElementById('doneView').hidden);
      assert.equal(await page.locator('#payBtn').getAttribute('href'), 'https://skkc.co.kr/shop_view?idx=26');
    });
    await scenario('clipboard denial reports failure and exposes selectable text', 'opaque', async page => {
      await fill(page); await send(page);
      await page.waitForFunction(() => !document.getElementById('doneView').hidden);
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'clipboard', { configurable: true,
          value: { writeText: async () => { throw new Error('denied'); } } });
        document.execCommand = () => false;
      });
      await page.locator('#copyBtn').click();
      assert.equal((await page.locator('#copyStatus').innerText()).includes('자동 복사가 지원되지 않습니다'), true);
      assert.equal(await page.locator('#doneCopy').evaluate(e => e.hidden), false);
    });
    await scenario('clipboard success is announced only after write resolves', 'opaque', async page => {
      await fill(page); await send(page);
      await page.waitForFunction(() => !document.getElementById('doneView').hidden);
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'clipboard', { configurable: true,
          value: { writeText: () => new Promise(resolve => { window.finishCopy = resolve; }) } });
      });
      await page.locator('#copyBtn').click();
      assert.equal(await page.locator('#copyStatus').innerText(), '');
      await page.evaluate(() => window.finishCopy());
      await page.waitForFunction(() => document.getElementById('copyStatus').textContent.includes('복사되었습니다'));
      assert.equal(await page.locator('#copyBtn').isDisabled(), false);
    });
    console.log('All ' + passed + ' browser checks passed; no external request was sent.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
