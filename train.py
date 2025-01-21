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
HISTORY_PATH = f'{project_dir}/history.csv'

MOS_PATH = f'{DATA_PATH}/mos.csv'
IMG_DIRPATH = f'{DATA_PATH}/images/train'

MAX_HEIGHT = 1080
MAX_WIDTH = 1920
RATINGS = 41 # range 1.0, 5.0 with step 0.1
BATCH_SIZE = 5
BATCHES = None
EPOCHS = 10

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

class CustomBatchCallback(tf.keras.callbacks.Callback):
    def on_batch_end(self, batch, logs=None):
        global status

        status['batch'] = batch
        log.log(f"Completed batch {batch}/{BATCHES} of epoch {status['epoch']}/{EPOCHS}")

        log.write_status(status)
        log.append_csv_history(HISTORY_PATH, status['batch'], status['epoch'], logs['accuracy'], logs['loss'])
        
        log.log(f"Saved status and history")

    def on_epoch_end(self, epoch, logs=None):
        global status

        status['epoch'] = epoch
        status['batch'] = 0

        log.log(f"Completed epoch {epoch}/{EPOCHS} completed")
        
        log.write_status(status)
        models.save_model(self.model, MODEL_PATH)
        
        log.log(f"Saved model")

def main():
    global status, model

    log.logprint("Program starting up...")
    
    initialize_resources()
    initialize_model()

    dataset = tf.data.Dataset.from_tensor_slices((img_paths, mos))
    dataset = dataset.map(load_img)
    dataset = dataset.batch(BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)

    custom_callback = CustomBatchCallback()

    history = model.fit(dataset, verbose=1, initial_epoch=status['epoch'], epochs=EPOCHS, callbacks=[custom_callback])
    
    log.logprint("Program completed")

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    main()
