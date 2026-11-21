#!/usr/bin/env python3
"""Generates synthetic chat-history exports for Rachel (fictional) in the ChatGPT and Claude formats.

Run:  python3 scripts/make_sample_export.py
Writes data/exports/rachel_chatgpt_conversations.json and data/exports/rachel_claude_conversations.json
"""
import datetime as dt
import json
import pathlib
import uuid

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "exports"
U, A = "user", "assistant"

# --------------------------------------------------------------------------
# ~45 irrelevant conversations: (title, [(role, text), ...])
# --------------------------------------------------------------------------
IRRELEVANT = [
    ("VLOOKUP vs XLOOKUP", [(U, "What's the difference between VLOOKUP and XLOOKUP in Google Sheets? I keep getting #N/A on my vendor sheet."), (A, "XLOOKUP searches in any direction and returns a column you pick, while VLOOKUP needs the key in the first column. Your #N/A is likely trailing spaces; wrap the key in TRIM().")]),
    ("Pivot table for survey results", [(U, "I have 400 rows of usability survey results. How do I build a pivot table showing average score by task and by participant segment?"), (A, "Insert > Pivot table, put Task in Rows, Segment in Columns, and Score in Values summarized by AVERAGE."), (U, "Can I add a count of responses too?"), (A, "Yes, add Score again in Values and set it to COUNTA.")]),
    ("Conditional formatting formula", [(U, "How do I highlight an entire row in Sheets if column D says 'Blocked'?"), (A, "Use a custom formula rule on the range A2:H100: =$D2=\"Blocked\". The dollar sign anchors the column.")]),
    ("Python pandas groupby", [(U, "My pandas groupby returns a MultiIndex and I just want flat columns. How?"), (A, "Call .reset_index() after the aggregation, or pass as_index=False to groupby. For named aggregates use .agg(total=('amt','sum')).")]),
    ("Regex to extract order numbers", [(U, "I need a regex that pulls order numbers like ORD-2024-00871 out of messy email text."), (A, "Try ORD-\\d{4}-\\d{5}. Add \\b on both sides if you want to avoid partial matches.")]),
    ("CSS flexbox centering", [(U, "I can never remember how to center a div both ways. Help?"), (A, "On the parent: display:flex; justify-content:center; align-items:center; and give it a height.")]),
    ("Git rebase vs merge", [(U, "When should I rebase versus merge for a long-lived feature branch on our design tokens repo?"), (A, "Rebase for a clean linear history on private branches; merge when others share the branch so you do not rewrite public history.")]),
    ("Figma auto layout spacing", [(U, "My auto layout card keeps collapsing when the text is short. How do I set a minimum width?"), (A, "Set the frame to fixed width or add a min-width in the resizing options, and keep the text layer on Fill container.")]),
    ("Cups to grams conversion", [(U, "Convert 2 and 1/4 cups of all-purpose flour to grams."), (A, "Roughly 270 grams, using about 120 grams per cup.")]),
    ("Doubling a cookie recipe", [(U, "I need to double a recipe that calls for 3/4 cup brown sugar and 1 egg. What do I use?"), (A, "1 1/2 cups brown sugar and 2 eggs. Keep the baking soda at double too, but check that your pan holds the dough.")]),
    ("Lisbon trip logistics", [(U, "I land in Lisbon at 9:40am and the hotel check-in is 3pm. Best way to spend the gap and handle bags?"), (A, "Store bags at the airport or a luggage service near Baixa, then do a walk through Alfama and lunch at a market hall."), (U, "And how do I get from the airport to the city?"), (A, "The metro red line runs straight into the center in about 30 minutes and costs a couple of euros.")]),
    ("Tahoe weekend packing list", [(U, "Make me a packing list for a two-night winter cabin weekend in Tahoe with friends, car trip."), (A, "Layers, waterproof boots, chains, snacks, headlamp, board games, a speaker, and a cooler for the group dinner.")]),
    ("Portland flight options", [(U, "Compare flying SFO to Portland versus taking the train for a work offsite."), (A, "Flying is about 1h45 but with airport time it is roughly equal door to door. The train is scenic yet takes much longer, so only choose it if you have a day to spare.")]),
    ("Email to landlord about heater", [(U, "Draft a polite but firm email to my landlord. The heater has been broken for nine days."), (A, "Subject: Heater repair needed. Hi Mr. Castillo, the heater in unit 3 has not worked since the 4th. Could you confirm a repair date this week? I can provide access any weekday afternoon. Thank you.")]),
    ("Email declining a vendor", [(U, "Write a short email telling a vendor we are going with another provider, keep it kind."), (A, "Thank you for the proposal and for your time. After review we have decided to move in a different direction. We appreciate the effort and would be glad to stay in touch.")]),
    ("Raise request talking points", [(U, "Help me outline how to ask my manager for a raise, I led two launches this year."), (A, "Lead with impact: both launches, metrics, scope growth, then state the number you want and ask for a timeline to decide.")]),
    ("Resume bullets for a design systems project", [(U, "Turn this into a strong resume bullet: built a component library used by 6 teams."), (A, "Built and launched a component library adopted by 6 product teams, cutting UI build time by about a third and eliminating inconsistent patterns.")]),
    ("Color contrast for buttons", [(U, "Is white text on #7FB069 accessible?"), (A, "It fails WCAG AA at roughly 2.3:1. Darken the green to something like #3F7D2A or use dark text.")]),
    ("User interview script", [(U, "Write a 30-minute user interview script for people who plan their own home renovations."), (A, "Open with warm-up and consent, then past behavior questions, a walkthrough of their last project, pain points, and close with a magic wand question.")]),
    ("Workshop agenda", [(U, "Build a two-hour agenda for a design sprint kickoff with eight people."), (A, "10 min intro, 25 min problem framing, 30 min lightning demos, 15 min break, 30 min sketching, 10 min voting.")]),
    ("Pricing page copy", [(U, "Suggest three headline options for a SaaS pricing page for a small team scheduling tool."), (A, "Simple pricing that scales with your team. Pay for seats you actually use. Start free, upgrade when you grow.")]),
    ("Leaky faucet fix", [(U, "My kitchen faucet drips from the spout handle. How do I fix it?"), (A, "Turn off the water, remove the handle, and replace the worn cartridge or O-ring. Bring the old part to the hardware store to match it.")]),
    ("Houseplant yellow leaves", [(U, "My pothos has yellow leaves and soggy soil. Help."), (A, "Classic overwatering. Let the top two inches dry out between waterings and make sure the pot drains.")]),
    ("Unit conversion for a tent", [(U, "How many square feet is a 10 by 12 meter tent, and how many people does it seat at rounds?"), (A, "That is about 1,292 square feet, seating roughly 80 people at rounds of eight.")]),
    ("Quarterly estimated taxes", [(U, "I did some freelance work. How do quarterly estimated taxes work in California?"), (A, "You pay federal and state estimates on April 15, June 15, September 15, and January 15. A tax pro can confirm safe-harbor amounts for you.")]),
    ("Summary of Atomic Habits", [(U, "Give me a five-bullet summary of Atomic Habits."), (A, "Small changes compound; focus on identity; make cues obvious; make habits easy and attractive; track and review.")]),
    ("SQL join question", [(U, "What is the difference between LEFT JOIN and INNER JOIN with an example for orders and customers?"), (A, "INNER JOIN keeps customers with orders only. LEFT JOIN keeps all customers and fills NULLs where there is no order.")]),
    ("Google Sheets budget template", [(U, "Set up a monthly budget sheet with categories, planned, and actual columns plus variance."), (A, "Columns: Category, Planned, Actual, Variance =C2-B2, and a SUM row. Add conditional formatting for negative variance.")]),
    ("Meeting notes cleanup", [(U, "Clean up these messy notes into action items with owners and dates."), (A, "Here is a table: Action, Owner, Due. I flagged two items that had no owner, so confirm those.")]),
    ("Slack message tone", [(U, "Rewrite this so it does not sound passive aggressive: As I mentioned before, the mocks are blocked."), (A, "Quick flag: the mocks are still blocked on the copy review. Could we get that done by Thursday?")]),
    ("JavaScript debounce", [(U, "Explain debounce vs throttle for a search input."), (A, "Debounce waits until typing stops; throttle limits calls to one per interval. Use debounce for search suggestions.")]),
    ("Excel date formula", [(U, "How do I calculate the number of business days between two dates?"), (A, "Use NETWORKDAYS(start, end, holidays). In Sheets it is the same function name.")]),
    ("Kitchen measurement fractions", [(U, "How many tablespoons are in 3/8 cup?"), (A, "Six tablespoons.")]),
    ("Airbnb vs hotel for team offsite", [(U, "We have 9 people for a 3 night offsite. Airbnb house or hotel?"), (A, "A house is cheaper and better for working sessions; a hotel has fewer logistics. For nine people I would pick a large house with a big table.")]),
    ("Dark mode design tokens", [(U, "How should I name semantic color tokens for light and dark themes?"), (A, "Use roles instead of values: surface-default, text-primary, border-subtle. Map each role to light and dark values.")]),
    ("Lorem ipsum alternatives", [(U, "Give me realistic placeholder copy for a plant delivery app onboarding screen."), (A, "Welcome. Tell us about your space, and we will match you with plants that thrive in your light.")]),
    ("Presentation outline for roadmap", [(U, "Outline a 10-slide quarterly roadmap presentation for execs."), (A, "Goals, recap, metrics, themes, roadmap, risks, dependencies, resourcing, asks, next steps.")]),
    ("Python script to rename files", [(U, "Write a Python script that renames all files in a folder to lowercase with underscores."), (A, "Use pathlib: loop through iterdir(), build a new name with lower() and replace(' ', '_'), then call rename().")]),
    ("Spanish translation for a sign", [(U, "Translate to Spanish: Please leave packages at the front door."), (A, "Por favor deje los paquetes en la puerta principal.")]),
    ("Standing desk height", [(U, "What is the ideal standing desk height for someone 5 foot 6?"), (A, "Elbows at about 90 degrees: roughly 40 to 41 inches for most people your height.")]),
    ("Carpool schedule for offsite", [(U, "Make a carpool plan for 11 people and 3 cars leaving at 8am."), (A, "Car A: 4 people, Car B: 4 people, Car C: 3 people, with pickup stops listed in order of distance.")]),
    ("Fix Wi-Fi dropping", [(U, "My Wi-Fi drops every evening around 8pm. Any ideas?"), (A, "Likely congestion on the 2.4GHz band. Try changing channels, moving to 5GHz, or restarting the router on a schedule.")]),
    ("Google Calendar recurring event", [(U, "How do I set a recurring event for the first Monday of each month?"), (A, "Choose Custom recurrence, monthly, and select On the first Monday.")]),
    ("Hex codes for a brand palette", [(U, "Suggest a warm terracotta and sage palette with hex codes for a small bakery brand."), (A, "Terracotta #E07A5F, sage #81B29A, cream #F4F1DE, ink #3D405B, and butter #F2CC8F.")]),
    ("Notion project template", [(U, "Make me a Notion template for tracking design projects."), (A, "Database with Status, Owner, Due date, Links, and a board view grouped by Status.")]),
    ("APR vs APY", [(U, "What is the difference between APR and APY on a savings account?"), (A, "APY includes compounding, APR does not, so APY is the better number for comparing savings.")]),
]

