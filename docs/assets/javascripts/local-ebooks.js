(() => {
  function setup(library) {
    if (library.dataset.ready) return;
    library.dataset.ready = "true";

    const reader = library.querySelector("[data-local-ebook-reader]");
    const frame = library.querySelector("[data-local-ebook-frame]");
    const title = library.querySelector("[data-local-ebook-title]");
    const open = library.querySelector("[data-local-ebook-open]");
    const cards = [...library.querySelectorAll("[data-local-ebook]")];

    function show(card) {
      const currentUrl = new URL(card.dataset.pdf, document.baseURI).href;
      title.textContent = card.querySelector("strong").textContent;
      frame.src = currentUrl;
      open.href = currentUrl;
      reader.hidden = false;
      cards.forEach((item) => item.classList.toggle("is-active", item === card));
      reader.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    cards.forEach((card) => card.addEventListener("click", () => show(card)));
  }

  function initialize() {
    document.querySelectorAll("[data-local-ebook-library]").forEach(setup);
  }

  if (typeof document$ !== "undefined") document$.subscribe(initialize);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize);
  else initialize();
})();
