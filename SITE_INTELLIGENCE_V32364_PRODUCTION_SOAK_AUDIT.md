# Site Intelligence v3.23.7 Production Soak Audit

The release separates shell readiness from data hydration, bounds effective request retries, serializes route transitions, and closes the service-worker update lifecycle so no controller change can force a current-session reload.

The mandatory Chromium gate runs the complete shipped script chain with service workers disabled and with registration failure, opens the shell within the bounded startup gate, rotates routes repeatedly, and verifies that the launch screen remains closed and the automatic reload count remains zero.
