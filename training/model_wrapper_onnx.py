import torch.nn as nn
import torch

class CreditModelWrapperOnnx(nn.Module):
    def __init__(self, model, scaler):
        super().__init__()
        
        self.model = model
        self.register_buffer("mean", torch.tensor(scaler.mean_, dtype=torch.float32))
        self.register_buffer("scale", torch.tensor(scaler.scale_, dtype=torch.float32))

    def forward(self, X):
        X = (X - self.mean) / self.scale
        return self.model(X)