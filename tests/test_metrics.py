"""
Tests unitaires pour le module de métriques système.
"""
from api.metrics import get_system_metrics


def test_metrics_contains_required_keys():
    """get_system_metrics() doit retourner tous les champs obligatoires."""
    metrics = get_system_metrics()
    required = [
        "cpu_percent", "memory_percent", "disk_percent",
        "memory_total_gb", "memory_used_gb",
        "disk_total_gb", "disk_used_gb",
    ]
    for key in required:
        assert key in metrics, f"Champ manquant : {key}"


def test_metrics_percentages_in_range():
    """Les pourcentages doivent être entre 0 et 100."""
    metrics = get_system_metrics()
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert 0 <= metrics["disk_percent"] <= 100


def test_metrics_gb_values_positive():
    """Les valeurs GB doivent être positives."""
    metrics = get_system_metrics()
    assert metrics["memory_total_gb"] > 0
    assert metrics["disk_total_gb"] > 0
    assert metrics["memory_used_gb"] >= 0
    assert metrics["disk_used_gb"] >= 0
