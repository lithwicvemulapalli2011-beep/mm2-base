document.addEventListener("DOMContentLoaded", () => {
  const app = window.MM2_BASE_APP;
  const container = document.getElementById("mm-profile-content");
  if (!container || !app) return;

  const params = new URLSearchParams(window.location.search);
  const id = String(params.get("id") || "").replace(/\D/g, "");

  if (!id) {
    app.setEmpty(container, "No middleman selected", "Use the lookup tool to select a public profile.");
    return;
  }

  app.setLoading(container, "Loading profile…");

  const person = app.fallbackMiddlemen.find((item) => String(item.discord_id) === String(id));
  const recentVouches = app.fallbackVouchFeed.slice(0, 5);

  const markup = person ? `
    <div class="profile-shell">
      <div class="profile-header">
        <img class="profile-avatar" src="${app.resolveAvatar(person.avatar_url, person.display_name || person.username)}" alt="${app.escapeHTML(person.display_name || person.username)} avatar" loading="lazy" />
        <div class="profile-meta">
          <h2>${app.escapeHTML(person.display_name || person.username)}</h2>
          <p>@${app.escapeHTML(person.username)}</p>
          <div class="verification-pill">Verified Middleman</div>
        </div>
      </div>
      <div class="profile-grid">
        <div class="detail-card">
          <div class="detail-label">Discord ID</div>
          <div class="detail-value mono">${app.escapeHTML(person.discord_id)}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">Vouch Count</div>
          <div class="detail-value">${app.escapeHTML(app.formatNumber(person.vouch_count || 0))}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">Earnings</div>
          <div class="detail-value">${app.escapeHTML(app.formatMoney(person.earnings || 0))}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">Joined</div>
          <div class="detail-value">${app.escapeHTML(app.formatDate(person.joined_at))}</div>
        </div>
      </div>
      <div class="verification-box">
        <h3>Verified Middleman</h3>
        <p>Public profile matched against the MM2 Base directory.</p>
      </div>
      <div class="warning-callout">
        <p><strong>Always verify the exact Discord ID.</strong> Display names and usernames can be copied. Verify with the community before starting a trade.</p>
      </div>
      <div class="hero-actions" style="margin-top: 20px;">
        <a class="button-secondary" href="/lookup/">Verify Another Middleman</a>
      </div>
      <div class="section-heading" style="margin-top: 26px;">
        <h2>Recent Vouches</h2>
      </div>
      <div class="vouch-list">
        ${recentVouches.map((item) => `
          <article class="vouch-item">
            <img class="feed-avatar" src="${app.resolveAvatar("", item.vouched_by || "MM")}" alt="${app.escapeHTML(item.vouched_by || "User")} avatar" loading="lazy" />
            <div>
              <strong>${app.escapeHTML(item.vouched_by || "Unknown")}</strong><br />
              <span class="feed-meta">${app.escapeHTML(app.relativeTime(item.created_at))}</span>
            </div>
            <div class="vouch-amount">${app.escapeHTML(app.formatMoney(item.amount_delta || 0))}</div>
          </article>
        `).join("")}
      </div>
    </div>
  ` : `
    <div class="empty-state">
      <h3>No public profile found</h3>
      <p>That Discord ID is not listed in the public middleman directory.</p>
    </div>
  `;

  container.innerHTML = markup;
});
