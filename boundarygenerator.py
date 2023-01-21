from PIL import Image
import numpy as np
img = np.array(Image.open("epic_gaiming.png"))

# one means it's legal to go through, 0 means not legal
new1 = np.ones((len(img), len(img[0])), dtype=bool)
new2 = np.ones((len(img[0]), len(img)), dtype=bool)

bounds = []
boundsRot = []

DRIVETRAINPIXELADD = 55

# iterate through each pixel of numpy image "yay", and if the pixel is transparent, then set the corresponding index in the numpy array "new" to 0. Otherwise, set it to 1.
def yayChecker(yay, new):
    for i in range(len(yay)):
        prevTrueIdx = -1
        for j in range(len(yay[0])):
            if yay[i][j][3] == 0:
                if prevTrueIdx == -1:
                    prevTrueIdx = j
                new[i][j] = 0
            else:
                if prevTrueIdx != -1:
                    bounds.append((i,prevTrueIdx,j))
                    prevTrueIdx = -1
                new[i][j] = 1

yayChecker(img, new1)
rotated = np.rot90(img)
yayChecker(rotated, new2)

# given the index bounds of areas that should be set to 0, set the indices within DRIVETRAINPIXELADD before the start index to 0, and the indices after the start index by DRIVETRAINPIXELADD to 0 as well.
def setThingsToZero(bounds, new):
    for i in bounds:
        for j in range(i[1]-DRIVETRAINPIXELADD,i[1]):
            new[i[0]][j] = 0
        for j in range(i[2],i[2]+DRIVETRAINPIXELADD):
            new[i[0]][j] = 0

newNew2 = np.rot90(new2, k=3)
newImg = np.logical_or(new1, newNew2)

# set all True values in the array to 1, all False to 0.
# newImg = new1.astype(int)

"""
for i in newImg:
    temp = ""
    for j in i:
        temp += str(int(j))
    print(temp)
"""
#img = Image.fromarray(new2)
#img.save("dady.png")


with open('boundariesBalls.npy', 'wb') as f:
    np.save(f, newImg)