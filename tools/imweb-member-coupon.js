/* =============================================================================
   성균관컨설팅(아임웹) 위원 추천 쿠폰 만들기 도우미
   -----------------------------------------------------------------------------
   새 캠페인위원이 생기면 위원 코드와 같은 코드의 쿠폰을 만들어야 명함 [커리어 시작하기]로
   들어온 주문서에 할인이 자동 적용됩니다(Footer Code 가 쿠폰 칸에 위원 코드를 넣음).

   쓰는 법 (Claude 브라우저 창, 아임웹 관리자 로그인 상태)
   1) https://skkc.co.kr/admin/promotion/coupon 을 연다.
   2) 이 파일 내용을 그 탭에서 자바스크립트로 실행해 window.__runCoupon 을 만든다.
   3) await window.__runCoupon('위원 추천 할인 (YIH0881 유인호)', 'YIH0881')
      → { created: true } 이면 완료. 여러 명이면 차례로 await.
   4) 목록에서 '쿠폰코드(단일) · 진행 중' 으로 보이는지 확인하고, 주문서 금액 계산으로도 확인.

   쿠폰 설정 (2026.09.26 사용자와 정한 값, 13개 모두 같음)
   - 쿠폰 코드 생성 · 발행 대상 회원 및 비회원 · 쿠폰 수량 단일 생성(코드 = 위원 코드)
   - 비율 할인 10% · 최소 주문 10원 · 최대 100,000원 · 단독으로만 사용
   - 적용 범위 특정 상품: [한국AI윤리위원회] AI윤리전문가 양성과정
   - 사용 기한 제한 없음 · 사용 횟수 제한 없음
   주의: '여러 개 생성'으로 만들면 코드가 무작위라 위원 코드로 적용되지 않음.
         수정 화면에서는 쿠폰 수량 방식이 잠겨 바꿀 수 없으니 새로 만들어야 함.
   ========================================================================== */
window.__runCoupon = async function (NAME, CODE) {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  const setVal = (el, v) => { el.focus(); setter.call(el, v); el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); el.blur(); };
  const lbl = r => ((r.closest('label') || {}).textContent || '').trim();
  const clickRadio = r => (r.closest('label') || r).click();
  const waitFor = async (fn, ms = 10000) => { const t = Date.now(); while (Date.now() - t < ms) { const v = fn(); if (v) return v; await sleep(150); } return null; };

  /* 같은 탭 안에서 새 쿠폰 폼 열기 (쿠폰 만들기 > 일반 쿠폰 만들기 > 쿠폰 코드 생성 과 같은 화면) */
  if (!/\/admin\/promotion\/coupon\/new/.test(location.pathname)) {
    history.pushState({}, '', '/admin/promotion/coupon/new?type=create');
    window.dispatchEvent(new PopStateEvent('popstate', {state: {}}));
  }
  const nameIn = await waitFor(() => { const e = document.querySelector('main input[placeholder="쿠폰명을 입력해 주세요"]'); return e && !e.value ? e : null; });
  if (!nameIn) return 'no empty form';
  await sleep(400);
  setVal(nameIn, NAME);
  clickRadio(document.querySelector('main input[type=radio][value=all]')); await sleep(200);            // 회원 및 비회원
  const one = document.querySelector('main input[type=radio][value=createOne]'); if (!one.checked) clickRadio(one); await sleep(200);
  const codeIn = [...document.querySelectorAll('main input')].find(e => /직접 쿠폰 코드/.test(e.placeholder || ''));
  setVal(codeIn, CODE);
  clickRadio(document.querySelector('main input[type=radio][value=percent]')); await sleep(400);        // 비율 할인
  const pr = document.querySelector('main input[type=radio][value=percent]');
  let box = pr.parentElement; while (box && !box.querySelector('input[name="benefitSetting.rateDiscount.maximumDiscountPrice"]')) box = box.parentElement;
  const rateIn = [...box.querySelectorAll('input')].find(e => /비율을/.test(e.placeholder || ''));
  setVal(rateIn, '10');
  setVal(box.querySelector('input[name="benefitSetting.rateDiscount.minimumOrderPrice"]'), '10');
  setVal(box.querySelector('input[name="benefitSetting.rateDiscount.maximumDiscountPrice"]'), '100000');
  clickRadio([...box.querySelectorAll('input[type=radio][value=product]')][0]); await sleep(500);        // 특정 상품
  const search = await waitFor(() => [...box.querySelectorAll('input[type=text]')].find(e => /상품명 혹은/.test(e.placeholder || '')));
  if (!search) return 'no search';
  search.focus(); search.click();
  setter.call(search, 'AI윤리전문가'); search.dispatchEvent(new Event('input', {bubbles: true}));
  const row = await waitFor(() => [...document.querySelectorAll('label, li, div')].reverse().find(e => e.children.length < 8 && /\[한국AI윤리위원회\] AI윤리전문가 양성과정/.test(e.textContent || '') && e.querySelector('input[type=checkbox]')));
  if (!row) return 'no product row';
  const cb = row.querySelector('input[type=checkbox]');
  if (!cb.checked) (cb.closest('label') || cb).click();
  await sleep(300);
  const add = await waitFor(() => [...document.querySelectorAll('button')].find(b => /^1개 상품 추가$/.test((b.textContent || '').trim()) && !b.disabled));
  if (!add) return 'no add button';
  add.click(); await sleep(600);
  clickRadio([...document.querySelectorAll('main input[type=radio]')].find(r => r.value === 'none' && /^제한 없음사용 기한/.test(lbl(r)))); await sleep(300);  // 사용 기한 제한 없음
  clickRadio([...document.querySelectorAll('main input[type=radio]')].find(r => r.value === 'none' && lbl(r) === '제한 없음')); await sleep(300);           // 사용 횟수 제한 없음

  const q = s => document.querySelector(s);
  const R = [...document.querySelectorAll('main input[type=radio]')];
  const st = {
    name: nameIn.value, code: codeIn.value, target: q('main input[type=radio][value=all]').checked, one: q('main input[type=radio][value=createOne]').checked,
    percent: q('main input[type=radio][value=percent]').checked, rate: rateIn.value,
    min: box.querySelector('input[name="benefitSetting.rateDiscount.minimumOrderPrice"]').value,
    max: box.querySelector('input[name="benefitSetting.rateDiscount.maximumDiscountPrice"]').value,
    only: [...box.querySelectorAll('input[type=radio][value=only]')][0].checked,
    scopeProduct: [...box.querySelectorAll('input[type=radio][value=product]')][0].checked,
    products: [...box.querySelectorAll('*')].filter(e => e.children.length === 0 && /AI윤리전문가 양성과정/.test(e.textContent || '')).length,
    dateNone: R.find(r => r.value === 'none' && /^제한 없음사용 기한/.test(lbl(r))).checked,
    useNone: R.find(r => r.value === 'none' && lbl(r) === '제한 없음').checked
  };
  const ok = st.name === NAME && st.code === CODE && st.target && st.one && st.percent && st.rate === '10' && st.min === '10' &&
    st.max === '100,000' && st.only && st.scopeProduct && st.products === 1 && st.dateNone && st.useNone;
  if (!ok) return {created: false, st};   // 하나라도 다르면 저장하지 않음
  [...document.querySelectorAll('button')].find(x => (x.textContent || '').trim() === '쿠폰 생성').click();
  const listed = await waitFor(() => !/\/new/.test(location.pathname) && document.body.innerText.includes(NAME), 12000);
  return {created: !!listed, code: CODE};
};
