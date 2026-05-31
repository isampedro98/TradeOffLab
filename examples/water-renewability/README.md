# Water renewability decision (example dossier)

This example shows a full TradeOffLab workflow on a non-trivial question:

**Can water be considered a renewable resource from the perspective of current civilization?**

It was built in the workspace (not scripted): options and criteria were defined manually, assumptions and evidence were added, then tradeoff matrix, adversarial review, and recommendation memo were generated through the structured AI pipeline and exported.

## Files

| File | Description |
|------|-------------|
| [`dossier.md`](dossier.md) | Canonical Markdown export — **3 options**, conditional recommendation, medium adversarial risk |
| [`dossier.json`](dossier.json) | Same dossier as JSON |
| [`dossier-iteration-binary-options.md`](dossier-iteration-binary-options.md) | Earlier iteration with **2 options only** — high adversarial risk, different recommendation |
| [`dossier-iteration-binary-options.json`](dossier-iteration-binary-options.json) | JSON for the 2-option iteration |

Screenshot of the adversarial review UI: [`../../docs/assets/water-adversarial-review.png`](../../docs/assets/water-adversarial-review.png)

## Why this example is useful

- Shows weighted criteria, assumptions with confidence and impact-if-false, and evidence — not a chat transcript.
- Adversarial review challenges the analysis (e.g. energy viability underweighted, lack of quantification).
- The **2-option → 3-option** iteration demonstrates improving the decision frame after critique: the review flagged that binary options blocked a nuanced answer; adding a third option changed risk level and recommendation.

## Reproduce locally

1. `docker compose up --build`
2. Create a new decision or adapt this question in the workspace.
3. Run generation steps in order: assumptions → tradeoff matrix → adversarial review → recommendation memo.
4. Export from the **Export** section (Markdown or JSON).
