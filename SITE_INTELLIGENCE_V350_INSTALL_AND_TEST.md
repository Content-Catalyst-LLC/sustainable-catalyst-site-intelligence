# Site Intelligence v3.5.0 install and test

1. Run the macOS installer from `~/Downloads`.
2. Confirm the full regression suite and release contract pass.
3. Deploy the latest `main` commit on Render.
4. Upload the generated v3.5.0 WordPress ZIP.
5. Open **Settings → SC Site Intelligence → Live Intelligence** and choose a default channel.
6. Test `[sc_live_intelligence channel="earth-systems"]`, `[sc_live_intelligence channel="humanitarian" region="africa"]`, and a country-filtered shortcode.
7. Confirm an unmatched country returns an honest empty state rather than global signals.
