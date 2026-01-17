## Prometheus for Observability

#### Prometheus Stack 설치 (Prometheus, Grafana, Alertmanager)
```sh
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm install obs prometheus-community/kube-prometheus-stack \
--namespace observability --create-namespace
```

#### Triton Inference Server Dashboard 설정
추가적으로 Triton inference server dashboard 설정을 위해 하위 디렉토리 [triton](./triton/README.md) 참조

#### FastAPI-based Inference Endpoint Dashboard 설정
추가적으로 FastAPI-based inference endpoint dashboard 설정을 위해 하위 디렉토리 [inference](./inference/README.md) 참조