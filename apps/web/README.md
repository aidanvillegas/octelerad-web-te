# Web Application

Next.js App Router interface for the Macro Library. Provides authentication, snippet listing/search, audit history, and export actions against the FastAPI backend.

## Local development

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`) when pointing at a remote API.

## Tests

Playwright powers the smoke tests. Install browsers once (`npx playwright install`) and run:

```bash
npm test
```

## Production build

```bash
npm run build
npm run start
```

Docker builds use the same scripts (see `infra/docker/web.Dockerfile`).
