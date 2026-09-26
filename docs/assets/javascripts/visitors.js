// Do not pollute production counts with local previews or mirror deployments.
(() => {
  if (!['bamb0ochen.com', 'bamb0ochen.github.io'].includes(location.hostname) ||
      !location.pathname.startsWith('/notes/')) return;
  if (navigator.doNotTrack === '1' || navigator.globalPrivacyControl === true) return;

  // Snapshot of the old domain's counters on 2026-09-27. The provider keeps
  // separate counters per domain, so add old PV only when viewing the new one.
  if (location.hostname === 'bamb0ochen.com') {
    const legacySitePv = 798;
    const sitePv = document.getElementById('busuanzi_value_site_pv');
    const legacyUv = document.getElementById('notes_visitors_legacy_uv');
    const legacyNote = document.getElementById('notes_visitors_legacy_note');
    if (legacyUv) legacyUv.style.display = 'inline';
    if (legacyNote) legacyNote.style.display = 'inline';
    if (sitePv) {
      const observer = new MutationObserver(() => {
        const currentSitePv = Number(sitePv.textContent);
        if (!Number.isSafeInteger(currentSitePv) || currentSitePv < 0) return;
        observer.disconnect();
        sitePv.textContent = String(legacySitePv + currentSitePv);
      });
      observer.observe(sitePv, { childList: true, characterData: true, subtree: true });
    }
  }

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.body.appendChild(script);
})();
