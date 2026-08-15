# LinkedIn Post Draft

---

**Built an AI system to test one cricket theory: Does "recent form" actually matter?**

Spent the last few weeks on this. Backtested on 144 IPL matches from 2023-24.

Results:

• Agent using historical stats: **55.6% accuracy**
• Agent using "hot team" form (last 5 matches): **43.7% accuracy** 📉

Plot twist: **Recent form is worse than random guessing.**

Turns out all those "CSK is on fire!" or "MI has lost their mojo!" narratives? Mostly noise. Historical patterns beat gut feeling.

**What I learned:**

1. Building separate "agents" for different signals forces you to think clearly
2. My intuition was wrong — backtesting doesn't lie
3. Publishing the 43.7% failure feels more honest than only showing wins

It's a small project, but it changed how I think about data vs. narratives.

Code + full writeup: https://github.com/ATULPS2001/cricket-ai-council

Shoutout to karpathy's llm-council for the vibe coding inspiration ⚡

#MachineLearning #DataScience #AI #Cricket #SportsAnalytics

---

**Optional first comment (with screenshot):**

> Screenshot of the results table from README

---

**DM to recruiter (after posting):**

> Hey [Name], I built this multi-agent prediction system to test ensemble methods on IPL data. Thought you'd find the approach interesting — especially that "recent form" was a negative signal. Would love your take on the architecture if you have 2 mins!

---
