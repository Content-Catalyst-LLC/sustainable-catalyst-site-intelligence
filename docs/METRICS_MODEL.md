# Sustainable Catalyst Metrics Model

The Site Intelligence layer translates generic analytics into site-specific institutional metrics.

## Metric families

### Institutional Depth Score

Measures whether a visitor is engaging with the page as part of a knowledge system rather than bouncing through isolated content.

Inputs:

- engagement rate,
- average session duration,
- pathway continuation events,
- Workbench events,
- Research Librarian events.

### Authority Surface Score

Measures whether a page is functioning as a credible public surface for Sustainable Catalyst.

Inputs:

- pageviews,
- engagement rate,
- repository clicks,
- article map presence,
- repository presence.

### Hub Efficiency Score

Measures whether a hub successfully moves readers into deeper material.

Inputs:

- pathway continuation rate,
- event density,
- engagement rate.

### Repository Conversion

Measures whether GitHub-backed articles are turning readers into repository visitors.

Primary event:

```text
sc_repository_click
```

### Workbench Activation

Measures whether article and hub traffic leads into calculators, scorecards, and advanced tools.

Primary event:

```text
sc_workbench_open
```

### Research Librarian Activation

Measures whether readers use the site-scoped AI assistant as a guided inquiry layer.

Primary event:

```text
sc_research_librarian_open
```

## Why this matters

The goal is not to optimize Sustainable Catalyst only for traffic. The goal is to measure whether the site is becoming an open knowledge lab where ideas become public infrastructure.
