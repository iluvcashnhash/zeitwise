# ZeitWise

**ZeitWise** is a multimodal AI-driven app that turns “doomscrolling” into **insight and humor**. In a time of information overload, it lets users engage in interactive dialogue with AI “**sages**” (philosophers, thinkers, and witty personas) to put today’s news into perspective.  The app combines text, voice (TTS), and images: news headlines are reframed with historical parallels and witty commentary, and chats with personas can generate meme-worthy images for emphasis.  In short, ZeitWise aims to make sense of the world’s noise – by finding history’s parallels, extracting wisdom, and even sharing a laugh – all in one place.

The MVP focus is on the “core wow”: **text chat + meme image + voice**.  Users can chat one-on-one with a small set of philosopher avatars (e.g. Socrates, Diogenes, a snarky Marx) via text and hear them speak (silero TTS).  Separately, the **“Doomscroll Detox”** feed (aka **History Lens**) presents a carousel of trending news where each headline is paired with: (1) a historical parallel, (2) an AI analysis, and (3) a humorous meme or remark.  (For example: *“This crisis echoes the 1637 Tulip Mania.”*)  The result is a scrolling feed that turns panic into perspective and even amusement.  These are delivered in a visually rich, swipeable format to engage users and encourage sharing.

## Core Goals

* **Engage and Enlighten:** Empower Gen Z and Millennial users (18–35) with intellectual depth in a snackable format. Combine *education, entertainment,* and *stress relief* so every news alert becomes a mini-lesson or joke.

* **MVP Delivery:** Ship the MVP in 12 weeks with a tight focus on the core experience: Sage Chat and Doomscroll Detox.  This means limiting heavy features (no live video debates or full-persona marketplace yet) and optimizing for speed and stability.

* **Viral, Shareable Content:** Build features that drive virality – memes, witty banter, and shareable video clips.  The personas should feel authentic and unfiltered (using a “wild” model codenamed *Grok* for edgy answers) but fact-checked by GPT-4 for accuracy.

* **Scalable Platform:** Establish a foundation for future features: multilingual support, more personas, gamification, and monetization.  For MVP, we provide a teaser **Persona Marketplace** (static store UI) and a simple free/pro/guru monetization model.

* **Data-Driven Learning:** Instrument the app with analytics (PostHog) and A/B testing to iterate quickly based on real user behavior.

In summary, the product vision is to reframe anxiety as wisdom – “history, analysis, and memes in one feed” – while laying the groundwork for a smart, fun “intellectual community” over time.

## Development Roadmap (12 Weeks)

We plan a 3-month MVP cycle with the following milestones:

1. **Weeks 1–3: Foundation.** Set up the repo, mobile/web scaffolds, and backend framework.  Initialize Supabase (Auth, Postgres, Storage) and CI/CD pipelines.  Build the **Telegram Bot MVP**: users can forward a news post to our `@ZeitWiseBot`, which stores it in `tg_posts_raw`.  Implement a reminder cron (e.g. push if ≥5 pending posts) and basic notifications.

2. **Weeks 4–6: Core Engine.** Develop the AI pipeline.  Create a **semantic search** proof-of-concept (“News Déjà Vu”) that finds related historical events for a given headline.  Build the **LLM Router**: route requests to OpenAI GPT-4 or to xAI Grok based on profanity score.  Begin the **meme generation pipeline** (GPT prompt → Stable Diffusion → post-processing).  By week 6, we should have an end-to-end backend worker that ingests posts, finds historical parallels, generates analysis and memes, and writes to `detox_items`.

3. **Weeks 7–9: Feature UIs.** Build the user-facing features.  Finalize the detox worker (cache results, integrate with vector DB).  **Detox Feed UI:** Develop a React Native carousel to display each 4-slide “detox card” (headline, history, analysis, meme).  **Sage Chat UI:** Implement the chat interface with voice (TTS) support.  Integrate persona audio/avatars and allow one-on-one chat with each AI Sage (text + speech).  Also design a **Persona Store** screen (initially static with locked items and “coming soon” placeholders).

