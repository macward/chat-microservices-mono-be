# Message Service - Architecture

Documentación completa de la arquitectura del Message Service, patrones de diseño y estrategias de implementación.

## 📋 Visión General

El Message Service es el microservicio de mayor complejidad técnica en el ecosistema Character Chat API, responsable del procesamiento de alto volumen de mensajes, integración con múltiples proveedores LLM, y análisis en tiempo real. Está diseñado para manejar millones de mensajes con baja latencia y alta disponibilidad.

## 🏗️ Arquitectura del Sistema

### Contexto en el Ecosistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                             │
│                    (Load Balancer)                             │
└─────────────┬───────────────┬───────────────┬───────────────────┘
              │               │               │
    ┌─────────▼─────────┐   ┌─▼─────────┐   ┌─▼────────────┐
    │  Auth Service     │   │Conversation│   │ Characters   │
    │    Port: 8001     │   │  Service   │   │   Service    │
    │                   │   │Port: 8003  │   │ Port: 8002   │
    └─────────┬─────────┘   └─┬─────────┘   └─┬────────────┘
              │               │               │
              └───────────────┼───────────────┼─────────────────┐
                              │               │                 │
                    ┌─────────▼─────────┐     │                 │
                    │ Message Service   │     │                 │
                    │  Port: 8004       │◄────┘                 │
                    │                   │                       │
                    └─────────┬─────────┘                       │
                              │                                 │
                    ┌─────────▼─────────┐                       │
                    │   LLM Service     │◄──────────────────────┘
                    │  Port: 8005       │
                    └───────────────────┘
```

### Responsabilidades en el Ecosistema

**Message Service actúa como:**
- **Procesador Central**: Hub para todo el procesamiento de mensajes
- **Orquestador LLM**: Coordina llamadas a diferentes proveedores de IA
- **Motor de Analytics**: Genera métricas y estadísticas en tiempo real
- **Gateway de Contenido**: Filtra y valida todo el contenido del sistema

## 🔧 Arquitectura Interna

### Patrón de Arquitectura por Capas Expandido

```
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   HTTP      │  │Rate Limiting│  │ Auth        │              │
│  │ Endpoints   │  │& Validation │  │Middleware   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Service Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Message     │  │ LLM         │  │ Content     │              │
│  │ Service     │  │ Service     │  │ Service     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Analytics   │  │ Search      │  │ Queue       │              │
│  │ Service     │  │ Service     │  │ Service     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                  Repository Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Message     │  │ Analytics   │  │ Search      │              │
│  │ Repository  │  │ Repository  │  │ Repository  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                Infrastructure Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   MongoDB   │  │    Redis    │  │  External   │              │
│  │  (Primary)  │  │(Cache+Queue)│  │  Services   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Arquitectura de Procesamiento Asíncrono

```
┌─────────────────────────────────────────────────────────────────┐
│                    Message Processing Flow                      │
└─────────────────────────────────────────────────────────────────┘

Request      Validation     Queue        Worker        LLM          Storage
   │              │           │           │             │             │
   ▼              ▼           ▼           ▼             ▼             ▼
┌─────┐      ┌─────────┐  ┌───────┐   ┌────────┐   ┌─────────┐   ┌─────────┐
│POST │────► │Validate │─►│Redis  │──►│Background│──►│Provider │──►│MongoDB  │
│/msg │      │& Enqueue│  │Queue  │   │Worker    │   │API      │   │Storage  │
└─────┘      └─────────┘  └───────┘   └────────┘   └─────────┘   └─────────┘
   │              │           │           │             │             │
   ▼              │           │           │             │             │
┌─────┐           │           │           │             │             │
│202  │◄──────────┘           │           │             │             │
│Resp │                       │           │             │             │
└─────┘                       │           │             │             │
                               │           │             │             │
                               ▼           ▼             ▼             ▼
                           ┌───────┐   ┌────────┐   ┌─────────┐   ┌─────────┐
                           │Status │   │Progress│   │Response │   │Complete │
                           │Update │   │Track   │   │Process  │   │Notify   │
                           └───────┘   └────────┘   └─────────┘   └─────────┘
```

## 🎯 Patrones de Diseño Implementados

### 1. Command Query Responsibility Segregation (CQRS)

**Separación de Comandos y Consultas**

