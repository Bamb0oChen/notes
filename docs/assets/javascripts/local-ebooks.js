(() => {
  function setup(library) {
    if (library.dataset.ready) return;
    library.dataset.ready = "true";

    const input = library.querySelector("[data-local-ebook-input]");
    const status = library.querySelector("[data-local-ebook-status]");
    const reader = library.querySelector("[data-local-ebook-reader]");
    const frame = library.querySelector("[data-local-ebook-frame]");
    const title = library.querySelector("[data-local-ebook-title]");
    const open = library.querySelector("[data-local-ebook-open]");
    const cards = [...library.querySelectorAll("[data-local-ebook]")];
    const files = new Map();
    let currentUrl = null;

    function show(card) {
      const file = files.get(card.dataset.localEbook);
      if (!file) {
        status.textContent = `请先选择“${card.querySelector("strong").textContent}”的 PDF 文件。`;
        input.click();
        return;
      }
      if (currentUrl) URL.revokeObjectURL(currentUrl);
      currentUrl = URL.createObjectURL(file);
      title.textContent = card.querySelector("strong").textContent;
      frame.src = currentUrl;
      open.href = currentUrl;
      reader.hidden = false;
      cards.forEach((item) => item.classList.toggle("is-active", item === card));
      reader.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    input.addEventListener("change", () => {
      let matched = 0;
      for (const file of input.files) {
        if (!file.name.toLowerCase().endsWith(".pdf")) continue;
        const card = cards.find((item) => file.name.startsWith(item.dataset.filePrefix));
        if (!card) continue;
        files.set(card.dataset.localEbook, file);
        card.classList.add("is-available");
        matched += 1;
      }
      status.textContent = matched
        ? `已识别 ${matched} 本；点击书目开始阅读。`
        : "未识别所选文件。请检查 PDF 文件名是否与书目相符。";
      input.value = "";
    });

    cards.forEach((card) => card.addEventListener("click", () => show(card)));
    window.addEventListener("pagehide", () => {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    }, { once: true });
  }

  function initialize() {
    document.querySelectorAll("[data-local-ebook-library]").forEach(setup);
  }

  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
