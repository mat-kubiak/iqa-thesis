import os, sys, time, signal, math
import tensorflow as tf
import numpy as np

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f'{project_dir}/src')

import images, labels, models
from tracker import Tracker

# input
DATA_DIR = f'{project_dir}/data'
MOS_PATH = f'{DATA_DIR}/mos.csv'
FIT_IMG_DIR = f'{DATA_DIR}/images/train'

# output
OUTPUT_DIR = f'{project_dir}/output'
MODEL_PATH = f'{OUTPUT_DIR}/model.keras'
BACKUP_PATH = f'{OUTPUT_DIR}/backup.keras'

HEIGHT = 512
WIDTH = 512
FIT_BATCH_SIZE = 20
EPOCHS = 50
AUGMENT = False
IS_CATEGORICAL = False

# if set, limits data to n first samples
FIT_LIMIT = None

tracker = None
model = None
fit_mos = None
fit_imgs = None
batches_per_epoch = None
total_batches = 0

def signal_handler(sig, frame):
    tracker.logprint(f"Received signal {sig}")
    
    models.save_model(model, BACKUP_PATH)

    tracker.logprint(f"Backup saved at batch {tracker.batch}/{batches_per_epoch} epoch {tracker.epoch}/{EPOCHS}")
    tracker.logprint(f"Exiting...")
    sys.exit(0)

def initialize_resources():
    global fit_mos, fit_imgs, batches_per_epoch

    fit_imgs = images.get_image_list(FIT_IMG_DIR)
    fit_mos = labels.load(MOS_PATH, FIT_IMG_DIR, IS_CATEGORICAL)
    tracker.logprint(f"Detected {len(fit_mos)} labels and {len(fit_imgs)} images")

    if FIT_LIMIT != None:
        fit_imgs = fit_imgs[:FIT_LIMIT]
        fit_mos = fit_mos[:FIT_LIMIT]
        tracker.logprint(f"Limiting data to {FIT_LIMIT} first samples")

    extra_batch_required = len(fit_imgs) % FIT_BATCH_SIZE != 0
    batches_per_epoch = math.floor(len(fit_imgs)/FIT_BATCH_SIZE) + extra_batch_required

def initialize_model():
    try:
        model = models.load_model(MODEL_PATH)
        tracker.logprint(f"Loaded model from file")
    
    except Exception as e:
        model = models.init_model(HEIGHT, WIDTH, IS_CATEGORICAL)
        tf.keras.utils.plot_model(model, to_file=f"{OUTPUT_DIR}/arch.png", show_shapes=True, show_dtype=True, show_layer_names=True, show_trainable=True)
        tracker.logprint(f"Initialized new model")
    
    model.summary()
    return model

class CustomBatchCallback(tf.keras.callbacks.Callback):
    def on_batch_end(self, batch, logs=None):
        global total_batches

        tracker.batch = batch + 1
        total_batches += 1
        tracker.log(f"Completed batch {tracker.batch}/{batches_per_epoch} of epoch {tracker.epoch}/{EPOCHS}")

        tracker.save_status()
        tracker.append_csv_history(total_batches, logs)
        
        tracker.log(f"Saved status and history")

    def on_epoch_end(self, epoch, logs=None):
        tracker.epoch = epoch + 1
        tracker.batch = 0

        tracker.log(f"Completed epoch {tracker.epoch}/{EPOCHS} completed")
        
        tracker.save_status()
        models.save_model(self.model, MODEL_PATH)
        
        tracker.log(f"Saved model")

def load_image(path, label):
    image = images.load_image(path, HEIGHT, WIDTH, AUGMENT)
    return image, label

def main():
    global model, tracker

    tracker = Tracker(OUTPUT_DIR)

    tracker.logprint("Program starting up...")
    
    initialize_resources()
    model = initialize_model()

    dataset = (tf.data.Dataset.from_tensor_slices((fit_imgs, fit_mos))
        .map(load_image, num_parallel_calls=tf.data.experimental.AUTOTUNE)
        .shuffle(buffer_size=1000)
        .batch(FIT_BATCH_SIZE)
        .prefetch(tf.data.experimental.AUTOTUNE)
    )

    custom_callback = CustomBatchCallback()

    history = model.fit(
        dataset,
        verbose=1,
        initial_epoch=tracker.epoch,
        epochs=EPOCHS,
        callbacks=[custom_callback]
    )

    tracker.logprint("Program completed")

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    main()
