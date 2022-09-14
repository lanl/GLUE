"""
Random Forest Learner Capability.

Functions in this file play the same role as in the nn_learner.py file;
Refer to the documentation.
"""
import warnings

import numpy as np
# Built with numpy '1.16.3'

# Built with pytorch 1.3.1

import sklearn.metrics
import sklearn.ensemble
import sklearn.model_selection
# Built with sklearn 0.20.1

from alInterface import getAllGNDData
from glueCodeTypes import SolverCode, BGKInputs, BGKOutputs


class Model():
    """
    Base class for RF models.
    """

    def __init__(self, solver, forest, uq_fussyness, err_info=None):
        self.forest = forest
        self.err_info = err_info
        self.solver = solver
        self.uq_fussyness = uq_fussyness

    def __call__(self, request_params):
        request_params = self.pack_inputs(request_params)

        result_mean, result_error = self.process(request_params)

        result_mean = self.unpack_outputs(result_mean)
        result_error = self.unpack_outputs(result_error)
        return result_mean, result_error

    def process(self, request_params, perform_column_extraction=True):  # as a numpy array
        batched = request_params.ndim > 1

        request_params = np.asarray(request_params)
        if perform_column_extraction:
            request_params = request_params[..., SOLVER_INDEXES[self.solver]["input_slice"]]

        if not batched:
            request_params = request_params[np.newaxis]

        results = np.asarray([tree.predict(request_params) for tree in self.forest.estimators_])

        mean = results.mean(axis=0)
        std = results.std(axis=0)

        if not batched:
            mean = mean[0]
            std = std[0]

        return mean, std

    def calibrate(self, dataset):
        pred, uncertainty = self.process(dataset[:][0], perform_column_extraction=False)
        true = dataset[:][-1]
        abserr = np.abs(pred - true)

        calibration = np.mean(abserr, axis=0) / np.mean(uncertainty, axis=0)

        calibration *= self.uq_fussyness

        self.err_info /= calibration

        inactive_columns = (np.std(abserr, axis=0) == 0) & (np.std(uncertainty, axis=0) == 0)

        warnings.warn(
            "Inactive columns detected: {} , they will not be included in isokay.".format(np.where(inactive_columns)))
        self.err_info[inactive_columns] = np.inf

    def process_iserrok_fuzzy(self, errbars):
        return errbars / self.err_info

    def process_iserrok(self, errbars):
        return errbars < self.err_info

    def iserrok(self, errbars):
        errbars = self.pack_outputs(errbars)
        iserrok = self.process_iserrok(errbars)
        iserrok = self.unpack_outputs(iserrok)
        return iserrok

    def iserrok_fuzzy(self, errbars):
        errbars = self.pack_outputs(errbars)
        iserrok = self.process_iserrok_fuzzy(errbars)
        iserrok = self.unpack_outputs(iserrok)
        return iserrok

    def pack_outputs(self, request):
        return NotImplemented

    def pack_inputs(self, request):
        return NotImplemented

    def unpack_outputs(self, result):
        return NotImplemented


# # BGKInputs
# #  Temperature: float
# #  Density: float[4]
# #  Charges: float[4]
# BGKInputs = collections.namedtuple('BGKInputs', 'Temperature Density Charges')
# # BGKoutputs
# #  Viscosity: float
# #  ThermalConductivity: float
# #  DiffCoeff: float[10]
# BGKOutputs = collections.namedtuple('BGKOutputs', 'Viscosity ThermalConductivity DiffCoeff')

class BGKModel(Model):
    def pack_inputs(self, request):
        packed_request = np.concatenate([[request.Temperature], request.Density, request.Charges])

        return packed_request

    def unpack_outputs(self, packed_result):
        # All things predicted
        v = packed_result[0]
        tc = packed_result[1]
        diff = packed_result[2:]
        unpacked_result = BGKOutputs(v, tc, diff)

        return unpacked_result

    def pack_outputs(self, outputs):
        output_vals = np.concatenate([[outputs.Viscosity], [outputs.ThermalConductivity], outputs.DiffCoeff])
        return output_vals


