{{/*
MinIO(S3) 접속을 위한 공통 환경 변수
*/}}
{{- define "common.env.minio" -}}
- name: AWS_ACCESS_KEY_ID
  value: {{ .Values.infrastructure.minio.rootUser | quote }}
- name: AWS_SECRET_ACCESS_KEY
  value: {{ .Values.infrastructure.minio.rootPassword | quote }}
- name: AWS_DEFAULT_REGION
  value: {{ .Values.featureStore.s3Region | quote }}
- name: AWS_ENDPOINT_URL
  value: "http://minio:{{ .Values.infrastructure.minio.apiPort }}"
- name: FEAST_S3_ENDPOINT_URL
  value: "http://minio:{{ .Values.infrastructure.minio.apiPort }}"
- name: MLFLOW_S3_ENDPOINT_URL
  value: "http://minio:{{ .Values.infrastructure.minio.apiPort }}"
{{- end -}}

{{/*
RabbitMQ 접속을 위한 공통 환경 변수
*/}}
{{- define "common.env.rabbitmq" -}}
- name: RABBITMQ_URL
  value: "amqp://{{ .Values.infrastructure.rabbitmq.user }}:{{ .Values.infrastructure.rabbitmq.password }}@rabbitmq:{{ .Values.infrastructure.rabbitmq.port }}/"
- name: QUEUE_NAME
  value: {{ .Values.inference.queueName | quote }}
{{- end -}}

{{/*
공통 라벨
*/}}
{{- define "common.labels" -}}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}