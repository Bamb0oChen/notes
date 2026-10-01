// Do not pollute production counts with local previews or mirror deployments.
(() => {
  if (!['bamb0ochen.com', 'bamb0ochen.github.io'].includes(location.hostname) ||
      !location.pathname.startsWith('/notes/')) return;
  const status = document.getElementById('notes-visitors-status');
  if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) {
    if (status) {
      status.textContent = '已根据浏览器隐私设置关闭访问统计。';
      status.hidden = false;
    }
    return;
  }

  const containers = ['site_pv', 'site_uv', 'page_pv']
    .map((key) => document.getElementById(`busuanzi_container_${key}`))
    .filter(Boolean);
  const hasCounts = () => containers.some((container) => container.style.display !== 'none');
  const showUnavailable = () => {
    if (status && !hasCounts()) status.hidden = false;
  };
  if (status) {
    const observer = new MutationObserver(() => {
      if (hasCounts()) {
        status.hidden = true;
        observer.disconnect();
      }
    });
    containers.forEach((container) => observer.observe(container, { attributes: true, attributeFilter: ['style'] }));
    setTimeout(showUnavailable, 9000);
  }

  // Snapshots from 2026-09-27. Busuanzi keeps separate counters per domain.
  if (location.hostname === 'bamb0ochen.com') {
    const mergeCounter = (id, history) => {
      const value = document.getElementById(id);
      if (!value) return;
      const observer = new MutationObserver(() => {
        const current = Number(value.textContent);
        if (!Number.isSafeInteger(current) || current < 0) return;
        observer.disconnect();
        value.textContent = String(history + current);
      });
      observer.observe(value, { childList: true, characterData: true, subtree: true });
    };
    mergeCounter('busuanzi_value_site_pv', 798);
    // This is a sum of two domain-level UV counts, not a deduplicated UV.
    mergeCounter('busuanzi_value_site_uv', 187);
    if (['/notes/', '/notes/index.html'].includes(location.pathname)) {
      mergeCounter('busuanzi_value_page_pv', 99);
    }
  }

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  script.onerror = showUnavailable;
  document.body.appendChild(script);
})();
