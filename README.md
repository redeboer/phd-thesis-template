# PhD thesis template

[![CI](https://github.com/redeboer/phd-thesis-template/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/redeboer/phd-thesis-template/actions/workflows/ci.yml)
[![Spelling checked](https://img.shields.io/badge/cspell-checked-brightgreen.svg)](https://github.com/streetsidesoftware/cspell/tree/main/packages/cspell)
[![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)

A reusable [Quarto](https://quarto.org) book template for writing and publishing a PhD thesis. It is based on the structure of [`redeboer/phd-thesis`](https://github.com/redeboer/phd-thesis), with the thesis-specific prose, figures, branding, and scientific dependencies removed.

The template builds itself with placeholder content, so its own output is a live example of what you get: [general theme](https://redeboer.github.io/phd-thesis-template) and [RUB theme](https://redeboer.github.io/phd-thesis-template/rub).

For this template repository, `pixi run doc` stages both examples in `docs/_build/html` for a single Pages deployment, with RUB under `rub/`. The publishing step runs only when `GITHUB_REPOSITORY=redeboer/phd-thesis-template`; it adds the preview link to the generated landing page without changing the Quarto sources. Standalone RUB tasks write to `docs/_build/rub`. Bootstrap removes the example publishing step and keeps the selected thesis at the website root.

Pull requests from this repository are published separately at `https://redeboer.github.io/phd-thesis-template-preview/pr-N/`, with the RUB example under `rub/`. A dependent PR CI job reuses the completed Pages artifact, so the PR can introduce and test its own publisher. It serializes publishing to preserve other previews, links both themes from the CI summary and PR, and removes the preview on close or merge. The preview repository serves its `main` branch through GitHub Pages. The existing `PAT` secret needs Contents write access there and permission to comment on PRs here. Fork PRs are not published. Bootstrap removes this template-only CI configuration.

> [!NOTE]
> This template is intended to remain compatible with Quarto v1. Quarto v2 is being developed separately in [`quarto-dev/q2`](https://github.com/quarto-dev/q2), and is not currently a compatibility target.

## Start a thesis

Click [**Use this template**](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) on GitHub, clone the resulting repository, and enter its directory.

Install [Pixi](https://pixi.sh/latest/installation) and [uv](https://docs.astral.sh/uv/getting-started/installation). On macOS and Linux, the standalone installer is:

```shell
curl -fsSL https://pixi.sh/install.sh | sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows PowerShell, use:

<!-- cspell:ignore useb -->

```powershell
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Start the guided configuration:

```shell
uv tool install pre-commit --with pre-commit-uv
pixi install
uv sync
pixi run bootstrap
```

Pixi installs native conda-forge dependencies and runs project tasks, while [uv](https://docs.astral.sh/uv) creates the locked Python environment. The one-shot bootstrap CLI configures either the general thesis or the RUB variant, then removes template-only validation tooling. Run `pixi run bootstrap --help` for non-interactive options and review the result with `git diff`.

After setup, replace the example chapters and front matter under `docs/`, add sources to `docs/references.bib`, and use [Quarto's citation syntax](https://quarto.org/docs/authoring/citations.html). Run `pixi task list` to see the available tasks; `pixi run html` builds the website. [PDF rendering](https://quarto.org/docs/output-formats/pdf-engine.html) requires a TeX distribution: the PDF tasks install TinyTeX through Quarto on first run if no TeX engine is found.

## Optional RUB theme

The template includes an optional [Ruhr University Bochum](https://www.ruhr-uni-bochum.de/en) [project profile](https://quarto.org/docs/projects/profiles.html). Selecting `rub` during bootstrap makes it the main configuration, so the standard Pixi tasks build the RUB thesis. The general profile uses a supervisor and examiner; the RUB title page instead uses first and second examiners.

Run `pixi run rub-html` to preview the RUB website, or `pixi run rub-assets` to download only its assets. The website pairs the full navbar logo with the square RUB cube in the sidebar. RUB builds fetch the unchanged logos from the official [logo archive](https://markenportal.ruhr-uni-bochum.de/wp-content/uploads/2026/10/RUB_Logo.zip) and [RUB Inter](https://markenportal.ruhr-uni-bochum.de/wp-content/uploads/2026/09/RUB_Inter.zip) on demand. The fonts retain their [SIL Open Font License](https://github.com/rsms/inter/blob/v4.1/LICENSE.txt).

> [!IMPORTANT]
> The RUB name and logos are institutional branding governed by Ruhr University Bochum's [corporate-design guidance](https://markenportal.ruhr-uni-bochum.de/corporate-design). Their inclusion in this template does not grant trademark rights or place those assets under the template's Apache licence.

The Methods chapter contains an [executable Jupyter example](https://quarto.org/docs/computations/python.html) demonstrating cached computation and [code presentation controls](https://quarto.org/docs/output-formats/html-code.html). Replace it with your analysis or remove it and its dependencies for a prose-only thesis.

Before publishing, replace the template README and licence as appropriate, then [enable GitHub Pages with GitHub Actions](https://quarto.org/docs/publishing/github-pages.html#github-action).

## Licence

The template code is available under the Apache License 2.0. You remain free to choose a separate licence for the prose, figures, and data in your thesis.
