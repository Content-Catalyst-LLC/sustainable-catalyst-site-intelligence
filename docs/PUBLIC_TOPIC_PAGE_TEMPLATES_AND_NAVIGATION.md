# Public Topic Page Templates and Navigation — v1.1.1

Site Intelligence v1.1.1 polishes the public topic page system introduced in v1.1.0.
It does not add a new data source layer. It locks in the public page structure,
canonical `/platform/site-intelligence/` paths, navigation helpers, metadata guidance,
and visual QA support for the public dashboard pages.

## Canonical public pages

```text
/platform/site-intelligence/
/platform/site-intelligence/dashboards/
/platform/site-intelligence/climate-energy/
/platform/site-intelligence/environmental-monitoring/
/platform/site-intelligence/biodiversity-land-use/
/platform/site-intelligence/knowledge-system/
/platform/site-intelligence/search-discovery/
/platform/site-intelligence/source-methodology/
```

## New public endpoints

```text
/public/navigation
/public/page-templates
/public/topic-page-visual-qa
```

Private review endpoints are also available:

```text
/intelligence/public-topic-page-templates
/intelligence/public-topic-page-visual-qa
```

## New WordPress shortcodes

```text
[sc_public_dashboard_navigation]
[sc_public_topic_page_templates]
[sc_public_topic_page_visual_qa]
```

The navigation shortcode accepts an optional active page slug:

```text
[sc_public_dashboard_navigation current="climate-energy"]
```

## Existing public topic shortcodes

```text
[sc_public_dashboard_directory]
[sc_public_climate_energy_dashboard]
[sc_public_environmental_monitoring_dashboard]
[sc_public_biodiversity_land_use_dashboard]
[sc_public_knowledge_system_dashboard]
[sc_public_search_discovery_dashboard]
[sc_public_source_methodology]
```

## Page-building guidance

Use the custom `cc-platform-v5 ccp-site-intelligence-public` page shell for public pages.
Place the topic shortcode inside a `.ccp-live-shell ccp-site-intelligence-shell` container.
Do not nest `[sc_site_intelligence_public_flagship]` inside custom page HTML.

## Navigation polish

The WordPress asset layer now marks active links on Site Intelligence, Platform, and
homepage surfaces when a link matches the current pathname. The active state is visual
only and does not change destination URLs.

## Text wrapping polish

Use the helper classes only around short product names or phrases that should not split:

```html
<span class="cch-nowrap">Knowledge Library</span>
<span class="ccp-nowrap">Site Intelligence</span>
<span class="scsi-nowrap">Source Methodology</span>
```

Avoid applying nowrap to whole paragraphs or long headings because that can cause mobile overflow.
