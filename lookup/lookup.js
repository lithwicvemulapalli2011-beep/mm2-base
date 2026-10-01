document.addEventListener("DOMContentLoaded", () => {
  const app = window.MM2_BASE_APP;
  const form = document.getElementById("lookup-form");
  const input = document.getElementById("lookup-input");
  const resultArea = document.getElementById("lookup-results");

  if (!form || !input || !resultArea || !app) return;

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const value = input.value.trim();
    if (!value) {
      app.setEmpty(resultArea, "No search entered.", "Type a Discord ID, username, or display name to check the public directory.");
      return;
    }

    app.setLoading(resultArea, "Checking the public directory…");

    try {
      const match = window.MM2_BASE_FALLBACKS?.middlemen?.find((item) => {
        const normalizedId = value.replace(/\D/g, "");
        return (normalizedId && String(item.discord_id) === normalizedId) || String(item.username).toLowerCase() === value.toLowerCase() || String(item.display_name).toLowerCase() === value.toLowerCase();
      }) || window.MM2_BASE_APP.fallbackMiddlemen.find((item) => {
        const normalizedId = value.replace(/\D/g, "");
        return (normalizedId && String(item.discord_id) === normalizedId) || String(item.username).toLowerCase() === value.toLowerCase() || String(item.display_name).toLowerCase() === value.toLowerCase();
      });

      if (!match) {
        app.setEmpty(resultArea, "No middleman was found matching that information.", "The person may not be registered, their username may have changed, or they may need to be verified using the exact Discord ID.");
        return;
      }

      const card = document.createElement("div");
      card.innerHTML = `
        <div class="result-card">
          <div class="profile-header">
            <img class="profile-avatar" src="${app.resolveAvatar(match.avatar_url, match.display_name || match.username)}" alt="${app.escapeHTML(match.display_name || match.username)} avatar" loading="lazy" />
            <div class="profile-meta">
              <h2>${app.escapeHTML(match.display_name || match.username)}</h2>
              <p>@${app.escapeHTML(match.username)}</p>
            </div>
          </div>
          <div class="profile-grid">
            <div class="detail-card">
              <div class="detail-label">Discord ID</div>
              <div class="detail-value mono">${app.escapeHTML(match.discord_id)}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">Vouch Count</div>
              <div class="detail-value">${app.escapeHTML(app.formatNumber(match.vouch_count || 0))}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">Status</div>
              <div class="detail-value">${match.active ? "Active Middleman" : "Inactive"}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">Joined</div>
              <div class="detail-value">${app.escapeHTML(app.formatDate(match.joined_at))}</div>
            </div>
          </div>
          <div class="warning-callout">
            <p><strong>Always verify the exact Discord ID.</strong> Display names and usernames can be copied, so public verification should always confirm the exact account.</p>
          </div>
          <div class="hero-actions" style="margin-top: 18px;">
            <a class="button" href="/mm/?id=${encodeURIComponent(match.discord_id)}">View Middleman Profile</a>
          </div>
        </div>
      `;
      resultArea.innerHTML = "";
      resultArea.appendChild(card.firstElementChild);
    } catch (error) {
      app.setError(resultArea, "The lookup service is temporarily unavailable. Please try again in a moment.");
    }
  });
});
