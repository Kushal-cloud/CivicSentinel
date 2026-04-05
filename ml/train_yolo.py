"""
YOLO training helper for CivicSentinel.

Expected dataset:
- YOLO format dataset with a dataset YAML describing:
  - train/valid image paths
  - `names:` mapping from class indices to class names

Example call:
  python ml/train_yolo.py --data data/urban_hazards.yaml --weights yolov8n.pt --imgsz 640 --epochs 50
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to YOLO dataset YAML")
    parser.add_argument("--weights", default="yolov8n.pt", help="Initial weights")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    parser.add_argument("--epochs", type=int, default=30, help="Epochs")
    parser.add_argument("--project", default="runs/yolo", help="Ultralytics project dir")
    parser.add_argument("--name", default="civicsentinel", help="Run name")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO  # type: ignore
    except Exception as e:
        raise SystemExit("Missing ultralytics. Install backend/requirements-ml.txt") from e

    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(f"Dataset YAML not found: {data_path}")

    model = YOLO(args.weights)
    model.train(
        data=str(data_path),
        imgsz=args.imgsz,
        epochs=args.epochs,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()

