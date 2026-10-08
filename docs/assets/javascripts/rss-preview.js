(() => {
  const preview = document.querySelector('.notes-rss-preview');
  if (!preview) return;

  const status = preview.querySelector('.notes-rss-preview__status');
  const changesUrl = new URL(preview.dataset.changes, document.baseURI);
  const readJson = (url) => fetch(url, { headers: { Accept: 'application/json' } }).then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    });
  Promise.all([readJson(changesUrl), readJson(new URL('presets.json', changesUrl))])
    .then(([items, presets]) => {
      if (!Array.isArray(items)) throw new Error('变更清单格式错误');
      if (!Array.isArray(presets)) throw new Error('订阅预设格式错误');
      const list = document.createElement('div');
      list.setAttribute('role', 'list');
      const filter = document.querySelector('#rss-folder');
      const stateFilter = document.querySelector('#rss-state');
      const subscriptionFilter = document.querySelector('#rss-preset');
      const subscriptionState = document.querySelector('#rss-preset-state');
      const folders = new Set();
      for (const item of items) {
        const parts = item.path.split('/').slice(0, -1);
        parts.forEach((_, index) => folders.add(parts.slice(0, index + 1).join('/')));
      }
      for (const folder of [...folders].sort((a, b) => a.localeCompare(b, 'zh-CN'))) {
        const option = document.createElement('option');
        option.value = folder;
        option.textContent = folder.replaceAll('/', ' / ');
        filter.append(option);
      }
      for (const preset of presets.filter((entry) => entry.folder && !entry.status)) {
        const option = document.createElement('option');
        option.value = preset.folder;
        option.textContent = preset.label;
        subscriptionFilter.append(option);
      }
      const subscribe = document.querySelector('#rss-subscribe');
      const copy = document.querySelector('#rss-copy');
      const address = document.querySelector('#rss-subscription-url');
      const copyStatus = document.querySelector('#rss-copy-status');
      const params = new URLSearchParams(location.search);
      if ([...filter.options].some((option) => option.value === params.get('folder'))) filter.value = params.get('folder');
      if ([...stateFilter.options].some((option) => option.value === params.get('status'))) stateFilter.value = params.get('status');
      copy.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(address.value);
          copyStatus.textContent = '订阅地址已复制';
        } catch {
          address.focus();
          address.select();
          copyStatus.textContent = '请复制已选中的订阅地址';
        }
      });
      const render = () => {
        const preset = presets.find((entry) => entry.folder === subscriptionFilter.value && entry.status === subscriptionState.value);
        if (preset) {
          subscribe.href = preset.url;
          address.value = preset.url;
          subscribe.hidden = copy.hidden = address.hidden = false;
          copyStatus.textContent = '';
        }
        list.replaceChildren();
        const visible = items.filter((item) =>
          (!filter.value || item.path.startsWith(`${filter.value}/`)) &&
          (!stateFilter.value || item.status === stateFilter.value)
        ).slice(0, 30);
        for (const item of visible) {
          const row = document.createElement('div');
          row.className = 'notes-rss-preview__item';
          row.setAttribute('role', 'listitem');

          const hasLink = typeof item.url === 'string';
          const path = document.createElement(hasLink ? 'a' : 'span');
          path.className = 'notes-rss-preview__path';
          path.textContent = item.breadcrumb.join(' - ');
          if (hasLink) path.href = new URL(`../${item.url}`, document.baseURI).href;
          row.append(path);

          const meta = document.createElement('span');
          meta.className = 'notes-rss-preview__meta';
          const parsed = new Date(item.date);
          if (!Number.isNaN(parsed.getTime())) {
            const date = document.createElement('time');
            date.dateTime = parsed.toISOString();
            date.textContent = new Intl.DateTimeFormat('zh-CN', {
              year: 'numeric', month: '2-digit', day: '2-digit',
            }).format(parsed);
            meta.append(date);
          }
          const state = document.createElement('span');
          state.className = `notes-rss-preview__state notes-rss-preview__state--${item.status}`;
          state.textContent = item.status;
          meta.append(state);
          row.append(meta);
          list.append(row);
        }
        if (!visible.length) list.textContent = '当前筛选条件下暂无文章变更。';
      };
      filter.addEventListener('change', render);
      stateFilter.addEventListener('change', render);
      subscriptionFilter.addEventListener('change', render);
      subscriptionState.addEventListener('change', render);
      render();
      status.remove();
      if (items.length) preview.append(list);
      else preview.textContent = '暂时没有文章变更。';
    })
    .catch((error) => {
      console.error('RSS 变更列表加载失败', error);
      status.textContent = `变更列表加载失败（${error.message}）。请稍后重试。`;
    });
})();
