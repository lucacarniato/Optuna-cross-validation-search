import numpy as np
from sklearn.utils import class_weight
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold
from sklearn.base import clone

import optuna
from pathlib import Path
import os


class Objective:

    def __init__(self, classifier, parameter_distributions, cv, x, y, class_weights, sample_weights):
        self.classifier = classifier
        self.parameter_distributions = parameter_distributions
        self.cv = cv
        self.x = x
        self.y = y
        self.class_weights = class_weights
        self.sample_weights = sample_weights

    def __call__(self, trial):

        parameters = {name: trial._suggest(name, distribution) for name, distribution in
                      self.parameter_distributions.items()}
        score = 0.0

        for X_train, X_test in KFold(self.cv, shuffle=False).split(self.x):
            train_x_fold, train_y_fold = self.x[X_train], self.y[X_train]
            test_x_fold, test_y_fold = self.x[X_test], self.y[X_test]

            self.classifier.set_params(**parameters)

            if hasattr(self.classifier, "name") and self.classifier.name == "keras_model":
                self.classifier.fit(train_x_fold, train_y_fold, self.class_weights, test_x_fold, test_y_fold)
            else:
                # clone un-fit classifier
                self.classifier = clone(self.classifier)
                self.classifier.fit(train_x_fold, train_y_fold, sample_weight=self.sample_weights[X_train])

            test_y_fold_pred = self.classifier.predict(X=test_x_fold)
            score -= accuracy_score(y_true=test_y_fold, y_pred=test_y_fold_pred)

        return score / self.cv


class OptunaCrossValidationSearch:
    """ A base class implementing cross validation
    Parameters:
    """

    """  
    X (array): the array of features
    y (array): the array of targets
    balance (str): weighting scheme ('equal' or None)
    cv: the number of cross validations
    """

    def __init__(self, classifier, parameter_distributions, cv_folds, n_trials, sample_weight_balance):
        self.classifier = classifier
        self.parameter_distributions = parameter_distributions
        self.cv_folds = cv_folds
        self.n_trials = n_trials
        self.sample_weight_balance = sample_weight_balance

    def optuna_get_study(self, remove_storage=True):

        model_name = type(self.classifier).__name__
        study_name = model_name + "_optimization"
        file_storage_name = model_name + ".sqlite"
        storage = "sqlite:///" + file_storage_name
        storage_path = Path(file_storage_name)

        if remove_storage and storage_path.is_file():
            os.remove(file_storage_name)

        return optuna.create_study(study_name=study_name, load_if_exists=True, storage=storage)

    def fit(self, x, y):

        x = np.array(x)
        y = np.array(y)

        unique_values = np.unique(y)
        class_weights = class_weight.compute_class_weight(self.sample_weight_balance, unique_values, y)
        class_weights = {i: class_weights[i] for i in range(len(unique_values))}

        sample_weights = np.zeros(len(y), dtype=np.float)
        for i, val in enumerate(y):
            for j, unique_val in enumerate(unique_values):
                if val == unique_val:
                    sample_weights[i] = class_weights[j]
                    break

        objective = Objective(self.classifier,
                              self.parameter_distributions,
                              self.cv_folds,
                              x,
                              y,
                              class_weights,
                              sample_weights)

        study = self.optuna_get_study(remove_storage=True)

        print("Searching the best hyperparameters...")

        study.optimize(objective, n_trials=self.n_trials)

        print("Finished searching the best hyperparameters...")

        study = self.optuna_get_study(remove_storage=False)
        self.classifier.set_params(**study.best_params)

        if hasattr(self.classifier, "name") and self.classifier.name == "keras_model":
            self.classifier.fit(x, y, class_weight=class_weights)
        else:
            self.classifier.fit(x, y, sample_weight=sample_weights)

        return self

    def predict(self, X):
        return self.classifier.predict(X)
