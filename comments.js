/* Soul Wired comments.
   Adds a comment section to blog posts published on or after START_DATE.
   Comments live in a Google Sheet (see scripts/comments-apps-script.gs) and
   only show here after Ale ticks Approved. Readers don't sign up. */
(function () {
  'use strict';

  // The Google Apps Script web app URL (ends in /exec). Empty = comments off.
  var ENDPOINT = '';
  var START_DATE = new Date(2026, 10, 24); // November 24, 2026

  var ES = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0;
  var T = ES ? {
    title: 'Comentarios',
    none: 'Todavía no hay comentarios. Sé la primera persona en comentar.',
    loadError: 'No pudimos cargar los comentarios en este momento.',
    name: 'Tu nombre',
    comment: 'Tu comentario',
    note: 'No necesitas registrarte. Los comentarios aparecen después de que Ale los lee.',
    post: 'Publicar comentario',
    sending: 'Enviando…',
    thanks: '¡Gracias! Tu comentario aparecerá en cuanto Ale lo apruebe.',
    error: 'Algo salió mal. Por favor intenta de nuevo.',
    missing: 'Escribe tu nombre y tu comentario.'
  } : {
    title: 'Comments',
    none: 'No comments yet. Be the first to share your thoughts.',
    loadError: "Comments couldn't load right now.",
    name: 'Your name',
    comment: 'Your comment',
    note: "No sign-up needed. Comments show up after Ale reads them.",
    post: 'Post comment',
    sending: 'Sending…',
    thanks: "Thank you! Your comment will show up once Ale approves it.",
    error: 'Something went wrong. Please try again.',
    missing: 'Please add your name and a comment.'
  };

  var MONTHS_ES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
    'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

  // "November 24, 2026 · 3 min read" or "24 de noviembre de 2026 · 3 min de lectura"
  function postDate(text) {
    var part = text.split('·')[0].trim();
    var m = part.match(/^(\d{1,2}) de ([a-záéíóú]+) de (\d{4})$/i);
    if (m) {
      var month = MONTHS_ES.indexOf(m[2].toLowerCase());
      return month < 0 ? null : new Date(+m[3], month, +m[1]);
    }
    var d = new Date(part);
    return isNaN(d) ? null : d;
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function formatDate(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return '';
    return d.toLocaleDateString(ES ? 'es-MX' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function init() {
    if (!ENDPOINT) return;
    var match = location.pathname.match(/\/blog\/([a-z0-9-]+)\.html$/i);
    var body = document.querySelector('.article-body');
    var meta = document.querySelector('.read-time');
    if (!match || !body || !meta) return;
    var date = postDate(meta.textContent);
    if (!date || date < START_DATE) return;

    var slug = match[1].toLowerCase();
    var openedAt = Date.now();

    var section = el('section', 'sw-comments');
    section.id = 'comments';
    section.setAttribute('aria-labelledby', 'sw-comments-title');
    var heading = el('h2', 'sw-comments-title', T.title);
    heading.id = 'sw-comments-title';
    var list = el('ol', 'sw-comments-list');
    var status = el('p', 'sw-comments-empty');
    section.appendChild(heading);
    section.appendChild(status);
    section.appendChild(list);

    // form
    var form = el('form', 'sw-comment-form');
    form.noValidate = true;
    var nameLabel = el('label', 'sw-label', T.name);
    var nameInput = el('input');
    nameInput.type = 'text'; nameInput.name = 'name'; nameInput.maxLength = 60;
    nameInput.autocomplete = 'name'; nameInput.required = true; nameInput.id = 'sw-comment-name';
    nameLabel.htmlFor = 'sw-comment-name';
    var textLabel = el('label', 'sw-label', T.comment);
    var textInput = el('textarea');
    textInput.name = 'comment'; textInput.maxLength = 2000; textInput.rows = 5;
    textInput.required = true; textInput.id = 'sw-comment-text';
    textLabel.htmlFor = 'sw-comment-text';
    // hidden from people, tempting to bots
    var trap = el('input', 'sw-trap');
    trap.type = 'text'; trap.name = 'website'; trap.tabIndex = -1;
    trap.autocomplete = 'off'; trap.setAttribute('aria-hidden', 'true');
    var note = el('p', 'sw-comment-note', T.note);
    var button = el('button', 'sw-comment-button', T.post);
    button.type = 'submit';
    var message = el('p', 'sw-comment-message');
    message.setAttribute('role', 'status');

    [nameLabel, nameInput, textLabel, textInput, trap, note, button, message]
      .forEach(function (n) { form.appendChild(n); });
    section.appendChild(form);

    var anchor = document.querySelector('.post-nav');
    if (anchor) anchor.parentNode.insertBefore(section, anchor);
    else body.parentNode.insertBefore(section, body.nextSibling);

    function render(comments) {
      list.textContent = '';
      heading.textContent = comments.length ? T.title + ' (' + comments.length + ')' : T.title;
      status.textContent = comments.length ? '' : T.none;
      status.hidden = !!comments.length;
      comments.forEach(function (c) {
        var item = el('li', 'sw-comment');
        var head = el('p', 'sw-comment-meta');
        head.appendChild(el('span', 'sw-comment-name', c.name));
        head.appendChild(el('span', 'sw-comment-date', formatDate(c.date)));
        item.appendChild(head);
        item.appendChild(el('p', 'sw-comment-text', c.comment));
        list.appendChild(item);
      });
    }

    fetch(ENDPOINT + '?post=' + encodeURIComponent(slug))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || !data.ok) throw new Error('bad response');
        render(data.comments || []);
      })
      .catch(function () { status.textContent = T.loadError; });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = nameInput.value.trim();
      var comment = textInput.value.trim();
      if (!name || !comment) { message.textContent = T.missing; return; }
      if (trap.value || Date.now() - openedAt < 3000) {
        // almost certainly a bot: act as if it worked
        message.textContent = T.thanks; textInput.value = ''; return;
      }
      button.disabled = true;
      button.textContent = T.sending;
      message.textContent = '';
      fetch(ENDPOINT, {
        method: 'POST',
        body: JSON.stringify({ post: slug, name: name, comment: comment, website: trap.value })
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data || !data.ok) throw new Error('not saved');
          message.textContent = T.thanks;
          textInput.value = '';
        })
        .catch(function () { message.textContent = T.error; })
        .then(function () { button.disabled = false; button.textContent = T.post; });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
