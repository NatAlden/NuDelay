import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import math
import time
import random
import json
from pathlib import Path

lis=np.array([1,2,3,4] + [5.1,5.2,5.3,5.4,5.5,5.6,5.7,5.8,5.9,6] + [7,8,9,10] + [11.1,11.2,11.3,11.4,11.5,11.6,11.7,11.8,11.9,12] + [13,14,15])
lis= np.array( range(1, 5, 0.5) + np.arange(5.1, 6.1, 0.1) + range(7, 11) + np.arange(11.1, 12.1, 0.1) + range(13, 16))
print(lis)

lis2=np.clip(lis, 0, max_value)
print(lis2)