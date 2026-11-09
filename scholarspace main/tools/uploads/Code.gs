/**
 * ScholarSpace uploads: a Google Apps Script web app that runs in the site owner's Google account.
 *
 *   1. A student submits a file on the Contribute page  -> doPost() saves it in a PRIVATE "Pending" folder,
 *      logs it in a Google Sheet and emails the owner.
 *   2. The owner opens the review page (link in the email), checks the file and approves or rejects it.
 *   3. Approved files move to the public "Approved" folder and are listed by doGet(?action=list),
 *      which the site reads to show them on the subject page.
 *
 * Setup steps are in tools/uploads/README.md.
 */

var MAX_BYTES = 15 * 1024 * 1024; // per file
var MAX_UPLOADS_PER_HOUR = 40;    // across everyone, to stop floods
var ALLOWED = {
  pdf: "application/pdf",
  doc: "application/msword",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ppt: "application/vnd.ms-powerpoint",
  pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  xls: "application/vnd.ms-excel",
  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png"
};
var KINDS = { notes: "Notes", papers: "Previous Year Paper", practice: "Practice / Assignment", books: "Book / Slides", syllabus: "Syllabus" };
var HEADER = ["id", "submittedAt", "status", "subjectId", "subjectName", "course", "kind", "title", "note",
              "name", "email", "fileId", "fileName", "bytes", "decidedAt"];
var COL = {}; HEADER.forEach(function (h, i) { COL[h] = i; });

/* ------------------------------------------------------------------ one-time setup */

/** Run once from the editor. Creates the folders, the log sheet and a secret review key. */
function setup() {
  var p = PropertiesService.getScriptProperties();
  if (!p.getProperty("ADMIN_KEY")) {
    p.setProperty("ADMIN_KEY", (Utilities.getUuid() + Utilities.getUuid()).replace(/-/g, ""));
  }
  if (!p.getProperty("ROOT_ID")) {
    var root = DriveApp.createFolder("ScholarSpace Uploads");
    var pending = root.createFolder("Pending (private)");
    var approved = root.createFolder("Approved (public)");
    approved.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    p.setProperties({ ROOT_ID: root.getId(), PENDING_ID: pending.getId(), APPROVED_ID: approved.getId() });
  }
  if (!p.getProperty("SHEET_ID")) {
    var ss = SpreadsheetApp.create("ScholarSpace Uploads log");
    ss.getSheets()[0].setName("uploads").appendRow(HEADER);
    DriveApp.getFileById(ss.getId()).moveTo(DriveApp.getFolderById(p.getProperty("ROOT_ID")));
    p.setProperty("SHEET_ID", ss.getId());
  }
  if (!p.getProperty("NOTIFY_EMAIL")) p.setProperty("NOTIFY_EMAIL", Session.getEffectiveUser().getEmail());
  Logger.log("Setup done. Folders and the log sheet are in 'ScholarSpace Uploads' in your Drive.");
  Logger.log("Now deploy as a web app, then run showReviewLink() to get your review page link.");
}

/** Run after deploying: prints the private link to your review page. Keep it secret. */
function showReviewLink() {
  var url = ScriptApp.getService().getUrl();
  if (!url) { Logger.log("Deploy the script as a web app first (Deploy > New deployment > Web app)."); return; }
  Logger.log("Review page (keep private): " + url + "?action=admin&key=" + cfg_("ADMIN_KEY"));
  Logger.log("Site upload URL (paste into assets/js/config.js): " + url);
}

