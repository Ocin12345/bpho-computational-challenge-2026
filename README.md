# BPhO Computational Challenge 2026

Qingxiang Liao's British Physics Olympiad Computational Challenge project:
ten Python models, their numerical checks, and a browser-based physics lab.
This repository is public and includes the code and supporting results.

## Start here

To explore the website, download or clone the whole repository, then run these
commands from its root folder. No scientific packages or npm install are needed
for the website.

```bash
python3 -m http.server 8080 --bind 127.0.0.1
```

Open [the local website](http://localhost:8080/site/) in a current browser.
Keep the server running while you use it; press Ctrl+C to stop it. Serve the
repository root, not just `site/`, because the task pages load results from
`data/` and `figures/`. Opening the HTML files directly with `file://` will block
some modules and data requests.

To run the Python models and checks, follow [Setting up Python](#setting-up-python)
below. The [reproducibility guide](submission/README.md) lists the additional
requirements for verification and rebuilding the presentation files.

## What we are making

The models cover random motion, thermal radiation and quantum physics. Each task
folder contains its equations, implementation and tests. Saved plots and numerical
results support the explanations in the screencast materials.

Python is our main tool because it is flexible for numerical modelling, plotting,
simulation, animation, and possible extensions. Excel and other software are also
allowed by the competition if they are useful for a particular task.

## Competition requirements

- Work individually or in a pair.
- Complete the challenge tasks at the level we are aiming for.
- Keep the code, calculations, graphs, and explanations as evidence of the working.
- Submit a maximum three-minute **unlisted YouTube screencast**.
- The screencast should show the models, code or spreadsheets, graphs, results, and
  explanation of how the results were obtained.
- The 2026 registration deadline is **30 July 2026**.
- The final submission deadline is **10pm on Monday 10 August 2026**.

### Award levels

- **Bronze:** spreadsheet-based challenge elements completed, with some basic coding
  attempted.
- **Silver:** all tasks completed in code.
- **Gold:** all tasks completed to a high standard, with possible extensions such as
  apps, improved models, or a research-style report.

## Task roadmap

| Folder | Topic |
| --- | --- |
| [`task01_random_walk`](task01_random_walk/README.md) | Random walk |
| [`task02_brownian_motion`](task02_brownian_motion/README.md) | Brownian motion |
| [`task03_thermal_radiation`](task03_thermal_radiation/README.md) | Black-body radiation and heat capacity |
| [`task04_photoelectric_effect`](task04_photoelectric_effect/README.md) | Photoelectric effect |
| [`task05_hydrogen_spectrum`](task05_hydrogen_spectrum/README.md) | Hydrogen spectrum and Bohr model |
| [`task06_electron_diffraction`](task06_electron_diffraction/README.md) | Electron diffraction |
| [`task07_particle_in_box`](task07_particle_in_box/README.md) | Particle in a box and the uncertainty principle |
| [`task08_quantum_cryptography`](task08_quantum_cryptography/OFFICIAL_REQUIREMENTS.md) | Quantum cryptography |
| [`task09_compton_scattering`](task09_compton_scattering/README.md) | Compton scattering |
| `task10_hydrogenic_orbitals` | Hydrogenic orbitals |

## Project layout

```text
taskXX_topic/       Code and notes for one challenge task
notebooks/          Exploratory Jupyter notebooks
figures/            Saved graphs and visual results
reports/            Written explanations and final write-up material
presentation/       Curated slide assets and timed narration scripts
data/               Small input data files
site/               Static website for the landing page and Tasks 1–10
requirements.txt    Python packages used by the project
```

## Interactive website

The integrated website is in [`site/`](site/). It contains the landing page,
the ten-task index, browser-based views for Tasks 1–10, and a separate
[`Advanced Lab`](site/advanced.html) for the optional extension programme.
Preview it from
the repository root with:

```bash
python3 -m http.server 8080
```

Then open [`http://localhost:8080/site/`](http://localhost:8080/site/). The
site README documents its local vendor dependencies and serving requirements.

## Advanced extension programme

All ten optional investigations now have committed models, regression tests,
generated evidence and an illustrated research record. They include dimensional
random walks; a Maxwellian many-particle bath; copper calorimetry fitting;
inverse photoelectric metrology; precision spectroscopy; graphite intensity
and broadening; finite wells, tunnelling and packet revival; finite-key BB84;
detector-level Compton spectra; and orbital superposition, hybridisation,
molecular orbitals and screened atoms.

- [`data/advanced_extensions.json`](data/advanced_extensions.json) is the
  deterministic cross-task evidence bundle.
- [`reports/advanced_extensions/`](reports/advanced_extensions/README.md)
  contains the ten illustrated reports.
- [`figures/advanced/`](figures/advanced/manifest.json) contains ten generated
  publication PNG/SVG pairs.
- [`site/advanced.html`](site/advanced.html) is the offline interactive viewer.

These additions do not replace or lengthen the maximum three-minute filming
route.

Current presentation material:

- [Task 1 PowerPoint pack](presentation/task01/README.md)
- [Task 2 PowerPoint pack](presentation/task02/README.md)
- [Task 3 PowerPoint pack](presentation/task03/README.md)
- [Task 4 PowerPoint pack](presentation/task04/README.md)
- [Task 5 PowerPoint pack](presentation/task05/README.md)
- [Task 6 PowerPoint pack](presentation/task06/README.md)
- [Task 7 PowerPoint pack](presentation/task07/README.md)
- [Task 8 PowerPoint pack](presentation/task08/README.md)
- [Task 9 PowerPoint pack](presentation/task09/README.md)
- [Task 10 PowerPoint pack](presentation/task10/README.md)

## Final verification and release archive

The completed Tasks 1–10 project now has one repository-wide verification and
release route:

```bash
python3 -m submission.verify_project
python3 -m submission.build_release_archive
```

The first command runs all ten task test suites, the extension bundle and
figures, final artifact gates, presentations, typography, timing, links and
portability. The second builds a clean evidence archive with per-file and
whole-archive SHA-256 digests. Full
regeneration, accepted dependencies, scientific assumptions and the final
handoff checklist are documented in
[`submission/README.md`](submission/README.md).

Large downloads, videos, and local Python environments should stay outside GitHub.
Never commit passwords, access tokens, or other private information.

## Setting up Python

Python 3.9.6 is the recorded reference environment. From the project root, create
a virtual environment and install the pinned scientific packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r submission/requirements-lock.txt
```

On Windows, use `py` to create the environment and activate it with
`.venv\Scripts\Activate.ps1` in PowerShell. After activation, use `python` for
the commands below. Install Node.js for the JavaScript checks and Times New Roman
for the scientific figure checks; see [the environment guide](submission/README.md).

```bash
python -m submission.verify_project
```

The `.venv` folder is excluded from Git. `requirements.txt` gives broader package
ranges for development; exact regenerated output can vary with library versions.

## Working on another computer

Before starting work on either computer:

```bash
git pull
```

When stopping work or changing computers:

```bash
git add <files-you-changed>
git commit -m "Describe what changed"
git push
```

Review `git status` before committing. Include the source and data needed to
reproduce any new website result, not just the page that displays it.

## Official resources

- [BPhO Computational Challenge page](https://www.bpho.org.uk/bpho/computational-challenge/)
- [2026 competition specification](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.pdf)
- [2026 course and challenge materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip)
- [Anaconda/Python installation guide](https://www.bpho.org.uk/bpho/computational-challenge/Downloading_anaconda.pdf)
