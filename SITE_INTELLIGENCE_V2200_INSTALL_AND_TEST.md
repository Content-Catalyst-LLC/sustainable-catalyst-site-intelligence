# Site Intelligence v2.20.0 — Installation and Validation

## Release

**Intelligence Publishing and Story Map Studio**

## Required files

Place these files directly in `~/Downloads`:

- `sustainable-catalyst-site-intelligence-v2.20.0-repo.zip`
- `install_and_push_site_intelligence_v2_20_0.sh`

## Install, validate, commit, and push

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_20_0.sh
bash ./install_and_push_site_intelligence_v2_20_0.sh
```

The installer:

1. Verifies the packaged immutable-file manifest.
2. Creates a safety archive and safety branch for the current checkout.
3. Resets the local checkout to `origin/main`.
4. Applies the v2.20.0 repository overlay.
5. Creates an isolated Python 3.11–3.13 validation environment.
6. Installs tested development dependencies, including HTTPX2.
7. Redirects every writable runtime subsystem outside the repository.
8. Runs the complete backend regression suite.
9. Runs the v2.20.0 release validator and syntax checks.
10. Removes test-generated state and re-verifies the immutable manifest.
11. Builds and verifies the WordPress plugin ZIP.
12. Commits and pushes through authenticated GitHub CLI or SSH credentials without interactive username prompts.

## Render deployment order

1. Run the installer and confirm the Git push completes.
2. Open the Site Intelligence service in Render.
3. Choose **Manual Deploy → Clear build cache & deploy**.
4. Confirm the deployment uses the new v2.20.0 commit.
5. Verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/intelligence-publishing | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/intelligence-publications | python3 -m json.tool
```

6. Install the v2.20.0 WordPress plugin only after `/health` and `/release` both report `2.20.0`.

## WordPress shortcodes

Public intelligence-publication directory:

```text
[sc_public_intelligence_publications]
```

Direct publication embed:

```text
[sc_intelligence_publication publication_id="publication-id"]
```

Administrator publishing control center:

```text
[sc_intelligence_publishing_control_center]
```

## Persistence

The zero-cost default remains file-backed. For publication projects, blocks, reviews, and immutable versions to survive Render replacement and redeployment, configure a persistent disk or another durable storage layer for:

- `SC_SI_INTELLIGENCE_PUBLISHING_ROOT_PATH`
- `SC_SI_INTELLIGENCE_PUBLISHING_PROJECTS_PATH`
- `SC_SI_INTELLIGENCE_PUBLISHING_BLOCKS_PATH`
- `SC_SI_INTELLIGENCE_PUBLISHING_REVIEWS_PATH`
- `SC_SI_INTELLIGENCE_PUBLISHING_VERSIONS_PATH`

## Responsible-use boundary

Publication structure does not establish causation. Public release requires human editorial approval and explicit publish confirmation. Unlisted publications are omitted from public directories but remain available through their exact identifier. WordPress handoffs are read-only.
