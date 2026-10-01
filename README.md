# MM2 Base

MM2 Base is a public website for a Discord-based Murder Mystery 2 (Roblox) middleman service. It is designed to help visitors understand the service, verify middlemen, review community history, and access public information in a read-only, static format.

## Project purpose

This website promotes trusted middleman verification for MM2 trades and acts as a community-facing hub for:

- middleman discovery
- profile verification
- public vouch history
- community statistics
- rules and scam awareness
- Discord invite access

This is not an item-value site or trade calculator. It is focused on middleman trust and verification.

## Tech stack

- HTML5
- CSS3
- Vanilla JavaScript
- Supabase CDN client
- Vercel static hosting

## File structure

- /index.html — landing page
- /lookup/index.html — lookup tool
- /mms/index.html — active middlemen directory
- /mm/index.html — a single middleman profile
- /stats/index.html — community statistics and trends
- /vouches/index.html — public vouch history
- /rules/index.html — community rules and scam guidance
- /admin/index.html — temporary client-side admin interface
- /styles.css — shared styling
- /app.js — shared utilities and Supabase setup
- /config.js — public Supabase configuration
- /vercel.json — Vercel rewrite configuration

## Supabase setup

The public Supabase configuration lives in /config.js and is initialized as:

window.MM2_BASE_CONFIG = {
  supabaseUrl: "https://yklkxobuaxfswbcgdfno.supabase.co",
  supabaseAnonKey: ""
};

The anon/publishable key should be inserted there when available. The website intentionally does not use or expose any service-role key in client-side code.

Never place a service-role key in this repository.

## Database behavior

All Supabase access is read-only except for site_config.

This project must never perform writes to any table other than site_config. The admin panel is the only place that may write to the site_config table, and it should be treated as a temporary, client-side tool.

## Admin panel

The admin page uses a temporary client-side password gate with the password:

mm2admin

This is not secure authentication. It is only a lightweight placeholder while the site is being built and deployed as a static front end. It must not be treated as secure authentication or used for sensitive administration.

## Deployment

This repository is designed to be deployed directly to Vercel as a static site. No application server or build pipeline is required.

## Logo

The file /logo.png is intentionally not included in this repository yet and will be uploaded later. The site is designed to render gracefully without it.
