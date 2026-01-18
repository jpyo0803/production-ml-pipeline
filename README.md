## 프로젝트 개요
본 프로젝트는 데이터 수집부터 모델 학습, 성능 최적화, 그리고 안정적인 서빙 및 운영(GitOps)까지의 **End-to-End MLOps 파이프라인**을 구축하는 것을 목표로 합니다. 단순한 모델 배포를 넘어, **수직적 최적화(Triton Model Analyzer)**와 **수평적 확장(K8s HPA)**을 결합하여 자원 효율성과 시스템 가용성을 동시에 극대화한 실무 지향적 아키텍처를 지향합니다.

## 핵심 설계 목표
1. **데이터 일관성 확보**: Feature Store(Feast)를 도입하여 학습(Training)과 추론(Serving) 시점의 데이터 불일치(Training-Serving Skew) 방지
2. **비용 효율적 성능 최적화**: Triton Model Analyzer를 통해 하드웨어 제한 내 최적의 처리량(Throughput)을 내는 'Golden Config' 도출
3. **선형적 확장성 구현**: 최적화된 단일 Pod를 기반으로 클러스터 부하에 따라 유연하게 대응하는 선형적 확장 체계 구축
4. **인프라의 코드화(IaC) 및 자동화**: Helm과 ArgoCD를 활용하여 배포 과정을 표준화하고 Git 기반의 지속적 배포(CD) 실현

## 시스템 아키텍처
1. **Data Layer**: Feast (Feature Store) + MinIO (S3 compatible)
2. **ML Engine Layer**: MLflow (Tracking/Registry) + Postgres (Metadata)
3. **Serving Layer**: Triton Inference Server (Core Engine) + FastAPI (BFF/Endpoint)
4. **Infra & Ops Layer**: Kubernetes (EKS/Local), Helm, ArgoCD (GitOps)
5. **Observability Layer**: Prometheus + Grafana (ServiceMonitor)

## 핵심 기술 스택
- **Infrastructure**: Kubernetes, Docker, Helm, ArgoCD
- **Data/Feature**: Feast, MinIO (S3), PostgreSQL
- **Model Serving**: NVIDIA Triton Inference Server, FastAPI, Model Analyzer
- **ML Lifecycle**: MLflow (Tracking & Registry)
- **Observability**: Prometheus, Grafana