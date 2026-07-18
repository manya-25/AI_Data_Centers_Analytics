# AI Data Center Sustainability & Energy Intelligence

An analysis of where AI infrastructure is being built, who's building it, and
how that build-out lines up against electricity cost, grid carbon intensity,
and renewable energy availability worldwide.

**The question this project answers**: as AI adoption accelerates, what
factors make a country an ideal location for efficient and sustainable AI
data centers — and does today's build-out actually reflect those factors?

## Data sources

No single public dataset covers AI infrastructure, electricity pricing, and
grid sustainability together, so this project combines three:

| Source | What it provides | License / access |
|---|---|---|
| [Epoch AI — AI Data Centers](https://epoch.ai/data/ai-data-centers) | 6 datasets: data centers, GPU clusters, build-out timelines, chip deployments, chillers, cooling towers | [CC BY](https://creativecommons.org/licenses/by/4.0/) — see Licensing below |
| [Our World in Data — Energy](https://github.com/owid/energy-data) | Renewable share of electricity, carbon intensity, by country/year | Open, CC BY |
| [GlobalPetrolPrices.com](https://www.globalpetrolprices.com/electricity_prices/) | Residential electricity price by country (USD/kWh) | Manually compiled snapshot, 2023-2026 average — no free bulk API exists, so this is transcribed and not a live feed |

## Repository structure

```
data/
  raw/          # untouched source files
  processed/    # analysis-ready, cleaned output of clean_data_centers.ipynb
notebooks/
  clean_data_centers.ipynb   # data pipeline: raw/ -> processed/
  02_EDA.ipynb                # the analysis itself
```

## How to run

1. `notebooks/clean_data_centers.ipynb` — Run All. Regenerates every file in
   `data/processed/` from `data/raw/`.
2. `notebooks/02_EDA.ipynb` — Run All. Reads only from `data/processed/`.

Each notebook has its own overview cell at the top explaining its inputs,
outputs, and structure in more detail.

## The 10 analytical questions

`02_EDA.ipynb` works through 10 questions, each with its own chart and a
written finding:

| # | Question | Key finding |
|---|---|---|
| 1 | Which countries host the largest concentration of AI-capable data centers? | China (188 GPU clusters) outnumbers the US (119) by count, though the US still leads on total power capacity |
| 2 | Does cheaper electricity correlate with more data center capacity? | No — essentially zero correlation (r = -0.05). The US pays more per kWh than several countries hosting far less capacity |
| 3 | Which operators have the highest renewable energy adoption? | Most major hyperscalers cluster tightly around the US grid average (~25%); single-site operators' numbers mostly reflect their one country, not real efficiency differences |
| 4 | How does carbon intensity differ across countries with major AI infrastructure? | A 24x spread — Norway (28 gCO2/kWh) to Saudi Arabia (692) — among countries all hosting meaningful AI infrastructure |
| 5 | Which countries provide the best balance of electricity cost and sustainability? | Norway and Brazil lead; China ranks notably higher here than on sustainability alone, because it's genuinely cheap even though its grid isn't especially clean |
| 6 | Where are new AI data centers being built most rapidly? | 2024 was the peak year (26 new tracked projects), overwhelmingly US-based |
| 7 | How does renewable energy usage relate to estimated emissions? | Strong relationship (r = -0.78), but France is a clear exception — a nuclear-heavy grid reaches low emissions without high renewable share |
| 8 | Which regions are best suited for future AI expansion? | Norway, Brazil, and Sweden top a sustainability-only ranking; both of today's largest hosts (US, China) sit in the lower half |
| 9 | How do cloud providers compare in global infrastructure footprint? | A single xAI site (783 MW) exceeds Meta AI, CoreWeave, Google, Microsoft, and Oracle's footprints combined |
| 10 | Can countries be grouped into AI infrastructure profiles based on energy, emissions, and capacity? | K-Means (k=3) finds scale — not sustainability — is what actually separates countries: the US and China form their own cluster on raw scale alone |

## Known limitations

- **No live electricity price feed.** The price data is a manually compiled,
  point-in-time snapshot — treat it as directional.
- **Two AI infrastructure tables, two different pictures.** `data_centers_clean.csv`
  is Epoch AI's curated set of the largest/most notable sites (74, heavily
  US-weighted); `gpu_clusters_clean.csv` is a broader global survey (482). The
  notebook uses whichever is more appropriate per question and says so.
- **No interactive dashboard yet.** Everything above is notebook output
  (matplotlib/seaborn), not a deployed Streamlit/Plotly app.

## Licensing

Epoch AI's data is free to use, distribute, and reproduce provided the source and authors are credited under the [Creative Commons Attribution license](https://creativecommons.org/licenses/by/4.0/).

### Citation
```
Epoch AI, ‘AI Data Centers’. Published online at epoch.ai. Retrieved from ‘https://epoch.ai/data/ai-data-centers’ [online resource].
```

### BibTeX Citation
```
@misc{EpochAIDataCenters2026,
  title = {{AI Data Centers}},
  author = {{Epoch AI}},
  year = {2026},
  month = {07},
  url = {https://epoch.ai/data/ai-data-centers}
}
```
