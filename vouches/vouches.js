document.addEventListener("DOMContentLoaded", () => {
  const app = window.MM2_BASE_APP;
  const listTarget = document.getElementById("vouch-history");
  const loadOlderButton = document.getElementById("load-older-button");

  if (!app || !listTarget) return;

  const params = new URLSearchParams(window.location.search);
  const olderThan = params.get("older_than");

  function renderList(items) {
    listTarget.innerHTML = "";
    if (!items.length) {
      app.setEmpty(listTarget, "No public vouches available.", "There are no recent vouch events to display yet.");
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("article");
      row.className = "vouch-item";
      row.innerHTML = `
        <img class="feed-avatar" src="${app.resolveAvatar("", item.middleman || "MM")}" alt="${app.escapeHTML(item.middleman || "Middleman")} avatar" loading="lazy" />
        <div>
          <strong>${app.escapeHTML(item.middleman || "Middleman")}</strong><br />
          <span class="feed-meta">vouched by ${app.escapeHTML(item.vouched_by || "Unknown")} • ${app.escapeHTML(app.relativeTime(item.created_at))}</span>
        </div>
        <div class="vouch-amount">${app.escapeHTML(app.formatMoney(item.amount_delta || 0))}</div>
      `;
      listTarget.appendChild(row);
    });

    if (loadOlderButton) {
      const oldest = items[items.length - 1];
      loadOlderButton.disabled = !oldest || !oldest.created_at;
      if (oldest && oldest.created_at) {
        loadOlderButton.onclick = () => {
          const url = new URL(window.location.href);
          url.searchParams.set("older_than", oldest.created_at);
          window.location.href = url.toString();
        };
      }
    }
  }

  const records = olderThan
    ? app.fallbackVouchFeed.filter((entry) => new Date(entry.created_at) < new Date(olderThan))
    : app.fallbackVouchFeed;

  renderList(records.slice(0, 20));
});