/** Optional, run once: renames 12 older files in the ScholarSpace Data folder to clean names. */
function renameOldDriveFiles() {
  var list = [
    ["1xEM8YdbWzT9BDthjNb1-H6Ixn4xq-wRf", "Engineering Mathematics - Matrices - Handwritten Notes.pdf"],
    ["13-AFVFdf2dKkA6mEvJNOliqvfLR7UW-R", "Communicative English - 2023-24 Odd Semester - Question Paper.pdf"],
    ["1d8F1qFPXt6AOrhTeJrMbs1XvYmtrDSwM", "Communicative English - 2023-24 Even Semester - Question Paper.pdf"],
    ["1jfnetLyyVzDPfnAIdLFdDU3SiHP-Ag7v", "Engineering Mathematics - Successive Differentiation - Handwritten Notes.pdf"],
    ["15Bnw5Sl5QDQytaWyc78BwwQEJ81HD_Ma", "Engineering Mathematics - Double Integrals - Handwritten Notes.pdf"],
    ["1AjhoBL3XtP5IgZkSLk8fRuAHEctS2K8O", "Engineering Mathematics - Vector Calculus - Handwritten Notes.pdf"],
    ["1ra9iGDDIX5o1aUAyKG2gLa6gvufO-kJP", "Matrices and Calculus - 2023-24 Odd Semester - Question Paper.pdf"],
    ["1x3EBbPN7hU9Yqrs4WbV3AO7hnYKZkc2a", "Basic Electrical Engineering - 2023-24 Even Semester - Question Paper.pdf"],
    ["1wVge1E9KuPY6_KTw6Crn4rSVlQdd5Egr", "Basic Electrical Engineering - Sessional 1 2023-24 - Question Paper.pdf"],
    ["1nr00ItvNGdewM8LjVIQZvDJKwiHEqPFq", "Basics of Artificial Intelligence - 2023-24 Odd Semester - Question Paper.pdf"],
    ["1q6Eo3pXr2ekcjwSXZGINptULuQciKAAB", "Programming in Python - Question Paper.pdf"],
    ["1UJVOzJD0N8bl-_b1s0GgwgA6-jcP5b69", "Engineering Chemistry - 2023-24 Even Semester - Question Paper.pdf"]
  ];
  list.forEach(function (r) {
    try { DriveApp.getFileById(r[0]).setName(r[1]); Logger.log("Renamed: " + r[1]); }
    catch (err) { Logger.log("Could not rename " + r[0] + ": " + err); }
  });
}

/* ------------------------------------------------------------------ web app entry points */

/** Upload from the site. The body is JSON sent as text/plain (no CORS preflight). */
function doPost(e) {
  try {
    var d = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (d.website) return json_({ ok: true, id: "x" }); // honeypot field filled in: a bot, pretend it worked

    var subjectId = String(d.subjectId || "");
    if (!/^[a-z0-9-]{2,60}$/.test(subjectId)) return json_({ ok: false, error: "Please choose a subject." });
    var kind = KINDS[d.kind] ? d.kind : "notes";
    var title = text_(d.title, 120);
    if (title.length < 3) return json_({ ok: false, error: "Please give the file a short title." });
    var fileName = text_(d.fileName, 150);
    var ext = (fileName.split(".").pop() || "").toLowerCase();
    if (!ALLOWED[ext]) return json_({ ok: false, error: "Only PDF, Word, PowerPoint, Excel, JPG and PNG files are accepted." });
    var bytes = Utilities.base64Decode(String(d.data || ""));
    if (!bytes.length) return json_({ ok: false, error: "The file is empty." });
    if (bytes.length > MAX_BYTES) return json_({ ok: false, error: "Files must be 15 MB or smaller." });

    var cache = CacheService.getScriptCache();
    var count = Number(cache.get("uploads-this-hour") || 0);
    if (count >= MAX_UPLOADS_PER_HOUR) return json_({ ok: false, error: "Too many uploads right now. Please try again in an hour." });
    cache.put("uploads-this-hour", String(count + 1), 3600);

    var id = Utilities.getUuid().slice(0, 8);
    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    var file;
    try {
      var blob = Utilities.newBlob(bytes, ALLOWED[ext], "[" + subjectId + "] " + title + "." + ext);
      file = DriveApp.getFolderById(cfg_("PENDING_ID")).createFile(blob);
      sheet_().appendRow([id, new Date(), "pending", subjectId, text_(d.subjectName, 120), text_(d.course, 80), kind, title,
        text_(d.note, 500), text_(d.name, 60), text_(d.email, 100), file.getId(), fileName, bytes.length, ""].map(cell_));
    } finally {
      lock.releaseLock();
    }
    notifyOwner_(id, d, kind, title, file, bytes.length);
    return json_({ ok: true, id: id });
  } catch (err) {
    console.error(err);
    return json_({ ok: false, error: "The upload failed on our side. Please try again in a few minutes." });
  }
}

