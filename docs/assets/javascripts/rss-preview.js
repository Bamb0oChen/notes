(() => {
  const preview = document.querySelector('.notes-rss-preview');
  if (!preview) return;

  const status = preview.querySelector('.notes-rss-preview__status');
  const changesUrl = new URL(preview.dataset.changes, document.baseURI);
  fetch(changesUrl, { headers: { Accept: 'application/json' } })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((items) => {
      if (!Array.isArray(items)) throw new Error('变更清单格式错误');
      const list = document.createElement('div');
      list.setAttribute('role', 'list');
      const filter = document.querySelector('#rss-folder');
      const folders = new Set();
      for (const item of items.filter((entry) => entry.status !== 'delete')) {
        const parts = item.path.split('/').slice(0, -1);
        parts.forEach((_, index) => folders.add(parts.slice(0, index + 1).join('/')));
      }
      for (const folder of [...folders].sort((a, b) => a.localeCompare(b, 'zh-CN'))) {
        const option = document.createElement('option');
        option.value = folder;
        const sample = items.find((item) => item.path.startsWith(`${folder}/`));
        option.textContent = sample.breadcrumb.slice(0, folder.split('/').length).join(' - ');
        filter.append(option);
      }
      const render = () => {
        list.replaceChildren();
        const visible = items.filter((item) => !filter.value || item.path.startsWith(`${filter.value}/`)).slice(0, 30);
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
        if (!visible.length) list.textContent = '这个文件夹暂时没有文章变更。';
      };
      filter.addEventListener('change', render);
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
