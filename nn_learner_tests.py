import basic_nn_learner
import alInterface
import torch

if __name__=="__main__":
    basic_nn_learner.CURRENT_DATABASE = "../realTraining.db"
    model = basic_nn_learner.retrain()

    #Ensure model can be pickled
    torch.save(model,"__MODEL_TEST.pt")
    model = torch.load("__MODEL_TEST.pt")

    #Run model on the data
    raw_dataset = alInterface.getAllGNDData(basic_nn_learner.CURRENT_DATABASE,alInterface.SolverCode.BGK)

    #full_dataset = basic_nn_learner.assemble_data(raw_dataset,basic_nn_learner.BGK_TRANSACTION_SIZES)
    for row in raw_dataset:
        prediction,errbar = model(row)
        isok =  model.iserrok(errbar)