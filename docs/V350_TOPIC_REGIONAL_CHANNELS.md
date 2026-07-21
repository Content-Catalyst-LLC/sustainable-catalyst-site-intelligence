# Site Intelligence v3.5.0 — Topic and Regional Channels

## Channel contract

Live Intelligence channels are named, public-safe filters over the existing signal service. They reuse source operations, clustering, ranking, context pages, evidence records, mobile controls, and cache behavior.

Built-in channels include global, Earth systems, weather and climate, humanitarian conditions, economy/energy/resources, science and research, infrastructure and resilience, Africa, the Americas, Asia-Pacific, Europe, and the Middle East and North Africa.

Country and region filters use explicit source-supplied country codes, country names, region names, and location text. Coordinates alone are not converted into a country assignment.

## Shortcodes

```text
[sc_live_intelligence channel="earth-systems"]
[sc_live_intelligence channel="humanitarian" region="africa"]
[sc_live_intelligence channel="global" country="KEN"]
```

## Empty results

An empty regional or country result remains empty. The service does not silently replace it with unrelated global signals.

## Boundaries

Channels are not exhaustive situation reports, geopolitical classifications, truth certification, severity ratings, or causal analysis.
