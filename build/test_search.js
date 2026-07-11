'use strict';
var assert = require('assert');
var SearchCore = require('../docs/assets/search-core.js');

var db = { v: 1, pages: [
  ['tar', 'common', 'Archiving utility.', 'pages/common/tar.html'],
  ['tar', 'linux', 'GNU archiving utility.', 'pages/linux/tar.html'],
  ['target', 'linux', 'Manage systemd targets.', 'pages/linux/target.html'],
  ['star', 'linux', 'Unique standard tape archiver.', 'pages/linux/star.html'],
  ['grep', 'common', 'Find patterns in files.', 'pages/common/grep.html'],
  ['choco', 'windows', 'Windows package manager.', 'pages/windows/choco.html'],
  ['wsl', 'windows', 'Manage Windows Subsystem for Linux.', 'pages/windows/wsl.html']
] };

var r = SearchCore.search(db, 'tar', 10);
assert.strictEqual(r[0].name, 'tar', 'exact match first');
assert.strictEqual(r[0].platform, 'common', 'platform tiebreak alphabetical');
assert.strictEqual(r[1].name, 'tar', 'both exact-name pages precede prefix matches');
assert.strictEqual(r[2].name, 'target', 'prefix beats substring');
assert.ok(r.some(function (x) { return x.name === 'star'; }), 'substring included');

r = SearchCore.search(db, 'archiving', 10);
assert.strictEqual(r[0].name, 'tar', 'description match');

r = SearchCore.search(db, 'tar linux', 10);
assert.ok(r.length === 3 && r.every(function (x) { return x.platform === 'linux'; }),
  'platform filter keeps only linux matches (tar, target, star)');
assert.strictEqual(r[0].name, 'tar', 'exact name ranks first within the platform');

r = SearchCore.search(db, 'linux tar', 10);
assert.strictEqual(r[0].platform, 'linux', 'filter position free');

r = SearchCore.search(db, 'tar win', 10);
assert.strictEqual(r.length, 0, 'prefix filter: no tar on windows');

r = SearchCore.search(db, 'wsl win', 10);
assert.strictEqual(r[0].name, 'wsl', 'prefix platform filter works');

r = SearchCore.search(db, 'windows', 10);
assert.ok(r.length === 2 && r.every(function (x) { return x.platform === 'windows'; }),
  'bare full platform name lists the platform');

r = SearchCore.search(db, 'win', 10);
assert.ok(r.length > 0 && r.every(function (x) {
  return x.desc.toLowerCase().indexOf('win') !== -1;
}), 'bare prefix is a normal search, not a listing');

r = SearchCore.search(db, 'windows package', 10);
assert.strictEqual(r[0].name, 'choco', 'platform token + description token');

assert.strictEqual(SearchCore.search(db, '', 10).length, 0, 'empty query');
assert.strictEqual(SearchCore.search(db, '   ', 10).length, 0, 'blank query');
assert.strictEqual(SearchCore.search(db, 'tar', 2).length, 2, 'limit respected');
assert.strictEqual(SearchCore.search(db, 'zzzz', 10).length, 0, 'no matches');

r = SearchCore.search(db, 'tar', 10);
assert.deepStrictEqual(r[0].hl, [0, 3], 'exact match highlight span');
r = SearchCore.search(db, 'get', 10);
assert.deepStrictEqual(r.filter(function (x) { return x.name === 'target'; })[0].hl, [3, 3],
  'substring highlight offset');
r = SearchCore.search(db, 'archiving', 10);
assert.strictEqual(r[0].hl, null, 'description-only match has no name highlight');

console.log('search-core: all tests passed');
