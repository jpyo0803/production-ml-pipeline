from datasets import load_dataset
from config import Config
import torch

from model import TabularModel
from model_wrapper import CreditModelWrapper

from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import mlflow
import mlflow.pytorch
import os

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("home-credit-default")

config = Config()
device = config.device

def train():
    X_train, y_train, X_val, y_val = load_dataset()

    scaler = StandardScaler()
    scaler.fit(X_train)

    X_train = torch.tensor(scaler.transform(X_train), dtype=torch.float32).to(device)
    y_train = torch.tensor(y_train, dtype=torch.float32).to(device)

    X_val = torch.tensor(scaler.transform(X_val), dtype=torch.float32).to(device)
    y_val = torch.tensor(y_val, dtype=torch.float32).to(device)

    with mlflow.start_run():
        model = TabularModel(input_dim=X_train.shape[1]).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
        loss_fn = torch.nn.BCEWithLogitsLoss()

        for epoch in range(config.num_epochs):
            model.train()
            optimizer.zero_grad()
            logits = model(X_train)
            loss = loss_fn(logits, y_train)
            loss.backward()
            optimizer.step()

            model.eval()
            with torch.no_grad():
                val_logits = model(X_val)
                preds = torch.sigmoid(val_logits).cpu().numpy()
                auc = roc_auc_score(y_val.cpu().numpy(), preds)

            print(f"Epoch {epoch+1}/{config.num_epochs}, Loss: {loss.item():.4f}, Val AUC: {auc:.4f}")

        mlflow.log_metric("val_auc", auc)

        wrapped_model = CreditModelWrapper(
            model=model,
            scaler=scaler,
            device=device
        )

        # 모델 저장 및 등록
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=wrapped_model,
            registered_model_name="HomeCreditDefaultModel",
            code_paths=["model.py", "model_wrapper.py"],
        )

if __name__ == "__main__":
    train()