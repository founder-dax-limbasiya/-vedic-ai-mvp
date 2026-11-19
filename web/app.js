const API_BASE = (window.VEDIC_CONFIG?.API_BASE || "").replace(/\/$/, "");
const form = document.getElementById("chart-form");
const submitButton = document.getElementById("submit-button");
const errorBox = document.getElementById("form-error");
const results = document.getElementById("results");
let lastChart = null;

const get = (id) => document.getElementById(id);
const localNow = new Date();
const dateToday = `${localNow.getFullYear()}-${String(localNow.getMonth()+1).padStart(2,"0")}-${String(localNow.getDate()).padStart(2,"0")}`;
get("birth-date").max = dateToday;

async function loadTimezones() {
  try {
    const response = await fetch(`${API_BASE}/v1/timezones?q=`);
    if (!response.ok) return;
    const data = await response.json();
    get("timezone-list").innerHTML = data.timezones.map((zone) => `<option value="${escapeHtml(zone)}"></option>`).join("");
  } catch (_) { /* Manual IANA timezone entry remains available. */ }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
}

function formatDate(value) {
  const parts = String(value).slice(0, 10).split("-").map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) return value;
  const date = new Date(parts[0], parts[1]-1, parts[2]);
  return new Intl.DateTimeFormat(undefined, {year:"numeric",month:"short",day:"numeric"}).format(date);
}

function todayInTimezone(timeZone) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone, year:"numeric", month:"2-digit", day:"2-digit"
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function renderVarga(chart, code) {
  const varga = chart.divisional_charts?.[code];
  if (!varga) {
    get("division-summary").textContent = "This divisional chart is unavailable in the calculation response.";
    get("varga-rows").innerHTML = "";
    return;
  }
  get("division-summary").textContent = `${code} · ${varga.name} · Ascendant: ${varga.ascendant_sign}`;
  get("varga-rows").innerHTML = varga.planets.map((planet) => `
    <tr><td>${escapeHtml(planet.planet)}</td><td>${escapeHtml(planet.sign)}</td></tr>`).join("");
}

function renderChart(chart) {
  lastChart = chart;
  get("daily-date").value = todayInTimezone(chart.birth.timezone);
  get("asc-sign").textContent = chart.ascendant.sign;
  get("asc-detail").textContent = `${chart.ascendant.degree_in_sign.toFixed(2)}° · ${chart.ascendant.nakshatra} · Pada ${chart.ascendant.pada}`;
  get("meta-grid").innerHTML = [
    ["Birth time", chart.birth.local_datetime.replace("T", " ")],
    ["Time zone", chart.birth.timezone],
    ["Ayanamsa", chart.settings.ayanamsa.replaceAll("_", " ")],
    ["Ayanamsa value", `${chart.ayanamsa_degrees.toFixed(4)}°`],
    ["House system", chart.settings.house_system],
    ["UTC offset", `${chart.birth.utc_offset_hours >= 0 ? "+" : ""}${chart.birth.utc_offset_hours}h`]
  ].map(([label,value]) => `<div class="meta-chip"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");

  get("planet-rows").innerHTML = chart.planets.map((planet) => `
    <tr><td>${escapeHtml(planet.planet)}</td><td>${escapeHtml(planet.sign)}</td>
    <td>${planet.degree_in_sign.toFixed(2)}°</td><td>${escapeHtml(planet.nakshatra)} · ${planet.pada}</td>
    <td class="${planet.retrograde ? "status-retro" : ""}">${planet.retrograde ? "Retrograde" : "Direct"}</td></tr>`).join("");

  get("house-grid").innerHTML = chart.houses.map((house) => `
    <div class="house-item"><span>House ${house.house}</span><strong>${escapeHtml(house.sign)}</strong><small>Lord: ${escapeHtml(house.lord)}</small></div>`).join("");

  const panchanga = chart.birth_panchanga || {};
  const panchangaItems = [
    ["Vara", panchanga.vara],
    ["Tithi", panchanga.tithi_name],
    ["Nakshatra", panchanga.nakshatra],
    ["Yoga", panchanga.yoga_name],
    ["Karana", panchanga.karana_name]
  ];
  get("panchanga-grid").innerHTML = panchangaItems.map(([label, value]) => `
    <div class="panchanga-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "Not available")}</strong></div>`).join("");
  const sunrise = panchanga.sunrise_local ? panchanga.sunrise_local.replace("T", " ") : "Unavailable";
  const sunset = panchanga.sunset_local ? panchanga.sunset_local.replace("T", " ") : "Unavailable";
  get("sunrise-sunset").textContent = `Birthplace local sunrise: ${sunrise} · sunset: ${sunset}`;

  get("dasha-list").innerHTML = chart.vimshottari_mahadashas.map((period) => `
    <div class="dasha-row"><strong>${escapeHtml(period.lord)}</strong><span>${formatDate(period.start_local)} – ${formatDate(period.end_local)}</span></div>`).join("");

  const divisionSelect = get("division-select");
  const divisionalCharts = chart.divisional_charts || {};
  const divisionCodes = Object.keys(divisionalCharts).sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)));
  divisionSelect.innerHTML = divisionCodes.map((code) => {
    const item = divisionalCharts[code];
    return `<option value="${escapeHtml(code)}">${escapeHtml(code)} · ${escapeHtml(item.name)}</option>`;
  }).join("");
  divisionSelect.value = divisionCodes.includes("D1") ? "D1" : (divisionCodes[0] || "");
  if (divisionSelect.value) renderVarga(chart, divisionSelect.value);

  const sources = Object.entries(chart.calculation.ephemeris_by_planet || {});
  const sourceNames = [...new Set(sources.map(([, source]) => source))];
  get("engine-note").innerHTML = `<strong>Calculation transparency</strong><br>Engine: ${escapeHtml(chart.calculation.engine)} · Ephemeris sources: ${sourceNames.map(escapeHtml).join(", ") || "Not reported"}.<br>${escapeHtml(chart.calculation.disclaimer)}`;
  results.hidden = false;
  results.scrollIntoView({behavior:"smooth",block:"start"});
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = "Calculating…";
  const foldValue = get("fold").value;
  const payload = {
    birth_date: get("birth-date").value,
    birth_time: get("birth-time").value,
    timezone: get("timezone").value.trim(),
    latitude: Number(get("latitude").value),
    longitude: Number(get("longitude").value),
    ayanamsa: get("ayanamsa").value,
    ...(foldValue === "" ? {} : {fold:Number(foldValue)})
  };
  try {
    const response = await fetch(`${API_BASE}/v1/chart`, {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail;
      throw new Error(typeof detail === "string" ? detail : (detail?.message || `Request failed (${response.status})`));
    }
    renderChart(data);
  } catch (error) {
    showError(error.message || "Could not calculate the chart. Check your connection and inputs.");
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = "Calculate my birth chart";
  }
});

