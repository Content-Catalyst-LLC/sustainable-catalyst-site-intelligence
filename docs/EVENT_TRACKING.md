# Sustainable Catalyst Event Tracking

Site Intelligence v0.1.3 validates whether Sustainable Catalyst conversion events are visible in GA4. The WordPress plugin pushes custom events into `window.dataLayer` and also posts an acknowledgement to the Site Intelligence backend. GA4 remains the primary event store.

## Event catalog

| Event | Meaning | Priority |
| --- | --- | --- |
| `sc_repository_click` | GitHub/repository CTA click | High |
| `sc_workbench_open` | Workbench/tool/calculator entry | High |
| `sc_research_librarian_open` | Research Librarian entry | High |
| `sc_decision_studio_open` | Decision Studio entry | Medium |
| `sc_pathway_continue` | Article-map, related-link, or deeper pathway continuation | High |
| `sc_library_nav` | Research Library navigation | Medium |
| `sc_scroll_depth` | 25/50/75/90% scroll thresholds | Medium |

## GTM setup checklist

Create one Custom Event trigger for each event above. Attach each trigger to a GA4 Event tag that sends the same event name to GA4. Then use `[sc_site_intelligence_events]` to verify which events have appeared in GA4.

## Useful HTML attributes

For precise tracking, links can include:

```html
<a href="https://github.com/..." data-scsi-event="sc_repository_click">View repository</a>
<a href="/workbench/" data-scsi-event="sc_workbench_open" data-scsi-tool-id="energy-systems-calculator">Open tool</a>
```

The plugin also detects common link patterns automatically.
