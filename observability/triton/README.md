## Triton Inference Server Observability
1. helm 명령어를 통해 성공적으로 **production-ml-pipeline** 어플리케이션을 배포한다.
2. 터미널을 새로 켜서 다음 명령어를 통해 포트포워딩을 한다.
   ```sh
   $ kubectl port-forward -n observability svc/obs-grafana 3000:80
   ```
3. 웹브라우저에서 **http://localhost:3000/dashboard/import** 에 접속한다.
4. 현재 디렉토리에 포함된 **dashboard.json** 파일 내용물을 Import 한다.
5. 데이터 소스를 Prometheus로 설정하고 Import를 완료한다.

그럼 아래와 같이 대시보드를 확인할 수 있다.

![Triton dashboard image](images/triton_dashboard.png)
