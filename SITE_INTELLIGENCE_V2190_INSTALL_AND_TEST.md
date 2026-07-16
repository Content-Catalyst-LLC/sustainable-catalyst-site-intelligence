# Site Intelligence v2.19.0 — Installation and Validation

## Release

**Cross-Domain Knowledge Graph and Relationship Explorer**

## Required files

Place these files directly in `~/Downloads`:

- `sustainable-catalyst-site-intelligence-v2.19.0-repo.zip`
- `install_and_push_site_intelligence_v2_19_0.sh`

## Install, validate, commit, and push

```bash
cd ~/Downloads
chmod 700 install_and_push_site_intelligence_v2_19_0.sh
bash ./install_and_push_site_intelligence_v2_19_0.sh
```

The installer:

1. Verifies the packaged immutable-file manifest.
2. Creates a safety archive and safety branch for the current checkout.
3. Resets the local checkout to `origin/main`.
4. Applies the v2.19.0 repository overlay.
5. Creates an isolated Python validation environment.
6. Installs production and development validation dependencies, including HTTPX2.
7. Redirects all writable runtime paths outside the repository.
8. Runs the complete backend regression suite.
9. Runs the v2.19.0 release validator and syntax checks.
10. Re-verifies the immutable manifest after testing.
11. Builds the WordPress plugin ZIP.
12. Commits and pushes through authenticated GitHub CLI or SSH credentials without interactive username prompts.

## Render deployment order

1. Run the installer and confirm the Git push completes.
2. Open the Site Intelligence service in Render.
3. Choose **Manual Deploy → Clear build cache & deploy**.
4. Confirm the deployed commit is the new v2.19.0 commit.
5. Verify:

```bash
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/health | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/release | python3 -m json.tool
curl -s https://sustainable-catalyst-site-intelligence.onrender.com/public/knowledge-graph | python3 -m json.tool
```

6. Install the v2.19.0 WordPress plugin only after `/health` and `/release` both report `2.19.0`.

## WordPress shortcodes

Public relationship explorer:

```text
[sc_public_relationship_explorer]
```

Administrator control center:

```text
[sc_knowledge_graph_control_center]
```

## Persistence

The zero-cost default remains file-backed. For production persistence across Render replacement and redeployment, set all knowledge-graph runtime paths to a durable disk or another persistent storage layer:

- `SC_SI_KNOWLEDGE_GRAPH_ROOT_PATH`
- `SC_SI_KNOWLEDGE_GRAPH_ENTITIES_PATH`
- `SC_SI_KNOWLEDGE_GRAPH_RELATIONSHIPS_PATH`
- `SC_SI_KNOWLEDGE_GRAPH_ALIASES_PATH`

## Responsible-use boundary

Graph proximity, degree, sequence, centrality, or path length is not evidence of causation, importance, influence, responsibility, or risk. Entity reconciliation is preview-only and requires human review.
