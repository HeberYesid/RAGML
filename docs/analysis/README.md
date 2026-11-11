# Dataset analysis

`ragml.analysis` validates the configured catalog, commercial records and source
manifest, then exports descriptive statistics without running an embedding or
generation model. It never reads adjustment or reserved evaluation cases.

Install the `analysis` extra when PNG/SVG figures are required:

```powershell
uv sync --extra analysis
.\.venv\Scripts\python.exe -m ragml.analysis --output-dir docs/analysis/new-run
```

The output directory must not already exist. Use a new directory for each run;
the command refuses to overwrite a previous export. `--no-charts` needs only the
base project dependencies and exports JSON, CSV and explanatory Markdown.

The demo reference clock comes from the catalog's scoped `package-metadata.json`.
An explicit `--evaluated-at 2026-11-04T12:05:00Z` overrides it. Non-demo data and
demo data without clock metadata require an explicit reference clock. The report
records that clock and SHA256 hashes for all inputs, including each source file.

The [2026-11-09 export](2026-11-09/README.md) contains:

- `summary.json`: typed statistics, category coverage, commerce states, attribute
  availability, text lengths, IQR flags and input hashes.
- `categories.csv`, `attributes.csv`, `commercial.csv`, `documents.csv` and
  `outliers.csv`: reviewable records with explicit columns and UTF-8 BOM.
- `categories`, `prices`, `missingness`, `commerce` and `lengths` in PNG and SVG:
  statistical figures for the academic report and presentation.

Prices enter the summaries only when known and fresh at the recorded clock.
Unknown or expired prices are not zero. Product attributes are analyzed once per
base product and separately by category, key and unit. Omitted optional attributes
and explicit nulls remain distinct. IQR flags identify values to inspect; the
analysis does not delete them or infer that an extreme value is wrong.

Quartiles use linear interpolation at `(n - 1) p`; sample standard deviation is
available for `n >= 2`. IQR flags require `n >= 4`. Empty or inapplicable values
remain null. The category and commerce balance reflects synthetic construction,
not observed purchasing behavior, market demand or participant validation.

The public boundaries covered by `tests/test_analysis.py` are descriptive
calculation, validated dataset analysis and the export command. Those software
tests are separate from assistant-quality evaluation.
