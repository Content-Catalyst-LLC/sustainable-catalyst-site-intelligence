# Site Intelligence v2.16.0 Installation and Test Guide

## Install

Place these files in `~/Downloads`:

- `sustainable-catalyst-site-intelligence-v2.16.0-repo.zip`
- `install_and_push_site_intelligence_v2_16_0.sh`

Run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_16_0.sh
bash ./install_and_push_site_intelligence_v2_16_0.sh
```

The installer creates a safety archive and backup branch, resets the local repository to `origin/main`, installs the release overlay, creates an isolated Python environment, proves HTTPX2/TestClient compatibility, runs all tests and release checks, packages the WordPress plugin, commits, rebases, and pushes without an interactive GitHub username prompt.

## Render

After the push, use **Manual Deploy → Clear build cache & deploy**. Confirm:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/harmonization | python3 -m json.tool
```

All version-bearing responses should report `2.16.0`.

## WordPress

Install `sustainable-catalyst-site-intelligence-v2.16.0-wordpress.zip` only after backend parity is confirmed. Test:

```text
[sc_public_comparable_series]
[sc_statistical_harmonization_control_center]
```

The second shortcode is administrator-only.

## Persistence

The default engine is file-backed. Configure the statistical harmonization root and index paths on durable storage if source series and lineage receipts must survive Render replacement or redeployment.
