# Autonomous Traders

Four named traders (Warren, George, Ray, Cathie) plus a researcher agent. They use MCP servers for accounts, push notifications, market data, web search, fetch, and memory. A FastAPI backend and a Vite dashboard show portfolios and live traces.


## Setup

Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.

```bash
git clone https://github.com/saaragmon/autonomous-traders.git
cd autonomous-traders
cp .env.example .env
# OPENAI_API_KEY is required
# TAVILY_API_KEY, MASSIVE_API_KEY, PUSHOVER_* are optional
uv sync
```

## Run (three terminals)

**1. API**

```bash
uv run uvicorn backend.api:app --port 8000
```

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

**3. Engine** — the US market is closed on weekends, so force a run:

```bash
RUN_EVEN_WHEN_MARKET_IS_CLOSED=true uv run -m backend.trading_floor
```

Stop the engine first (Ctrl+C) so it does not keep spending API credits. Then stop the frontend and API.

Gradio dashboard instead of Vite: `uv run app.py`.

Without `MASSIVE_API_KEY`, prices are simulated. With a free Massive key, last-trade is paid; this code uses previous close.

## Layout

```
backend/     Accounts, market, MCP, API, trading_floor
frontend/    Vite + TypeScript dashboard
demo/        Gradio UI
app.py       Launch Gradio
```
