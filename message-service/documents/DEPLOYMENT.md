# Message Service - Deployment Guide

Guía completa para el deployment del Message Service en diferentes entornos, optimizado para alta disponibilidad y escalabilidad.

## 📋 Información General

El Message Service es el componente de mayor complejidad operacional del ecosistema, requiriendo configuración especializada para manejo de alto volumen, múltiples workers y integración con servicios LLM externos.

## 🏗️ Prerequisitos del Sistema

### Requisitos Mínimos

| Componente | Desarrollo | Staging | Producción |
|------------|------------|---------|-------------|
| CPU | 2 cores | 4 cores | 8+ cores |
| RAM | 4GB | 8GB | 16GB+ |
| Storage | 10GB | 50GB | 200GB+ |
| Network | 100 Mbps | 1 Gbps | 10 Gbps |

### Dependencias Externas

| Servicio | Puerto | Requerido | Descripción |
|----------|--------|-----------|-------------|
| MongoDB | 27017 | Sí | Base de datos principal |
| Redis | 6379 | Sí | Cache y colas |
| Auth Service | 8001 | Sí | Autenticación |
| Conversation Service | 8003 | Sí | Metadatos de conversación |
| Characters Service | 8002 | Sí | Datos de personajes |
| LLM Service | 8005 | Sí | Procesamiento IA |
| Elasticsearch | 9200 | No | Búsqueda avanzada |

## 🚀 Deployment Local

### 1. Setup Manual de Desarrollo

```bash
# 1. Navegar al directorio del servicio
cd microservices/message-service

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-workers.txt

# 4. Configurar variables de entorno
cp .env.example .env
```

#### Configuración .env para Desarrollo

```bash
# Service Configuration
SERVICE_NAME=message-service
PORT=8004
LOG_LEVEL=DEBUG
ENVIRONMENT=development
DEBUG=true

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=message_service_dev
MONGODB_CONNECTION_POOL_MIN=5
MONGODB_CONNECTION_POOL_MAX=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_CONNECTION_POOL_MAX=20
CACHE_TTL_SECONDS=300

# External Services
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8003
CHARACTERS_SERVICE_URL=http://localhost:8002
LLM_SERVICE_URL=http://localhost:8005

# LLM Configuration
DEFAULT_LLM_PROVIDER=lmstudio
DEFAULT_MODEL=google/gemma-3-12b
MAX_TOKENS_PER_REQUEST=2048
DEFAULT_TEMPERATURE=0.7
REQUEST_TIMEOUT_SECONDS=30

# Rate Limiting (desarrollo)
MAX_MESSAGES_PER_MINUTE=1000
MAX_MESSAGES_PER_HOUR=10000

# Content Safety
ENABLE_CONTENT_FILTERING=true
SAFETY_THRESHOLD=0.7

# Performance
MAX_CONCURRENT_LLM_REQUESTS=10
MESSAGE_PROCESSING_TIMEOUT=60
BATCH_SIZE_FOR_ANALYTICS=100

# Workers
WORKER_COUNT=2
WORKER_QUEUE_SIZE=100
```

```bash
# 5. Configurar base de datos
python scripts/setup_indexes.py

# 6. Iniciar servicios de dependencias
docker-compose up -d mongodb redis

# 7. Ejecutar migraciones si es necesario
python scripts/migrate_data.py

# 8. Iniciar el servicio principal
python -m app.main

# 9. En terminales separados, iniciar workers
python workers/message_processor.py
python workers/llm_worker.py
python workers/analytics_worker.py
```

### 2. Docker Development Setup

#### Dockerfile Principal

```dockerfile
# microservices/message-service/Dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r messageservice && useradd -r -g messageservice messageservice

# Copy Python dependencies
COPY --from=builder /root/.local /home/messageservice/.local

# Set PATH
ENV PATH="/home/messageservice/.local/bin:$PATH"

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R messageservice:messageservice /app

# Switch to non-root user
USER messageservice

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Default command
CMD ["python", "-m", "app.main"]
```

#### Dockerfile para Workers

