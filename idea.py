from __future__ import print_function, division

from datagenerator_read_dir_face import DataGenerator
from glob import glob
from keras.layers import Activation, BatchNormalization, Conv2D, Conv2DTranspose, Dense, Dropout, Flatten, Input, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.models import Model, Sequential
from keras.optimizers import Adam
from keras_vggface.vggface import VGGFace
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from tqdm import tqdm

np.random.seed(10)

time = 87

# Load data
X_train = glob('D:/Bitcamp/Project/Frontalization/Imagenius/Data/Korean 224X224X3 filtering/X/*jpg')
Y_train = glob('D:/Bitcamp/Project/Frontalization/Imagenius/Data/Korean 224X224X3 filtering/Y/*jpg')

train_epochs = 100
batch_size = 16
save_interval = 1

class DCGAN():
    def __init__(self):
        # Load data
        self.datagenerator = DataGenerator(X_train, Y_train, batch_size = batch_size)

        # Prameters
        self.height = 224
        self.width = 224
        self.channels = 3

        self.optimizer = Adam(lr = 0.0002, beta_1 = 0.5)

        self.n_show_image = 1 # Number of images to show
        self.history = []
        self.number = 1
        self.save_path = 'D:/Generated Image/Training' + str(time) + '/'

        # Build and compile the discriminator
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss = 'binary_crossentropy', optimizer = self.optimizer, metrics = ['accuracy'])

        # Build the generator
        self.generator = self.build_generator()

        # Save .json
        generator_model_json = self.generator.to_json()

        # Check folder presence
        if not os.path.isdir(self.save_path + 'Json/'):
            os.makedirs(self.save_path + 'Json/')

        with open(self.save_path + 'Json/generator_model.json', "w") as json_file : 
            json_file.write(generator_model_json)

        # The generator takes side images as input and generates images
        z = Input(shape = (self.height, self.width, self.channels))
        image = self.generator(z)

        # For the combined model we will only train the generator
        self.discriminator.trainable = False

        # The discriminator takes generated images as input and determines validity
        valid = self.discriminator(image)

        # The combined model  (stacked generator and discriminator)
        # Trains the generator to fool the discriminator
        self.combined = Model(z, valid)
        self.combined.compile(loss = 'binary_crossentropy', optimizer = self.optimizer)

        # self.combined.summary()

    def senet50(self):
        senet50_layer = VGGFace(include_top = False, model = 'senet50', weights = 'vggface', input_shape = (self.height, self.width, self.channels))

        senet50_layer.trainable = False

        # senet50_layer.summary()

        return senet50_layer

    def build_generator(self):
        senet50_layer = self.senet50()

        senet50_last_layer = senet50_layer.get_layer('activation_162').output

        generator_layer = Conv2DTranspose(filters = 256, kernel_size = (4, 4), strides = (1, 1), padding = 'valid')(senet50_last_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 32, kernel_size = (4, 4), strides = (2, 2), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (1, 1), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (2, 2), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (2, 2), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (1, 1), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = 64, kernel_size = (4, 4), strides = (2, 2), padding = 'valid')(generator_layer)
        generator_layer = BatchNormalization(momentum = 0.8)(generator_layer)
        generator_layer = LeakyReLU(alpha = 0.2)(generator_layer)
        generator_layer = Conv2DTranspose(filters = self.channels, kernel_size = (5, 5), strides = (1, 1), padding = 'valid')(generator_layer)

        generator_output = Activation('tanh')(generator_layer)

        generator = Model(inputs = senet50_layer.input, outputs = generator_output)

        # generator.summary()

        return generator

    def build_discriminator(self):
        senet50_layer = self.senet50()

        senet50_last_layer = senet50_layer.get_layer('activation_81').output

        discriminator_layer = Flatten()(senet50_last_layer)

        discriminator_output = Dense(units = 1, activation = 'sigmoid')(discriminator_layer)

        discriminator = Model(inputs = senet50_layer.input, outputs = discriminator_output)

        return discriminator

    def train(self, epochs, batch_size, save_interval):
        # Adversarial ground truths
        fake = np.zeros((batch_size, 1))
        real = np.ones((batch_size, 1))

        print('Training')

        for k in range(1, epochs + 1):
            for l in tqdm(range(1, self.datagenerator.__len__() + 1)):
                # Select images
                side_image, front_image = self.datagenerator.__getitem__(l)

                # Generate a batch of new images
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
                print ('\nTraining epoch : %d \nTraining batch : %d \nAccuracy of discriminator : %.2f%% \nLoss of discriminator : %f \nLoss of generator : %f ' 
                        % (k, l, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss))

                record = (k, l, discriminator_loss[1] * 100, discriminator_loss[0], generator_loss)
                self.history.append(record)

                # If at save interval -> save generated image samples
                if l % save_interval == 0:
                    self.save_image(front_image = front_image, side_image = side_image, train_number = k, epoch_number = l, save_path = self.save_path)

            # Save .h5
            if k % 5 == 0:
                # Check folder presence
                if not os.path.isdir(self.save_path + 'H5/'):
                    os.makedirs(self.save_path + 'H5/')

                self.generator.save(self.save_path + 'H5/' + 'generator_epoch_%d.h5' % k)
                self.generator.save_weights(self.save_path + 'H5/' + 'generator_weights_epoch_%d.h5' % k)

        self.history = np.array(self.history)

        self.graph(history = self.history, save_path = self.save_path + 'History/')

    def save_image(self, front_image, side_image, train_number, epoch_number, save_path):
        # Rescale images 0 - 1
        generated_image = 0.5 * self.generator.predict(side_image) + 0.5

        front_image = (127.5 * (front_image + 1)).astype(np.uint8)
        side_image = (127.5 * (side_image + 1)).astype(np.uint8)

        # Show image (first column : original side image, second column : original front image, third column = generated image(front image))
        for m in range(batch_size):
            plt.figure(figsize = (8, 2))

            # Adjust the interval of the image
            plt.subplots_adjust(wspace = 0.6)

            for n in range(self.n_show_image):
                generated_image_plot = plt.subplot(1, 3, n + 1 + (2 * self.n_show_image))
                generated_image_plot.set_title('Generated image (front image)')
                plt.imshow(generated_image[m,  :  ,  :  ,  : ])

                original_front_face_image_plot = plt.subplot(1, 3, n + 1 + self.n_show_image)
                original_front_face_image_plot.set_title('Origninal front image')
                plt.imshow(front_image[m])

                original_side_face_image_plot = plt.subplot(1, 3, n + 1)
                original_side_face_image_plot.set_title('Origninal side image')
                plt.imshow(side_image[m])

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

            save_name = 'Train%d_Batch%d_%d.png' % (train_number, epoch_number, self.number)
            save_name = os.path.join(save_path, save_name)
        
            plt.savefig(save_name)
            plt.close()

    def graph(self, history, save_path):
        plt.plot(self.history[  :  , 2])     
        plt.plot(self.history[  :  , 3])
        plt.plot(self.history[  :  , 4])
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
    dcgan.train(epochs = train_epochs, batch_size = batch_size, save_interval = save_interval)