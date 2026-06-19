# LiveKit Voice Agent Workshop

Welcome to the Voice Agent Workshop! In this workshop, you will learn how to build and test a production-ready voice agent using [LiveKit](https://livekit.io) and [Coval](https://coval.dev).

## Project Structure

```
voice-agent-workshop/
├── agent.py              # Main voice agent (inbound)
├── obAgent.py            # Outbound calling agent
├── benchmark/            # Benchmarking & telemetry dashboard
│   ├── server.py         # FastAPI server (port 8089)
│   ├── sim_runner.py     # Simulation runner for automated tests
│   ├── asr_eval.py       # ASR accuracy evaluation
│   └── ui/index.html     # Benchmark dashboard UI
├── ops-ui/               # Operations UI (React + Chakra UI)
│   ├── server.py         # FastAPI backend (port 8000)
│   └── src/              # React frontend (Vite dev on port 5173)
├── telemetry/            # Telemetry data (JSONL & JSON files)
├── dispositions/         # Call disposition logs
└── .env.local            # Environment variables (not committed)
```

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **Node.js 18+** and **npm** — for the Ops UI frontend
- **[LiveKit CLI](https://docs.livekit.io/home/cli/cli-setup)** (`lk`) — for dispatch commands and cloud auth

### API Keys Required

| Service | Purpose |
|---------|---------|
| [LiveKit Cloud](https://cloud.livekit.io) | Real-time voice transport |
| [OpenAI](https://platform.openai.com) | LLM (GPT-4.1) |
| [Deepgram](https://www.deepgram.com) | Speech-to-text |
| [NVIDIA NIM](https://build.nvidia.com) | Nemotron STT (benchmark comparisons) |

## Local Setup

### 1. Clone the Repository

```bash
git clone <repo-url>
cd voice-agent-workshop
```

### 2. Install Python Dependencies

```bash
uv sync
```

This creates a `.venv` and installs all packages from `pyproject.toml`.

### 3. Create a Virtual Environment (for benchmark/ops-ui servers)

The benchmark and ops-ui servers spawn subprocesses that need packages available in a `venv`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install fastapi uvicorn certifi livekit livekit-api python-dotenv httpx openai
pip install "livekit-agents[mcp,nvidia]" livekit-plugins-nvidia
deactivate
```

### 4. Configure Environment Variables

Create a `.env.local` file in the project root:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=your_deepgram_key
```

You can auto-populate LiveKit credentials using the CLI:

```bash
lk cloud auth
lk app env -w -d .env.local
```

Then manually add `OPENAI_API_KEY` and `DEEPGRAM_API_KEY` to the file.

### 5. Install Ops UI Frontend Dependencies

```bash
cd ops-ui
npm install
cd ..
```

## Running the Voice Agent

### Console Mode (quick test, no browser needed)

```bash
uv run agent.py console
```

### Dev Mode (connects to LiveKit Cloud for playground/telephony)

```bash
uv run agent.py dev
```

The agent is compatible with the [LiveKit Agents Playground](https://agents-playground.livekit.io).

## Running the Ops UI

The Ops UI provides a real-time operations dashboard for initiating outbound calls, viewing live transcripts, and managing call dispositions.

**Terminal 1 — Backend (port 8000):**

```bash
source venv/bin/activate
cd ops-ui
python server.py
```

**Terminal 2 — Frontend (port 5173):**

```bash
cd ops-ui
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

> **Note:** The outbound agent (`obAgent.py`) must also be running in dev mode for outbound calls to work:
> ```bash
> uv run obAgent.py dev
> ```

## Running the Benchmark Dashboard

The benchmark server runs automated simulation tests against your agent and displays latency, WER, and other metrics.

**Start the benchmark server (port 8089):**

```bash
source venv/bin/activate
python -m benchmark.server
```

Open [http://localhost:8089](http://localhost:8089) in your browser.

The dashboard compares **Nemotron** vs **Deepgram** STT providers across metrics like TTFB, WER, interruption rate, and session duration.

## Testing with Coval

Run your agent in `dev` mode to make it available to Coval:

```bash
uv run agent.py dev
```

To setup the Coval connection:

1. Enable the token server from your project's **Options** on the [Settings](https://cloud.livekit.io/projects/p_/settings/project) page in LiveKit Cloud
2. Copy the `sandboxId` & `sandboxUrl` displayed below the toggle
3. Sign in to your [Coval](https://www.coval.dev/) account
4. Click **Agents** → **Connect Agent**
5. Enter a name for your agent
6. Select **LiveKit** as the simulator type
7. Token endpoint: `https://cloud-api.livekit.io/api/sandbox/connection-details`
8. Token sandbox id: use the `sandboxId` from step 2
9. Add your LiveKit server URL (from `.env.local`)
10. Set content type to `application/json`

## Troubleshooting

- **SSL errors** — The agents set `SSL_CERT_FILE` via `certifi`. Make sure `certifi` is installed in your venv.
- **Module not found in subprocesses** — The benchmark/ops-ui servers use the `venv/` directory (not `.venv`). Ensure packages are installed there per step 3.
- **Browser audio not playing** — Click the page first to satisfy browser autoplay policies. The playground provides an "Enable Audio" fallback button.
- **Port conflicts** — Default ports: agent (LiveKit managed), ops-ui backend (8000), ops-ui frontend (5173), benchmark (8089).

## Post-Workshop Resources

- [Deploying to production](https://docs.livekit.io/agents/ops/deployment/)
- [Web & mobile starter apps](https://docs.livekit.io/agents/start/frontend/#starter-apps)
- [Telephony integrations](https://docs.livekit.io/agents/start/telephony/)