# Parameters governing input and outputs to problem

SOLVER_INDEXES = {
    # HARDCODED TO 3 DIFFUSION TERM PROBLEM
    SolverCode.BGK: dict(
        input_slice=slice(0, 9),  # For full version: slice(0,9),
        output_slice=slice(10, 22),  # For full version? slice(10,22)?
        n_inputs=9,  # For full version: 9
        n_outputs=12,  # For full version: 12?
        model_type=BGKModel,  #
    )
    # Other solver codes...
}

DEFAULT_HYPERSEARCH_CONFIG = dict(
    min_samples_split=[2, 4, 6, 10, 20, 40],
    max_depth=[1, 2, 3, 4, 6, 8, 10, 14],
    min_samples_leaf=[1, 2, 3, 4, 5],
    cv=3,
    n_iter=50,
    n_estimators=[200],
    max_features=[1.],
)

# Bundle of all learning-related parameters
DEFAULT_LEARNING_CONFIG = dict(
    hyper_config=DEFAULT_HYPERSEARCH_CONFIG,
    solver_type=SolverCode.BGK,
    uq_fussyness=2. / 3., # Reasonable value for RF learner
)


def assemble_dataset(raw_dataset, solver_code):
    features = np.asarray(raw_dataset[:, SOLVER_INDEXES[solver_code]["input_slice"]])
    print("Feature shape:", features.shape)
    print(features.std(axis=0))
    targets = np.asarray(raw_dataset[:, SOLVER_INDEXES[solver_code]["output_slice"]])
    print("Targets shape:", targets.shape)
    print(targets.std(axis=0))
    return features, targets


def retrain(db_path, learning_config=DEFAULT_LEARNING_CONFIG):
    solver = learning_config["solver_type"]
    raw_dataset = getAllGNDData(db_path, solver)
    full_dataset = assemble_dataset(raw_dataset, solver)
    features, labels = full_dataset
    hypers = learning_config["hyper_config"].copy()
    cv = hypers.pop('cv')
    n_iter = hypers.pop('n_iter')
    forest = sklearn.ensemble.RandomForestRegressor(oob_score=True)
    searcher = sklearn.model_selection.RandomizedSearchCV(forest, n_iter=n_iter, cv=cv, param_distributions=hypers,
                                                          n_jobs=-1, refit=True)

    searcher.fit(features, labels)
    forest = searcher.best_estimator_
    oob_predictions = forest.oob_prediction_
    err_info = np.sqrt(np.mean((oob_predictions - labels) ** 2, axis=0))
    print("relative rmse:", err_info / np.std(labels, axis=0))

    model = SOLVER_INDEXES[solver]["model_type"](solver, forest, uq_fussyness=learning_config['uq_fussyness'],
                                                 err_info=err_info)
    model.calibrate(full_dataset)
    return model


def l1_score(true, predicted):
    sum_abs_resid = np.abs(true - predicted).sum()
    med = np.median(true)
    sum_abs_dev = np.abs(true - med).sum()
    return 1 - sum_abs_resid / sum_abs_dev


def get_score(predicted, true):
    score = []
    rmse_list = []
    for i, (p, t) in enumerate(zip(predicted.T, true.T)):

        rmse = np.sqrt(sklearn.metrics.mean_squared_error(t, p))

        if p.std() < 1e-300 and t.std() < 1e-300:
            # print("divide by zero error for column",i)
            rsq = 1.
            l1resid = 1.
        else:
            rsq = sklearn.metrics.r2_score(t, p)
            l1resid = l1_score(t, p)

        # HARDCODED: SCORE FOR EACH THING TO PREDICT IS RSQ
        score.append(rsq)
        rmse_list.append(rmse)
        # print(i,rsq,l1resid)

    # HARDCODED: TOTAL SCORE IS PRODUCT OF SCORES FOR EACH TARGET
    score = np.asarray(score)
    # score = np.prod(score*(score>0))
    rmse_list = np.asarray(rmse_list)
    return score, rmse_list
