import copy

import torch
import torch.utils.data
import numpy as np

torch.set_default_dtype(torch.float64)

import matplotlib
import matplotlib.pyplot as plt

from alInterface import getAllGNDData, SolverCode

import sklearn.metrics

CURRENT_DATABASE = None

class Model():
    """
    Basic ensemble model. Error bar is std. dev. of networks.
    """
    def __init__(self,networks,err_info=None):
        self.networks = networks
        self.err_info = err_info

    def __call__(self,request_params,batch=False):
        """
        :param request_params: features for BGK
        :param batch: whether request_params is a 2-d array of (example,inputs).
        :return: result[3], errbar[3]
        """

        request_params = torch.as_tensor(request_params)
        if not batch:
            request_params = request_params.unsqueeze(0)

        results = np.asarray([np.asarray(nn(request_params)) for nn in self.networks])

        mean = results.mean(axis=0)
        std = results.std(axis=1)

        return mean, std

    def iserrok(self,errbars):
        """
        :param errbars:
        :return: bool[3] -- use self.err_info to
        """
        return errbars < self.err_info



# Parameters governing input and outputs to problem
#WARNING HARDCODING
BGK_TRANSACTION_SIZES =dict(
    n_inputs=9,   # 9 inputs temp density[4], charge[4]
    #skip column of metadta
    n_outputs=3,  # outputs hydro[2], diffusion[10] # only care about first 3 diffusions
)


#Parameters governing network structure
DEFAULT_NET_CONFIG = dict(
    n_layers=3,
    n_hidden=10,
    activation_type=torch.nn.ReLU,
    layer_type = torch.nn.Linear
    )

#Parameters for ensemble uncertainty
DEFAULT_ENSEMBLE_CONFIG = dict(
    n_members = 10,
    test_fraction = 0.2,
)

#Parameters for the optimization process
DEFAULT_TRAINING_CONFIG = dict(
    n_epochs=1000,
    optimizer_type=torch.optim.Adam,
    validation_fraction=0.1,
    lr=1e-3,
    patience=10,
    batch_size=5,
    scheduler_type = torch.optim.lr_scheduler.ReduceLROnPlateau,
    cost_type = torch.nn.MSELoss
)

#Bundle of all learning-related parameters
DEFAULT_LEARNING_CONFIG = dict(
    net_config = DEFAULT_NET_CONFIG,
    ensemble_config = DEFAULT_ENSEMBLE_CONFIG,
    transaction_config = BGK_TRANSACTION_SIZES,
    training_config = DEFAULT_TRAINING_CONFIG,
)

def assemble_dataset(raw_dataset,transaction_config):
    n_in = transaction_config["n_inputs"]
    n_out = transaction_config["n_outputs"]
    # WARNING HARDCODING FOR BGK TEST
    features = torch.as_tensor(raw_dataset[:, :9])
    targets = torch.as_tensor(raw_dataset[:, 12:15])
    return torch.utils.data.TensorDataset(features,targets)

#prototype, only covers ensemble uncertainties
def retrain(learning_config=DEFAULT_LEARNING_CONFIG):

    raw_dataset = getAllGNDData(CURRENT_DATABASE,SolverCode.BGK)

    transaction_config = learning_config["transaction_config"]
    ensemble_config = learning_config["ensemble_config"]

    full_dataset = assemble_dataset(raw_dataset,transaction_config)

    n_total = len(full_dataset)
    n_test = int(ensemble_config["test_fraction"]*n_total)
    n_train = n_total-n_test

    networks = []
    model_errors = []

    for i in range(ensemble_config["n_members"]):
        print("Training ensemble member",i)
        train_data,test_data = torch.utils.data.random_split(full_dataset, (n_train,n_test))

        #This is a place where we could trivially parallelize training.

        this_model = train_single_model(train_data, test_data, learning_config=learning_config)

        networks.append(this_model)



        this_error_info = get_error_info(this_model,test_data)

        model_errors.append(this_error_info)

    error_info = compute_err_info(this_error_info)

    return Model(networks,error_info)


def train_single_model(train_data, test_data, learning_config):

    net_config = learning_config["net_config"]
    training_config = learning_config["training_config"]
    transaction_config = learning_config["transaction_config"]

    #Type parameters
    activation_type = net_config["activation_type"]
    layer_type = net_config["layer_type"]

    #Splitting
    n_total = len(train_data)
    n_valid = int(training_config["validation_fraction"]*n_total)
    n_train = n_total-n_valid
    train_data, valid_data = torch.utils.data.random_split(train_data, (n_train, n_valid))

    #Normalizing
    train_features, train_labels = (train_data[:])
    print(train_labels.shape)
    inscaler = Scaler.from_tensor(train_features)

    cost_scaler = Scaler.from_tensor(train_labels)
    outscaler = Scaler.from_inversion((cost_scaler))

    #Size parameters
    n_inputs = transaction_config["n_inputs"]
    n_outputs = transaction_config["n_outputs"]
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
    scheduler = training_config["scheduler_type"](opt,patience=patience,verbose=True,factor=0.5)


    best_cost = np.inf
    best_params = train_network.state_dict()

    train_dloader = torch.utils.data.DataLoader(train_data,batch_size=training_config["batch_size"],shuffle=True)
    valid_dloader = torch.utils.data.DataLoader(valid_data,batch_size=10*training_config["batch_size"],shuffle=False)
    test_dloader = torch.utils.data.DataLoader(test_data,batch_size=10*training_config["batch_size"],shuffle=False)

    # Need to add scales for costs
    for i in range(training_config["n_epochs"]):
        train_epoch(train_dloader,train_network,cost_fn,opt,scaler=cost_scaler)
        eval_cost = evaluate_dataset_errors(valid_dloader,train_network,scaler=cost_scaler).abs().mean().item()
        #if i%100==0: print(eval_cost)
        scheduler.step(eval_cost)
        if eval_cost < best_cost:
            print("best epoch:",i)
            best_cost = eval_cost
            best_params = copy.deepcopy(train_network.state_dict())
            boredom = 0
        else:
            boredom +=1

        if boredom > 2*patience+1:
            print("Training finalized at epoch",i)
            break


    real_scale_network = torch.nn.Sequential(*train_network[:], outscaler)

    train_network.load_state_dict(best_params)

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

    if not show:
        return err

    predicted = predicted.numpy()
    true = true.numpy()

    fig,axarr = plt.subplots(1,3,figsize=(12,4))
    for p,t,ax in zip(predicted.T,true.T,axarr):
        plt.sca(ax)
        plt.scatter(p,t,label=show)
        mm = min(min(p),min(t))
        xx = max(max(p),max(t))
        plt.plot((mm,xx),(mm,xx),lw=1,c='r')
        plt.title(show)
        plt.xlabel("predicted")
        plt.ylabel("true")
    plt.show()

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

    score = []
    rmse_list = []
    for i,(p,t) in enumerate(zip(predicted.T,true.T)):
        rmse = np.sqrt(sklearn.metrics.mean_squared_error(t,p))
        rsq = sklearn.metrics.r2_score(t,p)
        l1resid = l1_score(t,p)

        #HARDCODED: SCORE FOR EACH THING TO PREDICT IS RSQ
        score.append(rsq)
        rmse_list.append(rmse)
        print(i,rsq,l1resid)

    #HARDCODED: TOTAL SCORE IS PRODUCT OF SCORES FOR EACH TARGET
    score = np.prod(score)
    rmse_list = np.asarray(rmse_list)
    return score,rmse_list


def compute_err_info(errors):
    pass

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
