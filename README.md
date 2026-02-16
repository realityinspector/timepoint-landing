# TIMEPOINT Landing Page

Static teaser landing page for TIMEPOINT — an AI-powered historical scene generator.

## Stack

- Pure HTML + CSS (no JavaScript, no build step)
- nginx:alpine container
- Deployed on Railway

## Local Development

Open `index.html` in a browser, or:

```bash
docker build -t timepoint-landing .
docker run -p 8080:8080 timepoint-landing
```

## Deployment

Push to `main` — Railway auto-deploys to dev and production.

## Rollback

To restore the full API backend:

```bash
git push origin archive/v2-api-backend:main --force
```
