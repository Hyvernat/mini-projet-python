from api.metrics import get_system_metrics


def test_metrics_keys():
    metrics = get_system_metrics()
    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        assert key in metrics, f"Missing key: {key}"


def test_metrics_values_in_range():
    metrics = get_system_metrics()
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert 0 <= metrics["disk_percent"] <= 100
