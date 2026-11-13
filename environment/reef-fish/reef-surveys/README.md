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
| `code/analyze.py`, `code/export.py` | Analysis and export scripts |
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
