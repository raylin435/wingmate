# Wingmate seed data

All people are fictional. Regenerate with:

```
python3 scripts/make_personas.py        # personas/*.json (author-written DSL inside the script)
python3 scripts/make_sample_export.py   # exports/*.json
python3 scripts/validate_seed.py        # checks everything
```

## Layout

- `personas/<id>.json` - 30 SF personas (ages 25-38). `facts[].share` is `public` or `private`; private facts (smoking, drinking, kids, dealbreakers) are used for matching only and never shown to the other side before mutual opt-in. Every fact `quote` is an exact substring of one of that person's user chat messages.
- `venues.json` - 20 invented SF date spots; tags overlap persona interests.
- `exports/maya_chatgpt_conversations.json` - 61 conversations in ChatGPT `conversations.json` format (46 irrelevant, 15 personal).
- `exports/maya_claude_conversations.json` - 8 conversations in Claude export format.

Slot window: 2026-11-21 (Sat) to 2026-11-27 (Fri). Dealbreaker semantics: a candidate is excluded if `candidate.attributes[attr] == equals`.

## Maya demo storyline

1. Maya imports her ChatGPT export. The agent sifts ~61 conversations, ignoring spreadsheets, code and recipes, and surfaces dating-relevant facts: trail running before 7, dumplings, jazz, Wingspan, Biscuit the beagle mix, not sure about kids, and new details not in her persona (pottery class in Dogpatch, an ex who smoked, her dad's COPD, prefers daytime first dates).
2. **Jordan** looks perfect on paper (trail running, dumplings, jazz, board games, early riser, similar values) but says "I still smoke a few cigarettes when I'm out with friends". Maya's private dealbreaker ("I really can't date someone who smokes") filters him out without revealing why.
3. **Theo** is the genuine match: same interests, no dealbreaker conflicts, and two shared free slots: Sun 2026-11-22 11:00 and Tue 2026-11-24 19:00. The booking agent picks a venue by shared interests (for example Steam & Soup Dumpling House or Lookout Trailhead Coffee; Clayworks Pottery Studio for the pottery angle) and proposes one of the shared slots.
4. Weaker but decent mutual candidates for Maya: **Ben** (board games, dumplings, but night owl and a cat person), **Kenji** (ramen/dumplings, mountain biking, shiba; one shared slot, Sun 11:00), **Diego** (outdoorsy, salsa, drinks often), plus Luis and Wes as long shots.

## Compatible pairs (strong, mutual)

| Pair | Why |
| --- | --- |
| maya + theo | Trail running, dumplings, board games, jazz; shared slots Sun 11:00 and Tue 19:00 |
| lena + rosa | Both women seeking women; climbing/bouldering, ramen, tacos; shared slots Sat 18:00 and Tue 19:00 |
| andre + ravi | Both men seeking men; hiking, cooking, vinyl; shared slots Sun 11:00 and Tue 19:00 |
| ash + kit | Nonbinary; zine fairs, bouldering, bakeries, thrifting; shared slots Sun 11:00 and Tue 19:00; neither wants kids |
| nadia + marcus | Both want kids and value faith (Marcus's dealbreakers exclude non-religious or anti-kids partners; Nadia fits); shared slot Mon evening |
| priya + ben | Comedy, board games, night owls, both fine with their kids stances (priya unsure, ben no, ben's dealbreaker is a partner who wants kids, priya is unsure); shared slots Wed 18:30 and Fri 19:30 |
| zoe + owen | Both do not want kids; water and craft beer; shared slots Sat 18:30 and Fri 18:00 |

## Useful traps for the demo

- Smoking dealbreakers: maya, diego, kenji, luis, wes, priya, sofia, hannah, tessa, lena, june, ravi, caleb, kit vs smokers jordan and eli.
- Kids dealbreakers: chloe, zoe, owen, ben (exclude people who want kids), nadia (excludes people who do not want kids), marcus (also excludes non-religious).
- Marcus has only one mutual candidate (nadia) and Caleb two, so the agent must handle sparse results.
