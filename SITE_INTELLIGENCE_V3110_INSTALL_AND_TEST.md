# Site Intelligence v3.13.0 — Install and Test

```bash
cd ~/Downloads
unzip -o sustainable-catalyst-site-intelligence-v3.13.0-release-bundle.zip
chmod +x install_and_push_site_intelligence_v3_11_0.sh
./install_and_push_site_intelligence_v3_11_0.sh
```

The installer verifies the repository archive checksum and immutable manifest, overlays the release into the detected repository, runs the chained regression suite, validates Python/JSON/HTML/JavaScript/PHP, rebuilds the WordPress ZIP, commits the release, and pushes unless `SC_SI_SKIP_PUSH=1` is set.

WordPress review surface:

```text
[sc_live_intelligence_editorial_workspace]
```

After deploying the backend, verify:

```text
GET /public/live-intelligence/editorial/policy
GET /public/live-intelligence/editorial/status
GET /admin/live-intelligence/editorial
```
