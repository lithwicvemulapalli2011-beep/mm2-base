document.addEventListener("DOMContentLoaded", () => {
  const app = window.MM2_BASE_APP;
  const list = document.getElementById("mm-list");
  const input = document.getElementById("mm-search");
  if (!list || !input || !app) return;

  const allMembers = [...app.fallbackMiddlemen.filter(item => item.active)].sort((a, b) => Number(b.vouch_count || 0) - Number(a.vouch_count || 0));

  function render(items) {
    if (!items.length) {
      app.setEmpty(list, "No active middlemen match this search.", "Try a different username, display name, or Discord ID.");
      return;
    }

    list.innerHTML = "";
    items.forEach((member) => {
      const card = document.createElement("article");
      card.className = "mm-card";
      card.innerHTML = `
        <div class="mm-header">
          <img class="mm-avatar" src="${app.resolveAvatar(member.avatar_url, member.display_name || member.username)}" alt="${app.escapeHTML(member.display_name || member.username)} avatar" loading="lazy" />
          <div>
            <div class="mm-name">${app.escapeHTML(member.display_name || member.username)}</div>
            <div class="mm-username">@${app.escapeHTML(member.username)}</div>
          </div>
        </div>
        <div class="mm-meta">
          <span>Vouches</span>
          <strong>${app.escapeHTML(app.formatNumber(member.vouch_count || 0))}</strong>
        </div>
        <div class="mm-meta">
          <span>Joined</span>
          <strong>${app.escapeHTML(app.formatDate(member.joined_at))}</strong>
        </div>
        <span class="status-pill active">Active Middleman</span>
        <a class="card-link" href="/mm/?id=${encodeURIComponent(member.discord_id)}">View Profile</a>
      `;
      list.appendChild(card);
    });
  }

  render(allMembers);

  input.addEventListener("input", (event) => {
    const value = event.target.value.trim().toLowerCase();
    if (!value) {
      render(allMembers);
      return;
    }

    const filtered = allMembers.filter((member) => {
      const haystack = [member.display_name, member.username, member.discord_id].join(" ").toLowerCase();
      return haystack.includes(value);
    });

    render(filtered);
  });
});
