from datasets import load_dataset
from config import Config
import torch

from model import TabularModel
from sklearn.metrics import roc_auc_score

import mlflow
import mlflow.pytorch
import os

import joblib

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("home-credit-default")

config = Config()
device = config.device

def train():
    X_train, y_train, X_val, y_val, scaler = load_dataset()

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

        # scaler artifact 저장
        os.makedirs("artifacts", exist_ok=True)
        scaler_path = "artifacts/scaler.joblib"
        joblib.dump(scaler, scaler_path)
        mlflow.log_artifact(scaler_path, artifact_path="preprocessing")

        # 모델 저장 및 등록
        mlflow.pytorch.log_model(
            model,
            artifact_path="tabular_model",
            registered_model_name="HomeCreditDefaultModel",
            code_paths=["model.py"], # model.py 파일도 함께 저장
        )

if __name__ == "__main__":
    train()