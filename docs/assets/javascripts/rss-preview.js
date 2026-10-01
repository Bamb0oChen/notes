(() => {
  const preview = document.querySelector('.notes-rss-preview');
  if (!preview) return;

  const status = preview.querySelector('.notes-rss-preview__status');
  const feedUrl = new URL(preview.dataset.feed, document.baseURI);
  fetch(feedUrl, { headers: { Accept: 'application/rss+xml, application/xml, text/xml' } })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.text();
    })
    .then((xml) => {
      const feed = new DOMParser().parseFromString(xml, 'application/xml');
      const parseError = feed.getElementsByTagName('parsererror')[0];
      if (parseError) throw new Error(`XML 格式错误：${parseError.textContent.trim().slice(0, 120)}`);
      if (feed.documentElement.localName !== 'rss') throw new Error('返回内容不是 RSS 订阅文件');
      const channel = feed.getElementsByTagName('channel')[0];
      if (!channel) throw new Error('RSS 缺少 channel');
      const value = (item, tag) => item.getElementsByTagName(tag)[0]?.textContent?.trim() || '';
      const items = [...channel.getElementsByTagName('item')].filter((item) => {
        const link = value(item, 'link');
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
        link.href = value(item, 'link') || '#';
        link.textContent = value(item, 'title') || '未命名文章';
        heading.append(link);
        article.append(heading);

        const published = value(item, 'pubDate');
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
    .catch((error) => {
      console.error('RSS 预览加载失败', error);
      status.textContent = `文章列表加载失败（${error.message}）。请使用上方订阅地址或稍后重试。`;
    });
})();
