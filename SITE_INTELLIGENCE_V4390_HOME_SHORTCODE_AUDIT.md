# v4.39.0 Homepage Shortcode Audit

## Separation of responsibilities

| Surface | Shortcode | Runtime behavior |
| --- | --- | --- |
| Homepage snapshot | `[sc_site_intelligence_home]` | Lightweight HTML shell plus one bounded JSON request; no iframe |
| Full Site Intelligence page | `[sc_site_intelligence_app height="900"]` | Full application iframe |

## Verified boundaries

- Country-profile and source counts come from repository registries.
- Current signal count equals the returned bounded highlight set.
- No live signal is synthesized when sources return no records.
- All highlights preserve a source label, freshness state, and context destination when supplied.
- The shortcode remains navigable if JavaScript or the summary request is unavailable.
- The summary does not boot the full public application.
- The component does not add a second account, private storage, or visitor profiling surface.

## Homepage placement

Place the shortcode as a major Platform showcase below the homepage introduction or platform overview:

```text
[sc_site_intelligence_home]
```
