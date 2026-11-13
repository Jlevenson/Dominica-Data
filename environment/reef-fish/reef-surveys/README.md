# Dominica reef fish trends from REEF volunteer surveys, 1994–2026

**Catalog ID:** ENV-REF-001
**Access:** Public
**Contact:** Jacob Levenson, Oceans Forward

**Interactive dashboard:** https://jlevenson.github.io/Dominica-Data/environment/reef-fish/reef-surveys/

## What this is
An analysis of 33 years of Reef Environmental Education Foundation (REEF) Volunteer Fish Survey Project data for Dominica (REEF geographic zone 7112). The dashboard shows survey effort, the lionfish invasion, fish groups over time, the species with the largest consistent changes, and a lookup for any species.

Oceans Forward staff and REEF volunteers, together with participatory science divers, have collected data on Dominica's reef fish populations over the years using REEF methods.

## Coverage
- **When:** 1994 to 2026 (download of 13 November 2026)
- **Where:** All REEF survey sites in Dominica (zone 7112)
- **Size:** 2,335 surveys (821 expert, 1,514 novice), 412 taxa

## How it was collected
Divers use REEF's Roving Diver Technique: they swim freely around a site, record every fish species they can identify and give each a log-scale abundance category. Surveyors are classed as novice or expert by REEF from survey experience and ID exam scores. These files are built from REEF's public yearly Comparison Report summaries, not from survey-level raw data.

## Files
| File | What it contains |
|------|------------------|
| `index.html` | Interactive dashboard (runs in the browser, no server needed) |
| `effort.csv` | Surveys per year, expert and novice |
| `lionfish.csv` | Red lionfish sighting frequency and density index per year |
| `trends.json` | Trend model results for 196 taxa (`rows`), with the analysis code in `meta` |
| `periods.json` | Sighting frequency with 95% Wilson intervals for each species in eight periods |
| `groups.json` | Mean sighting frequency for five fish groups per period |
| `species_by_year.csv` | REEF yearly summaries as downloaded: %SF and density index for every taxon, year and experience level |
| `effort_by_year_detail.csv` | Survey counts per year by type (species-and-abundance `SA`, species-only `SO`) and experience level |
| `reserve.csv` | Sighting frequency inside vs outside the Soufrière–Scotts Head Marine Reserve for 19 key species (dashboard) |
| `mpa_species.csv` | Inside vs outside reserve model results for 168 species: odds ratio, change over time, q values, robustness |
| `regional.csv` | Trend per decade for 24 focal species on seven islands (Dominica, St Lucia, St Vincent, Grenada, Saba, St Kitts, St Eustatius) |
| `regional_trends_all.csv` | Trend per decade on each island for 170 species with at least 200 records across islands |
| `fgroups.csv` | Mean trend per decade for four functional groups (fished, herbivores, small cryptic/benthic, other) |
| `abundance_den_trends.csv` | Change in REEF density index (abundance when seen) per decade for 138 species |
| `code/analyze.py`, `code/export.py` | Trend analysis and dashboard export scripts |
| `code/mpa.py`, `code/regional.py`, `code/extra.py` | Reserve comparison, regional comparison, and abundance, functional group, lionfish–prey, Hurricane Maria and community analyses |
| `code/habitat.py`, `code/within_site_all.py`, `code/fig_regional_z.py` | Habitat-matched reserve comparison, within-site trends for all species, regional figure |
| `habitat_matched.csv`, `habitat.csv` | Inside vs outside the reserve within the same (slope) habitat, with provisional site habitat classes in `code/habitat.py` |
| `within_site_all.csv` | Trend per decade at the same sites (site fixed effects) for 168 species |
| `regional_z.csv`, `curves.csv`, `robustness.csv` | Dashboard data: Dominica vs region, smoothed trajectories, robustness summary |
| `code/review.py`, `code/traits.py` | Autocorrelation and non-linearity, Dominica vs between-island variation, effort-corrected richness, sensitivity and species-trait analyses |
| `review_autocorr_gam.csv`, `review_gam_curves.csv`, `fig4_trajectories.png` | Autocorrelation and spline tests for 201 taxa; smoothed trajectories for nine species |
| `review_regional_predictive.csv` | Dominica's trend against the spread of six other islands, 152 species |
| `review_richness_period.csv`, `review_richness_year.csv` | Rarefied and Chao2 species richness by period and year |
| `review_sensitivity.csv` | Robust trends refitted under six alternative analysis choices |
| `traits_species.csv` | Species traits (FishLife/FishBase) with trends |
| `review_summary.json`, `traits_summary.json` | Summary statistics from the above |
| `d3.v7.min.js` | Charting library used by the dashboard (d3 v7, ISC license) |

