from datasets import load_dataset
from config import Config
import torch

from model import TabularModel
from sklearn.metrics import roc_auc_score

import mlflow
import mlflow.pytorch
import os

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("home-credit-default")

config = Config()
device = config.device

def train():
    X_train, X_val, y_train, y_val = load_dataset()

    X_train = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train = torch.tensor(y_train, dtype=torch.float32).to(device)
    X_val = torch.tensor(X_val, dtype=torch.float32).to(device)
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
        mlflow.pytorch.log_model(
            model,
            artifact_path="tabular_model",
            registered_model_name="HomeCreditDefaultModel"
        )

if __name__ == "__main__":
    train()