import json
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt



def open_data():
    with open("data.json", "r") as f:
        return json.load(f)
    
def norm_arr(array):
    h = max(array)
    return array / h

def mean(array, d):
    s = np.sum(array)
    return s / d

def norm_px(x: ndarray, mean, var):
    return (np.exp( -((x - mean) ** 2) / (2 * var))) / (np.sqrt(2 * np.pi * var))

data = open_data()

x = np.array(data["x"])
y = np.array(data["y"])

weighted_x = x * y

x_bar = mean(weighted_x, np.sum(y))

n = np.linspace(min(x), max(x), 1000)
n_dist = norm_px(n, x_bar, 30000)

fig, ax = plt.subplots()

ax.hist(np.linspace(min(x), max(x), 1000), n_dist * 3000)

ax.plot(x, y)

plt.show()