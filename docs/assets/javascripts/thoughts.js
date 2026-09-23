/* Plain-text posts: user input is never inserted as HTML. */
(() => {
  'use strict';
  const root = document.getElementById('thoughts');
  if (!root) return;
  const api = root.dataset.api.replace(/\/$/, '');
  const el = id => document.getElementById('thoughts-' + id);
  const status = text => { el('status').textContent = text; };
  const node = (tag, text, className) => {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = text;
    if (className) result.className = className;
    return result;
  };
  let token = '', next = null, editing = null, busy = false, loggedIn = false;
  const storageKey = 'notes.thoughts.' + api;
  const storage = {
    get(key) { try { return sessionStorage.getItem(storageKey + key); } catch { return null; } },
    set(key, value) { try { sessionStorage.setItem(storageKey + key, value); return true; } catch { return false; } },
    remove(key) { try { sessionStorage.removeItem(storageKey + key); } catch { /* private browser */ } }
  };
  const draftKey = 'notes.thoughts.draft.' + location.pathname;
  const persist = () => {
    el('count').textContent = el('body').value.length + ' / 20000';
    try {
      localStorage.setItem(draftKey, JSON.stringify({ title: el('title').value, body: el('body').value, editing }));
      el('draft-note').textContent = '已暂存到此浏览器，尚未发布。';
    } catch { el('draft-note').textContent = '浏览器不允许暂存，请及时保存草稿。'; }
  };
  function clearDraft() { try { localStorage.removeItem(draftKey); } catch { /* no storage */ } }
  function ownerUI(value) {
    loggedIn = value;
    el('owner').hidden = !value;
    el('login').hidden = value;
  }
  async function request(path, options = {}) {
    const response = await fetch(api + path, {
      ...options, cache: 'no-store', credentials: 'omit', signal: AbortSignal.timeout(20000),
      headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: 'Bearer ' + token } : {}) }
    });
    if (!response.ok) {
      if (response.status === 401) { token = ''; storage.remove('.token'); ownerUI(false); }
      const data = await response.json().catch(() => ({}));
      throw new Error(typeof data.detail === 'string' ? data.detail : '请求失败，请稍后重试。');
    }
    return response.status === 204 ? null : response.json();
  }
  async function action(work) {
    if (busy) return;
    busy = true;
    root.querySelectorAll('button').forEach(button => { button.disabled = true; });
    try { await work(); }
    catch (error) { status(error.name === 'TimeoutError' || error instanceof TypeError ? '连接服务失败，内容已保留，请稍后重试。' : error.message); }
    finally { busy = false; root.querySelectorAll('button').forEach(button => { button.disabled = false; }); }
  }
  function edit(post = null, restore = false) {
    if (!restore && (el('body').value || el('title').value) && !confirm('切换编辑内容？当前暂存内容将被新的编辑内容覆盖。')) return;
    editing = post && post.id ? { id: post.id, version: post.version } : null;
    el('title').value = post?.title || '';
    el('body').value = post?.body || '';
    el('editor').hidden = false;
    persist();
    el('body').focus();
  }
  function card(post) {
    const article = node('article', undefined, 'thoughts-card');
    article.id = 'post-' + post.id;
    const header = node('header');
    header.append(node('strong', 'Bamb0oChen'));
    const date = new Date((post.published_at || post.created_at) * 1000);
    const time = node('time', date.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }));
    time.dateTime = date.toISOString();
    header.append(time);
    if (post.status === 'draft') header.append(node('span', '草稿 · 仅自己可见'));
    article.append(header);
    if (post.title) article.append(node('h2', post.title));
    article.append(node('p', post.body, 'thoughts-card-body'));
    if (loggedIn) {
      const footer = node('footer');
      const editButton = node('button', '编辑');
      editButton.type = 'button'; editButton.addEventListener('click', () => edit(post));
      const deleteButton = node('button', '删除');
      deleteButton.type = 'button';
      deleteButton.addEventListener('click', () => action(async () => {
        if (!confirm('确定删除这条随想？删除后无法恢复。')) return;
        await request('/posts/' + post.id + '?version=' + post.version, { method: 'DELETE' });
        if (editing?.id === post.id) { el('editor').hidden = true; editing = null; clearDraft(); }
        await load(); status('已删除。');
      }));
      footer.append(editButton, deleteButton); article.append(footer);
    }
    return article;
  }
  async function load(append = false) {
    const result = await request((loggedIn ? '/admin/posts' : '/posts') + (append && next ? '?before=' + encodeURIComponent(next) : ''));
    if (!append) el('feed').replaceChildren();
    result.items.forEach(post => el('feed').append(card(post)));
    next = result.next; el('more').hidden = !next;
    if (!el('feed').children.length) el('feed').append(node('p', '这里还很安静，等一个值得记下的念头。', 'thoughts-empty'));
    status(loggedIn ? '只有你的账号可以发布；草稿仅自己可见。' : '一些零散的念头，也是一点生活的痕迹。');
  }
  el('login').addEventListener('click', () => action(async () => {
    const verifier = Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('');
    if (!storage.set('.verifier', verifier)) throw new Error('请允许此站点使用会话存储后再登录。');
    const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
    const encoded = btoa(String.fromCharCode(...new Uint8Array(hash))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    location.assign(api + '/auth/start?browser_challenge=' + encoded);
  }));
  el('logout').addEventListener('click', () => action(async () => {
    await request('/auth/logout', { method: 'POST' });
    token = ''; storage.remove('.token'); ownerUI(false); el('editor').hidden = true;
    await load(); status('已退出，浏览器暂存内容保留。');
  }));
  el('new').addEventListener('click', () => {
    if (el('body').value || el('title').value) { el('editor').hidden = false; el('body').focus(); }
    else edit();
  });
  el('cancel').addEventListener('click', () => { persist(); el('editor').hidden = true; el('new').textContent = '继续写'; });
  ['title', 'body'].forEach(id => el(id).addEventListener('input', persist));
  el('more').addEventListener('click', () => action(() => load(true)));
  el('editor').addEventListener('submit', event => {
    event.preventDefault();
    const intent = event.submitter?.value || 'draft';
    action(async () => {
      if (!el('body').value.trim()) throw new Error('先写一点内容吧。');
      const data = { title: el('title').value, body: el('body').value, status: intent, version: editing?.version };
      await request('/posts' + (editing ? '/' + editing.id : ''), { method: editing ? 'PUT' : 'POST', body: JSON.stringify(data) });
      clearDraft(); editing = null; el('editor').reset(); el('editor').hidden = true; el('new').textContent = '写一条';
      await load(); status(intent === 'published' ? '已发布。' : '草稿已保存，仅你可见。');
    });
  });
  if (!api) {
    status('随想服务尚未连接，发布功能暂未开放。');
    el('feed').append(node('p', '留一处地方，收集日常的念头。', 'thoughts-empty'));
    return;
  }
  action(async () => {
    ownerUI(false);
    const hash = new URLSearchParams(location.hash.slice(1));
    const code = hash.get('thoughts-code');
    const loginError = hash.get('thoughts-error');
    if (code || loginError) history.replaceState(null, '', location.pathname + location.search);
    if (code) {
      const verifier = storage.get('.verifier'); storage.remove('.verifier');
      const result = await request('/auth/exchange', { method: 'POST', body: JSON.stringify({ code, verifier: verifier || '' }) });
      token = result.token; storage.set('.token', token);
    } else token = storage.get('.token') || '';
    if (token) {
      try { await request('/auth/me'); ownerUI(true); }
      catch { token = ''; storage.remove('.token'); ownerUI(false); }
    } else ownerUI(false);
    await load();
    if (loggedIn) {
      try {
        const draft = JSON.parse(localStorage.getItem(draftKey));
        if (draft && (draft.body || draft.title)) edit({ ...draft, ...draft.editing }, true);
      } catch { /* corrupt or unavailable local draft */ }
    }
    if (loginError) status(loginError === 'forbidden' ? '此账号没有发布权限，请使用 Bamb0oChen 登录。' : '登录未完成，请重试。');
  });
})();
