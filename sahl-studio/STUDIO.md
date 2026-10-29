# Sahl Studio

The toolkit the Sahl Digital «سهل» marketing employees use to make each week's posts.
It renders faceless Reels and still posts from the showcase sites, publishes the media on
GitHub Pages, and queues the posts for the auto-poster and the HQ board.

Everything here is data and code for Adham's own business. Nothing in it sends messages to anyone.

## Where things live

| Thing | Where |
|---|---|
| This toolkit | `sahl-studio/` in the repo `adhamAbuAllan/adhamabuallan.github.io` |
| Published media | `sahl/media/wNN/<code>.<ext>` in the same repo, served at `https://adhamabuallan.github.io/sahl/media/wNN/...` |
| Brand images | `sahl/brand/` (cover, profile, logo SVGs) |
| Auto-poster | Supabase project `iezglohziunneucnsngq` ("adham-billing", the same project as the WhatsApp bot), edge function `sahl-poster`, tables `sahl_posts` and `sahl_settings`, cron job `sahl-poster-hourly` (posts once a day at 20:00 Asia/Hebron) |
| HQ board | https://claude.ai/artifact/7PczNdLyr7Ldr8FV7DHp4U (database via the ArtifactData tool: collections `posts`, `leads`, `groups`, `todo`, doc `meta/numbers`) |
| WhatsApp chats | Supabase project `iezglohziunneucnsngq`, table `wa_messages` (role `user` = customer). Every post's WhatsApp link ends with its code, like `(P08)`, so chats can be counted per post |
| Marketing plan | Claude Docs doc `8d714db3-9999-4010-94f7-3ae94ea04b4a` (https://claude.ai/artifact/JU2QN3vGDSuUSx17cfHApZ) |
| Design system | https://claude.ai/artifact/9xznFf9hRraxjt8NWCt8kn |
| Facebook Page | https://www.facebook.com/profile.php?id=61595836807777 ("Sahl Digital سهل للمواقع والتطبيقات") |

## Setup in a fresh session

```bash
git clone https://github.com/adhamAbuAllan/adhamabuallan.github.io.git site
cd site/sahl-studio
npm install            # puppeteer-core + @sparticuz/chromium (a bundled Chromium, works behind the allowlist)
python3 -c "import PIL" || pip install pillow --break-system-packages
which ffmpeg           # needed for Reels
```

Fonts are local (`fonts/*.woff2`, loaded by `brand.css`), so renders never depend on the network.

## Brand rules (short version; the design system has the full book)

- Colors: ground `#0A0A0A`, surface `#111412`, line `#26302A`, text `#F5F7F5`, muted `#A3AFA7`, emerald `#22C55E` (one accent word per hook), text on emerald `#052E16`.
- Type: IBM Plex Sans Arabic for Arabic, Inter for Latin and numbers.
- Faceless: no people, no stock photos. The work itself (a site scrolling on a phone, a bot chat) is the visual.
- Every Reel shows the result in the first 3 seconds. No logo intros.
- Arabic: light Levantine for captions and on-screen text, Palestinian dialect for DMs. Spell هسا and قديش. Western digits 0-9. No em or en dashes. Before saving any Arabic, load the `arabic-voice` skill and run its checker:
  `python3 <arabic-voice skill dir>/scripts/check_arabic.py --register light file.txt` (must exit 0).
- Never invent prices, results, client names or reviews. Prices: landing page $33/mo, website or web app $66/mo, app + web $99/mo, Custom. Pages are ready in about 24 hours. Hosting, domain, edits and support are included; if a client stops paying, the service stops.

## The weekly rhythm (7 posts, 20:00 Palestine time)

| Day | Format | Theme |
|---|---|---|
| Saturday | Showcase Reel (`showcase-reel`, kind `video`) | Online, made easy (`online-easy`) |
| Sunday | Tips carousel (`tips-carousel`, kind `carousel`) | More customers through WhatsApp (`whatsapp-customers`) |
| Monday | Showcase Reel | Online, made easy |
| Tuesday | Before and after (`before-after`, kind `image`) | Online, made easy |
| Wednesday | Demo Reel (`demo-reel`, kind `video`) | More customers through WhatsApp |
| Thursday | Showcase Reel | Online, made easy |
| Friday | Offer or proof (`price-card` or a proof post, kind `image`) | Offer and proof (`offer-proof`) |

Idea rule: every post tests a NEW idea (a new angle, pain, niche or hook) until one wins.
A post is a candidate at 2× the average chats; it is a winner after 3 copies that each beat the
average by 20%. Once there is a winner, copy it in 2 of every 3 posts and keep 1 in 3 as a new idea.
Before planning, read last weeks' numbers (`sahl_posts.chats`, `winner`) and the HQ `posts` docs.

Codes are global and keep counting: week 1 was P01 to P07, week 2 is P08 to P14, and so on.

## Week file

Copy `week1.json` to `weeks/wNN.json` and change it. Fields per format (see week 1 for full examples):

- all posts: `code, date (YYYY-MM-DD), day, theme, format, kind, idea (English, one line), caption (Arabic, ends with hashtags), wa_text (the WhatsApp prefill, ends with "(<code>)")`
- `showcase-reel`: `site` (a folder in `frames/`), `chip`, `hook_html` (one `<span class="em">` word), `sub`, `note`, optional `scroll_to`
- `demo-reel`: `chip, hook_html, sub, chat [{from: "them"|"bot", text, t}]`, optional `biz_name, biz_sub, end_at, seconds`
- `tips-carousel`: `slides [{type: cover|tip|cta, ...}]` (6 slides)
- `before-after`: `site, headline, tag, before_title, before_lines [4], after_title`
- `price-card`: `headline, price, price_note, items [..], foot`
- top level `group_posts [{day, kind: welcome|poll|tip|question, text}]` (3 per week, for our own Group)

## Build

```bash
export WEEK_JSON=weeks/w45.json OUT=out/w45
python3 build_reels.py            # every showcase-reel in the week (or pass codes)
python3 build_chat.py P12         # the demo Reel
python3 build_stills.py           # carousel, before/after, price card
```

Check every output before publishing: watch one frame per Reel (`ffmpeg -ss 3 -i X.mp4 -frames:v 1 f.jpg`) and look at every PNG.
Arabic must render joined and right to left; prices inside Arabic need `<bdi dir="ltr">`.

New showcase site? Capture it on a phone-width page (375×812) in the built-in browser: one screenshot
every 700px named `frames/<site>/0000.jpg, 0700.jpg, ...` plus `frames/<site>/header.jpg`, then
`python3 stitch.py <site>` (add its sticky-header height to `HDR` in stitch.py).

## Publish the media

```bash
mkdir -p ../sahl/media/w45 && cp out/w45/*.mp4 out/w45/*.png ../sahl/media/w45/
cd .. && git add sahl/media/w45 && git commit -m "Sahl week 45 media" && git push origin main
```

GitHub Pages takes about a minute. Check each URL loads (from a browser tool; the shell may be blocked) before queueing.

## Queue the posts

1. Supabase `iezglohziunneucnsngq` (execute_sql), one row per post:

```sql
insert into public.sahl_posts (code, week, post_date, theme, format, kind, idea, caption, first_comment, media_urls, approve_by)
values ('P08','2026-W45','2026-11-07','online-easy','showcase-reel','video','<idea>','<caption>',
  'للحجز والاستفسار عالواتساب 👇' || chr(10) || 'https://wa.me/972595376623?text=<url-encoded wa_text>',
  array['https://adhamabuallan.github.io/sahl/media/w45/P08.mp4']::text[],
  ('<Friday before the week> 23:59'::timestamp at time zone 'Asia/Hebron'))
on conflict (code) do nothing;
```
Escape single quotes in Arabic by doubling them. A pending post auto-approves after `approve_by`.

2. HQ board (ArtifactData, one `batch`): `posts/<code>` docs with
`{code, week, date, theme, format, kind, idea, caption, first_comment, media_urls, approve_by (ISO UTC), status: "pending", synced: true, wa_text, thumb}`
where `thumb` is a 360px-wide JPEG as a `data:image/jpeg;base64,...` string (Reels: a frame at 3.2 s).
Also `groups/<week>-<n>` docs `{week, date, day, kind, text, done: false}`.

## Auto-poster endpoints (all need header `x-cron-key` = `sahl_settings.cron_key`)

Call them from SQL with `net.http_post(url := 'https://iezglohziunneucnsngq.supabase.co/functions/v1/sahl-poster/<route>', headers := jsonb_build_object('Content-Type','application/json','x-cron-key',(select cron_key from public.sahl_settings where id=1)), body := '{}'::jsonb)`, then read `net._http_response` by the returned id.

- `/status` Page connection check
- `/cron` the hourly run (posts at 20:00 local, once a day)
- `/post-now?code=P08` post one now (only when Adham asks)
- `/insights` pull shares and reach into `sahl_posts`
- `/setup-page` with JSON body `{picture_url, cover_url, about}` to change Page images
- `/refresh-token` re-read the Page token after Adham reconnects the Meta app

`sahl_settings.paused = true` stops all posting.

The poster moved from project `alfhdieorygvgrmhypea` on 2026-10-29 (that project is paused). Use only `iezglohziunneucnsngq`.
