## FastAPI-based Inference Endpoint Observability
1. helm 명령어를 통해 성공적으로 **production-ml-pipeline** 어플리케이션을 배포한다.
2. 터미널을 새로 켜서 다음 명령어를 통해 포트포워딩을 한다.
   ```sh
   $ kubectl port-forward -n observability svc/obs-grafana 3000:80
   ```
3. 웹브라우저에서 **http://localhost:3000/** 에 접속한다.
4. 왼쪽 패널에서 **Dashboard** 선택
5. 오른쪽 상단에서 **New** 드롭다운 메뉴에서 **New dashboard** 클릭
6. **Add visualizaiton**
7. 데이터 소스는 **Prometheus** 선택
8. **Add query**에서 목적에 맞게 Metric 지표를 추가한다.


그럼 아래와 같이 대시보드를 확인할 수 있다.

![Inference dashboard image](images/inference_dashboard.png)
