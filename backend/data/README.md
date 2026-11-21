# Wingmate seed data

All people are fictional except **Cici**, a real teammate. Her persona is built from the friend-style
portrait her own assistant wrote with the Step 1 import prompt, plus her own answers for matching fields
(age range, neighborhood, slots, handle and tagline were filled in for the demo). Only low-sensitivity
portrait details are included; keep anything the portrait marks private out of `make_personas.py`.

Regenerate with:

```
python3 scripts/make_personas.py        # personas/*.json (author-written DSL inside the script)
python3 scripts/make_sample_export.py   # exports/*.json
python3 scripts/validate_seed.py        # checks everything
```

## Layout

- `personas/<id>.json` - 31 SF personas (ages 25-38). `facts[].share` is `public` or `private`; private facts (smoking, drinking, kids, dealbreakers) are used for matching only and never shown to the other side before mutual opt-in. Every fact `quote` is an exact substring of one of that person's user chat messages.
- `venues.json` - 20 invented SF date spots; tags overlap persona interests.
- `exports/rachel_chatgpt_conversations.json` - 61 conversations in ChatGPT `conversations.json` format (46 irrelevant, 15 personal).
- `exports/rachel_claude_conversations.json` - 8 conversations in Claude export format.

Slot window: 2026-11-21 (Sat) to 2026-11-27 (Fri). Dealbreaker semantics: a candidate is excluded if `candidate.attributes[attr] == equals`.

## Rachel demo storyline

1. Rachel imports her ChatGPT export. The agent sifts ~61 conversations, ignoring spreadsheets, code and recipes, and surfaces dating-relevant facts: trail running before 7, dumplings, jazz, Wingspan, Biscuit the beagle mix, not sure about kids, and new details not in her persona (pottery class in Dogpatch, an ex who smoked, her dad's COPD, prefers daytime first dates).
2. **Chris** looks perfect on paper (trail running, dumplings, jazz, board games, early riser, similar values) but says "I still smoke a few cigarettes when I'm out with friends". Rachel's private dealbreaker ("I really can't date someone who smokes") filters him out without revealing why.
3. **Matt** is the genuine match: same interests, no dealbreaker conflicts, and two shared free slots: Sun 2026-11-22 11:00 and Tue 2026-11-24 19:00. The booking agent picks a venue by shared interests (for example Steam & Soup Dumpling House or Lookout Trailhead Coffee; Clayworks Pottery Studio for the pottery angle) and proposes one of the shared slots.
4. Weaker but decent mutual candidates for Rachel: **Greg** (board games, dumplings, but night owl and a cat person), **Kevin** (ramen/dumplings, mountain biking, shiba; one shared slot, Sun 11:00), **Javier** (outdoorsy, salsa, drinks often), plus Adrian and Patrick as long shots.

## Compatible pairs (strong, mutual)

| Pair | Why |
| --- | --- |
| rachel + matt | Trail running, dumplings, board games, jazz; shared slots Sun 11:00 and Tue 19:00 |
| erin + marisol | Both women seeking women; climbing/bouldering, ramen, tacos; shared slots Sat 18:00 and Tue 19:00 |
| darius + arjun | Both men seeking men; hiking, cooking, vinyl; shared slots Sun 11:00 and Tue 19:00 |
| robin + alex | Nonbinary; zine fairs, bouldering, bakeries, thrifting; shared slots Sun 11:00 and Tue 19:00; neither wants kids |
| leila + jerome | Both want kids and value faith (Jerome's dealbreakers exclude non-religious or anti-kids partners; Leila fits); shared slot Mon evening |
| anjali + greg | Comedy, board games, night owls, both fine with their kids stances (anjali unsure, greg no, greg's dealbreaker is a partner who wants kids, anjali is unsure); shared slots Wed 18:30 and Fri 19:30 |
| allison + brian | Both do not want kids; water and craft beer; shared slots Sat 18:30 and Fri 18:00 |

## Useful traps for the demo

- Smoking dealbreakers: rachel, javier, kevin, adrian, patrick, anjali, natalie, lauren, kayla, erin, megan, arjun, nate, alex vs smokers chris and tyler.
- Kids dealbreakers: brianna, allison, brian, greg (exclude people who want kids), leila (excludes people who do not want kids), jerome (also excludes non-religious).
- Jerome has only one mutual candidate (leila) and Nate two, so the agent must handle sparse results.
