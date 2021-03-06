from __future__ import print_function, division

from keras.layers import Activation, add, BatchNormalization, Conv2D, Conv2DTranspose, Dense, Dropout, Flatten, Input, MaxPooling2D, Reshape, UpSampling2D, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU, PReLU
from keras.models import Model, Sequential
from keras.optimizers import Adam, Nadam
import math
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
import sys
from tqdm import tqdm

time = 60

# Load data
X_train = np.load('D:/Bitcamp/Project/Frontalization/Imagenius/Numpy/color_128_x.npy') # Side face
Y_train = np.load('D:/Bitcamp/Project/Frontalization/Imagenius/Numpy/color_128_y.npy') # Front face

# print(X_train.shape)
# print(Y_train.shape)

# print(X_train.shape)
# print(Y_train.shape)
# print(X_test.shape)
# print(Y_test.shape)

# Rescale -1 to 1
X_train = X_train / 127.5 - 1.
Y_train = Y_train / 127.5 - 1.
# X_test = X_test / 127.5 - 1.
# Y_test = Y_test / 127.5 - 1.

# # Shuffle
X_train, Y_train = shuffle(X_train, Y_train, random_state = 66)
# X_test, Y_test = shuffle(X_test, Y_test, random_state = 66)

# Prameters
height = X_train.shape[1]
width = X_train.shape[2]
channels = X_train.shape[3]
latent_dimension = width

# print(height)
# print(width)
# print(quarter_height)
# print(quarter_width)
# print(channels)
# print(latent_dimension)

optimizer = Adam(lr = 0.0002, beta_1 = 0.5)

n_show_image = 1 # Number of images to show

history = []
number = 0

def batch_size():
    if latent_dimension > 32:
        batch_size = 32

        return batch_size

    else:
        batch_size = latent_dimension

        return batch_size
        
train_epochs = 10000
test_epochs = 1
train_batch_size = batch_size()
test_batch_size = batch_size()
train_save_interval = 1
test_save_interval = 1

def paramertic_relu(alpha_initializer, alpha_regularizer, alpha_constraint, shared_axes):
    PReLU(alpha_initializer = alpha_initializer, alpha_regularizer = alpha_regularizer, alpha_constraint = alpha_constraint, shared_axes = shared_axes)

