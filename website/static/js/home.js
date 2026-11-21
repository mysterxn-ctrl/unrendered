/* Unrendered landing page: live surface logic. Everything here computes from data in the page. */
(function () {
  "use strict";
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------------------------------------------------------------- copy */
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () {
        btn.textContent = "Copied"; btn.classList.add("is-done");
        setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("is-done"); }, 1500);
      };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, function () {});
      else {
        var ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });

  /* ---------------------------------------------------------------- plan: the skill's decision rule */
  var data = null;
  try { data = JSON.parse($("#board-data").textContent); } catch (e) {}
  var currentModel = { generate: "", edit: "" };
  if (data) {
    Object.keys(data.tracks).forEach(function (track) {
      var t = data.tracks[track], rows = t.rows, cur = t.current;
      var top = rows[0], curRow = rows.filter(function (r) { return r.id === cur; })[0];
      var out = $('[data-verdict="' + track + '"]'), keep = cur, text;
      if (!curRow) { keep = top.id; text = "Current model not on the board: <b>switch to " + esc(top.name) + "</b>."; }
      else if (top.id === cur) { text = "<b>Keep " + esc(curRow.name) + "</b>: first on the board."; }
      else {
        var margin = top.elo - curRow.elo, ciSum = (top.ci || 15) + (curRow.ci || 15);
        if (margin > ciSum) { keep = top.id; text = "<b>Switch to " + esc(top.name) + "</b>: lead " + margin + " Elo is larger than the combined interval " + ciSum + "."; }
        else text = "<b>Keep " + esc(curRow.name) + "</b>: " + esc(top.name) + " leads by " + margin + " Elo, inside the combined interval " + ciSum + ".";
      }
      currentModel[track] = keep;
      if (out) out.innerHTML = text;
      $$('[data-track="' + track + '"] tr[data-model="' + keep + '"]').forEach(function (tr) { tr.classList.add("is-current"); });
    });
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  /* ---------------------------------------------------------------- chrome: tabs, steps, status */
  var order = ["session", "plan", "brief", "inspect", "finish", "your-turn"];
  var statusText = $("#status-text");
  var statusFor = {
    "session": "session ready · sample request · track generate",
    "plan": "plan · track generate · " + (currentModel.generate || "default model") + " · rule: lead > CI(new) + CI(current)",
    "brief": "brief · photographer's view · 9 fields",
    "inspect": "inspect · sample review · 7 findings · verdict: render",
    "finish": "finish · photo_finish",
    "your-turn": "ready · type a request"
  };
  var active = "session";
  function setActive(id) {
    if (id === active) return;
    active = id;
    $$(".chrome__tabs a").forEach(function (a) {
      if (a.getAttribute("data-tab") === id) a.setAttribute("aria-current", "step"); else a.removeAttribute("aria-current");
    });
    var idx = order.indexOf(id);
    $$(".steps li").forEach(function (li) {
      var i = order.indexOf(li.getAttribute("data-step"));
      li.classList.toggle("is-done", i < idx);
      li.classList.toggle("is-active", i === idx);
    });
    if (id !== "finish" && statusText) statusText.textContent = statusFor[id];
  }
  var sections = order.map(function (id) { return document.getElementById(id); }).filter(Boolean);
  function pickActive() {
    var mid = innerHeight * 0.45, best = "session";
    sections.forEach(function (s) { var r = s.getBoundingClientRect(); if (r.top <= mid && r.bottom > mid) best = s.id; });
    setActive(best);
  }
  addEventListener("scroll", pickActive, { passive: true });
  addEventListener("resize", pickActive);
  var first = $('.chrome__tabs a[data-tab="session"]'); if (first) first.setAttribute("aria-current", "step");
  $$(".steps li").forEach(function (li, i) { if (i === 0) li.classList.add("is-active"); });

  /* ---------------------------------------------------------------- inspect: trailing glass lens */
  var frame = $("#lens-frame"), lens = frame && $(".lens", frame), limg = frame && $("img", frame);
  if (frame && lens && limg && fine && !reduce) {
    var Z = 2.4, tx = 0, ty = 0, lx = 0, ly = 0, raf = 0, inside = false;
    var layers = $$(".lens__img, .lens__fringe", lens);
    var src = function () { return limg.currentSrc || limg.src; };
    var setBg = function () { layers.forEach(function (l) { l.style.backgroundImage = 'url("' + src() + '")'; }); };
    if (limg.complete) setBg(); else limg.addEventListener("load", setBg);
    var tick = function () {
      lx += (tx - lx) * 0.14; ly += (ty - ly) * 0.14;
      var L = lens.offsetWidth, w = limg.clientWidth, h = limg.clientHeight;
      lens.style.transform = "translate(" + (lx - L / 2).toFixed(1) + "px," + (ly - L / 2).toFixed(1) + "px)";
      var bx = -(lx * Z - L / 2), by = -(ly * Z - L / 2), size = (w * Z) + "px " + (h * Z) + "px";
      layers.forEach(function (l, i) {
        var d = i === 1 ? 2.5 : i === 2 ? -2.5 : 0;
        l.style.backgroundSize = size;
        l.style.backgroundPosition = (bx + d) + "px " + by + "px";
      });
      if (inside || Math.abs(tx - lx) + Math.abs(ty - ly) > 0.3) raf = requestAnimationFrame(tick); else raf = 0;
    };
    frame.addEventListener("pointermove", function (e) {
      var r = limg.getBoundingClientRect(); tx = e.clientX - r.left; ty = e.clientY - r.top;
      if (!inside) { inside = true; lens.classList.add("is-on"); if (!lx && !ly) { lx = tx; ly = ty; } }
      if (!raf) raf = requestAnimationFrame(tick);
    });
    frame.addEventListener("pointerleave", function () { inside = false; lens.classList.remove("is-on"); });
  }

  /* ---------------------------------------------------------------- finish: render / photo slider */
  // Pointer (or finger, or keyboard) moves the line between the render and the photo.
  var compare = $("#compare");
  if (compare) {
    var photo = $(".compare__photo", compare), line = $(".compare__line", compare), range = $(".compare__range", compare);
    var target = 50, shown = 50, raf = 0;
    var paint = function () {
      shown += (target - shown) * (reduce ? 1 : 0.22);
      if (Math.abs(target - shown) < 0.05) shown = target;
      photo.style.clipPath = "inset(0 0 0 " + shown.toFixed(2) + "%)";
      line.style.transform = "translateX(" + (shown / 100 * compare.clientWidth).toFixed(1) + "px)";
      if (statusText && active === "finish") statusText.textContent = "finish · render " + Math.round(shown) + "% · photo " + Math.round(100 - shown) + "%";
      raf = shown !== target ? requestAnimationFrame(paint) : 0;
    };
    var set = function (pct) {
      target = Math.max(0, Math.min(100, pct));
      if (range && Math.round(target) !== +range.value) range.value = Math.round(target);
      if (!raf) raf = requestAnimationFrame(paint);
    };
    var fromEvent = function (e) { var r = compare.getBoundingClientRect(); set((e.clientX - r.left) / r.width * 100); };
    compare.addEventListener("pointermove", function (e) {
      if (e.pointerType === "mouse" || e.pointerType === "pen" || e.buttons) fromEvent(e);
    });
    compare.addEventListener("pointerdown", function (e) { fromEvent(e); });
    if (range) range.addEventListener("input", function () { set(+range.value); });
    set(50);
  }

  /* ---------------------------------------------------------------- your turn: brief console */
  var RECIPES = [
    { genre: "selfie", rx: /\bselfie/, mm: 24, f: "1.8", s: "1/60", iso: 400, k: 5600, light: [-0.4, 0.9], text: "phone front camera at arm's length, window light from the front left" },
    { genre: "on-camera flash snapshot", rx: /\b(party|club|birthday|wedding|friends? (at|in))/, mm: 28, f: "4", s: "1/60", iso: 800, k: 5500, light: [0, 1], text: "direct on-camera flash, hard shadow on the wall behind" },
    { genre: "sports", rx: /\b(football|soccer|basketball|tennis|runner|running|race|match|sprint)/, mm: 400, f: "2.8", s: "1/2000", iso: 1600, k: 5600, light: [0.6, -0.8], text: "high side sun from behind right, rim on the players" },
    { genre: "wildlife", rx: /\b(bird|fox|deer|wolf|lion|wildlife|eagle|owl|bear)/, mm: 300, f: "4", s: "1/1000", iso: 800, k: 4800, light: [-0.8, 0.3], text: "low morning side light from the left" },
    { genre: "studio product", rx: /\b(product|bottle|shoe|sneaker|watch|perfume|bag|packaging|headphones|phone case|mug)/, mm: 100, f: "11", s: "1/160", iso: 100, k: 5500, light: [-0.7, 0.7], text: "large strip softbox at 45 degrees camera left, white bounce right" },
    { genre: "food", rx: /\b(food|dish|plate|pizza|pasta|cake|salad|breakfast|burger|soup|sushi|bread)/, mm: 60, f: "4", s: "1/100", iso: 400, k: 5600, light: [-0.5, -0.85], text: "window backlight from behind left, steam and texture lit from the back" },
    { genre: "night ambient", rx: /\b(night|neon|bar|concert|midnight|street ?lights?)/, mm: 35, f: "1.4", s: "1/60", iso: 3200, k: 3200, light: [0.85, 0.2], text: "mixed sodium and LED practicals from the right, deep shadows" },
    { genre: "environmental portrait", rx: /\b(man|woman|person|people|girl|boy|child|kid|grand(ma|pa|mother|father)|portrait|face|chef|worker|farmer|nurse|doctor|musician|artist|barista|teacher|old)/, mm: 50, f: "2.8", s: "1/125", iso: 800, k: 5600, light: [-1, 0.25], text: "window light from camera left as the only key, gentle falloff" },
    { genre: "street documentary", rx: /\b(street|city|market|crowd|subway|station|alley|traffic|bus)/, mm: 35, f: "8", s: "1/250", iso: 400, k: 5500, light: [0.75, 0.55], text: "hard afternoon sun from the right, deep shadows" },
    { genre: "interior", rx: /\b(kitchen|room|interior|living|house|office|hotel|lobby|cafe|café|restaurant)/, mm: 20, f: "8", s: "1/30", iso: 400, k: 5600, light: [-0.9, -0.3], text: "daylight through a window behind left, lamps on" },
    { genre: "landscape", rx: /\b(mountain|beach|sea|ocean|lake|forest|desert|valley|field|landscape|coast|river|island)/, mm: 24, f: "11", s: "1/125", iso: 100, k: 5200, light: [0.55, -0.85], text: "low sun ahead right, haze building with distance" }
  ];
  var DEFAULT = { genre: "documentary", mm: 35, f: "5.6", s: "1/250", iso: 400, k: 5600, light: [-0.6, 0.6], text: "available daylight from the front left" };
  var COLORS = ["#ffc857", "#00e5ff", "#a56cff", "#ff8a00", "#f7f5f0", "#7ee0a1"];
  function compile(req) {
    var q = req.toLowerCase(), r = DEFAULT;
    for (var i = 0; i < RECIPES.length; i++) if (RECIPES[i].rx.test(q)) { r = RECIPES[i]; break; }
    var b = { genre: r.genre, mm: r.mm, f: r.f, s: r.s, iso: r.iso, k: r.k, light: r.light.slice(), text: r.text };
    if (/\b(sunset|golden hour|dusk|sunrise|dawn)\b/.test(q)) { b.k = 3500; b.light = [0.95, -0.3]; b.text = "low golden sun from the right, long shadows toward camera"; }
    else if (/\b(overcast|rain|rainy|fog|foggy|grey|gray|cloudy|snow)\b/.test(q)) { b.k = 6500; b.text = "soft overcast light, open shade, no hard shadows"; }
    else if (/\b(candle|candlelight|fireplace)\b/.test(q)) { b.k = 1900; b.iso = 3200; b.f = "1.8"; b.text = "candle as the only source, warm falloff into black"; }
    if (/\bindoor|inside\b/.test(q) && b.iso < 800) b.iso = 800;
    return b;
  }
  var form = $("#console"), input = $("#request"), view = $("#console-view"), cards = $("#cards"), arrows = $("#arrows");
  var count = 0, svgNS = "http://www.w3.org/2000/svg";
  function addArrow(b, color, req) {
    var len = Math.hypot(b.light[0], b.light[1]) || 1, x = b.light[0] / len * 88, y = b.light[1] / len * 88;
    var g = document.createElementNS(svgNS, "g"); g.setAttribute("class", "arrow");
    var line = document.createElementNS(svgNS, "line");
    line.setAttribute("x1", 0); line.setAttribute("y1", 0); line.setAttribute("x2", x.toFixed(1)); line.setAttribute("y2", y.toFixed(1)); line.setAttribute("stroke", color);
    var a = Math.atan2(y, x), hx = x - 9 * Math.cos(a), hy = y - 9 * Math.sin(a);
    var head = document.createElementNS(svgNS, "path");
    head.setAttribute("d", "M" + x.toFixed(1) + " " + y.toFixed(1) + " L" + (hx - 5 * Math.sin(a)).toFixed(1) + " " + (hy + 5 * Math.cos(a)).toFixed(1) +
      " L" + (hx + 5 * Math.sin(a)).toFixed(1) + " " + (hy - 5 * Math.cos(a)).toFixed(1) + " Z");
    head.setAttribute("fill", color);
    var title = document.createElementNS(svgNS, "title"); title.textContent = req + ": key light, " + b.text;
    var hit = document.createElementNS(svgNS, "line");
    hit.setAttribute("x1", 0); hit.setAttribute("y1", 0); hit.setAttribute("x2", x.toFixed(1)); hit.setAttribute("y2", y.toFixed(1));
    hit.setAttribute("stroke", "transparent"); hit.setAttribute("stroke-width", 14);
    g.appendChild(title); g.appendChild(line); g.appendChild(head); g.appendChild(hit);
    g.addEventListener("pointerenter", function () { arrows.classList.add("is-focus"); g.classList.add("is-hot"); });
    g.addEventListener("pointerleave", function () { arrows.classList.remove("is-focus"); g.classList.remove("is-hot"); });
    arrows.appendChild(g);
  }
  function addCard(b, color, req) {
    var c = document.createElement("article"); c.className = "card"; c.setAttribute("role", "listitem");
    var head = document.createElement("div"); head.className = "card__head";
    var id = document.createElement("span"); id.className = "card__id"; id.style.background = color;
    var q = document.createElement("span"); q.className = "card__req"; q.textContent = req;
    head.appendChild(id); head.appendChild(q);
    var genre = document.createElement("p"); genre.className = "card__genre"; genre.textContent = "brief " + count + " · " + b.genre;
    var dl = document.createElement("dl");
    [["mm", b.mm], ["f/", b.f], ["s", b.s], ["ISO", b.iso], ["K", b.k]].forEach(function (pair) {
      var d = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
      dt.textContent = pair[0]; dd.textContent = pair[1]; d.appendChild(dt); d.appendChild(dd); dl.appendChild(d);
    });
    var light = document.createElement("p"); light.className = "card__light"; light.textContent = "Key light: " + b.text + ".";
    c.appendChild(head); c.appendChild(genre); c.appendChild(dl); c.appendChild(light);
    cards.appendChild(c);
    cards.scrollTo({ left: cards.scrollWidth, behavior: reduce ? "auto" : "smooth" });
  }
  if (form && input) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var req = input.value.trim().replace(/\s+/g, " ");
      if (req.length < 3) { form.classList.remove("is-error"); void form.offsetWidth; form.classList.add("is-error"); input.focus(); return; }
      input.disabled = true;
      setTimeout(function () {
        count += 1;
        var b = compile(req), color = COLORS[(count - 1) % COLORS.length];
        if (view.hidden) view.hidden = false;
        addCard(b, color, req); addArrow(b, color, req);
        if (statusText) statusText.textContent = "brief " + count + " · " + b.genre + " · " + b.mm + " mm f/" + b.f + " " + b.s + " ISO " + b.iso + " " + b.k + " K";
        input.disabled = false; input.value = ""; input.focus({ preventScroll: true });
      }, reduce ? 0 : 280);
    });
    var focused = false;
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && !focused && fine && document.activeElement === document.body) { focused = true; input.focus({ preventScroll: true }); }
      });
    }, { threshold: 0.6 }).observe(form);
  }
})();
