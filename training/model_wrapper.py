import torch.nn as nn
import torch

'''
    학습 데이터에서 사용한 스케일러 통계를 사용하여

    입력 데이터를 스케일링한 후 모델에 전달하는 래퍼 클래스
'''
class CreditModelWrapper(nn.Module):
    def __init__(self, model, scaler):
        super().__init__()

        # 원본 모델 저장
        self.model = model
        # 스케일러의 평균과 표준편차를 버퍼로 등록
        self.register_buffer("mean", torch.tensor(scaler.mean_, dtype=torch.float32))
        self.register_buffer("scale", torch.tensor(scaler.scale_, dtype=torch.float32))

    def forward(self, X):
        # 입력 데이터를 스케일링
        X = (X - self.mean) / self.scale

        # 모델에 전달 후 출력 반환
        return self.model(X)