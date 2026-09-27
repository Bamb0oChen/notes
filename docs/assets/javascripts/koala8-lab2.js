document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("koala8-lab2-clue-button");
  const status = document.getElementById("koala8-lab2-clue-status");
  if (!button || !status) return;

  button.addEventListener("click", () => {
    const destination = new URL("../../../../assets/labs/koala8/step2.html", window.location.href);
    const alteredUrl = destination.href.replace("step2.html", "{password=koalastudio}step2.html");
    const sitePath = new URL("../../../../", window.location.href).pathname;
    document.cookie = `koala8_lab2_clue=${btoa(alteredUrl)}; Path=${sitePath}; SameSite=Lax`;
    status.textContent = document.cookie.includes("koala8_lab2_clue=")
      ? "线索已保存到浏览器。打开开发者工具找找它。"
      : "线索未能保存，请检查浏览器是否允许此站点使用 Cookie。";
    status.hidden = false;
  });
});
