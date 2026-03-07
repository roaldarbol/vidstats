# Tests for metrics.py
# - ALL_METRICS is a non-empty list of strings
# - All expected channel groups are present
# - METRIC_DESCRIPTIONS covers every metric
# - COLUMN_NAMES covers every metric
# - COLUMN_NAMES values are unique (no two metrics share an output column name)
# - COLUMN_NAMES values are snake_case (lowercase, underscores only)
# - validate_metrics returns empty list for valid metrics
# - validate_metrics returns offending names for invalid metrics

import re

from vidstats.metrics import ALL_METRICS, COLUMN_NAMES, METRIC_DESCRIPTIONS, validate_metrics


def test_all_metrics_nonempty():
    assert len(ALL_METRICS) > 0


def test_all_metrics_are_strings():
    assert all(isinstance(m, str) for m in ALL_METRICS)


def test_expected_metrics_present():
    expected = {"YAVG", "UAVG", "VAVG", "SATAVG", "HUEMED", "TOUT", "VREP", "BRNG"}
    assert expected.issubset(set(ALL_METRICS))


def test_descriptions_cover_all_metrics():
    missing = [m for m in ALL_METRICS if m not in METRIC_DESCRIPTIONS]
    assert missing == [], f"Metrics missing descriptions: {missing}"


def test_column_names_cover_all_metrics():
    missing = [m for m in ALL_METRICS if m not in COLUMN_NAMES]
    assert missing == [], f"Metrics missing column names: {missing}"


def test_column_names_are_unique():
    values = list(COLUMN_NAMES.values())
    assert len(values) == len(set(values)), "Duplicate output column names found"


def test_column_names_are_snake_case():
    pattern = re.compile(r"^[a-z][a-z0-9_]*$")
    bad = [v for v in COLUMN_NAMES.values() if not pattern.match(v)]
    assert bad == [], f"Non-snake_case column names: {bad}"


def test_known_column_name_mappings():
    assert COLUMN_NAMES["YAVG"] == "luminance_mean"
    assert COLUMN_NAMES["SATAVG"] == "saturation_mean"
    assert COLUMN_NAMES["HUEMED"] == "hue_median"
    assert COLUMN_NAMES["TOUT"] == "temporal_outlier_pct"


def test_validate_metrics_all_valid():
    assert validate_metrics(ALL_METRICS) == []


def test_validate_metrics_subset_valid():
    assert validate_metrics(["YAVG", "SATAVG", "HUEMED"]) == []


def test_validate_metrics_invalid():
    invalid = validate_metrics(["YAVG", "NOTAMETRIC", "ALSOFAKE"])
    assert "NOTAMETRIC" in invalid
    assert "ALSOFAKE" in invalid
    assert "YAVG" not in invalid


def test_validate_metrics_empty():
    assert validate_metrics([]) == []
