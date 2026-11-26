# Free cloud deployment (no Vercel, no paid Hugging Face Docker)

The application is deployed as:
- **Frontend:** Cloudflare Workers (Next.js via OpenNext).
- **Backend:** Render free Docker web service, built from the root `Dockerfile`.
- **Database and file storage:** Supabase free project (PostgreSQL + private Storage bucket).
- **Automation:** GitHub Actions triggers Render and deploys the Cloudflare Worker on pushes to `main`.

## 1. Create the Render backend

1. Sign in at https://render.com/.
2. Choose **New → Web Service** and connect `pradeep14012004/PatentVision-Ai`.
3. Select branch `main`, runtime **Docker**, Dockerfile path `./Dockerfile`, and plan **Free**.
4. Name the service `patentvision-api`, then create it.
5. In the service settings, copy its public URL (for example `https://patentvision-api.onrender.com`).
6. In Settings, create a **Deploy Hook** and copy its URL.

The free service sleeps after 15 minutes of inactivity and wakes on the next request (often around one minute). Its local filesystem is ephemeral. Do not use local SQLite or local file storage for user data.

## 2. Configure persistent data using Supabase

1. Create a free project at https://supabase.com/.
2. Create a **private** Storage bucket named `patentvision-files`.
3. In Project Settings → API, copy the Project URL and service-role key.
4. In Project Settings → Database, copy the PostgreSQL connection string (URI). Use the pooler connection if the direct connection is not reachable.

Set these environment variables in Render → Environment:
- `PV_SECRET_KEY`: a long random secret (32+ characters).
- `PV_DATABASE_URL`: the Supabase PostgreSQL connection string.
- `PV_STORAGE_BACKEND`: `supabase`.
- `PV_SUPABASE_URL`: Supabase Project URL.
- `PV_SUPABASE_SERVICE_KEY`: Supabase service-role key.
- `PV_SUPABASE_BUCKET`: `patentvision-files`.
- `PV_CORS_ORIGINS`: initially leave until the Cloudflare Worker URL is known; then set it to the exact frontend origin, without a trailing slash.

Keep service-role keys private. Never put them in frontend environment variables.

## 3. Configure GitHub Actions

In **Repository → Settings → Secrets and variables → Actions**, add:

**Repository variable**
- `CLOUDFLARE_ACCOUNT_ID`: your Cloudflare account ID.
- `RENDER_API_URL`: your Render service URL, e.g. `https://patentvision-api.onrender.com` (no `/api` suffix).

**Repository secrets**
- `CLOUDFLARE_API_TOKEN`: Cloudflare API token with Workers Scripts Edit permission.
- `RENDER_DEPLOY_HOOK`: Render deploy hook URL.

The workflow deploys the backend by triggering Render's deploy hook and builds the frontend with `NEXT_PUBLIC_API_URL=<RENDER_API_URL>/api`.

## 4. Deploy and configure CORS

Push to `main`, or open **Actions → Deploy PatentVision AI → Run workflow**.

After the first Cloudflare deployment, the Worker URL is:
`https://patentvision-ai.<your-workers-subdomain>.workers.dev`

Set Render's `PV_CORS_ORIGINS` to that exact origin, save, and redeploy the backend.

## 5. Verify

- Backend health: `<RENDER_API_URL>/health`
- Backend API docs: `<RENDER_API_URL>/docs`
- Frontend: Cloudflare Worker URL shown after deployment.

Free-tier caveats: Render free services sleep after 15 minutes idle and wake slowly; Render's local disk is temporary; free Render Postgres expires after 30 days. Supabase is used here for persistent database and uploaded files. Review free-tier quotas and limits before relying on this for production data.