# --------------------------------------------------------------------------
# ~15 personal conversations consistent with Rachel's persona (plus new details)
# --------------------------------------------------------------------------
PERSONAL = [
    ("Trail half marathon training plan", [
        (U, "I'm training for a trail half marathon in Marin in February. I'm on the trail before 7 most Saturdays with my dog Biscuit. Can you build a 10 week plan?"),
        (A, "Happy to. How many miles are you running now and how many days a week?"),
        (U, "About 20 miles a week over four runs. Saturday is my long run, I like going early because the trails are empty and I'm a morning person anyway."),
        (A, "Great base. Here is a 10 week plan with a long run building from 9 to 12 miles, one hill session, and a down week every fourth week.")]),
    ("Bio help for a dating profile", [
        (U, "I'm thinking of trying dating apps again. Can you help me write a bio? I'm a product designer in the Inner Sunset, I love trail running, dumplings, and live jazz."),
        (A, "Sure. What tone do you want, and what do you want a match to know about you?"),
        (U, "Playful. I'd like someone curious and outdoorsy who would happily split a plate of dumplings. I have a beagle mix named Biscuit and she's basically my co-pilot."),
        (A, "Draft: Product designer, trail runner, dumpling cartographer. Biscuit the beagle mix is my co-pilot. Looking for someone who will race me to the last xiao long bao.")]),
    ("Why I can't date smokers", [
        (U, "My friend set me up and I found out halfway through dinner that he smokes. I left early and felt kind of bad. But I really can't date someone who smokes."),
        (A, "That sounds like a firm boundary. Do you want help communicating it kindly next time?"),
        (U, "Yeah. My dad had COPD for years and I watched him struggle to breathe. Also my ex smoked and I could smell it on everything. It's just a hard no for me."),
        (A, "That makes sense. You could say early: I'm not a fit with smoking because of my family history. It is honest and kind.")]),
    ("First date ideas that aren't a bar", [
        (U, "I hate loud bars for first dates. I'd rather do something daytime. What are good first date ideas in SF?"),
        (A, "Coffee and a walk, a dumpling lunch, a trailhead meet-up, or a game cafe are all low pressure."),
        (U, "A dumpling lunch followed by a walk is exactly my vibe. And I'm free Saturday evenings or Sunday late morning usually."),
        (A, "Then a Sunday late morning dumpling lunch with a walk to Golden Gate Park would be perfect.")]),
    ("Pottery class at Clayworks", [
        (U, "I signed up for a beginner pottery class on Wednesday nights at a studio in Dogpatch! I'm obsessed with how relaxing the wheel is even though my bowls look like hats."),
        (A, "That is wonderful. Want tips for centering clay?"),
        (U, "Yes please. I'd love to find someone who would do a pottery class together honestly. It's one of my favorite things right now."),
        (A, "Centering: brace your elbows against your hips, use steady pressure, and keep your wheel speed fast at the start.")]),
    ("Wingspan strategy", [
        (U, "I want to get better at Wingspan. Any strategies? I play with friends every other Sunday."),
        (A, "Focus on engine building early with bird powers that chain, and plan egg placement for end-of-round goals."),
        (U, "Love that. I'm kind of a board game person in general, I'd happily date someone who owns Catan and Ticket to Ride."),
        (A, "Then a game night would be a great second date idea.")]),
    ("Sichuan dumplings from scratch", [
        (U, "I want to make Sichuan-style wontons in chili oil from scratch. I will cross the city for a good soup dumpling but I want to learn to make my own."),
        (A, "Start with a pork filling with ginger and white pepper, wrap them in thin skins, and make a chili oil with Sichuan peppercorn."),
        (U, "Perfect. I'd love to cook this with a partner someday. My idea of a great date is a kitchen and a playlist.")  ,
        (A, "Then keep the playlist jazzy and the chili oil on the side.")]),
    ("Jazz night in the Fillmore", [
        (U, "I want to find live jazz on a weeknight in the Fillmore this week. I love it. It is my favorite kind of date but I never find anyone to go with."),
        (A, "Try a small listening room with a late set on Wednesday or Thursday."),
        (U, "Thursday is Thanksgiving so I'll aim for Wednesday. I'm usually in bed by ten though, so an early set please."),
        (A, "Look for the 7pm set. Here are some questions to ask when booking.")]),
    ("Do I want kids?", [
        (U, "I honestly don't know if I want kids. I turn 30 next year and everyone keeps asking me. I told my mom I was unsure and she got quiet."),
        (A, "It is okay to be unsure. What feels clearer, a life with or without kids?"),
        (U, "Mostly I'm just not sure. I'd rather meet the right person and decide together. I don't want to date someone who is dead set either way."),
        (A, "That is a reasonable stance. You can say it plainly on a first date.")]),
    ("Sister's wedding speech", [
        (U, "I'm giving a toast at my sister's wedding in June. She's my best friend and we grew up trail running with our dad before he got sick."),
        (A, "I'm sorry about your dad. Do you want the toast to include him?"),
        (U, "Yes, a small mention. And some jokes about her terrible puns, which I clearly inherited."),
        (A, "Here is a draft: Anna taught me that the best views are on the steepest trails.")]),
    ("Dog sitting for Biscuit", [
        (U, "Can you help me write a post for a neighborhood group asking for a dog sitter? Biscuit is a beagle mix, friendly, loves hikes, hates the vacuum."),
        (A, "Draft: Looking for a kind dog sitter for a sweet beagle mix who loves hikes. Two weekends in March."),
        (U, "Add that I prefer someone who runs. She needs a lot of exercise."),
        (A, "Done. I added a line about daily walks and trail runs.")]),
    ("Texting rhythm with a new match", [
        (U, "I've been texting a guy and he replies at 1am. I'm asleep by ten! Is that a sign we aren't compatible?"),
        (A, "Not necessarily, but schedule mismatch matters. What does your ideal rhythm look like?"),
        (U, "I like early mornings and early dinners. I'm an early bird and I'd rather meet in person during the day than text all night."),
        (A, "Then propose a Sunday morning plan and see how he responds.")]),
    ("Therapy homework on boundaries", [
        (U, "My therapist wants me to practice stating needs earlier in dating. Mine are: no smoking, honesty, and someone who doesn't need to drink every weekend."),
        (A, "Those are clear. Let's practice a script."),
        (U, "I have a glass of wine or a beer when I'm out, maybe twice a week, so I'm not anti-drinking. I just don't love heavy partiers."),
        (A, "Script: I enjoy a drink socially, but I prefer plans that don't revolve around it.")]),
    ("Weekend plan: Muir Woods vs Mt Sutro", [
        (U, "Plan a Saturday: sunrise trail run, then brunch, then something chill. Biscuit comes along, so dog-friendly spots only."),
        (A, "Mount Sutro at sunrise, then a dog-friendly patio brunch in the Inner Sunset, then a browse in a bookstore."),
        (U, "Love it. Add dumplings for dinner. I'm basically a dumpling person in human form."),
        (A, "Added. A Richmond dumpling spot would make the loop complete.")]),
    ("Ex stuff and what I want now", [
        (U, "I got out of a three year relationship last spring. He smoked and was very indoorsy. I want someone who gets outside with me and is kind."),
        (A, "What did you learn about what you need?"),
        (U, "That I need someone curious and communicative. I'm ready to date again but I want to be intentional, I want a real partner not just a Friday night."),
        (A, "That is a great clarity to bring into dating.")]),
]

