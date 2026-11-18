/* =============================================================================
   FILE:      frontend/js/websocket.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/websocket.js
   PURPOSE:   Single WebSocket connection for the entire app. Dispatches
              incoming messages to the correct module by `type`.
              Reconnects automatically every 5 seconds.
   ============================================================================= */

window.WS = (function () {
  let socket = null;
  const handlers = {};   // type -> [fn]

  function register(type, fn) {
    if (!handlers[type]) handlers[type] = [];
    handlers[type].push(fn);
  }

  function dispatch(msg) {
    if (!msg || !msg.type) return;
    const list = handlers[msg.type] || [];
    list.forEach((fn) => { try { fn(msg); } catch (e) { console.error(e); } });
    const anyList = handlers["*"] || [];
    anyList.forEach((fn) => { try { fn(msg); } catch (e) { console.error(e); } });
  }

  function connect() {
    try {
      socket = new WebSocket(APP_CONFIG.WS_URL);
      socket.onopen = () => console.log("[WS] connected");
      socket.onmessage = (ev) => {
        try { dispatch(JSON.parse(ev.data)); }
        catch (e) { console.error("WS parse error", e); }
      };
      socket.onclose = () => {
        console.log("[WS] closed, retrying in 5s");
        setTimeout(connect, 5000);
      };
      socket.onerror = () => { try { socket.close(); } catch (e) {} };
    } catch (e) {
      console.error("WS connect failed", e);
      setTimeout(connect, 5000);
    }
  }

  function start() { if (!socket) connect(); }

  return { start, register };
})();
