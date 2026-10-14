# Example prompts

## 1) Rewrite notes into LaTeX

**Prompt**

`Turn these notes into an Overleaf-ready methods subsection for a hyperspectral classification paper...`

**Expected behavior**

- returns a `\subsection{Methods}` block
- uses technical hyperspectral terminology correctly
- keeps claims modest and evidence-based

## 2) Tighten GIS terminology

**Prompt**

`Rewrite this paragraph to use proper GIS language. Keep the meaning, but make it sound like a journal paper.`

**Expected behavior**

- replaces vague phrases like `map stuff` with `geospatial layers`, `raster products`, `spatial overlay`, etc.
- preserves the user's actual workflow

## 3) Write a figure caption

**Prompt**

`Write a LaTeX figure caption for a map showing the study area, sensor footprint, and land-cover classes.`

**Expected behavior**

- concise caption
- explains symbols/colors
- names study area and map content cleanly

## 4) Draft a reviewer response

**Prompt**

`Write a polite response to Reviewer 2 asking us to justify the CRS choice and explain reprojection effects.`

**Expected behavior**

- formal reviewer-response tone
- mentions CRS and reprojection with correct GIS terminology
- avoids defensiveness

## 5) Convert plain text abstract to LaTeX

**Prompt**

`Convert this abstract to LaTeX and improve the wording for a space remote sensing audience.`

**Expected behavior**

- returns a clean abstract block
- uses EO/space terminology precisely
- does not invent missing metrics or references

## 6) Page-limit compression

**Prompt**

`Shorten this introduction by 25% without losing the technical content. Keep it in LaTeX.`

**Expected behavior**

- removes repetition and filler
- keeps acronyms and citations intact
- preserves structure and meaning
