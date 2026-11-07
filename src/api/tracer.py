from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from sqlalchemy.engine import Engine


def configure_tracer(
    app: FastAPI,
    jaeger_host: str,
    jaeger_port: int,
    jaeger_insecure: bool,
    sqlalchemy_engine: Engine,
) -> None:
    sampler = ParentBased(root=TraceIdRatioBased(0.05))
    resource = Resource.create({"service.name": "auth-service"})

    trace.set_tracer_provider(TracerProvider(resource=resource, sampler=sampler))
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=f"{jaeger_host}:{jaeger_port}",
                insecure=jaeger_insecure,
            )
        )
    )
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)
    FastAPIInstrumentor.instrument_app(app)