```dockerfile
# microservices/message-service/Dockerfile.worker
FROM python:3.11-slim

RUN groupadd -r worker && useradd -r -g worker worker

WORKDIR /app

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-workers.txt

COPY . .

RUN chown -R worker:worker /app
USER worker

# Variable para especificar qué worker ejecutar
ENV WORKER_TYPE=message_processor

CMD python workers/${WORKER_TYPE}.py
```

#### Docker Compose para Desarrollo

```yaml
# microservices/message-service/docker-compose.yml
version: '3.8'

services:
  message-service:
    build: .
    ports:
      - "8004:8004"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - AUTH_SERVICE_URL=http://auth-service:8001
      - CONVERSATION_SERVICE_URL=http://conversation-service:8003
      - CHARACTERS_SERVICE_URL=http://characters-service:8002
      - LLM_SERVICE_URL=http://llm-service:8005
    depends_on:
      - mongodb
      - redis
    networks:
      - microservices-network
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Workers
  message-processor:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - WORKER_TYPE=message_processor
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongodb
      - redis
    deploy:
      replicas: 2
    networks:
      - microservices-network
    restart: unless-stopped

  llm-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - WORKER_TYPE=llm_worker
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - LLM_SERVICE_URL=http://llm-service:8005
    depends_on:
      - mongodb
      - redis
    deploy:
      replicas: 3
    networks:
      - microservices-network
    restart: unless-stopped

  analytics-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - WORKER_TYPE=analytics_worker
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongodb
      - redis
    deploy:
      replicas: 1
    networks:
      - microservices-network
    restart: unless-stopped

  # Dependencies
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_DATABASE=message_service
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - microservices-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - microservices-network
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

  # Optional: Elasticsearch for search
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - microservices-network
    restart: unless-stopped

volumes:
  mongodb_data:
  redis_data:
  elasticsearch_data:

networks:
  microservices-network:
    driver: bridge
```

```bash
# Ejecutar con Docker Compose
docker-compose up -d

# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f message-service
docker-compose logs -f message-processor

# Escalar workers
docker-compose up -d --scale llm-worker=5
```

## 🌐 Deployment en Staging

### 1. Configuración de Staging

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  message-service:
    image: registry.company.com/message-service:${VERSION}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      placement:
        constraints:
          - node.labels.tier == api
    environment:
      - ENVIRONMENT=staging
      - LOG_LEVEL=INFO
      - WORKER_COUNT=4
      - MAX_CONCURRENT_LLM_REQUESTS=50
    secrets:
      - mongodb_password
      - jwt_secret
      - llm_api_keys
    networks:
      - staging-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 15s
      timeout: 5s
      retries: 3

  message-processor:
    image: registry.company.com/message-service:${VERSION}
    command: ["python", "workers/message_processor.py"]
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
      placement:
        constraints:
          - node.labels.tier == workers
    environment:
      - ENVIRONMENT=staging
      - WORKER_TYPE=message_processor
      - BATCH_SIZE_FOR_ANALYTICS=500
    secrets:
      - mongodb_password
      - redis_password
    networks:
      - staging-network

  llm-worker:
    image: registry.company.com/message-service:${VERSION}
    command: ["python", "workers/llm_worker.py"]
    deploy:
      replicas: 6
      resources:
        limits:
          cpus: '1.5'
          memory: 3G
        reservations:
          cpus: '0.75'
          memory: 1.5G
    environment:
      - ENVIRONMENT=staging
      - WORKER_TYPE=llm_worker
      - MAX_CONCURRENT_REQUESTS=20
    secrets:
      - llm_api_keys
    networks:
      - staging-network

secrets:
  mongodb_password:
    external: true
  jwt_secret:
    external: true
  llm_api_keys:
    external: true

networks:
  staging-network:
    external: true
```

### 2. Script de Deployment para Staging

```bash
#!/bin/bash
# scripts/deploy-staging.sh

set -e

VERSION=${1:-latest}
ENVIRONMENT=staging

echo "🚀 Deploying Message Service v${VERSION} to ${ENVIRONMENT}"

# Validaciones previas
echo "📋 Running pre-deployment checks..."