```python
# app/services/message_service.py
class MessageService:
    def __init__(
        self,
        write_repository: MessageWriteRepository,
        read_repository: MessageReadRepository,
        event_publisher: EventPublisher
    ):
        self.write_repo = write_repository
        self.read_repo = read_repository
        self.event_publisher = event_publisher
    
    # COMMAND - Modificación de estado
    async def send_message(self, command: SendMessageCommand) -> MessageId:
        # Validación y procesamiento
        message = await self._process_message(command)
        
        # Escritura optimizada
        message_id = await self.write_repo.save(message)
        
        # Publicar evento para procesamiento asíncrono
        await self.event_publisher.publish(
            MessageCreatedEvent(message_id, command.conversation_id)
        )
        
        return message_id
    
    # QUERY - Solo lectura, optimizada
    async def get_conversation_messages(
        self, 
        query: GetMessagesQuery
    ) -> PaginatedMessages:
        # Lectura optimizada con cache
        return await self.read_repo.get_paginated(
            query.conversation_id,
            query.pagination,
            query.filters
        )
```

### 2. Event Sourcing Pattern

**Almacenamiento de Eventos para Auditabilidad**

```python
# app/core/events.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class Event(ABC):
    def __init__(self):
        self.event_id = str(uuid4())
        self.timestamp = datetime.utcnow()
        self.version = 1
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class MessageCreatedEvent(Event):
    def __init__(self, message_id: str, conversation_id: str, content: str):
        super().__init__()
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.content = content
        self.event_type = "message_created"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }

class LLMResponseGeneratedEvent(Event):
    def __init__(
        self, 
        message_id: str, 
        response_content: str, 
        token_usage: Dict[str, int],
        processing_time_ms: int
    ):
        super().__init__()
        self.message_id = message_id
        self.response_content = response_content
        self.token_usage = token_usage
        self.processing_time_ms = processing_time_ms
        self.event_type = "llm_response_generated"

# app/services/event_store.py
class EventStore:
    async def append_event(self, stream_id: str, event: Event) -> None:
        event_data = {
            "stream_id": stream_id,
            "event_data": event.to_dict(),
            "created_at": datetime.utcnow()
        }
        await self.events_collection.insert_one(event_data)
    
    async def get_events(self, stream_id: str) -> List[Event]:
        cursor = self.events_collection.find({"stream_id": stream_id})
        events = []
        async for event_doc in cursor:
            events.append(self._deserialize_event(event_doc))
        return events
```

### 3. Saga Pattern

**Orquestación de Transacciones Distribuidas**

```python
# app/sagas/message_processing_saga.py
class MessageProcessingSaga:
    def __init__(
        self,
        message_service: MessageService,
        llm_service: LLMService,
        analytics_service: AnalyticsService,
        conversation_service: ConversationService
    ):
        self.message_service = message_service
        self.llm_service = llm_service
        self.analytics_service = analytics_service
        self.conversation_service = conversation_service
        self.state_store = SagaStateStore()
    
    async def handle_message_created(self, event: MessageCreatedEvent):
        saga_id = f"message_processing_{event.message_id}"
        
        try:
            # Paso 1: Validar conversación existe
            conversation = await self.conversation_service.get_conversation(
                event.conversation_id
            )
            await self._update_saga_state(saga_id, "conversation_validated")
            
            # Paso 2: Obtener contexto
            context = await self.message_service.build_context(
                event.conversation_id,
                conversation.settings.context_window_size
            )
            await self._update_saga_state(saga_id, "context_built")
            
            # Paso 3: Generar respuesta LLM
            llm_response = await self.llm_service.generate_response(
                context,
                conversation.character_id,
                conversation.settings
            )
            await self._update_saga_state(saga_id, "llm_response_generated")
            
            # Paso 4: Guardar respuesta
            await self.message_service.save_assistant_message(
                event.conversation_id,
                llm_response
            )
            await self._update_saga_state(saga_id, "response_saved")
            
            # Paso 5: Actualizar analytics
            await self.analytics_service.update_conversation_stats(
                event.conversation_id,
                llm_response.token_usage
            )
            await self._update_saga_state(saga_id, "analytics_updated")
            
            # Paso 6: Notificar completado
            await self._complete_saga(saga_id)
            
        except Exception as e:
            await self._handle_saga_error(saga_id, e)
    
    async def _handle_saga_error(self, saga_id: str, error: Exception):
        # Implementar compensación basada en el estado actual
        current_state = await self.state_store.get_state(saga_id)
        
        if current_state == "llm_response_generated":
            # Reversar: Marcar mensaje como fallido
            await self.message_service.mark_message_failed(saga_id)
        
        # Log y alertas
        logger.error(f"Saga {saga_id} failed: {str(error)}")
        await self._send_alert(saga_id, error)
```

