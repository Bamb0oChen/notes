// Count only visits to the public domains, not local previews.
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

  const origin = 'https://bamb0ochen.goatcounter.com';
  const path = location.pathname;
  const showCount = (id, count, baseline) => {
    const element = document.getElementById(id);
    const number = Number(String(count).replace(/,/g, ''));
    if (!element || !Number.isSafeInteger(number) || number < 0) return false;
    element.querySelector('strong').textContent = String(baseline + number);
    element.hidden = false;
    return true;
  };

  const readCount = async (counterPath, id, baseline) => {
    const response = await fetch(`${origin}/counter/${encodeURIComponent(counterPath)}.json`);
    // A newly created page has no counter yet.
    if (response.status === 404) return showCount(id, 0, baseline);
    if (!response.ok) throw new Error(`GoatCounter returned ${response.status}`);
    const data = await response.json();
    if (!showCount(id, data.count, baseline)) throw new Error('Invalid GoatCounter count');
  };

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://gc.zgo.at/count.js';
  script.dataset.goatcounter = `${origin}/count`;
  script.dataset.goatcounterSettings = JSON.stringify({ no_onload: true, no_events: true });
  script.onload = () => {
    // GoatCounter normally deduplicates repeat visits. Here we want page loads.
    window.goatcounter.count({ path, no_session: true });
  };
  script.onerror = () => {
    if (status) status.hidden = false;
  };
  document.body.appendChild(script);

  const pageBaseline = ['/notes/', '/notes/index.html'].includes(path) ? 99 : 0;
  Promise.allSettled([
    readCount('TOTAL', 'notes-site-views', 1596),
    readCount(path, 'notes-page-views', pageBaseline),
  ]).then((results) => {
    if (status && results.every((result) => result.status === 'rejected')) status.hidden = false;
  });
})();
