# Conversation Service - Deployment Guide

Guía completa para el deployment del Conversation Service en diferentes entornos.

## 📋 Información General

Esta guía cubre el deployment del Conversation Service desde desarrollo local hasta producción, incluyendo containerización, orquestación, monitoring y mejores prácticas de seguridad.

## 🏗️ Prerequisitos

### Requisitos del Sistema

| Componente | Versión Mínima | Recomendada |
|------------|----------------|-------------|
| Python | 3.11+ | 3.11+ |
| MongoDB | 5.0+ | 6.0+ |
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |
| RAM | 512MB | 1GB+ |
| CPU | 1 core | 2+ cores |
| Storage | 1GB | 5GB+ |

### Dependencias Externas

- **Auth Service**: Puerto 8001 (para validación JWT)
- **Characters Service**: Puerto 8002 (para validación de personajes)
- **Message Service**: Puerto 8004 (para estadísticas)
- **MongoDB**: Puerto 27017 (base de datos principal)

## 🚀 Deployment Local

### 1. Setup Manual (Desarrollo)

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd microservices/conversation-service

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo

# 4. Configurar variables de entorno
cp .env.example .env
```

#### Configuración .env para Desarrollo

```bash
# Service Configuration
SERVICE_NAME=conversation-service
PORT=8003
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=conversation_service_dev

# External Services (URLs de desarrollo)
AUTH_SERVICE_URL=http://localhost:8001
CHARACTERS_SERVICE_URL=http://localhost:8002
MESSAGE_SERVICE_URL=http://localhost:8004

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Performance
CONNECTION_POOL_MIN=5
CONNECTION_POOL_MAX=20
REQUEST_TIMEOUT=30.0

# Development
DEBUG=true
RELOAD=true
```

```bash
# 5. Ejecutar migraciones de base de datos
python scripts/setup_indexes.py

# 6. Iniciar el servicio
python -m app.main

# O con recarga automática
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### 2. Docker Local

#### Dockerfile

```dockerfile
# conversation-service/Dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set PATH to include user site-packages
ENV PATH="/home/appuser/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Start application
CMD ["python", "-m", "app.main"]
```

#### Docker Compose (Desarrollo)

```yaml
# conversation-service/docker-compose.yml
version: '3.8'

services:
  conversation-service:
    build: .
    ports:
      - "8003:8003"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - AUTH_SERVICE_URL=http://auth-service:8001
      - CHARACTERS_SERVICE_URL=http://characters-service:8002
      - JWT_SECRET_KEY=dev-secret-key
    depends_on:
      - mongodb
      - redis
    networks:
      - microservices-network
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_DATABASE=conversation_service
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

volumes:
  mongodb_data:
  redis_data:

networks:
  microservices-network:
    driver: bridge
```

```bash
# Ejecutar con Docker Compose
docker-compose up -d

# Ver logs
docker-compose logs -f conversation-service

# Detener servicios
docker-compose down
```

## 🌐 Deployment en Staging

### 1. Docker Compose para Staging

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  conversation-service:
    image: conversation-service:${VERSION}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    environment:
      - ENVIRONMENT=staging
      - LOG_LEVEL=INFO
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
    secrets:
      - jwt_secret
      - mongodb_password
    networks:
      - staging-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:6.0
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD_FILE=/run/secrets/mongodb_password
    secrets:
      - mongodb_password
    volumes:
      - mongodb_staging_data:/data/db
    networks:
      - staging-network

secrets:
  jwt_secret:
    external: true
  mongodb_password:
    external: true

volumes:
  mongodb_staging_data:

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

echo "🚀 Deploying Conversation Service v${VERSION} to ${ENVIRONMENT}"

# Build image
echo "📦 Building Docker image..."
docker build -t conversation-service:${VERSION} .

# Tag for registry
docker tag conversation-service:${VERSION} registry.company.com/conversation-service:${VERSION}

# Push to registry
echo "📤 Pushing to registry..."
docker push registry.company.com/conversation-service:${VERSION}

# Deploy to staging
echo "🎯 Deploying to staging..."
VERSION=${VERSION} docker-compose -f docker-compose.staging.yml up -d