function doGet(e) {
  var q = (e && e.parameter) || {};
  var action = q.action || "list";
  if (action === "list") return list_();
  if (q.key !== cfg_("ADMIN_KEY")) return page_("Not allowed", "<p>This link is not valid.</p>");
  if (action === "admin") return adminPage_(q.key);
  if (action === "review") return reviewPage_(q.key, q.id);
  if (action === "decide") return decide_(q);
  return page_("Unknown action", "<p>Nothing to do.</p>");
}

/* ------------------------------------------------------------------ public list for the site */

function list_() {
  var cache = CacheService.getScriptCache();
  var cached = cache.get("approved-list");
  if (cached) return ContentService.createTextOutput(cached).setMimeType(ContentService.MimeType.JSON);
  var items = rows_().filter(function (r) { return r.status === "approved"; }).map(function (r) {
    return { id: r.id, f: r.fileId, s: r.subjectId, t: r.title, k: r.kind,
             x: (String(r.fileName).split(".").pop() || "").toLowerCase(), by: firstName_(r.name),
             d: r.decidedAt ? new Date(r.decidedAt).toISOString().slice(0, 10) : "" };
  });
  var out = JSON.stringify({ ok: true, items: items });
  if (out.length < 90000) cache.put("approved-list", out, 300);
  return ContentService.createTextOutput(out).setMimeType(ContentService.MimeType.JSON);
}

/* ------------------------------------------------------------------ owner pages */

function adminPage_(key) {
  var all = rows_().reverse();
  var pending = all.filter(function (r) { return r.status === "pending"; });
  var done = all.filter(function (r) { return r.status !== "pending"; }).slice(0, 30);
  var body = "<h2>Waiting for review (" + pending.length + ")</h2>" +
    (pending.length ? table_(pending, key, true) : "<p class='muted'>Nothing to review. 🎉</p>") +
    "<h2>Recent decisions</h2>" + (done.length ? table_(done, key, false) : "<p class='muted'>None yet.</p>");
  return page_("Uploads to review", body);
}

function table_(rows, key, pending) {
  return "<table><tr><th>Subject</th><th>Title</th><th>Type</th><th>From</th><th>Date</th><th></th></tr>" +
    rows.map(function (r) {
      return "<tr><td>" + esc_(r.subjectName || r.subjectId) + "</td><td>" + esc_(r.title) + "</td><td>" + esc_(KINDS[r.kind] || r.kind) +
        "</td><td>" + esc_(r.name || "Anonymous") + "</td><td>" + esc_(fmtDate_(r.submittedAt)) + "</td><td>" +
        (pending ? "<a class='btn' href='" + url_({ action: "review", id: r.id, key: key }) + "'>Review</a>"
                 : "<span class='tag " + r.status + "'>" + esc_(r.status) + "</span>" +
                   (r.status === "approved" ? " <a href='" + url_({ action: "review", id: r.id, key: key }) + "'>Edit</a>" : "")) +
        "</td></tr>";
    }).join("") + "</table>";
}

