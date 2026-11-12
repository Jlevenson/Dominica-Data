# Sightings to Add: scanned DomSeTCO sighting forms

**Catalog ID:** ENV-TUR-003
**Access:** Public
**Contact:** DomSeTCO, Oceans Forward

**Interactive dashboard:** https://jlevenson.github.io/Dominica-Data/environment/sea-turtles/sightings-to-add/

## What this is
224 paper sighting forms from DomSeTCO beach patrols, scanned and transcribed by hand so they can be checked against the nesting database. The dashboard shows encounter times, seasonality, sizes and outcomes by species.

## Coverage
- **When:** 2014-03-19 to 2023-08-29 (mostly 2014–2017)
- **Where:** Net Rosalie, Londonderry, Boute Sable and a few other Dominica beaches

## How it was collected
Patrol teams filled in the standard DomSeTCO sighting form on the beach. The scans were held in the "Sightings to Add" Drive folder and transcribed in November 2026.

## Files
| File | What it contains |
|------|------------------|
| `index.html` | Interactive dashboard (runs in the browser, no server needed) |
| `sightings.csv` | One row per transcribed sighting form, public columns only |
| `d3.v7.min.js` | Charting library used by the dashboard (d3 v7, ISC license) |

## Columns
| Column | Meaning | Units |
|--------|---------|-------|
| `row` | Row number in this file | |
| `date` | Date written on the form | YYYY-MM-DD |
| `year`, `month` | From `date` | |
| `species` | Leatherback, Green, Hawksbill or Unknown ("?" on the form is folded into the species) | |
| `beach` | Grouped beach: Net Rosalie, Londonderry, Boute Sable, Other, Unknown | |
| `beach_name` | Beach as written on the form | |
| `result` | Nest, Suspected Nest, False Crawl or Not recorded | |
| `hour` | Time of encounter | decimal hours, 0–24 |
| `crawl_width_cm` | Crawl width | cm |
| `ccl_cm`, `ccw_cm` | Curved carapace length and width | cm |
| `yolked_eggs` | Yolked egg count | eggs |
| `duplicate_check` | Likely duplicate, Possible duplicate, Same-night form only, or No match, against existing DomSeTCO masterdocs | |

## Quality control
- Every form was read by eye; tallies and ticked boxes were checked on zoomed scans.
- Implausible or conflicting values are kept but were flagged for review in the working sheet (for example leatherback crawl widths of 200–264 cm).
- `duplicate_check`: *likely* = same date, beach and species plus a matching tag or a time within 30–90 minutes; *possible* = same date, beach and species only.
- Withheld from this public version: beach sections, tag numbers, observer names, free-text descriptions and source file names.

## Where the raw data lives
Scans and the full transcription (including excavation forms) are in the Oceans Forward "Sightings to Add" Drive folder. On request.

## How to cite
Oceans Forward (2026). Sightings to Add: scanned DomSeTCO sighting forms. Dominica Data Hub. https://github.com/Jlevenson/Dominica-Data

## Change log
- 2026-11-12 First version.
