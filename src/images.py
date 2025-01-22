import os
import tensorflow as tf
import numpy as np

def augment_image(image):
    image = tf.image.random_flip_left_right(image)  # Random horizontal flip
    image = tf.image.random_flip_up_down(image)    # Random vertical flip

    # Optionally add random cropping
    # if tf.random.uniform(()) > 0.5:
        # image = tf.image.resize_with_crop_or_pad(image, tf.shape(image)[0] - 10, tf.shape(image)[1] - 10)
        # image = tf.image.resize(image, (tf.shape(image)[0] + 10, tf.shape(image)[1] + 10))

    return tf.clip_by_value(image, 0.0, 1.0)  # Ensure pixel values stay in [0, 1]


def load_img(path, target_height, target_width):
    image = tf.io.read_file(path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.cast(image, tf.float32) / 255.0

    height, width = tf.shape(image)[0], tf.shape(image)[1]

    # the same
    if height == target_height and width == target_width:
        return image

    # smaller - only pad
    if height <= target_height and width <= target_width:
        image = tf.image.resize_with_crop_or_pad(image, target_height, target_width)
        return image

    # bigger in 1 or 2 dims - resize and pad
    image = tf.image.resize_with_pad(image, target_height, target_width)

    image = augment_image(image)

    return image

def get_image_list(path):
    return np.sort(np.array(os.listdir(path)))
