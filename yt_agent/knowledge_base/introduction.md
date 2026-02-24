# yt Library - Introduction

`yt` is a python library for analyzing and visualizing volumetric data.
It supports many different frontend codes (Enzo, FLASH, Ramses, Gadget, etc).

Key Concepts:

- **Datasets**: Represent the simulation output. Usually loaded with `yt.load()`.
- **Fields**: Physical quantities (e.g., density, temperature). `("gas", "density")`.
- **Data Objects**: Regions in space (e.g., sphere, box, region).
- **Plots**: Visualization objects (SlicePlot, ProjectionPlot).

To use `yt`, you always start by importing it:

```python
import yt
```

Then load a dataset:

```python
ds = yt.load("path/to/data")
```
