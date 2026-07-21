# Site Intelligence v3.15.0 — Install and Test

## Install and push

Place the release bundle in `~/Downloads`, then run:

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.15.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_15_0.sh
./install_and_push_site_intelligence_v3_15_0.sh
```

The default installer gate runs the publication-release, change-history, and v3.15.0 public-archive integration tests plus the current release contract and static checks.

To run the complete regression suite during installation:

```bash
SC_SI_FULL_TESTS=1 ./install_and_push_site_intelligence_v3_15_0.sh
```

To rehearse locally without pushing:

```bash
SC_SI_SKIP_PUSH=1 SC_SI_SKIP_PIP_INSTALL=1 \
SC_SI_TARGET_DIR=/path/to/disposable/repository \
SC_SI_REPO_URL=/path/to/disposable/bare.git \
./install_and_push_site_intelligence_v3_15_0.sh
```

## Deploy

1. Deploy the latest `main` commit to the existing Render service.
2. Upload and activate `sustainable-catalyst-site-intelligence-v3.15.0-wordpress.zip` in WordPress.
3. Clear WordPress, Cloudflare, and browser caches.
4. Confirm `/public/build-info` and the WordPress plugin both report `3.15.0`.
5. Add the archive surface where appropriate:

```text
[sc_live_intelligence_public_archive]
```

## Public verification

```text
GET /public/live-intelligence/archive/policy
GET /public/live-intelligence/archive/status
GET /public/live-intelligence/archive
GET /public/live-intelligence/archive/{archive_id}
GET /public/live-intelligence/archive/sources/{source_id}
```

The system exposes read-only approved archive records only. It performs no source mutation, archive deletion, destination write, or remote deposit.
