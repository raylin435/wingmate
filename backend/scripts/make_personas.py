#!/usr/bin/env python3
"""Builds data/personas/<id>.json from a compact DSL (author-written, no LLM calls).

Answer lines may embed facts as [[code|value|quote text]]. The quote text stays in the
answer verbatim, so every fact quote is an exact substring of a user message.
Code letter: i interest, l lifestyle, v value, d dealbreaker, g logistics, s seeking.
Uppercase = private (only used for matching, never shown), lowercase = public.
"""
import json
import pathlib
import re

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "personas"

QUESTIONS = [
    ("Hey, I'm your Wingmate. Let's start easy: tell me about yourself and what a good week looks like.",
     "Hi! I'm here to help you meet people worth meeting. Who are you, and what does a good week look like?"),
    ("Nice. What do your weekends usually look like?",
     "Love that. How do you typically spend your weekends?"),
    ("Food is a big signal. What are you always down to eat?",
     "What's your food personality? What would you happily eat on repeat?"),
    ("What else do you do to move, make, or unwind?",
     "What else fills your free time?"),
    ("How's work, and does it leave you energy for dating?",
     "Tell me about work. Does it leave room for dating?"),
    ("What's your relationship with drinking?",
     "Drinking: where do you land?"),
    ("Any smoking, vaping or similar I should know about, for you or in a match?",
     "Smoking or vaping, anything I should know, either way?"),
    ("How do you feel about having kids someday?",
     "Kids: where are you on that?"),
    ("Pets? A dog, a cat, allergies, none?",
     "Any pets in your life?"),
    ("How important are religion or spirituality to you, and what values matter most?",
     "How big a role do religion or spirituality play, and what do you value most in people?"),
    ("Morning person or night owl?",
     "Early bird or night owl?"),
    ("What are you hoping to find in a partner?",
     "What kind of person are you hoping to meet?"),
    ("Any hard dealbreakers I should screen for?",
     "Anything that's a hard no for you?"),
    ("Last one: when are you free for a first date this coming week?",
     "Final question: which times next week could work for a first date?"),
]
CLOSING = ("Thanks, that's plenty to work with. I'll look for matches quietly and keep your private "
           "details private until you both opt in.")

FIELDS = {"i": "interest", "l": "lifestyle", "v": "value", "d": "dealbreaker", "g": "logistics", "s": "seeking"}
MARK = re.compile(r"\[\[([a-zA-Z])\|([^|\]]+)\|([^\]]+?)\]\]")
COLORS = ["#E07A5F", "#3D405B", "#81B29A", "#F2CC8F", "#6D597A", "#B56576", "#355070", "#EAAC8B",
          "#2A9D8F", "#E9C46A", "#F4A261", "#264653", "#9A8C98", "#4A6FA5", "#C97C5D"]

