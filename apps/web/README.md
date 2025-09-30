# Web Application

Next.js App Router interface for the Macro Library public datasets experience. It surfaces the dataset list, handles CSV/JSON import/export, and mirrors realtime edits over WebSockets via AG Grid.

## Local development

    npm install
    npm run dev

Set NEXT_PUBLIC_API_URL (defaults to http://localhost:8000) when pointing at a remote API.

The app is intentionally anonymous. A browser-scoped client id stored in localStorage tags datasets created from that device so they surface under “Created on this browser”.

## Tests

Playwright powers the smoke tests. Install browsers once (npx playwright install) and run:

    npm test

## Production build

    npm run build
    npm run start

Docker builds use the same scripts (see infra/docker/web.Dockerfile).
