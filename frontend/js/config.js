/* =============================================================================
   FILE:      frontend/js/config.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/config.js
   PURPOSE:   Global constants used by every other JS file. Loaded first.
   ============================================================================= */

window.APP_CONFIG = {
  BACKEND_URL: "",                              // same origin
  WS_URL: (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws",
  REFRESH_INTERVAL_MS: 10000,                   // irrigation data refresh
  SURVEILLANCE_FRAME_INTERVAL_MS: 800,          // frame POST cadence
  SURVEILLANCE_CHUNK_MS: 5 * 60 * 1000,         // 5-minute chunks
  SURVEILLANCE_KEEP_THRESHOLD: 0.35,
  ADMIN_STORAGE_KEY: "itf_admin_key",
};
