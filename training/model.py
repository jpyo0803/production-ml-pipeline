import torch.nn as nn

'''
    간단한 피드포워드 신경망 모델 정의

    현재는 동작 확인용으로만 사용
'''
class TabularModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x) # [Batch, 1]