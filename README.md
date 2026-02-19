# TIMEPOINT Landing Page

Static landing page for TIMEPOINT AI at `timepointai.com`.

## Stack

- Pure HTML + CSS (single file, no build step)
- nginx:alpine container
- Deployed on Railway

## Local Development

Open `index.html` in a browser, or:

```bash
docker build -t timepoint-landing .
docker run -p 8080:8080 timepoint-landing
```

## Deployment

Push to `main` — Railway auto-deploys.