# 8 Claude conversations (mix of relevant and irrelevant)
CLAUDE = [
    ("Naming a design system", [(U, "Help me name an internal design system. We build tools for home renovation teams."), (A, "Some ideas: Framework, Plumb, Joist, Level, Mortar. Plumb is short and memorable.")]),
    ("Dating after a breakup", [(U, "I'm ready to date again but nervous. I want someone curious and outdoorsy who would happily split a plate of dumplings and doesn't smoke."), (A, "That is a clear picture. What does a good first date feel like for you?"), (U, "Daytime, low pressure, with a walk. And my dog Biscuit can come along if it's outdoors.")]),
    ("Figma plugin idea", [(U, "I'm brainstorming a Figma plugin that checks spacing consistency. Thoughts?"), (A, "Useful. Start with a lint that flags off-grid spacing and offers a one-click snap.")]),
    ("Trail running shoes", [(U, "Compare trail shoes for muddy Marin trails, I run about 20 miles a week."), (A, "Look for aggressive lugs, a rock plate, and a snug heel. Try a few on at a local running store.")]),
    ("Weekend board game picks", [(U, "Recommend three board games for a group that loves Wingspan and Catan."), (A, "Try Everdell, Terraforming Mars, and Cascadia.")]),
    ("Pottery glaze questions", [(U, "I'm taking a beginner pottery class. What's the difference between underglaze and glaze?"), (A, "Underglaze is for color and decoration under a clear glaze, while glaze creates the final glassy surface.")]),
    ("Budget for a bay area move", [(U, "Estimate monthly costs if I move from the Inner Sunset to a one-bedroom in the Richmond."), (A, "Rent is similar. Factor in moving costs, deposits, and utilities of about 150 to 200 per month.")]),
    ("Talking about kids on a first date", [(U, "How do I bring up kids on a first date when I honestly don't know what I want?"), (A, "Be honest: I'm open but unsure, and I would like to explore it with the right person."), (U, "That feels right. I don't want to pretend to be certain.")]),
]


