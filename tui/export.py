import csv
import os

from .queries import raw_entries, summary_by_category, summary_by_app


def export_csv(output_path, db_path=None, days=7, mode="raw"):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if mode == "raw":
        rows = raw_entries(db_path, days)
        fields = ["id", "start_ts", "end_ts", "duration", "process",
                   "window_title", "category"]
    elif mode == "category":
        rows = summary_by_category(db_path, days)
        fields = ["category", "total_seconds", "sessions"]
    elif mode == "app":
        rows = summary_by_app(db_path, days)
        fields = ["process", "window_title", "category", "total_seconds",
                   "sessions"]
    else:
        raise ValueError(f"Unknown export mode: {mode}")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    return output_path
