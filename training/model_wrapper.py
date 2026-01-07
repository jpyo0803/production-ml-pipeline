import mlflow.pyfunc
import numpy as np
import torch

class CreditModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model, scaler, device):
        self.model = model
        self.scaler = scaler
        self.device = device

    def predict(self, model_input):
        X = self.scaler.transform(model_input)
        X = torch.tensor(X, dtype=torch.float32).to(self.device)

        self.model.eval()
        with torch.no_grad():
            logits = self.model(X)

        return logits.cpu().numpy()