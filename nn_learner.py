import copy

import torch
import torch.utils.data
import numpy as np

torch.set_default_dtype(torch.float64)

from alInterface import getAllGNDData, SolverCode

import sklearn.metrics

CURRENT_DATABASE = None

class Model():
    """
    Ensemble model. Error bar is std. dev. of networks.
    """
    def __init__(self,solver,networks,err_info=None):
        self.networks = networks
        self.err_info = err_info
        self.solver = solver

    def __call__(self,request_params):
        """
        :param request_params: features for BGK
        :return: result[3], errbar[3]
        """
        batched = request_params.ndim>1
        request_params = torch.as_tensor(request_params[...,SOLVER_INDEXES[self.solver]["input_slice"]])

        if not batched:
            request_params = request_params.unsqueeze(0)

        results = np.asarray([np.asarray(nn(request_params)) for nn in self.networks])

        mean = results.mean(axis=0)
        std = results.std(axis=0)

        if not batched:
            mean = mean[0]
            std = std[0]

        return mean, std

    def calibrate(self,dataset):
        pred,uncertainty = self(dataset[:][0].numpy())
        true = dataset[:][-1].numpy()
        abserr = np.abs(pred-true)

        calibration = np.mean(abserr,axis=0)/np.mean(uncertainty,axis=0)

        # Factor 2 is somewhat arbitrary... larger -> less fussy model.
        # Roughly corresponds to a number of standard deviations
        calibration /= 2

        self.err_info /= calibration

    def iserrok_fuzzy(self,errbars):
        return errbars/self.err_info

    def iserrok(self,errbars):
        return errbars < self.err_info

# Parameters governing input and outputs to problem

SOLVER_INDEXES = {
    SolverCode.BGK:dict(
                        input_slice=slice(0,9),
                        output_slice=slice(12,15),
                        n_inputs = 9,
                        n_outputs = 3,
                    )
    #Other solver codes...
}


#Parameters governing network structure
DEFAULT_NET_CONFIG = dict(
    n_layers=4,
    n_hidden=32,
    activation_type=torch.nn.ReLU,
    layer_type = torch.nn.Linear
    )

#Parameters for ensemble uncertainty
DEFAULT_ENSEMBLE_CONFIG = dict(
    n_members = 10,
    test_fraction = 0.1,
    score_thresh = 0.75,
    max_model_tries = 100,
)


#Parameters for the optimization process
DEFAULT_TRAINING_CONFIG = dict(
    n_epochs=2000,
    optimizer_type=torch.optim.Adam,
    validation_fraction=0.2,
    lr=1e-3,
    patience=20,
    batch_size=5,
    eval_batch_size=10000,
    scheduler_type = torch.optim.lr_scheduler.ReduceLROnPlateau,
    cost_type = torch.nn.MSELoss
)

#Bundle of all learning-related parameters
DEFAULT_LEARNING_CONFIG = dict(
    net_config = DEFAULT_NET_CONFIG,
    ensemble_config = DEFAULT_ENSEMBLE_CONFIG,
    solver_type = SolverCode.BGK,
    training_config = DEFAULT_TRAINING_CONFIG,
)

def assemble_dataset(raw_dataset,solver_code):
    # WARNING HARDCODING FOR BGK TEST
    features = torch.as_tensor(raw_dataset[:,SOLVER_INDEXES[solver_code]["input_slice"]])
    targets = torch.as_tensor(raw_dataset[:,SOLVER_INDEXES[solver_code]["output_slice"]])
    return torch.utils.data.TensorDataset(features,targets)

#prototype, only covers ensemble uncertainties
def retrain(learning_config=DEFAULT_LEARNING_CONFIG):

    solver = learning_config["solver_type"]
    raw_dataset = getAllGNDData(CURRENT_DATABASE,solver)
    full_dataset = assemble_dataset(raw_dataset,solver)


    ensemble_config = learning_config["ensemble_config"]
    n_total = len(full_dataset)
    n_test = int(ensemble_config["test_fraction"]*n_total)
    n_test = max(n_test,2)
    n_train = n_total-n_test
    print("Total / train / test points:",n_total,n_train,n_test)

    networks = []
    network_errors = []
    network_scores = []

    successful_models = 0
    i=0
    while successful_models < ensemble_config["n_members"]:
        i += 1
        if i > ensemble_config["max_model_tries"]:
            break
        print("Good models found:",successful_models)
        print("Training ensemble member",i)

        train_data,test_data = torch.utils.data.random_split(full_dataset, (n_train,n_test))

        #This is a place where we could trivially parallelize training.

        this_model = train_single_model(train_data, learning_config=learning_config)
        model_score,model_errors = get_error_info(this_model,test_data)
        print("Score:",model_score)
        if any(m < ensemble_config["score_thresh"] for m in model_score):
            print("Rejected.")
            continue
        print("Accepted.")

        successful_models+=1

        networks.append(this_model)
        network_scores.append(model_score)
        network_errors.append(model_errors)

    #print("scores",network_scores)
    error_info = np.mean(np.asarray(network_errors),axis=0)

    full_model = Model(solver, networks, error_info)
    full_model.calibrate(full_dataset)

    return full_model


