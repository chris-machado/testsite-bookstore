import numpy as np
w = np.array([1,2])
npoints = 5
myones = np.ones(npoints)
x = np.arange(0, npoints)
x = np.vstack((myones, x))
y = np.dot(w,x)
print(f'x = {x}')
print(f'y = {y}')


