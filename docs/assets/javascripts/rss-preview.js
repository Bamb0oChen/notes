(() => {
  const preview = document.querySelector('.notes-rss-preview');
  if (!preview) return;

  const status = preview.querySelector('.notes-rss-preview__status');
  fetch(preview.dataset.feed)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.text();
    })
    .then((xml) => {
      const feed = new DOMParser().parseFromString(xml, 'application/xml');
      if (feed.querySelector('parsererror')) throw new Error('RSS XML 无法解析');
      const items = [...feed.querySelectorAll('channel > item')].filter((item) => {
        const link = item.querySelector('link')?.textContent;
        try { return !new URL(link).pathname.endsWith('/rss/'); }
        catch { return true; }
      });
      status.remove();
      if (!items.length) {
        preview.textContent = '暂时没有可预览的文章。';
        return;
      }

      for (const item of items) {
        const article = document.createElement('article');
        article.className = 'notes-rss-preview__item';
        const heading = document.createElement('h2');
        const link = document.createElement('a');
        link.href = item.querySelector('link')?.textContent || '#';
        link.textContent = item.querySelector('title')?.textContent || '未命名文章';
        heading.append(link);
        article.append(heading);

        const published = item.querySelector('pubDate')?.textContent;
        if (published) {
          const date = document.createElement('time');
          const parsed = new Date(published);
          if (!Number.isNaN(parsed.getTime())) {
            date.dateTime = parsed.toISOString();
            date.textContent = new Intl.DateTimeFormat('zh-CN', {
              year: 'numeric', month: 'long', day: 'numeric'
            }).format(parsed);
            article.append(date);
          }
        }
        preview.append(article);
      }
    })
    .catch(() => {
      status.textContent = '文章列表暂时加载失败，请使用上方订阅地址或稍后重试。';
    });
})();