4. **Weeks 10–11: Polish & Web.** Sync the web experience (Next.js via Solito) with mobile features.  Set up analytics (PostHog) and crash reporting (Sentry).  Conduct QA, security audit, and fix bugs.  Ensure payment/IAP (Stripe) integration stubs for Free/Pro/Guru plans.  Prepare marketing copy, screenshots, and TestFlight/Play store assets.

5. **Week 12: Beta Launch.** Release the beta on TestFlight and Google Play (closed beta).  Soft-launch the Telegram bot to seed user content.  Gather feedback, monitor usage, and plan next-phase features.

Throughout, key milestones are: **Detox Feed UI (week 8)**, **Sage Chat UI (week 9)**, and **Beta Release (week 12)**.  Features deferred beyond MVP include live multi-avatar debates, user-generated persona training, full persona marketplace, advanced gamification, and extended localization.

## Technical Stack

* **Frontend (Mobile & Web):** Expo/React Native (mobile) and Next.js with `react-native-web` (web) using [Solito](https://solito.dev) for shared code.  We use Tamagui for cross-platform UI styling.  Voice features use Silero TTS on-device or via API.

* **Backend API:** Python + FastAPI (Dockerized) serves as the API gateway.  It handles user requests, authentication (JWT), and proxies to AI services.  A Redis queue backs async tasks (chat processing, detox generation).

* **Edge Functions:** Supabase Edge Functions (Deno) run lightweight jobs: scheduled tasks (cron/email/push reminders), simple DB operations, and webhooks (e.g. Telegram callback).

* **Databases:**

  * *Relational:* Supabase Postgres for user data (users, settings, chat logs).
  * *Storage:* Supabase Storage for media (avatars, generated memes, videos).
  * *Vector Search:* Qdrant (self-hosted) for semantic retrieval. We index news & history corpora to power the “Historical Correlator” search. (MVP used Pinecone sandbox, now Qdrant.)

* **AI/ML Models:**

  * *LLM:* OpenAI GPT-3.5/4 for general Q\&A, and xAI Grok for edgy/unfiltered responses.  A profanity threshold (e.g. >0.7) switches input to Grok.
  * *Vision:* Stable Diffusion 1.5 (on NVIDIA T4 GPU) generates meme images.
  * *Speech:* Silero TTS for voice output (multi-language capable).
  * *NLP:* VADER sentiment analysis for content tone.
  * *Custom:* In the long run we may finetune smaller LLMs (on-device) to enable offline mode.

* **Integrations/APIs:**

  * Social/news sources: Twitter/X (OAuth), Telegram channel feeds, RSS parsing.  (MVP polls user-linked sources every 6 h.)
  * **Telegram Bot:** A @ZeitWiseBot (Python) ingests forwarded posts.
  * **Payments:** Stripe SDK for in-app subscriptions (Free/Pro/Guru tiers).

* **Analytics & Monitoring:** PostHog (cloud) to track DAU, feature usage, funnel metrics. Sentry for crash/error reporting. These tools inform product decisions and scaling needs.

* **Hosting:**

  * API & worker run on Docker (Node/Python) on a VM with GPU.
  * Mobile apps built via Expo EAS and distributed to app stores.
  * Web app deployed on Vercel.

Key tech components summary:

```markdown
- **Mobile/Web:** React Native (Expo) + Next.js/Solito:contentReference[oaicite:63]{index=63}  
- **UI Library:** Tamagui (cross-platform)  
- **API:** FastAPI (Python, Docker):contentReference[oaicite:64]{index=64}  
- **Edge/Serverless:** Supabase Edge Functions (Deno):contentReference[oaicite:65]{index=65}  
- **DB:** Supabase Postgres & Storage; Qdrant vector DB:contentReference[oaicite:66]{index=66}  
- **AI Models:** OpenAI GPT-4, xAI Grok, Stable Diffusion 1.5, Silero TTS:contentReference[oaicite:67]{index=67}:contentReference[oaicite:68]{index=68}  
- **Search:** Qdrant semantic search (“News Déjà Vu”):contentReference[oaicite:69]{index=69}  
- **Auth:** Supabase Auth (email, no social logins), JWT tokens:contentReference[oaicite:70]{index=70}  
- **Payments:** Stripe In-App Purchases (Free/Pro/Guru):contentReference[oaicite:71]{index=71}  
- **CI/CD:** GitHub Actions, Expo EAS, Vercel, Supabase migrations:contentReference[oaicite:72]{index=72}  
- **Analytics:** PostHog, plus custom dashboards for funnels/retention.  
```

## CI/CD & DevOps

* **GitHub Actions:** On each push/PR the CI pipeline builds Docker images, runs backend/unit tests, and lints code (ESLint for JS/TS, pytest/flake8 for Python). Successful merges to `main` trigger deployments.

* **Mobile Builds:** Expo EAS is configured to automatically build iOS and Android bundles on the main branch. New builds are pushed to TestFlight and Google Play Beta channels.

* **Web Deployments:** The Next.js web app is auto-deployed to Vercel from `main` (preview environments on PRs).

* **Supabase Migrations:** Using the Supabase CLI, any database schema changes (SQL migrations) are applied on merging to `main`. We maintain a `supabase/migrations` directory under version control.

* **Secrets & Config:** API keys (OpenAI, Stripe, Supabase) and environment variables are stored in GitHub Secrets and Expo Secrets. Each environment (dev/beta/prod) uses appropriate configs.

* **Infrastructure:** We manage backend services via Docker Compose (FastAPI, Qdrant, Redis). GPU instances (NVIDIA T4) are autoscaled off for cost control and only powered on during key tasks.

* **Monitoring & Alerts:** Post-launch, we integrate Sentry for error alerts. Automated tests (unit, integration) run on schedule for early detection of regressions.

All CI/CD and DevOps pipelines are documented in `/docs/ci-cd.md` for the team, and key deployment scripts are versioned alongside the repo.

## Global Constants and Variables

Some representative global constants (to be placed in a config file or environment):

```js
// Maximum free detox usage per user per day (see MVP limits):contentReference[oaicite:76]{index=76}
const MAX_FREE_DETOXES_PER_DAY = 5;

// Default app language (ISO code)
const DEFAULT_LANG = 'en';

// Threshold above which queries use xAI Grok (unfiltered model)
const GROK_PROFANITY_THRESHOLD = 0.75;

// Text-to-Speech voice mapping by language
const TTS_VOICE_MAP = {
  en: 'en-US-Neural2-J',
  ru: 'ru-RU-Wavenet-A',
  // add more as needed...
};

// Default temperature for GPT-4 (fine-tuned per persona later)
const OPENAI_TEMPERATURE = 0.7;

// Dimensions for generated meme images (per MVP spec):contentReference[oaicite:77]{index=77}
const MEME_IMAGE_DIMENSIONS = { width: 512, height: 512 };
```

Other examples: rate limits (e.g. `MAX_CHAT_MESSAGES`), cache TTLs for Semantic Search, feature flags (e.g. `ENABLE_PERSONA_MARKETPLACE = false` initially), etc. Values marked with MVP references should match the tech spec above.

## Key Modules

* **SageChat:** An interactive chat engine where users pick an AI persona (philosophical mask) and have a conversation.  Each persona (e.g. *Socrates the Gadfly, Karl Marx the Smoker*) has a distinct voice and attitude. Chats support text input and audio output via TTS. (Multi-person “summon a meeting” panels are planned later.)

* **Doomscroll Detox (History Lens):** The signature news detox feature. It fetches headlines from user feeds or trending sources and produces a 4-part card: *Headline → Historical Parallel → Sage Analysis → Meme*. This module uses the **Historical Correlator** to find relevant events from our history corpus, then an LLM to write context and a meme image to lighten the mood. The result is presented as an interactive carousel or short video.

* **Persona Marketplace:** A store UI where users can see available and “coming soon” AI personas. In the MVP this is a **static teaser** (locked personas, subscription prompts). Eventually, it will allow purchasing persona packs or custom personas via IAP and user contributions.

* **MemeGen:** The image generation pipeline. Given a text prompt or conversation context, this module uses a GPT-based prompt followed by Stable Diffusion (SDXL) to create a meme image. We support a built-in template library (\~50 popular meme formats) and ensure safe generation (NSFW filter) on the GPU. The `meme_url` is then attached to the Detox item for display.

* **Historical Correlator:** A semantic search engine over a database of historical events and news (the “News Déjà Vu” database). When given a headline, it queries Qdrant to find analogous past events. This provides the “Historical Parallel” used in the Detox feed. It runs as part of the Detox worker pipeline.

* **Telegram Bot:** The `@ZeitWiseBot` lets users forward disturbing news posts directly from Telegram. It stores incoming messages in Supabase (`tg_posts_raw`). The backend worker then processes these posts for detoxification. The bot also handles user reminders and feedback.

* **Gamification Engine:** (Planned for future iterations) Tracks user streaks, awards badges (e.g. “Little Socrates” for 7-day streak), and may include leaderboards or levels.  Initially we provide a simple streak counter and 6 achievement badges; advanced features come after launch.

Each module is implemented as a separate service or component (e.g. Detox pipeline worker, chat service, search indexer) to allow independent scaling.

## Local Development & Build

To run ZeitWise locally for development:

1. **Prerequisites:**

   * Install Node.js (16+), Yarn, and Expo CLI.
   * Install [Supabase CLI](https://supabase.com/docs/guides/cli) for local DB/migrations.
   * Install Docker (for backend & vector DB).

2. **Clone the repo:**

   ```bash
   git clone https://github.com/our-org/ZeitWise.git
   cd ZeitWise
   ```

3. **Install Dependencies:**

   ```bash
   yarn install
   ```

4. **Configure Environment:**

   * Copy `.env.example` to `.env` and fill in keys (SUPABASE\_URL/KEY, OPENAI\_API\_KEY, TELEGRAM\_BOT\_TOKEN, STRIPE\_KEY, etc.).
   * Set `EXPO_DEV_CLIENT=1` to use the dev client for TTS if needed.

5. **Initialize Supabase:**

   ```bash
   supabase start   # starts local Postgres & Studio
   supabase db reset   # create database from migrations
   ```

6. **Start Backend & Services:**

   ```bash
   docker-compose up -d
   # This starts the FastAPI backend, Redis, and Qdrant containers.
   ```

7. **Run Mobile App:**

   ```bash
   cd mobile
   expo start
   ```

   Then open the app in the Expo Go client or simulator. The app will connect to the local API (set `API_URL` in `.env`).

8. **Run Web App:**

   ```bash
   cd web
   yarn dev
   ```

   (Or `yarn dev:web` from root, if configured.) This serves the Next.js app locally.

9. **Test Integrations:**

   * Use the Telegram bot: `/forward` a message to `@ZeitWiseBot` and watch it appear in Supabase (`tg_posts_raw`).
   * Use the Detox UI to enter a headline or forward from Telegram to see the historical context and meme.

10. **Build/Test:**

    * Run tests with `yarn test` (backend) and `yarn lint` (frontend).
    * Use `yarn eas build` for production mobile builds as needed.

See `CONTRIBUTING.md` for coding conventions and more details. The README in each subfolder (`/mobile`, `/web`, `/api`) contains further instructions for those components.

**This README should evolve with the project**. Update it whenever adding new modules, changing architecture, or adjusting milestones. It’s intended as a living document for the ZeitWise team’s reference.
