---
title: "Day 7 design template"
parent: "Day 7: your first real design"
grand_parent: "Week 1: ground truth"
nav_order: 1
---

# Day 7: design a URL shortener

Fill this in against the clock, 45 minutes for a first full pass, before you open the Solutions on the day page. Then go back with the readings and improve it, marking what you added.

## 1. Requirements

Functional (what it must do):

Non-functional (how well: speed, availability, scale, read vs write):

## 2. Scale estimate

Writes per second (average and peak):

Reads per second (average and peak):

URLs stored over 5 years, and terabytes:

The one number that drives the design:

## 3. API

Create a short URL (method, path, body, response, status):

Use a short URL / redirect (method, path, response, 301 or 302 and why):

## 4. Data model

Table, keys, and why the redirect is a single fast lookup:

## 5. Short code

Scheme chosen (counter+base62 / hash / random), and how long the code is:

Why this scheme, and its weakness:

## 6. High-level design

The write path (boxes, in order):

The read path (boxes, in order, and where the cache sits):

Why the two paths differ:

## 7. Bottleneck and failure

What gives out first, at what number:

What you add to fix it, and the database read rate afterwards:

What happens when a server dies, and when the cache dies:

## Second pass

What my second pass added that my first pass missed:
