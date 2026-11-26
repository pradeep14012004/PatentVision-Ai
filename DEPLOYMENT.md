# Cloud deployment (no Vercel)

This repository deploys the Next.js frontend to Cloudflare Workers and the FastAPI backend to a Hugging Face Docker Space. GitHub Actions runs both deployments after pushes to `main`.

## 1. Create the Hugging Face Space

1. Create a **Docker** Space named `patentvision-ai` (or another name you choose).
2. In the Space settings, add:
   - Secret `PV_SECRET_KEY`: a random secret of at least 32 characters.
   - Variable `PV_CORS_ORIGINS`: the exact Cloudflare Worker origin, e.g. `https://patentvision-ai.<your-workers-subdomain>.workers.dev`.
   - Variable `PV_STORAGE_BACKEND`: `supabase` for persistent uploads.
   - Secret `PV_SUPABASE_URL`: your Supabase project URL.
   - Secret `PV_SUPABASE_SERVICE_KEY`: your Supabase service-role key.
   - Secret `DATABASE_URL`: a persistent PostgreSQL connection string (Supabase or Neon).
3. Create a private Supabase Storage bucket named `patentvision-files` (or set `PV_SUPABASE_BUCKET` to your bucket name).

SQLite and local file storage in a hosted Space are not durable across rebuilds/restarts. Configure PostgreSQL and Supabase Storage before using this for real project data.

## 2. Configure GitHub Actions

In **Repository → Settings → Secrets and variables → Actions**, add:

**Repository variables**
- `HF_SPACE`: Hugging Face Space identifier, exactly `username/space-name`.
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account ID.

**Repository secrets**
- `HF_TOKEN`: Hugging Face token with write access to the Space.
- `CLOUDFLARE_API_TOKEN`: Cloudflare API token with Workers Scripts edit permission.

The Cloudflare Worker name is `patentvision-ai`. Its public URL will be `https://patentvision-ai.<your-workers-subdomain>.workers.dev`. Add that origin to `PV_CORS_ORIGINS` in the Space settings (no trailing slash).

## 3. Deploy

Push to `main`, or open **Actions → Deploy PatentVision AI → Run workflow**. The workflow pushes the repository Docker app to Hugging Face, builds the Next.js app with the Space API URL, and deploys the Worker.

Backend API base URL is `https://<username>-<space-name>.hf.space/api`.

## 4. Verify

- Backend health: `https://<username>-<space-name>.hf.space/health`
- Frontend: `https://patentvision-ai.<your-workers-subdomain>.workers.dev`

Wait for the Space to finish its first Docker build before testing login and uploads. Keep the HF Space and Cloudflare Worker public if the app is intended for public access.
