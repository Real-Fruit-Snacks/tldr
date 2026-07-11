/* SearchCore — pure tldr-page index matching. UMD so node tests can load it. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) { module.exports = factory(); }
  else { root.SearchCore = factory(); }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var PLATFORMS = ['common', 'linux', 'windows'];

  function matchPlatform(tok) {
    if (tok.length < 3) return null;
    for (var i = 0; i < PLATFORMS.length; i++) {
      if (PLATFORMS[i].indexOf(tok) === 0) return PLATFORMS[i];
    }
    return null;
  }

  function scoreName(name, tok) {
    if (name === tok) return 100;
    if (name.indexOf(tok) === 0) return 80;
    if (name.indexOf(tok) !== -1) return 60;
    return 0;
  }

  function search(db, query, limit) {
    limit = limit || 50;
    var q = String(query || '').trim().toLowerCase();
    if (!q || !db || !db.pages) return [];
    var tokens = q.split(/\s+/);
    var results = [];
    var pages = db.pages;
    var i, t, s;

    /* Platform filter: "tar linux", "linux tar", prefixes ("wsl win"),
       or a bare full platform name ("windows") listing that platform. */
    var platFilter = null;
    if (tokens.length > 1) {
      for (t = tokens.length - 1; t >= 0; t--) {
        var p = matchPlatform(tokens[t]);
        if (p) { platFilter = p; tokens.splice(t, 1); break; }
      }
    }
    if (!platFilter && tokens.length === 1 && PLATFORMS.indexOf(tokens[0]) !== -1) {
      platFilter = tokens[0]; tokens = [];
    }

    for (i = 0; i < pages.length; i++) {
      if (platFilter && pages[i][1] !== platFilter) continue;
      var name = pages[i][0].toLowerCase();
      var desc = (pages[i][2] || '').toLowerCase();
      var total = 0, ok = true, hl = null;
      if (!tokens.length) total = 1; /* bare-platform listing */
      for (t = 0; t < tokens.length; t++) {
        s = scoreName(name, tokens[t]);
        if (s && !hl) hl = [name.indexOf(tokens[t]), tokens[t].length];
        if (!s && desc.indexOf(tokens[t]) !== -1) s = 30;
        if (!s) { ok = false; break; }
        total += s;
      }
      if (ok) results.push({ name: pages[i][0], platform: pages[i][1],
        desc: pages[i][2] || '', path: pages[i][3], score: total, hl: hl });
    }

    results.sort(function (x, y) {
      if (y.score !== x.score) return y.score - x.score;
      if (x.name.length !== y.name.length) return x.name.length - y.name.length;
      if (x.name !== y.name) return x.name < y.name ? -1 : 1;
      return x.platform < y.platform ? -1 : 1;
    });

    var seen = {}, out = [];
    for (i = 0; i < results.length && out.length < limit; i++) {
      if (!seen[results[i].path]) { seen[results[i].path] = 1; out.push(results[i]); }
    }
    return out;
  }

  return { search: search };
}));
