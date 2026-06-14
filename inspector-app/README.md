# Inspector — Property Inspection Companion App

A React Native (Expo) app for property hunters: import open-home invites, run
guided room-by-room inspections, sanity-check listings against reality, and
compare properties side by side. Built on Supabase (auth, Postgres, storage)
with Claude for listing intelligence.

> This app lives in `inspector-app/` and is independent of the FPL Streamlit
> tool at the repository root.

## Status

- ✅ **Phase 1 — Project scaffold & auth** (this commit)
- ⬜ Phase 2 — Inspection import & schedule
- ⬜ Phase 3 — Listing intelligence (Claude)
- ⬜ Phase 4 — Photo integrity check (Claude vision)
- ⬜ Phase 5 — Inspection mode
- ⬜ Phase 6 — Post-inspection summary & navigation
- ⬜ Phase 7 — Compare dashboard
- ⬜ Phase 8 — Gamification & contributor system

## Phase 1 — what's built

- Expo + TypeScript project using **expo-router** (file-based routing).
- **Supabase client** with email/password auth and persisted sessions
  (AsyncStorage on native).
- **Login** and **Signup** screens with validation and email-confirmation
  handling.
- **Bottom tab navigation**: Schedule · Inspect · Compare · Profile, gated
  behind authentication.
- **Profile** tab reads the signed-in user's `users` row (contributor score +
  badges), proving the schema and RLS work end to end.
- Design system: dark navy + white base, amber accent — see
  `src/theme/colors.ts`.

### Database (live on Supabase)

Tables, all with **Row Level Security enabled** (a user can only read/write
their own data, enforced via the `inspections.user_id` ownership chain):

| Table | Purpose |
| --- | --- |
| `users` | Profile, contributor score, badges (auto-created on signup) |
| `inspections` | Listing details, schedule time, address, status, ratings |
| `rooms` | Room type and notes per inspection |
| `photos` | File path, source (user/listing), confidence flag |
| `voice_notes` | File path, transcript, transcription status |
| `prompted_answers` | Answers to the prompted question bank |

A trigger (`on_auth_user_created`) inserts a `users` profile row whenever a new
auth user signs up.

## Getting started

```bash
cd inspector-app
npm install
npm start          # then press i / a, or scan the QR with Expo Go
```

### Configuration

Supabase URL and the **publishable** (anon) key are committed in
`app.json -> expo.extra` so the app runs with zero setup. These values are
public by design and protected server-side by RLS. To override locally, copy
`.env.example` to `.env`.

> Never commit the Supabase `service_role` key or other server secrets.
> Claude API calls (Phase 3+) will be proxied through a Supabase Edge Function
> so no model API key ships in the client.

## Project structure

```
inspector-app/
  app/                      # expo-router routes
    _layout.tsx             # root: AuthProvider + auth gatekeeper
    (auth)/                 # login + signup (shown when signed out)
    (tabs)/                 # Schedule · Inspect · Compare · Profile
  src/
    components/             # shared UI (buttons, fields, cards)
    context/AuthContext.tsx # session state + sign in/up/out
    data/questionBank.ts    # prompted question bank (Phase 5)
    lib/supabase.ts         # typed Supabase client
    theme/colors.ts         # design system tokens
    types/database.ts       # DB row types
```
