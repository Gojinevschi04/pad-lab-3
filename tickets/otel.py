from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_otel() -> None:
    resource = Resource.create(
        {
            "service.name": "tickets-service",
            "service.version": "1.0.0",
        },
    )

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    zipkin_exporter = ZipkinExporter(
        endpoint=settings.ZIPKIN_ENDPOINT,
        local_node_ipv4=settings.LOCAL_NODE_IPV_4,
    )

    span_processor = BatchSpanProcessor(zipkin_exporter)
    tracer_provider.add_span_processor(span_processor)

    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=True)
