from unittest.mock import MagicMock, patch

import pytest

from tickets.otel import configure_otel


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr(
        "tickets.settings.ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans"
    )
    monkeypatch.setattr("tickets.settings.LOCAL_NODE_IPV_4", "127.0.0.1")


@patch("tickets.otel.LoggingInstrumentor")
@patch("tickets.otel.RequestsInstrumentor")
@patch("tickets.otel.DjangoInstrumentor")
@patch("tickets.otel.BatchSpanProcessor")
@patch("tickets.otel.ZipkinExporter")
@patch("tickets.otel.trace.set_tracer_provider")
@patch("tickets.otel.TracerProvider")
@patch("tickets.otel.Resource")
def test_configure_otel(
    mock_resource,
    mock_tracer_provider_class,
    mock_set_tracer_provider,
    mock_zipkin_exporter_class,
    mock_batch_span_processor_class,
    mock_django_instrumentor_class,
    mock_requests_instrumentor_class,
    mock_logging_instrumentor_class,
    monkeypatch,
):
    mock_resource_instance = MagicMock()
    mock_resource.create.return_value = mock_resource_instance

    mock_tracer_provider_instance = MagicMock()
    mock_tracer_provider_class.return_value = mock_tracer_provider_instance

    mock_zipkin_exporter_instance = MagicMock()
    mock_zipkin_exporter_class.return_value = mock_zipkin_exporter_instance

    mock_batch_span_processor_instance = MagicMock()
    mock_batch_span_processor_class.return_value = mock_batch_span_processor_instance

    mock_django_instrumentor = MagicMock()
    mock_django_instrumentor_class.return_value = mock_django_instrumentor

    mock_requests_instrumentor = MagicMock()
    mock_requests_instrumentor_class.return_value = mock_requests_instrumentor

    mock_logging_instrumentor = MagicMock()
    mock_logging_instrumentor_class.return_value = mock_logging_instrumentor

    configure_otel()

    mock_resource.create.assert_called_once_with(
        {"service.name": "tickets-service", "service.version": "1.0.0"}
    )

    mock_tracer_provider_class.assert_called_once_with(resource=mock_resource_instance)

    mock_set_tracer_provider.assert_called_once_with(mock_tracer_provider_instance)

    assert mock_zipkin_exporter_class.call_count == 1
    called_args, called_kwargs = mock_zipkin_exporter_class.call_args

    endpoint = called_kwargs.get("endpoint") or (
        called_args[0] if called_args else None
    )
    local_ip = called_kwargs.get("local_node_ipv4") or (
        called_args[1] if len(called_args) > 1 else None
    )

    assert local_ip == "127.0.0.1"
    assert endpoint is not None
    assert "9411" in endpoint
    assert "api/v2/spans" in endpoint
    assert endpoint.startswith("http")

    mock_batch_span_processor_class.assert_called_once_with(
        mock_zipkin_exporter_instance
    )

    mock_tracer_provider_instance.add_span_processor.assert_called_once_with(
        mock_batch_span_processor_instance
    )

    mock_django_instrumentor.instrument.assert_called_once()
    mock_requests_instrumentor.instrument.assert_called_once()
    mock_logging_instrumentor.instrument.assert_called_once_with(
        set_logging_format=True
    )
