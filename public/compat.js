// Chrome 81 compatibility polyfills for Ant Design 5 CSS-in-JS
(function() {
  // CSS.supports() - used by @ant-design/cssinjs
  if (!window.CSS) window.CSS = {};
  if (!CSS.supports) {
    CSS.supports = function(prop, value) {
      try {
        if (arguments.length === 1) {
          // @supports (property: value) format
          var el = document.createElement('div');
          el.style.cssText = prop;
          return el.style.length > 0;
        }
        var el = document.createElement('div');
        el.style[prop] = value;
        return el.style[prop] !== '';
      } catch (e) {
        return false;
      }
    };
  }

  // document.adoptedStyleSheets
  if (!document.adoptedStyleSheets) document.adoptedStyleSheets = [];

  // CSSStyleSheet.prototype.replaceSync
  if (typeof CSSStyleSheet !== 'undefined' && !CSSStyleSheet.prototype.replaceSync) {
    CSSStyleSheet.prototype.replaceSync = function() {};
  }

  // ResizeObserver
  if (typeof ResizeObserver === 'undefined') {
    window.ResizeObserver = function(callback) {
      this.callback = callback; this.observations = new Map();
    };
    ResizeObserver.prototype.observe = function(target) {
      this.observations.set(target, true);
      if (this._timer) clearInterval(this._timer);
      this._timer = setInterval(function() {
        var entries = [];
        this.observations.forEach(function(_, t) {
          entries.push({ target: t, contentRect: t.getBoundingClientRect() });
        }.bind(this));
        if (entries.length) this.callback(entries);
      }.bind(this), 200);
    };
    ResizeObserver.prototype.unobserve = function(target) { this.observations.delete(target); };
    ResizeObserver.prototype.disconnect = function() {
      if (this._timer) clearInterval(this._timer); this.observations.clear();
    };
  }

  // Element.prototype.closest / matches
  if (!Element.prototype.matches) {
    Element.prototype.matches = Element.prototype.msMatchesSelector || Element.prototype.webkitMatchesSelector;
  }
  if (!Element.prototype.closest) {
    Element.prototype.closest = function(s) {
      var el = this;
      do { if (el.matches(s)) return el; el = el.parentElement || el.parentNode; } while (el !== null && el.nodeType === 1);
      return null;
    };
  }

  // Object.fromEntries
  if (!Object.fromEntries) {
    Object.fromEntries = function(entries) {
      var obj = {}; for (var i = 0; i < entries.length; i++) obj[entries[i][0]] = entries[i][1]; return obj;
    };
  }

  // Array.prototype.flat / flatMap
  if (!Array.prototype.flat) {
    Array.prototype.flat = function(depth) {
      depth = depth === undefined ? 1 : depth; var result = [];
      for (var i = 0; i < this.length; i++) {
        if (Array.isArray(this[i]) && depth > 0) result = result.concat(this[i].flat(depth - 1));
        else result.push(this[i]);
      } return result;
    };
  }
  if (!Array.prototype.flatMap) {
    Array.prototype.flatMap = function(cb) { return this.map(cb).flat(); };
  }

  // String.prototype.replaceAll
  if (!String.prototype.replaceAll) {
    String.prototype.replaceAll = function(s, r) { return this.split(s).join(r); };
  }

  // globalThis
  if (typeof globalThis === 'undefined') {
    (typeof self !== 'undefined' ? self : typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : {}).globalThis = typeof self !== 'undefined' ? self : typeof window !== 'undefined' ? window : typeof global !== 'undefined' ? global : {};
  }

  // Promise.allSettled
  if (!Promise.allSettled) {
    Promise.allSettled = function(promises) {
      return Promise.all(promises.map(function(p) {
        return Promise.resolve(p).then(
          function(v) { return { status: 'fulfilled', value: v }; },
          function(r) { return { status: 'rejected', reason: r }; }
        );
      }));
    };
  }

  // queueMicrotask
  if (typeof queueMicrotask === 'undefined') {
    window.queueMicrotask = function(cb) { Promise.resolve().then(cb); };
  }

  // structuredClone
  if (typeof structuredClone === 'undefined') {
    window.structuredClone = function(obj) { return JSON.parse(JSON.stringify(obj)); };
  }
})();
