const tabs = Array.from(document.querySelectorAll<HTMLButtonElement>("[data-task]"));
const panels = Array.from(document.querySelectorAll<HTMLElement>("[role=tabpanel]"));
const status = document.querySelector<HTMLElement>(".copy-status");
let statusTimer: ReturnType<typeof setTimeout>;
const buttonTimers = new WeakMap<HTMLButtonElement, ReturnType<typeof setTimeout>>();

function selectTask(tab: HTMLButtonElement, focus = false) {
  for (const item of tabs) {
    const selected = item === tab;
    item.setAttribute("aria-selected", String(selected));
    item.tabIndex = selected ? 0 : -1;
  }
  for (const panel of panels) panel.hidden = panel.id !== tab.getAttribute("aria-controls");
  if (focus) tab.focus();
}
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTask(tab));
  tab.addEventListener("keydown", (event) => {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    selectTask(tabs[next], true);
  });
});
function announce(message: string) {
  clearTimeout(statusTimer);
  if (status) status.textContent = message;
  statusTimer = setTimeout(() => { if (status) status.textContent = ""; }, 4000);
}
async function copyText(text: string, button: HTMLButtonElement, guide = false) {
  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch {
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.cssText = "position:fixed;left:-9999px;top:0";
    document.body.append(field);
    field.select();
    try { copied = document.execCommand("copy"); } catch { copied = false; }
    field.remove();
    button.focus();
  }
  if (!copied) {
    announce("Copy is unavailable in this browser. Select the text and copy it manually.");
    return;
  }
  clearTimeout(buttonTimers.get(button));
  button.dataset.copied = "true";
  const label = button.querySelector<HTMLElement>("[data-copy-label]");
  if (label) label.textContent = "Copied";
  announce(guide ? "Link copied. Share it with your agent." : "Prompt copied. Paste it into your agent.");
  buttonTimers.set(button, setTimeout(() => {
    delete button.dataset.copied;
    if (label) label.textContent = "Copy prompt";
  }, 2400));
}
document.querySelectorAll<HTMLButtonElement>("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const text = document.getElementById(button.dataset.copyTarget || "")?.textContent?.trim();
    if (text) void copyText(text, button);
  });
});
document.querySelector<HTMLButtonElement>("[data-copy-guide]")?.addEventListener("click", (event) => {
  const button = event.currentTarget as HTMLButtonElement;
  const link = document.querySelector<HTMLAnchorElement>("#agent-guide-link");
  // Resolve against this host so local previews also share a working URL.
  if (link) void copyText(link.href, button, true);
});