### 4. Circuit Breaker Pattern Avanzado

**Protección contra Fallos en Cascada**

```python
# app/core/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Funcionamiento normal
    OPEN = "open"          # Bloqueando requests
    HALF_OPEN = "half_open"  # Probando recuperación

class AdvancedCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3,
        timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker is OPEN. Next retry in "
                        f"{self._time_to_next_attempt()}s"
                    )
            
            try:
                # Ejecutar con timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.timeout
                )
                
                await self._on_success()
                return result
                
            except Exception as e:
                await self._on_failure()
                raise e
    
    async def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    async def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return False
        
        return (datetime.utcnow() - self.last_failure_time).total_seconds() >= self.recovery_timeout

# Uso en servicios
class LLMService:
    def __init__(self):
        self.circuit_breakers = {
            "lmstudio": AdvancedCircuitBreaker(failure_threshold=3),
            "openai": AdvancedCircuitBreaker(failure_threshold=5),
            "anthropic": AdvancedCircuitBreaker(failure_threshold=5)
        }
    
    async def generate_response(self, provider: str, *args, **kwargs):
        circuit_breaker = self.circuit_breakers.get(provider)
        if not circuit_breaker:
            raise ValueError(f"Unknown provider: {provider}")
        
        return await circuit_breaker.call(
            self._call_llm_provider,
            provider,
            *args,
            **kwargs
        )
```

### 5. Strategy Pattern para Providers LLM

**Abstraer Diferentes Proveedores de IA**

```python
# app/services/llm/providers.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def validate_config(self, config: LLMConfig) -> bool:
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        pass

class LMStudioProvider(LLMProvider):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig
    ) -> LLMResponse:
        payload = {
            "messages": messages,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        processing_time = int((time.time() - start_time) * 1000)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            provider="lmstudio",
            token_usage=TokenUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"]
            ),
            processing_time_ms=processing_time,
            finish_reason=data["choices"][0]["finish_reason"]
        )

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig
    ) -> LLMResponse:
        start_time = time.time()
        
        response = await self.client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            token_usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            ),
            processing_time_ms=processing_time,
            finish_reason=response.choices[0].finish_reason
        )

# Factory para providers
class LLMProviderFactory:
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, name: str, **config) -> LLMProvider:
        if name not in cls._providers:
            raise ValueError(f"Unknown provider: {name}")
        
        return cls._providers[name](**config)

# Registro de providers
LLMProviderFactory.register_provider("lmstudio", LMStudioProvider)
LLMProviderFactory.register_provider("openai", OpenAIProvider)
LLMProviderFactory.register_provider("anthropic", AnthropicProvider)
```

### 6. Observer Pattern para Analytics

**Sistema de Eventos para Métricas**

```python
# app/core/analytics_observer.py
class AnalyticsObserver(ABC):
    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        pass

class TokenUsageAnalytics(AnalyticsObserver):
    def __init__(self, analytics_repo: AnalyticsRepository):
        self.analytics_repo = analytics_repo
    
    async def handle_event(self, event: Event) -> None:
        if isinstance(event, LLMResponseGeneratedEvent):
            await self._update_token_metrics(event)
    
    async def _update_token_metrics(self, event: LLMResponseGeneratedEvent):
        daily_stats = await self.analytics_repo.get_daily_stats(
            date=datetime.utcnow().date()
        )
        
        daily_stats.total_tokens += event.token_usage.total_tokens
        daily_stats.total_cost += event.token_usage.total_cost
        daily_stats.request_count += 1
        
        await self.analytics_repo.save_daily_stats(daily_stats)

class PerformanceAnalytics(AnalyticsObserver):
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    async def handle_event(self, event: Event) -> None:
        if isinstance(event, LLMResponseGeneratedEvent):
            # Actualizar métricas de rendimiento
            self.metrics.record_histogram(
                "llm_response_time",
                event.processing_time_ms,
                tags={"provider": event.provider, "model": event.model}
            )
            
            self.metrics.increment_counter(
                "llm_requests_total",
                tags={"provider": event.provider, "status": "success"}
            )

# Event publisher con observers
class EventPublisher:
    def __init__(self):
        self.observers: List[AnalyticsObserver] = []
    
    def add_observer(self, observer: AnalyticsObserver):
        self.observers.append(observer)
    
    async def publish(self, event: Event):
        # Almacenar evento
        await self.event_store.append_event(
            stream_id=event.stream_id,
            event=event
        )
        
        # Notificar a todos los observers
        for observer in self.observers:
            try:
                await observer.handle_event(event)
            except Exception as e:
                logger.error(f"Observer failed: {e}")
```

