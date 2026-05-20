/**
 * TRS Platform — Real-time Client Library
 * Manages WebSocket connections for live sync across all modules
 */
window.TRSRealtime = (function () {
  const sockets  = {};
  const handlers = {};
  const MAX_RECONNECT_MS = 8000;

  function _wsUrl(channel) {
    const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
    return proto + location.host + '/ws/trs/' + channel;
  }

  function connect(channel, onMessage) {
    if (sockets[channel] && sockets[channel].readyState < 2) {
      if (onMessage) handlers[channel] = onMessage;
      return sockets[channel];
    }

    if (onMessage) handlers[channel] = onMessage;

    const ws = new WebSocket(_wsUrl(channel));
    sockets[channel] = ws;

    ws.onopen = () => {
      console.log('[TRS] WS connected:', channel);
      try { toast('🔗 Live sync connected', 'success', 1600); } catch (e) {}
    };

    ws.onmessage = (ev) => {
      let msg = {};
      try { msg = JSON.parse(ev.data); } catch (e) {}
      // Call registered handler
      const h = handlers[channel];
      if (h) { try { h(msg); } catch (e) {} }
      // Also dispatch global event so any page can listen
      window.dispatchEvent(new CustomEvent('trs:message', { detail: { channel, msg } }));
    };

    ws.onerror = (e) => {
      console.warn('[TRS] WS error:', channel, e);
    };

    ws.onclose = () => {
      console.log('[TRS] WS closed:', channel, '— reconnecting...');
      delete sockets[channel];
      // Exponential back-off capped at MAX_RECONNECT_MS
      const delay = Math.min(MAX_RECONNECT_MS, 2500 + Math.random() * 1000);
      setTimeout(() => connect(channel, handlers[channel]), delay);
    };

    return ws;
  }

  function send(channel, data) {
    const ws = sockets[channel];
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  function disconnect(channel) {
    if (sockets[channel]) {
      sockets[channel].onclose = null; // prevent auto-reconnect
      sockets[channel].close();
      delete sockets[channel];
      delete handlers[channel];
    }
  }

  function status(channel) {
    const ws = sockets[channel];
    if (!ws) return 'disconnected';
    return ['connecting', 'open', 'closing', 'closed'][ws.readyState] || 'unknown';
  }

  function injectStatusBadge() {
    if (document.getElementById('trs-live-badge')) return;
    const el = document.createElement('div');
    el.id = 'trs-live-badge';
    el.style.cssText = 'position:fixed;right:16px;bottom:14px;z-index:9999;padding:8px 12px;border:1px solid rgba(34,211,238,.35);background:rgba(6,18,30,.92);color:#a7f3ff;border-radius:999px;font:12px Segoe UI,Arial;box-shadow:0 10px 30px rgba(0,0,0,.35)';
    el.textContent = '● Live sync ready';
    document.body.appendChild(el);
    window.addEventListener('trs:message', (e) => {
      const msg = e.detail && e.detail.msg ? e.detail.msg : {};
      if (msg.type === 'presence') el.textContent = `● Live sync · ${msg.clients || 1} online`;
      else if (msg.type) el.textContent = `● Live sync · ${msg.type.replaceAll('_',' ')}`;
      clearTimeout(el._t);
      el._t = setTimeout(()=>{ el.textContent = '● Live sync connected'; }, 3500);
    });
  }

  /** Safe live-update helper. It never reloads the whole page. */
  function autoReload(channel, filterFn) {
    connect(channel, (msg) => {
      if (!msg.type || msg.type === 'presence' || msg.type === 'ping') return;
      if (filterFn && !filterFn(msg)) return;
      try { toast('Live update: ' + String(msg.type).replaceAll('_',' '), 'info', 1800); } catch (e) {}
      window.dispatchEvent(new CustomEvent('trs:realtime', { detail: { channel, msg } }));
    });
  }

  return { connect, send, disconnect, status, autoReload, injectStatusBadge };
})();
