# Site Intelligence v3.23.7 Installation and Test Guide

1. Download the v3.23.7 release bundle and macOS installer into `~/Downloads`.
2. Run the installer with the release bundle path.
3. Allow the installer to verify checksums, create an isolated Python environment, run the deterministic validation twice, publish GitHub refs, and wait for the Render release gate.
4. Install the WordPress ZIP only after Terminal reports success.
5. Purge WordPress, hosting, CDN, and browser caches.
6. Test the embedded application in current Chrome or Edge, Safari, and Firefox when available.
7. Test at phone width, keyboard-only navigation, reduced-motion mode, and the Low bandwidth control.

The WordPress host page must not display application diagnostic panels. Browser reliability assets are packaged for the embedded Site Intelligence application and are not enqueued as host-page runtimes.
