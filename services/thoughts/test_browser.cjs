/* UI-only fixtures: never shipped to docs/ or written to the real API. */
const assert = require('node:assert/strict');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url = 'http://localhost:8769/' + encodeURIComponent('随想') + '/';
const api = 'https://thoughts.test';

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    let posts = [], sequence = 0;
    await page.route('**/*', async route => {
      const request = route.request();
      if (request.url().startsWith(api)) {
        const path = new URL(request.url()).pathname;
        const method = request.method();
        const auth = request.headers().authorization === 'Bearer test-only';
        let body = {}, status = 200;
        if (path === '/auth/me') { status = auth ? 200 : 401; }
        else if (path === '/auth/logout') { status = 204; }
        else if (method === 'GET') body = { items: posts.filter(p => auth || p.status === 'published'), next: null };
        else if (!auth) status = 401;
        else if (method === 'DELETE') posts = posts.filter(p => path !== '/posts/' + p.id);
        else {
          const payload = request.postDataJSON();
          if (method === 'POST') {
            body = { ...payload, id: String(++sequence), version: 1, created_at: 1790000000, published_at: payload.status === 'published' ? 1790000000 : null };
            posts.unshift(body);
          } else {
            const p = posts.find(p => path === '/posts/' + p.id);
            Object.assign(p, payload, { version: p.version + 1 }); body = p;
          }
        }
        await route.fulfill({ status, contentType: 'application/json', body: status === 204 ? '' : JSON.stringify(body), headers: { 'Access-Control-Allow-Origin': 'http://localhost:8769' } });
      } else if (request.isNavigationRequest() && request.url().startsWith(url)) {
        const response = await route.fetch();
        await route.fulfill({ response, body: (await response.text()).replace('data-api=""', `data-api="${api}"`) });
      } else await route.continue();
    });
    await page.addInitScript(() => sessionStorage.setItem('notes.thoughts.https://thoughts.test.token', 'test-only'));
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.locator('#thoughts-new').click();
    await page.locator('#thoughts-title').fill('测试标题（仅自动化测试）');
    await page.locator('#thoughts-body').fill('<img src=x onerror=alert(1)>\n第一段\n第二段');
    await page.locator('button[value="draft"]').click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent.includes('草稿已保存'));
    assert.equal(posts[0].status, 'draft');
    assert.equal(await page.locator('.thoughts-card img').count(), 0);
    await page.locator('.thoughts-card button', { hasText: '编辑' }).click();
    await page.locator('#thoughts-body').fill('仅供自动化测试的随想。\n换行保留，卡片正文不执行 HTML。');
    await page.locator('button[value="published"]').click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent === '已发布。');
    assert.equal(posts[0].status, 'published');
    await page.locator('#thoughts-new').click();
    await page.locator('#thoughts-body').fill('本地暂存恢复测试');
    await page.reload({ waitUntil: 'networkidle' });
    assert.equal(await page.locator('#thoughts-body').inputValue(), '本地暂存恢复测试');
    await page.locator('#thoughts-cancel').click();
    await page.locator('#thoughts-new').click();
    assert.equal(await page.locator('#thoughts-body').inputValue(), '本地暂存恢复测试');
    await page.screenshot({ path: join(tmpdir(), 'thoughts-editor-test.png') });
    await page.evaluate(() => document.body.setAttribute('data-md-color-scheme', 'default'));
    assert.notEqual(await page.locator('#thoughts-body').evaluate(e => getComputedStyle(e).color), 'rgb(255, 255, 255)');
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: join(tmpdir(), 'thoughts-mobile-test.png') });
    await page.locator('#thoughts-cancel').click();
    page.on('dialog', dialog => dialog.accept());
    await page.locator('.thoughts-card button', { hasText: '删除' }).click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent === '已删除。');
    assert.equal(posts.length, 0);
    await page.locator('#thoughts-logout').click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent.startsWith('已退出'));
    assert.equal(await page.locator('#thoughts-editor').isVisible(), false);
    assert.equal(await page.locator('#thoughts-login').isVisible(), true);
    assert.deepEqual(errors, []);
    console.log('PASS: editor, draft, publish, edit, safe text, recovery, mobile, light theme, delete, logout');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
