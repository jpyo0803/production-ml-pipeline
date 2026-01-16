import os
import shutil
import mlflow
from mlflow.tracking import MlflowClient

# 컨테이너 환경변수에서 MLflow 추적 URI 및 모델/별칭 정보 로드
TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = "HomeCreditDefaultModel"
ALIAS = "prod"
BASE_REPO_PATH = "./models"  # Triton이 바라보는 공유 볼륨 경로

os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ.get("MLFLOW_S3_ENDPOINT_URL", "http://localhost:9000")

def download_from_mlflow():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    # 'prod' 별칭이 붙은 모델의 버전 및 아티팩트 위치 조회
    print(f"Fetching model '{MODEL_NAME}' with alias '{ALIAS}' from MLflow...")
    model_version_details = client.get_model_version_by_alias(MODEL_NAME, ALIAS)
    version = model_version_details.version
    
    # 학습 시 artifact_path="triton_model"로 저장했으므로 해당 경로를 지정
    artifact_uri = f"models:/{MODEL_NAME}@{ALIAS}"

    tmp_download_dir = "/tmp/mlflow_model"
    if os.path.exists(tmp_download_dir):
        shutil.rmtree(tmp_download_dir)

    local_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri, dst_path=tmp_download_dir)

    print(f"DEBUG: Files in local_path ({local_path}): {os.listdir(local_path)}")

    # 아티팩트 다운로드 (임시 로컬 경로로 내려받음)
    print(f"Downloading artifacts from: {artifact_uri}")
    local_path = mlflow.artifacts.download_artifacts(artifact_uri=artifact_uri)

    # Triton 규격에 맞는 최종 목적지 경로 설정
    # 구조: /models/HomeCreditDefaultModel/<version>/model.onnx
    model_dir = os.path.join(BASE_REPO_PATH, MODEL_NAME)
    version_dir = os.path.join(model_dir, str(version))
    os.makedirs(version_dir, exist_ok=True)

    # 파일 배일
    artifacts = os.listdir(local_path)
    print(f"Deploying artifacts: {artifacts}")

    for item in artifacts:
        src_path = os.path.join(local_path, item)
        
        # (1) config.pbtxt는 모델 루트 폴더로
        if item == "config.pbtxt":
            dest_path = os.path.join(model_dir, "config.pbtxt")
            shutil.copy(src_path, dest_path)
            print(f"    - Copied config: {item}")
            
        # (2) 나머지 파일들(model.onnx, *.data 등)은 버전 폴더로 통째로 이동
        elif os.path.isfile(src_path):
            if not item.startswith("MLmodel") and not item.endswith(".yaml"):
                dest_path = os.path.join(version_dir, item)
                shutil.copy(src_path, dest_path)
                print(f"    - Copied model data: {item}")

    print(f"Deployment Complete!")
    print(f" - Config: {model_dir}/config.pbtxt")
    print(f" - Model:  {version_dir}/model.onnx")

if __name__ == "__main__":
    download_from_mlflow()