function reviewPage_(key, id) {
  var r = find_(id);
  if (!r) return page_("Not found", "<p>That upload doesn't exist.</p>");
  var view = "https://drive.google.com/file/d/" + r.fileId + "/view";
  var kinds = Object.keys(KINDS).map(function (k) {
    return "<option value='" + k + "'" + (k === r.kind ? " selected" : "") + ">" + KINDS[k] + "</option>";
  }).join("");
  var body =
    "<p><a href='" + url_({ action: "admin", key: key }) + "'>&larr; All uploads</a></p>" +
    "<dl><dt>Subject</dt><dd>" + esc_(r.subjectName || r.subjectId) + " <span class='muted'>(" + esc_(r.course) + ")</span></dd>" +
    "<dt>From</dt><dd>" + esc_(r.name || "Anonymous") + (r.email ? " &lt;" + esc_(r.email) + "&gt;" : "") + "</dd>" +
    "<dt>Note</dt><dd>" + (esc_(r.note) || "<span class='muted'>None</span>") + "</dd>" +
    "<dt>File</dt><dd>" + esc_(r.fileName) + " · " + Math.round(r.bytes / 1024) + " KB · <a href='" + view + "'>Open the file</a></dd>" +
    "<dt>Status</dt><dd><span class='tag " + r.status + "'>" + esc_(r.status) + "</span></dd></dl>" +
    "<iframe src='https://drive.google.com/file/d/" + r.fileId + "/preview'></iframe>" +
    "<form method='get' action='" + ScriptApp.getService().getUrl() + "' target='_top'>" +
    "<input type='hidden' name='action' value='decide'><input type='hidden' name='id' value='" + esc_(r.id) + "'>" +
    "<input type='hidden' name='key' value='" + esc_(key) + "'>" +
    "<label>Title shown on the site<input name='title' value='" + esc_(r.title) + "' maxlength='120'></label>" +
    "<label>Type<select name='kind'>" + kinds + "</select></label>" +
    "<div class='actions'>" +
    (r.status === "approved"
      ? "<button name='decision' value='approve'>Save changes</button><button name='decision' value='remove' class='danger'>Remove from site</button>"
      : "<button name='decision' value='approve'>Approve and publish</button><button name='decision' value='reject' class='danger'>Reject</button>") +
    "</div></form>";
  return page_("Review: " + r.title, body);
}

function decide_(q) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var r = find_(q.id);
    if (!r) return page_("Not found", "<p>That upload doesn't exist.</p>");
    var sh = sheet_(), file = DriveApp.getFileById(r.fileId);
    var title = text_(q.title || r.title, 120), kind = KINDS[q.kind] ? q.kind : r.kind;
    var ext = (String(r.fileName).split(".").pop() || "").toLowerCase();
    var status;
    if (q.decision === "approve") {
      var folder = subFolder_(DriveApp.getFolderById(cfg_("APPROVED_ID")), r.subjectId);
      file.moveTo(folder);
      file.setName(title + "." + ext);
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      status = "approved";
    } else if (q.decision === "reject") {
      file.setTrashed(true); // stays in Drive trash for 30 days
      status = "rejected";
    } else if (q.decision === "remove") {
      file.setSharing(DriveApp.Access.PRIVATE, DriveApp.Permission.NONE);
      file.moveTo(DriveApp.getFolderById(cfg_("PENDING_ID")));
      status = "removed";
    } else {
      return page_("Unknown decision", "<p>Nothing changed.</p>");
    }
    sh.getRange(r._row, COL.status + 1).setValue(status);
    sh.getRange(r._row, COL.title + 1).setValue(cell_(title));
    sh.getRange(r._row, COL.kind + 1).setValue(kind);
    sh.getRange(r._row, COL.decidedAt + 1).setValue(new Date());
    CacheService.getScriptCache().remove("approved-list");
    var msg = { approved: "Published. It appears on the site within a few minutes.", rejected: "Rejected. The file is in your Drive trash.",
                removed: "Removed from the site. The file is back in your private Pending folder." }[status];
    return page_("Done", "<p class='ok'>" + msg + "</p><p><a class='btn' href='" + url_({ action: "admin", key: q.key }) + "'>Back to all uploads</a></p>");
  } finally {
    lock.releaseLock();
  }
}

/* ------------------------------------------------------------------ helpers */