## Columns
**effort.csv**
| Column | Meaning | Units |
|--------|---------|-------|
| `year` | Calendar year | |
| `surveys`, `expert`, `novice` | All surveys (SA + SO), and by experience level | count |

**lionfish.csv**
| Column | Meaning | Units |
|--------|---------|-------|
| `surveys` | All surveys that year | count |
| `sf` | Share of surveys recording red lionfish | % |
| `den` | REEF density index when recorded (1 single, 2 few, 3 many, 4 abundant) | |

**trends.json (`rows`)**
| Column | Meaning |
|--------|---------|
| `species`, `family` | Common name and family |
| `odds_ratio_decade` | Change in odds of a survey recording the species, per decade; above 1 means recorded more often |
| `q` | Benjamini–Hochberg corrected p-value for the year term |
| `beta_exp`, `beta_nov` | Year effect (log odds per decade) in expert-only and novice-only fits |
| `sightings` | Surveys recording the species in the modelled years |
| `robust`, `direction` | Robust = q < 0.05 and expert-only and novice-only fits agree in sign |

**species_by_year.csv**: `sf` is REEF's published %SF (see Quality control), `den` the density index, `level` All, Expert or Novice.

## Quality control
- **Sighting frequency denominator.** REEF's published %SF counts sightings on all surveys but divides by species-and-abundance surveys only, so it can exceed 100% in years with species-only surveys. Sightings were back-calculated (%SF × SA surveys, which gives whole numbers in every case) and divided by all surveys. All derived files use this corrected sighting frequency; `species_by_year.csv` keeps REEF's values as published.
- **Trend models.** Quasi-binomial GLM per taxon of sightings out of surveys against year, adjusted for the share of expert surveys; years with fewer than 10 surveys dropped; taxa with fewer than 30 records or fewer than 5 years with records not modelled.
- **Excluded from trend calls:** reporting categories REEF added or merged (juvenile hamlet, juvenile grunt, goby and blenny complexes, unidentified taxa).
- **Known limits.** Presence records, not density. Site mix, season, depth and individual surveyors are not controlled. Effort is concentrated in a few years. Some declines may reflect identification changes, for example cleaning goby against the lookalike sharknose goby, which increased over the same period.

## Where the raw data lives
Survey-level REEF data (date, site, depth, surveyor ID) is held by REEF and available to researchers on request from REEF's Director of Science. An older REEF download (May 2014) is in Oceans Forward's Dropbox (`Lionfish/REEF Dominica DATA.xlsx`).

## How to cite
Data: REEF. 2026. Reef Environmental Education Foundation Volunteer Fish Survey Project Database. World Wide Web electronic publication. www.REEF.org, date of download 13 November 2026.

Analysis: Oceans Forward (2026). Dominica reef fish trends from REEF volunteer surveys, 1994–2026. Oceans Forward Dominica Data Repository. https://github.com/Jlevenson/Dominica-Data

The REEF summary data in this folder belong to REEF and are shared here with attribution; the CC BY 4.0 license of this repository covers Oceans Forward's analysis and derived files.

## Change log
- 2026-11-13 First version.
- 2026-11-13 Added reserve, regional and functional group comparisons, with their data and code.
- 2026-11-13 Added robustness analyses (autocorrelation, between-island comparison, richness, sensitivity, traits).
- 2026-11-13 Added habitat-matched reserve comparison, within-site trends for all species and four dashboard sections.
