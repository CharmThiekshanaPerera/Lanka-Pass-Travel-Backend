# SendGrid Troubleshooting (EC2)

This guide helps when OTP emails are sent successfully by the API but users still don't receive them.

## What “202 Accepted” Means
- SendGrid accepted your email request successfully.
- It does **not** guarantee delivery to the recipient inbox.

## Common Reasons Emails Don’t Arrive
- **Spam/Junk folder**: Ask users to check spam.
- **Suppression list**: The recipient email may be blocked/bounced.
- **Unverified sender**: `SENDGRID_FROM_EMAIL` must be verified in SendGrid.
- **Wrong API key**: Key missing `Mail Send` permission or revoked.
- **Recipient address issue**: Invalid or temporary email addresses may be rejected.

## Sender Verification Steps
Use **Single Sender Verification** (fast) or **Domain Authentication** (recommended).

### Single Sender Verification
1. Go to **Settings → Sender Authentication** in SendGrid.
2. Click **Verify a Single Sender**.
3. Add your sender email (e.g., `thiekshana@phyxle.com`).
4. Check your inbox and click the verification link.

### Domain Authentication (Recommended)
1. Go to **Settings → Sender Authentication → Authenticate Your Domain**.
2. Follow the DNS setup instructions (CNAME/TXT records).
3. Click **Verify** after DNS is added.

## Suppression List Check
1. In SendGrid, go to **Email Activity → Suppressions**.
2. Check **Bounces**, **Blocks**, and **Spam Reports**.
3. Remove the recipient email from suppression if needed.

## Safe EC2 Debug Commands (No Secrets)
### Check SendGrid env vars exist
```bash
docker compose -f docker-compose.prod.yml exec -T api env | grep -i sendgrid
```

### Trigger OTP (from EC2)
```bash
curl -X POST http://localhost/api/auth/send-email-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"youremail@example.com"}'
```

### Watch API logs
```bash
docker compose -f docker-compose.prod.yml logs -f --tail=50 api
```

### Test outbound HTTPS to SendGrid
```bash
docker compose -f docker-compose.prod.yml exec -T api python - <<'PY'
import urllib.request
with urllib.request.urlopen("https://api.sendgrid.com", timeout=10) as r:
    print("status", r.status)
PY
```

## Notes
- A **202** response plus “Email OTP sent” in logs means the backend is working.
- If emails still don’t arrive, focus on **sender verification** and **suppression lists**.