## 🔄 Arquitectura de Caching

### Estrategia de Cache Multi-Nivel

```python
# app/core/cache.py
class MultiLevelCache:
    def __init__(
        self,
        l1_cache: InMemoryCache,      # Más rápido, menor capacidad
        l2_cache: RedisCache,         # Rápido, mayor capacidad
        l3_cache: DatabaseCache       # Más lento, capacidad ilimitada
    ):
        self.l1 = l1_cache
        self.l2 = l2_cache
        self.l3 = l3_cache
    
    async def get(self, key: str) -> Optional[Any]:
        # Intentar L1 (in-memory)
        value = await self.l1.get(key)
        if value is not None:
            return value
        
        # Intentar L2 (Redis)
        value = await self.l2.get(key)
        if value is not None:
            # Promover a L1
            await self.l1.set(key, value, ttl=300)
            return value
        
        # Intentar L3 (Database/Cold storage)
        value = await self.l3.get(key)
        if value is not None:
            # Promover a L2 y L1
            await self.l2.set(key, value, ttl=3600)
            await self.l1.set(key, value, ttl=300)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Escribir en todos los niveles
        await asyncio.gather(
            self.l1.set(key, value, ttl=min(ttl, 300)),
            self.l2.set(key, value, ttl=ttl),
            self.l3.set(key, value, ttl=ttl)
        )
    
    async def invalidate(self, key: str):
        # Invalidar en todos los niveles
        await asyncio.gather(
            self.l1.delete(key),
            self.l2.delete(key),
            self.l3.delete(key)
        )

# Cache específico para contexto de conversaciones
class ConversationContextCache:
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
    
    async def get_context(
        self,
        conversation_id: str,
        window_size: int
    ) -> Optional[List[Dict[str, str]]]:
        cache_key = f"context:{conversation_id}:{window_size}"
        return await self.cache.get(cache_key)
    
    async def set_context(
        self,
        conversation_id: str,
        window_size: int,
        context: List[Dict[str, str]]
    ):
        cache_key = f"context:{conversation_id}:{window_size}"
        # Context cache con TTL corto para mantener coherencia
        await self.cache.set(cache_key, context, ttl=300)
    
    async def invalidate_conversation(self, conversation_id: str):
        # Invalidar todos los contextos de una conversación
        pattern = f"context:{conversation_id}:*"
        await self.cache.invalidate_pattern(pattern)
```

## 📊 Arquitectura de Analytics en Tiempo Real

### Stream Processing para Métricas

