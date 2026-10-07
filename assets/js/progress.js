/*
 * Progress tracking for the System Design in 60 Days site.
 *
 * Everything lives in localStorage on the reader's own device. Nothing is sent
 * anywhere. Each day has four blocks (read, drill, build, write); a day counts
 * as complete when all four are ticked. Works on two kinds of page:
 *   - a day page, which carries one .sd-day-progress control for that day
 *   - the tracker page, which lists every published day and shows the bar
 *
 * Written defensively: if localStorage is blocked (private windows, some
 * browsers), the checkboxes still toggle for the session, they just don't
 * persist, and nothing throws.
 */
(function () {
  "use strict";

  var KEY = "sd60-progress";
  var BLOCKS = ["read", "drill", "build", "write"];

  function load() {
    try {
      var raw = window.localStorage.getItem(KEY);
      return new Set(raw ? JSON.parse(raw) : []);
    } catch (e) {
      return new Set();
    }
  }

  function save(set) {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(Array.from(set)));
    } catch (e) {
      /* storage unavailable; keep going in memory for this session */
    }
  }

  var done = load();

  function key(day, block) {
    return day + ":" + block;
  }

  function blocksDoneFor(day) {
    return BLOCKS.filter(function (b) {
      return done.has(key(day, b));
    }).length;
  }

  function wireCheckboxes() {
    var boxes = document.querySelectorAll(
      'input[type="checkbox"][data-day][data-block]'
    );
    Array.prototype.forEach.call(boxes, function (box) {
      var k = key(box.getAttribute("data-day"), box.getAttribute("data-block"));
      box.checked = done.has(k);
      box.addEventListener("change", function () {
        if (box.checked) {
          done.add(k);
        } else {
          done.delete(k);
        }
        save(done);
        refreshAll();
      });
    });
  }

  function refreshDayControls() {
    var controls = document.querySelectorAll(".sd-day-progress[data-day]");
    Array.prototype.forEach.call(controls, function (el) {
      var day = el.getAttribute("data-day");
      var n = blocksDoneFor(day);
      el.classList.toggle("is-complete", n === BLOCKS.length);
      var badge = el.querySelector(".sd-day-count");
      if (badge) {
        badge.textContent = n === BLOCKS.length ? "done" : n + " of 4";
      }
    });
  }

  function refreshTracker() {
    var tracker = document.getElementById("sd-tracker");
    if (!tracker) {
      return;
    }
    var rows = tracker.querySelectorAll(".sd-row[data-day]");
    var totalDays = rows.length;
    var totalBlocks = totalDays * BLOCKS.length;
    var daysDone = 0;
    var blocksDone = 0;
    Array.prototype.forEach.call(rows, function (row) {
      var n = blocksDoneFor(row.getAttribute("data-day"));
      blocksDone += n;
      var complete = n === BLOCKS.length;
      if (complete) {
        daysDone += 1;
      }
      row.classList.toggle("is-complete", complete);
    });

    var pct = totalBlocks ? Math.round((blocksDone / totalBlocks) * 100) : 0;
    var fill = document.getElementById("sd-bar-fill");
    if (fill) {
      fill.style.width = pct + "%";
    }
    var count = document.getElementById("sd-count");
    if (count) {
      count.textContent =
        daysDone +
        " of " +
        totalDays +
        " days complete  (" +
        blocksDone +
        " of " +
        totalBlocks +
        " blocks, " +
        pct +
        "%)";
    }
  }

  function refreshAll() {
    refreshDayControls();
    refreshTracker();
  }

  function wireReset() {
    var btn = document.getElementById("sd-reset");
    if (!btn) {
      return;
    }
    btn.addEventListener("click", function () {
      var ok = window.confirm(
        "Reset all progress on this device? This cannot be undone."
      );
      if (!ok) {
        return;
      }
      done = new Set();
      try {
        window.localStorage.removeItem(KEY);
      } catch (e) {
        /* ignore */
      }
      var boxes = document.querySelectorAll(
        'input[type="checkbox"][data-day][data-block]'
      );
      Array.prototype.forEach.call(boxes, function (box) {
        box.checked = false;
      });
      refreshAll();
    });
  }

  function init() {
    wireCheckboxes();
    wireReset();
    refreshAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
