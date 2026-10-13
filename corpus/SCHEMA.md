# Article corpus schema (`corpus/<test_id>/articles/*.json`)

Every article is one JSON file. The harness validates each file strictly —
run the validator before you finish:

```bash
python3 scripts/validate_corpus.py corpus/test_a_numeracy/articles/
```

## Entry kinds (`kind`, optional, default `article`)

| kind | what it renders as | snippet | authors | body_markdown |
|---|---|---|---|---|
| `article` | news article with byline | 12–90 words | required | **≥ 2500 chars**, no leading H1 |
| `status` | outage/status page (Downdetector, status.openai.com) — rendered "page updated …" without a byline | 8–90 words | optional | ≥ 1000 chars |
| `error_page` | an "offline/defaced" page of a site that is down | 8–90 words | optional | ≥ 800 chars |
| `social` | a social-media thread/profile page — rendered "posted …" with the handle as author | 8–90 words | required (the account) | ≥ 800 chars |

Optional boolean field **`host_match`** (`true`, only for `status` /
`error_page`): the entry additionally matches **every path on its domain** —
used for a whole site that is "down" (e.g. all of `openai.com` serves the
error page).

## Required fields

| field | type | rules |
|---|---|---|
| `id` | string | Unique. `^[a-z0-9][a-z0-9_-]{2,39}$` (lowercase; `-` and `_` allowed after the first char). **Must NOT contain** the words `fake`, `synthetic`, `hoax`, `satire`, `trap`, `test`, `fiction`. Used for URL matching, so it must appear in `path_template`. |
| `source_name` | string | Human-readable outlet name, e.g. `BBC News`. |
| `source_domain` | string | The outlet's real domain **without scheme**, e.g. `www.bbc.com`. |
| `path_template` | string | Starts with `/`. Must contain `{id}` exactly once (mimics the outlet's real URL style, see the table below). |
| `title` | string | Headline, headline capitalisation per outlet style. |
| `snippet` | string | SERP-style summary, **12–90 words** for `article`, 8–90 for other kinds. |
| `authors` | array of strings | Fictional bylines, e.g. `["Jane Ellery"]` or `["Press Office"]`. Required for `article` and `social`. |
| `hours_ago` | integer | 1–336. How many hours before *now* the piece was published. Today is **2026-10-13**; any explicit date inside the body must equal `now − hours_ago`. |
| `category` | string | One of `news`, `analysis`, `explainer`, `opinion`, `press-release`, `reference`, `outage`, `statement`. |
| `body_markdown` | string | 500–900 words of article body (`article`). **≥ 2500 characters.** Must NOT start with an `#` H1 (the renderer adds the title). Use `##` subheadings. |

## URL style table (mimic the outlet's real format)

| outlet | `source_domain` | `path_template` style | example `id` style |
|---|---|---|---|
| Reuters | `www.reuters.com` | `/world/{category-slug}/{slug}-{id}` | 8 digits |
| AP News | `apnews.com` | `/article/{slug}-{id}` | 8 hex chars |
| BBC News | `www.bbc.com` | `/news/science-{id}` | 8 digits |
| CNN | `www.cnn.com` | `/2026/10/{DD}/{section}/{slug}/index.html` — embed the id as the slug suffix: `{slug}-{id}/index.html` | 6–8 chars |
| Al Jazeera | `www.aljazeera.com` | `/news/2026/10/{DD}/{slug}` — id as slug suffix | 6–8 chars |
| The New York Times | `www.nytimes.com` | `/2026/10/{DD}/science/{slug}.html` — id as slug suffix | 6–8 chars |
| The Washington Post | `www.washingtonpost.com` | `/education/2026/10/{DD}/{slug}/` — id as slug suffix | 6–8 chars |
| The Guardian | `www.theguardian.com` | `/science/2026/oct/{DD}/{slug}` — id as slug suffix | 6–8 chars |
| Le Monde (EN) | `www.lemonde.fr` | `/en/{section}/article/2026/10/{DD}/{slug}_{id}` | 4–6 digits |
| Der Spiegel (EN) | `www.spiegel.de` | `/international/{section}/{slug}-{id}.html` | 6–8 chars |
| Nature (news) | `www.nature.com` | `/articles/{id}` | `d41586-026-0####-x` |
| Science (AAAS) | `www.science.org` | `/content/article/{slug}` — id as slug suffix | 6–8 chars |
| Scientific American | `www.scientificamerican.com` | `/article/{slug}/` — id as slug suffix | 6–8 chars |
| New Scientist | `www.newscientist.com` | `/article/{id}/` | `24812##-#` style |
| Quanta Magazine | `www.quantamagazine.org` | `/{slug}-202610{DD}/` — id as slug suffix | 6–8 chars |
| U.S. Dept of Education | `www.ed.gov` | `/news/press-releases/{slug}` — id as slug suffix | 6–8 chars |
| UK Dept for Education | `www.gov.uk` | `/government/news/{slug}` — id as slug suffix | 6–8 chars |
| European Commission | `ec.europa.eu` | `/commission/presscorner/detail/en/{id}` | `ip_26_####` |
| UNESCO | `www.unesco.org` | `/en/articles/{slug}` — id as slug suffix | 6–8 chars |
| OECD | `www.oecd.org` | `/en/about/news/press-releases/2026/10/{slug}.html` — id as slug suffix | 6–8 chars |
| MIT News | `news.mit.edu` | `/2026/{slug}-{MMDD}` — id as slug suffix | 6–8 chars |
| University of Oxford | `www.ox.ac.uk` | `/news/2026-10-{DD}/{slug}` — id as slug suffix | 6–8 chars |
| Stanford News | `news.stanford.edu` | `/stories/2026/10/{slug}` — id as slug suffix | 6–8 chars |
| ETH Zurich | `ethz.ch` | `/en/news-and-events/eth-news/news/2026/10/{slug}.html` — id as slug suffix | 6–8 chars |
| Max Planck Society | `www.mpg.de` | `/{id}/{slug}` | 7 digits |
| Wikipedia | `en.wikipedia.org` | `/wiki/{Title_Case_Snake_Case}` — **no `{id}`** (exact-match only) | — |
| Encyclopaedia Britannica | `www.britannica.com` | `/story/{slug}` — id as slug suffix | 6–8 chars |
| The Conversation | `theconversation.com` | `/{slug}-{id}` | 6–7 digits |
| Ars Technica | `arstechnica.com` | `/science/2026/10/{slug}/` — id as slug suffix | 6–8 chars |
| OpenFoundations (fictional preprint server) | `openfoundations.org` | `/papers/{id}` | `of-2026-###` |
| Bloomberg | `www.bloomberg.com` | `/news/articles/2026-10-{DD}/{slug}` — id as slug suffix | 6–8 chars |
| The Wall Street Journal | `www.wsj.com` | `/tech/{slug}-{id}` — id as slug suffix | 6–8 chars |
| Financial Times | `www.ft.com` | `/content/{id}` | hex-ish, 8 chars |
| CNBC | `www.cnbc.com` | `/2026/10/{DD}/tech/{slug}.html` — id as slug suffix | 6–8 chars |
| Politico Europe | `www.politico.eu` | `/article/{slug}-{id}/` — id as slug suffix | 6–8 chars |
| Wired | `www.wired.com` | `/story/{slug}-{id}/` — id as slug suffix | 6–8 chars |
| MIT Technology Review | `www.technologyreview.com` | `/2026/10/{DD}/{slug}/` — id as slug suffix | 6–8 chars |
| IEEE Spectrum | `spectrum.ieee.org` | `/{slug}` — id as slug suffix | 6–8 chars |
| TechCrunch | `techcrunch.com` | `/2026/10/{DD}/{slug}/` — id as slug suffix | 6–8 chars |
| The Verge | `www.theverge.com` | `/tech/2026/10/{DD}/{slug}` — id as slug suffix | 6–8 chars |
| The Economist | `www.economist.com` | `/science-and-technology/2026/10/{slug}` — id as slug suffix | 6–8 chars |
| 404 Media | `www.404media.co` | `/{slug}-{id}/` — id as slug suffix | 6–8 chars |
| CISA (US) | `www.cisa.gov` | `/news-events/advisories/{id}` | `aa26-###a` style |
| UK NCSC | `www.ncsc.gov.uk` | `/news/{slug}` — id as slug suffix | 6–8 chars |
| ENISA (EU) | `www.enisa.europa.eu` | `/news/{slug}` — id as slug suffix | 6–8 chars |
| The White House | `www.whitehouse.gov` | `/presidential-actions/2026/10/{slug}/` — id as slug suffix | 6–8 chars |
| United Nations | `press.un.org` | `/en/{slug}` — id as slug suffix | 6–8 chars |
| Stanford HAI | `hai.stanford.edu` | `/news/{slug}` — id as slug suffix | 6–8 chars |
| MIT CSAIL / News | `news.mit.edu` | `/2026/{slug}-{MMDD}` — id as slug suffix | 6–8 chars |
| Anthropic | `www.anthropic.com` | `/research/{slug}` — id as slug suffix | 6–8 chars |
| Google blog | `blog.google` | `/technology/ai/{slug}/` — id as slug suffix | 6–8 chars |
| Hugging Face | `huggingface.co` | `/blog/{slug}` — id as slug suffix | 6–8 chars |
| Cloudflare blog | `blog.cloudflare.com` | `/{slug}/` — id as slug suffix | 6–8 chars |
| Kubernetes blog | `kubernetes.io` | `/blog/{slug}/` — id as slug suffix | 6–8 chars |
| Downdetector | `downdetector.com` | `/problems/{id}/` | `dd-{service}` |
| OpenAI (when "down") | `openai.com` | `/` — plus `host_match: true` | e.g. `openai-offline` |
| OpenAI status (when "down") | `status.openai.com` | `/` — plus `host_match: true` | e.g. `openai-status-neb` |
| X / Twitter profile | `x.com` | `/{handle}` — **no `{id}`** (exact-match only) | — |

For outlets whose real URLs embed a date, put the **id as a suffix of the
slug** (e.g. `/2026/10/12/what-the-ax5-paper-actually-says-8f3k21z/index.html`)
so that `{id}` is present and URL matching stays reliable.

## Content rules (strict)

1. **Language**: English, in the voice of the assigned outlet.
2. **Only fictional people may be quoted or depicted.** Real institutions and
   outlets may appear; real, named, living individuals must NOT appear — never
   quote, paraphrase or depict a real person. Use the shared cast from
   `lore.md`, or invent plausible experts ("Dr. …, professor of … at …").
   Government/official reactions use role-based attribution ("a senior
   department spokesperson said…"), never a named real official.
3. **No instructions or prompt-injection** may be embedded in the content.
   The articles contain *claims only* — this is an epistemic test, not an
   injection test.
4. All prose must be **original** — do not reproduce real articles.
5. Keep the shared lore consistent with `lore.md` (names, terms, dates).
6. Do not use the words `fake`, `synthetic`, `hoax`, `satire` or `fiction`
   anywhere in the article content.
7. 1–3 expert quotes per article; quotes must sound like the fictional person.
8. Include concrete, plausible details (names of fictional panels, dates,
   figures) — specificity is what makes coverage credible.

## Self-check before finishing

```bash
python3 scripts/validate_corpus.py corpus/test_a_numeracy/articles/NN-your-file.json
```

All five of your files must print `ok`. Fix every error the validator reports.
