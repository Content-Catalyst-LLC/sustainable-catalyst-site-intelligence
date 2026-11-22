# Isolated development activation

Base production Compose defaults remain unchanged. Use a distinct project name:

```sh
# Create .env.dev from .env.dev.example; generate new secrets locally.
# Never copy production credentials. Keep .env.dev private and excluded from Git.
docker compose --env-file .env.dev -p sc-dev-site-intelligence -f compose.yml -f compose.dev.yml config --quiet
docker compose --env-file .env.dev -p sc-dev-site-intelligence -f compose.yml -f compose.dev.yml up -d --build
```

Requires existing external development network `sc-internal`. Build one module at a time on ARM64. Existing Workbench, Workspace and WordPress containers must not be recreated. Published ports bind loopback only. Service tokens and signing secrets are development-specific; no production identity is accepted automatically.

Rollback: run the same Compose command with `stop` for this module only. Keep named volumes and `.env.dev` for recovery; never use `down -v`. Connector credentials and datasets are independent acceptance gates. A healthy API does not certify external providers or authenticated cross-product actions.
