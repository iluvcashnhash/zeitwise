# ZeitWise

**ZeitWise** is a multimodal AI-powered application that turns endless doomscrolling into **actionable insights and humor**. In an era of information overload, it lets users hold a **two-way conversation** with virtual "sages" (philosophers, thinkers, and witty personalities) for a fresh perspective on the news. The app combines text, voice (TTS), and images: news headlines come with historical parallels and witty commentary, while chats with personas can spawn meme images to amplify the effect. In short, ZeitWise aims to tame the noise—finding echoes in history, extracting wisdom, and even sparking a smile—all in a single app.

## Project Structure

```
zeitwise/
├── apps/                  # Frontend applications (Next.js, React Native)
├── docs/                  # Documentation
├── infra/                 # Infrastructure as Code (Docker, Kubernetes)
│   └── supabase/          # Supabase migrations and configuration
├── packages/              # Shared packages and libraries
├── scripts/               # Utility scripts
│   └── generate-types.ts   # Database type generation
├── services/              # Backend services
│   └── backend/           # FastAPI backend
│       ├── app/           # Application code
│       ├── tests/         # Test suite
│       └── pyproject.toml # Python dependencies
├── types/                 # Generated TypeScript types
├── .env.example          # Environment variables example
├── docker-compose.yml     # Local development stack
└── README.md             # This file
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.10+
- PostgreSQL 15+

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/zeitwise.git
   cd zeitwise
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development stack**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   # Apply migrations
   docker-compose exec api alembic upgrade head
   
   # Generate TypeScript types
   npm run generate:types
   ```

5. **Start the development servers**
   ```bash
   # Backend (FastAPI)
   cd services/backend
   poetry install
   poetry run uvicorn app.main:app --reload
   
   # Frontend (Next.js)
   cd ../../apps/web
   npm install
   npm run dev
   ```

## Development Workflow

### Database Migrations

1. Create a new migration:
   ```bash
   docker-compose exec api alembic revision --autogenerate -m "description"
   ```

2. Apply migrations:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. Generate TypeScript types after schema changes:
   ```bash
   npm run generate:types
   ```

### Testing

```bash
# Run backend tests
cd services/backend
poetry run pytest

# Run frontend tests
cd ../../apps/web
npm test
```

## API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Core Features

- **Sage Chat**: Interactive chat with AI personas
- **Doomscroll Detox**: Historical context for news articles
- **Meme Generation**: AI-generated memes based on content
- **User Authentication**: JWT-based auth with Supabase
- **Real-time Updates**: WebSocket support for live interactions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Core Goals

* **Engagement & enlightenment:** Deliver intellectually rich content to Gen Z and millennials (18–35) in a convenient format—blending *education*, *entertainment*, and *stress relief* so every news item becomes a mini-lesson or joke.
* **Ship the MVP:** Release an MVP within 12 weeks focused on the core experience: Sage Chat and Doomscroll Detox. Skip heavyweight features for now (no live video debates or full persona marketplace) and optimize speed and stability.
* **Viral, shareable content:** Build features that spark viral growth—memes, witty replies, short videos. Personas must feel authentic and “spicy” (edgy answers come from the *wild* Grok model) yet be fact-checked by GPT-4.
* **Scalable platform:** Lay the foundation for future capabilities—multiple languages, more personas, gamification, and monetization. The MVP teases a *Persona Marketplace* (static screen) and a simple Free/Pro/Guru subscription model.
* **Data-driven iteration:** Instrument the app with analytics (PostHog) and A/B testing to refine the product based on real usage data.

## 12-Week Development Roadmap

1. **Weeks 1–3 – Foundations.**

   * Set up repo, initial mobile & web scaffolds, and backend.
   * Initialize Supabase (Auth, Postgres, Storage) and CI/CD pipelines.
   * Create an *MVP Telegram bot*: users forward a news item to `@ZeitWiseBot`, which saves it to `tg_posts_raw`. Add a cron reminder (push when ≥ 5 new posts) and basic notifications.

