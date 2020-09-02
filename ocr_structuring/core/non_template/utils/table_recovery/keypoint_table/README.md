# Table recovery using KeyPoint detection

-----
there are nine kinds point

0┏  1┳  2┓

3┣  4╋  5┫

6┗  7┻  8┛

-----
1. Where does data come from?  

Read data from extra_data

2. how to use it?
```python
from ocr_structuring.core.non_template.utils.table_recovery.keypoint_table import KeypointPostProcess, Point
from typing import List
import numpy as np

points: List[Point]
image: np.ndarray

# Instantiation
postprocess = KeypointPostProcess(points, image)

# get all grids        
grids, points = postprocess.get_grids()
```

3. How to Customize data structure?

Inherit it!

> Author Jmy