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
    let posts = [], sequence = 0, sessionValid = false, failPublic = false;
    let githubRequests = 0;
    await page.route('**/*', async route => {
      const request = route.request();
      if (request.url().includes('/login/oauth')) githubRequests++;
      if (request.url().startsWith(api)) {
        const path = new URL(request.url()).pathname;
        const method = request.method();
        const auth = sessionValid && request.headers().authorization === 'Bearer test-only';
        let body = {}, status = 200;
        if (path === '/auth/login') {
          const valid = request.postDataJSON().password === 'browser-test-password-1234';
          status = valid ? 200 : 401;
          sessionValid = valid;
          body = valid ? { token: 'test-only' } : { detail: '管理密码不正确' };
        }
        else if (path === '/auth/me') { status = auth ? 200 : 401; }
        else if (path === '/auth/logout') { status = 204; sessionValid = false; }
        else if (method === 'GET') {
          if (path === '/admin/posts' && !auth) { status = 401; body = { detail: '请先输入管理密码解锁' }; }
          else if (failPublic && path === '/posts') { status = 503; body = { detail: 'temporary offline' }; }
          else body = { items: posts.filter(p => auth || p.status === 'published'), next: null };
        }
        else if (!auth) { status = 401; body = { detail: '请先输入管理密码解锁' }; }
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
    await page.goto(url, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('#thoughts-owner').isVisible(), false);
    await page.locator('#thoughts-login').click();
    await page.locator('#thoughts-password').fill('wrong');
    await page.locator('#thoughts-unlock button[type=submit]').click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent === '管理密码不正确');
    assert.equal(await page.locator('#thoughts-owner').isVisible(), false);
    assert.equal(await page.locator('#thoughts-password').inputValue(), '');
    await page.locator('#thoughts-password').fill('browser-test-password-1234');
    await page.screenshot({ path: join(tmpdir(), 'thoughts-unlock-test.png') });
    await page.locator('#thoughts-unlock button[type=submit]').click();
    await page.locator('#thoughts-new').waitFor();
    assert.equal(await page.locator('#thoughts-unlock').isVisible(), false);
    assert.equal(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }).includes('browser-test-password-1234')), false);
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
    // A separate reader never sees a draft and has no write controls.
    posts.push({ id: 'public-fixture', title: '公开内容', body: '读者可以看见', status: 'published', created_at: 1790000000 });
    posts.push({ id: 'private-fixture', title: '服务端私密草稿', body: '仅管理可见', status: 'draft', created_at: 1790000000, version: 1 });
    await page.reload({ waitUntil: 'networkidle' });
    assert.equal(await page.locator('.thoughts-card').count(), 1);
    assert.equal(await page.locator('.thoughts-card button').count(), 0);
    assert.equal(await page.locator('#thoughts-feed').innerText().then(t => t.includes('服务端私密草稿')), false);
    await page.locator('#thoughts-login').click();
    await page.locator('#thoughts-password').fill('browser-test-password-1234');
    await page.locator('#thoughts-unlock button[type=submit]').click();
    await page.waitForFunction(() => document.querySelectorAll('.thoughts-card').length === 2);
    await page.screenshot({ path: join(tmpdir(), 'thoughts-mobile-unlocked-test.png') });
    // Expiry must remove private cards immediately, not leave them behind after a failed request.
    sessionValid = false; failPublic = true;
    await page.locator('.thoughts-card button', { hasText: '删除' }).first().click();
    await page.waitForFunction(() => document.querySelector('#thoughts-status').textContent.includes('请先输入管理密码'));
    assert.equal(await page.locator('#thoughts-owner').isVisible(), false);
    assert.equal(await page.locator('.thoughts-card').count(), 0);
    assert.equal(await page.evaluate(() => sessionStorage.getItem('notes.thoughts.https://thoughts.test.token')), null);
    assert.equal(githubRequests, 0);
    assert.deepEqual(errors, []);
    console.log('PASS: password login, read-only access, draft privacy, CRUD, recovery, mobile, light theme, logout, expiry');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
