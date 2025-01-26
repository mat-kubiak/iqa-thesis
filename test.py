import os
import sys
import tensorflow as tf
import numpy as np

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{project_dir}/src')

import images, labels, models

MODEL_PATH = f'{project_dir}/output/model.keras'

DATA_PATH = f'{project_dir}/data'
MOS_PATH = f'{DATA_PATH}/mos.csv'
IMG_DIRPATH = f'{DATA_PATH}/images/train'

HEIGHT = None
WIDTH = None

TEST_BATCH_SIZE = 5
LIMIT = 50

def load_img(path, label):
    image = images.load_img(path, HEIGHT, WIDTH)
    return image, label

def main():
    global HEIGHT, WIDTH

    img_paths = images.get_image_list(IMG_DIRPATH)
    mos = labels.load_categorical(MOS_PATH, IMG_DIRPATH)
    print(f"Detected {len(mos)} labels and {len(img_paths)} images")

    if LIMIT < len(mos):
        print(f"Limited images to {LIMIT}")
        mos = mos[:LIMIT]
        img_paths = img_paths[:LIMIT]
    
    if not os.path.isfile(MODEL_PATH):
        print("Fatal error: model could not be found")
        sys.exit(1)

    model = models.load_model(MODEL_PATH)
    print(f"Loaded model")

    HEIGHT, WIDTH = model.input_shape[1:3]
    print(f"Found dimensions: width: {WIDTH}, height: {HEIGHT}")

    dataset = tf.data.Dataset.from_tensor_slices((img_paths, mos))
    dataset = dataset.map(load_img)
    dataset = dataset.batch(TEST_BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)

    loss, accuracy = model.evaluate(dataset)
    print(f"loss: {loss}")
    print(f"accuracy: {accuracy}")
    print("Program finished")

if __name__ == '__main__':
    main()
