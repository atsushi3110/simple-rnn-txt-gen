import sys
import re
import numpy as np
import json

from keras.models import Sequential, model_from_json
from keras.layers import Dense, Activation, Dropout
from keras.layers import LSTM



def clean_text(text):

    # Encode from unicode, ignoring characters that don't make sense in standard speech
    try:
        text = unicode(text, errors="ignore")
    except:
        pass

    # Fix a few problems : nuisance characters, new lines, extra spaces...
    nuisance_chars = ["\n", "=", "(", ")", "[", "[", "/"]
    for char in nuisance_chars:
        text = text.replace(char, "")

    # Look for blocks of several capital letters in a row, followed by a colon, and remove them
    # These are typically things like "AUDIENCE:"
    text = re.sub(r"[A-Z]{2,}:", "", text)

    # There are occasional full stops without a space before the next sentence; get rid of those.
    text = re.sub(r"\.([a-zA-Z])", r". \1", text)

    # Occasionally, there are two spaces in a row.
    text = text.replace("  ", " ")

    return text



def predict(text):

    # Characters to predict
    prediction_length = 200

    # Temperature of the Boltzmann distribution
    temperature = 0.2

    # Load and compile the current model
    model = model_from_json(json.dumps(json.load(open("../model.json"))))
    model.load_weights("../weights.h5")
    model.compile(loss="categorical_crossentropy", optimizer="adam")

    # Clean the input text, ensuring it's exactly primer_length characters long
    if text:
        text = clean_text(text)
        while len(text) < primer_length:
            text = " " + text
        if len(text) > primer_length:
            text = text[-primer_length:]
    # If we weren't passed text, pick something random from the corpus
    else:
        with open("../data/trump_corpus", "r") as f:
            corpus = f.read()
        idx = np.random.randint(0, len(corpus) - primer_length)
        text = corpus[idx : idx + primer_length]

    # Read in the required objects
    with open("required_objects.pickle", "rb") as f:
        required_objects = pickle.load(f)
    alphabet = required_objects["alphabet"]
    alphabet_indices = required_objects["alphabet_indices"]
    indices_alphabet = required_objects["indices_alphabet"]
    primer_length = required_objects["primer_length"]

    # Initialise the predictions array
    y = text

    # Generate some predictions
    for i in range(prediction_length):

        # Initialise the prompt and
        X = np.zeros((1, primer_length, len(alphabet)))
        for idx, char in enumerate(text[-primer_length:]):
            X[idx, alphabet_indices[char]] = 1

        # Make predictions character by character
        predictions = model.predict(X, verbose=0)[0]
        next_index = sample(predictions, temperature)
        next_char = indices_alphabet[next_index]

        # Add the prediction to the output array
        y += next_char

    return y




# Helper function :
# Sample from a Boltzmann distribution with energies proportional to the probabilities
# returned by the LSTM network, as a function of a temperature parameter
def sample(energies, temperature=1.0):
    energies = np.log(energies) / temperature
    energies = np.exp(energies) / np.sum(np.exp(energies))
    return np.argmax(np.random.multinomial(1, energies))