# DomSeTCO sea turtle sightings explorer

**Catalog ID:** ENV-TUR-004
**Access:** Public (tag numbers, observer names and GPS positions withheld)
**Contact:** DomSeTCO / Oceans Forward

## What this is
Every sea turtle encounter recorded on Dominica's beach patrols from 2003 to 2025, merged from 18 record sources into one row per encounter, with an [interactive dashboard](index.html). The dashboard shows the change in leatherback nesting, encounters by season, month, beach and outcome, carapace length, and tagged turtles returning in later seasons. Every chart follows the species, outcome, beach and season filters.

## Coverage
- **When:** 2003 to 2025 nesting seasons (2026 left out as incomplete)
- **Where:** Dominica nesting beaches, mainly Rosalie, Bout Sable (La Plaine), Londonderry and Turtle Point on the east coast, and Point Gunard, Champagne and Secret Bay on the west coast
- **Species:** leatherback, green, hawksbill, plus single loggerhead and Kemp's ridley records

## How it was collected
Night beach patrols by DomSeTCO staff, community members and volunteers (from 2003 under the Rosalie Sea Turtle Initiative, run by WIDECAST, and from 2007 under DomSeTCO). Crews recorded date, time, beach, species, outcome (confirmed nest, suspected nest, false crawl), flipper tags, curved carapace length and width, crawl width and egg counts.

## Files
| File | What it contains |
|------|------------------|
| `index.html` | Interactive dashboard (needs the two CSV files next to it; open it on the repository website, not from your computer) |
| `encounters.csv` | One row per de-duplicated encounter, all species |
| `turtle_seasons.csv` | One row per tagged turtle per season it was recorded, under an anonymous turtle ID |
| `d3.v7.min.js` | Charting library used by the dashboard |

## Columns
**encounters.csv**

| Column | Meaning | Units |
|--------|---------|-------|
| `event_id` | Encounter ID in the merged dataset | |
| `date`, `time` | Date and local time of the encounter | YYYY-MM-DD, HH:MM |
| `season`, `month`, `day_of_year` | Calendar year, month and day of year | |
| `species` | Species, or `Not recorded` | |
| `beach` | Beach as recorded, or `Not recorded` | |
| `result` | Nest, Suspected Nest, False Crawl, Poached, Release, Dead or Not recorded | |
| `tagged` | Whether a flipper tag was read (numbers withheld) | |
| `crawl_width_cm`, `ccl_cm`, `ccw_cm` | Crawl width, curved carapace length (notch to tip) and width | cm |
| `yolked_eggs`, `unyolked_eggs` | Egg counts for confirmed nests (0 treated as not counted) | count |
| `n_source_records` | Number of source records merged into this encounter | count |

**turtle_seasons.csv**

| Column | Meaning |
|--------|---------|
| `turtle_id` | Anonymous turtle ID (species prefix and number) |
| `species`, `season` | Species and season the turtle was recorded |
| `encounters`, `nests` | Encounters and confirmed nests that season |
| `first_date`, `last_date` | First and last record that season |
| `beach` | Most frequent recorded beach that season |
| `status` | `First season` or `Returning` (seen in an earlier season) |

## Quality control
- Duplicates across and within the 18 sources were removed by matching tag numbers within 2 days, then (for untagged records) species, beach and outcome on the same night with times within 90 minutes, identical egg counts, or crawl widths within 5 cm.
- ArcGIS records back-entered for seasons up to 2021 were 4 hours behind the original records and were corrected. Undated legacy records given the ArcGIS import timestamp (22 July 2022) were treated as undated, and a re-submitted batch of 19 copies (17 June 2022) was removed.
- 47 leatherback dates entered day/month were swapped back, 2019 sheet dates were re-read day-first, and 3 year typos were fixed. Placeholder tag values (99999, UNK, LB2008) count as untagged.
- Individual turtles: within each species, tags recorded together on at least two nights belong to one turtle. A single shared night can add a new tag to a turtle but never merges two known turtles. Leatherback records under 120 cm CCL are left out of this.
- Patrol effort was not logged in most seasons, so counts reflect both nesting and how much beach was watched. Beach was often not recorded before 2013.
- Patrol shifts logged with no turtle (mostly 2020–2021) are left out.

## Where the raw data lives
The DomSeTCO database export, yearly masterdocs, the ArcGIS Survey123 layer and scanned field forms are held by DomSeTCO and Oceans Forward. Tag numbers and nest locations are available on request.

## How to cite
Oceans Forward (2026). DomSeTCO sea turtle sightings explorer, 2003–2025. Oceans Forward Dominica Data Repository. https://github.com/Jlevenson/Dominica-Data

## Change log
- 2026-11-14 First version.
