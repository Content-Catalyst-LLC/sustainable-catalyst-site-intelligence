# Site Intelligence v1.18.1 — Public Feed Notice Removal

The global partial-data banner was removed because optional connector failures could trigger it even when the main application was operating normally.

Failures now remain local to the affected map, chart, export, event, or country panel. The application continues to retry and use explicit local fallback states without displaying a persistent site-wide nag message.
