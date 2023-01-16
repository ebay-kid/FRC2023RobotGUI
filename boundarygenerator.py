from PIL import Image
import numpy as np
yay = np.array(Image.open("epic_gaiming.png"))
new = np.zeros((len(yay),len(yay[0])),dtype=bool)
new2 = np.zeros((len(yay),len(yay[0])),dtype=bool)

DRIVETRAINPIXELADD = 55

for i in range(len(yay)):
    for j in range(len(yay[0])):
        if yay[i][j][3] == 0:
            new[i][j] = True
        else:
            new[i][j] = False

for k in range(DRIVETRAINPIXELADD):
    for i in range(len(new)):
        for j in range(len(new[0])):
            if i+1 < len(new) and new[i+1][j]:
                new[i][j] = True
                continue
            if i-1 >= 0 and new[i-1][j]:
                new[i][j] = True
                continue
            if j+1 < len(new[0]) and new[i][j+1]:
                new[i][j] = True
                continue
            if j-1 >= 0 and new[i][j-1]:
                new[i][j] = True
                continue
            if i+1 < len(new) and j+1 < len(new[0]) and new[i+1][j+1]:
                new[i][j] = True
                continue
            if i-1 >= 0 and j+1 < len(new[0]) and new[i-1][j+1]:
                new[i][j] = True
                continue
            if i+1 < len(new) and j-1 > 0 and new[i+1][j-1]:
                new[i][j] = True
                continue
            if j-1 >= 0 and i-1 >= 0 and new[i-1][j-1]:
                new[i][j] = True
                continue


for i in range(len(new2)):
    for j in range(len(new2[0])):
        if new[i][j]:
            new2[i][j] = (0,0,0,0)
        else:
            new2[i][j] = (255,255,255,255)

img = Image.fromarray(new2)
img.save("dady.png")


#with open('boundariesTEST.npy', 'wb') as f:
#    np.save(f, new)