SRC = r"""
maya|Maya|Trail Runner 27|29|woman|man|27|36|Inner Sunset|Sunrise runs, dumpling crawls, bad puns.
attrs: smokes=F kids=unsure drinks=socially pets=has_dog rel=F early=T
db: smokes=true:smoking
int: trail running; dumplings; board games; live jazz
slots: 21T18:00 22T11:00 24T19:00 25T18:30
I'm a product designer who lives for the weekend. A good week has two trail runs, one night out with friends, and nothing on my calendar Sunday evening.
Saturdays I'm [[i|Runs trails at sunrise|on the trail before 7 most Saturdays]] with my dog Biscuit, then a slow brunch. Sundays are board games or a jazz set somewhere in the Fillmore.
Dumplings, always. [[i|Dumpling obsessive|I will cross the city for a good soup dumpling]] and I'm slowly working through every xiao long bao spot in the Richmond.
Besides running I love board games, Wingspan especially, and live jazz on a weeknight when I can swing it.
Work is busy but reasonable, around 45 hours. I have energy for dating if the plans are low-key.
[[L|Drinks socially|I have a glass of wine or a beer when I'm out, maybe twice a week]], never more than a couple.
Smoking is the one thing I can't do. [[D|Smoking is a dealbreaker|I really can't date someone who smokes]], my dad had COPD for years. [[L|Does not smoke|I don't smoke or vape myself]].
[[V|Unsure about kids|I honestly don't know if I want kids]], ask me again in a year. I'm open if it's the right person.
I have a dog, Biscuit, a beagle mix who comes on every run. Dog people get bonus points.
[[v|Religion not important|Religion isn't important to me]], but I care a lot about kindness and showing up for people.
[[g|Early bird|I'm up at 5:45 every day]] and fading by ten. Night owls, I'll be the one yawning at your show.
[[s|Wants curious, outdoorsy partner|I want someone curious and outdoorsy who would happily split a plate of dumplings]] and doesn't take themselves too seriously.
Smoking, like I said. Otherwise I'm flexible, I just want someone kind.
[[g|Free Saturday evening, Sunday morning, Tuesday evening|Saturday evening around six works, Sunday late morning is great]], and Tuesday after seven. Thanksgiving week gets hectic.

jordan|Jordan|Late-Night Cartographer|31|man|woman|26|35|Hayes Valley|Sound engineer, trail runner, dumpling scholar.
attrs: smokes=T kids=unsure drinks=socially pets=none rel=F early=T
db: -
int: trail running; dumplings; live jazz; board games
slots: 22T11:00 23T19:00 25T18:30
I'm a sound engineer and a bit of a night-time wanderer. A perfect week is a trail run, a good jazz set, and dumplings with friends.
I'm [[i|Runs trails on weekends|out on the Marin Headlands trails most Saturday mornings]], then I'm hunting for the best dumplings in the city.
[[i|Dumpling devotee|Soup dumplings are my love language]]. Also a hole-in-the-wall noodle guy. I'll cook for you if you let me.
Live jazz, board games with my roommates, and long runs. I play upright bass, badly.
I freelance so my hours bend. I actually have time and energy for dating, which is rare.
[[L|Drinks socially|I'll have a whiskey or two when there's music, but never to excess]].
[[L|Smokes occasionally|I still smoke a few cigarettes when I'm out with friends]], mostly at shows. I'm trying to cut down but I'm not there yet.
[[V|Unsure about kids|I could see kids in the future but I'm in no rush]].
No pets right now because my landlord is strict, but I'm a dog person all the way.
[[v|Religion not important|Religion isn't a big thing for me]]. Honesty, loyalty and showing up matter more.
I'm up early for runs, so [[g|Early riser|I'm a morning person even after late shows]]. Weird combo, I know.
[[s|Wants adventurous, kind partner|I want someone adventurous and kind who is up for a spontaneous trail and a late dumpling dinner]].
[[D|Dislikes flakiness|Flakiness is my pet peeve]]. I'm pretty easy otherwise.
[[g|Free Sunday morning, Monday and Wednesday evening|Sunday late morning, Monday evening and Wednesday evening all work for me]].

theo|Theo|Fog Chaser 30|30|man|woman|26|34|Outer Richmond|Science teacher, drummer, will race you to the dim sum.
attrs: smokes=F kids=yes drinks=socially pets=none rel=F early=T
db: smokes=true:smoking
int: trail running; dumplings; board games; live jazz; bouldering
slots: 22T11:00 24T19:00 25T12:00 27T18:00
I teach high school science and spend every free hour outside. A good week has a couple of runs, a dumpling night, and a board game with friends.
[[i|Trail runs and bouldering|I run trails on Saturday mornings and boulder on Sundays]]. Then dumplings, because I have a problem.
[[i|Dumplings and dim sum|I'll happily eat dumplings three times a week]]. Dim sum in the Richmond is basically my church.
Live jazz is my guilty pleasure, I drum in a terrible garage band, and I'll play any board game with a wooden meeple.
Teaching is draining on weekdays but I save energy for evenings. I'm very much up for dates.
[[L|Drinks socially|I'll have a beer or two with friends, nothing crazy]].
[[L|Does not smoke|I've never smoked and I don't vape]]. It's just never been my thing.
[[V|Open to kids|I'd like kids one day but I'm in no rush]].
No pet yet, but I'm planning to adopt a dog next spring. I adore beagles.
[[v|Religion not important|Religion isn't important to me]], but I try to be thoughtful and kind, especially with my students.
[[g|Early bird|I'm a morning person, up at six]] and ready to go.
[[s|Wants curious, outdoorsy partner|I want someone curious and outdoorsy who likes dumplings and dancing around the kitchen]].
[[D|Dislikes unkindness|I can't stand people who are unkind to waiters or animals]]. That's about it.
[[g|Free Sunday morning and Tuesday evening|Sunday late morning and Tuesday at seven both work]]. Wednesday lunch is open too.

ben|Ben|Meeple & Matcha|32|man|woman|27|35|Mission|Data analyst with a shelf of board games and strong latte opinions.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=F
db: wants_kids=yes:wanting kids
int: board games; comedy; dumplings; coffee; pickleball
slots: 21T19:00 25T18:30 27T19:30
I'm a data analyst who collects board games the way other people collect shoes. A good week is a game night, a standup show, and a very long coffee.
[[i|Hosts board game nights|I host board game night every Saturday]], usually a heavy euro, and Sundays I sleep in and wander the Mission for coffee.
[[i|Dumplings and coffee|I'll go for dumplings any time and I'm a latte art snob]]. Dessert first, always.
Standup comedy, pickleball badly, and baking sourdough. I try to catch a show every week.
I work hybrid so I have plenty of energy. Dating is a priority this year.
[[L|Drinks socially|I'll have a cocktail with friends once or twice a week]].
[[L|Does not smoke|I don't smoke or vape]]. Never have.
[[V|Does not want kids|I don't want kids, I've known that since my twenties]]. I'm happy being the fun uncle.
I have a cat named Pixel. Not a dog person, but dogs are fine in small doses.
[[v|Religion not important|Religion isn't important to me]]. Loyalty and a sense of humor matter.
[[g|Night owl|I'm a total night owl, my best thinking happens after ten]].
[[s|Wants funny, playful partner|I want someone funny and playful who will take game night seriously]].
[[D|Dealbreaker: wants kids|If someone really wants kids that's a dealbreaker for me]], just because I'm sure about my answer.
[[g|Free Saturday evening, Wednesday evening, Friday evening|Saturday after seven, Wednesday evening or Friday after six]] work best.

marcus|Marcus|Sunday Pitmaster|34|man|woman|28|37|Bernal Heights|ER nurse, cookout captain, choir-loft alumnus.
attrs: smokes=F kids=yes drinks=socially pets=none rel=T early=T
db: religion_important=false:not religious; wants_kids=no:not wanting kids
int: bbq; soccer; hiking; soul records; church
slots: 23T18:30 27T18:00 28T12:00
I'm an ER nurse and a deacon's kid. A good week is long shifts, a big cookout, and a hike to reset.
[[i|BBQ and cookouts|I grill ribs in my backyard most Saturdays]], and Sundays I'm at church followed by pickup soccer.
[[i|Southern comfort food|Mac and cheese, ribs, peach cobbler, I'll eat all of it]]. I make a mean gumbo.
Pickup soccer, hiking Mount Sutro, and digging through old soul records.
Twelve-hour nursing shifts three days a week, so my weeks are lumpy but my days off are all yours.
[[L|Drinks socially|I'll have a glass of wine at a wedding and that's about it]].
[[L|Does not smoke|I don't smoke, my mom raised me better]].
[[V|Wants kids|I definitely want kids, two or three]]. That's a big part of my plan.
No pets with my shift schedule, but I grew up with a golden retriever.
[[v|Faith is important|My faith is really important to me]], and I'd want a partner who respects that or shares it.
[[g|Early bird|I'm up at five to hit the gym before shifts]].
[[s|Wants partner with shared family goals|I want a partner who wants a family and a home full of laughter]].
[[D|Needs faith-friendly, kid-friendly partner|I need someone who is not against faith, and who is open to kids]].
[[g|Free Monday and Friday evenings|I'm off Monday and Friday evenings]]. Saturday daytime sometimes too.

diego|Diego|Salsa Sunday|28|man|woman|25|34|Mission|Bar manager by night, hiker by day, loud laugher always.
attrs: smokes=F kids=yes drinks=often pets=has_dog rel=F early=F
db: smokes=true:smoking
int: salsa dancing; hiking; tacos; live music
slots: 22T14:00 23T18:00 24T18:00
I'm a bar manager, so I live by the clock when everyone else is off. A good week has a salsa class, tacos, and a day by the ocean.
[[i|Salsa dancing and hiking|I go salsa dancing Saturday night and hike Lands End on Sunday]] to recover.
[[i|Tacos and mariscos|Al pastor tacos from a truck at 1am are my happy place]]. I also make my abuela's pozole.
Salsa classes, pickup volleyball, live Latin music, and the occasional jazz night.
Bar hours are late, but I have Mondays and Tuesdays off.
[[L|Drinks often|I work in bars so I drink more than most, a few nights a week]].
[[L|Does not smoke|I quit cigarettes two years ago and I don't smoke]].
[[V|Wants kids|I want kids eventually, I'm close to my big family]].
I have a rescue dog, Chispa, who hates salsa music.
[[v|Religion not important|Religion isn't important to me]], but I love family traditions.
[[g|Night owl|I'm a night owl by profession]] and I sleep in until ten.
[[s|Wants warm, playful partner|I want someone warm, playful and not afraid to dance badly]].
[[D|Dealbreaker: smoking|I can't date a smoker]]. I quit, so I'm sensitive to it.
[[g|Free Sunday afternoon, Monday and Tuesday evenings|Sunday afternoon, Monday and Tuesday evenings are free]].

kenji|Kenji|Ramen Cartographer|29|man|woman|25|34|Inner Richmond|UX researcher mapping every noodle shop in the city.
attrs: smokes=F kids=unsure drinks=socially pets=has_dog rel=F early=T
db: smokes=true:smoking
int: mountain biking; climbing; ramen; dumplings; film photography
slots: 22T11:00 25T19:00 27T18:30
I'm a UX researcher who plans weekends around ramen maps. A good week includes a climb, a long bike ride, and a new noodle spot.
[[i|Mountain biking and climbing|I'm on my mountain bike or at the climbing gym every weekend]], then ramen.
[[i|Ramen and dumplings|I keep a spreadsheet of every ramen and dumpling place I've tried]]. Eighty-four and counting.
Film photography, mountain biking, and quiet live jazz at small clubs.
Hybrid work and lots of energy after hours. I'd love midweek dates.
[[L|Drinks socially|I drink sake or a beer with food, maybe once a week]].
[[L|Does not smoke|I don't smoke or vape]].
[[V|Unsure about kids|I'm genuinely unsure about kids]], I'd want to talk about it.
I have a shiba named Mochi, a cranky little guy.
[[v|Religion not important|Religion isn't important to me]], though I like the New Year traditions.
[[g|Early bird|I'm usually up at six for the first ride]].
[[s|Wants adventurous foodie|I want someone adventurous and curious about food who doesn't mind a long bike ride]].
[[D|Smoke bothers him|Cigarette smoke is a dealbreaker, my asthma flares up]].
[[g|Free Sunday morning and Wednesday evening|Sunday late morning and Wednesday evening work for me]].

owen|Owen|Weekend Sailor|36|man|woman|30|38|Potrero Hill|Structural engineer who sails when the wind cooperates.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=T
db: wants_kids=yes:wanting kids
int: sailing; woodworking; craft beer; seafood
slots: 21T18:30 27T18:00 28T11:00
I'm a structural engineer who sails when the wind cooperates. A good week is work, a long sail, and a quiet dinner.
[[i|Sailing on the Bay|I'm on a sailboat on the Bay every Saturday I can]], then woodshop on Sunday.
[[i|Craft beer and seafood|Fresh Dungeness crab and a crisp lager are my favorite meal]].
Woodworking, sailing, and craft beer tastings. I build furniture on the side.
Steady nine to five, no weekend work. I have time for a relationship.
[[L|Drinks socially|I enjoy craft beer, two or three a week, never sloppy]].
[[L|Does not smoke|I've never smoked]].
[[V|Does not want kids|I don't want kids, I've settled that]].
I have a cat named Sawdust who supervises my woodworking.
[[v|Religion not important|Religion isn't important to me]], I'm more about integrity.
[[g|Early bird|I wake at dawn to check the wind]].
[[s|Wants calm, independent partner|I want someone calm and independent who loves the water]].
[[D|Dealbreaker: wants kids|Wanting kids is a dealbreaker for me]], I'd rather be clear up front.
[[g|Free Saturday evening and Friday evening|Saturday evening or Friday after six work]].

luis|Luis|Chalk & Tacos|27|man|woman|25|32|Dogpatch|Junior game designer, boulderer, taco truck completionist.
attrs: smokes=F kids=yes drinks=often pets=none rel=F early=F
db: smokes=true:smoking
int: climbing; video games; tacos; board games
slots: 21T19:00 23T19:00 24T20:00
I'm a junior game designer. A good week has two climbing sessions, one big taco night and a lot of co-op games.
[[i|Climbing and video games|I climb Saturday mornings and play co-op games on Sundays]].
[[i|Tacos and Korean BBQ|I'll eat tacos every day if no one stops me]].
Bouldering, co-op board games, and a little live music.
Startup hours are fine, I leave by six most days.
[[L|Drinks often|I go out for drinks a few nights a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Wants kids|I want kids someday, probably in my thirties]].
No pet, but I love cats.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl for sure]].
[[s|Wants fun, easygoing partner|I want someone fun and easygoing who'll try a new taco truck with me]].
[[D|Dealbreaker: smoking|I can't deal with cigarette smoke]].
[[g|Free Saturday evening, Monday evening, Tuesday night|Saturday evening, Monday after seven and Tuesday night work]].

wes|Wes|Sourdough Wes|33|man|woman,nonbinary|28|36|North Panhandle|Line chef with a sourdough starter older than most of my relationships.
attrs: smokes=F kids=unsure drinks=socially pets=has_cat rel=F early=F
db: smokes=true:smoking
int: cooking; hiking; trail running; vinyl records
slots: 23T18:30 24T18:30 27T19:00
I'm a chef at a small restaurant and I'm tired of dating people who don't understand restaurant hours. A good week ends with a long hike on my day off.
[[i|Hiking and cooking|I hike on Mondays, my day off, and cook for friends on Sundays]].
[[i|Fresh pasta and ferments|I'm into fresh pasta, kimchi and anything fermented]].
Trail running, sourdough, and a very large record collection.
Kitchen hours are long. I'm off Mondays and Tuesdays so I'd like Monday dates.
[[L|Drinks socially|I'll have wine with dinner a few times a week]].
[[L|Quit smoking|I quit smoking last year and I'm not going back]].
[[V|Unsure about kids|I'm undecided about kids]].
I have a cat named Basil.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|Kitchen life made me a night owl]].
[[s|Wants someone who loves food|I want someone who loves food and isn't scared of hard work]].
[[D|Dealbreaker: smoking|I really don't want to date a smoker]], since I just quit.
[[g|Free Monday and Tuesday evenings|Monday and Tuesday evenings are open]].

priya|Priya|Standup Spectator|31|woman|man|29|38|Cole Valley|Pediatric dentist with unreasonably dry humor.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=F
db: smokes=true:smoking
int: comedy; board games; south indian food; pickleball
slots: 25T18:30 27T19:30 28T13:00
I'm a pediatric dentist, which means my humor is unreasonably dry. A good week has a comedy show, a board game night, and masala dosa.
[[i|Comedy shows and board games|I'm at a comedy show most Friday nights and board games on Sundays]].
[[i|South Indian food|I'd drive across the Bay for a good masala dosa]].
Pickleball, true crime podcasts, and trying to master my mom's sambar.
Long clinic days but I leave on time. Dating is a priority.
[[L|Drinks socially|I drink socially, a cocktail or two with friends]].
[[L|Does not smoke|I don't smoke or vape]].
[[V|Unsure about kids|I'm on the fence about kids]], still figuring it out.
No pets, but I'd love a cat.
[[v|Religion not important|Religion isn't important to me]], though I like Diwali with family.
[[g|Night owl|I'm a night owl and my best jokes happen after ten]].
[[s|Wants funny, kind partner|I want someone funny, kind and secure enough to laugh at themselves]].
[[D|Dealbreaker: smoking|Smoking is a hard no for me]].
[[g|Free Wednesday evening and Friday evening|Wednesday evening or Friday after seven work]].

chloe|Chloe|Thrift Disco|27|woman|man|26|34|Lower Haight|Social media manager, vintage hunter, dance floor regular.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=F
db: wants_kids=yes:wanting kids
int: dancing; thrifting; vinyl; cocktails
slots: 21T20:00 27T19:00 28T14:00
I'm a social media manager for a small brand. A good week has a dance class, a thrift run, and a big night out.
[[i|Dance nights and thrifting|I thrift on Saturdays and go dancing Saturday night]].
[[i|Brunch and cocktails|I could live on avocado toast and a good mimosa]].
Dance cardio, record shopping, and the occasional house party.
Busy but flexible, I work remotely.
[[L|Drinks socially|I love a cocktail, maybe a few a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids, ever]].
I have a tabby cat named Disco.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm definitely a night owl]].
[[s|Wants fun, stylish partner|I want someone fun with good taste who'll dance with me]].
[[D|Dealbreaker: wants kids|I can't date someone who wants kids]].
[[g|Free Saturday night and Friday evening|Friday evening and Saturday after eight work]].

nadia|Nadia|Choir & Cardamom|33|woman|man|30|38|Noe Valley|School counselor, alto, cardamom bun enthusiast.
attrs: smokes=F kids=yes drinks=rarely pets=none rel=T early=T
db: wants_kids=no:not wanting kids
int: baking; choir; hiking; volunteering
slots: 23T18:30 25T18:30 28T15:00
I'm a middle school counselor and an alto in my church choir. A good week has choir, a Marin hike, and Sunday dinner with family.
[[i|Choir and hiking|I sing in choir on Sundays and hike Muir Woods on Saturdays]].
[[i|Baking|I bake cardamom buns every weekend]].
Baking, hiking, and volunteering with the youth program.
School keeps me busy but I'm free most evenings.
[[L|Rarely drinks|I rarely drink, maybe a glass of wine at a wedding]].
[[L|Does not smoke|I don't smoke or vape]].
[[V|Wants kids|I want kids, two at least, and I'd like to start in the next few years]].
No pets, but I'd welcome a dog.
[[v|Faith is important|My faith is a big part of my life]], and I want to share it.
[[g|Early bird|I'm up at six for a prayer and a walk]].
[[s|Wants partner who wants family|I want a partner who wants a family and who's grounded and kind]].
[[D|Dealbreaker: no kids|If someone doesn't want kids I can't continue]].
[[g|Free Monday and Wednesday evenings|Monday and Wednesday evenings work]].

sofia|Sofia|Street Photo|28|woman|man,woman|26|35|Mission|Film photographer with a marketing day job.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=F
db: smokes=true:smoking
int: photography; murals; gallery openings; mezcal
slots: 21T19:00 22T15:00 27T19:00
I'm a photographer with a day job in marketing. A good week has a street photography walk, a gallery night, and a long dinner.
[[i|Street photography|I walk around the Mission with my film camera every Saturday]].
[[i|Mexican and Peruvian food|I'm always down for ceviche or a really good burrito]].
Film photography, gallery openings, and mural walks.
Marketing job, nine to six. Evenings are mine.
[[L|Drinks socially|I'll have a mezcal or a glass of wine with friends]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets, my apartment is tiny.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl]].
[[s|Open to men or women, wants creative partner|I'm open to men or women, I just want someone creative and curious]].
[[D|Dealbreaker: smoking|I can't date smokers]].
[[g|Free Friday evening and Sunday afternoon|Friday evening or Sunday afternoon work for me]].

hannah|Hannah|Pilates & Pinot|35|woman|man|31|40|Pacific Heights|Runs a design studio, plans trips like military campaigns.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=T
db: smokes=true:smoking
int: pilates; wine tasting; theater; travel
slots: 21T12:00 23T19:00 25T18:30 27T19:00
I run a small design consultancy and I'm finally making time for dating. A good week has pilates, a play, and dinner with someone interesting.
[[i|Pilates and theater|I do reformer pilates Saturday mornings and catch a play most Sunday afternoons]].
[[i|Wine and small plates|I love a long dinner of small plates and a bottle of Riesling]].
Travel planning, wine country day trips and the occasional ballet.
I own my schedule, which helps. I've got time for dinners midweek.
[[L|Drinks socially|I enjoy wine with dinner a few nights a week]].
[[L|Does not smoke|I don't smoke and never have]].
[[V|Unsure about kids|I'm open to kids but not set on it]].
No pets, I travel too much.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six for pilates before work]].
[[s|Wants established, curious partner|I want someone established, curious and ready to commit]].
[[D|Dealbreaker: smoking|Smoking is a dealbreaker for me]].
[[g|Free Saturday midday and Monday evening|Saturday midday or Monday evening work]].

tessa|Tessa|Salt & Matcha|26|woman|man|25|33|Outer Sunset|Vet tech who surfs at dawn and dreams of a camper van.
attrs: smokes=F kids=yes drinks=socially pets=has_dog rel=F early=T
db: smokes=true:smoking
int: surfing; matcha; camping; vintage shopping
slots: 21T18:00 22T09:00 24T18:30
I'm a veterinary tech and I surf before work. A good week has three dawn sessions, a camping trip planned, and one night out.
[[i|Surfing at dawn|I paddle out at Ocean Beach at six every weekend]] and then grab matcha.
[[i|Matcha and burritos|I'm a matcha person and a burrito snob]].
Camping, thrift shopping, and long beach walks with my dog.
Vet clinic shifts end at five. I have energy for dates.
[[L|Drinks socially|I'll have a beer at the beach bonfire, just casually]].
[[L|Does not smoke|I don't smoke or vape]], and I try to keep my lungs happy for surfing.
[[V|Wants kids|I want kids someday and I'm not shy about it]].
I have a dog named Kelp, a lab mix who sort of surfs.
[[v|Religion not important|Religion isn't important to me]], but I care about kindness to animals.
[[g|Early bird|I'm in bed by nine and up at five]].
[[s|Wants outdoorsy, kind partner|I want someone outdoorsy and kind who loves dogs]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Saturday evening and Sunday morning|Saturday evening and Sunday morning work]].

zoe|Zoe|Bay Kayaker|32|woman|man|30|38|Hayes Valley|Landscape architect who paddles the Bay and hates small talk.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=T
db: wants_kids=yes:wanting kids
int: kayaking; sourdough; running; craft beer
slots: 21T18:30 24T19:00 27T18:00
I'm a landscape architect. A good week has a Bay paddle, a loaf of sourdough, and an evening away from a screen.
[[i|Kayaking on the Bay|I kayak on the Bay most Saturdays when the wind is mild]].
[[i|Sourdough and craft beer|I bake sourdough every week and I'll trade a loaf for a good IPA]].
Running, kayaking, and gardening.
Steady hours, I'm free most evenings.
[[L|Drinks socially|I'll have a craft beer or two, usually on weekends]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids, and I've known that since I was a teenager]].
I have a cat named Rye.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm a morning person]].
[[s|Wants calm, outdoorsy partner|I want someone calm and outdoorsy who loves the water]].
[[D|Dealbreaker: wants kids|If someone wants kids it's a dealbreaker]].
[[g|Free Saturday evening, Tuesday and Friday evenings|Saturday evening, Tuesday evening or Friday after six work]].

lena|Lena|Chalk Hands|30|woman|woman,nonbinary|27|36|Outer Sunset|Climbing coach, ramen devotee, indie film nerd.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=T
db: smokes=true:smoking
int: climbing; ramen; indie films; hiking
slots: 21T18:00 24T19:00 26T11:00
I coach at a climbing gym and moonlight as a ramen critic. A good week has outdoor climbing, a new noodle shop, and an indie film.
[[i|Climbing outdoors|I climb at Mount Tam most Saturdays]], then a long soup.
[[i|Ramen obsessive|I rate every ramen shop I visit on a ten-point scale]].
Indie films, hiking, and thrifted sweaters.
Coaching ends by seven. I have energy for dates after.
[[L|Drinks socially|I'll have a beer or two, maybe weekly]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets, I'm allergic to cats.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six]].
[[s|Wants adventurous, thoughtful partner|I want someone adventurous and thoughtful who'll try a V4 with me]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Saturday evening and Tuesday evening|Saturday evening and Tuesday evening work]].

rosa|Rosa|Boulder Bunny|27|woman|woman|25|33|Mission|Pastry cook, bouldering newbie, dance floor loyalist.
attrs: smokes=F kids=unsure drinks=often pets=none rel=F early=F
db: -
int: bouldering; tacos; ramen; queer dance nights
slots: 21T18:00 24T19:00 25T20:00
I'm a pastry cook and I just got into bouldering. A good week has a climb, tacos, and a queer dance night.
[[i|Bouldering and dancing|I boulder on Saturdays and dance on Saturday night]].
[[i|Tacos and ramen|I'll eat tacos or ramen any day of the week]].
Baking, dance nights, and thrift stores.
Pastry hours start at four so I'm in bed early on work nights.
[[L|Drinks often|I like going out and I drink a few nights a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm undecided about kids]].
No pets yet.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl on days off]].
[[s|Wants playful, caring partner|I want someone playful and caring who is not afraid of the dance floor]].
[[D|No hard dealbreakers|I don't really have hard dealbreakers, just kindness]].
[[g|Free Saturday evening and Tuesday night|Saturday evening or Tuesday night work for me]].

imani|Imani|Garden Poet|33|woman|woman,nonbinary|29|38|Bayview|Community gardener and poet with a soul food problem.
attrs: smokes=F kids=yes drinks=socially pets=has_dog rel=T early=T
db: -
int: gardening; poetry; soul food; live jazz
slots: 22T13:00 25T18:30 27T18:30
I'm a librarian and a community gardener. A good week has a poetry night, garden work, and Sunday supper.
[[i|Gardening and poetry|I garden Saturday mornings and read poetry on Sundays]].
[[i|Soul food|I cook collards and cornbread for my whole block]].
Jazz at small rooms, poetry open mics, and volunteering.
Library hours are steady, I have evenings free.
[[L|Drinks socially|I'll have a glass of wine at dinner]].
[[L|Does not smoke|I don't smoke]].
[[V|Wants kids|I want kids, maybe through adoption]].
I have a dog named Maple.
[[v|Faith is important|My faith is important to me]], and community matters most.
[[g|Early bird|I'm up at six to garden]].
[[s|Wants grounded, loving partner|I want someone grounded and loving who cares about community]].
[[D|Dislikes disrespect|I can't stand disrespect]].
[[g|Free Sunday afternoon and Wednesday evening|Sunday afternoon or Wednesday evening work]].

june|June|Clay & Corgi|29|woman|woman|26|35|Richmond|Ceramicist with a corgi and a strong opinion on trail snacks.
attrs: smokes=F kids=unsure drinks=socially pets=has_dog rel=F early=T
db: smokes=true:smoking
int: ceramics; hiking; dogs; board games
slots: 22T10:00 24T19:00 25T18:30
I'm a ceramicist and part-time barista. A good week has studio time, a hike with my corgi, and board games.
[[i|Ceramics and hiking|I throw pottery on Saturdays and hike on Sundays]].
[[i|Dumplings and baked goods|I love dumplings and anything with butter]].
Board games, baking, and walks with Waffles.
Studio hours are flexible. I have energy for dates.
[[L|Drinks socially|I'll have a beer with friends]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm not sure about kids]].
I have a corgi named Waffles.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six]].
[[s|Wants creative, kind partner|I want someone creative and kind who loves dogs]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Sunday morning and Tuesday evening|Sunday morning and Tuesday evening work]].

andre|Andre|Vinyl & Veg|31|man|man|28|37|Duboce Triangle|Pastry-curious hiker with too many records.
attrs: smokes=F kids=yes drinks=socially pets=none rel=F early=T
db: -
int: cooking; hiking; vinyl records; farmers markets
slots: 22T11:00 24T19:00 27T18:00
I'm a product manager who cooks when stressed. A good week has a hike, a farmers market run, and a vinyl night.
[[i|Hiking and farmers markets|I hike on Saturdays and hit the farmers market on Sundays]].
[[i|Cooking from scratch|I cook a big dinner for friends most Sundays]].
Vinyl collecting, hiking, and cooking classes.
Steady hours. I have energy for dating.
[[L|Drinks socially|I'll have wine with dinner, a few nights a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Wants kids|I want kids, ideally through adoption]].
No pets right now.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six]].
[[s|Wants kind, curious partner|I want someone kind and curious who likes cooking with me]].
[[D|No hard dealbreakers|I don't have hard dealbreakers except cruelty]].
[[g|Free Sunday morning and Tuesday evening|Sunday morning or Tuesday evening work]].

ravi|Ravi|Trailhead Chef|30|man|man|27|36|Lower Nob Hill|Line cook with a backpack always packed.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=T
db: smokes=true:smoking
int: hiking; cooking; vinyl records; board games
slots: 22T11:00 24T19:00 28T10:00
I'm a sous chef who spends days off outside. A good week has a hike, a record store, and a long dinner.
[[i|Hiking and records|I hike on Sundays and dig through record stores on Saturdays]].
[[i|Indian and Italian food|I make my own pasta and my mother's dal]].
Hiking, cooking, board games, and records.
Kitchen hours but I'm off Sundays.
[[L|Drinks socially|I'll have a drink or two with friends]].
[[L|Does not smoke|I don't smoke or vape]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets yet.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six for hikes]].
[[s|Wants kind, adventurous partner|I want someone kind and adventurous who'll eat anything I cook]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Sunday morning and Tuesday evening|Sunday morning and Tuesday evening work]].

felix|Felix|Gym Rat Felix|28|man|man|26|34|SoMa|Fitness coach, football obsessive, secret poet.
attrs: smokes=F kids=no drinks=often pets=none rel=F early=T
db: -
int: lifting; football; podcasts; brunch
slots: 21T19:00 23T19:00 27T19:00
I'm a fitness coach. A good week has lifting, football, and brunch.
[[i|Lifting and football|I lift on Saturdays and watch football on Sundays]].
[[i|Brunch and burgers|I'll eat brunch every weekend]].
Podcasts, poetry, and trying new restaurants.
Coaching hours start at five.
[[L|Drinks often|I drink a few nights a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids]].
No pets.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at five]].
[[s|Wants fun, driven partner|I want someone fun and driven who likes the gym]].
[[D|No hard dealbreakers|I don't have any hard dealbreakers]].
[[g|Free Saturday evening and Monday evening|Saturday evening or Monday evening work]].

caleb|Caleb|Cat Dad Carpenter|35|man|man|30|40|Glen Park|Carpenter with two cats and a very patient sourdough.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=T
db: smokes=true:smoking
int: woodworking; wine; cats; hiking
slots: 22T11:00 25T18:30 27T18:30
I'm a carpenter who builds furniture. A good week has woodworking, a hike, and wine.
[[i|Woodworking and hiking|I build furniture on Saturdays and hike on Sundays]].
[[i|Wine and cheese|I love wine and cheese nights]].
Cats, hiking, and cooking.
Steady hours.
[[L|Drinks socially|I drink wine socially]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids]].
I have two cats.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at six]].
[[s|Wants warm, steady partner|I want someone warm and steady]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Sunday morning and Wednesday evening|Sunday morning or Wednesday evening work]].

miles|Miles|Night DJ|26|man|man,nonbinary|25|32|Western Addition|DJ and gallery assistant chasing the perfect bassline.
attrs: smokes=F kids=unsure drinks=often pets=none rel=F early=F
db: -
int: DJing; art shows; synths; dancing
slots: 21T20:00 24T20:00 27T20:00
I'm a DJ and gallery assistant. A good week has a set, an art show, and dancing.
[[i|DJing and dancing|I DJ on Saturday nights and dance on Fridays]].
[[i|Late-night eats|I love late-night ramen and dumplings]].
Synths, art shows, and thrifting.
Gallery hours are flexible.
[[L|Drinks often|I go out and drink a few nights a week]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl]].
[[s|Wants creative, fun partner|I want someone creative and fun who loves music]].
[[D|No hard dealbreakers|I don't have hard dealbreakers]].
[[g|Free Saturday night and Tuesday night|Saturday night or Tuesday night work]].

eli|Eli|Skatepark Eli|29|man|man,nonbinary|26|35|Excelsior|Bike mechanic and skater with a punk-show habit.
attrs: smokes=T kids=unsure drinks=socially pets=none rel=F early=F
db: -
int: skating; ramen; bike rides; punk shows
slots: 21T19:00 24T19:00 25T19:00
I'm a bike mechanic. A good week has skating, a punk show, and ramen.
[[i|Skating and punk shows|I skate on Saturdays and go to a punk show most Sundays]].
[[i|Ramen and burritos|I'll eat ramen and burritos all week]].
Bike rides, skating, and zines.
Shop hours are flexible.
[[L|Drinks socially|I'll have a beer at shows]].
[[L|Vapes sometimes|I vape sometimes, mostly when I'm skating with friends]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl]].
[[s|Wants easygoing, loud partner|I want someone easygoing who doesn't mind loud shows]].
[[D|No hard dealbreakers|I don't have hard dealbreakers]].
[[g|Free Saturday evening, Tuesday and Wednesday evening|Saturday evening, Tuesday evening or Wednesday evening work]].

ash|Ash|Zine Wanderer|28|nonbinary|man,woman,nonbinary|25|35|Mission|Zine maker, bouldering regular, bakery scout.
attrs: smokes=F kids=no drinks=socially pets=has_cat rel=F early=F
db: -
int: zine fairs; bouldering; bakeries; thrifting
slots: 21T18:00 22T11:00 24T19:00
I'm a graphic designer who makes zines. A good week has bouldering, a bakery crawl, and a zine fair.
[[i|Zines and bouldering|I make zines on Fridays and boulder on Saturdays]].
[[i|Bakeries and thrift stores|I plan weekends around bakeries and thrift stores]].
Zines, bouldering, and thrifting.
Design work is flexible.
[[L|Drinks socially|I'll have a drink with friends]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids]].
I have a cat named Pixel Dust.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl]].
[[s|Open to any gender; wants creative partner|I'm open to any gender, I want someone creative and kind]].
[[D|No hard dealbreakers|I don't have hard dealbreakers]].
[[g|Free Saturday evening and Sunday morning|Saturday evening or Sunday morning work]].

kit|Kit|Boulder Baker|31|nonbinary|woman,nonbinary|27|36|Bernal Heights|Baker who climbs, zines, and thrifts on weekends.
attrs: smokes=F kids=no drinks=socially pets=none rel=F early=T
db: smokes=true:smoking
int: bouldering; baking; zine fairs; thrifting
slots: 22T11:00 24T19:00 27T18:30
I'm a baker who climbs. A good week has bouldering, a zine fair, and a thrift run.
[[i|Bouldering and baking|I boulder on Saturdays and bake all day Sundays]].
[[i|Bakeries and ramen|I love bakeries and ramen]].
Zines, thrifting, and bouldering.
Baker hours start at four.
[[L|Drinks socially|I'll have a glass of wine]].
[[L|Does not smoke|I don't smoke]].
[[V|Does not want kids|I don't want kids]].
No pets.
[[v|Religion not important|Religion isn't important to me]].
[[g|Early bird|I'm up at four for work]].
[[s|Wants creative, adventurous partner|I want someone creative and adventurous]].
[[D|Dealbreaker: smoking|I can't date a smoker]].
[[g|Free Sunday morning and Tuesday evening|Sunday morning or Tuesday evening work]].

river|River|Synth & Thrift|27|nonbinary|man,nonbinary|25|33|Potrero Hill|Modular synth tinkerer with an eye for thrift finds.
attrs: smokes=F kids=unsure drinks=socially pets=none rel=F early=F
db: -
int: modular synths; thrifting; bike rides; ramen
slots: 21T19:00 24T19:30 27T19:00
I'm a sound designer. A good week has synths, thrifting, and ramen.
[[i|Synths and thrifting|I tinker with synths on Saturdays and thrift on Sundays]].
[[i|Ramen and dumplings|I love ramen and dumplings]].
Bike rides, synths, and thrifting.
Sound design hours are flexible.
[[L|Drinks socially|I'll have a drink with friends]].
[[L|Does not smoke|I don't smoke]].
[[V|Unsure about kids|I'm not sure about kids]].
No pets.
[[v|Religion not important|Religion isn't important to me]].
[[g|Night owl|I'm a night owl]].
[[s|Wants creative, kind partner|I want someone creative and kind]].
[[D|No hard dealbreakers|I don't have hard dealbreakers]].
[[g|Free Saturday evening and Tuesday evening|Saturday evening or Tuesday evening work]].
"""