class DCGAN():
    def __init__(self):
        self.height = height
        self.width = width
        self.channels = channels
        self.latent_dimension = latent_dimension

        self.optimizer = optimizer

        self.number = number

        # Build and compile the discriminator
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss = 'binary_crossentropy', optimizer = optimizer, metrics = ['accuracy'])

        # Build the generator
        self.generator = self.build_generator()

        # The generator takes noise as input and generates imgs
        # z = Input(shape = (self.height, self.width, self.channels, ))
        z = Input(shape = (self.height, self.width, self.channels))
        image = self.generator(z)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        valid = self.discriminator(image)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(z, valid)
        self.combined.compile(loss = 'binary_crossentropy', optimizer = optimizer)

        # self.combined.summary()

    def build_generator(self):
        model = Sequential()

        model.add(Conv2D(filters = 16, kernel_size = (4, 4), strides = (2, 2), padding = 'same', input_shape = (self.height, self.width, self.channels)))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2D(filters = 32, kernel_size = (4, 4), strides = (2, 2), padding = 'valid'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2D(filters = 64, kernel_size = (4, 4), strides = (2, 2), padding = 'valid'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2D(filters = 128, kernel_size = (4, 4), strides = (2, 2), padding = 'valid'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2D(filters = 256, kernel_size = (4, 4), strides = (2, 2), padding = 'valid'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2D(filters = 512, kernel_size = (1, 1), strides = (1, 1), padding = 'valid'))
        model.add(MaxPooling2D(pool_size = (2, 2))) # At this point, we arrive at our low D representation vector, which is 512 dimensional
        model.add(Conv2DTranspose(filters = 256, kernel_size = (4, 4), strides = (2, 2), padding = 'same', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2DTranspose(filters = 128, kernel_size = (4, 4), strides = (2, 2), padding = 'valid', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (2, 2), padding = 'valid', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2DTranspose(filters = 32, kernel_size = (4, 4), strides = (2, 2), padding = 'valid', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2DTranspose(filters = 16, kernel_size = (4, 4), strides = (2, 2), padding = 'valid', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Conv2DTranspose(filters = self.channels, kernel_size = (6, 6), strides = (2, 2), padding = 'valid', use_bias = None))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(Activation(paramertic_relu(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])))
        model.add(Activation('tanh'))

        # model.summary()
        
        side_face = Input(shape = (self.height, self.width, self.channels, ))
        image = model(side_face)
        
        return Model(side_face, image)

    def build_discriminator(self):
        model = Sequential()

        model.add(Conv2D(32, kernel_size = (3, 3), strides = (2, 2), input_shape = (self.height, self.width, self.channels), padding = 'same'))
        model.add(LeakyReLU(alpha = 0.2))
        model.add(Dropout(0.25))
        model.add(Conv2D(64, kernel_size = (3, 3), strides = (2, 2), padding = 'same'))
        model.add(ZeroPadding2D(padding = ((0, 1), (0, 1))))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(LeakyReLU(alpha = 0.2))
        model.add(Dropout(0.25))
        model.add(Conv2D(128, kernel_size = (3, 3), strides = (2, 2), padding = 'same'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(LeakyReLU(alpha = 0.2))
        model.add(Dropout(0.25))
        model.add(Conv2D(256, kernel_size = (3, 3), strides = (2, 2), padding = 'same'))
        model.add(BatchNormalization(momentum = 0.8))
        model.add(LeakyReLU(alpha = 0.2))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(1, activation = 'sigmoid'))

        # model.summary()

        image = Input(shape = (self.height, self.width, self.channels))
        validity = model(image)

        return Model(image, validity)

    def train(self, epochs, batch_size, save_interval):
        global history

        # Adversarial ground truths
        fake = np.zeros((batch_size, 1))
        real = np.ones((batch_size, 1))

        print('Training')

        for k in range(epochs):
            for l in tqdm(range(batch_size)):
                # Select a random half of images
                index = np.random.randint(0, X_train.shape[0], batch_size)
                front_image = Y_train[index]

                # Generate a batch of new images
                side_image = X_train[index]
                
                generated_image = self.generator.predict(side_image)

                self.discriminator.trainable = True

                # Train the discriminator (real classified as ones and generated as zeros)
                discriminator_fake_loss = self.discriminator.train_on_batch(generated_image, fake)
                discriminator_real_loss = self.discriminator.train_on_batch(front_image, real)
                discriminator_loss = 0.5 * np.add(discriminator_fake_loss, discriminator_real_loss)

                self.discriminator.trainable = False

                # Train the generator (wants discriminator to mistake images as real)
                generator_loss = self.combined.train_on_batch(side_image, real)
                
                # Plot the progress
                print ('\nTraining epoch : %d \nTraining batch : %d  \nAccuracy of discriminator : %.2f%% \nLoss of discriminator : %f \nLoss of generator : %f'
                        % (k + 1, l + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss))

                record = (k + 1, l + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss)
                history.append(record)

                # If at save interval -> save generated image samples
                if l % save_interval == 0:
                    save_path = 'D:/Generated Image/Training' + str(time) + '/'
                    self.save_image(image_index = l, front_image = front_image, side_image = side_image, save_path = save_path)

        history = np.array(history)

        self.history(history = history, save_path = save_path)

    def test(self, epochs, batch_size, save_interval):
        global history

        # Adversarial ground truths
        fake = np.zeros((batch_size, 1))
        real = np.ones((batch_size, 1))

        print('Testing')

        for m in range(epochs):
            for n in tqdm(range(batch_size)):
                # Select a random half of images
                index = np.random.randint(0, X_test.shape[0], batch_size)
                front_image = Y_test[index]

                # Generate a batch of new images
                side_image = X_test[index]

                generated_image = self.generator.predict(side_image)

                # Train the discriminator (real classified as ones and generated as zeros)
                discriminator_fake_loss = self.discriminator.test_on_batch(generated_image, fake)
                discriminator_real_loss = self.discriminator.test_on_batch(front_image, real)
                discriminator_loss = 0.5 * np.add(discriminator_fake_loss, discriminator_real_loss)

                # Train the generator (wants discriminator to mistake images as real)
                generator_loss = self.combined.test_on_batch(side_image, [front_image, real])
                
                # Plot the progress
                print ('\nTraining epoch : %d \nTraining batch : %d  \nAccuracy of discriminator : %.2f%% \nLoss of discriminator : %f \nLoss of generator : %f'
                        % (m + 1, n + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss))

                record = (m + 1, n + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss)
                history.append(record)

                # If at save interval -> save generated image samples
                if n % save_interval == 0:
                    save_path = 'D:/Generated Image/Testing' + str(time) + '/'
                    self.save_image(image_index = n, front_image = front_image, side_image = side_image, save_path = save_path)

        history = np.array(history)

        self.history(history = history, save_path = save_path)

    def save_image(self, image_index, front_image, side_image, save_path):
        global number

        # Rescale images 0 - 1
        generated_image = 0.5 * self.generator.predict(side_image) + 0.5

        front_image = (127.5 * (front_image + 1)).astype(np.uint8)
        side_image = (127.5 * (side_image + 1)).astype(np.uint8)

        plt.figure(figsize = (8, 2))

        # Adjust the interval of the image
        plt.subplots_adjust(wspace = 0.6)

        # Show image (first column : original side image, second column : original front image, third column = generated image(front image))
        for m in range(n_show_image):
            generated_image_plot = plt.subplot(1, 3, m + 1 + (2 * n_show_image))
            generated_image_plot.set_title('Generated image (front image)')

            if channels == 1:
                plt.imshow(generated_image[image_index,  :  ,  :  , 0], cmap = 'gray')
            
            else:
                plt.imshow(generated_image[image_index,  :  ,  :  ,  : ])

            original_front_face_image_plot = plt.subplot(1, 3, m + 1 + n_show_image)
            original_front_face_image_plot.set_title('Origninal front image')

            if channels == 1:
                plt.imshow(front_image[image_index].reshape(height, width), cmap = 'gray')
                
            else:
                plt.imshow(front_image[image_index])

            original_side_face_image_plot = plt.subplot(1, 3, m + 1)
            original_side_face_image_plot.set_title('Origninal side image')

            if channels == 1:
                plt.imshow(side_image[image_index].reshape(height, width), cmap = 'gray')
                
            else:
                plt.imshow(side_image[image_index])

            # Don't show axis of x and y
            generated_image_plot.axis('off')
            original_front_face_image_plot.axis('off')
            original_side_face_image_plot.axis('off')

            number += 1

            # plt.show()

        save_path = save_path

        # Check folder presence
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        save_name = '%d.png' % number
        save_name = os.path.join(save_path, save_name)
    
        plt.savefig(save_name)
        plt.close()

    def history(self, history, save_path):
        plt.plot(history[:, 2])     
        plt.plot(history[:, 3])
        plt.plot(history[:, 4])
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Generative adversarial network')
        plt.legend(['Accuracy of discriminator', 'Loss of discriminator', 'Loss of generator'], loc = 'upper left')

        figure = plt.gcf()

        plt.show()

        save_path = save_path

        # Check folder presence
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        save_name = 'History.png'
        save_name = os.path.join(save_path, save_name)

        figure.savefig(save_name)
        plt.close()

if __name__ == '__main__':
    dcgan = DCGAN()
    dcgan.train(epochs = train_epochs, batch_size = train_batch_size, save_interval = train_save_interval)
    # dcgan.test(epochs = test_epochs, batch_size = test_batch_size, save_interval = test_save_interval)