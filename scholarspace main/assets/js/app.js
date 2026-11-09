/* ScholarSpace: shared layout, search and page rendering. Data comes from catalog.js (window.CATALOG). */
(function () {
  "use strict";

  var CAT = window.CATALOG || { programs: [], subjects: [] };
  var UPLOADS_URL = (window.SS_CONFIG && window.SS_CONFIG.uploadsUrl) || "";
  var CONTACT = {
    email: "contact.rahul82@gmail.com",
    github: "https://github.com/Rahul-web01",
    linkedin: "https://www.linkedin.com/in/rahul-singh-cs/"
  };
  var TYPES = {
    notes: { label: "Notes", icon: "fa-book-open" },
    papers: { label: "Previous Year Papers", short: "PYQs", icon: "fa-file-circle-question" },
    practice: { label: "Practice & Assignments", short: "Practice", icon: "fa-pen-to-square" },
    books: { label: "Books & Slides", short: "Books", icon: "fa-book" },
    syllabus: { label: "Syllabus", icon: "fa-list-ol" }
  };
  var TYPE_ORDER = ["notes", "papers", "practice", "books", "syllabus"];
  var YEARS = {
    1: { name: "1st Year", sems: "Semester I & II" },
    2: { name: "2nd Year", sems: "Semester III & IV" },
    3: { name: "3rd Year", sems: "Semester V & VI" },
    4: { name: "4th Year", sems: "Semester VII & VIII" }
  };
  var GROUPS = {
    core: { title: "Core subjects", note: "" },
    "group-a": { title: "Group A", note: "Studied in Semester I or II, depending on your section." },
    "group-b": { title: "Group B", note: "Studied in Semester I or II, depending on your section." },
    elective: { title: "Electives", note: "Pick the electives offered in your semester." },
    open: { title: "Open electives & value-added courses", note: "Common courses taken alongside your branch subjects." },
    skill: { title: "Skill & value-added courses", note: "Vocational and co-curricular courses offered alongside the core subjects." },
    more: { title: "More subjects", note: "From earlier syllabi. Still useful for practice and reference." }
  };
  var EXT_ICON = { pdf: "fa-file-pdf", docx: "fa-file-word", doc: "fa-file-word", pptx: "fa-file-powerpoint", ppt: "fa-file-powerpoint", xlsx: "fa-file-excel" };

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function param(name) { return new URLSearchParams(location.search).get(name); }
  function fileUrl(id) { return "https://drive.google.com/file/d/" + encodeURIComponent(id) + "/view"; }
  function downloadUrl(id) { return "https://drive.google.com/uc?export=download&id=" + encodeURIComponent(id); }
  function folderUrl(id) { return "https://drive.google.com/drive/folders/" + encodeURIComponent(id); }
  function program(id) { return CAT.programs.filter(function (p) { return p.id === id; })[0]; }
  function subject(id) { return CAT.subjects.filter(function (s) { return s.id === id; })[0]; }
  function subjectsOf(pid, year) {
    return CAT.subjects.filter(function (s) { return s.program === pid && (year == null || s.year === year); });
  }
  function plural(n, w) { return n + " " + w + (n === 1 ? "" : "s"); }
  function fileCount(list) { return list.reduce(function (n, s) { return n + (s.files ? s.files.length : 0); }, 0); }
  function counts(s) {
    var c = {};
    (s.files || []).forEach(function (f) { c[f.k] = (c[f.k] || 0) + 1; });
    return c;
  }
  function brandIcon(icon) {
    return /^fa-(python|java)$/.test(icon) ? "fa-brands " + icon : "fa-solid " + icon;
  }
  function isYearly(pid) { var p = program(pid); return !!(p && p.years); }
  function yearPrograms(course) { return CAT.programs.filter(function (p) { return p.years && (!course || p.course === course); }); }
  function browseUrl(s) {
    return "browse.html?program=" + s.program + (isYearly(s.program) && s.year ? "&year=" + s.year : "");
  }
  /* The same subject at the other college ("dbms" <-> "itm-dbms"), if it has files. */
  function counterpart(s) {
    var other = /^itm-/.test(s.id) ? subject(s.id.slice(4)) : subject("itm-" + s.id);
    return other && other.files && other.files.length ? other : null;
  }
  function collegeBlocks(cls) {
    return yearPrograms().map(function (p) {
      var all = subjectsOf(p.id);
      return '<div class="college' + (cls ? " " + cls : "") + '"><div class="college-head"><span class="card-icon"><i class="fa-solid ' + p.icon + '"></i></span>' +
        "<div><h3>" + esc(p.name) + "</h3><p>" + esc(p.blurb) + "</p></div>" +
        '<span class="badge">' + plural(fileCount(all), "file") + "</span></div>" +
        '<div class="grid grid-4">' + [1, 2, 3, 4].map(function (y) {
          var list = all.filter(function (s) { return s.year === y; });
          return '<a class="card year-card" href="browse.html?program=' + p.id + "&year=" + y + '">' +
            '<span class="year-num">0' + y + "</span><h3>" + YEARS[y].name + "</h3><p>" + YEARS[y].sems + "</p>" +
            '<div class="card-foot"><span>' + plural(list.length, "subject") + " · " + plural(fileCount(list), "file") + '</span><i class="fa-solid fa-arrow-right arrow"></i></div></a>';
        }).join("") + "</div></div>";
    }).join("");
  }
  function storage(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  /* ---------- approved student uploads (tools/uploads/Code.gs) ---------- */
  var COMMUNITY_KEY = "ss-community";
  function mergeCommunity(items) {
    var changed = [];
    (items || []).forEach(function (it) {
      var s = subject(it.s);
      if (!s || !it.f) return;
      s.files = s.files || [];
      if (s.files.some(function (f) { return f.id === it.f; })) return;
      s.files.push({ t: String(it.t || "Untitled"), k: TYPES[it.k] ? it.k : "notes", id: String(it.f), x: String(it.x || "file"), c: 1, by: String(it.by || "") });
      changed.push(s.id);
    });
    if (changed.length) INDEX = null;
    return changed;
  }
  function cachedCommunity() {
    try { var v = JSON.parse(sessionStorage.getItem(COMMUNITY_KEY) || "null"); return v && v.items ? v : null; } catch (e) { return null; }
  }
  function loadCommunity(onNew) {
    if (!UPLOADS_URL) return;
    var cached = cachedCommunity();
    if (cached) mergeCommunity(cached.items);
    if (cached && Date.now() - cached.at < 5 * 60 * 1000) return;
    fetch(UPLOADS_URL + "?action=list").then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.items) return;
      try { sessionStorage.setItem(COMMUNITY_KEY, JSON.stringify({ at: Date.now(), items: d.items })); } catch (e) { /* storage full or blocked */ }
      var changed = mergeCommunity(d.items);
      if (changed.length && onNew) onNew(changed);
    }).catch(function () { /* the site works without community uploads */ });
  }

  /* ---------- theme ---------- */
  var savedTheme = storage("ss-theme");
  if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches;
  }

  /* ---------- layout ---------- */
  function header(active) {
    var links = [
      ["index.html", "Home", "home"], ["browse.html", "Browse", "browse"], ["sgpa.html", "SGPA Calculator", "sgpa"],
      ["about.html", "About", "about"], ["feedback.html", "Contribute", "feedback"]
    ];
    return '<a class="skip-link" href="#main">Skip to content</a>' +
      '<header class="site-header"><div class="container">' +
      '<a class="brand" href="index.html" aria-label="ScholarSpace home"><span class="brand-mark"><i class="fa-solid fa-graduation-cap"></i></span>ScholarSpace</a>' +
      '<nav class="nav" id="site-nav" aria-label="Main">' +
      links.map(function (l) {
        return '<a href="' + l[0] + '"' + (l[2] === active ? ' aria-current="page"' : "") + ">" + l[1] + "</a>";
      }).join("") + "</nav>" +
      '<div class="header-actions">' +
      '<button class="icon-btn" id="theme-btn" type="button" aria-label="Switch colour theme"><i class="fa-solid fa-moon"></i></button>' +
      '<button class="icon-btn menu-btn" id="menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-nav"><i class="fa-solid fa-bars"></i></button>' +
      "</div></div></header>";
  }
  function footer() {
    var year = new Date().getFullYear();
    return '<footer class="site-footer"><div class="container"><div class="footer-grid">' +
      '<div class="footer-about"><a class="brand" href="index.html"><span class="brand-mark"><i class="fa-solid fa-graduation-cap"></i></span>ScholarSpace</a>' +
      "<p>Free notes, previous year papers and practice sets for university students, organised by year and subject.</p>" +
      '<div class="socials"><a href="' + CONTACT.github + '" target="_blank" rel="noopener" aria-label="GitHub"><i class="fa-brands fa-github"></i></a>' +
      '<a href="' + CONTACT.linkedin + '" target="_blank" rel="noopener" aria-label="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>' +
      '<a href="mailto:' + CONTACT.email + '" aria-label="Email"><i class="fa-solid fa-envelope"></i></a></div></div>' +
      "<div><h4>Year-wise courses</h4><ul>" +
      yearPrograms().map(function (p) { return '<li><a href="browse.html?program=' + p.id + '&year=1">' + esc(p.name) + "</a></li>"; }).join("") +
      "</ul></div>" +
      "<div><h4>Courses</h4><ul>" +
      CAT.programs.filter(function (p) { return !p.years; }).map(function (p) {
        return '<li><a href="browse.html?program=' + p.id + '">' + esc(p.name) + "</a></li>";
      }).join("") + "</ul></div>" +
      '<div><h4>ScholarSpace</h4><ul><li><a href="sgpa.html">SGPA Calculator</a></li><li><a href="about.html">About</a></li>' +
      '<li><a href="feedback.html">Contribute notes</a></li><li><a href="feedback.html">Feedback</a></li></ul></div>' +
      '</div><div class="footer-bottom"><span>&copy; ' + year + " ScholarSpace. Built by Rahul Singh.</span>" +
      "<span>Study material is shared for learning. Files open from Google Drive.</span></div></div></footer>" +
      '<a href="#main" class="btn btn-ghost btn-sm to-top" id="to-top" aria-label="Back to top"><i class="fa-solid fa-arrow-up"></i></a>';
  }
  function mountLayout(active) {
    var h = document.createElement("div");
    h.innerHTML = header(active);
    while (h.firstChild) document.body.insertBefore(h.firstChild, document.body.firstChild);
    document.body.insertAdjacentHTML("beforeend", footer());

    var themeBtn = $("#theme-btn");
    function paintTheme() { themeBtn.innerHTML = '<i class="fa-solid ' + (isDark() ? "fa-sun" : "fa-moon") + '"></i>'; }
    paintTheme();
    themeBtn.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      storage("ss-theme", next);
      paintTheme();
    });
    var menuBtn = $("#menu-btn"), nav = $("#site-nav");
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
      menuBtn.innerHTML = '<i class="fa-solid ' + (open ? "fa-xmark" : "fa-bars") + '"></i>';
    });
    var toTop = $("#to-top");
    window.addEventListener("scroll", function () { toTop.classList.toggle("show", window.scrollY > 600); }, { passive: true });
  }

  /* ---------- search ---------- */
  var INDEX = null;
  function norm(s) { return String(s).toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9]+/g, " ").trim(); }
  function buildIndex() {
    if (INDEX) return INDEX;
    INDEX = { subjects: [], files: [] };
    CAT.subjects.forEach(function (s) {
      var p = program(s.program);
      INDEX.subjects.push({ s: s, hay: norm([s.name, s.alias, s.code, p && p.name, s.year && YEARS[s.year].name].join(" ")) });
      (s.files || []).forEach(function (f) { INDEX.files.push({ f: f, s: s, hay: norm(f.t + " " + s.name + " " + (s.alias || "")) }); });
    });
    return INDEX;
  }
  function search(q) {
    var terms = norm(q).split(" ").filter(Boolean);
    if (!terms.length) return { subjects: [], files: [] };
    var idx = buildIndex();
    function match(e) { return terms.every(function (t) { return (" " + e.hay).indexOf(" " + t) !== -1 || e.hay.indexOf(t) !== -1; }); }
    function score(e, name) {
      var n = norm(name), sc = 0;
      terms.forEach(function (t) { if (n.indexOf(t) === 0) sc += 3; else if ((" " + n).indexOf(" " + t) !== -1) sc += 2; else if (n.indexOf(t) !== -1) sc += 1; });
      return sc;
    }
    function has(e) { return e.s.files && e.s.files.length ? 1 : 0; }
    var subs = idx.subjects.filter(match).sort(function (a, b) { return score(b, b.s.name) - score(a, a.s.name) || has(b) - has(a); });
    var files = idx.files.filter(match).sort(function (a, b) { return score(b, b.f.t) - score(a, a.f.t); });
    return { subjects: subs.map(function (e) { return e.s; }), files: files };
  }
  function subjectMeta(s) {
    var p = program(s.program), bits = [];
    if (p && p.years && s.year) bits.push(p.short + " · " + YEARS[s.year].name);
    else if (p) bits.push(p.name);
    if (s.code) bits.push(s.code);
    return bits.join(" · ");
  }
  function mountSearch(input, panel) {
    var active = -1;
    function items() { return panel.querySelectorAll(".sr-item"); }
    function setActive(i) {
      var list = items();
      if (!list.length) return;
      active = (i + list.length) % list.length;
      list.forEach(function (el, j) { el.classList.toggle("active", j === active); });
      list[active].scrollIntoView({ block: "nearest" });
    }
    function render() {
      var q = input.value.trim();
      active = -1;
      if (q.length < 2) { panel.classList.remove("open"); panel.innerHTML = ""; return; }
      var r = search(q), html = "";
      if (r.subjects.length) {
        html += '<div class="sr-group">Subjects</div>' + r.subjects.slice(0, 6).map(function (s) {
          return '<a class="sr-item" href="subject.html?id=' + s.id + '"><span class="sr-icon"><i class="' + brandIcon(s.icon) + '"></i></span>' +
            '<span class="sr-text"><strong>' + esc(s.name) + "</strong><small>" + esc(subjectMeta(s)) + " · " + (s.files ? s.files.length : 0) + " files</small></span></a>";
        }).join("");
      }
      if (r.files.length) {
        html += '<div class="sr-group">Files</div>' + r.files.slice(0, 10).map(function (e) {
          return '<a class="sr-item t-' + e.f.k + '" href="' + fileUrl(e.f.id) + '" target="_blank" rel="noopener">' +
            '<span class="sr-icon" style="background:var(--c-soft);color:var(--c)"><i class="fa-solid ' + TYPES[e.f.k].icon + '"></i></span>' +
            '<span class="sr-text"><strong>' + esc(e.f.t) + "</strong><small>" + esc(e.s.name) + (program(e.s.program) && program(e.s.program).college ? " · " + esc(program(e.s.program).college) : "") + " · " + TYPES[e.f.k].label + "</small></span></a>";
        }).join("");
        if (r.files.length > 10) html += '<div class="sr-empty">' + (r.files.length - 10) + " more files match. Try a more specific search.</div>";
      }
      if (!html) html = '<div class="sr-empty">No results for “' + esc(q) + "”. Try a subject name like “DBMS” or “Physics”.</div>";
      panel.innerHTML = html;
      panel.classList.add("open");
    }
    input.addEventListener("input", render);
    input.addEventListener("focus", render);
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); setActive(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive(active - 1); }
      else if (e.key === "Enter") {
        var list = items(), el = list[active >= 0 ? active : 0];
        if (el) { e.preventDefault(); el.click(); }
      } else if (e.key === "Escape") { panel.classList.remove("open"); input.blur(); }
    });
    document.addEventListener("click", function (e) { if (!panel.contains(e.target) && e.target !== input) panel.classList.remove("open"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") { e.preventDefault(); input.focus(); }
    });
  }

  /* ---------- shared pieces ---------- */
  function chipsFor(s) {
    var c = counts(s);
    var one = { notes: "Note", papers: "PYQ", books: "Book" };
    var html = TYPE_ORDER.filter(function (k) { return c[k]; }).map(function (k) {
      var label = c[k] === 1 && one[k] ? one[k] : (TYPES[k].short || TYPES[k].label);
      return '<span class="chip t-' + k + '"><i class="fa-solid ' + TYPES[k].icon + '"></i>' + c[k] + " " + label + "</span>";
    }).join("");
    return html || '<span class="chip">Coming soon</span>';
  }
  function subjectCard(s) {
    var empty = !(s.files && s.files.length);
    var meta = [];
    if (s.code) meta.push(esc(s.code));
    if (s.sem) meta.push("Sem " + esc(s.sem));
    return '<a class="card subject-card fade-in' + (empty ? " empty" : "") + '" href="subject.html?id=' + s.id + '">' +
      '<div class="row"><span class="card-icon"><i class="' + brandIcon(s.icon) + '"></i></span><div>' +
      "<h3>" + esc(s.name) + "</h3>" + (meta.length ? '<div class="meta">' + meta.join('<span class="dot">•</span>') + "</div>" : "") +
      '</div></div><div class="chips">' + chipsFor(s) + "</div></a>";
  }
  function crumbs(list) {
    return '<nav class="crumbs" aria-label="Breadcrumb">' + list.map(function (c, i) {
      var last = i === list.length - 1;
      return (i ? '<i class="fa-solid fa-chevron-right"></i>' : "") + (c[1] && !last ? '<a href="' + c[1] + '">' + esc(c[0]) + "</a>" : '<span aria-current="page">' + esc(c[0]) + "</span>");
    }).join("") + "</nav>";
  }

  /* ---------- pages ---------- */
  function pageHome() {
    $("#stat-files").textContent = fileCount(CAT.subjects) + "+";
    $("#stat-subjects").textContent = CAT.subjects.filter(function (s) { return s.files && s.files.length; }).length;
    $("#stat-courses").textContent = CAT.programs.filter(function (p) { return p.id !== "syllabus"; }).length;
    mountSearch($("#search-input"), $("#search-results"));

    $("#colleges").innerHTML = collegeBlocks("fade-in");

    $("#programs").innerHTML = CAT.programs.filter(function (p) { return !p.years; }).map(function (p) {
      var list = subjectsOf(p.id);
      return '<a class="card fade-in" href="browse.html?program=' + p.id + '"><span class="card-icon"><i class="fa-solid ' + p.icon + '"></i></span>' +
        "<h3>" + esc(p.name) + "</h3><p>" + esc(p.blurb) + "</p>" +
        '<div class="card-foot"><span>' + (p.id === "syllabus" ? fileCount(list) + " documents" : plural(list.length, "subject") + " · " + plural(fileCount(list), "file") + "") +
        '</span><i class="fa-solid fa-arrow-right arrow"></i></div></a>';
    }).join("");

    var tc = {};
    CAT.subjects.forEach(function (s) { (s.files || []).forEach(function (f) { tc[f.k] = (tc[f.k] || 0) + 1; }); });
    var blurbs = {
      notes: "Unit-wise handwritten and typed notes, one-shot revision notes and complete course notes.",
      papers: "Semester and sessional question papers from previous years to practise the real exam pattern.",
      practice: "Practice sets, DPPs, assignments and important questions for every unit.",
      books: "Reference books and lecture slides to go deeper into a topic."
    };
    $("#types").innerHTML = ["notes", "papers", "practice", "books"].map(function (k) {
      return '<div class="card type-card t-' + k + '"><span class="card-icon"><i class="fa-solid ' + TYPES[k].icon + '"></i></span>' +
        "<h3>" + TYPES[k].label + "</h3><p>" + blurbs[k] + '</p><div class="card-foot"><span>' + (tc[k] || 0) + " files</span></div></div>";
    }).join("");
  }

  function pageBrowse() {
    var pid = param("program");
    var app = $("#app");
    if (!pid || !program(pid)) {
      document.title = "Browse study material | ScholarSpace";
      app.innerHTML = '<section class="page-head"><div class="container">' + crumbs([["Home", "index.html"], ["Browse"]]) +
        "<h1>Browse study material</h1><p class=\"lead\">Choose your course and year. B.Tech CSE material is kept separate for BBD University and ITM College (AKTU), because their syllabi and exam patterns differ.</p></div></section>" +
        '<section class="section" style="padding-top:20px"><div class="container"><div class="section-head"><h2>Year-wise courses</h2></div><div id="colleges"></div>' +
        '<div class="section-head" style="margin-top:40px"><h2>More courses</h2></div><div class="grid grid-3" id="programs"></div></div></section>';
      $("#colleges").innerHTML = collegeBlocks();
      $("#programs").innerHTML = CAT.programs.filter(function (p) { return !p.years; }).map(function (p) {
        var list = subjectsOf(p.id);
        return '<a class="card" href="browse.html?program=' + p.id + '"><span class="card-icon"><i class="fa-solid ' + p.icon + '"></i></span><h3>' + esc(p.name) +
          "</h3><p>" + esc(p.blurb) + '</p><div class="card-foot"><span>' + plural(fileCount(list), "file") + '</span><i class="fa-solid fa-arrow-right arrow"></i></div></a>';
      }).join("");
      return;
    }

    var p = program(pid);
    if (pid === "syllabus") { location.replace("subject.html?id=syllabus"); return; }
    var hasYears = !!p.years;
    var year = hasYears ? Math.min(4, Math.max(1, parseInt(param("year"), 10) || 1)) : null;
    var list = subjectsOf(pid, year);
    var title = hasYears ? YEARS[year].name + " · " + p.short : p.name;
    document.title = title + " | ScholarSpace";

    var groupOrder = hasYears ? ["core", "group-a", "group-b", "elective", "open", "skill", "more"] : [];
    if (!hasYears) list.forEach(function (s) { var g = s.group || "core"; if (groupOrder.indexOf(g) === -1) groupOrder.push(g); });

    app.innerHTML = '<section class="page-head"><div class="container">' +
      crumbs([["Home", "index.html"], ["Browse", "browse.html"]].concat(hasYears ? [[p.short, "browse.html?program=" + pid], [YEARS[year].name]] : [[p.name]])) +
      "<h1>" + esc(hasYears ? p.name : p.name) + "</h1>" +
      '<p class="lead">' + (hasYears ? YEARS[year].name + " (" + YEARS[year].sems + "). " : "") + esc(p.blurb) + "</p>" +
      (hasYears && yearPrograms(p.course).length > 1 ? '<div class="college-switch" role="group" aria-label="College"><span>College</span>' + yearPrograms(p.course).map(function (q) {
        return '<a class="tab' + (q.id === pid ? " active" : "") + '"' + (q.id === pid ? ' aria-current="true"' : "") + ' href="browse.html?program=' + q.id + "&year=" + year + '">' +
          '<i class="fa-solid ' + q.icon + '"></i>' + esc(q.short) + "</a>";
      }).join("") + "</div>" : "") +
      '<div class="toolbar">' +
      (hasYears ? '<div class="tabs year-tabs" role="tablist" aria-label="Year">' + [1, 2, 3, 4].map(function (y) {
        return '<a class="tab' + (y === year ? " active" : "") + '" role="tab" aria-selected="' + (y === year) + '" href="browse.html?program=' + pid + "&year=" + y + '">' + YEARS[y].name + "</a>";
      }).join("") + "</div>" : "") +
      '<label class="filter"><i class="fa-solid fa-filter"></i><span class="sr-only">Filter subjects</span><input id="filter" type="search" placeholder="Filter subjects…" autocomplete="off"></label>' +
      "</div></div></section>" +
      '<section style="padding-bottom:24px"><div class="container" id="groups"></div></section>';

    function draw(q) {
      var n = norm(q || "");
      var html = groupOrder.map(function (g) {
        var items = list.filter(function (s) { return (s.group || "core") === g && (!n || norm(s.name + " " + (s.alias || "") + " " + (s.code || "")).indexOf(n) !== -1); });
        if (!items.length) return "";
        items.sort(function (a, b) { return (b.files ? 1 : 0) - (a.files ? 1 : 0); });
        var info = GROUPS[g] || { title: g, note: "" };
        return '<div class="group-title"><h2>' + esc(info.title) + '</h2><span class="badge">' + items.length + "</span></div>" +
          (info.note ? '<p class="group-note">' + esc(info.note) + "</p>" : "") +
          '<div class="grid grid-3">' + items.map(subjectCard).join("") + "</div>";
      }).join("");
      $("#groups").innerHTML = html || '<div class="empty-state" style="margin-top:24px"><i class="fa-solid fa-magnifying-glass"></i><h3>No subjects match</h3><p>Try another word, or search everything from the home page.</p></div>';
    }
    draw("");
    $("#filter").addEventListener("input", function (e) { draw(e.target.value); });
  }

  function pageSubject() {
    var s = subject(param("id"));
    var app = $("#app");
    if (!s && subject("itm-" + param("id"))) { location.replace("subject.html?id=itm-" + encodeURIComponent(param("id"))); return; }
    if (!s) {
      document.title = "Subject not found | ScholarSpace";
      app.innerHTML = '<section class="section"><div class="container"><div class="empty-state"><i class="fa-solid fa-circle-question"></i><h3>Subject not found</h3>' +
        '<p>The link may be out of date.</p><a class="btn btn-primary" href="browse.html">Browse all subjects</a></div></div></section>';
      return;
    }
    var p = program(s.program);
    document.title = s.name + " notes, PYQs & practice sets | ScholarSpace";
    var trail = [["Home", "index.html"], ["Browse", "browse.html"]];
    if (p && p.years && s.year) trail.push([p.short, "browse.html?program=" + s.program], [YEARS[s.year].name, browseUrl(s)]);
    else if (s.program !== "syllabus") trail.push([p.name, browseUrl(s)]);
    trail.push([s.name]);

    var c = counts(s), files = s.files || [];
    var other = counterpart(s), otherNote = "";
    if (other) {
      var op = program(other.program);
      otherNote = '<a class="other-college" href="subject.html?id=' + encodeURIComponent(other.id) + '"><i class="fa-solid ' + op.icon + '"></i>' +
        "<span><b>" + esc(other.name) + " at " + esc(op.college) + "</b>" + plural(other.files.length, "file") +
        " · different syllabus and exam pattern</span><i class=\"fa-solid fa-arrow-right\"></i></a>";
    }
    var tabs = ["all"].concat(TYPE_ORDER.filter(function (k) { return c[k]; }));
    var meta = [];
    if (p && p.college) meta.push('<span class="badge badge-college"><i class="fa-solid ' + (p.years ? p.icon : "fa-school") + '"></i>' + esc(p.college) + "</span>");
    if (p && p.years && s.year) meta.push('<span class="badge"><i class="fa-solid fa-layer-group"></i>' + YEARS[s.year].name + "</span>");
    else if (p && !p.years && s.program !== "syllabus") meta.push('<span class="badge"><i class="fa-solid ' + p.icon + '"></i>' + esc(p.name) + "</span>");
    if (s.code) meta.push('<span class="badge"><i class="fa-solid fa-hashtag"></i>' + esc(s.code) + "</span>");
    if (s.sem) meta.push('<span class="badge"><i class="fa-regular fa-calendar"></i>Semester ' + esc(s.sem) + "</span>");
    meta.push('<span class="badge"><i class="fa-regular fa-file-lines"></i>' + files.length + " files</span>");

    var folderBtns = (s.folders || []).map(function (id, i) {
      return '<a class="btn btn-ghost" href="' + folderUrl(id) + '" target="_blank" rel="noopener"><i class="fa-brands fa-google-drive"></i>' +
        ((s.folders.length > 1) ? "Drive folder " + (i + 1) : "Open folder in Drive") + "</a>";
    }).join("");

    app.innerHTML = '<section class="page-head"><div class="container">' + crumbs(trail) +
      '<div class="subject-hero"><span class="card-icon"><i class="' + brandIcon(s.icon) + '"></i></span><div class="info">' +
      "<h1>" + esc(s.name) + '</h1><div class="meta" style="gap:8px">' + meta.join("") + "</div>" +
      '<div class="subject-actions">' + folderBtns + "</div></div></div>" +
      (files.length ? '<div class="toolbar"><div class="tabs" role="tablist" aria-label="File type">' + tabs.map(function (k, i) {
        var n = k === "all" ? files.length : c[k];
        return '<button class="tab" type="button" role="tab" data-k="' + k + '" aria-selected="' + (i === 0) + '">' +
          (k === "all" ? "All" : (TYPES[k].short || TYPES[k].label)) + '<span class="count">' + n + "</span></button>";
      }).join("") + '</div><label class="filter"><i class="fa-solid fa-magnifying-glass"></i><span class="sr-only">Search files</span>' +
        '<input id="filter" type="search" placeholder="Search in ' + esc(s.name) + '…" autocomplete="off"></label></div>' : "") +
      '</div></section><section><div class="container"><div id="files"></div>' + otherNote + '</div></section>';

    if (!files.length) {
      $("#files").innerHTML = '<div class="empty-state"><i class="fa-solid fa-hourglass-half"></i><h3>Material coming soon</h3>' +
        "<p>We don’t have files for " + esc(s.name) + " yet. If you have notes or papers for this subject, please share them.</p>" +
        '<a class="btn btn-primary" href="feedback.html?subject=' + encodeURIComponent(s.id) + '"><i class="fa-solid fa-upload"></i>Upload notes</a></div>';
      return;
    }

    var kind = "all", q = "";
    function row(f) {
      var t = TYPES[f.k];
      return '<div class="file t-' + f.k + '"><span class="file-icon"><i class="fa-solid ' + (EXT_ICON[f.x] || "fa-file") + '"></i></span>' +
        '<div class="file-main"><a href="' + fileUrl(f.id) + '" target="_blank" rel="noopener">' + esc(f.t) + "</a>" +
        '<div class="file-sub"><span class="chip t-' + f.k + '"><i class="fa-solid ' + t.icon + '"></i>' + (t.short || t.label) + "</span><span>" + esc(f.x.toUpperCase()) + "</span>" +
        (f.c ? '<span class="chip chip-community"><i class="fa-solid fa-user-pen"></i>' + (f.by ? "Shared by " + esc(f.by) : "Student upload") + "</span>" : "") + "</div></div>" +
        '<div class="file-actions"><a class="btn btn-ghost btn-sm" href="' + fileUrl(f.id) + '" target="_blank" rel="noopener"><i class="fa-regular fa-eye"></i>View</a>' +
        '<a class="btn btn-ghost btn-sm" href="' + downloadUrl(f.id) + '" target="_blank" rel="noopener" aria-label="Download ' + esc(f.t) + '"><i class="fa-solid fa-download"></i><span>Download</span></a></div></div>';
    }
    function draw() {
      var n = norm(q);
      var sel = files.filter(function (f) { return (kind === "all" || f.k === kind) && (!n || norm(f.t).indexOf(n) !== -1); });
      if (!sel.length) {
        $("#files").innerHTML = '<div class="empty-state"><i class="fa-solid fa-magnifying-glass"></i><h3>No files match</h3><p>Try another word or pick “All”.</p></div>';
        return;
      }
      var order = kind === "all" ? TYPE_ORDER : [kind];
      $("#files").innerHTML = order.map(function (k) {
        var part = sel.filter(function (f) { return f.k === k; });
        if (!part.length) return "";
        return '<div class="group-title"><h2>' + TYPES[k].label + '</h2><span class="badge">' + part.length + '</span></div><div class="files">' + part.map(row).join("") + "</div>";
      }).join("");
    }
    draw();
    document.querySelectorAll(".tab[data-k]").forEach(function (b) {
      b.addEventListener("click", function () {
        kind = b.getAttribute("data-k");
        document.querySelectorAll(".tab[data-k]").forEach(function (x) { x.setAttribute("aria-selected", String(x === b)); x.classList.toggle("active", x === b); });
        draw();
      });
    });
    var first = document.querySelector(".tab[data-k]");
    if (first) first.classList.add("active");
    $("#filter").addEventListener("input", function (e) { q = e.target.value; draw(); });
  }

  function pageSgpa() {
    var GRADES = [[90, 10, "O"], [75, 9, "A+"], [60, 8, "A"], [55, 7, "B+"], [50, 6, "B"], [45, 5, "C"], [40, 4, "P"], [0, 0, "F"]];
    function grade(m) { for (var i = 0; i < GRADES.length; i++) if (m >= GRADES[i][0]) return GRADES[i]; return GRADES[GRADES.length - 1]; }
    var body = $("#rows");
    var defaults = [["", 4], ["", 4], ["", 3], ["", 3], ["", 3], ["", 2]];
    function addRow(name, credits) {
      var tr = document.createElement("tr");
      tr.innerHTML = '<td class="name"><input class="input" type="text" placeholder="Subject name (optional)" value="' + esc(name || "") + '" aria-label="Subject name"></td>' +
        '<td class="num" data-label="Credits"><input class="input credits" type="number" min="0" max="10" step="0.5" value="' + (credits || "") + '" placeholder="Credits" aria-label="Credits"></td>' +
        '<td class="num" data-label="Marks /100"><input class="input marks" type="number" min="0" max="100" placeholder="Marks" aria-label="Total marks out of 100"></td>' +
        '<td class="grade" data-label="Grade">–</td><td class="del"><button class="icon-btn" type="button" aria-label="Remove subject"><i class="fa-solid fa-trash-can"></i></button></td>';
      tr.querySelector("button").addEventListener("click", function () { tr.remove(); calc(); });
      tr.querySelectorAll("input").forEach(function (i) { i.addEventListener("input", calc); });
      body.appendChild(tr);
    }
    function calc() {
      var cp = 0, cr = 0, marks = 0, n = 0, failed = 0, invalid = false;
      body.querySelectorAll("tr").forEach(function (tr) {
        var c = parseFloat(tr.querySelector(".credits").value), m = parseFloat(tr.querySelector(".marks").value), g = tr.querySelector(".grade");
        if (isNaN(m) || isNaN(c)) { g.textContent = "–"; return; }
        if (m < 0 || m > 100 || c < 0) { g.textContent = "!"; invalid = true; return; }
        var gr = grade(m);
        g.textContent = gr[2];
        g.style.color = gr[1] === 0 ? "var(--papers)" : "var(--practice)";
        cp += gr[1] * c; cr += c; marks += m; n++;
        if (gr[1] === 0) failed++;
      });
      $("#sgpa").textContent = cr ? (cp / cr).toFixed(2) : "0.00";
      $("#credits").textContent = cr;
      $("#percent").textContent = n ? (marks / n).toFixed(2) + "%" : "–";
      $("#subjects").textContent = n;
      var status = $("#status");
      if (invalid) status.innerHTML = '<span style="color:var(--papers)">Marks must be between 0 and 100.</span>';
      else if (failed) status.innerHTML = '<span style="color:var(--papers)">' + failed + " subject" + (failed > 1 ? "s" : "") + " below pass marks (40).</span>";
      else status.textContent = n ? "All subjects passed." : "Enter credits and marks to see your SGPA.";
    }
    defaults.forEach(function (d) { addRow(d[0], d[1]); });
    $("#add-row").addEventListener("click", function () { addRow("", ""); body.lastChild.querySelector("input").focus(); });
    $("#reset").addEventListener("click", function () { body.innerHTML = ""; defaults.forEach(function (d) { addRow(d[0], d[1]); }); calc(); });
    $("#scale").innerHTML = "<tr><th>Marks</th><th>Grade</th><th>Points</th></tr>" + GRADES.map(function (g, i) {
      var hi = i === 0 ? 100 : GRADES[i - 1][0] - 1;
      return "<tr><td>" + g[0] + "–" + hi + "</td><td>" + g[2] + "</td><td>" + g[1] + "</td></tr>";
    }).join("");
    calc();
  }

  function pageAbout() {
    $("#ab-files").textContent = fileCount(CAT.subjects) + "+";
    $("#ab-subjects").textContent = CAT.subjects.filter(function (s) { return s.files && s.files.length; }).length;
    $("#ab-courses").textContent = CAT.programs.filter(function (p) { return p.id !== "syllabus"; }).length;
  }

  function pageFeedback() {
    /* ---- request / feedback by email ---- */
    var topicParam = param("topic");
    if (topicParam && $("#topic option[value='" + topicParam.replace(/[^a-z]/g, "") + "']")) $("#topic").value = topicParam;
    $("#feedback-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var el = e.target.elements;
      var topicSel = el.namedItem("topic");
      var body = el.namedItem("message").value + "\n\n- " + el.namedItem("name").value.trim();
      location.href = "mailto:" + CONTACT.email + "?subject=" + encodeURIComponent("ScholarSpace: " + topicSel.options[topicSel.selectedIndex].text) + "&body=" + encodeURIComponent(body);
      $("#sent").hidden = false;
    });

    /* ---- upload form ---- */
    var MAX_FILES = 5, MAX_BYTES = 15 * 1024 * 1024, OK_EXT = /\.(pdf|docx?|pptx?|xlsx?|jpe?g|png)$/i;
    var progSel = $("#up-program"), yearSel = $("#up-year"), subjSel = $("#up-subject"), status = $("#up-status");
    var progs = CAT.programs.filter(function (p) { return p.id !== "syllabus" && subjectsOf(p.id).length; });
    progSel.innerHTML = progs.map(function (p) { return '<option value="' + p.id + '">' + esc(p.name) + "</option>"; }).join("");
    function fillYears() {
      var p = program(progSel.value);
      $("#up-year-field").hidden = !p.years;
      if (p.years) {
        var ys = [1, 2, 3, 4].filter(function (y) { return subjectsOf(p.id, y).length; });
        yearSel.innerHTML = ys.map(function (y) { return '<option value="' + y + '">' + YEARS[y].name + "</option>"; }).join("");
      }
      fillSubjects();
    }
    function fillSubjects() {
      var p = program(progSel.value);
      var list = subjectsOf(p.id, p.years ? parseInt(yearSel.value, 10) : null).slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
      subjSel.innerHTML = list.map(function (s) { return '<option value="' + s.id + '">' + esc(s.name) + (s.code ? " (" + esc(s.code) + ")" : "") + "</option>"; }).join("");
    }
    progSel.addEventListener("change", fillYears);
    yearSel.addEventListener("change", fillSubjects);
    fillYears();
    var pre = subject(param("subject") || "");
    if (pre) {
      progSel.value = pre.program; fillYears();
      if (pre.year) { yearSel.value = String(pre.year); fillSubjects(); }
      subjSel.value = pre.id;
    }

    function say(kind, html) { status.className = "up-status " + kind; status.innerHTML = html; }
    function readBase64(file) {
      return new Promise(function (resolve, reject) {
        var r = new FileReader();
        r.onload = function () { resolve(String(r.result).split(",")[1] || ""); };
        r.onerror = function () { reject(new Error("Could not read " + file.name)); };
        r.readAsDataURL(file);
      });
    }

    $("#upload-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var files = Array.prototype.slice.call($("#up-files").files || []);
      var title = $("#up-title").value.trim();
      var s = subject(subjSel.value);
      if (!s) return say("error", "Please choose a subject.");
      if (title.length < 3) { $("#up-title").focus(); return say("error", "Please give the file a short title."); }
      if (!files.length) return say("error", "Please choose at least one file.");
      if (files.length > MAX_FILES) return say("error", "You can upload up to " + MAX_FILES + " files at a time.");
      var bad = files.filter(function (f) { return !OK_EXT.test(f.name) || f.size > MAX_BYTES || !f.size; });
      if (bad.length) return say("error", esc(bad[0].name) + " can't be uploaded. Use PDF, Word, PowerPoint, Excel, JPG or PNG files of 15 MB or less.");
      if (!$("#up-agree").checked) return say("error", "Please confirm you have the right to share these files.");

      var p = program(s.program);
      var base = {
        subjectId: s.id, subjectName: s.name, course: p.name + (s.year ? " · " + YEARS[s.year].name : ""),
        kind: $("#up-kind").value, name: $("#up-name").value.trim(), email: $("#up-email").value.trim(),
        note: $("#up-note").value.trim(), website: $("#up-website").value
      };

      if (!UPLOADS_URL) {  // uploads not set up yet: hand over to email
        var body = "Subject: " + s.name + " (" + base.course + ")\nType: " + base.kind + "\nTitle: " + title + "\n\n" + base.note +
          "\n\nI'll attach the files to this email.\n- " + (base.name || "");
        location.href = "mailto:" + CONTACT.email + "?subject=" + encodeURIComponent("Notes for ScholarSpace: " + s.name) + "&body=" + encodeURIComponent(body);
        return say("info", "Your email app should open. Please attach your files there and send it.");
      }

      var btn = $("#up-submit"); btn.disabled = true;
      var done = 0, failed = [];
      say("info", '<i class="fa-solid fa-spinner fa-spin"></i> Uploading 1 of ' + files.length + "…");
      files.reduce(function (chain, f, i) {
        return chain.then(function () {
          say("info", '<i class="fa-solid fa-spinner fa-spin"></i> Uploading ' + (i + 1) + " of " + files.length + ": " + esc(f.name) + "…");
          return readBase64(f).then(function (data) {
            var payload = Object.assign({}, base, { title: files.length > 1 ? title + " (" + (i + 1) + ")" : title, fileName: f.name, data: data });
            return fetch(UPLOADS_URL, { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(payload) });
          }).then(function (r) { return r.json(); }).then(function (res) {
            if (res && res.ok) done++; else failed.push(f.name + ": " + ((res && res.error) || "upload failed"));
          }).catch(function () { failed.push(f.name + ": network error"); });
        });
      }, Promise.resolve()).then(function () {
        btn.disabled = false;
        if (done && !failed.length) {
          say("success", '<i class="fa-solid fa-circle-check"></i> Thank you! ' + plural(done, "file") + " sent for review. Once approved, " + (done > 1 ? "they" : "it") + " will appear on the " + esc(s.name) + " page.");
          $("#up-files").value = ""; $("#up-title").value = ""; $("#up-note").value = "";
        } else {
          say(done ? "info" : "error", (done ? plural(done, "file") + " uploaded. " : "") + "Some files didn't upload:<br>" + failed.map(esc).join("<br>"));
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var page = document.body.getAttribute("data-page");
    mountLayout(page === "subject" ? "browse" : page);
    var run = { home: pageHome, browse: pageBrowse, subject: pageSubject, sgpa: pageSgpa, feedback: pageFeedback, about: pageAbout }[page];
    loadCommunity(function (changed) {  // newly approved uploads arrived after the page was drawn
      if (page === "subject" && changed.indexOf(param("id")) !== -1) pageSubject();
    });
    if (run) run();
  });
})();
