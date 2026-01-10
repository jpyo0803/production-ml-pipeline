from copy import deepcopy
from datasets import load_dataset
from config import Config
import torch

from model import TabularModel
from model_wrapper import CreditModelWrapper
from model_wrapper_onnx import CreditModelWrapperOnnx

from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import mlflow
from mlflow.tracking import MlflowClient

import os
import boto3

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

def export_onnx(model, scaler, input_dim, onnx_path):
    model.eval()

    # canonical dummy input (raw space)
    dummy_input = torch.zeros(
        1, input_dim, dtype=torch.float32
    )

    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
        opset_version=17,
    )

def upload_to_minio(local_path, bucket, s3_key):
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    s3.upload_file(local_path, bucket, s3_key)

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

        model.eval()
        model_cpu = deepcopy(model).to("cpu").eval()

        mlflow.log_metric("val_auc", auc)

        wrapped_model = CreditModelWrapper(
            model=model_cpu,
            scaler=scaler,
            device="cpu",
        )

        # 모델 저장 및 등록
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=wrapped_model,
            registered_model_name="HomeCreditDefaultModel",
            code_paths=["model.py", "model_wrapper.py"],
        )

        client = MlflowClient()

        model_versions = client.search_model_versions(
            filter_string="name='HomeCreditDefaultModel'",
            order_by=["creation_timestamp DESC"],
            max_results=1
        )

        client.set_registered_model_alias(
            name="HomeCreditDefaultModel",
            alias="prod",
            version=model_versions[0].version
        )

        print("Exporting model to ONNX format and uploading to MinIO...")
        model_for_onnx = CreditModelWrapperOnnx(
            model=model_cpu,
            scaler=scaler,
        ).eval()

        onnx_path = "/tmp/model.onnx"

        export_onnx(
            model=model_for_onnx,
            scaler=scaler,
            input_dim=X_train.shape[1],
            onnx_path=onnx_path,
        )

        upload_to_minio(
            local_path=onnx_path,
            bucket="models",
            s3_key="home_credit_default/1/model.onnx",
        )

        # MLflow와 ONNX 출력 차이 확인
        x_raw = torch.randn(5, X_train.shape[1])

        with torch.no_grad():
            torch_out = model_for_onnx(x_raw)

        import onnxruntime as ort
        import numpy as np
        sess = ort.InferenceSession("/tmp/model.onnx")
        onnx_out = sess.run(None, {"input": x_raw.numpy()})[0]

        print("max diff:", np.max(np.abs(torch_out.numpy() - onnx_out)))

if __name__ == "__main__":
    train()