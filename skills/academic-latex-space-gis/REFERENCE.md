# Reference

## Overleaf-friendly LaTeX conventions

- Prefer common packages already likely to exist in academic projects: `amsmath`, `amssymb`, `graphicx`, `booktabs`, `multirow`, `siunitx`, `hyperref`, `xcolor`, `subcaption`.
- Avoid adding packages unless they clearly solve the user's problem.
- Keep tables readable: use `booktabs`, avoid vertical rules unless the document already uses them.
- Keep figures compact: clear captions, defined symbols, consistent units.
- Use math mode only for mathematical objects, variables, units handled consistently.
- Preserve existing citation commands (`\cite`, `\citet`, `\citep`, etc.).

## Academic tone rules

Prefer:

- precise verbs: `estimate`, `derive`, `quantify`, `characterize`, `evaluate`
- evidence-based claims: `results indicate`, `the analysis suggests`, `the model achieved`
- explicit scope: `for the study area`, `under the evaluated conditions`, `within the spectral range`

Avoid unless justified:

- `novel`, `groundbreaking`, `revolutionary`
- `very`, `huge`, `massive`, `clearly`
- unsupported claims of superiority

## Space / Earth observation terminology

Prefer terms such as:

- Earth observation (EO)
- platform, payload, instrument, sensor
- spatial resolution, spectral resolution, temporal resolution, radiometric resolution
- swath width, revisit time, ground sampling distance (GSD)
- orbit, nadir, off-nadir, geolocation accuracy
- radiometric calibration, atmospheric correction, orthorectification
- level-1 / level-2 products when appropriate

Example phrase:

- `The instrument acquires multispectral observations with a revisit time of five days over the study region.`

## Hyperspectral terminology

Prefer terms such as:

- hyperspectral cube / data cube
- spectral signature, reflectance spectrum
- band, wavelength, contiguous bands
- signal-to-noise ratio (SNR)
- endmember, spectral unmixing, abundance estimation
- dimensionality reduction, feature extraction, band selection
- atmospheric absorption bands, water-vapor bands
- supervised classification, anomaly detection, target detection
- spectral angle mapper (SAM), matched filtering, continuum removal

Example phrase:

- `The hyperspectral cube was resampled after removing low-SNR and water-absorption bands.`

## GIS / geospatial terminology

Prefer terms such as:

- coordinate reference system (CRS)
- projection, datum, georeferencing
- raster, vector, polygon, polyline, point feature
- spatial join, overlay, buffering, zonal statistics
- digital elevation model (DEM)
- land cover, land use, study area, extent
- topology, adjacency, spatial autocorrelation
- geostatistical interpolation only when actually used

Example phrase:

- `All layers were reprojected to a common CRS before raster-vector overlay analysis.`

## Useful writing patterns

### Methods

- dataset/source
- preprocessing
- model or algorithm
- parameterization
- evaluation protocol
- metrics

### Results

- key quantitative finding
- comparison against baseline or prior method
- uncertainty or variance
- observed failure mode or limitation

### Figure captions

A good caption usually states:

1. what is shown
2. where/when it applies
3. what symbols/colors mean
4. the takeaway, if appropriate

### Reviewer responses

Use a polite pattern:

- thank the reviewer
- restate the concern briefly
- describe the revision precisely
- point to section/page/figure if known

## Safe fallback behavior

If the user does not specify a journal/template:

- keep LaTeX generic and portable
- avoid journal-specific environments
- use placeholder citations and labels
- do not fabricate datasets, sensor specs, metrics, or references
