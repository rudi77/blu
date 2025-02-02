from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from opentelemetry.metrics import Instrument
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from openinference.instrumentation.openai import OpenAIInstrumentor
from phoenix.otel import register
from functools import wraps
import time
from backend.config import get_settings

settings = get_settings()

# Set up Phoenix tracer provider
tracer_provider = register(
    project_name="bluapp-llm",
    endpoint=settings.otel_exporter_otlp_endpoint
)

# Instrument OpenAI
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# Set up metrics with HTTP exporter
metric_exporter = OTLPMetricExporter(
    endpoint=settings.phoenix_collector_endpoint + "/v1/metrics"
)
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)

# Get tracer and meter
tracer = trace.get_tracer("openai.client")
meter = metrics.get_meter("openai.client")

# Create metrics
llm_request_duration = meter.create_histogram(
    name="llm.request.duration",
    description="Duration of LLM requests",
    unit="ms"
)

llm_request_tokens = meter.create_histogram(
    name="llm.request.tokens",
    description="Number of tokens in request/response",
    unit="tokens"
)

llm_request_count = meter.create_counter(
    name="llm.request.count",
    description="Number of LLM requests",
    unit="requests"
)

def trace_openai_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with tracer.start_as_current_span("llm.request") as span:
            start_time = time.time()
            
            try:
                # Execute the OpenAI request
                response = await func(*args, **kwargs)
                
                # Record metrics
                duration = (time.time() - start_time) * 1000  # Convert to ms
                llm_request_duration.record(duration)
                llm_request_count.add(1)
                
                # Add response tokens to metrics if available
                if hasattr(response, 'usage'):
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    llm_request_tokens.record(prompt_tokens, {"type": "prompt"})
                    llm_request_tokens.record(completion_tokens, {"type": "completion"})
                
                # Add span attributes
                span.set_attribute("llm.provider", "openai")
                span.set_attribute("llm.request.duration_ms", duration)
                if hasattr(response, 'model'):
                    span.set_attribute("llm.model", response.model)
                
                span.set_status(Status(StatusCode.OK))
                return response
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
                
    return wrapper 