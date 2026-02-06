# Fix: Supabase Email Validation Blocking Registration

## Problem
Supabase is rejecting emails as "invalid" even though they appear correctly formatted.

## Solution Options

### Option 1: Disable Email Validation in Supabase (Recommended for Development)

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/azrdrjbrwdahwnkuufvw
2. Navigate to: **Authentication** → **Settings**
3. Scroll to **Email Auth** section
4. Find **Email validation** settings
5. Disable strict validation or add allowed domains

### Option 2: Use Real Email Addresses

Instead of test emails, use:
- Your actual Gmail address
- A temp email service
- Mailinator (vendor@mailinator.com)

### Option 3: Disable Email Confirmation (Backend Fix)

I can modify the code to bypass email confirmation during development.

## Quick Test

Try using:
- `vendor@example.com`
- Your real email address
- `admin@test.local`

If all fail, the issue is in Supabase dashboard settings and you need to go to Option 1.
