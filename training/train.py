from datasets import load_dataset
from config import Config
import torch

from model import TabularModel
from model_wrapper import CreditModelWrapper

from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import mlflow
from mlflow.tracking import MlflowClient

import os

import onnx
import onnxruntime as ort

mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("home-credit-default")

config = Config()
device = config.device

# 시드 고정
import random
import numpy as np

seed = 42
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def log_triton_config(model_name, input_dim, artifact_path):    
    config_content = f"""name: "{model_name}"
platform: "onnxruntime_onnx"
max_batch_size: 0

input [
  {{
    name: "input"
    data_type: TYPE_FP32
    dims: [ -1, {input_dim} ]
  }}
]

output [
  {{
    name: "output"
    data_type: TYPE_FP32
    dims: [ -1 ]
  }}
]

instance_group [
  {{
    kind: KIND_CPU
    count: 1
  }}
]

dynamic_batching {{ }}
"""
    config_file_path = "config.pbtxt"
    with open(config_file_path, "w") as f:
        f.write(config_content)

    mlflow.log_artifact(config_file_path, artifact_path=artifact_path)

def convert_to_onnx_model(model, scaler, input_dim):
    import io
    buffer = io.BytesIO()

    model.eval()

    # canonical dummy input (raw space)
    dummy_input = torch.zeros(
        1, input_dim, dtype=torch.float32
    )

    torch.onnx.export(
        model,
        dummy_input,
        buffer,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
        opset_version=17,
    )

    onnx_model = onnx.load_from_string(buffer.getvalue())
    return onnx_model

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

        # Metric 로그
        mlflow.log_metric("val_auc", auc)

        model = model.to("cpu")

        # ONNX로 변환 
        onnx_model = convert_to_onnx_model(
            model=CreditModelWrapper(model, scaler).eval(),
            scaler=scaler,
            input_dim=X_train.shape[1],
        )

        artifact_path = "triton_model"

        # MLflow에 ONNX 모델로 저장
        mlflow.onnx.log_model(
            onnx_model=onnx_model,
            artifact_path=artifact_path,
            registered_model_name="HomeCreditDefaultModel",
        )

        # Triton용 설정 파일 생성 및 저장
        log_triton_config(
            model_name="HomeCreditDefaultModel",
            input_dim=X_train.shape[1],
            artifact_path=artifact_path,
        )

        client = MlflowClient()
        model_version = client.get_latest_versions(
            name="HomeCreditDefaultModel",
            stages=["None"],
        )[0].version

        client.set_registered_model_alias(
            name="HomeCreditDefaultModel",
            alias="prod",
            version=model_version,
        )

        print(f"[MLflow] logged model version: {model_version}")

if __name__ == "__main__":
    train()