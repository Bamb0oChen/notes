// Do not pollute production counts with local previews or mirror deployments.
(() => {
  if (!['bamb0ochen.com', 'bamb0ochen.github.io'].includes(location.hostname) ||
      !location.pathname.startsWith('/notes/')) return;
  if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.body.appendChild(script);
})();