```python
# app/analytics/stream_processor.py
class RealTimeAnalyticsProcessor:
    def __init__(
        self,
        event_stream: EventStream,
        metrics_store: MetricsStore,
        alert_manager: AlertManager
    ):
        self.event_stream = event_stream
        self.metrics_store = metrics_store
        self.alert_manager = alert_manager
        self.running = False
    
    async def start_processing(self):
        self.running = True
        
        # Procesar múltiples streams en paralelo
        await asyncio.gather(
            self._process_message_events(),
            self._process_llm_events(),
            self._process_performance_events(),
            self._process_error_events()
        )
    
    async def _process_message_events(self):
        async for event in self.event_stream.subscribe("message_events"):
            if isinstance(event, MessageCreatedEvent):
                await self._update_message_metrics(event)
            elif isinstance(event, MessageArchivedEvent):
                await self._update_archive_metrics(event)
    
    async def _process_llm_events(self):
        async for event in self.event_stream.subscribe("llm_events"):
            if isinstance(event, LLMResponseGeneratedEvent):
                await self._update_llm_metrics(event)
                await self._check_performance_thresholds(event)
    
    async def _update_message_metrics(self, event: MessageCreatedEvent):
        # Actualizar contadores en tiempo real
        metrics = {
            "messages_total": 1,
            "messages_by_user": {event.user_id: 1},
            "messages_by_conversation": {event.conversation_id: 1},
            "timestamp": event.timestamp
        }
        
        await self.metrics_store.increment_counters(metrics)
    
    async def _check_performance_thresholds(
        self,
        event: LLMResponseGeneratedEvent
    ):
        # Verificar SLA de rendimiento
        if event.processing_time_ms > 5000:  # > 5 segundos
            alert = PerformanceAlert(
                message_id=event.message_id,
                processing_time=event.processing_time_ms,
                threshold=5000,
                severity="warning"
            )
            await self.alert_manager.send_alert(alert)
        
        # Verificar uso excesivo de tokens
        if event.token_usage.total_tokens > 4000:
            alert = TokenUsageAlert(
                message_id=event.message_id,
                token_count=event.token_usage.total_tokens,
                threshold=4000,
                severity="info"
            )
            await self.alert_manager.send_alert(alert)

# Sliding window analytics
class SlidingWindowAnalytics:
    def __init__(self, window_size_minutes: int = 5):
        self.window_size = window_size_minutes
        self.data_points = deque()
        self.lock = asyncio.Lock()
    
    async def add_data_point(self, value: float, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        async with self.lock:
            self.data_points.append((timestamp, value))
            await self._cleanup_old_data()
    
    async def get_average(self) -> float:
        async with self.lock:
            if not self.data_points:
                return 0.0
            
            values = [point[1] for point in self.data_points]
            return sum(values) / len(values)
    
    async def get_percentile(self, percentile: float) -> float:
        async with self.lock:
            if not self.data_points:
                return 0.0
            
            values = sorted([point[1] for point in self.data_points])
            index = int(len(values) * percentile / 100)
            return values[min(index, len(values) - 1)]
    
    async def _cleanup_old_data(self):
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_size)
        
        while (self.data_points and 
               self.data_points[0][0] < cutoff_time):
            self.data_points.popleft()
```

## 🔍 Arquitectura de Búsqueda

### Elasticsearch Integration

```python
# app/search/elasticsearch_service.py
class ElasticsearchService:
    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client
        self.index_name = "messages"
    
    async def index_message(self, message: Message):
        doc = {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "user_id": message.user_id,
            "content": message.content.text,
            "role": message.role,
            "timestamp": message.timestamps.created_at,
            "topics": message.custom_metadata.get("topics", []),
            "sentiment": message.custom_metadata.get("sentiment"),
            "language": message.content.detected_language
        }
        
        await self.es.index(
            index=self.index_name,
            id=message.message_id,
            document=doc
        )
    
    async def search_messages(
        self,
        query: SearchQuery
    ) -> SearchResults:
        # Construir query DSL de Elasticsearch
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query.text,
                                "fields": ["content^3", "topics^2"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "content": {}
                }
            },
            "sort": [
                {"timestamp": {"order": "desc"}}
            ]
        }
        
        # Agregar filtros
        if query.user_id:
            es_query["query"]["bool"]["filter"].append(
                {"term": {"user_id": query.user_id}}
            )
        
        if query.conversation_id:
            es_query["query"]["bool"]["filter"].append(
                {"term": {"conversation_id": query.conversation_id}}
            )
        
        if query.date_range:
            es_query["query"]["bool"]["filter"].append({
                "range": {
                    "timestamp": {
                        "gte": query.date_range.start,
                        "lte": query.date_range.end
                    }
                }
            })
        
        # Ejecutar búsqueda
        response = await self.es.search(
            index=self.index_name,
            body=es_query,
            size=query.limit,
            from_=query.offset
        )
        
        # Procesar resultados
        results = []
        for hit in response["hits"]["hits"]:
            result = SearchResult(
                message_id=hit["_source"]["message_id"],
                content=hit["_source"]["content"],
                score=hit["_score"],
                highlights=hit.get("highlight", {}),
                metadata=hit["_source"]
            )
            results.append(result)
        
        return SearchResults(
            results=results,
            total_hits=response["hits"]["total"]["value"],
            max_score=response["hits"]["max_score"]
        )
```