# Verificar conectividad a dependencias
./scripts/check-dependencies.sh

# Ejecutar tests
echo "🧪 Running test suite..."
docker run --rm \
  -v $(pwd):/app \
  registry.company.com/message-service:${VERSION} \
  pytest tests/ --junitxml=test-results.xml

# Build y push imagen
echo "📦 Building and pushing image..."
docker build -t registry.company.com/message-service:${VERSION} .
docker push registry.company.com/message-service:${VERSION}

# Deploy a staging
echo "🎯 Deploying to staging..."
VERSION=${VERSION} docker stack deploy \
  -c docker-compose.staging.yml \
  message-service-staging

# Verificar deployment
echo "🔍 Verifying deployment..."
timeout 300 bash -c '
  until curl -f http://staging-api.company.com/message-service/health; do
    echo "Waiting for service to be ready..."
    sleep 10
  done
'

# Ejecutar smoke tests
echo "💨 Running smoke tests..."
./scripts/smoke-tests.sh staging

echo "✅ Staging deployment completed successfully!"

# Slack notification
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Message Service '${VERSION}' deployed to staging successfully"}' \
  $SLACK_WEBHOOK_URL
```

## ☁️ Deployment en Producción

### 1. Kubernetes Deployment

#### Namespace y ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: message-service
  labels:
    app.kubernetes.io/name: message-service
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: message-service-config
  namespace: message-service
data:
  SERVICE_NAME: "message-service"
  PORT: "8004"
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  
  # External Service URLs
  AUTH_SERVICE_URL: "http://auth-service.auth-service.svc.cluster.local:8001"
  CONVERSATION_SERVICE_URL: "http://conversation-service.conversation-service.svc.cluster.local:8003"
  CHARACTERS_SERVICE_URL: "http://characters-service.characters-service.svc.cluster.local:8002"
  LLM_SERVICE_URL: "http://llm-service.llm-service.svc.cluster.local:8005"
  
  # Performance Settings
  MAX_CONCURRENT_LLM_REQUESTS: "100"
  MESSAGE_PROCESSING_TIMEOUT: "300"
  BATCH_SIZE_FOR_ANALYTICS: "1000"
  
  # Rate Limiting
  MAX_MESSAGES_PER_MINUTE: "100"
  MAX_MESSAGES_PER_HOUR: "1000"
  MAX_MESSAGES_PER_DAY: "10000"
  
  # Content Safety
  ENABLE_CONTENT_FILTERING: "true"
  SAFETY_THRESHOLD: "0.8"
```

#### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: message-service-secrets
  namespace: message-service
type: Opaque
data:
  MONGODB_URL: <base64-encoded-mongodb-url>
  REDIS_URL: <base64-encoded-redis-url>
  JWT_SECRET_KEY: <base64-encoded-jwt-secret>
  OPENAI_API_KEY: <base64-encoded-openai-key>
  ANTHROPIC_API_KEY: <base64-encoded-anthropic-key>
```

#### Main Service Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: message-service
  namespace: message-service
  labels:
    app: message-service
    component: api
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  selector:
    matchLabels:
      app: message-service
      component: api
  template:
    metadata:
      labels:
        app: message-service
        component: api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8004"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: message-service
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: message-service
        image: registry.company.com/message-service:1.0.0
        ports:
        - containerPort: 8004
          name: http
        envFrom:
        - configMapRef:
            name: message-service-config
        - secretRef:
            name: message-service-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: logs
          mountPath: /app/logs
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: tmp
        emptyDir: {}
      - name: logs
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - message-service
                - key: component
                  operator: In
                  values:
                  - api
              topologyKey: kubernetes.io/hostname
      tolerations:
      - key: "app"
        operator: "Equal"
        value: "message-service"
        effect: "NoSchedule"
```

#### Workers Deployment

