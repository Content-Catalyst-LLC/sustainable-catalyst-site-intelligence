# Publishing Intelligence

Site Intelligence v0.4.0 adds a planning layer for Sustainable Catalyst publishing and platform development.

## Purpose

Publishing Intelligence connects:

- GA4 page behavior
- Search Console visibility
- Sustainable Catalyst registry metadata
- Repository clicks
- Workbench events
- Research Librarian events
- Pathway continuation events
- Prior-period comparison windows

It produces an internal action queue for updates, promotion, newsletter topics, article-map improvements, and platform CTA placement.

## Endpoints

```text
/publishing/content-strategy
/publishing/topic-momentum
/publishing/update-priorities
/publishing/promotion-opportunities
/intelligence/publishing
```

## Default comparison windows

```text
Current: 28daysAgo to yesterday
Prior:   56daysAgo to 29daysAgo
```

You can override these with:

```text
start_date
end_date
prior_start_date
prior_end_date
limit
```

## Shortcodes

```text
[sc_content_strategy_intelligence]
[sc_topic_momentum]
[sc_update_priorities]
[sc_publishing_opportunities]
```

Optional attributes:

```text
start_date="28daysAgo"
end_date="yesterday"
prior_start_date="56daysAgo"
prior_end_date="29daysAgo"
limit="20"
```

## Interpretation notes

Publishing scores are directional planning metrics. They are designed to help decide what to update, promote, connect, or expand. They are not official Google metrics, rankings, or editorial mandates.

Keep the full publishing action queue private until public dashboard mode exists, because it may expose internal strategy gaps and conversion weaknesses.
