# ZeitWise – MVP Roadmap (Q3 2025)

> Single‑snapshot timeline to align product, design & engineering for the 12‑week MVP sprint. Update statuses inline.

## Overview

| Week | Theme                      | Lead Function    | Definition of Done                                                             |
| ---- | -------------------------- | ---------------- | ------------------------------------------------------------------------------ |
| 1    | Foundations                | DevOps           | Repo bootstrap, Supabase project, CI/CD skeleton live                          |
| 2    | Telegram Ingest            | Integrations     | `@ZeitWiseBot` saves forwarded posts to `tg_posts_raw`; push notification cron |
| 3    | Core DB & Auth             | Backend          | Schema migrations (`users`, `chat`, `detox`), JWT auth wired to Supabase       |
| 4    | Historical Search PoC      | Data / ML        | News Déjà Vu ↔ Qdrant prototype returns top‑1 analogue in <1 s                 |
| 5    | LLM Router & Profanity     | Backend / ML     | Routing layer (OpenAI vs Grok) passes profanity tests; unit coverage ≥ 80 %    |
| 6    | MemeGen Pipeline v1        | ML / Infra       | GPT‑prompt → Stable Diffusion → Pillow overlay; Safety Checker on GPU T4       |
| 7    | Detox Worker E2E           | Data             | Background queue writes fully‑formed `detox_items`; cache hits tested          |
| 8    | Detox Feed UI              | Frontend         | React‑Native carousel renders 4‑slide card; pulls pre‑computed items           |
| 9    | Sage Chat UI + TTS         | Frontend / Audio | One‑on‑one chat with Socrates et al.; Silero voices streamed                   |
| 10   | Web Parity & Payments Stub | Web / Platform   | Next.js (Solito) hits same API; Stripe sandbox plans visible                   |
| 11   | QA & Analytics             | QA / Product     | Sentry integrated; PostHog funnels live; critical bugs < 5                     |
| 12   | **Closed Beta Launch**     | All              | TestFlight & Google Play Beta + Telegram soft‑launch; feedback channels open   |

### Milestones

* **Mid‑sprint demo:** end of Week 6 – full Detox card from headline to meme.
* **Feature‑freeze:** start of Week 11 – only bug‑fixes and performance tuning.
* **Go/No‑Go:** Week 12 Thursday – beta readiness review.

## Post‑MVP (Q4 2025 +)

* Live multi‑avatar debates (panel mode)
* Persona Marketplace with IAP unlocks
* Mind Metrics dashboard & gamification tree
* Extended localization (FR / ES / KO)
* Video 9:16 auto‑clips for social sharing

## Known Risks & Mitigations

| Risk                              | Impact               | Mitigation                                 |
| --------------------------------- | -------------------- | ------------------------------------------ |
| Twitter API cost spikes           | Delays personal feed | Fallback to RSS/TG channels                |
| GPU bottleneck for SD             | Slow meme generation | Hash‑cache + single‑queue throttle         |
| OpenAI moderation false positives | Blocks edgy content  | Route to Grok, adjust thresholds           |
| Slip in mobile approval           | Beta delay           | Parallel Web SPA + early TestFlight review |

*Last updated: 26 June 2025 – keep this file authoritative.*
