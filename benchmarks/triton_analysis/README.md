## 모델 분석 및 성능 최적화

본 프로젝트는 **Triton Inference Server**와 **Model Analyzer**를 활용하여, 하드웨어 자원을 최대한 효율적으로 사용하는 최적의 추론 환경설정을 자동으로 탐색합니다.

### 성능 최적화의 필요성
모델 추론 서비스의 처리량(Throughput)과 지연 시간(Latency)은 다음 요소들에 의해 결정됩니다.
- **Model Architecture**: 타겟 모델의 구조는 연산적, 메모리 특성을 좌우합니다.
- **Target Hardware**: 현재 사용하는 하드웨어
- **Workload**: 동시 요청 수(Concurrency)에 따른 부하 특성
- **Inference Configuration**: Max batch size, Dynamic batching delay, Instance group count 등

### 분석 방법론
Model Analyzer를 통해 다양한 환경설정 조합을 시뮬레이션하고, **지연 시간(Latency) 제약 조건 내에서 처리량(Throughput)을 극대화**하는 최적의 지점을 찾습니다.

#### 실행 방법
1. **사전 준비**: Docker Compose를 통해 MLOps 환경(MinIO, MLflow 등)이 실행 중이어야 합니다.
2. **의존성 설치**
   ```sh
   $ pip install -r requirements.txt
   ```
3. **분석기 실행**:
   ```sh
   $ ./run_analyzer.sh
   ```

필요 시 config.yaml 수정을 통해 실험 스윕(Sweep) 범위를 조절할 수 있습니다.

#### 결과 확인
분석기 실행이 완료되면 **results/reports/summaries/HomeCreditDefaultModel/result_summary.pdf** 에 분석 결과 파일이 생성됩니다.

현재 디렉토리에 샘플 분석 결과(example_result_summary.pdf)를 포함

해당 샘플 분석 결과에서 사용한 Default 환경설정은 **results/output_models/HomeCreditDefaultModel_config_default/config.pbtxt** 에서 확인할 수 있습니다.

```
# Default 환경설정 
name: "HomeCreditDefaultModel"
platform: "onnxruntime_onnx"
max_batch_size: 16
input {
  name: "input"
  data_type: TYPE_FP32
  dims: 10
}
output {
  name: "output"
  data_type: TYPE_FP32
  dims: 1
}
instance_group {
  count: 1
  kind: KIND_CPU
}
dynamic_batching {
}
```

샘플 분석 결과에 따르면 **HomeCreditDefaultModel_config_12** 설정이 가장 최적의 성능을 보였다고 합니다. 다음은 config_12의 환경설정입니다. 
```
# config_12 환경설정
name: "HomeCreditDefaultModel"
platform: "onnxruntime_onnx"
max_batch_size: 8
input {
  name: "input"
  data_type: TYPE_FP32
  dims: 10
}
output {
  name: "output"
  data_type: TYPE_FP32
  dims: 1
}
instance_group {
  count: 2
  kind: KIND_CPU
}
dynamic_batching {
  max_queue_delay_microseconds: 500
}
```

위 둘의 차이점을 비교 분석해보면 아래와 같습니다. 
#### Triton Inference Server 성능 분석 결과: Default vs. Config 12

![example result summary chart](images/example_result_summary_chart.png)

| 항목 (Metric) | 기본 설정 (Default) | 최적 설정 (Config 12) | 비고 (Technical Insight) |
| :--- | :---: | :---: | :--- |
| **Max Batch Size** | 16 | **8** | 배치 크기를 줄여 개별 추론 속도 최적화 |
| **Instance Count** | 1 (CPU) | **2 (CPU)** | 추론 엔진 복제로 병렬 처리 성능 2배 강화 |
| **Max Queue Delay** | 0 $\mu s$ | **500 $\mu s$** | 대기 시간을 활용해 다이내믹 배칭 효율 극대화 |
| **Throughput** | 61,471.6 infer/sec | **88,022.5 infer/sec** | 기본 설정 대비 **약 43% 처리량 향상**  |
| **p99 Latency** | 1.513 ms | **1.316 ms** | 처리량 증가에도 지연 시간을 약 13% 단축 |

#### 샘플 결과에 대한 분석
본 분석을 통해 현재 사용한 HomeCreditDefaultModel의 경우 무작정 배치를 키우기보다 적절한 대기 시간(Dynamic Batching Delay)과 인스턴스 병렬 처리를 조합하는 것이 지연 시간과 처리량 모두를 잡는 최적의 전략임을 확인할 수 있었습니다.

## Kubernetes HPA(수평 확장)와의 관계

본 프로젝트에서 수행한 Triton Model Analyzer 분석은 단일 Pod(또는 단일 컨테이너) 환경에서 자원 효율을 극대화하는 **수직적 최적화(Vertical Optimization)** 과정입니다.

#### 1. 단위 성능과 시스템 확장의 연결
* **수직적 최적화**: 단일 유닛이 가질 수 있는 최적의 Throughput과 Latency 조합을 결정합니다. 분석 결과에 따라 `config_12`는 2 CPU 환경에서 약 8.8만 infer/sec를 처리하는 'Golden Config'로 확정되었습니다. 
* **수평적 확장 (HPA)**: 쿠버네티스 HPA는 단일 Pod의 처리 한계치에 도달했을 때, 동일하게 최적화된 Pod를 복제하여 시스템 전체의 가용성을 높이는 **수평적 확장(Horizontal Scaling)**을 담당합니다.

#### 2. 선형적 성능 향상의 전제 조건
단일 Pod의 성능이 이미 최적화되어 있으므로, 다음 조건이 충족될 경우 전체 시스템 성능은 Pod 수에 비례하여 선형적으로 향상(Linear Scalability)될 것이라고 신뢰할 수 있습니다.
- **자원 격리**: 각 Pod가 `K8s Resource Requests/Limits`를 통해 독립된 CPU 자원을 보장받음.
- **독립성 보장**: Pod 간 자원 경합이 발생하지 않는 노드 배치(Anti-affinity 등).