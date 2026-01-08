import mlflow.pyfunc
import numpy as np
import torch

class CreditModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model, scaler, device):
        self.model = model
        self.device = device
        self.mean = torch.tensor(scaler.mean_, dtype=torch.float32).to(device)
        self.scale = torch.tensor(scaler.scale_, dtype=torch.float32).to(device)

    def predict(self, model_input):
        if hasattr(model_input, "values"):
            X_np = model_input.values.astype(np.float32)
        else:
            X_np = np.asarray(model_input, dtype=np.float32)

        X = torch.from_numpy(X_np).to(self.device)

        X = (X - self.mean) / self.scale

        self.model.eval()
        with torch.no_grad():
            logits = self.model(X)

        return logits.cpu().numpy()