# Wait for health check
echo "🔍 Waiting for service to be healthy..."
timeout 300 bash -c 'until curl -f http://localhost:8003/health; do sleep 5; done'

echo "✅ Deployment completed successfully!"

# Run smoke tests
echo "🧪 Running smoke tests..."
python scripts/smoke_tests.py --environment=staging

echo "🎉 Staging deployment successful!"
```

## ☁️ Deployment en Producción

### 1. Kubernetes Deployment

#### Namespace y ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: conversation-service
  labels:
    app: conversation-service
    environment: production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: conversation-service-config
  namespace: conversation-service
data:
  SERVICE_NAME: "conversation-service"
  PORT: "8003"
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  AUTH_SERVICE_URL: "http://auth-service.auth-service.svc.cluster.local:8001"
  CHARACTERS_SERVICE_URL: "http://characters-service.characters-service.svc.cluster.local:8002"
  MESSAGE_SERVICE_URL: "http://message-service.message-service.svc.cluster.local:8004"
  CONNECTION_POOL_MIN: "10"
  CONNECTION_POOL_MAX: "50"
  REQUEST_TIMEOUT: "30.0"
```

#### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: conversation-service-secrets
  namespace: conversation-service
type: Opaque
data:
  JWT_SECRET_KEY: <base64-encoded-secret>
  MONGODB_URL: <base64-encoded-mongodb-url>
  REDIS_URL: <base64-encoded-redis-url>
```

#### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: conversation-service
  namespace: conversation-service
  labels:
    app: conversation-service
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: conversation-service
  template:
    metadata:
      labels:
        app: conversation-service
        version: v1
    spec:
      serviceAccountName: conversation-service
      containers:
      - name: conversation-service
        image: registry.company.com/conversation-service:1.0.0
        ports:
        - containerPort: 8003
          name: http
        envFrom:
        - configMapRef:
            name: conversation-service-config
        - secretRef:
            name: conversation-service-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: logs
          mountPath: /app/logs
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
                  - conversation-service
              topologyKey: kubernetes.io/hostname
```

#### Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: conversation-service
  namespace: conversation-service
  labels:
    app: conversation-service
spec:
  type: ClusterIP
  ports:
  - port: 8003
    targetPort: 8003
    protocol: TCP
    name: http
  selector:
    app: conversation-service
```

#### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: conversation-service-hpa
  namespace: conversation-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: conversation-service
  minReplicas: 3
  maxReplicas: 10
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

### 2. Script de Deployment para Kubernetes

```bash
#!/bin/bash
# scripts/deploy-k8s.sh

set -e

VERSION=${1:-latest}
NAMESPACE=conversation-service

echo "🚀 Deploying Conversation Service v${VERSION} to Kubernetes"

# Create namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMaps and Secrets
echo "📝 Applying configuration..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Update deployment image
echo "🔄 Updating deployment..."
kubectl set image deployment/conversation-service \
  conversation-service=registry.company.com/conversation-service:${VERSION} \
  -n ${NAMESPACE}

# Wait for rollout to complete
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/conversation-service -n ${NAMESPACE} --timeout=600s

# Verify deployment
echo "🔍 Verifying deployment..."
kubectl get pods -n ${NAMESPACE} -l app=conversation-service

# Run health check
echo "🏥 Running health check..."
EXTERNAL_IP=$(kubectl get service conversation-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -f http://${EXTERNAL_IP}:8003/health || {
  echo "❌ Health check failed"
  exit 1
}

echo "✅ Kubernetes deployment completed successfully!"
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy Conversation Service

on:
  push:
    branches: [main]
    paths: ['microservices/conversation-service/**']
  pull_request:
    branches: [main]
    paths: ['microservices/conversation-service/**']

env:
  REGISTRY: registry.company.com
  IMAGE_NAME: conversation-service

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd microservices/conversation-service
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        cd microservices/conversation-service
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push
      id: build
      uses: docker/build-push-action@v4
      with:
        context: microservices/conversation-service
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        echo "Deploying to staging..."
        # Add your staging deployment commands here

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy to production
      run: |
        export KUBECONFIG=kubeconfig
        ./scripts/deploy-k8s.sh ${{ github.sha }}
```

## 📊 Monitoring y Observabilidad

### 1. Prometheus Metrics

```yaml
# k8s/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: conversation-service
  namespace: conversation-service
  labels:
    app: conversation-service
