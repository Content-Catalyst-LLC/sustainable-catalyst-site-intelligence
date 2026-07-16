# Site Intelligence v2.18.0 — Evidence Synthesis, Claims, and Contradiction Review

## Purpose

This release adds a governed evidence layer that keeps claims, source evidence, reviewer decisions, uncertainty, and synthesized language separate and auditable. It does not convert source counts into truth scores and does not allow deterministic or AI-assisted text to invent evidence.

## Records

- **Claims:** factual, interpretive, causal, projection, or normative statements with scope, status, visibility, tags, human-review state, and SHA-256 integrity.
- **Evidence:** supporting, qualifying, conflicting, or contextual records with source identifiers, titles, URLs, excerpts, locators, authority context, methodology context, limitations, and redacted metadata.
- **Uncertainty:** measurement, method, source, comparability, causal, forecast, coverage, or other uncertainty with severity and resolution state.
- **Reviews:** approve, reject, needs-revision, unresolved, or supersede decisions made by a named reviewer role with rationale and evidence IDs reviewed.
- **Syntheses:** deterministic grounded packets that cite registered evidence IDs, preserve contradictions and uncertainty, and require human approval before public release.

## Contradiction review

The engine reports supporting, qualifying, and conflicting evidence independently. A claim with both supporting and conflicting evidence is marked `review_required`; the system does not average disagreement away, infer causation, or select a winner automatically.

## Grounded assistance

The default assistance mode is a deterministic grounded template. No external model is invoked. Any future AI-assisted wording must use registered evidence IDs, preserve source attribution, label generated language, and remain subject to human review.

## Public boundary

Public endpoints expose only approved public claims, public evidence, public uncertainty, and approved public syntheses. Draft claims, private evidence, reviewer history, and control operations remain behind the existing administrative token boundary.

## Handoffs

Read-only evidence packets can be handed to Knowledge Library or Research Librarian. Handoffs preserve claim text, evidence relationships, contradictions, uncertainty, citations, integrity digests, and review status.

## Prohibited behavior

- Fabricated evidence, quotations, citations, or source authority.
- Suppression of conflicting evidence or unresolved uncertainty.
- Causal conclusions from correlation, proximity, sequence, or majority counts alone.
- Automatic legal, medical, scientific, security, or policy determinations.
- Individual targeting, surveillance, risk scoring, or consequential automated action.
