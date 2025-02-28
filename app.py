from fastapi import FastAPI
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
import logging
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
import os
from logging.handlers import RotatingFileHandler
from fastapi.responses import StreamingResponse
import asyncio
import datetime
import random
import uvicorn

app = FastAPI()

# Configure OpenTelemetry Tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Add OpenTelemetry ASGI middleware
app.add_middleware(OpenTelemetryMiddleware)

# Instrument logging to include trace context
LoggingInstrumentor().instrument(set_logging_format=True)

# Configure Logging with OpenTelemetry
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    logger.info("Processing request to root endpoint")
    return {"message": "Hello, OpenTelemetry!"}

@app.get("/error")
async def error():
    logger.error("This is an example error log")
    return {"message": "Error logged"}

LOG_LEVELS = ["INFO", "WARNING", "ERROR", "DEBUG"]
MESSAGES = [
    "User logged in",
    "Database connection established",
    "Payment processed successfully",
    "API request timeout",
    "New order placed",
    "Cache refreshed",
    "User authentication failed",
]




async def generate_logs():
    yield f"{datetime.datetime.utcnow().isoformat()} [INFO] - Log streaming started\n".encode("utf-8")
    
    while True:
        log = f"{datetime.datetime.utcnow().isoformat()} [{random.choice(LOG_LEVELS)}] - {random.choice(MESSAGES)}\n"
        yield log.encode("utf-8")
        logger.info(log.strip())
        await asyncio.sleep(1)  



@app.get("/logs")
async def stream_logs():
    return StreamingResponse(generate_logs(), media_type="text/plain", status_code=200)




if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI app with OpenTelemetry logging!")
    uvicorn.run(app, host="0.0.0.0", port=8000)