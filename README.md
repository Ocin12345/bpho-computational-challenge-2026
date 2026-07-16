# BPhO Computational Challenge 2026

Private working repository for our British Physics Olympiad Computational Challenge project.

The repository is currently **private**. We can make it public later if we decide that
we want to share the finished work.

## What we are making

We are building physics models in Python, checking them with calculations and graphs,
and keeping enough evidence to explain our working in the final screencast.

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
| `task05_hydrogen_spectrum` | Hydrogen spectrum and Bohr model |
| `task06_electron_diffraction` | Electron diffraction |
| `task07_particle_in_box` | Particle in a box and the uncertainty principle |
| `task08_quantum_cryptography` | Quantum cryptography |
| `task09_compton_scattering` | Compton scattering |
| `task10_hydrogenic_orbitals` | Hydrogenic orbitals |

## Project layout

```text
taskXX_topic/       Code and notes for one challenge task
notebooks/          Exploratory Jupyter notebooks
figures/            Saved graphs and visual results
reports/            Written explanations and final write-up material
presentation/       Curated slide assets and timed narration scripts
data/               Small input data files
requirements.txt    Python packages used by the project
```

Current presentation material:

- [Task 1 PowerPoint pack](presentation/task01/README.md)
- [Task 2 PowerPoint pack](presentation/task02/README.md)
- [Task 3 PowerPoint pack](presentation/task03/README.md)

Large downloads, videos, and local Python environments should stay outside GitHub.
Never commit passwords, access tokens, or other private information.

## Setting up Python

From the project folder, create a virtual environment and install the project packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `.venv` folder is deliberately excluded from Git.

## Using both computers

The MacBook Air is the main computer because it is available every day. The 4090 laptop
is a second computer for backup or more demanding visualisations.

Before starting work on either computer:

```bash
git pull
```

When stopping work or changing computers:

```bash
git add .
git commit -m "Describe what changed"
git push
```

This keeps GitHub as the shared source of truth between both computers.

## Official resources

- [BPhO Computational Challenge page](https://www.bpho.org.uk/bpho/computational-challenge/)
- [2026 competition specification](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.pdf)
- [2026 course and challenge materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip)
- [Anaconda/Python installation guide](https://www.bpho.org.uk/bpho/computational-challenge/Downloading_anaconda.pdf)
