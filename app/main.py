# --- Imports ---
from fastapi import FastAPI, Request, HTTPException
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
import structlog
import time
import random
import asyncio
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# --- Structured Logging Setup ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# --- FastAPI App ---
app = FastAPI(title="FastAPI Monitoring Service", version="1.0.0")

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

# --- OpenTelemetry Tracing ---
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

try:
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=14268,
    )
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    logger.info("Jaeger tracing configured successfully")
except Exception as e:
    logger.warning("Failed to configure Jaeger", error=str(e))

# --- Instrumentation ---
FastAPIInstrumentor.instrument_app(app)
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
LoggingInstrumentor().instrument(set_logging_format=True)

# --- Endpoints ---


@app.get("/")
async def root():
    with tracer.start_as_current_span("root_endpoint") as span:
        start_time = time.time()
        logger.info("Root endpoint accessed", endpoint="/", method="GET")
        # Simulate some processing time (async)
        processing_time = random.uniform(0.1, 0.5)
        await asyncio.sleep(processing_time)
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method="GET", endpoint="/", status_code="200").inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/").observe(duration)
        span.set_attribute("processing_time", processing_time)
        span.set_attribute("endpoint", "/")
        return {
            "message": "Hello from monitored service!",
            "processing_time": processing_time,
            "endpoint": "/",
        }


@app.get("/slow")
async def slow_endpoint():
    with tracer.start_as_current_span("slow_endpoint") as span:
        start_time = time.time()
        logger.info("Slow endpoint accessed", endpoint="/slow", method="GET")
        # Simulate slow processing (async)
        processing_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(processing_time)
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method="GET", endpoint="/slow", status_code="200").inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/slow").observe(duration)
        span.set_attribute("processing_time", processing_time)
        span.set_attribute("endpoint", "/slow")
        return {
            "message": "This was a slow operation",
            "processing_time": processing_time,
            "endpoint": "/slow",
        }


@app.get("/error")
async def error_endpoint():
    with tracer.start_as_current_span("error_endpoint") as span:
        start_time = time.time()
        will_error = random.random() < 0.7  # 70% chance of error
        if will_error:
            logger.error(
                "Error endpoint accessed - simulating error",
                endpoint="/error",
                method="GET",
                will_error=True,
            )
            REQUEST_COUNT.labels(
                method="GET", endpoint="/error", status_code="500"
            ).inc()
            REQUEST_DURATION.labels(method="GET", endpoint="/error").observe(
                time.time() - start_time
            )
            span.set_attribute("error", True)
            span.set_attribute("endpoint", "/error")
            raise HTTPException(status_code=500, detail="Simulated server error")
        else:
            logger.info(
                "Error endpoint accessed - no error this time",
                endpoint="/error",
                method="GET",
                will_error=False,
            )
            REQUEST_COUNT.labels(
                method="GET", endpoint="/error", status_code="200"
            ).inc()
            REQUEST_DURATION.labels(method="GET", endpoint="/error").observe(
                time.time() - start_time
            )
            span.set_attribute("error", False)
            span.set_attribute("endpoint", "/error")
            return {"message": "No error this time!", "endpoint": "/error"}


@app.get("/health")
async def health_check():
    with tracer.start_as_current_span("health_check") as span:
        start_time = time.time()
        logger.info("Health check performed", endpoint="/health", method="GET")
        REQUEST_COUNT.labels(method="GET", endpoint="/health", status_code="200").inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/health").observe(
            time.time() - start_time
        )
        span.set_attribute("endpoint", "/health")
        return {"status": "healthy", "timestamp": time.time(), "endpoint": "/health"}


# Additional endpoint for more interesting metrics
@app.get("/cpu-intensive")
async def cpu_intensive():
    with tracer.start_as_current_span("cpu_intensive") as span:
        start_time = time.time()
        logger.info(
            "CPU intensive endpoint accessed", endpoint="/cpu-intensive", method="GET"
        )
        # Simulate CPU-intensive work
        iterations = random.randint(100000, 500000)
        result = sum(i * i for i in range(iterations))
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method="GET", endpoint="/cpu-intensive", status_code="200"
        ).inc()
        REQUEST_DURATION.labels(method="GET", endpoint="/cpu-intensive").observe(
            duration
        )
        span.set_attribute("iterations", iterations)
        span.set_attribute("duration", duration)
        span.set_attribute("endpoint", "/cpu-intensive")
        return {
            "message": "CPU intensive operation completed",
            "iterations": iterations,
            "result": result,
            "duration": duration,
            "endpoint": "/cpu-intensive",
        }
