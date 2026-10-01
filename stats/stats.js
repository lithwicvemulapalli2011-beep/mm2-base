document.addEventListener("DOMContentLoaded", () => {
  const app = window.MM2_BASE_APP;
  const chartTarget = document.getElementById("vouch-chart");
  const statCards = document.getElementById("stat-cards");

  if (!app || !chartTarget || !statCards) return;

  const data = [
    { label: "Members", value: 1284 },
    { label: "Online", value: 214 },
    { label: "Boosts", value: 28 },
    { label: "Total Vouches", value: 923 },
    { label: "Total Trades", value: 1840 },
    { label: "Total Volume", value: 142500 },
    { label: "Verified Middlemen", value: 42 }
  ];

  statCards.innerHTML = data.map((item) => `
    <div class="stat-card">
      <div class="stat-card-label">${app.escapeHTML(item.label)}</div>
      <div class="stat-card-value">${app.escapeHTML(item.label === "Total Volume" ? app.formatMoney(item.value) : app.formatNumber(item.value))}</div>
    </div>
  `).join("");

  const chartRows = app.buildVouchChart(app.fallbackVouchFeed);
  app.renderChart(chartRows);
});
