from __future__ import print_function, division

from keras.applications.vgg19 import VGG19
import keras.backend as K
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

time = 62

# Load data
X_train = np.load('D:/Bitcamp/Project/Frontalization/Imagenius/Numpy/korean_lux_x.npy') # Side face
Y_train = np.load('D:/Bitcamp/Project/Frontalization/Imagenius/Numpy/korean_lux_y.npy') # Front face

# print(X_train.shape)
# print(Y_train.shape)
# print(X_test.shape)
# print(Y_test.shape)

# Shuffle
# X_train, Y_train = shuffle(X_train, Y_train, random_state = 66)
# X_test, Y_test = shuffle(X_test, Y_test, random_state = 66)

train_epochs = 10000
test_epochs = 1
train_batch_size = 32
test_batch_size = 32
train_save_interval = 1
test_save_interval = 1

class DCGAN():
    def __init__(self):
        # Rescale -1 to 1
        self.X_train = X_train / 127.5 - 1.
        self.Y_train = Y_train / 127.5 - 1.
        # X_test = X_test / 127.5 - 1.
        # Y_test = Y_test / 127.5 - 1.

        # Prameters
        self.height = self.X_train.shape[1]
        self.width = self.X_train.shape[2]
        self.channels = self.X_train.shape[3]
        self.latent_dimension = self.width

        self.optimizer = Adam(lr = 0.0002, beta_1 = 0.5)

        self.n_show_image = 1 # Number of images to show
        self.history = []
        self.number = 0

        # Build and compile the discriminator
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss = 'binary_crossentropy', optimizer = self.optimizer, metrics = ['accuracy'])

        # Build and compile the generator
        self.generator = self.build_generator()
        self.generator.compile(loss = self.vgg19_loss, optimizer = self.optimizer)

        # The generator takes noise as input and generates imgs
        z = Input(shape = (self.height, self.width, self.channels))
        image = self.generator(z)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        valid = self.discriminator(image)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(z, [image, valid])
        self.combined.compile(loss = [self.vgg19_loss, 'binary_crossentropy'], loss_weights=[1., 1e-3], optimizer = self.optimizer)

        # self.combined.summary()

    def discriminator_block(self, model, filters, kernel_size, strides):
        layer = Conv2D(filters = filters, kernel_size = kernel_size, strides = strides, padding = 'same')(model)
        layer = BatchNormalization(momentum = 0.5)(layer)
        layer = LeakyReLU(alpha = 0.2)(layer)

        return layer

    def residual_block(self, model, filters, kernel_size, strides):
        generator = model

        layer = Conv2D(filters = filters, kernel_size = kernel_size, strides = strides, padding = 'same')(generator)
        layer = BatchNormalization(momentum = 0.5)(layer)

        # Using Parametric ReLU
        layer = PReLU(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])(layer)
        layer = Conv2D(filters = filters, kernel_size = kernel_size, strides=strides, padding = 'same')(layer)
        output = BatchNormalization(momentum = 0.5)(layer)

        model = add([generator, output])

        return model

    def up_sampling_block(self, model, filters, kernel_size, strides):
        # In place of Conv2D and UpSampling2D we can also use Conv2DTranspose (Both are used for Deconvolution)
        # Even we can have our own function for deconvolution (i.e one made in Utils.py)
        # layer = Conv2DTranspose(filters = filters, kernel_size = kernal_size, strides = strides, padding = 'same)(layer)
        layer = Conv2D(filters = filters, kernel_size = kernel_size, strides = strides, padding = 'same')(model)
        layer = UpSampling2D(size = (2, 2))(layer)
        layer = LeakyReLU(alpha = 0.2)(layer)

        return layer
    
    # computes VGG loss or content loss
    def vgg19_loss(self, true, prediction):
        vgg19 = VGG19(include_top = False, weights = 'imagenet', input_shape = (self.height, self.width, self.channels))
        # Make trainable as False

        vgg19.trainable = False

        for layer in vgg19.layers:
            layer.trainable = False
        
        model = Model(inputs = vgg19.input, outputs = vgg19.get_layer('block5_conv4').output)
        model.trainable = False

        return K.mean(K.square(model(true) - model(prediction)))

    def build_generator(self):
        input = Input(shape = (self.height, self.width, self.channels))

        layer = Conv2D(filters = 16, kernel_size = (2, 2), strides = (1, 1), padding = 'same')(input)
        layer = PReLU(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])(layer)
        layer = MaxPooling2D(pool_size = (2, 2))(layer)
        layer = Conv2D(filters = 32, kernel_size = (2, 2), strides = (1, 1), padding = 'same')(layer)
        layer = PReLU(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])(layer)
        layer = MaxPooling2D(pool_size = (2, 2))(layer)
        layer = Conv2D(filters = 64, kernel_size = (2, 2), strides = (1, 1), padding = 'same')(layer)
        layer = PReLU(alpha_initializer = 'zeros', alpha_regularizer = None, alpha_constraint = None, shared_axes = [1, 2])(layer)
        layer = MaxPooling2D(pool_size = (2, 2))(layer)

        previous_output = layer

        # Using 16 Residual Blocks
        for i in range(16):
            layer = self.residual_block(model = layer, filters = 64, kernel_size = (3, 3), strides = (1, 1))

        layer = Conv2D(filters = 64, kernel_size = (3, 3), strides = (1, 1), padding = 'same')(layer)
        layer = BatchNormalization(momentum = 0.5)(layer)
        layer = add([previous_output, layer])

        # Using 2 UpSampling Blocks
        for j in range(3):
            layer = self.up_sampling_block(model = layer, filters = 256, kernel_size = (3, 3), strides = (1, 1))

        layer = Conv2D(filters = self.channels, kernel_size = (9, 9), strides = (1, 1), padding = 'same')(layer)
        output = Activation('tanh')(layer)

        generator_model = Model(inputs = input, outputs = output)

        # generator_model.summary()

        return generator_model

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
        # Adversarial ground truths
        fake = np.zeros((batch_size, 1))
        real = np.ones((batch_size, 1))

        print('Training')

        for k in range(epochs):
            for l in tqdm(range(batch_size)):
                # Select a random half of images
                index = np.random.randint(0, self.X_train.shape[0], batch_size)
                front_image = self.Y_train[index]

                # Generate a batch of new images
                side_image = self.X_train[index]

                # optimizer.zero_grad()
                
                generated_image = self.generator.predict(side_image)

                self.discriminator.trainable = True

                # Train the discriminator (real classified as ones and generated as zeros)
                discriminator_fake_loss = self.discriminator.train_on_batch(generated_image, fake)
                discriminator_real_loss = self.discriminator.train_on_batch(front_image, real)
                discriminator_loss = 0.5 * np.add(discriminator_fake_loss, discriminator_real_loss)
                
                self.discriminator.trainable = False

                # Train the generator (wants discriminator to mistake images as real)
                generator_loss = self.combined.train_on_batch(side_image, [front_image, real])

                # Plot the progress
                print ('\nTraining epoch : %d \nTraining batch : %d \nAccuracy of discriminator : %.2f%% \nLoss of discriminator : %f \nLoss of generator : %f ' 
                        % (k + 1, l + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss[2]))

                record = (k + 1, l + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss[2])
                self.history.append(record)

                # If at save interval -> save generated image samples
                if l % save_interval == 0:
                    save_path = 'D:/Generated Image/Training' + str(time) + '/'
                    self.save_image(image_index = l, front_image = front_image, side_image = side_image, save_path = save_path)

        self.history = np.array(self.history)

        self.graph(history = history, save_path = save_path)

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
                print ('\nTest epoch : %d \nTest batch : %d \nAccuracy of discriminator : %.2f%% \nLoss of discriminator : %f \nLoss of generator : %f ' 
                        % (m + 1, n + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss[2]))

                record = (m + 1, n + 1, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss[2])
                history.append(record)

                # If at save interval -> save generated image samples
                if n % save_interval == 0:
                    save_path = 'D:/Generated Image/Testing' + str(time) + '/'
                    self.save_image(image_index = n, front_image = front_image, side_image = side_image, save_path = save_path)

        history = np.array(history)

        self.history(history = history, save_path = save_path)

    def save_image(self, image_index, front_image, side_image, save_path):
        # Rescale images 0 - 1
        generated_image = 0.5 * self.generator.predict(side_image) + 0.5

        front_image = (127.5 * (front_image + 1)).astype(np.uint8)
        side_image = (127.5 * (side_image + 1)).astype(np.uint8)

        plt.figure(figsize = (8, 2))

        # Adjust the interval of the image
        plt.subplots_adjust(wspace = 0.6)

        # Show image (first column : original side image, second column : original front image, third column = generated image(front image))
        for m in range(self.n_show_image):
            generated_image_plot = plt.subplot(1, 3, m + 1 + (2 * self.n_show_image))
            generated_image_plot.set_title('Generated image (front image)')

            if self.channels == 1:
                plt.imshow(generated_image[image_index,  :  ,  :  , 0], cmap = 'gray')
            
            else:
                plt.imshow(generated_image[image_index,  :  ,  :  ,  : ])

            original_front_face_image_plot = plt.subplot(1, 3, m + 1 + self.n_show_image)
            original_front_face_image_plot.set_title('Origninal front image')

            if self.channels == 1:
                plt.imshow(front_image[image_index].reshape(self.height, self.width), cmap = 'gray')
                
            else:
                plt.imshow(front_image[image_index])

            original_side_face_image_plot = plt.subplot(1, 3, m + 1)
            original_side_face_image_plot.set_title('Origninal side image')

            if self.channels == 1:
                plt.imshow(side_image[image_index].reshape(self.height, self.width), cmap = 'gray')
                
            else:
                plt.imshow(side_image[image_index])

            # Don't show axis of x and y
            generated_image_plot.axis('off')
            original_front_face_image_plot.axis('off')
            original_side_face_image_plot.axis('off')

            self.number += 1

            # plt.show()

        save_path = save_path

        # Check folder presence
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        save_name = '%d.png' % self.number
        save_name = os.path.join(save_path, save_name)
    
        plt.savefig(save_name)
        plt.close()

    def graph(self, history, save_path):
        plt.plot(self.history[:, 2])     
        plt.plot(self.history[:, 3])
        plt.plot(self.history[:, 4])
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Generative adversarial network')
        plt.legend(['Accuracy of discriminator', 'Loss of discriminator', 'Loss of generator'], loc = 'upper left')

        figure = plt.gcf()

        # plt.show()

        save_path = save_path

        # Check folder presence
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        # save_name = '%d.png' % number
        save_name = 'History.png'
        save_name = os.path.join(save_path, save_name)

        figure.savefig(save_name)
        plt.close()

if __name__ == '__main__':
    dcgan = DCGAN()
    dcgan.train(epochs = train_epochs, batch_size = train_batch_size, save_interval = train_save_interval)
    # dcgan.test(epochs = test_epochs, batch_size = test_batch_size, save_interval = test_save_interval)