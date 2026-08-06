# Site Intelligence v3.23.3

## Production Truth and Workspace Completion

This release audits and completes the public application route contract introduced by v3.23.0. It does not add another broad feature family. It makes every visible workspace honest about what is available, empty, degraded, or unavailable.

### Public route contract

- Registers all 35 public routes in `/public/workspaces/production-truth`.
- Classifies 19 core analytical workspaces as operational and 16 public or browser-local workspaces as operational within a bounded scope.
- Gives every route explicit initial, ready, empty, degraded, and unavailable states.
- Defines required controllers, visible surfaces, endpoint families, empty-state language, degraded-state language, and limitations.
- Disables a navigation item when its required controller is absent instead of displaying a false-complete workspace.

### Browser completion

- Adds a compact production-state bar to the active workspace.
- Distinguishes an empty result from a source or controller failure.
- Restores supported routes through the `view` query parameter and browser history.
- Moves focus to the active workspace heading after navigation.
- Retries only the active route after service recovery.
- Keeps inactive route controllers closed and prevents their workspace-specific open routines from running.

### Deployment and WordPress

- Adds the production-truth runtime and styles to the offline application shell.
- Packages and enqueues the same assets in WordPress.
- Extends runtime health and the Render promotion gate to verify the live route directory, production-state runtime, app shell, release identity, and WordPress parity.

### Responsible boundary

A route marked operational means its public interface and failure states are implemented. It does not claim that every external source is continuously available or that an empty result proves no real-world condition exists.
