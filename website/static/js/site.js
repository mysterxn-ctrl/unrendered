// Unrendered — small progressive enhancements. The site is fully usable without JavaScript.
(function () {
  "use strict";

  var COPY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>';

  function copyText(text, btn) {
    var done = function () {
      var label = btn.querySelector("span");
      btn.classList.add("copied");
      if (label) label.textContent = "Copied";
      setTimeout(function () {
        btn.classList.remove("copied");
        if (label) label.textContent = "Copy";
      }, 1600);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {});
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  // explicit copy buttons (install line)
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () { copyText(btn.getAttribute("data-copy"), btn); });
  });

  // copy buttons for every code block
  document.querySelectorAll(".prose pre, .codeblock pre").forEach(function (pre) {
    var wrap = pre.closest(".codeblock");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "codeblock";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
    }
    if (wrap.querySelector(".copy-btn")) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.setAttribute("aria-label", "Copy code");
    btn.innerHTML = COPY_ICON + "<span>Copy</span>";
    btn.addEventListener("click", function () { copyText(pre.innerText.replace(/\n$/, ""), btn); });
    wrap.appendChild(btn);
  });

  // mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // highlight the current section in the docs table of contents
  var toc = document.querySelector(".docs-toc");
  if (toc && "IntersectionObserver" in window) {
    var links = {};
    toc.querySelectorAll("a[href^='#']").forEach(function (a) { links[decodeURIComponent(a.hash.slice(1))] = a; });
    var current = null;
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          if (current) current.classList.remove("active");
          current = links[e.target.id];
          current.classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    document.querySelectorAll(".prose h2[id], .prose h3[id]").forEach(function (h) { obs.observe(h); });
  }
})();

// collapse the docs menu on small screens (it stays open without JavaScript)
(function () {
  var menu = document.querySelector(".docs-menu");
  if (menu && window.matchMedia && window.matchMedia("(max-width: 920px)").matches) menu.removeAttribute("open");
})();
