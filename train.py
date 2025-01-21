import os, sys, time, signal, math
import tensorflow as tf
import numpy as np
import tqdm

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{project_dir}/src')

import images, labels, log, models

# path to the database containing the images and mos.csv
# change according to your needs
DATA_PATH = f'{project_dir}/data'

MODEL_PATH = f'{project_dir}/model.keras'
MOS_PATH = f'{DATA_PATH}/mos.csv'
IMG_DIRPATH = f'{DATA_PATH}/images/train'

MAX_HEIGHT = 1080
MAX_WIDTH = 1920
RATINGS = 41 # range 1.0, 5.0 with step 0.1
BATCH_SIZE = 5
BATCHES = None
EPOCHS = 10

# Debug Mode
# put to true to simulate logic without actually training
DEBUG = False

status = None
mos = None
model = None
img_paths = None

def signal_handler(sig, frame):
    log.logprint(f"Received signal {sig}, exiting...")    
    sys.exit(0)

def initialize_resources():
    global status, mos, img_paths, BATCHES

    # load labels
    mos = labels.load_labels(MOS_PATH, IMG_DIRPATH)
    log.logprint(f"Loaded {mos.shape[0]} labels")
    
    if (mos.shape[0] == 0):
        log.logprint("Fatal error: no labels found")
        sys.exit(1)

    # image list
    img_paths = images.get_image_list(IMG_DIRPATH)
    img_paths = IMG_DIRPATH + "/" + img_paths
    log.logprint(f"Found {len(img_paths)} images")

    # batches
    if len(img_paths) % BATCH_SIZE != 0:
        log.logprint("Warning: number of images is not divisible by batch size")
    BATCHES = math.floor(len(img_paths)/BATCH_SIZE)

    # status
    if not log.status_exists():
        log.logprint("Created status file")
        log.write_status({'epoch': 0, 'batch': 0})
    
    status = log.read_status()
    log.logprint(f"Loaded status file: {status}")

def initialize_model():
    global model

    if not models.model_exists(MODEL_PATH):
        model = models.init_model(MAX_HEIGHT, MAX_WIDTH, RATINGS)
        log.logprint(f"Initialized new model with max image dims: {MAX_WIDTH}x{MAX_HEIGHT}")
        return
    
    try:
        model = models.load_model(MODEL_PATH)
        log.logprint(f"Loaded model from file")
    except Exception as e:
        log.logprint(f"Fatal Error: Could not load model file: {e}")
        sys.exit(1)

def load_img(path, label):
    image = images.load_img(path, MAX_HEIGHT, MAX_WIDTH)
    return image, label

def main():
    global status, model

    log.logprint("Program starting up...")
    if DEBUG:
        log.logprint("Started with DEBUG=True")
    
    initialize_resources()

    if (status['epoch'] >= EPOCHS):
        log.logprint(f"Target number of epochs {EPOCHS} already achieved. Exiting...")
        sys.exit(0)

    initialize_model()

    dataset = tf.data.Dataset.from_tensor_slices((img_paths, mos))
    dataset = dataset.map(load_img)
    dataset = dataset.batch(BATCH_SIZE)

    history = model.fit(dataset, epochs=1)
    model.save(MODEL_PATH)
    
    log.logprint("Program completed")

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    main()
