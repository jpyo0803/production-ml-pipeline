## ArgoCD 적용
1. ArgoCD 전용 네임스페이스 생성
    ```sh
    $ kubectl create namespace argocd
    ```
2. ArgoCD 헬름 레포 추가 및 설치
    ```sh
    $ helm repo add argo https://argoproj.github.io/argo-helm
    $ helm repo update
    $ helm install argocd argo/argo-cd -n argocd
    ```
3. ArgoCD 포트 포워딩
    ```sh
    $ kubectl port-forward svc/argocd-server -n argocd 8080:443
    ```
4. 비밀번호 확인 
    ```sh
    $ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
    ```
5. Observability를 위한 ServiceMonitor CRD 관련 설치
    ```sh
    $ kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
    $ kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
    $ kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
    ```

6. 로컬 스토리지 프로비저너 설치 (DB 및 스토리지용) 
    ```sh 
    $ kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml 
    $ kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
    ```
7. ArgoCD 실행
    ```sh
    $ kubectl apply -f argocd/argocd-app.yaml
    ```
8. ArgoCD 웹페이지(http://localhost:8080/)에서 Sync 확인
![ArgoCD dashboard](images/argocd_dashboard.png)
