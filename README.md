# Oceans Forward Dominica Data Hub

One directory for every dataset Oceans Forward collects or manages in Dominica: sea turtles, telemetry, coral, BRUV, GIS and agriculture.

**Browse it:** https://jlevenson.github.io/Dominica-Data/

## How this repository works

The repository is a catalog, not a warehouse.

- `catalog.csv` lists every dataset, one row each. The website is built from this file automatically.
- Small, cleaned datasets live in the program folders.
- Large raw data (BRUV video, raw telemetry, logger dumps) stays in external storage. The catalog row links to it.
- Sensitive data (nest locations, unpublished tracks, staff and budget files) is never committed here. It is listed with access set to **On request** or **Embargoed** so people know it exists and who to ask.

## Folders

| Folder | Contents |
|--------|----------|
| `environment/sea-turtles/` | DomSeTCO beach patrols and nesting (Londonderry, Woodford Hill, Marigot) |
| `environment/leatherback-telemetry/` | Satellite tracking of post-nesting leatherbacks |
| `environment/coral-thermal/` | Restoration site temperature loggers, DHW, SST comparison |
| `environment/bruv/` | Baited remote underwater video deployments |
| `environment/gis/` | Land planning, soils, landslide hazard |
| `agriculture/cane-farming/` | Cane farming program |
| `templates/` | README template for new datasets |

## Access levels

- **Public**: file is in this repository or linked, free to use under the license below.
- **On request**: exists but is not published. Contact the listed person.
- **Embargoed**: held until a publication or partner agreement allows release.

## Adding a dataset

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License and citation

Data is released under [CC BY 4.0](LICENSE.md) unless a dataset's README says otherwise. Cite as:

> Oceans Forward ([year]). [Dataset title]. Oceans Forward Dominica Data Hub. https://github.com/Jlevenson/Dominica-Data
