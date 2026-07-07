/**
 * TS Deal Hunter AI — frontend logic.
 *
 * IMPORTANT (temporary): the backend /search endpoint does not exist yet
 * (MVP Step 2/3 still in progress). Until it's live, this file falls back
 * to MOCK_RESULTS so the UI/PWA/APK can be tested end-to-end today.
 * Once the real endpoint is deployed, just set API_BASE below and
 * everything else keeps working unchanged.
 */

// Set this to your deployed backend URL once it's live, e.g.
// "https://api.tsdealhunter.com" — leave empty to always use mock data.
const API_BASE = "https://ts-deal-hunter-api.onrender.com";

const MOCK_RESULTS = [
  {
    title: "NVIDIA RTX 4090 24GB Founders Edition",
    price: 1249.99,
    currency: "USD",
    marketplace: "eBay",
    seller: "techliquidators",
    location: "Berlin, DE",
    condition: "used",
    published_at: "2026-07-05T10:00:00Z",
    url: "https://www.ebay.com/",
    image: "",
  },
  {
    title: "Sony WH-1000XM6 Wireless Noise Cancelling",
    price: 289.0,
    currency: "USD",
    marketplace: "OLX",
    seller: "audio_deals",
    location: "Kyiv, UA",
    condition: "new",
    published_at: "2026-07-06T08:30:00Z",
    url: "https://www.olx.ua/",
    image: "",
  },
  {
    title: "Sony PlayStation 5 Slim Disc Edition",
    price: 379.5,
    currency: "USD",
    marketplace: "eBay",
    seller: "gamestop_outlet",
    location: "Warsaw, PL",
    condition: "new",
    published_at: "2026-07-01T12:00:00Z",
    url: "https://www.ebay.com/",
    image: "",
  },
];

const form = document.getElementById("search-form");
const queryInput = document.getElementById("query");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const filters = {
  minPrice: document.getElementById("filter-min-price"),
  maxPrice: document.getElementById("filter-max-price"),
  marketplace: document.getElementById("filter-marketplace"),
  condition: document.getElementById("filter-condition"),
  sortBy: document.getElementById("sort-by"),
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;
  await runSearch(query);
});

async function runSearch(query) {
  setStatus(`Шукаємо "${query}"...`);
  resultsEl.innerHTML = "";

  let results;
  try {
    results = await fetchFromApi(query);
  } catch (err) {
    results = applyClientFilters(MOCK_RESULTS, query);
    setStatus(
      `Бекенд ще не підключений — показані тестові дані (${results.length}).`
    );
    renderResults(results);
    return;
  }

  setStatus(`Знайдено: ${results.length}`);
  renderResults(results);
}

async function fetchFromApi(query) {
  if (!API_BASE) throw new Error("API_BASE not configured");

  const params = new URLSearchParams({ q: query });
  if (filters.minPrice.value) params.set("min_price", filters.minPrice.value);
  if (filters.maxPrice.value) params.set("max_price", filters.maxPrice.value);
  if (filters.marketplace.value) params.set("marketplace", filters.marketplace.value);
  if (filters.condition.value) params.set("condition", filters.condition.value);
  if (filters.sortBy.value) params.set("sort_by", filters.sortBy.value);

  const res = await fetch(`${API_BASE}/search?${params.toString()}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function applyClientFilters(items, query) {
  const q = query.toLowerCase();
  let filtered = items.filter((item) => item.title.toLowerCase().includes(q));

  const min = parseFloat(filters.minPrice.value);
  const max = parseFloat(filters.maxPrice.value);
  if (!isNaN(min)) filtered = filtered.filter((i) => i.price >= min);
  if (!isNaN(max)) filtered = filtered.filter((i) => i.price <= max);

  if (filters.marketplace.value) {
    filtered = filtered.filter(
      (i) => i.marketplace.toLowerCase() === filters.marketplace.value
    );
  }
  if (filters.condition.value) {
    filtered = filtered.filter((i) => i.condition === filters.condition.value);
  }

  switch (filters.sortBy.value) {
    case "price_desc":
      filtered.sort((a, b) => b.price - a.price);
      break;
    case "newest":
      filtered.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
      break;
    case "oldest":
      filtered.sort((a, b) => new Date(a.published_at) - new Date(b.published_at));
      break;
    default:
      filtered.sort((a, b) => a.price - b.price);
  }

  return filtered;
}

function renderResults(items) {
  if (items.length === 0) {
    resultsEl.innerHTML = `<div class="empty-state">Нічого не знайдено. Спробуй іншу назву товару.</div>`;
    return;
  }

  resultsEl.innerHTML = items
    .map((item) => {
      const price = `${item.price.toFixed(2)} ${item.currency}`;
      const published = item.published_at
        ? new Date(item.published_at).toLocaleDateString("uk-UA")
        : "";
      const img = item.image || "icons/icon-192.png";

      return `
        <a class="deal-card" href="${item.url}" target="_blank" rel="noopener">
          <img src="${img}" alt="" loading="lazy" />
          <div class="deal-info">
            <p class="deal-title">${escapeHtml(item.title)}</p>
            <div class="deal-price">${price}</div>
            <div class="deal-meta">
              <span class="badge">${item.marketplace}</span>
              <span class="badge">${item.condition}</span>
              ${item.location ? `<span class="badge">${item.location}</span>` : ""}
            </div>
            <div class="deal-meta">${item.seller || ""} ${published ? "· " + published : ""}</div>
          </div>
        </a>
      `;
    })
    .join("");
}

function setStatus(text) {
  statusEl.textContent = text;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Register service worker for offline shell / installability
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {
      /* non-fatal — app still works online without it */
    });
  });
}