function notifyOwner_(id, d, kind, title, file, size) {
  var key = cfg_("ADMIN_KEY");
  var review = url_({ action: "review", id: id, key: key });
  var html = "<p><b>" + esc_(d.name || "Someone") + "</b> uploaded <b>" + esc_(title) + "</b> (" + esc_(KINDS[kind]) + ")</p>" +
    "<p>Subject: " + esc_(d.subjectName || d.subjectId) + " · " + esc_(d.course || "") + "<br>File: " + esc_(d.fileName) + " · " +
    Math.round(size / 1024) + " KB" + (d.note ? "<br>Note: " + esc_(d.note) : "") + "</p>" +
    "<p><a href='" + review + "' style='background:#4f46e5;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none'>Review and approve</a></p>" +
    "<p style='color:#666;font-size:12px'>The file stays private until you approve it.</p>";
  try {
    MailApp.sendEmail({ to: cfg_("NOTIFY_EMAIL"), subject: "New upload to review: " + title, htmlBody: html });
  } catch (err) {
    console.error("Email failed: " + err); // the upload is still saved and shows on the review page
  }
}

function cfg_(k) {
  var v = PropertiesService.getScriptProperties().getProperty(k);
  if (!v) throw new Error("Missing " + k + ". Run setup() once from the editor.");
  return v;
}
function sheet_() { return SpreadsheetApp.openById(cfg_("SHEET_ID")).getSheetByName("uploads"); }
function rows_() {
  var v = sheet_().getDataRange().getValues();
  var out = [];
  for (var i = 1; i < v.length; i++) {
    var r = { _row: i + 1 };
    HEADER.forEach(function (h, j) { r[h] = v[i][j]; });
    if (r.id) out.push(r);
  }
  return out;
}
function find_(id) { return rows_().filter(function (r) { return String(r.id) === String(id || ""); })[0]; }
function subFolder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
function text_(v, max) { return String(v == null ? "" : v).replace(/[\u0000-\u001f]+/g, " ").replace(/\s+/g, " ").trim().slice(0, max); }
/** Stops a value like "=IMPORTXML(...)" being run as a spreadsheet formula. */
function cell_(v) { return typeof v === "string" && /^[=+\-@]/.test(v) ? "'" + v : v; }
function firstName_(n) { return text_(n, 60).split(" ")[0] || ""; }
function esc_(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}
function fmtDate_(d) { return d ? Utilities.formatDate(new Date(d), Session.getScriptTimeZone(), "d MMM yyyy, HH:mm") : ""; }
function url_(params) {
  return ScriptApp.getService().getUrl() + "?" + Object.keys(params).map(function (k) {
    return k + "=" + encodeURIComponent(params[k]);
  }).join("&");
}
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function page_(title, body) {
  var css = "body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#0f172a}" +
    "h1{font-size:1.5rem}h2{font-size:1.1rem;margin-top:28px}.muted{color:#5b6478}" +
    "table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{text-align:left;padding:8px;border-bottom:1px solid #e3e7ef;vertical-align:top}" +
    "a{color:#4f46e5}.btn,button{background:#4f46e5;color:#fff;border:0;border-radius:8px;padding:8px 14px;text-decoration:none;font:inherit;cursor:pointer}" +
    "button.danger{background:#b91c1c}.actions{display:flex;gap:10px;margin-top:12px}" +
    "label{display:block;margin-top:12px;font-weight:600}input,select{display:block;width:100%;padding:9px;margin-top:4px;font:inherit;border:1px solid #cbd2e0;border-radius:8px;box-sizing:border-box}" +
    "dl{display:grid;grid-template-columns:110px 1fr;gap:6px 12px}dt{font-weight:600}dd{margin:0}" +
    "iframe{width:100%;height:520px;border:1px solid #e3e7ef;border-radius:10px;margin-top:16px}" +
    ".tag{padding:2px 8px;border-radius:999px;font-size:.8rem;background:#eef1f5}.tag.approved{background:#e8f7ee;color:#15803d}" +
    ".tag.rejected,.tag.removed{background:#fdecec;color:#b91c1c}.tag.pending{background:#fff1e6;color:#c2410c}.ok{color:#15803d;font-weight:600}";
  return HtmlService.createHtmlOutput("<!doctype html><html><head><base target='_top'><style>" + css + "</style></head><body><h1>" +
    esc_(title) + "</h1>" + body + "</body></html>").setTitle(title).addMetaTag("viewport", "width=device-width, initial-scale=1");
}
