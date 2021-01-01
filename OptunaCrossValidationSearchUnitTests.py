import unittest
import optuna
import sklearn
import sklearn.datasets
import numpy as np
from OptunaCrossValidationSearch import OptunaCrossValidationSearch
from ModelKerasFullyConnected import ModelKerasFullyConnected
import lightgbm as lgb
import xgboost as xgb
import ModelKerasFullyConnected


def get_train_val(train_fraction):
    dataset = sklearn.datasets.load_digits()
    x = dataset.data
    y = dataset.target
    split = int(len(x) * train_fraction)
    return np.array(x[:split]), np.array(y[:split]), np.array(x[split:]), np.array(y[split:])


class TestModels(unittest.TestCase):

    def setUp(self):
        dataset = sklearn.datasets.load_digits()
        self.params = {'X': dataset.data, 'y': dataset.target, 'balance': 'balanced', 'cv': 3}

    def test_lgb_model(self):
        X_train, y_train, X_test, y_test = get_train_val(0.8)

        classifier = lgb.LGBMClassifier(n_jobs=4)
        parameter_distributions = {'min_data_in_leaf': optuna.distributions.IntUniformDistribution(10, 100),
                                   'bagging_fraction': optuna.distributions.LogUniformDistribution(0.01, 1.0)}
        optuna_cross_validation = OptunaCrossValidationSearch(classifier=classifier,
                                                              parameter_distributions=parameter_distributions,
                                                              cv_folds=5,
                                                              n_trials=10,
                                                              sample_weight_balance='balanced')
        optuna_cross_validation.fit(X_train, y_train)
        y_test_pred = optuna_cross_validation.predict(X_test)
        score = sklearn.metrics.accuracy_score(y_test, y_test_pred)
        self.assertGreater(score, 0.80)

    def test_xgboost_model(self):
        X_train, y_train, X_test, y_test = get_train_val(0.8)

        classifier = xgb.XGBClassifier(n_jobs=3)

        parameter_distributions = {'max_depth': optuna.distributions.IntUniformDistribution(5, 20),
                                   'min_child_weight': optuna.distributions.IntUniformDistribution(8, 50),
                                   'gamma': optuna.distributions.LogUniformDistribution(0.1, 10.0)}
        optuna_cross_validation = OptunaCrossValidationSearch(classifier=classifier,
                                                              parameter_distributions=parameter_distributions,
                                                              cv_folds=5,
                                                              n_trials=10,
                                                              sample_weight_balance='balanced')
        optuna_cross_validation.fit(X_train, y_train)
        y_test_pred = optuna_cross_validation.predict(X_test)
        score = sklearn.metrics.accuracy_score(y_test, y_test_pred)
        self.assertGreater(score, 0.80)

    def test_keras_model(self):
        x_train, y_train, x_test, y_test = get_train_val(0.8)

        classifier = ModelKerasFullyConnected.ModelKerasFullyConnected(x_train.shape, len(np.unique(y_train)))
        parameter_distributions = {'num_units': optuna.distributions.IntUniformDistribution(32, 128),
                                   'num_hidden': optuna.distributions.IntUniformDistribution(0, 3),
                                   'dropout': optuna.distributions.LogUniformDistribution(0.05, 0.4),
                                   'learning_rate': optuna.distributions.LogUniformDistribution(1e-8, 1e-4)}

        optuna_cross_validation = OptunaCrossValidationSearch(classifier=classifier,
                                                              parameter_distributions=parameter_distributions,
                                                              cv_folds=5,
                                                              n_trials=10,
                                                              sample_weight_balance='balanced')
        optuna_cross_validation.fit(x_train, y_train)

        y_test_pred = optuna_cross_validation.predict(x_test)
        score = sklearn.metrics.accuracy_score(y_test, y_test_pred)
        self.assertGreater(score, 0.80)


def run_tests():
    x_train, y_train, x_test, y_test = get_train_val(0.8)

    classifier = xgb.XGBClassifier(n_jobs=6)

    parameter_distributions = {'max_depth': optuna.distributions.IntUniformDistribution(5, 20),
                               'min_child_weight': optuna.distributions.IntUniformDistribution(8, 50),
                               'gamma': optuna.distributions.LogUniformDistribution(0.1, 10.0)}

    optuna_cross_validation = OptunaCrossValidationSearch(classifier, parameter_distributions, 5, 40, 'balanced')
    optuna_cross_validation.fit(x_train, y_train)

    y_test_pred = optuna_cross_validation.predict(x_test)
    score = sklearn.metrics.accuracy_score(y_test, y_test_pred)
    print(score)


if __name__ == '__main__':
    unittest.main()
