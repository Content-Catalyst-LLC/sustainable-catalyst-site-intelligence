# Site Intelligence v2.8.0 Installation and Test Guide

Run the provided installer from `~/Downloads`. It resets the local repository to `origin/main`, applies the verified v2.8.0 repository archive, creates an isolated Python test environment when required, runs the full backend regression suite and syntax checks, scans for secrets, builds the WordPress package, commits, rebases, and pushes.

After Render redeploys, verify `/health` reports `2.8.0`, open `/app/?view=alerts`, create a local rule, reconnect the stream, generate a digest, and install the matching WordPress plugin.
