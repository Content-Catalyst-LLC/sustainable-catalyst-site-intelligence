# Site Intelligence v1.25.0 — Public Launch and Portfolio Release

## Purpose

v1.25.0 presents Site Intelligence as a coherent public product and portfolio project after the reliability, thematic, methodology, saved-view, accessibility, performance, and mobile releases.

## Public launch route

```text
/app/?view=launch
```

The launch route contains the public positioning statement, primary and secondary calls to action, product-area directory, research workflow, technical architecture, responsible-use boundary, project facts, GitHub link, and downloadable portfolio record.

## Public product structure

The flagship WordPress page should use one primary application embed:

```text
[sc_site_intelligence_app height="1000"]
```

A dedicated launch/portfolio presentation is available through:

```text
[sc_site_intelligence_launch height="1200"]
```

Focused shortcodes remain available for supporting pages. Legacy preview shortcodes remain compatible through v1.x but are scheduled for removal or redesign in v2.0.0.

## Public endpoints

- `GET /public/launch-profile`
- `GET /public/launch-profile/checklist`
- `GET /public/launch-profile/materials`
- `GET /public/launch-profile/diagnostics`
- `GET /public/launch-profile/portfolio?format=json`
- `GET /public/launch-profile/portfolio?format=markdown`

## Portfolio boundary

The portfolio record describes the public project, technical architecture, research workspaces, evidence principles, responsible-use limits, and public links. It does not expose credentials, private connector URLs, environment variables, internal stack traces, or deployment secrets.

## Launch completion boundary

Automated tests and diagnostics verify product contracts. Production deployment, WordPress page composition, screenshots, social preview artwork, and demo recording remain manual launch activities.
