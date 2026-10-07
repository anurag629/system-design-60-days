---
title: "Track your progress"
nav_order: 2
permalink: /tracker/
---

# Track your progress 📊

Tick off each block as you finish it. A day is done when all four of its blocks, read, drill, build and write, are ticked.

Your progress is saved in this browser, on this device, and nowhere else. It is not sent anywhere and it is not an account, so it will not follow you to another browser or another machine. Clearing it is one button, below.

<div id="sd-progress-summary">
  <div class="sd-bar" aria-hidden="true"><div id="sd-bar-fill" class="sd-bar-fill"></div></div>
  <p id="sd-count" class="sd-count">Loading your progress...</p>
  <button id="sd-reset" class="sd-reset" type="button">Reset progress</button>
</div>

<div id="sd-tracker">
{%- assign days = site.pages | where_exp: "p", "p.url contains '/days/'" | sort: "url" -%}
{%- assign current_week = "" -%}
{%- for d in days -%}
  {%- assign dayid = d.url | split: "/" | last | split: "." | first -%}
  {%- if d.parent != current_week -%}
    {%- assign current_week = d.parent -%}
  <h3 class="sd-week">{{ current_week }}</h3>
  {%- endif -%}
  <div class="sd-row" data-day="{{ dayid }}">
    <a class="sd-row-title" href="{{ d.url | relative_url }}">{{ d.title }}</a>
    <span class="sd-row-blocks">
      <label title="Read"><input type="checkbox" data-day="{{ dayid }}" data-block="read"> R</label>
      <label title="Drill"><input type="checkbox" data-day="{{ dayid }}" data-block="drill"> D</label>
      <label title="Build"><input type="checkbox" data-day="{{ dayid }}" data-block="build"> B</label>
      <label title="Write"><input type="checkbox" data-day="{{ dayid }}" data-block="write"> W</label>
    </span>
  </div>
{%- endfor -%}
</div>

New days appear here automatically as they are published. The full roadmap for all sixty days lives in the week pages in the sidebar.
