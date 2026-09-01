# Site Intelligence v4.39.0 R1 — Install and Test

## WordPress

1. Install the R1 WordPress ZIP and choose **Replace current with uploaded**.
2. Confirm the installed plugin version remains `4.39.0`.
3. Keep `[sc_site_intelligence_home]` on the homepage.
4. Clear WordPress/page caches and hard-refresh while logged out.

## Homepage checks

- The Earth, Space, and Ocean imagery triptych appears beside the Site Intelligence introduction.
- The original Live Intelligence ticker moves inside the console and is not duplicated above the page.
- Pause, hover/focus pause, reduced-motion, and mobile behavior remain available.
- The online state, four coverage metrics, current signal cards, three entry points, refresh text, and primary CTA populate normally.
- Each image-credit link opens its official source page.

## Release gate

No backend deployment is required. Both sides remain at `4.39.0`, so the WordPress release gate should remain ready.

## GitHub

Use `SITE_INTELLIGENCE_V4390_R1_TERMINAL_COMMANDS.txt`. The installer validates, applies, commits, tags `v4.39.0-r1`, and pushes the current branch and tag.
