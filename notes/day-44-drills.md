---
title: "Day 44 drills"
parent: "Day 44: SLOs and error budgets"
grand_parent: "Week 7: production"
nav_order: 2
---

# Day 44 drills

Paper first, with numbers. SLIs, SLOs, error budgets, burn rate, and the way dependencies multiply. A month is 43,830 minutes (the average Gregorian month, the figure behind Day 2's nines table).

D1 (nines and downtime: over one month, how many minutes of downtime does each of 99.9%, 99.95% and 99.99% allow? Which row is "three nines", and how much does the step from 99.9% to 99.99% cost you in room?):

D2 (budget in requests: a service serves 5,000,000 requests this month under a 99.95% SLO. How many failures are you allowed? If it logged 1,800 failures, what percent of the budget did it spend, how much is left, and are you meeting the SLO?):

D3 (burn rate: SLO is 99.9%. A one-hour incident serves 60,000 requests and fails 1,200 of them. What is the error rate during the incident, and the burn rate? If that rate were sustained, roughly how long until the whole month's budget is gone?):

D4 (dependencies multiply: your service needs all 4 of its dependencies. Three are at 99.9% and one legacy service is at 99%. What is your combined availability ceiling, which dependency dominates the loss, and what does the ceiling become if you make the legacy one optional with a fallback?):

D5 (choosing the target: product asks for "100% uptime" on an internal batch-reporting API. Give two concrete reasons 100% is the wrong goal, propose a defensible SLO, state the error budget it implies in minutes per month, and say what that leftover budget lets the team actually do):
