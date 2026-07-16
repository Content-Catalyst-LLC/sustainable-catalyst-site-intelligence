# Site Intelligence v2.20.0 — Intelligence Publishing and Story Map Studio

## Purpose

This release converts approved Site Intelligence evidence into durable, source-aware public publications without hiding editorial review, uncertainty, limitations, or provenance.

## Publication model

A publication moves through explicit states: `draft`, `review`, `approved`, `published`, and `archived`. Public and unlisted outputs require a human editorial decision and a separate human publish confirmation. Published versions are immutable and receive SHA-256 integrity receipts.

## Structured blocks

The studio supports narrative, heading, callout, quote, map, timeline, chart, evidence-table, source-list, methodology, image, and divider blocks. Maps, charts, evidence tables, and source lists require registered source or evidence references.

## Story maps

Story maps are projections of approved publication blocks. They preserve map, timeline, narrative, image, and callout sequence, but sequence, temporal adjacency, spatial proximity, and chart alignment do not establish causation.

## Visibility

Public publications appear in the public directory. Unlisted publications are omitted from the directory but remain accessible through their exact publication identifier. Private drafts and review history never appear in public endpoints.

## Exports

Each publication can produce JSON, CSV, Markdown, and print-ready HTML. The release marks HTML as PDF-ready but does not claim to generate a PDF binary.

## WordPress integration

The backend provides read-only WordPress handoff packets and the plugin provides a public publication shortcode. A handoff never claims a successful remote write.

## Governance

The studio does not fabricate sources, quotations, evidence, maps, institutional approval, or causal conclusions. Conflicting evidence, missing data, methodology notes, and limitations must remain reviewable.
