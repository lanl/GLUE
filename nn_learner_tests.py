import torch

import sklearn.metrics

import numpy as np

import matplotlib
import matplotlib.pyplot as plt

import nn_learner
import alInterface


def plot_errors(predicted,true,label):
    predicted = predicted.numpy()
    true = true.numpy()

    fig,axarr = plt.subplots(1,3,figsize=(12,4))
    for p,t,ax in zip(predicted.T,true.T,axarr):
        plt.sca(ax)
        plt.scatter(p,t,label=label)
        mm = min(min(p),min(t))
        xx = max(max(p),max(t))
        plt.plot((mm,xx),(mm,xx),lw=1,c='r')
        plt.title(label)
        plt.xlabel("predicted")
        plt.ylabel("true")
    plt.show()




if __name__=="__main__":
    print("PYTORCH VERSION",torch.__version__)

    DB_PATH = "../realTraining.db"
    model = nn_learner.retrain(db_path=DB_PATH)

    #Ensure model can be pickled and unpickled.
    torch.save(model,"__MODEL_TEST.pt")
    model = torch.load("__MODEL_TEST.pt")

    #Run model on the data
    raw_dataset = alInterface.getAllGNDData(DB_PATH, alInterface.SolverCode.BGK)
    output_location = nn_learner.SOLVER_INDEXES[alInterface.SolverCode.BGK]["output_slice"]

    #Prediction on individual rows. Test sending in arrays as well as BGKInputs/BGKOutputs
    for i,row in enumerate(raw_dataset):

        prediction,errbar = model.process(row)
        input_bgk = alInterface.BGKInputs(row[0],row[1:5],row[5:9])
        # MODEL Accepts inputs of input_bgk type as well
        predict_throughtypes,err_throughtypes = model(input_bgk)

        #HARDCODE checking last 3 diffusion coefficients
        out_throughtypes = predict_throughtypes.DiffCoeff[-3:]
        #print(err_throughtypes)

        assert (out_throughtypes == prediction).all()

        outerr_throughtypes = err_throughtypes.DiffCoeff[-3:]
        assert (errbar==outerr_throughtypes).all()

        real_answer = row[output_location]

        isok_array = model.process_iserrok(errbar)
        isok_result = model.iserrok(err_throughtypes)

        isok_throughtypes = isok_result.DiffCoeff[-3:]

        assert (isok_throughtypes==isok_array).all()

        #print("example ")
        #print(prediction,errbar,prediction-real_answer,isok)

    print("Model passed type wrapping checks")

    # Batched Prediction on multiple rows
    prediction,errbar = model.process(raw_dataset)
    true = raw_dataset[...,output_location]
    error = prediction-true
    okay_prediction = model.process_iserrok(errbar)
    point_badness = model.process_iserrok_fuzzy(errbar)


    # Plot thing to see how it is doing.

    #print(prediction,errbar,okay_prediction)
    n_targets = prediction.shape[1]

    fig,axarr=plt.subplots(1,n_targets,figsize=(4*n_targets,4))
    for relerr,ax in zip(point_badness.T,axarr):
        plt.sca(ax)
        plt.hist(relerr,bins=30)
    plt.show()

    fig,axarr=plt.subplots(1,n_targets,figsize=(4*n_targets,4))

    print("Bad points:",(point_badness>=1).any(axis=1).sum(axis=0))

    for i,(p,t,bad,ax,eb) in enumerate(zip(prediction.T,true.T,point_badness.T,axarr,model.err_info)):

        plt.sca(ax)
        plt.title("Target {}".format(i))
        plt.xlabel("True")
        plt.ylabel("Predicted")

        # Lines
        mm = min(min(p), min(t)) # minimum
        xx = max(max(p), max(t)) # maximum

        plt.plot((mm, xx), (mm, xx), lw=1, c='grey')
        plt.plot((mm, xx), (mm + eb, xx + eb)  , lw=1, c='grey',ls='--')
        plt.plot((mm, xx), (mm + 2*eb, xx + 2*eb), lw=1, c='grey', ls=':')
        plt.plot((mm, xx), (mm - eb, xx - eb)  , lw=1, c='grey', ls='--')
        plt.plot((mm, xx), (mm - 2*eb, xx - 2*eb), lw=1, c='grey', ls=':')

        # Points
        colors = np.minimum(bad,1)

        plt.scatter(t,p,c=colors,s=5,cmap=plt.get_cmap('plasma')) # <- this is my idea of a pun
        plt.colorbar()

        # Really bad points
        really_bad = (bad>=1.0)
        plt.scatter(t[really_bad],p[really_bad],edgecolors='r',s=20,marker='o',c=[[0,0,0,0]])

        rsq = sklearn.metrics.r2_score(t,p)

        plt.text(0.1,0.9,"R^2 = {}".format(round(rsq,3)),transform=ax.transAxes)

        margin = 0.1*(xx-mm)
        plt.xlim(mm-margin,xx+margin)
        plt.ylim(mm-margin,xx+margin)

    plt.suptitle("This is not test data!",color='r')
    plt.tight_layout()
    plt.show()