def train_single_model(train_data, learning_config):

    net_config = learning_config["net_config"]
    training_config = learning_config["training_config"]

    #Type parameters
    activation_type = net_config["activation_type"]
    layer_type = net_config["layer_type"]

    #Splitting
    n_total = len(train_data)
    n_valid = int(training_config["validation_fraction"]*n_total)
    n_valid = max(n_valid,2)
    n_train = n_total-n_valid
    train_data, valid_data = torch.utils.data.random_split(train_data, (n_train, n_valid))

    #Normalizing
    train_features, train_labels = (train_data[:])

    inscaler = Scaler.from_tensor(train_features)
    cost_scaler = Scaler.from_tensor(train_labels)
    outscaler = Scaler.from_inversion((cost_scaler))

    #Size parameters
    solver = learning_config["solver_type"]
    indices = SOLVER_INDEXES[solver]

    n_inputs = indices["n_inputs"]
    n_outputs = indices["n_outputs"]
    n_hidden = net_config["n_hidden"]

    layers = [inscaler,layer_type(n_inputs,n_hidden),activation_type()]

    for i in range(net_config["n_layers"]-2):
        layers.append(layer_type(n_hidden,n_hidden))
        layers.append(activation_type())
    layers.append(layer_type(n_hidden,n_outputs))

    train_network = torch.nn.Sequential(*layers)

    cost_fn = training_config["cost_type"]()
    opt = training_config["optimizer_type"](train_network.parameters(),lr=training_config["lr"])
    patience = training_config["patience"]
    scheduler = training_config["scheduler_type"](opt,patience=patience,verbose=False,factor=0.5)


    best_cost = np.inf
    best_params = train_network.state_dict()

    train_dloader = torch.utils.data.DataLoader(train_data,batch_size=training_config["batch_size"],shuffle=True)
    valid_dloader = torch.utils.data.DataLoader(valid_data,batch_size=training_config["eval_batch_size"],shuffle=False)

    # Need to add scales for costs
    for i in range(training_config["n_epochs"]):
        train_epoch(train_dloader,train_network,cost_fn,opt,scaler=cost_scaler)
        eval_cost = evaluate_dataset_errors(valid_dloader,train_network,scaler=cost_scaler).abs().mean().item()
        #if i%100==0: print(eval_cost)
        scheduler.step(eval_cost)
        if eval_cost < best_cost:
            #print("best epoch:",i)
            best_cost = eval_cost
            best_params = copy.deepcopy(train_network.state_dict())
            boredom = 0
        else:
            boredom +=1

        if boredom > 2*patience+1:
            print("Training finalized at epoch",i)
            break
    else:
        print("Training finished due to max epoch",i)





    train_network.load_state_dict(best_params)
    real_scale_network = torch.nn.Sequential(*train_network[:], outscaler)

    for param in real_scale_network.parameters():
        param.requires_grad_(False)

    # evaluate_dataset_errors(train_dloader,real_scale_network,scaler=None,show="train")
    # evaluate_dataset_errors(valid_dloader,real_scale_network,scaler=None,show="valid")
    # evaluate_dataset_errors(test_dloader,real_scale_network,scaler=None,show="test")

    return real_scale_network


def train_epoch(train_data,network,cost_fn,opt,scaler):
    for batch_in,batch_out in train_data:
        opt.zero_grad()
        batch_pred = network(batch_in)
        cost = cost_fn(batch_pred,scaler(batch_out))
        cost.backward()
        opt.step()

def evaluate_dataset_errors(dloader,network,scaler,show=False):
    predicted = []
    true = []
    with torch.autograd.no_grad():
        for bin,bout in dloader:

            bpred = network(bin)
            if scaler is not None:
                bout = scaler(bout)

            true.append(bout)
            predicted.append(bpred)

    true = torch.cat(true,dim=0)
    predicted = torch.cat(predicted,dim=0)
    err = predicted-true

    return err



def build_network(net_config):
    pass
    #do we need this? maybe for serializing more efficiently?

def l1_score(true,predicted):
    sum_abs_resid = np.abs(true-predicted).sum()
    med = np.median(true)
    sum_abs_dev = np.abs(true-med).sum()
    return 1 - sum_abs_resid/sum_abs_dev


def get_error_info(network,test_dset):
    test_dloader = torch.utils.data.DataLoader(test_dset,batch_size=100,shuffle=False)

    error = evaluate_dataset_errors(test_dloader,network,scaler=None).numpy()
    true = test_dset[:][-1].numpy()
    predicted = true + error
    return get_score(predicted,true)

def get_score(predicted,true):
    score = []
    rmse_list = []
    for i,(p,t) in enumerate(zip(predicted.T,true.T)):
        rmse = np.sqrt(sklearn.metrics.mean_squared_error(t,p))
        rsq = sklearn.metrics.r2_score(t,p)
        l1resid = l1_score(t,p)

        #HARDCODED: SCORE FOR EACH THING TO PREDICT IS RSQ
        score.append(rsq)
        rmse_list.append(rmse)
        #print(i,rsq,l1resid)

    #HARDCODED: TOTAL SCORE IS PRODUCT OF SCORES FOR EACH TARGET
    score = np.asarray(score)
    #score = np.prod(score*(score>0))
    rmse_list = np.asarray(rmse_list)
    return score,rmse_list

class Scaler(torch.nn.Module):
    def __init__(self,means,stds,eps=1e-100):
        super().__init__()
        self.means = torch.nn.Parameter(means,requires_grad=False)
        self.stds = torch.nn.Parameter(stds,requires_grad=False)
        self.eps  = eps

    @classmethod
    def from_tensor(cls,tensor):
        means = tensor.mean(dim=0)
        stds = tensor.std(dim=0)
        return cls(means,stds)

    @classmethod
    def from_inversion(cls,other):
        new_means = -other.means/other.stds
        new_stds = 1/other.stds
        return cls(new_means,new_stds)

    def forward(self,tensor):
        return (tensor-self.means)/(self.stds + self.eps)
