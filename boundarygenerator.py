from PIL import Image
import numpy as np
yay = np.array(Image.open("epic_gaiming.png"))
new = np.zeros((len(yay),len(yay[0])),dtype=bool)


for i in range(len(yay)):
    for j in range(len(yay[0])):
        if yay[i][j][3] == 0:
            new[i][j] = True
        else:
            new[i][j] = False

with open('boundariesTEST.npy', 'wb') as f:
    np.save(f, new)