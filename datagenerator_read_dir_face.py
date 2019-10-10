import numpy as np
from skimage.io import imread
import keras
from glob import glob
import PIL.Image as pilimg

class DataGenerator(keras.utils.Sequence):
    def __init__(self, sideslist, frontslist, batch_size=32, dim = (128, 128), n_channels = 3, shuffle = True):
        self.dim = dim
        self.batch_size = batch_size
        self.sideslist = sideslist
        self.frontslist = frontslist
        self.n_channels = n_channels
        self.shuffle = shuffle
        self.on_epoch_end()

    def __len__(self):
        return int(np.floor(len(self.sideslist) / self.batch_size))

    def __getitem__(self, index):
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        sideslist_temp = [self.sideslist[k] for k in indexes]
        frontslist_temp = [self.frontslist[k] for k in indexes]

        sides, fronts = self.__data_generation(sideslist_temp, frontslist_temp)

        return sides, fronts

    def on_epoch_end(self):
        self.indexes = np.arange(len(self.sideslist))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)

    def __data_generation(self, sideslist, frontslist):
        X = np.empty((self.batch_size, * self.dim, self.n_channels))
        Y = np.empty((self.batch_size, * self.dim, self.n_channels))
        i = 0

        for sidename, frontname in zip(sideslist, frontslist):
            # print("sidename : " + sidename)
            side = pilimg.open(sidename)
            side = np.array(side)
            # pilimg._show(side)
            # side.close()
            X[i] = side
            # print(X.shape)
            # print("frontname : " + frontname)
            front = pilimg.open(frontname)
            front = np.array(front)
            # pilimg._show(front)
            # front.close()
            Y[i] = front
            # print(Y.shape)
            i += 1


        return self.preprossing(X), self.preprossing(Y)
    
    def preprossing(self, img):
        return (img / 127.5 - 1)


if __name__ == '__main__':

    sideslist = glob("D:/X_train/*jpg")
    frontslist = glob("D:/Y_train/*jpg")

    dg = DataGenerator(sideslist, frontslist)
    dg.__getitem__(1)