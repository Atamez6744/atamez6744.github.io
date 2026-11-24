/**
 * Soul Wired comments: a Google Apps Script that stores blog comments in a
 * Google Sheet. Readers don't sign up for anything.
 *
 * How it works
 *   - A reader posts a comment on the site. It's added to the "Comments" tab
 *     of this spreadsheet with the Approved box unticked, and you get an email.
 *   - Tick the Approved box and the comment shows on the post.
 *     Untick it (or delete the row) to take it down.
 *
 * Setup (once)
 *   1. In the spreadsheet: Extensions > Apps Script. Delete what's there,
 *      paste this whole file, and click Save.
 *   2. Deploy > New deployment > gear icon > Web app.
 *      Execute as: Me.  Who has access: Anyone.  Click Deploy and allow access.
 *   3. Copy the Web app URL (it ends in /exec) and send it to Claude.
 *
 * If you change this code later, use Deploy > Manage deployments > edit (pencil)
 * > Version: New version, so the same URL keeps working.
 */

var SHEET_NAME = 'Comments';
var HEADERS = ['Date', 'Post', 'Name', 'Comment', 'Approved'];
var MAX_NAME = 60;
var MAX_COMMENT = 2000;
var MAX_PER_10_MIN = 30;   // stops a flood of spam
var SEND_EMAIL = true;     // email you when a new comment arrives

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setColumnWidth(4, 420);
  }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// Text that starts with = + - @ would turn into a formula in the sheet.
function safeText_(s) {
  s = String(s || '').replace(/\r\n?/g, '\n').trim();
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function cleanPost_(s) {
  return String(s || '').replace(/[^a-z0-9\-]/gi, '').slice(0, 120).toLowerCase();
}

// A ticked box counts, and so does typing yes / sí / x in the cell.
function isApproved_(v) {
  return v === true || /^(yes|true|si|sí|x)$/i.test(String(v).trim());
}

/** Returns the approved comments for one post: ?post=take-it-all-away-then */
function doGet(e) {
  var post = cleanPost_(e && e.parameter && e.parameter.post);
  if (!post) return json_({ ok: false, error: 'missing post' });
  var rows = getSheet_().getDataRange().getValues().slice(1);
  var comments = rows
    .filter(function (r) { return r[1] === post && isApproved_(r[4]); })
    .map(function (r) {
      return {
        date: r[0] instanceof Date ? r[0].toISOString() : String(r[0]),
        name: String(r[2]),
        comment: String(r[3])
      };
    });
  return json_({ ok: true, comments: comments });
}

/** Saves a new comment, unapproved. */
function doPost(e) {
  var data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'bad request' });
  }

  // "website" is a hidden field people never see; bots fill it in.
  if (data.website) return json_({ ok: true });

  var post = cleanPost_(data.post);
  var name = String(data.name || '').trim().slice(0, MAX_NAME);
  var comment = String(data.comment || '').trim().slice(0, MAX_COMMENT);
  if (!post || !name || !comment) {
    return json_({ ok: false, error: 'missing fields' });
  }

  var cache = CacheService.getScriptCache();
  var count = Number(cache.get('recent') || 0);
  if (count >= MAX_PER_10_MIN) return json_({ ok: false, error: 'busy' });
  cache.put('recent', String(count + 1), 600);

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sheet = getSheet_();
    sheet.appendRow([new Date(), post, safeText_(name), safeText_(comment), false]);
    sheet.getRange(sheet.getLastRow(), 5).insertCheckboxes();
  } finally {
    lock.releaseLock();
  }

  if (SEND_EMAIL) {
    try {
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      MailApp.sendEmail(
        Session.getEffectiveUser().getEmail(),
        'New comment on Soul Wired: ' + post,
        name + ' wrote:\n\n' + comment +
        '\n\nPost: https://alejandratamez.com/blog/' + post + '.html' +
        '\n\nTo show it on the site, tick Approved in the sheet:\n' + ss.getUrl()
      );
    } catch (err) {
      // The comment is saved even if the email fails.
    }
  }

  return json_({ ok: true });
}