spec:
  selector:
    matchLabels:
      app: conversation-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Conversation Service",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{service=\"conversation-service\"}[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"conversation-service\"}[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{service=\"conversation-service\",status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

### 3. Logging con ELK Stack

```yaml
# k8s/filebeat-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: conversation-service
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*conversation-service*.log
      processors:
        - add_kubernetes_metadata:
            host: ${NODE_NAME}
            matchers:
            - logs_path:
                logs_path: "/var/log/containers/"

    output.elasticsearch:
      hosts: ["elasticsearch.logging.svc.cluster.local:9200"]
      index: "conversation-service-%{+yyyy.MM.dd}"

    setup.template.name: "conversation-service"
    setup.template.pattern: "conversation-service-*"
```

## 🛡️ Seguridad

### 1. Network Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: conversation-service-netpol
  namespace: conversation-service
spec:
  podSelector:
    matchLabels:
      app: conversation-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: api-gateway
    ports:
    - protocol: TCP
      port: 8003
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: auth-service
    ports:
    - protocol: TCP
      port: 8001
  - to:
    - namespaceSelector:
        matchLabels:
          name: characters-service
    ports:
    - protocol: TCP
      port: 8002
  - to: []
    ports:
    - protocol: TCP
      port: 27017  # MongoDB
    - protocol: TCP
      port: 6379   # Redis
    - protocol: TCP
      port: 53     # DNS
    - protocol: UDP
      port: 53     # DNS
```

### 2. Pod Security Policy

```yaml
# k8s/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: conversation-service-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 🔧 Troubleshooting

### Comandos Útiles

```bash
# Verificar estado del servicio
kubectl get pods -n conversation-service
kubectl describe pod <pod-name> -n conversation-service

# Ver logs
kubectl logs -f deployment/conversation-service -n conversation-service

# Port forward para debugging
kubectl port-forward service/conversation-service 8003:8003 -n conversation-service

# Ejecutar shell en contenedor
kubectl exec -it <pod-name> -n conversation-service -- /bin/bash

# Verificar configuración
kubectl get configmap conversation-service-config -n conversation-service -o yaml

# Verificar secrets
kubectl get secret conversation-service-secrets -n conversation-service

# Verificar connectivity
kubectl run debug --image=curlimages/curl -it --rm -- /bin/sh
```

### Problemas Comunes

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Pod no inicia | `CrashLoopBackOff` | Verificar logs, configuración, recursos |
| Health check falla | `Unhealthy` en readiness | Verificar conexión a MongoDB, variables de entorno |
| Error de conectividad | Timeout en servicios externos | Verificar network policies, service discovery |
| Alto uso de memoria | OOMKilled | Ajustar resource limits, optimizar queries |
| Latencia alta | Slow response times | Verificar índices de DB, connection pooling |

### Scripts de Diagnóstico

```bash
#!/bin/bash
# scripts/diagnose.sh

echo "🔍 Conversation Service Diagnostics"

# Check pod status
echo "📋 Pod Status:"
kubectl get pods -n conversation-service -l app=conversation-service

# Check resource usage
echo "📊 Resource Usage:"
kubectl top pods -n conversation-service

# Check service endpoints
echo "🔗 Service Endpoints:"
kubectl get endpoints -n conversation-service

# Test connectivity
echo "🌐 Connectivity Test:"
kubectl run connectivity-test --image=curlimages/curl --rm -i --restart=Never -- \
  curl -s -o /dev/null -w "%{http_code}" http://conversation-service.conversation-service.svc.cluster.local:8003/health

echo "✅ Diagnostics completed"
```

## 📈 Performance Tuning

### Configuración de Producción

```bash
# Optimización de MongoDB
mongod --config /etc/mongod.conf \
  --wiredTigerCacheSizeGB 8 \
  --wiredTigerConcurrentReadTransactions 64 \
  --wiredTigerConcurrentWriteTransactions 64

# Optimización de Python
export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1

# Configuración de Uvicorn para producción
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8003 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-log \
  --loop uvloop
```

Esta guía proporciona todo lo necesario para deployar el Conversation Service de manera segura y escalable en diferentes entornos.