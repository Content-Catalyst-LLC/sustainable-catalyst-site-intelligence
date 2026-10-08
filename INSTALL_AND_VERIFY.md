# Site Intelligence v4.55.3.2.1 — Install & Verify

Deploy the backend first, verify release identity and canonical `/health`, then deploy the standalone web application on loopback port 8096.

The release is a corrective runtime/context patch. Optional domain failures may truthfully report **degraded**; they must not make the site report **offline** while `/health` is reachable. Economics may truthfully report zero records until v4.55.4 activates substantive domain data.

See `docs/V455321_INSTALL_AND_VERIFY.md` for the complete procedure.