2. **Weeks 4–6 – Core Engine.**

   * Build the AI pipeline. Prototype semantic search (“News Déjà Vu”) that finds historical events matching headlines.
   * Construct an *LLM router*: send requests to OpenAI GPT-4 or xAI Grok based on profanity score.
   * Start the meme-generation pipeline (GPT prompt → Stable Diffusion → post-processing).
   * By week 6, a background worker should ingest posts, find historical parallels, generate analysis & memes, and save them to `detox_items`.

3. **Weeks 7–9 – Interfaces.**

   * Polish the UX. Finalize Detox worker (caching & vector DB integration).
   * **Detox Feed UI:** React Native carousel showing 4-slide Detox cards (headline, history, analysis, meme).
   * **Sage Chat UI:** chat with voice replies (TTS). Integrate persona voices and allow personal chats with each sage.
   * Prepare *Persona Store* screen (static “coming soon” teaser).

4. **Weeks 10–11 – Polish & Web.**

   * Sync web (Next.js via Solito) with mobile.
   * Add analytics (PostHog) and error reporting (Sentry).
   * QA, security audit, bug-fixes.
   * Integrate payments (Stripe) for Free/Pro/Guru plans (stubbed).
   * Prepare marketing assets, screenshots, and store listings for TestFlight/Play Store.

5. **Week 12 – Beta Release.**

   * Ship closed betas on TestFlight and Google Play.
   * Launch Telegram bot for user news collection.
   * Gather feedback, watch metrics, plan next-stage features.

Key milestones: **Detox Feed UI (week 8)**, **Sage Chat UI (week 9)**, **beta release (week 12)**. Post-MVP features: live multi-avatar debates, user-generated personas, full marketplace, extended localization.

## Tech Stack

