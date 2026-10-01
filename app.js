(function () {
  const rootConfig = window.MM2_BASE_CONFIG || {
    supabaseUrl: "https://yklkxobuaxfswbcgdfno.supabase.co",
    supabaseAnonKey: ""
  };

  const fallbackStats = {
    members: 1284,
    online: 214,
    boosts: 28,
    verifiedMms: 42,
    safeDeals: 1840,
    vouches: 923,
    tradeVolume: 142500
  };

  const fallbackMiddlemen = [
    {
      discord_id: "4101010101010101",
      username: "maplebroker",
      display_name: "Maple Broker",
      avatar_url: "",
      vouch_count: 182,
      earnings: 1250,
      active: true,
      joined_at: "2024-01-14T10:00:00.000Z"
    },
    {
      discord_id: "4202020202020202",
      username: "embertrader",
      display_name: "Ember Trader",
      avatar_url: "",
      vouch_count: 146,
      earnings: 980,
      active: true,
      joined_at: "2024-02-03T14:20:00.000Z"
    },
    {
      discord_id: "4303030303030303",
      username: "goldenrow",
      display_name: "Golden Row",
      avatar_url: "",
      vouch_count: 133,
      earnings: 840,
      active: true,
      joined_at: "2024-03-22T18:40:00.000Z"
    },
    {
      discord_id: "4404040404040404",
      username: "stumpcheck",
      display_name: "Stump Check",
      avatar_url: "",
      vouch_count: 118,
      earnings: 670,
      active: true,
      joined_at: "2024-04-09T08:10:00.000Z"
    },
    {
      discord_id: "4505050505050505",
      username: "cindervault",
      display_name: "Cinder Vault",
      avatar_url: "",
      vouch_count: 104,
      earnings: 610,
      active: true,
      joined_at: "2024-05-18T09:30:00.000Z"
    },
    {
      discord_id: "4606060606060606",
      username: "ashlantern",
      display_name: "Ash Lantern",
      avatar_url: "",
      vouch_count: 98,
      earnings: 540,
      active: false,
      joined_at: "2023-11-02T12:15:00.000Z"
    }
  ];

  const fallbackVouchFeed = [
    { id: 1, middleman: "Maple Broker", vouched_by: "Cassian", amount_delta: 175, created_at: "2026-09-30T18:42:00.000Z", screenshot_url: "" },
    { id: 2, middleman: "Ember Trader", vouched_by: "Riven", amount_delta: 220, created_at: "2026-09-30T16:16:00.000Z", screenshot_url: "" },
    { id: 3, middleman: "Golden Row", vouched_by: "Ari", amount_delta: 130, created_at: "2026-09-29T13:25:00.000Z", screenshot_url: "" },
    { id: 4, middleman: "Stump Check", vouched_by: "Noel", amount_delta: 95, created_at: "2026-09-28T09:40:00.000Z", screenshot_url: "" },
    { id: 5, middleman: "Cinder Vault", vouched_by: "Sora", amount_delta: 310, created_at: "2026-09-27T21:11:00.000Z", screenshot_url: "" },
    { id: 6, middleman: "Ash Lantern", vouched_by: "Milo", amount_delta: 160, created_at: "2026-09-26T17:30:00.000Z", screenshot_url: "" },
    { id: 7, middleman: "Maple Broker", vouched_by: "Kae", amount_delta: 140, created_at: "2026-09-25T15:05:00.000Z", screenshot_url: "" },
    { id: 8, middleman: "Ember Trader", vouched_by: "Rook", amount_delta: 180, created_at: "2026-09-24T12:00:00.000Z", screenshot_url: "" },
    { id: 9, middleman: "Golden Row", vouched_by: "Pax", amount_delta: 210, created_at: "2026-09-23T08:12:00.000Z", screenshot_url: "" },
    { id: 10, middleman: "Maple Broker", vouched_by: "Thorn", amount_delta: 90, created_at: "2026-09-22T14:42:00.000Z", screenshot_url: "" }
  ];

  const fallbackHours = [
    { label: "Mon", value: 18 },
    { label: "Tue", value: 32 },
    { label: "Wed", value: 26 },
    { label: "Thu", value: 41 },
    { label: "Fri", value: 36 },
    { label: "Sat", value: 52 },
    { label: "Sun", value: 44 }
  ];

  function escapeHTML(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatNumber(value) {
    const num = Number(value || 0);
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: num >= 10000 ? 1 : 0
    }).format(num);
  }

  function formatMoney(value) {
    const num = Number(value || 0);
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  }

  function formatDate(value) {
    if (!value) return "Unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown";
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  }

  function relativeTime(value) {
    if (!value) return "Unknown";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown";
    const diff = Date.now() - date.getTime();
    const minute = 60 * 1000;
    const hour = 60 * minute;
    const day = 24 * hour;
    const month = 30 * day;
    const year = 365 * day;

    if (diff < hour) {
      const mins = Math.max(1, Math.round(diff / minute));
      return `${mins} minute${mins === 1 ? "" : "s"} ago`;
    }
    if (diff < day) {
      const hours = Math.max(1, Math.round(diff / hour));
      return `${hours} hour${hours === 1 ? "" : "s"} ago`;
    }
    if (diff < month) {
      const days = Math.max(1, Math.round(diff / day));
      return `${days} day${days === 1 ? "" : "s"} ago`;
    }
    if (diff < year) {
      const months = Math.max(1, Math.round(diff / month));
      return `${months} month${months === 1 ? "" : "s"} ago`;
    }
    const years = Math.max(1, Math.round(diff / year));
    return `${years} year${years === 1 ? "" : "s"} ago`;
  }

  function normalizeValue(value) {
    if (typeof value === "string") {
      return value.trim();
    }
    if (typeof value === "number") {
      return String(value);
    }
    return "";
  }

  function createFallbackAvatar(input, label = "MM") {
    const seed = normalizeValue(input) || label;
    const initials = seed
      .split(/[^a-zA-Z0-9]/)
      .filter(Boolean)
      .slice(0, 2)
      .map(part => part.slice(0, 1).toUpperCase())
      .join("") || "MM";

    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
        <defs>
          <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stop-color="#ffb347"/>
            <stop offset="100%" stop-color="#c73b1e"/>
          </linearGradient>
        </defs>
        <rect width="120" height="120" rx="24" fill="#1a0f08"/>
        <circle cx="60" cy="46" r="26" fill="url(#g)"/>
        <path d="M27 103c7-18 23-28 33-28s26 10 33 28" fill="url(#g)"/>
        <text x="60" y="66" text-anchor="middle" font-size="20" font-family="Arial, sans-serif" font-weight="700" fill="#fef3e0">${escapeHTML(initials)}</text>
      </svg>
    `;

    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  }

  function resolveAvatar(url, label = "MM") {
    if (!url) return createFallbackAvatar(label, label);
    const fallback = createFallbackAvatar(label, label);
    return url || fallback;
  }

  function initSupabase() {
    const config = window.MM2_BASE_CONFIG || rootConfig;
    const hasLib = typeof window.supabase !== "undefined";
    const isReady = Boolean(config && config.supabaseUrl && config.supabaseAnonKey && hasLib);

    if (!isReady) {
      return null;
    }

    return window.supabase.createClient(config.supabaseUrl, config.supabaseAnonKey);
  }

  async function safeQuery({ table, select = "*", filters = [], orderBy = null, limit = null, single = false }) {
    const supabase = initSupabase();
    if (!supabase) {
      return { data: [], error: null, fallback: true };
    }

    try {
      let query = supabase.from(table).select(select);

      filters.forEach(({ column, op, value }) => {
        if (op === "eq") query = query.eq(column, value);
        if (op === "lt") query = query.lt(column, value);
        if (op === "gt") query = query.gt(column, value);
        if (op === "order") query = query.order(column, { ascending: value });
      });

      if (orderBy) {
        query = query.order(orderBy.column, { ascending: orderBy.ascending !== false });
      }

      if (limit) {
        query = query.limit(limit);
      }

      const { data, error } = single ? await query.maybeSingle() : await query;

      if (error) {
        return { data: [], error, fallback: true };
      }

      return { data: data || [], error: null, fallback: false };
    } catch (error) {
      return { data: [], error, fallback: true };
    }
  }

  function setLoading(container, message = "Loading…") {
    if (!container) return;
    container.innerHTML = `
      <div class="loading-state">
        <h3>${escapeHTML(message)}</h3>
        <span class="loading-spinner" aria-hidden="true"></span>
      </div>
    `;
  }

  function setEmpty(container, title = "No results found", description = "There is nothing to display right now.") {
    if (!container) return;
    container.innerHTML = `
      <div class="empty-state">
        <h3>${escapeHTML(title)}</h3>
        <p>${escapeHTML(description)}</p>
      </div>
    `;
  }

  function setError(container, message = "Something went wrong while loading the data.") {
    if (!container) return;
    container.innerHTML = `
      <div class="error-state">
        <h3>Unable to load this information</h3>
        <p>${escapeHTML(message)}</p>
      </div>
    `;
  }

  function initNavigation() {
    const navLinks = document.querySelectorAll(".nav-link");
    const current = window.location.pathname;

    navLinks.forEach(link => {
      const href = link.getAttribute("href");
      const isHome = href === "/" && (current === "/" || current === "/index.html");
      if (isHome || current === href || current.startsWith(href) && href !== "/") {
        link.classList.add("active");
      }
    });

    const toggle = document.querySelector(".mobile-menu-toggle");
    const menu = document.querySelector(".nav-links");
    if (toggle && menu) {
      toggle.addEventListener("click", () => {
        const isExpanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!isExpanded));
        menu.classList.toggle("is-open");
      });

      menu.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
          toggle.setAttribute("aria-expanded", "false");
          menu.classList.remove("is-open");
        });
      });
    }
  }

  function initFAQ() {
    document.querySelectorAll(".faq-button").forEach(button => {
      button.addEventListener("click", () => {
        const item = button.closest(".faq-item");
        const content = item.querySelector(".faq-content");
        const expanded = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!expanded));
        content.style.maxHeight = expanded ? "0px" : `${content.scrollHeight}px`;
      });
    });
  }

  function initProgressBars() {
    const bars = document.querySelectorAll(".progress-bar");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
        }
      });
    }, { threshold: 0.2 });

    bars.forEach(bar => observer.observe(bar));
  }

  function updateFooterYear() {
    const yearEl = document.getElementById("footer-year");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  }

  function createSafeLabelFromName(name) {
    if (!name) return "MM";
    return String(name).replace(/[^a-zA-Z0-9]/g, "").slice(0, 2).toUpperCase() || "MM";
  }

  function renderHomeData() {
    const feedTarget = document.getElementById("vouch-feed");
    const teamTarget = document.getElementById("team-grid");
    if (!feedTarget && !teamTarget) return;

    if (feedTarget) {
      feedTarget.innerHTML = "";
      const rows = fallbackVouchFeed.slice(0, 8);
      rows.forEach(item => {
        const row = document.createElement("div");
        row.className = "feed-row";
        row.innerHTML = `
          <div class="feed-entity">
            <img class="feed-avatar" src="${resolveAvatar(item.avatar_url || "", item.middleman || "MM")}" alt="${escapeHTML(item.middleman)} avatar" loading="lazy" />
            <div>
              <div class="feed-author">${escapeHTML(item.middleman)}</div>
              <div class="feed-meta">${escapeHTML(item.vouched_by)}</div>
            </div>
          </div>
          <div class="feed-meta">${escapeHTML(item.vouched_by)}</div>
          <div class="feed-meta">${escapeHTML(formatMoney(item.amount_delta))}</div>
          <div class="feed-meta">${escapeHTML(relativeTime(item.created_at))}</div>
        `;
        feedTarget.appendChild(row);
      });
    }

    if (teamTarget) {
      teamTarget.innerHTML = "";
      fallbackMiddlemen.slice(0, 6).forEach(member => {
        const card = document.createElement("article");
        card.className = "mm-card";
        card.innerHTML = `
          <div class="mm-header">
            <img class="mm-avatar" src="${resolveAvatar(member.avatar_url, member.display_name || member.username)}" alt="${escapeHTML(member.display_name || member.username)} avatar" loading="lazy" />
            <div>
              <div class="mm-name">${escapeHTML(member.display_name || member.username)}</div>
              <div class="mm-username">@${escapeHTML(member.username)}</div>
            </div>
          </div>
          <div class="mm-meta">
            <span>Vouches</span>
            <strong>${escapeHTML(formatNumber(member.vouch_count))}</strong>
          </div>
          <div class="verification-pill">Verified</div>
          <a href="/mm/?id=${encodeURIComponent(member.discord_id)}" class="card-link">View Profile</a>
        `;
        teamTarget.appendChild(card);
      });
    }
  }

  function parseId(value) {
    return String(value || "").replace(/[^\d]/g, "").slice(0, 50);
  }

  function formatJoinedDate(value) {
    return formatDate(value || new Date());
  }

  function createStatusPill(active) {
    return active ? '<span class="status-pill active">Active Middleman</span>' : '<span class="status-pill inactive">Inactive</span>';
  }

  function setBrandFallbacks() {
    document.querySelectorAll(".brand-logo-wrap img").forEach(img => {
      img.addEventListener("error", function () {
        this.style.display = "none";
        const fallback = this.parentElement.querySelector(".brand-fallback");
        if (fallback) {
          fallback.style.display = "inline-flex";
        }
      });
    });
  }

  function initPageSpecific() {
    const body = document.body;
    const page = body.dataset.page;

    if (page === "home") {
      renderHomeData();
    }

    if (page === "lookup") {
      const form = document.getElementById("lookup-form");
      const input = document.getElementById("lookup-input");
      const resultArea = document.getElementById("lookup-results");
      if (form && input && resultArea) {
        form.addEventListener("submit", async (event) => {
          event.preventDefault();
          const query = input.value.trim();
          if (!query) {
            setEmpty(resultArea, "No search entered", "Enter a Discord ID, username, or display name to look up a middleman.");
            return;
          }

          setLoading(resultArea, "Checking the public directory…");

          try {
            const supabase = initSupabase();
            if (!supabase) {
              const match = fallbackMiddlemen.find(item => {
                const byId = query.replace(/[^\d]/g, "") && item.discord_id === query.replace(/[^\d]/g, "");
                const byName = item.username.toLowerCase() === query.toLowerCase() || item.display_name.toLowerCase() === query.toLowerCase();
                return byId || byName;
              });

              if (!match) {
                setEmpty(resultArea, "No middleman was found matching that information.", "The person may not be registered, their username may have changed, or they may need to be verified using their exact Discord ID.");
                return;
              }

              renderPersonCard(resultArea, match);
              return;
            }

            const normalized = parseId(query);
            let { data, error } = await safeQuery({
              table: "middlemen",
              limit: 20
            });

            if (error) {
              throw error;
            }

            let match = null;
            if (normalized) {
              match = data.find(item => String(item.discord_id) === normalized);
            }

            if (!match) {
              const q = query.toLowerCase();
              match = data.find(item => String(item.username || "").toLowerCase() === q || String(item.display_name || "").toLowerCase() === q || (String(item.username || "").toLowerCase().includes(q) && q.length > 2));
            }

            if (!match) {
              setEmpty(resultArea, "No middleman was found matching that information.", "The person may not be registered, their username may have changed, or they may need to be verified using their exact Discord ID.");
              return;
            }

            renderPersonCard(resultArea, match);
          } catch (error) {
            setError(resultArea, "This lookup is temporarily unavailable. Please try again in a moment.");
          }
        });
      }
    }

    if (page === "mms") {
      const listTarget = document.getElementById("mm-list");
      const searchInput = document.getElementById("mm-search");
      if (listTarget && searchInput) {
        const render = (items) => {
          if (!items.length) {
            setEmpty(listTarget, "No active middlemen match this search.", "Try a different username, display name, or Discord ID.");
            return;
          }

          listTarget.innerHTML = "";
          items.forEach(member => {
            const card = document.createElement("article");
            card.className = "mm-card";
            card.innerHTML = `
              <div class="mm-header">
                <img class="mm-avatar" src="${resolveAvatar(member.avatar_url, member.display_name || member.username)}" alt="${escapeHTML(member.display_name || member.username)} avatar" loading="lazy" />
                <div>
                  <div class="mm-name">${escapeHTML(member.display_name || member.username)}</div>
                  <div class="mm-username">@${escapeHTML(member.username)}</div>
                </div>
              </div>
              <div class="mm-meta">
                <span>Vouches</span>
                <strong>${escapeHTML(formatNumber(member.vouch_count || 0))}</strong>
              </div>
              <div class="mm-meta">
                <span>Joined</span>
                <strong>${escapeHTML(formatDate(member.joined_at))}</strong>
              </div>
              ${createStatusPill(member.active)}
              <a class="card-link" href="/mm/?id=${encodeURIComponent(member.discord_id)}">View Profile</a>
            `;
            listTarget.appendChild(card);
          });
        };

        const loadData = async () => {
          setLoading(listTarget, "Loading middlemen…");
          try {
            const supabase = initSupabase();
            let records = fallbackMiddlemen.filter(item => item.active);
            if (supabase) {
              const result = await safeQuery({
                table: "middlemen",
                filters: [{ column: "active", op: "eq", value: true }],
                orderBy: { column: "vouch_count", ascending: false }
              });
              records = result.data.length ? result.data : records;
            }

            const all = [...records].sort((a, b) => (Number(b.vouch_count || 0) - Number(a.vouch_count || 0)));
            render(all);
            searchInput.addEventListener("input", (event) => {
              const value = event.target.value.trim().toLowerCase();
              if (!value) {
                render(all);
                return;
              }
              const filtered = all.filter(item => {
                const haystack = [item.display_name, item.username, item.discord_id].join(" ").toLowerCase();
                return haystack.includes(value);
              });
              render(filtered);
            });
          } catch (error) {
            setError(listTarget, "The middlemen directory is unavailable right now.");
          }
        };

        loadData();
      }
    }

    if (page === "mm-profile") {
      const id = parseId(new URLSearchParams(window.location.search).get("id"));
      const container = document.getElementById("mm-profile-content");
      if (container) {
        if (!id) {
          setEmpty(container, "No middleman selected", "Use the lookup tool to select a verified middleman profile.");
          return;
        }

        setLoading(container, "Loading profile…");

        (async () => {
          try {
            const supabase = initSupabase();
            let data = fallbackMiddlemen.find(item => String(item.discord_id) === String(id));
            if (supabase) {
              const result = await safeQuery({
                table: "middlemen",
                filters: [{ column: "discord_id", op: "eq", value: id }],
                single: true
              });
              if (result.data) data = result.data;
            }

            if (!data) {
              setEmpty(container, "No public profile found", "That Discord ID is not listed in the public middleman directory.");
              return;
            }

            const vouches = await safeQuery({
              table: "vouch_events",
              filters: [{ column: "vouched_for", op: "eq", value: String(data.discord_id) }],
              orderBy: { column: "created_at", ascending: false },
              limit: 20
            });

            const items = vouches.data && vouches.data.length ? vouches.data : fallbackVouchFeed.slice(0, 5).map((entry, index) => ({
              id: index + 1,
              vouched_by: entry.vouched_by,
              amount_delta: entry.amount_delta,
              created_at: entry.created_at,
              screenshot_url: entry.screenshot_url
            }));

            renderProfile(container, data, items);
          } catch (error) {
            setError(container, "This profile is temporarily unavailable.");
          }
        })();
      }
    }

    if (page === "stats") {
      const statsRoot = document.getElementById("stats-root");
      if (statsRoot) {
        const renderStats = async () => {
          setLoading(statsRoot, "Loading community stats…");
          try {
            const supabase = initSupabase();
            const fallback = {
              members: fallbackStats.members,
              online: fallbackStats.online,
              boosts: fallbackStats.boosts,
              total_vouches: fallbackStats.vouches,
              total_trades: fallbackStats.safeDeals,
              total_volume_usd: fallbackStats.tradeVolume,
              verified_middlemen: fallbackStats.verifiedMms
            };

            let guildData = fallback;
            if (supabase) {
              const result = await safeQuery({
                table: "guild_stats",
                limit: 1
              });
              if (result.data && result.data.length) {
                guildData = result.data[0];
              }
            }

            const numericData = [
              { label: "Members", value: guildData.member_count || fallback.members, key: "member_count" },
              { label: "Online", value: guildData.online_count || fallback.online, key: "online_count" },
              { label: "Boosts", value: guildData.boost_count || fallback.boosts, key: "boost_count" },
              { label: "Total Vouches", value: guildData.total_vouches || fallback.vouches, key: "total_vouches" },
              { label: "Total Trades", value: guildData.total_trades || fallback.safeDeals, key: "total_trades" },
              { label: "Total Volume", value: guildData.total_volume_usd || fallback.tradeVolume, key: "total_volume_usd" },
              { label: "Verified Middlemen", value: fallbackMiddlemen.filter(item => item.active).length, key: "verified_middlemen" }
            ];

            const statCards = document.getElementById("stat-cards");
            if (statCards) {
              statCards.innerHTML = numericData.map(item => `
                <div class="stat-card">
                  <div class="stat-card-label">${escapeHTML(item.label)}</div>
                  <div class="stat-card-value">${escapeHTML(item.label === "Total Volume" ? formatMoney(item.value) : formatNumber(item.value))}</div>
                </div>
              `).join("");
            }

            const events = await safeQuery({
              table: "vouch_events",
              orderBy: { column: "created_at", ascending: false },
              limit: 200
            });

            const chartRows = buildVouchChart(events.data.length ? events.data : fallbackVouchFeed);
            renderChart(chartRows);
          } catch (error) {
            document.getElementById("stats-root").innerHTML = `
              <div class="error-state">
                <h3>Statistics are currently unavailable</h3>
                <p>Community statistics will appear here once the public data is reachable.</p>
              </div>
            `;
          }
        };

        renderStats();
      }
    }

    if (page === "vouches") {
      const listTarget = document.getElementById("vouch-history");
      if (listTarget) {
        const params = new URLSearchParams(window.location.search);
        const olderThan = params.get("older_than");
        const loadOlder = document.getElementById("load-older-button");
        const renderList = async () => {
          setLoading(listTarget, "Loading vouch history…");

          try {
            const supabase = initSupabase();
            let records = fallbackVouchFeed;
            if (supabase) {
              let query = supabase.from("vouch_events").select("*" );
              if (olderThan) {
                query = query.lt("created_at", olderThan);
              }
              query = query.order("created_at", { ascending: false }).limit(20);
              const { data, error } = await query;
              if (!error && data && data.length) {
                records = data;
              }
            }

            if (!records.length) {
              setEmpty(listTarget, "No public vouches available", "There are no recent vouch events to display yet.");
              return;
            }

            listTarget.innerHTML = "";
            records.forEach(item => {
              const row = document.createElement("article");
              row.className = "vouch-item";
              row.innerHTML = `
                <img class="feed-avatar" src="${resolveAvatar("", item.middleman || "MM")}" alt="${escapeHTML(item.middleman)} avatar" loading="lazy" />
                <div>
                  <strong>${escapeHTML(item.middleman || "Middleman")}</strong><br />
                  <span class="feed-meta">vouched by ${escapeHTML(item.vouched_by || "Unknown")} • ${escapeHTML(relativeTime(item.created_at))}</span>
                </div>
                <div class="vouch-amount">${escapeHTML(formatMoney(item.amount_delta || 0))}</div>
              `;
              listTarget.appendChild(row);
            });

            if (loadOlder) {
              const oldest = records[records.length - 1];
              loadOlder.disabled = false;
              loadOlder.onclick = () => {
                if (!oldest || !oldest.created_at) return;
                const url = new URL(window.location.href);
                url.searchParams.set("older_than", oldest.created_at);
                window.location.href = url.toString();
              };
            }
          } catch (error) {
            setError(listTarget, "The public vouch history is temporarily unavailable.");
          }
        };

        renderList();
      }
    }

    if (page === "rules") {
      document.querySelectorAll(".nav-link").forEach(link => {
        if (link.getAttribute("href") === "/rules/") {
          link.classList.add("active");
        }
      });
    }

    if (page === "admin") {
      initAdminPage();
    }
  }

  function renderPersonCard(target, person) {
    target.innerHTML = `
      <div class="result-card">
        <div class="profile-header">
          <img class="profile-avatar" src="${resolveAvatar(person.avatar_url, person.display_name || person.username)}" alt="${escapeHTML(person.display_name || person.username)} avatar" loading="lazy" />
          <div class="profile-meta">
            <h2>${escapeHTML(person.display_name || person.username)}</h2>
            <p>@${escapeHTML(person.username)}</p>
          </div>
        </div>
        <div class="profile-grid">
          <div class="detail-card">
            <div class="detail-label">Discord ID</div>
            <div class="detail-value mono">${escapeHTML(person.discord_id)}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Vouch Count</div>
            <div class="detail-value">${escapeHTML(formatNumber(person.vouch_count || 0))}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Status</div>
            <div class="detail-value">${person.active ? "Active Middleman" : "Inactive"}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Joined</div>
            <div class="detail-value">${escapeHTML(formatDate(person.joined_at))}</div>
          </div>
        </div>
        <div class="warning-callout">
          <p><strong>Always verify the exact Discord ID.</strong> Display names and usernames can be copied. Impersonators may use similar public information or renamed accounts.</p>
        </div>
        <div class="hero-actions" style="margin-top: 18px;">
          <a class="button" href="/mm/?id=${encodeURIComponent(person.discord_id)}">View Middleman Profile</a>
        </div>
      </div>
    `;
  }

  function renderProfile(container, person, vouches) {
    const hasVouches = Array.isArray(vouches) && vouches.length > 0;
    container.innerHTML = `
      <div class="profile-shell">
        <div class="profile-header">
          <img class="profile-avatar" src="${resolveAvatar(person.avatar_url, person.display_name || person.username)}" alt="${escapeHTML(person.display_name || person.username)} avatar" loading="lazy" />
          <div class="profile-meta">
            <h2>${escapeHTML(person.display_name || person.username)}</h2>
            <p>@${escapeHTML(person.username)}</p>
            <div class="verification-pill">Verified Middleman</div>
          </div>
        </div>

        <div class="profile-grid">
          <div class="detail-card">
            <div class="detail-label">Discord ID</div>
            <div class="detail-value mono">${escapeHTML(person.discord_id)}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Vouch Count</div>
            <div class="detail-value">${escapeHTML(formatNumber(person.vouch_count || 0))}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Earnings</div>
            <div class="detail-value">${escapeHTML(formatMoney(person.earnings || 0))}</div>
          </div>
          <div class="detail-card">
            <div class="detail-label">Joined</div>
            <div class="detail-value">${escapeHTML(formatDate(person.joined_at))}</div>
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

        ${hasVouches ? `
          <div class="vouch-list">
            ${vouches.slice(0, 10).map(item => `
              <article class="vouch-item">
                <img class="feed-avatar" src="${resolveAvatar("", item.vouched_by || "MM")}" alt="${escapeHTML(item.vouched_by || "User")} avatar" loading="lazy" />
                <div>
                  <strong>${escapeHTML(item.vouched_by || "Unknown")}</strong><br />
                  <span class="feed-meta">${escapeHTML(relativeTime(item.created_at))}</span>
                </div>
                <div class="vouch-amount">${escapeHTML(formatMoney(item.amount_delta || 0))}</div>
              </article>
            `).join("")}
          </div>
        ` : `
          <div class="empty-state">
            <h3>No public vouches yet</h3>
            <p>This middleman does not have any public vouches in the directory.</p>
          </div>
        `}
      </div>
    `;
  }

  function buildVouchChart(rows) {
    const today = new Date();
    const days = [];
    for (let i = 29; i >= 0; i -= 1) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const key = date.toISOString().slice(0, 10);
      days.push({ key, label: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }), value: 0 });
    }

    rows.forEach(item => {
      if (!item.created_at) return;
      const key = new Date(item.created_at).toISOString().slice(0, 10);
      const row = days.find(day => day.key === key);
      if (row) row.value += 1;
    });

    const maxValue = Math.max(1, ...days.map(day => day.value));
    return days.map(day => ({ ...day, percent: (day.value / maxValue) * 100 }));
  }

  function renderChart(days) {
    const chart = document.getElementById("vouch-chart");
    if (!chart) return;

    if (!days.length || days.every(day => day.value === 0)) {
      chart.innerHTML = `<div class="empty-state"><h3>Not enough vouch activity yet</h3><p>Chart data will appear as public vouch history builds up.</p></div>`;
      return;
    }

    const width = 860;
    const height = 220;
    const padding = 24;
    const points = days.map((day, index) => {
      const x = padding + (index * (width - padding * 2)) / (days.length - 1);
      const y = height - padding - (day.percent / 100) * (height - padding * 2);
      return `${x},${y}`;
    }).join(" ");

    const labels = days.filter((_, index) => index % 5 === 0 || index === days.length - 1).map(day => `
      <g>
        <text x="${padding + ((days.indexOf(day) * (width - padding * 2)) / (days.length - 1))}" y="${height - 6}" font-size="10" fill="#a08060" text-anchor="middle">${escapeHTML(day.label)}</text>
      </g>
    `).join("");

    chart.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="30-day vouch history chart">
        <defs>
          <linearGradient id="chartFill" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="#ff8c1a"/>
            <stop offset="100%" stop-color="#ffd88a"/>
          </linearGradient>
        </defs>
        <path d="M ${padding} ${height - padding} L ${days.map((day, index) => {
          const x = padding + (index * (width - padding * 2)) / (days.length - 1);
          const y = height - padding - (day.percent / 100) * (height - padding * 2);
          return ` ${x} ${y}`;
        }).join(" ")} L ${width - padding} ${height - padding} Z" fill="rgba(255, 140, 26, 0.12)"/>
        <polyline points="${points}" fill="none" stroke="url(#chartFill)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        ${days.map((day, index) => {
          const x = padding + (index * (width - padding * 2)) / (days.length - 1);
          const y = height - padding - (day.percent / 100) * (height - padding * 2);
          return `<circle cx="${x}" cy="${y}" r="3" fill="#ffd88a" />`;
        }).join("")}
        ${labels}
      </svg>
    `;
  }

  function initAdminPage() {
    const authBox = document.getElementById("admin-auth-box");
    const configForm = document.getElementById("admin-config-form");
    const statusBox = document.getElementById("admin-status");
    const statusBoxAlt = document.getElementById("admin-status-2");
    const passwordInput = document.getElementById("admin-password");
    const loginButton = document.getElementById("admin-login");

    if (!authBox || !configForm || !statusBox || !passwordInput || !loginButton) return;

    const localKey = "mm2base-admin-auth";
    const isAuthenticated = () => localStorage.getItem(localKey) === "true";

    const setStatus = (message, type, target = statusBox) => {
      target.textContent = message;
      target.className = "status-message visible " + type;
    };

    const showAuth = () => {
      authBox.hidden = false;
      configForm.hidden = true;
    };

    const showConfig = () => {
      authBox.hidden = true;
      configForm.hidden = false;
    };

    if (!isAuthenticated()) {
      showAuth();
    } else {
      showConfig();
    }

    loginButton.addEventListener("click", () => {
      const password = passwordInput.value.trim();
      if (password === "mm2admin") {
        localStorage.setItem(localKey, "true");
        showConfig();
        setStatus("Authenticated successfully.", "success");
      } else {
        setStatus("Incorrect temporary password.", "error");
      }
    });

    const saveButton = document.getElementById("save-config");
    if (saveButton) {
      saveButton.addEventListener("click", async () => {
        const key = document.getElementById("config-key").value.trim();
        const value = document.getElementById("config-value").value.trim();
        const supabase = initSupabase();
        const target = statusBoxAlt || statusBox;

        if (!supabase) {
          setStatus("Admin configuration storage is unavailable because Supabase is not configured.", "error", target);
          return;
        }

        if (!key || !value) {
          setStatus("Configuration key and value are required.", "error", target);
          return;
        }

        try {
          const { error } = await supabase.from("site_config").upsert({ key, value });
          if (error) {
            throw error;
          }
          setStatus("Saved successfully to site_config.", "success", target);
        } catch (error) {
          setStatus("Write failed. The admin panel could not save the configuration.", "error", target);
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initFAQ();
    initProgressBars();
    updateFooterYear();
    setBrandFallbacks();
    initPageSpecific();
  });

  window.MM2_BASE_APP = {
    escapeHTML,
    formatNumber,
    formatMoney,
    formatDate,
    relativeTime,
    setLoading,
    setError,
    setEmpty,
    resolveAvatar,
    safeQuery,
    initSupabase,
    fallbackMiddlemen,
    fallbackVouchFeed,
    fallbackStats,
    buildVouchChart,
    renderChart,
    initAdminPage
  };
})();
