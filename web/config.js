// Use the local API during development and same-origin API routes on Vercel.
const isLocalHost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
window.VEDIC_CONFIG = {
  API_BASE: isLocalHost ? "http://127.0.0.1:8000" : "",
  SOURCE_URL: "https://github.com/founder-dax-limbasiya/-vedic-ai-mvp"
};
