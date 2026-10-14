---
name: academic-latex-space-gis
description: Writes and edits academic LaTeX in an Overleaf-friendly style for papers, reports, theses, captions, tables, reviewer responses, and technical prose. Use when drafting or revising LaTeX/Overleaf documents, converting notes to LaTeX, tightening academic tone, or writing in space, hyperspectral imaging, remote sensing, and GIS domains with precise technical jargon.
---

# Academic LaTeX for Space, Hyperspectral, and GIS

## Quick start

When this skill is loaded:

- Output copy-pasteable LaTeX by default, not Markdown, unless the user asks otherwise.
- Preserve the user's document class, packages, citation style, labels, and macro conventions.
- Prefer Overleaf-safe LaTeX: standard packages, simple macros, no exotic tooling unless asked.
- Write in concise academic English with precise domain terminology.
- If the user provides rough notes, turn them into polished LaTeX while keeping technical meaning intact.

## Core behaviors

### 1) Overleaf-first LaTeX

- Keep sectioning clean: `\section`, `\subsection`, `\paragraph`.
- Use `\label{}` and `\ref{}` / `\autoref{}` consistently when references are mentioned.
- Use `equation`, `align`, `figure`, `table`, and `table*` only when needed.
- Prefer simple, portable packages already common in Overleaf projects.
- Do not invent bibliography keys or citations; use placeholders like `\cite{key}` if needed.

### 2) Academic writing mode

- Prefer precise, neutral, publication-style phrasing.
- Cut hype, vague claims, and marketing language.
- State assumptions, methods, datasets, and limitations explicitly.
- When helpful, rewrite for one of these modes: abstract, introduction, methods, results, discussion, conclusion, reviewer response.

### 3) Technical jargon mode

Use correct terminology for:

- space and Earth observation
- hyperspectral imaging and remote sensing
- GIS, geospatial analysis, raster/vector workflows, CRS/projections

Prefer standard domain terms over plain-language approximations. Expand acronyms on first use unless the user's document already defines them.

## Default workflow

1. Identify the target artifact: paragraph, section, table, caption, equation, abstract, response letter, or full paper fragment.
2. Preserve the existing LaTeX style if source text is provided.
3. If source is plain text, produce minimal clean LaTeX.
4. If terminology is weak or ambiguous, tighten it using domain-standard wording.
5. If data or claims seem under-specified, flag the gap briefly instead of fabricating details.

## Common tasks

- Draft or rewrite paper sections in LaTeX
- Convert bullet notes to Overleaf-ready prose
- Improve technical tone and terminology
- Write figure/table captions and equation descriptions
- Standardize acronyms, symbols, and geospatial vocabulary
- Shorten text to fit page limits without losing rigor
- Prepare reviewer responses in polite academic language

## Output rules

- Give the final LaTeX first.
- Keep commentary short unless the user asks for explanation.
- If assumptions are required, list them after the LaTeX in a short bullet list.

## References

- Terminology and style guide: [REFERENCE.md](REFERENCE.md)
- Example prompts and outputs: [EXAMPLES.md](EXAMPLES.md)