## 🛡️ Arquitectura de Seguridad

### Content Security Pipeline

```python
# app/security/content_pipeline.py
class ContentSecurityPipeline:
    def __init__(self):
        self.filters = [
            LengthFilter(max_length=50000),
            ProfanityFilter(),
            PersonalInfoFilter(),
            SpamDetectionFilter(),
            ToxicityFilter(),
            PromptInjectionFilter()
        ]
    
    async def process_content(self, content: str) -> SecurityResult:
        result = SecurityResult(
            original_content=content,
            is_safe=True,
            detected_issues=[],
            sanitized_content=content,
            confidence_score=1.0
        )
        
        # Ejecutar todos los filtros
        for filter_instance in self.filters:
            filter_result = await filter_instance.process(result.sanitized_content)
            
            if not filter_result.is_safe:
                result.is_safe = False
                result.detected_issues.extend(filter_result.issues)
                result.confidence_score = min(
                    result.confidence_score,
                    filter_result.confidence
                )
            
            # Aplicar sanitización si está disponible
            if filter_result.sanitized_content:
                result.sanitized_content = filter_result.sanitized_content
        
        return result

class ToxicityFilter(ContentFilter):
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.model = self._load_toxicity_model()
    
    async def process(self, content: str) -> FilterResult:
        # Usar modelo ML para detectar toxicidad
        toxicity_score = await self._analyze_toxicity(content)
        
        is_safe = toxicity_score < self.threshold
        issues = [] if is_safe else ["toxic_content"]
        
        return FilterResult(
            is_safe=is_safe,
            issues=issues,
            confidence=1.0 - toxicity_score,
            sanitized_content=content if is_safe else self._sanitize_toxic_content(content)
        )

class PromptInjectionFilter(ContentFilter):
    def __init__(self):
        self.injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"you\s+are\s+now\s+a",
            r"new\s+instructions:",
            r"system\s*:\s*",
            r"\/\*.*\*\/",  # SQL comment patterns
            r"<script.*?>.*?<\/script>",  # Script injection
        ]
    
    async def process(self, content: str) -> FilterResult:
        content_lower = content.lower()
        detected_patterns = []
        
        for pattern in self.injection_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                detected_patterns.append(pattern)
        
        is_safe = len(detected_patterns) == 0
        issues = ["prompt_injection"] if not is_safe else []
        
        return FilterResult(
            is_safe=is_safe,
            issues=issues,
            confidence=0.9,
            sanitized_content=content
        )
```

## 📈 Arquitectura de Escalabilidad

### Horizontal Scaling Strategy

```python
# app/scaling/load_balancer.py
class MessageLoadBalancer:
    def __init__(self):
        self.workers = {}
        self.health_checker = HealthChecker()
        self.load_metrics = LoadMetrics()
    
    async def route_message(self, message: ProcessMessageRequest) -> str:
        # Obtener workers saludables
        healthy_workers = await self._get_healthy_workers()
        
        if not healthy_workers:
            raise NoAvailableWorkersException()
        
        # Seleccionar worker basado en carga
        selected_worker = await self._select_optimal_worker(
            healthy_workers,
            message
        )
        
        return selected_worker.worker_id
    
    async def _select_optimal_worker(
        self,
        workers: List[Worker],
        message: ProcessMessageRequest
    ) -> Worker:
        # Estrategia: Least Response Time + Round Robin
        
        # Considerar specialización por provider LLM
        llm_specialized = [
            w for w in workers 
            if message.llm_provider in w.specialized_providers
        ]
        
        candidate_workers = llm_specialized if llm_specialized else workers
        
        # Seleccionar basado en métricas actuales
        best_worker = None
        best_score = float('inf')
        
        for worker in candidate_workers:
            metrics = await self.load_metrics.get_worker_metrics(worker.worker_id)
            
            # Score compuesto: latencia + queue size + CPU usage
            score = (
                metrics.avg_response_time * 0.4 +
                metrics.queue_size * 0.3 +
                metrics.cpu_usage * 0.3
            )
            
            if score < best_score:
                best_score = score
                best_worker = worker
        
        return best_worker

# Auto-scaling basado en métricas
class AutoScaler:
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        worker_manager: WorkerManager
    ):
        self.metrics = metrics_collector
        self.worker_manager = worker_manager
        self.scaling_rules = [
            ScalingRule(
                metric="queue_size",
                threshold=100,
                action="scale_up",
                cooldown=300
            ),
            ScalingRule(
                metric="avg_response_time",
                threshold=5000,  # 5 segundos
                action="scale_up",
                cooldown=300
            ),
            ScalingRule(
                metric="cpu_usage",
                threshold=80,
                action="scale_up",
                cooldown=300
            )
        ]
    
    async def evaluate_scaling(self):
        current_metrics = await self.metrics.get_current_metrics()
        
        for rule in self.scaling_rules:
            if await self._should_trigger_scaling(rule, current_metrics):
                await self._execute_scaling_action(rule)
    
    async def _execute_scaling_action(self, rule: ScalingRule):
        if rule.action == "scale_up":
            await self.worker_manager.add_worker()
            logger.info(f"Scaled up due to {rule.metric} > {rule.threshold}")
        elif rule.action == "scale_down":
            await self.worker_manager.remove_worker()
            logger.info(f"Scaled down due to {rule.metric} < {rule.threshold}")
```