* **Frontend (mobile & web):** Expo/React Native (mobile) + Next.js with `react-native-web` via [Solito](https://solito.dev). Cross-platform UI styling with Tamagui. Voice via Silero TTS.
* **Backend API:** Python + FastAPI (Docker). Handles user requests, auth (JWT), and proxies to AI services. Background tasks (chat processing, Detox generation) run via Redis queue.
* **Edge Functions (Supabase):** Supabase Edge Functions (Deno) for lightweight tasks: cron reminders/notifications, simple DB ops, and webhooks (e.g., from Telegram).

### Databases

* *Relational:* Supabase Postgres for user data (accounts, settings, chat logs).
* *Storage:* Supabase Storage for media (avatars, generated memes, videos).
* *Vector search:* Qdrant for semantic search. Indexes news & historical data for the “Historical Correlator.” (Early MVP used Pinecone sandbox; now Qdrant.)

### AI/ML Models

* **LLM:** OpenAI GPT-3.5/4 for general tasks and xAI Grok for edgier replies. Requests with profanity > 0.7 go to Grok.
* **Computer vision:** Stable Diffusion 1.5 (NVIDIA T4) for meme images.
* **Speech:** Silero TTS for voice synthesis (multi-language).
* **NLP:** VADER for sentiment analysis.
* **Custom:** Future fine-tuned lightweight LLMs for offline use.

### Integrations / APIs

* Social/news sources: X/Twitter (OAuth), Telegram channels, RSS. (MVP polls sources every 6 hours.)
* **Telegram bot:** `@ZeitWiseBot` (Python) accepts forwarded posts.
* **Payments:** Stripe SDK for in-app subscriptions (Free/Pro/Guru).

### Analytics & Monitoring

* PostHog for DAU & funnel metrics.
* Sentry for error reporting.

### Hosting

* API & background services run in Docker (Node/Python) on a GPU VM.
* Mobile builds via Expo EAS.
* Web app hosted on Vercel.

**Quick tech recap**

* **Mobile/Web:** React Native (Expo) + Next.js (Solito)
* **UI library:** Tamagui
* **API:** FastAPI (Python, Docker)
* **Edge Functions:** Supabase Edge (Deno)
* **Databases:** Supabase Postgres & Storage; Qdrant
* **AI models:** OpenAI GPT-4, xAI Grok, Stable Diffusion 1.5, Silero TTS
* **Search:** Semantic search on Qdrant (“News Déjà Vu”)
* **Auth:** Supabase Auth (email, JWT)
* **Payments:** Stripe (Free/Pro/Guru)
* **CI/CD:** GitHub Actions, Expo EAS, Vercel, Supabase migrations
* **Analytics:** PostHog dashboards for funnels/retention

## CI/CD & DevOps

* **GitHub Actions:** On every push/PR, the CI pipeline builds Docker images, runs backend tests, and lints code (ESLint for JS/TS, pytest/flake8 for Python). Merge to `main` triggers deploy.
* **Mobile builds:** Expo EAS auto-builds iOS & Android on pushes to `main`; new builds upload to TestFlight & Google Play Beta.
* **Web deploy:** Next.js auto-deploys to Vercel from `main` (preview deployments for PRs).
* **Supabase migrations:** Managed via Supabase CLI; SQL migrations in `supabase/migrations` apply on merge.
* **Secrets & config:** API keys (OpenAI, Stripe, Supabase, etc.) live in GitHub Secrets & Expo Secrets; each environment (dev/beta/prod) has its own.
* **Infrastructure:** Backend services orchestrated with Docker Compose (FastAPI, Qdrant, Redis, n8n). Each service has its own container & volume. n8n runs in the shared Docker network and connects to Supabase and FastAPI APIs.
* **Monitoring & alerts:** Sentry for runtime errors. Automated tests (unit, integration) run on schedule to catch regressions early.

CI/CD is fully documented in `/docs/ci-cd.md`; key deploy scripts live in the repo.

## Automation Layer (n8n)

We use [n8n](https://n8n.io)—an open-source workflow-automation platform—to orchestrate background tasks and integrations. n8n acts as an orchestration bus and ETL tool, complementing (not replacing) the FastAPI backend, and lets non-technical editors configure workflows visually. Sample n8n workflows:

* **Telegram handler:** New messages from a Telegram channel are automatically stored in Supabase (`tg_posts_raw`) for further processing.
* **RSS sentiment monitor:** n8n watches RSS feeds, analyzes sentiment (VADER), and inserts matching items into `detox_items`.
* **Audio (TTS) queue:** New texts trigger TTS generation tasks; audio is saved for later playback.
* **Daily push notifications:** On a schedule (via Supabase cron), n8n sends daily push notifications through the Push API.
* **Meme publishing (optional):** n8n can post generated memes to a Telegram channel on schedule.
* **Flexibility:** All automations are set up in the n8n GUI, letting editors add new sources or actions without code changes.

Important: n8n does **not** replace the core FastAPI backend. FastAPI still handles client requests and business logic, while n8n tackles data-source integrations, background orchestration, and ETL.

## Global Constants & Variables

Examples of global settings (config or `.env`):

```js
// Max free Detox cards per user per day (MVP cap)
const MAX_FREE_DETOXES_PER_DAY = 5;

// Default app language (ISO code)
const DEFAULT_LANG = 'en';

// Profanity threshold above which requests switch to xAI Grok
const GROK_PROFANITY_THRESHOLD = 0.75;

// Mapping of TTS voices to languages
const TTS_VOICE_MAP = {
  en: 'en-US-Neural2-J',
  ru: 'ru-RU-Wavenet-A',
  // add more as needed...
};

// Default temperature for GPT-4 (tuned per persona later)
const OPENAI_TEMPERATURE = 0.7;

// Meme image dimensions (per MVP requirements)
const MEME_IMAGE_DIMENSIONS = { width: 512, height: 512 };
```

## Key Modules

* **Sage Chat:** Interactive chat engine where a user picks an AI persona (philosopher mask) and converses. Each persona (e.g., *“Provocateur Socrates”* or *“Karl Marx the Smoker”*) has its own voice and character. Supports text input and voice output (TTS). (Future: multi-persona group chats.)
* **Doomscroll Detox (Historical Prism):** The flagship feature. Takes trending news from user feeds and generates a 4-slide card: *Headline → Historical Parallel → Sage Analysis → Meme*. The “Historical Correlator” finds analogous past events via Qdrant; an LLM crafts explanatory text; the MemeGen pipeline makes a humorous image. Displayed as a carousel or short video.
* **Persona Marketplace:** Store for personas. MVP shows a static teaser (many personas locked; subscription upsell). Later, users can buy persona packs or add custom personas via IAP.
* **MemeGen:** Image-generation pipeline. Given text/context, GPT drafts a creative prompt, Stable Diffusion (SDXL) renders an image, and NSFW filters run on GPU. URL saved in `detox_item` for feed display.
* **Historical Correlator:** Semantic search engine over historical events/news (“News Déjà Vu”). Finds past analogues for headlines using Qdrant. Part of the Detox worker.
* **Telegram bot:** `@ZeitWiseBot` lets users forward alarming news from Telegram. Saves incoming messages to Supabase (`tg_posts_raw`); backend worker processes them for Detox. Also handles reminders and feedback.
* **Gamification Engine:** (planned) Tracks user streaks, awards badges (e.g., “Little Socrates” for 7 days), and may introduce leaderboards. Initial implementation is a simple counter and six badges; richer gamification comes later.

Each module is its own service or component (e.g., Detox worker, SageChat service, history indexer) for independent scaling.

## Local Development & Build

To run ZeitWise locally for development:

1. **Requirements**

   * Install Node.js 16+, Yarn, and Expo CLI.
   * Install the [Supabase CLI](https://supabase.com/docs/guides/cli) for local DB & migrations.
   * Install Docker (backend & Qdrant).

2. **Clone the repo**

   ```bash
   git clone https://github.com/iluvcashnhash/ZeitWise.git
   cd ZeitWise
   ```

3. **Install dependencies**

   ```bash
   yarn install
   ```

4. **Configure environment**

   * Copy `.env.example` to `.env` and fill in keys (SUPABASE\_URL/KEY, OPENAI\_API\_KEY, TELEGRAM\_BOT\_TOKEN, STRIPE\_KEY, etc.).
   * To enable the Expo dev client (e.g., for TTS testing), set `EXPO_DEV_CLIENT=1`.

5. **Initialize Supabase**

   ```bash
   supabase start      # launches local Postgres & Studio
   supabase db reset   # applies migrations
   ```

6. **Start backend & services**

   ```bash
   docker-compose up -d
   ```

   This spins up FastAPI, Redis, Qdrant **and n8n** containers.

7. **Run the mobile app**

   ```bash
   cd mobile
   expo start
   ```

   Open in Expo Go or an emulator. It connects to the local API (set `API_URL` in `.env`).

8. **Run the web app**

   ```bash
   cd web
   yarn dev
   ```

   (Or `yarn dev:web` from root if configured.) This serves Next.js locally.

9. **Integration test**

   * Forward a message with `/forward` to `@ZeitWiseBot` and verify it appears in Supabase (`tg_posts_raw`).
   * In the Detox interface, input a headline or forwarded post and check the historical context & meme display.

10. **Build & test**

    * Run backend tests `yarn test` and linters `yarn lint`.
    * For production mobile builds, use `yarn eas build`.

See `CONTRIBUTING.md` for code conventions. Each sub-project (`/mobile`, `/web`, `/api`) has its own README.

**This README will evolve with the project.** Update it whenever new modules, architectural changes, or plans are added. It serves as a living reference for the ZeitWise team.