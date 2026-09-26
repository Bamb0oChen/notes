document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("koala8-lab2-clue-button");
  const output = document.getElementById("koala8-lab2-clue-output");
  if (!button || !output) return;

  button.addEventListener("click", () => {
    const destination = new URL("../../../../assets/labs/koala8/step2.html", window.location.href);
    const alteredUrl = destination.href.replace("step2.html", "{password=koalastudio}step2.html");
    output.textContent = btoa(alteredUrl);
    output.hidden = false;
  });
});