## 🔧 Patrones de Configuración

### Configuration Management

```python
# app/core/config_manager.py
class ConfigurationManager:
    def __init__(self):
        self.config_sources = [
            EnvironmentConfigSource(),
            FileConfigSource("config.yaml"),
            RemoteConfigSource("consul://config-service"),
            DatabaseConfigSource()
        ]
        self.cache = {}
        self.watchers = {}
    
    async def get_config(self, key: str, default=None):
        # Check cache first
        if key in self.cache:
            return self.cache[key]
        
        # Try each source in order
        for source in self.config_sources:
            try:
                value = await source.get(key)
                if value is not None:
                    self.cache[key] = value
                    return value
            except Exception as e:
                logger.warning(f"Config source {source} failed: {e}")
        
        return default
    
    async def watch_config(self, key: str, callback):
        """Watch for configuration changes"""
        if key not in self.watchers:
            self.watchers[key] = []
        
        self.watchers[key].append(callback)
        
        # Start watching if first watcher
        if len(self.watchers[key]) == 1:
            asyncio.create_task(self._watch_key(key))
    
    async def _watch_key(self, key: str):
        last_value = await self.get_config(key)
        
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            current_value = await self.get_config(key)
            if current_value != last_value:
                # Notify all watchers
                for callback in self.watchers.get(key, []):
                    try:
                        await callback(key, current_value, last_value)
                    except Exception as e:
                        logger.error(f"Config watcher failed: {e}")
                
                last_value = current_value

# Feature flags management
class FeatureFlagManager:
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.flags_cache = {}
    
    async def is_enabled(
        self,
        flag_name: str,
        user_id: str = None,
        default: bool = False
    ) -> bool:
        flag_config = await self.config_manager.get_config(
            f"features.{flag_name}",
            {"enabled": default, "rollout_percentage": 0}
        )
        
        if not flag_config["enabled"]:
            return False
        
        # Check rollout percentage
        rollout_percentage = flag_config.get("rollout_percentage", 100)
        
        if rollout_percentage >= 100:
            return True
        
        if user_id:
            # Consistent hash-based rollout
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            user_percentage = user_hash % 100
            return user_percentage < rollout_percentage
        
        return False

# Usage in services
class MessageService:
    async def process_message(self, message: ProcessMessageRequest):
        # Check feature flag for new processing pipeline
        use_new_pipeline = await self.feature_flags.is_enabled(
            "new_message_pipeline",
            message.user_id
        )
        
        if use_new_pipeline:
            return await self._process_message_v2(message)
        else:
            return await self._process_message_v1(message)
```

Esta arquitectura proporciona una base sólida, escalable y mantenible para el Message Service, con patrones avanzados de diseño que aseguran alta disponibilidad, rendimiento óptimo y facilidad de evolución del sistema.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "create-message-documentation", "content": "Create comprehensive Message Service documentation", "status": "completed"}]