```yaml
# k8s/workers-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: message-processor-workers
  namespace: message-service
  labels:
    app: message-service
    component: message-processor
spec:
  replicas: 8
  selector:
    matchLabels:
      app: message-service
      component: message-processor
  template:
    metadata:
      labels:
        app: message-service
        component: message-processor
    spec:
      serviceAccountName: message-service
      containers:
      - name: message-processor
        image: registry.company.com/message-service:1.0.0
        command: ["python", "workers/message_processor.py"]
        envFrom:
        - configMapRef:
            name: message-service-config
        - secretRef:
            name: message-service-secrets
        env:
        - name: WORKER_TYPE
          value: "message_processor"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-workers
  namespace: message-service
  labels:
    app: message-service
    component: llm-worker
spec:
  replicas: 12
  selector:
    matchLabels:
      app: message-service
      component: llm-worker
  template:
    metadata:
      labels:
        app: message-service
        component: llm-worker
    spec:
      serviceAccountName: message-service
      containers:
      - name: llm-worker
        image: registry.company.com/message-service:1.0.0
        command: ["python", "workers/llm_worker.py"]
        envFrom:
        - configMapRef:
            name: message-service-config
        - secretRef:
            name: message-service-secrets
        env:
        - name: WORKER_TYPE
          value: "llm_worker"
        - name: MAX_CONCURRENT_REQUESTS
          value: "5"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-workers
  namespace: message-service
  labels:
    app: message-service
    component: analytics-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: message-service
      component: analytics-worker
  template:
    metadata:
      labels:
        app: message-service
        component: analytics-worker
    spec:
      serviceAccountName: message-service
      containers:
      - name: analytics-worker
        image: registry.company.com/message-service:1.0.0
        command: ["python", "workers/analytics_worker.py"]
        envFrom:
        - configMapRef:
            name: message-service-config
        - secretRef:
            name: message-service-secrets
        env:
        - name: WORKER_TYPE
          value: "analytics_worker"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

#### Services

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: message-service
  namespace: message-service
  labels:
    app: message-service
    component: api
spec:
  type: ClusterIP
  ports:
  - port: 8004
    targetPort: 8004
    protocol: TCP
    name: http
  selector:
    app: message-service
    component: api

---
# Headless service para workers (para service discovery)
apiVersion: v1
kind: Service
metadata:
  name: message-workers
  namespace: message-service
  labels:
    app: message-service
    component: workers
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: message-service
  ports:
  - name: metrics
    port: 9090
    targetPort: 9090
```

#### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: message-service-hpa
  namespace: message-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: message-service
  minReplicas: 5
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: message_queue_size
      target:
        type: AverageValue
        averageValue: "50"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 5
        periodSeconds: 15
      selectPolicy: Max

---
# HPA separado para workers LLM
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-workers-hpa
  namespace: message-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-workers
  minReplicas: 8
  maxReplicas: 50
  metrics:
  - type: Pods
    pods:
      metric:
        name: llm_queue_size
      target:
        type: AverageValue
        averageValue: "10"
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

### 2. Script de Deployment para Kubernetes

```bash
#!/bin/bash
# scripts/deploy-k8s.sh

set -e

VERSION=${1:-latest}
NAMESPACE=message-service
ENVIRONMENT=production

echo "🚀 Deploying Message Service v${VERSION} to Kubernetes (${ENVIRONMENT})"

# Verificaciones previas
echo "📋 Pre-deployment checks..."

# Verificar contexto de kubectl
CURRENT_CONTEXT=$(kubectl config current-context)
echo "Current kubectl context: $CURRENT_CONTEXT"

if [[ "$CURRENT_CONTEXT" != *"production"* ]]; then
  echo "❌ Not in production context. Exiting."
  exit 1
fi

# Verificar namespace
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Aplicar configuraciones
echo "📝 Applying configurations..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Rolling update del deployment principal
echo "🔄 Updating main service..."
kubectl set image deployment/message-service \
  message-service=registry.company.com/message-service:${VERSION} \
  -n ${NAMESPACE}

# Rolling update de workers
echo "🔄 Updating workers..."
kubectl set image deployment/message-processor-workers \
  message-processor=registry.company.com/message-service:${VERSION} \
  -n ${NAMESPACE}

kubectl set image deployment/llm-workers \
  llm-worker=registry.company.com/message-service:${VERSION} \
  -n ${NAMESPACE}

kubectl set image deployment/analytics-workers \
  analytics-worker=registry.company.com/message-service:${VERSION} \
  -n ${NAMESPACE}

# Esperar rollout
echo "⏳ Waiting for rollouts to complete..."
kubectl rollout status deployment/message-service -n ${NAMESPACE} --timeout=600s
kubectl rollout status deployment/message-processor-workers -n ${NAMESPACE} --timeout=600s
kubectl rollout status deployment/llm-workers -n ${NAMESPACE} --timeout=600s
kubectl rollout status deployment/analytics-workers -n ${NAMESPACE} --timeout=600s

# Verificar salud
echo "🏥 Health checks..."
kubectl wait --for=condition=ready pod \
  -l app=message-service,component=api \
  -n ${NAMESPACE} \
  --timeout=300s

# Test de conectividad
EXTERNAL_IP=$(kubectl get service message-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [[ -n "$EXTERNAL_IP" ]]; then
  curl -f http://${EXTERNAL_IP}:8004/health || {
    echo "❌ Health check failed"
    exit 1
  }
fi

# Verificar métricas
echo "📊 Checking metrics..."
kubectl get hpa -n ${NAMESPACE}

echo "✅ Kubernetes deployment completed successfully!"

# Notificación
./scripts/notify-deployment.sh "Message Service v${VERSION} deployed to production"
```

