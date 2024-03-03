import tensorflow as tf
from basic_pitch import ICASSP_2022_MODEL_PATH
model = tf.saved_model.load(str(ICASSP_2022_MODEL_PATH))


# Optional: Perform optimizations specific to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Convert the TensorFlow model to TensorFlow Lite format
tflite_model = converter.convert()

# Save the TensorFlow Lite model to a file
with open('converted_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("Conversion to TensorFlow Lite complete.")