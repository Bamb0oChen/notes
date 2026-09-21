// Do not pollute production counts with local previews or mirror deployments.
(() => {
  if (location.hostname !== 'bamb0ochen.github.io' ||
      !location.pathname.startsWith('/notes/')) return;
  if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.body.appendChild(script);
})();
