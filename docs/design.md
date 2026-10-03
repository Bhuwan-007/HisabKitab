Palette (no orange, navy, purple or green)
Role	Name	Hex
Desk background	Kora safed	
#FCFAF5
Page paper	Purana panna	
#F2E6CC
Stains, borders	Chai stain	
#D8BC8E
Corner spots	Dark sepia	
#5A3A24
Text, ink	Kaali syahi	
#231710
Muted text	Pencil grey	
#6B5F55
At risk	Sindoor lal	
#A3271F
Duplicates, ribbon, cover	Bahi maroon	
#6B1F2A
Needs a fix (fills only)	Pital brass	
#B28A33

Colour is for exceptions only. Accountants use red ink only for what needs attention, so we do the same:

Safe to claim is plain ink on paper with a ✓ stamp. No colour needed, since safe is the default state.
At risk is sindoor red.
Needs a fix is brass, used as a fill with dark text. Brass text on paper is too low-contrast.
Review is pencil grey.

Charts use hatching and cross-hatching in ink instead of coloured slices. It looks like an engraving and also works for colour-blind viewers.

Your ideas, refined
Floating symbols.
Use line-art rupee notes, coin stacks, an abacus, scales, a seal, an inkpot and a graph.
Keep it to 8 to 12 at 8 to 12 percent opacity, drifting slowly with CSS transforms only.
They pause when the tab is hidden and respect reduced-motion settings.
Loading with equations. Make the equation real. The loader solves the thing being loaded.
Dashboard: Safe + At risk + Needs fix = Total ITC.
UPI fee: ₹3,000 × 0.4% = ₹12.
180-day clock: 180 − 169 = 11 days.
The animation inks the digits in, draws small red carry marks, draws the total line, and finishes with the accountant's double underline.
For the "Run reconciliation" step (up to 10 s), show the real stages as ledger lines getting ticked.
Skip the loader if the data arrives in under 300 ms, to avoid flicker.
Book flip. Yes, for page changes between main sections only.
Use a CSS 3D rotate from the left edge, about 600 ms.
Don't flip when filtering or opening a drawer.
Book-style scroll. I'd skip scroll hijacking. It hurts usability, accessibility and performance, and it's slow when judges want to click around fast. Instead:
Show long lists as numbered ledger pages with turn arrows ("Page 2 of 7").
Add a bookmark ribbon on the period picker.
Make the floating symbols drift slightly as you scroll.
Aged paper.
Use a pre-rendered paper-grain tile, not a live filter, which is slow.
Add radial brown stains in corners only, with a curled corner on each card.
Cards sit at a slight random tilt (±0.3°), but tables stay straight.
Use crisp, brown-tinted shadows. No glow.
Additions that make it feel alive
Dashboard as an open book. A two-page spread with a centre gutter: the left page has the KPIs and liability, the right has the Top 5 actions.
Rubber stamps. When you mark an issue Resolved, a "VERIFIED" stamp slams onto the row with a small settle.
Sticky chits for deadlines. Torn yellowed slips pinned on cards: "2 din baaki".
Margin notes. AI explanations appear as pencil notes in the margin, in a handwriting font.
Corner peel. Hovering a queue row curls its corner to reveal an evidence preview.
Numbers writing themselves. On first load, figures count up like fresh ink.
Fonts. Playfair Display for titles, IBM Plex Sans with tabular numbers for tables, and Kalam for notes and stamps. Kalam also covers Hindi.
Fitting every kind of business

I'm reading "controlled by anyone" as "used by anyone", whether owner, accountant or auditor. Three cheap switches cover it:

Size mode: Dukaan (big plain cards, fewer columns), Vyapaar (default), Company (dense tables).
Language: English/हिंदी for key labels, if we centralise the copy.
Role default page: the owner lands on the Dashboard, the accountant on the Queue, and the CA or auditor on the Audit trail.

Real multi-company and role permissions are out of scope for the prototype, so I'd label them as a roadmap.

Time and scope

The design stage grows from about 1 hour to about 3 to 3.5 hours. It fits in the gap where the frontend session was waiting.

Tier 1 (about 2 h): palette, fonts, paper texture, ruled pages, corner stains, floating symbols, hatched charts, equation loader.
Tier 2 (about 1.5 h): book flip between sections, stamps, sticky chits, bookmark ribbon.
Tier 3 (optional): corner peel, Hindi toggle, size modes.

One thing to know: the deck you submitted uses orange and green. The app can use the new look, and we can restyle the final-round deck to match if you like.