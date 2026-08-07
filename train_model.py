"""
Train a movie-review sentiment classifier (Negative / Neutral / Positive)
from scratch using TensorFlow / Keras.

Dataset: Stanford Sentiment Treebank (SST-5), which contains real sentences
drawn from Rotten Tomatoes movie reviews, each fine-grained labelled 1-5
(very negative -> very positive) by human annotators. We collapse the
5 fine-grained labels into 3 classes:

    labels 1, 2  -> Negative (0)
    label  3     -> Neutral  (1)   <-- a REAL neutral class from the dataset,
                                        not a synthetic / made-up one
    labels 4, 5  -> Positive (2)

This keeps the "neutral" class grounded in genuine human annotations
(sentences the raters themselves judged as neither positive nor negative),
rather than inventing neutral examples.
"""

import re
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

DATA_DIR = "data"
MODEL_DIR = "model"
MAX_WORDS = 10000
MAX_LEN = 40
EMBED_DIM = 64

LABEL_MAP = {1: 0, 2: 0, 3: 1, 4: 2, 5: 2}  # -> Negative=0, Neutral=1, Positive=2
CLASS_NAMES = ["Negative", "Neutral", "Positive"]


def load_split(path):
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            # format: __label__N\t<sentence>
            m = re.match(r"__label__(\d)\t(.*)", line)
            if not m:
                continue
            fine_label = int(m.group(1))
            sentence = m.group(2)
            texts.append(sentence)
            labels.append(LABEL_MAP[fine_label])
    return texts, labels


def main():
    print("Loading SST-5 movie review data...")
    train_texts, train_labels = load_split(f"{DATA_DIR}/sst_train.txt")
    dev_texts, dev_labels = load_split(f"{DATA_DIR}/sst_dev.txt")
    test_texts, test_labels = load_split(f"{DATA_DIR}/sst_test.txt")

    print(f"train={len(train_texts)} dev={len(dev_texts)} test={len(test_texts)}")
    for name, labels in [("train", train_labels), ("dev", dev_labels), ("test", test_labels)]:
        counts = np.bincount(labels, minlength=3)
        print(f"  {name} class counts (Neg/Neu/Pos): {counts.tolist()}")

    tokenizer = Tokenizer(num_words=MAX_WORDS, oov_token="<OOV>")
    tokenizer.fit_on_texts(train_texts)

    def prep(texts):
        seqs = tokenizer.texts_to_sequences(texts)
        return pad_sequences(seqs, maxlen=MAX_LEN, padding="post", truncating="post")

    X_train, X_dev, X_test = prep(train_texts), prep(dev_texts), prep(test_texts)
    y_train = np.array(train_labels)
    y_dev = np.array(dev_labels)
    y_test = np.array(test_labels)

    model = keras.Sequential([
        keras.layers.Embedding(MAX_WORDS, EMBED_DIM, input_length=MAX_LEN),
        keras.layers.Bidirectional(keras.layers.LSTM(64, return_sequences=False)),
        keras.layers.Dropout(0.5),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(3, activation="softmax"),
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=3, restore_best_weights=True
    )

    model.fit(
        X_train, y_train,
        validation_data=(X_dev, y_dev),
        epochs=15,
        batch_size=64,
        callbacks=[early_stop],
        verbose=2,
    )

    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest accuracy: {test_acc:.4f}  |  Test loss: {test_loss:.4f}")

    # Save model + tokenizer
    model.save(f"{MODEL_DIR}/sentiment_model.keras")
    with open(f"{MODEL_DIR}/tokenizer.pickle", "wb") as f:
        pickle.dump(tokenizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(f"{MODEL_DIR}/config.pickle", "wb") as f:
        pickle.dump({"max_len": MAX_LEN, "class_names": CLASS_NAMES}, f)

    print("Saved model to model/sentiment_model.keras")
    print("Saved tokenizer to model/tokenizer.pickle")


if __name__ == "__main__":
    main()
