# StatusPulse Monitoring Setup for ChurnPilot

This document describes how to set up StatusPulse to monitor ChurnPilot's production and experiment URLs.

## Overview

**StatusPulse** is our uptime monitoring service built on Cloudflare Workers. It checks URLs on a regular schedule and alerts when they go down.

**What we want to monitor:**
1. Production: https://churnpilot.streamlit.app
2. Experiment: https://churncopilothendrix-j9sadpe83mwj34ha7kfgqw.streamlit.app

## Current Status

As of 2026-02-05, StatusPulse is **not yet deployed** to Cloudflare Workers. The code exists in `projects/statuspulse/worker/` but has not been published.

## Prerequisites

Before StatusPulse can monitor ChurnPilot, the following must be completed:

### 1. Deploy StatusPulse Worker to Cloudflare

**Location:** `projects/statuspulse/worker/`

**Steps:**
```bash
cd projects/statuspulse/worker/

# Install dependencies
npm install

# Set up Cloudflare secrets (one-time setup)
npx wrangler secret put SUPABASE_URL
# Enter: https://iwekqsxshzadzxezkrxo.supabase.co

npx wrangler secret put SUPABASE_SERVICE_KEY
# Enter: <your-supabase-service-key-from-.env>

# Deploy to Cloudflare Workers
npx wrangler deploy
```

**What this does:**
- Deploys the monitoring engine to Cloudflare's edge network
- Sets up a cron trigger to run checks every 5 minutes
- Connects to StatusPulse's Supabase database to read monitor configs and write results

**Cloudflare Account:**
- Account ID: `213fb8bf311bea879989652b6a0c938c`
- API Token: Already configured in `.env`

### 2. Add ChurnPilot Monitors to StatusPulse Database

**Option A: Via StatusPulse Dashboard**

1. Visit https://statuspulse.streamlit.app (once deployed)
2. Create an account or sign in
3. Add monitors:
   - **Production Monitor:**
     - Name: "ChurnPilot Production"
     - URL: https://churnpilot.streamlit.app
     - Check interval: 5 minutes (free tier)
     - Expected status: 200
   - **Experiment Monitor:**
     - Name: "ChurnPilot Experiment"
     - URL: https://churncopilothendrix-j9sadpe83mwj34ha7kfgqw.streamlit.app
     - Check interval: 5 minutes (free tier)
     - Expected status: 200

**Option B: Direct Database Insert**

```sql
-- Connect to StatusPulse's Supabase database
-- (using credentials from projects/statuspulse/.env)

-- Get your user ID first
SELECT id FROM users WHERE email = 'hendrix.ai.dev@gmail.com';

-- Insert production monitor
INSERT INTO monitors (user_id, name, url, check_interval_seconds, is_active)
VALUES (
    '<your-user-id>',
    'ChurnPilot Production',
    'https://churnpilot.streamlit.app',
    300,  -- 5 minutes
    true
);

-- Insert experiment monitor
INSERT INTO monitors (user_id, name, url, check_interval_seconds, is_active)
VALUES (
    '<your-user-id>',
    'ChurnPilot Experiment',
    'https://churncopilothendrix-j9sadpe83mwj34ha7kfgqw.streamlit.app',
    300,  -- 5 minutes
    true
);
```

### 3. Configure Alerts

**Email Alerts:**

StatusPulse can send email alerts when monitors go down. To enable:

```bash
cd projects/statuspulse/worker/

# Set SMTP credentials (Gmail)
npx wrangler secret put SMTP_EMAIL
# Enter: hendrix.ai.dev@gmail.com

npx wrangler secret put SMTP_PASSWORD
# Enter: <your-gmail-app-password>
```

**Note:** You'll need to generate a Gmail App Password:
1. Go to https://myaccount.google.com/apppasswords
2. Create a new app password for "StatusPulse"
3. Use that password (not your regular Gmail password)

## Verification

Once deployed, verify StatusPulse is monitoring ChurnPilot:

1. **Check worker deployment:**
   ```bash
   cd projects/statuspulse/worker/
   npx wrangler tail
   ```
   You should see check logs every 5 minutes.

2. **Manual trigger (for immediate test):**
   ```bash
   curl -X POST https://statuspulse-monitor.<your-subdomain>.workers.dev/check \
     -H "Authorization: Bearer <your-supabase-service-key>"
   ```

3. **View results in dashboard:**
   - Go to https://statuspulse.streamlit.app
   - Sign in
   - You should see both ChurnPilot monitors with their status

4. **Test alert (optional):**
   - Temporarily mark a monitor as down in the database
   - Verify you receive an email alert
   - Restore the monitor status

## Monitoring Schedule

**Free Tier (Current):**
- Checks every 5 minutes
- 24-hour history
- Email alerts

**Pro Tier (Future):**
- Checks every 1 minute
- 90-day history
- Email + webhook alerts
- Response time charts

## What Happens When ChurnPilot Goes Down?

1. **Detection:** StatusPulse worker checks the URL and gets a non-200 response (or timeout)
2. **Incident Creation:** Creates an incident record in the database
3. **Alert Sent:** Sends email to hendrix.ai.dev@gmail.com
4. **Dashboard Update:** Public status page shows "DOWN" status
5. **Recovery Detection:** When URL returns 200, marks incident as resolved and sends recovery email

## Cost

**Cloudflare Workers Free Tier:**
- 100,000 requests/day
- 10ms CPU time per request
- Unlimited cron triggers

**Current usage:**
- 2 monitors × 12 checks/hour = 24 checks/hour = 576 checks/day
- Well within free tier limits

**Supabase Free Tier:**
- StatusPulse uses its own Supabase instance (separate from ChurnPilot)
- 500MB database (plenty for monitoring data)
- 50,000 monthly active users (we need 1)

## Troubleshooting

**If checks aren't running:**
1. Check worker logs: `npx wrangler tail`
2. Verify cron triggers are enabled in Cloudflare dashboard
3. Check Supabase connection (SUPABASE_URL and SUPABASE_SERVICE_KEY)

**If alerts aren't sending:**
1. Check SMTP credentials are set correctly
2. Verify Gmail app password is valid
3. Check worker logs for email send errors

**If monitors show constant DOWN:**
1. Verify URLs are accessible from Cloudflare's edge network
2. Check if Streamlit has IP blocking (unlikely but possible)
3. Increase timeout in monitor config (default is 10 seconds)

## Next Steps

1. ✅ Deploy StatusPulse worker to Cloudflare (one-time setup)
2. ✅ Add ChurnPilot monitors via dashboard or SQL
3. ✅ Configure email alerts
4. ✅ Verify monitoring is working
5. 📅 Set up weekly/monthly uptime reports (future enhancement)

## Related Files

- Worker code: `projects/statuspulse/worker/src/index.js`
- Dashboard: `projects/statuspulse/app.py`
- Database schema: `projects/statuspulse/schema.sql`
- Monitoring engine (old): `projects/statuspulse/monitor_engine.py` (deprecated, replaced by worker)

---

**Last Updated:** 2026-02-05  
**Status:** Documentation complete, deployment pending
