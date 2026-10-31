/*
 * Bilingual toggle for alejandratamez.com
 * Content lives side by side in each page: elements marked data-lang="en" or data-lang="es".
 * This script picks the language (URL ?lang=, then saved choice, then browser language),
 * sets <html lang>, swaps the page title, and wires up the EN / ES switch.
 */
(function () {
  var KEY = 'site-lang';
  var root = document.documentElement;

  function pick() {
    try {
      var q = new URLSearchParams(window.location.search).get('lang');
      if (q === 'es' || q === 'en') return q;
    } catch (e) {}
    try {
      var saved = window.localStorage.getItem(KEY);
      if (saved === 'es' || saved === 'en') return saved;
    } catch (e) {}
    var nav = (navigator.language || 'en').toLowerCase();
    return nav.indexOf('es') === 0 ? 'es' : 'en';
  }

  function apply(lang) {
    root.setAttribute('lang', lang);
    var t = root.getAttribute('data-title-' + lang);
    if (t) document.title = t;
    var buttons = document.querySelectorAll('.lang-switch button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', buttons[i].getAttribute('data-set-lang') === lang ? 'true' : 'false');
    }
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang: lang } }));
  }

  window.siteLang = function () { return root.getAttribute('lang') === 'es' ? 'es' : 'en'; };

  // Set language before first paint to avoid a flash of the wrong copy.
  root.setAttribute('lang', pick());

  document.addEventListener('DOMContentLoaded', function () {
    apply(window.siteLang());
    var buttons = document.querySelectorAll('.lang-switch button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener('click', function () {
        var lang = this.getAttribute('data-set-lang');
        try { window.localStorage.setItem(KEY, lang); } catch (e) {}
        apply(lang);
      });
    }
  });
})();
