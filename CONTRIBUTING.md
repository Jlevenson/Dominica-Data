# Adding a dataset

1. **Pick the folder** for the program. If none fits, make a new one and add it to the table in `README.md`.
2. **Copy the template.** Put `templates/dataset-README.md` in a subfolder named for the dataset, e.g. `environment/sea-turtles/nesting-2026/README.md`, and fill it in.
3. **Add the data, if it belongs here.**
   - Commit it if it is public, cleaned, and under about 50 MB.
   - Otherwise store it externally (Drive, Movebank, Zenodo) and put the link in the catalog.
   - Never commit nest coordinates, unpublished tracks, personal information, or budget and staff files.
4. **Add one row to `catalog.csv`.**
   - `id`: program prefix plus a number, e.g. `ENV-TUR-003`. IDs never change once used.
   - `link`: the relative path to the file or folder (e.g. `environment/sea-turtles/nesting-2026/`) or a full URL. Leave it empty if the data is not available yet.
   - `access`: `Public`, `On request` or `Embargoed`.
   - `status`: `Available` or `Planned`.
   - `updated`: YYYY-MM-DD.
   - Put quotes around any value that contains a comma.
5. **Commit.** The website updates within a minute or two.

## ID prefixes

| Prefix | Program |
|--------|---------|
| ENV-TUR | Sea turtles and beach patrols |
| ENV-TEL | Telemetry |
| ENV-COR | Coral |
| ENV-BRV | BRUV |
| ENV-GIS | GIS and land planning |
| AGR-CAN | Cane farming |
| RBD-ENE / RBD-SAL | Distillery energy / sales |
| EDU-WHL | Education, whale model |
