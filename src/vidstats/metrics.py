from __future__ import annotations

# All metrics available from ffprobe's signalstats filter.
# Names correspond to the suffix after lavfi.signalstats.<n>.
ALL_METRICS: list[str] = [
    # Luminance (Y)
    "YMIN", "YLOW", "YAVG", "YHIGH", "YMAX",
    # Cb chrominance (U)
    "UMIN", "ULOW", "UAVG", "UHIGH", "UMAX",
    # Cr chrominance (V)
    "VMIN", "VLOW", "VAVG", "VHIGH", "VMAX",
    # Saturation
    "SATMIN", "SATLOW", "SATAVG", "SATHIGH", "SATMAX",
    # Hue
    "HUEMED", "HUEAVG",
    # Quality flags (percentages of pixels)
    "TOUT", "VREP", "BRNG",
]

# Maps ffprobe metric names to descriptive snake_case output column names.
COLUMN_NAMES: dict[str, str] = {
    "YMIN":    "luminance_min",
    "YLOW":    "luminance_p10",
    "YAVG":    "luminance_mean",
    "YHIGH":   "luminance_p90",
    "YMAX":    "luminance_max",
    "UMIN":    "chroma_u_min",
    "ULOW":    "chroma_u_p10",
    "UAVG":    "chroma_u_mean",
    "UHIGH":   "chroma_u_p90",
    "UMAX":    "chroma_u_max",
    "VMIN":    "chroma_v_min",
    "VLOW":    "chroma_v_p10",
    "VAVG":    "chroma_v_mean",
    "VHIGH":   "chroma_v_p90",
    "VMAX":    "chroma_v_max",
    "SATMIN":  "saturation_min",
    "SATLOW":  "saturation_p10",
    "SATAVG":  "saturation_mean",
    "SATHIGH": "saturation_p90",
    "SATMAX":  "saturation_max",
    "HUEMED":  "hue_median",
    "HUEAVG":  "hue_mean",
    "TOUT":    "temporal_outlier_pct",
    "VREP":    "vertical_repeat_pct",
    "BRNG":    "broadcast_range_pct",
}

METRIC_DESCRIPTIONS: dict[str, str] = {
    "YMIN":    "Minimum luminance value [0-255]",
    "YLOW":    "Luminance at 10th percentile [0-255]",
    "YAVG":    "Mean luminance value [0-255]",
    "YHIGH":   "Luminance at 90th percentile [0-255]",
    "YMAX":    "Maximum luminance value [0-255]",
    "UMIN":    "Minimum Cb chrominance (U) value [0-255]",
    "ULOW":    "Cb chrominance (U) at 10th percentile [0-255]",
    "UAVG":    "Mean Cb chrominance (U) value [0-255]",
    "UHIGH":   "Cb chrominance (U) at 90th percentile [0-255]",
    "UMAX":    "Maximum Cb chrominance (U) value [0-255]",
    "VMIN":    "Minimum Cr chrominance (V) value [0-255]",
    "VLOW":    "Cr chrominance (V) at 10th percentile [0-255]",
    "VAVG":    "Mean Cr chrominance (V) value [0-255]",
    "VHIGH":   "Cr chrominance (V) at 90th percentile [0-255]",
    "VMAX":    "Maximum Cr chrominance (V) value [0-255]",
    "SATMIN":  "Minimum saturation value [0-~181]",
    "SATLOW":  "Saturation at 10th percentile [0-~181]",
    "SATAVG":  "Mean saturation value [0-~181]",
    "SATHIGH": "Saturation at 90th percentile [0-~181]",
    "SATMAX":  "Maximum saturation value [0-~181]",
    "HUEMED":  "Median hue value [0-360]",
    "HUEAVG":  "Mean hue value [0-360]",
    "TOUT":    "Percentage of pixels that are temporal outliers [0-100]",
    "VREP":    "Percentage of pixels with vertical line repetition [0-100]",
    "BRNG":    "Percentage of pixels outside broadcast range [0-100]",
}


def validate_metrics(metrics: list[str]) -> list[str]:
    """Return list of invalid metric names, empty if all valid."""
    return [m for m in metrics if m not in ALL_METRICS]
