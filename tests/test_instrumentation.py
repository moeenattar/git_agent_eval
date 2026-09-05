from github_triage.instrumentation import configure_phoenix_from_env


def test_project_endpoint_overrides_conflicting_host_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_register(**kwargs):
        captured.update(kwargs)
        return "provider"

    monkeypatch.setenv("TRIAGE_ENABLE_PHOENIX", "true")
    monkeypatch.setenv(
        "TRIAGE_PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"
    )
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4317/v1/traces")
    monkeypatch.setattr("phoenix.otel.register", fake_register)

    result = configure_phoenix_from_env()

    assert result == "provider"
    assert captured == {
        "endpoint": "http://localhost:6006/v1/traces",
        "project_name": "github-triage",
        "protocol": "http/protobuf",
        "auto_instrument": True,
    }