get("division-select").addEventListener("change", () => {
  if (lastChart) renderVarga(lastChart, get("division-select").value);
});


get("load-daily-panchanga").addEventListener("click", async () => {
  if (!lastChart) return;
  const button = get("load-daily-panchanga");
  const error = get("daily-panchanga-error");
  error.hidden = true;
  button.disabled = true;
  button.textContent = "Loading…";
  try {
    const response = await fetch(`${API_BASE}/v1/panchanga`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        calendar_date: get("daily-date").value,
        timezone: lastChart.birth.timezone,
        latitude: lastChart.birth.latitude,
        longitude: lastChart.birth.longitude
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail;
      throw new Error(typeof detail === "string" ? detail : (detail?.message || `Request failed (${response.status})`));
    }
    const items = [
      ["Vara", data.vara],
      ["Tithi", data.tithi_name],
      ["Nakshatra", data.nakshatra],
      ["Yoga", data.yoga_name],
      ["Karana", data.karana_name]
    ];
    get("daily-panchanga-grid").innerHTML = items.map(([label,value]) => `
      <div class="panchanga-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "Not available")}</strong></div>`).join("");
    const sunrise = data.sunrise_local ? data.sunrise_local.replace("T", " ") : "Unavailable";
    const sunset = data.sunset_local ? data.sunset_local.replace("T", " ") : "Unavailable";
    get("daily-sunrise-sunset").textContent = `${data.calculation_time} · Sunrise: ${sunrise} · Sunset: ${sunset} · ${data.timezone}`;
  } catch (err) {
    error.textContent = err.message || "Could not load the daily Panchanga.";
    error.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Load Panchanga";
  }
});

get("new-chart").addEventListener("click", () => {
  results.hidden = true;
  form.scrollIntoView({behavior:"smooth",block:"start"});
});

get("download-json").addEventListener("click", () => {
  if (!lastChart) return;
  const blob = new Blob([JSON.stringify(lastChart, null, 2)], {type:"application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "vedic-birth-chart.json";
  anchor.click();
  URL.revokeObjectURL(url);
});

get("search-place").addEventListener("click", async () => {
  const query = get("place-name").value.trim();
  const button = get("search-place");
  const container = get("place-results");
  container.hidden = false;
  container.textContent = "Searching…";
  button.disabled = true;
  try {
    const response = await fetch(`${API_BASE}/v1/places?q=${encodeURIComponent(query)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Place search is unavailable.");
    if (!data.places?.length) throw new Error("No matching places found. Try a nearby city or enter coordinates manually.");
    container.innerHTML = data.places.map((place, index) => `<button type="button" class="place-option" data-index="${index}">${escapeHtml(place.label)}</button>`).join("");
    container.querySelectorAll("button").forEach((option) => option.addEventListener("click", async () => {
      const place = data.places[Number(option.dataset.index)];
      get("latitude").value = place.latitude;
      get("longitude").value = place.longitude;
      get("place-name").value = place.label;
      container.hidden = true;
      get("timezone-hint").textContent = "Getting the time zone from the selected coordinates…";
      try {
        const zoneResponse = await fetch(`${API_BASE}/v1/place-timezone?latitude=${place.latitude}&longitude=${place.longitude}`);
        const zoneData = await zoneResponse.json().catch(() => ({}));
        if (!zoneResponse.ok) throw new Error(zoneData.detail || "Automatic time-zone lookup unavailable.");
        get("timezone").value = zoneData.timezone;
        get("timezone-hint").textContent = `Suggested: ${zoneData.timezone}. Check that it matches the local civil time at the birthplace and birth date.`;
      } catch (zoneError) {
        get("timezone-hint").textContent = `${zoneError.message} Choose the IANA timezone manually.`;
      }
    }));
  } catch (error) {
    container.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

const sourceLink = get("source-link");
if (window.VEDIC_CONFIG?.SOURCE_URL) { sourceLink.href = window.VEDIC_CONFIG.SOURCE_URL; sourceLink.hidden = false; }

loadTimezones();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
}
