# Site Intelligence v2.6.0 installation and testing

Run the supplied installer from `Downloads`. It creates a safety backup, resets the Git repository to `origin/main`, validates the release manifest, installs v2.6.0, creates an isolated Python test environment when necessary, runs the complete backend suite, performs syntax and secret checks, builds the repository and WordPress ZIPs, commits, rebases, and pushes.

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_6_0.sh
bash ./install_and_push_site_intelligence_v2_6_0.sh
```

After Render deploys, verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/trade-energy-resources/diagnostics | python3 -m json.tool
```

The health response must report version `2.6.0`. The diagnostics response must not expose credentials and must report all advisory and scoring flags as false.
