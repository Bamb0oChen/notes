/* Frame the daylight portrait in the actual space beside the article, rather
   than pinning it to a viewport percentage that breaks on wider monitors. */
(() => {
  let observer;
  let frame;
  let image;
  let content;
  const desktop = matchMedia('(min-width: 60em)');
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  function update() {
    frame = undefined;
    if (!image || !content) return;
    const width = document.documentElement.clientWidth;
    const height = innerHeight;
    const right = content.getBoundingClientRect().right;
    const gap = width - right;
    // Mobile keeps the original source and its existing framing. On layouts
    // without a usable side gutter, do not zoom in on an invisible subject.
    if (!desktop.matches || gap < 160) {
      image.removeAttribute('data-framed');
      return;
    }
    // Coordinates refer to the 1702 x 851 outpainting, not its mobile source.
    const focalX = 1192;
    const focalY = 285;
    const targetX = right + gap * .53;
    const headerBottom = document.querySelector('.md-header')?.getBoundingClientRect().bottom || 0;
    const tabsBottom = document.querySelector('.md-tabs')?.getBoundingClientRect().bottom || 0;
    const top = Math.max(0, headerBottom, tabsBottom);
    const targetY = top + (height - top) * .3;
    // Cover the entire viewport while moving the face into the right gutter.
    // The extra scale crops scenery, never stretches the illustration.
    const scale = Math.max(width / 1702, height / 851, targetX / focalX);
    const renderedWidth = 1702 * scale;
    const renderedHeight = 851 * scale;
    image.style.setProperty('--backdrop-width', `${renderedWidth}px`);
    image.style.setProperty('--backdrop-height', `${renderedHeight}px`);
    image.style.setProperty('--backdrop-x', `${clamp(targetX - focalX * scale, width - renderedWidth, 0)}px`);
    image.style.setProperty('--backdrop-y', `${clamp(targetY - focalY * scale, height - renderedHeight, 0)}px`);
    image.setAttribute('data-framed', '');
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(update);
  }

  function mount() {
    observer?.disconnect();
    image = document.querySelector('.notes-backdrop__light img');
    content = document.querySelector('.md-content');
    if (!image || !content) return;
    observer = new ResizeObserver(schedule);
    observer.observe(content);
    observer.observe(document.documentElement);
    update();
  }
  addEventListener('resize', schedule, {passive: true});
  desktop.addEventListener('change', schedule);
  if (typeof document$ !== 'undefined') document$.subscribe(mount);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
