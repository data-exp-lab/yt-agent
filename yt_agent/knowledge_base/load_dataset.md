# Loading Datasets

To load a dataset in `yt`, use the `yt.load` function. It detects the file format automatically.

```python
import yt

# Load a single file
ds = yt.load("snapshot_001.h5")

# Load a time series
ts = yt.load("snapshot_*.h5")
```

After loading, you can inspect the available fields:

```python
print(ds.field_list)
print(ds.derived_field_list)
```