## 📊 Monitoreo y Observabilidad

### 1. Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "message_service_rules.yml"

scrape_configs:
  - job_name: 'message-service'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names: ['message-service']
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__

  - job_name: 'message-workers'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names: ['message-service']
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_component]
      action: keep
      regex: '.*-worker'
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Message Service Dashboard",
    "tags": ["message-service", "microservices"],
    "panels": [
      {
        "title": "Message Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(messages_processed_total{service=\"message-service\"}[5m])"
          }
        ]
      },
      {
        "title": "LLM Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(llm_response_time_bucket{service=\"message-service\"}[5m]))"
          }
        ]
      },
      {
        "title": "Queue Sizes",
        "type": "graph",
        "targets": [
          {
            "expr": "message_queue_size{service=\"message-service\"}"
          },
          {
            "expr": "llm_queue_size{service=\"message-service\"}"
          }
        ]
      },
      {
        "title": "Error Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{service=\"message-service\",status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_tokens_used_total{service=\"message-service\"}[1h])"
          }
        ]
      },
      {
        "title": "Worker Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"message-workers\"}"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules

```yaml
# monitoring/message_service_rules.yml
groups:
- name: message_service_alerts
  rules:
  - alert: MessageServiceDown
    expr: up{job="message-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Message Service is down"
      description: "Message Service has been down for more than 1 minute"

  - alert: HighMessageQueueSize
    expr: message_queue_size > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High message queue size"
      description: "Message queue size is {{ $value }}, above threshold of 1000"

  - alert: LLMHighLatency
    expr: histogram_quantile(0.95, rate(llm_response_time_bucket[5m])) > 10
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "High LLM response latency"
      description: "95th percentile LLM response time is {{ $value }}s"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate"
      description: "Error rate is {{ $value | humanizePercentage }}"

  - alert: WorkerDown
    expr: up{component=~".*-worker"} == 0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Message worker is down"
      description: "Worker {{ $labels.component }} is down"
```

## 🔧 Performance Tuning

### 1. Configuración Optimizada para Producción

```python
# app/core/config.py - Production settings
class ProductionConfig:
    # Database optimization
    MONGODB_CONNECTION_POOL_MIN = 50
    MONGODB_CONNECTION_POOL_MAX = 200
    MONGODB_MAX_IDLE_TIME_MS = 30000
    MONGODB_SERVER_SELECTION_TIMEOUT_MS = 5000
    
    # Redis optimization
    REDIS_CONNECTION_POOL_MAX = 100
    REDIS_SOCKET_KEEPALIVE = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS = {
        'TCP_KEEPIDLE': 1,
        'TCP_KEEPINTVL': 3,
        'TCP_KEEPCNT': 5
    }
    
    # Worker optimization
    WORKER_COUNT = 16
    WORKER_BATCH_SIZE = 50
    WORKER_PREFETCH_COUNT = 100
    
    # LLM optimization
    MAX_CONCURRENT_LLM_REQUESTS = 200
    LLM_REQUEST_TIMEOUT = 45
    LLM_CONNECTION_POOL_SIZE = 50
    
    # Cache optimization
    CACHE_TTL_CONTEXT = 600  # 10 minutos
    CACHE_TTL_ANALYTICS = 3600  # 1 hora
    CACHE_TTL_SEARCH = 1800  # 30 minutos
```

### 2. JVM Tuning para MongoDB

```bash
# /etc/mongod.conf
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: zstd
    indexConfig:
      prefixCompression: true

net:
  maxIncomingConnections: 1000
  compression:
    compressors: "zstd,zlib"

systemLog:
  destination: file
  path: /var/log/mongodb/mongod.log
  logAppend: true
  logRotate: reopen

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100
```

### 3. Redis Optimization

```bash
# /etc/redis/redis.conf
maxmemory 8gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Network optimization
tcp-keepalive 300
timeout 0

# Threading
io-threads 4
io-threads-do-reads yes

# Persistence optimization
rdbcompression yes
rdbchecksum yes
```

## 🚨 Troubleshooting

### Problemas Comunes y Soluciones

| Problema | Síntoma | Diagnóstico | Solución |
|----------|---------|-------------|----------|
| Alta latencia LLM | Response time > 5s | Check LLM service logs | Escalar workers LLM, verificar network |
| Memory leaks | OOMKilled pods | Monitor heap usage | Restart workers, revisar cache TTL |
| Queue backup | Queue size > 1000 | Check worker health | Escalar workers, verificar dependencies |
| Database locks | Slow queries | Check MongoDB profiler | Optimizar índices, revisar query patterns |
| Redis connection issues | Connection timeouts | Check Redis logs | Aumentar connection pool, verificar Redis memory |

### Comandos de Diagnóstico

```bash
# Verificar estado de pods
kubectl get pods -n message-service -o wide

# Ver logs en tiempo real
kubectl logs -f deployment/message-service -n message-service

# Verificar métricas de HPA
kubectl get hpa -n message-service

# Ejecutar en pod para debugging
kubectl exec -it deploy/message-service -n message-service -- /bin/bash

# Verificar configuración
kubectl describe configmap message-service-config -n message-service

# Verificar recursos
kubectl top pods -n message-service

# Test de conectividad entre servicios
kubectl run debug --image=curlimages/curl -it --rm -- /bin/sh
```

### Scripts de Diagnóstico Automatizado

```bash
#!/bin/bash
# scripts/diagnose-production.sh

echo "🔍 Message Service Production Diagnostics"

# Verificar estado general
echo "📊 Service Status:"
kubectl get deployment,service,hpa -n message-service

# Verificar salud de pods
echo "🏥 Pod Health:"
kubectl get pods -n message-service | grep -v Running | head -10

# Verificar logs de errores recientes
echo "🚨 Recent Errors:"
kubectl logs deployment/message-service -n message-service --since=10m | grep -i error | tail -10

# Verificar métricas clave
echo "📈 Key Metrics:"
curl -s http://prometheus:9090/api/v1/query?query=message_queue_size | jq .

# Verificar conectividad a dependencias
echo "🔗 Dependency Health:"
kubectl run connectivity-test --image=curlimages/curl --rm -i --restart=Never -- \
  sh -c "
    curl -s -o /dev/null -w 'MongoDB: %{http_code}\n' http://mongodb:27017/
    curl -s -o /dev/null -w 'Redis: %{http_code}\n' http://redis:6379/
    curl -s -o /dev/null -w 'Auth Service: %{http_code}\n' http://auth-service.auth-service:8001/health
  "

echo "✅ Diagnostics completed"
```

Esta guía de deployment proporciona una configuración robusta y escalable para el Message Service en todos los entornos, con énfasis en alta disponibilidad, monitoreo comprehensivo y facilidad de troubleshooting.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "create-message-documentation", "content": "Create comprehensive Message Service documentation", "status": "completed"}]