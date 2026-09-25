const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { join } = require('node:path');
const { tmpdir } = require('node:os');
const url = 'http://127.0.0.1:8769/' + encodeURIComponent('随想') + '/';
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    let apiCalls = 0;
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => { if (/\/auth\/|\/admin\/posts/.test(request.url())) apiCalls++; });
    await page.route('**/*', route => route.request().url().startsWith('http://127.0.0.1:8769/')
      ? route.continue() : route.abort());
    await page.goto(url, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('.thoughts-card').count(), 138);
    assert.equal(await page.locator('.thoughts-card:visible').count(), 12);
    assert.equal(await page.locator('#thoughts-login').count(), 0);
    assert.equal(await page.locator('.thoughts-card time').first().textContent(), '2026-09-25');
    await page.screenshot({ path: join(tmpdir(), 'thoughts-static-desktop.png'), fullPage: false });
    await page.locator('#thoughts-more').click();
    assert.equal(await page.locator('.thoughts-card:visible').count(), 24);
    await page.locator('#thoughts-month').selectOption('2025-12');
    assert.equal(await page.locator('.thoughts-card:visible').count(), 12);
    assert.equal(await page.locator('.thoughts-card:visible').evaluateAll(es => es.every(e => e.dataset.month === '2025-12')), true);
    await page.locator('.thoughts-card:visible h2 a').first().click();
    await page.waitForSelector('.thought-post');
    assert.match(await page.locator('.thought-post').innerText(), /今天完成了/);
    await page.locator('.thought-back').click();
    await page.waitForSelector('#thoughts-month');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('#thoughts-month').selectOption('2025-09');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: join(tmpdir(), 'thoughts-static-mobile.png') });
    await page.locator('label[for="__palette_1"]').click();
    await page.waitForFunction(() => document.body.dataset.mdColorScheme === 'default');
    await page.waitForTimeout(1000); // Wait for the existing .75s background crossfade.
    await page.screenshot({ path: join(tmpdir(), 'thoughts-static-mobile-light.png') });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    const context = await browser.newContext({ javaScriptEnabled: false });
    const plain = await context.newPage();
    await plain.goto(url, { waitUntil: 'domcontentloaded' });
    assert.equal(await plain.locator('.thoughts-card:visible').count(), 138);
    await context.close();
    assert.equal(apiCalls, 0);
    assert.deepEqual(errors, []);
    console.log('PASS: static cards, sorting, pagination, month filter, article/back links, mobile, light theme, no-JS, no auth API');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