def parse_attrs(line):
    kv = dict(p.split("=") for p in line.split(":", 1)[1].split())
    b = lambda v: v == "T"
    return {
        "smokes": b(kv["smokes"]), "wants_kids": kv["kids"], "drinks": kv["drinks"],
        "pets": kv["pets"], "religion_important": b(kv["rel"]), "early_bird": b(kv["early"]),
    }


def parse_db(line):
    raw = line.split(":", 1)[1].strip()
    if raw == "-":
        return []
    out = []
    for part in raw.split(";"):
        kv, label = part.strip().split(":", 1)
        attr, val = kv.split("=")
        val = True if val == "true" else False if val == "false" else val
        out.append({"attr": attr if attr != "kids" else "wants_kids", "equals": val, "label": label})
    return out


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    blocks = [b for b in SRC.strip().split("\n\n") if b.strip()]
    ids = []
    for idx, block in enumerate(blocks):
        lines = block.strip().split("\n")
        h = lines[0].split("|")
        pid, first, alias, age, gender, seek, mn, mx, hood, tagline = h
        attrs = parse_attrs(lines[1])
        dbs = parse_db(lines[2])
        interests = [s.strip() for s in lines[3].split(":", 1)[1].split(";")]
        # window is 2026-11-21..27; fold any later day back into Friday the 27th
        slots = []
        for t in lines[4].split(":", 1)[1].split():
            d, hm = t.split("T")
            s = "2026-11-%02dT%s" % (min(int(d), 27), hm)
            if s not in slots:
                slots.append(s)
        answers = lines[5:]
        assert len(answers) == 14, (pid, len(answers))
        facts = []

        def sub(m):
            c = m.group(1)
            facts.append({"field": FIELDS[c.lower()], "value": m.group(2), "quote": m.group(3),
                          "share": "private" if c.isupper() else "public"})
            return m.group(3)

        texts = [MARK.sub(sub, a) for a in answers]
        variant = idx % 2
        chat = []
        for (q0, q1), t in zip(QUESTIONS, texts):
            chat.append({"role": "assistant", "text": (q0, q1)[variant]})
            chat.append({"role": "user", "text": t})
        chat.append({"role": "assistant", "text": CLOSING})
        persona = {
            "id": pid, "first_name": first, "alias": alias, "age": int(age), "gender": gender,
            "seeking": {"genders": seek.split(","), "min_age": int(mn), "max_age": int(mx)},
            "neighborhood": hood, "tagline": tagline, "avatar_color": COLORS[idx % len(COLORS)],
            "attributes": attrs, "dealbreakers": dbs, "interests": interests,
            "free_slots": slots, "chat": chat, "facts": facts,
        }
        (OUT / f"{pid}.json").write_text(json.dumps(persona, indent=2, ensure_ascii=False) + "\n")
        ids.append(pid)
    print(f"wrote {len(ids)} personas to {OUT}")


if __name__ == "__main__":
    build()
