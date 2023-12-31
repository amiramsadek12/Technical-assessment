import matplotlib.pyplot as plt
import numpy as np
from typing import List
import joblib
import random

import tensorflow as tf
from keras.models import Model
from keras.layers import Input, Reshape, Dropout, LSTM, Dense
from keras.optimizers import SGD
from keras.regularizers import l2
from keras.preprocessing.sequence import pad_sequences


from encoder import LabelEncoder

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data.normlengthdata import NormLengthData
from data.normvaluesdata import NormValuesData


NUM_EPOCHS = 100
BATCH_SIZE = 1
LEARNING_RATE = 0.1


class ActionModel:
    """Class for action model."""

    def __init__(self, encoder: LabelEncoder) -> None:
        """Create an RNN architecture based on LSTM.

        Args:
            encoder: encoder used for input data.


        """
        input_layer = Input(shape=(None, 20))

        # Reshape layer to prepare the input data for LSTM
        reshaped_input = Reshape((1, 20))(input_layer)

        Danse_layer = Dense(64, activation="relu")(reshaped_input)

        # LSTM layers with dropout.
        lstm_layer = LSTM(
            units=128, kernel_regularizer=l2(0.005), return_sequences=True
        )(Danse_layer)
        lstm_layer = Dropout(0.25)(lstm_layer)
        lstm_output = LSTM(units=128)(lstm_layer)

        Danse_layer = Dense(32, activation="relu")(lstm_output)
        output_layer = Dense(len(encoder.classes), activation="softmax")(
            lstm_output
        )  # noqa:E501

        self.model = Model(inputs=input_layer, outputs=output_layer)
        self.encoder = encoder

    def compile(self) -> None:
        """Compile the model."""
        self.model.compile(
            optimizer=SGD(learning_rate=LEARNING_RATE),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

    def fit(
        self, X_train: List, y_train: List, X_val: List = [], y_val: List = []
    ) -> None:
        """Starting Model training.

        Args:
            X_train: Sequences used for training.
            y_train: Labels of the provided sequences.
            X_val (list, optional): Sequences for validation. Defaults to [].
            y_val (list, optional): Labels of validation set. Defaults to [].
        """
        self.history = self.model.fit(
            X_train,
            y_train,
            epochs=NUM_EPOCHS,
            batch_size=BATCH_SIZE,
            validation_data=(X_val, y_val),
            callbacks=[],
        )

    def predict_standalone(self, X: List):
        """Given a list of sequence. eg, ["driblle", "pass"],
        the output is the next action for example "walk"."""
        encoded_test_case = self.encoder.encode(X)
        padded_test_case = pad_sequences(
            [encoded_test_case],
            padding="pre",
            truncating="pre",
            maxlen=20,
            value=18,  # noqa:E501
        )
        predictions = self.model.predict(padded_test_case)
        predicted_classes = predictions.argmax(axis=1)
        predicted_action = self.encoder.decode(predicted_classes)
        if predicted_action[0] == X[-1] and predicted_action[0] == X[-2]:
            second_best_predicted_classes = predictions.argsort(axis=1)[
                :, -2:-1
            ]  # noqa:E501
            predicted_action = self.encoder.decode(
                second_best_predicted_classes[0]
            )  # noqa:E501
        return predicted_action

    def predict(self, X) -> int:
        """Run prediction on a single sequence X."""
        return self.model.predict(X)

    def evaluate(self, X, y) -> None:
        """Evaluate model performance using given data."""
        test_loss, test_accuracy = self.model.evaluate(X, y)
        print(f"Test loss: {test_loss} \n" f"Test accuracy: {test_accuracy}")

    def plot(self) -> None:
        """Extract training and validation accuracy
        cand loss from the history and plot it."""
        train_accuracy = self.history.history["accuracy"]
        val_accuracy = self.history.history["val_accuracy"]
        train_loss = self.history.history["loss"]
        val_loss = self.history.history["val_loss"]

        plt.figure(figsize=(12, 4))
        plt.subplot(1, 2, 1)
        plt.plot(train_accuracy, label="Training Accuracy")
        plt.plot(val_accuracy, label="Validation Accuracy")
        plt.xlabel("Epoch")
        plt.ylabel("Accuracy")
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(train_loss, label="Training Loss")
        plt.plot(val_loss, label="Validation Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()

        plt.tight_layout()
        plt.show()

    def save(self, fp="../data/model/action_model.h5"):
        """Save model to a given Directory."""
        self.model.save(fp)

    @classmethod
    def load(cls, encoder, fp="../data/model/action_model.h5"):
        """Load saved model."""
        instance = cls(encoder)
        instance.model = tf.keras.models.load_model(fp)
        return instance


class GaitLengthPredictor:
    """Base model for predicting the gait length based on the action."""

    def __init__(self, data: NormLengthData) -> None:
        self.data = data
        self.model = RandomForestRegressor(n_estimators=100, random_state=1234)

    def fit(self, X, y) -> None:
        """Train the model on the provided data."""
        self.model.fit(X, y)

    def predict(self, X) -> np.ndarray:
        y_pred = self.model.predict(np.array(X).reshape(1, -1))
        action_mean_value, action_std_value = self.data.action_interval[X]
        lower_bound = action_mean_value - 2 * action_std_value
        upper_bound = action_mean_value + 2 * action_std_value
        choices = range(int(lower_bound), int(upper_bound))
        y_pred_clipped = np.clip(
            y_pred,
            random.choice(choices),
            random.choice(choices),
        )
        return int(y_pred_clipped)

    def evaluate(self, X_val, y_val, X_test, y_test) -> None:
        """Evaluate model performance against val and test set."""
        y_val_pred = self.model.predict(X_val)
        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_mse = mean_squared_error(y_val, y_val_pred)
        val_rmse = mean_squared_error(y_val, y_val_pred, squared=False)
        val_r2 = r2_score(y_val, y_val_pred)

        print(
            "Validation Metrics: \n"
            f"MAE: {val_mae} \n"
            f"MSE: {val_mse} \n"
            f"RMSE: {val_rmse} \n"
            f"R-squared (R2): {val_r2}\n"
        )

        y_test_pred = self.model.predict(X_test)
        # Calculate evaluation metrics on the test set
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        test_rmse = mean_squared_error(y_test, y_test_pred, squared=False)
        test_r2 = r2_score(y_test, y_test_pred)

        print(
            "Test Metrics: \n"
            f"MAE: {test_mae} \n"
            f"MSE: {test_mse} \n"
            f"RMSE: {test_rmse} \n"
            f"R-squared (R2): {test_r2}\n"
        )

    def save(self, fp="../data/model/gait_model.pkl"):
        """Save the model."""
        joblib.dump(self.model, fp)

    @classmethod
    def load(cls, fp="../data/model/gait_model.pkl"):
        """load the model."""
        loaded_model = joblib.load(fp)
        loaded_data = NormLengthData.load()
        instance = cls(data=loaded_data)
        instance.model = loaded_model
        return instance


class GaitValuesPredictor:
    """Base model for predicting the values in the gait based on the action."""

    def __init__(self, data: NormValuesData) -> None:
        self.data = data
        self.model = GradientBoostingRegressor(
            n_estimators=50, learning_rate=0.01, random_state=42
        )

    def fit(self, X, y) -> None:
        """Train the model on the provided data."""
        self.model.fit(X, y)

    def predict(self, X, gait_length=1) -> np.ndarray:
        predicted_values = []
        for _ in range(0, gait_length):
            y_pred = self.model.predict(np.array(X).reshape(1, -1))
            action_mean_value, action_std_value = self.data.action_interval[X]
            lower_bound = action_mean_value - 2 * action_std_value
            upper_bound = action_mean_value + 2 * action_std_value
            choices = range(int(lower_bound), int(upper_bound))
            y_pred_clipped = np.clip(
                y_pred,
                random.choice(choices),
                random.choice(choices),
            )
            predicted_values.append(y_pred_clipped)
        return predicted_values

    def evaluate(self, X_val, y_val, X_test, y_test) -> None:
        """Evaluate model performance against val and test set."""
        y_val_pred = self.model.predict(X_val)
        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_mse = mean_squared_error(y_val, y_val_pred)
        val_rmse = mean_squared_error(y_val, y_val_pred, squared=False)
        val_r2 = r2_score(y_val, y_val_pred)

        print(
            "Validation Metrics: \n"
            f"MAE: {val_mae} \n"
            f"MSE: {val_mse} \n"
            f"RMSE: {val_rmse} \n"
            f"R-squared (R2): {val_r2}\n"
        )

        y_test_pred = self.model.predict(X_test)
        # Calculate evaluation metrics on the test set
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        test_rmse = mean_squared_error(y_test, y_test_pred, squared=False)
        test_r2 = r2_score(y_test, y_test_pred)

        print(
            "Test Metrics: \n"
            f"MAE: {test_mae} \n"
            f"MSE: {test_mse} \n"
            f"RMSE: {test_rmse} \n"
            f"R-squared (R2): {test_r2}\n"
        )

    def save(self, fp="../data/model/gait_values_model.pkl"):
        """Save the model."""
        joblib.dump(self.model, fp)

    @classmethod
    def load(cls, fp="../data/model/gait_values_model.pkl"):
        """load the model."""
        loaded_model = joblib.load(fp)
        loaded_data = NormValuesData.load()
        instance = cls(data=loaded_data)
        instance.model = loaded_model
        return instance
