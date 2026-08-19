# A.S.T.A. Frontend

Vite + React frontend, matching the directory structure and stack described
in the system architecture doc (Section 3 & 5).

## Setup

```bash
npm install
cp .env.example .env   # fill in your Firebase project's values
npm run dev
```

Enable the **Google** sign-in provider in Firebase Console → Authentication →
Sign-in method, and add your dev/prod domains under Authentication →
Settings → Authorized domains (`localhost` is allowed by default).

## Talking to the backend

`vite.config.js` proxies `/api/*` to `http://localhost:8000` in development,
matching the FastAPI backend's routes from Section 6 of the architecture doc
(`/api/v1/topics`, `/api/v1/chat/stream`, `/api/v1/vision/crop-analyze`,
`/api/v1/training/*`, `/api/v1/models/*`, `/api/v1/export|import`). Until
that backend exists, every component falls back to a visible
"backend not reachable yet" state instead of failing silently.

## Structure

```
src/
├── main.jsx              entry point
├── App.jsx                shell: auth, tab console, routing between features
├── firebase/config.js     Firebase SDK init (auth, firestore, storage)
├── components/
│   ├── ui/                 shadcn-style primitives (Button, Card)
│   ├── Dashboard.jsx        overview + topic preview
│   ├── TopicManager.jsx     create/list study topics
│   ├── LensScanner.jsx      ROI visual inquiry (Gemini Vision)
│   ├── ChatWindow.jsx       grounded SSE chat
│   └── ModelTrainerModal.jsx  dataset upload + .asta-model export/import
├── animations/
│   ├── scanEffects.js       raw GSAP timeline builders
│   └── gsapHooks.js         React hooks wrapping those timelines
├── lib/utils.js            cn() class-merge helper
└── styles/globals.css      Tailwind entry + shared HUD styles
```
