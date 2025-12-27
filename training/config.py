import torch

class Config:
    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() 
            else 'mps' if torch.backends.mps.is_available() 
            else "cpu"
        )
        self.label_path = "/app/data/raw/application_train.csv"
        self.num_epochs = 10
        self.lr = 1e-3