def ts(i, base=1_770_000_000.0, step=86_400 * 3.1):
    return base + i * step


def chatgpt_conv(idx, title, msgs, create):
    mapping = {}
    root = f"root-{idx:03d}"
    mapping[root] = {"id": root, "message": None, "parent": None, "children": []}
    parent = root
    t = create
    for k, (role, text) in enumerate(msgs):
        nid = f"{idx:03d}-{k:02d}-{uuid.uuid5(uuid.NAMESPACE_URL, f'{title}{k}').hex[:8]}"
        t += 20 + 7 * k
        mapping[nid] = {
            "id": nid,
            "message": {"id": nid, "author": {"role": role}, "create_time": t,
                        "content": {"content_type": "text", "parts": [text]}},
            "parent": parent, "children": [],
        }
        mapping[parent]["children"].append(nid)
        parent = nid
    return {"title": title, "create_time": create, "update_time": t, "mapping": mapping, "current_node": parent}


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z")


def claude_conv(idx, title, msgs, create):
    chat, t = [], create
    for k, (role, text) in enumerate(msgs):
        t += 15 + 5 * k
        chat.append({"uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"claude-{idx}-{k}")),
                     "sender": "human" if role == U else "assistant", "text": text, "created_at": iso(t)})
    return {"uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"claude-conv-{idx}")), "name": title,
            "created_at": iso(create), "updated_at": iso(t), "chat_messages": chat}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # interleave personal conversations among the irrelevant ones, deterministically
    items = [(t, m, False) for t, m in IRRELEVANT]
    step = len(items) // len(PERSONAL) or 1
    for j, (t, m) in enumerate(PERSONAL):
        items.insert(min(len(items), 2 + j * (step + 1)), (t, m, True))
    convs = [chatgpt_conv(i, t, m, ts(i)) for i, (t, m, _) in enumerate(items)]
    (OUT / "rachel_chatgpt_conversations.json").write_text(json.dumps(convs, indent=2, ensure_ascii=False) + "\n")
    claude = [claude_conv(i, t, m, ts(i, base=1_772_000_000.0, step=86_400 * 9)) for i, (t, m) in enumerate(CLAUDE)]
    (OUT / "rachel_claude_conversations.json").write_text(json.dumps(claude, indent=2, ensure_ascii=False) + "\n")
    print(f"chatgpt: {len(convs)} conversations ({len(PERSONAL)} personal), claude: {len(claude)}")


if __name__ == "__main__":
    main()
