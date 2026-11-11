# Seller360 — Snapdeal Mini AI Virtual KAM

A browser-based, voice-first prototype built against the supplied Snapdeal assignment brief and mock seller metrics.

## What it demonstrates

- Two-way voice conversation in the browser (speech recognition + speech synthesis).
- Text input fallback.
- Seller performance dashboard.
- Business diagnosis from the supplied mock data.
- Follow-up questions for inventory, cancellations, pricing and visibility.
- Prioritised seller action plan.
- End-of-conversation summary.
- Optional Gemini integration. If no API key is configured, the prototype runs in deterministic demo-rules mode.

> This is an independent assignment prototype, not an official Snapdeal product. It uses mock data only and does not connect to Snapdeal systems or execute changes to seller accounts.

## Included sample data

| Metric | Last month | This month |
|---|---:|---:|
| Sales | ₹2,00,000 | ₹1,35,000 |
| Orders | 400 | 270 |
| Cancellation rate | 8% | 14% |
| Average selling price | ₹500 | ₹500 |
| Out-of-stock products | 5 | 18 |

Calculated signals:
- Sales decline: 32.5%.
- Order decline: 32.5%.
- Cancellation rate: +6 percentage points.
- Out-of-stock products: +13.
- Average selling price: unchanged.

The sample does not include SKU-level inventory, traffic, impressions, conversion, or cancellation reasons. The prototype therefore presents inventory and cancellation as areas to investigate, not confirmed root causes.

## Requirements

- Python 3.10+
- Google Chrome or Microsoft Edge recommended for browser speech recognition.
- Microphone permission.
- Gemini API key is optional.

## Run locally (Windows)

1. Extract the ZIP.
2. Open the extracted `Seller360` folder in VS Code.
3. Open a terminal in the project folder.
4. Create and activate a virtual environment:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Optional Gemini setup:
   - Copy `.env.example` to `.env` inside `backend`.
   - Add your Gemini API key to `GEMINI_API_KEY`.
   - Keep the key private; do not commit `.env` to GitHub.
   - Without a key, the app still works using the built-in rule-based demo assistant.

7. Start the backend:

```bash
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

8. Open a second terminal and serve the frontend:

```bash
cd frontend
python -m http.server 5500
```

9. Open `http://127.0.0.1:5500` in Chrome or Edge.
10. Click **AI Voice KAM**, allow microphone access, and speak.

Do not open `index.html` directly with `file://`; use the local web server.

## Demo conversation to record

1. Open Overview and show the month-over-month seller metrics.
2. Open AI Voice KAM and click the microphone.
3. Say: "My sales have dropped significantly this month. Can you help me?"
4. Ask: "Why do you think orders are down?"
5. Ask: "What should I do about cancellations?"
6. Ask: "Can you give me a recovery plan?"
7. Click End conversation to hear the summary.
8. Show the Action Planner and tick an action to demonstrate task tracking.

## Architecture

```text
Seller (browser microphone)
        |
        v
Web Speech API (speech-to-text)
        |
        v
Frontend JavaScript
        |
        v
FastAPI /api/chat
        |
        +---- Optional Gemini LLM
        |
        +---- Rule-based fallback
        |
        v
Seller metrics + business diagnosis + action plan
        |
        v
Frontend conversation and action planner
        |
        v
SpeechSynthesis API (text-to-speech)
```

## AI and voice technology note

- **LLM:** Google Gemini (optional, configured with `GEMINI_API_KEY`) for natural conversational responses grounded in the supplied seller metrics.
- **Fallback reasoning:** Python rule-based intent handling and deterministic metric calculations. This keeps the prototype demonstrable without an API key.
- **Speech-to-text:** Browser Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`), configured for `en-IN`.
- **Text-to-speech:** Browser SpeechSynthesis API, configured for Indian English.
- **Backend:** FastAPI exposes dashboard, chat and summary endpoints.
- **Business logic:** Python computes percentage changes and creates prioritised recommendations from the mock dataset.

## Limitations / honest demo notes

- Browser speech recognition support varies. Use Chrome or Edge and allow microphone access.
- Browser speech recognition may use the browser vendor's online recognition service; this prototype does not host its own speech model.
- Gemini requires a valid API key and internet access. Demo-rules mode works without it.
- The action planner is a local prototype checklist; it does not modify live seller data.
- The seller metrics are mock data supplied for the assignment.
