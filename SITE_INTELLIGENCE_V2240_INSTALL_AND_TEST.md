# Site Intelligence v2.24.0 Installation and Testing

## Install and push

Place these files directly in `~/Downloads`:

- `sustainable-catalyst-site-intelligence-v2.24.0-repo.zip`
- `install_and_push_site_intelligence_v2_24_0.sh`

Run:

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_24_0.sh
bash ./install_and_push_site_intelligence_v2_24_0.sh
```

The installer creates a safety archive and Git branch, resets the local repository to `origin/main`, installs the release overlay, verifies the immutable manifest, creates an isolated Python environment, proves TestClient compatibility, runs the complete regression suite, checks Python/JSON/JavaScript/PHP syntax, packages the WordPress plugin, commits, rebases, and pushes through GitHub CLI or SSH without an interactive username prompt.

## Deploy

After the push completes:

1. In Render, use **Manual Deploy → Clear build cache & deploy**.
2. Confirm `/health` and `/release` report `2.24.0`.
3. Confirm `/public/institutional-data-exchange` responds.
4. Confirm `/public/institutional-data-exchange/catalog?format=jsonld` returns a catalog.
5. Install the v2.24.0 WordPress plugin only after backend parity is confirmed.

## WordPress shortcodes

```text
[sc_public_institutional_data_exchange]
```

```text
[sc_institutional_data_exchange_control_center]
```

The control-center shortcode is administrator-only.

## Persistent storage

The file-backed exchange requires a durable Render disk or another persistent configured path for institutions, records, manifests, trust policies, and import receipts to survive replacement deployments. Store `SC_SI_FEDERATION_SIGNING_KEY` as a private Render secret; never place it in WordPress, public manifests, or source control.

## Responsible-use checks

- Remote catalogs are not fetched automatically.
- Imports require preview and `confirm=true`.
- Invalid or blocked manifests are quarantined.
- A signature verifies integrity only with a trusted key and does not independently prove institutional identity.
- Hosted, mirrored, and referenced records remain distinct.
- Private records, trust policies, import receipts, and signing keys remain outside public responses.
