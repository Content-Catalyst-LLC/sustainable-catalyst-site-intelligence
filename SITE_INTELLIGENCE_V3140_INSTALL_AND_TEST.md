# Site Intelligence v3.14.0 — Install and Test

## Install and push

Place the release bundle in `~/Downloads`, then run:

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.14.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_14_0.sh
./install_and_push_site_intelligence_v3_14_0.sh
```

The default installer gate runs the publication-release, release-operations, and v3.14.0 change-history integration tests plus the current release contract and static checks.

To run the complete 739-test regression suite during installation:

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_14_0.sh
```

To rehearse locally without pushing:

```bash
SC_SI_SKIP_PUSH=1 SC_SI_SKIP_PIP_INSTALL=1 \
SC_SI_TARGET_DIR=/path/to/disposable/repository \
SC_SI_REPO_URL=/path/to/disposable/bare.git \
./install_and_push_site_intelligence_v3_14_0.sh
```

## Deploy

1. Deploy the latest `main` commit to the existing Render service.
2. Upload and activate `sustainable-catalyst-site-intelligence-v3.14.0-wordpress.zip` in WordPress.
3. Clear WordPress, Cloudflare, and browser caches.
4. Confirm `/public/build-info` and the WordPress plugin both report `3.14.0`.
5. Add the public change-history surface where appropriate:

```text
[sc_live_intelligence_change_history]
```

## Public verification

```text
GET /public/live-intelligence/change-history/policy
GET /public/live-intelligence/change-history/status
GET /public/live-intelligence/change-history
GET /public/live-intelligence/change-history/releases/{release_id}
```

The system publishes read-only history only after separate human approval. It performs no destination rewrite, deletion, or automatic republication.
