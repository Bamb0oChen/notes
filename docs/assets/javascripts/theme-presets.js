(() => {
  const storageKey = "notes-theme-preset";
  const presets = {
    night: { scheme: "slate", image: "night" },
    autumn: { scheme: "default", image: "autumn" },
    forest: { scheme: "default", image: "forest" },
  };

  function savedPreset() {
    try { return localStorage.getItem(storageKey); } catch { return null; }
  }

  function savePreset(value) {
    try { localStorage.setItem(storageKey, value); } catch { /* Private browsing. */ }
  }

  function setPicture(picture, desktop, mobile) {
    const image = picture?.querySelector("img");
    if (!image) return;
    const source = picture.querySelector("source");
    if (source && mobile) source.srcset = mobile;
    image.src = desktop;
  }

  function crossfadeDay(picture, nextDesktop, nextMobile) {
    document.querySelectorAll(".notes-backdrop__previous").forEach((layer) => layer.remove());
    const previous = picture.cloneNode(true);
    previous.className = "notes-backdrop__previous";
    previous.style.background = getComputedStyle(picture).background;
    const oldImage = picture.querySelector("img");
    const copy = previous.querySelector("img");
    copy.style.objectFit = getComputedStyle(oldImage).objectFit;
    copy.style.objectPosition = getComputedStyle(oldImage).objectPosition;
    picture.after(previous);

    const nextSource = matchMedia("(max-width: 59.984375em)").matches ? nextMobile : nextDesktop;
    const preload = new Image();
    let fading = false;
    const fade = () => {
      if (fading || !previous.isConnected) return;
      fading = true;
      requestAnimationFrame(() => previous.classList.add("notes-backdrop__previous--fade"));
      previous.addEventListener("transitionend", () => previous.remove(), { once: true });
      setTimeout(() => previous.remove(), 900);
    };
    preload.onload = fade;
    preload.onerror = fade;
    preload.src = nextSource;
    if (preload.complete) fade();
  }

  function apply(picker, name, changeScheme = true) {
    const preset = presets[name];
    if (!preset) return;
    const body = document.body;
    const night = document.querySelector(".notes-backdrop__dark");
    const day = document.querySelector(".notes-backdrop__light");
    setPicture(night, picker.dataset.nightDesktop, picker.dataset.nightMobile);
    const images = {
      autumn: [picker.dataset.autumnDesktop, picker.dataset.autumnMobile],
      forest: [picker.dataset.forestDesktop, picker.dataset.forestMobile],
    };
    const nextImages = images[preset.image] || images.autumn;
    if (["autumn", "forest"].includes(body.dataset.notesTheme) &&
        ["autumn", "forest"].includes(name) && body.dataset.notesTheme !== name &&
        !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      crossfadeDay(day, ...nextImages);
    }
    setPicture(day, ...nextImages);
    body.dataset.notesTheme = name;
    picker.querySelectorAll("[data-notes-theme-option]").forEach((option) => {
      option.setAttribute("aria-pressed", String(option.dataset.notesThemeOption === name));
    });
    if (changeScheme && body.dataset.mdColorScheme !== preset.scheme) {
      document.querySelector(`input[name="__palette"][data-md-color-scheme="${preset.scheme}"]`)?.click();
    }
    savePreset(name);
  }

  function mount() {
    const picker = document.querySelector(".notes-theme-picker");
    if (!picker || picker.dataset.ready) return;
    picker.dataset.ready = "true";
    const toggle = picker.querySelector(".notes-theme-toggle");
    const menu = picker.querySelector(".notes-theme-menu");
    const close = () => {
      menu.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    };
    toggle.addEventListener("click", () => {
      menu.hidden = !menu.hidden;
      toggle.setAttribute("aria-expanded", String(!menu.hidden));
    });
    menu.addEventListener("click", (event) => {
      const option = event.target.closest("[data-notes-theme-option]");
      if (!option) return;
      apply(picker, option.dataset.notesThemeOption);
      close();
      toggle.focus();
    });
    document.addEventListener("click", (event) => {
      if (!picker.contains(event.target)) close();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !menu.hidden) { close(); toggle.focus(); }
    });

    const initial = savedPreset();
    apply(picker, presets[initial] ? initial :
      (document.body.dataset.mdColorScheme === "default" ? "autumn" : "night"),
      Boolean(initial));
    new MutationObserver(() => {
      const current = document.body.dataset.notesTheme;
      const scheme = document.body.dataset.mdColorScheme;
      if (presets[current]?.scheme !== scheme) {
        apply(picker, scheme === "default" ? "autumn" : "night", false);
      }
    }).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  }

  if (typeof document$ !== "undefined") document$.subscribe(mount);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
