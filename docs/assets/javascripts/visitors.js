// Do not pollute production counts with local previews or mirror deployments.
(() => {
  if (!['bamb0ochen.com', 'bamb0ochen.github.io'].includes(location.hostname) ||
      !location.pathname.startsWith('/notes/')) return;
  if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;

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
  document.body.appendChild(script);
})();
