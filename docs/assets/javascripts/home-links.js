document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("index-wechat-button");
  const status = document.getElementById("index-wechat-status");
  if (!button || !status) return;

  button.addEventListener("click", () => {
    const clue = "{congratulations!you-find-my-wechat-id:Bamb0oChen}";
    const sitePath = new URL(".", window.location.href).pathname;
    document.cookie = `wechat_id_clue=${btoa(clue)}; Path=${sitePath}; SameSite=Lax; Max-Age=2592000`;
    status.textContent = document.cookie.includes("wechat_id_clue=")
      ? "Wechat ID 已发送，尝试找出它吧。"
      : "线索未能保存，请检查浏览器是否允许此站点使用 Cookie。";
    status.hidden = false;
  });
});
