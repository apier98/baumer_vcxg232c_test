from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys
from typing import Any

import numpy as np

from .config import InferenceConfig


class InferenceError(RuntimeError):
    """Raised when bundle-backed inference cannot be initialized or executed."""


class LiveInferenceOverlay:
    def __init__(self, config: InferenceConfig) -> None:
        self.config = config
        self.bundle_dir = config.resolved_bundle_dir()
        self._validate_bundle_dir()
        self._install_bundle_path()

        try:
            infer_module = import_module("rfdetr_training.infer")
        except Exception as exc:
            raise InferenceError(
                f"Failed to import the bundle runtime from {self.bundle_dir}: {exc}"
            ) from exc

        engine_class = getattr(infer_module, "InferenceEngine", None)
        if engine_class is None:
            raise InferenceError(
                f"The bundle at {self.bundle_dir} does not expose rfdetr_training.infer.InferenceEngine."
            )

        try:
            self.engine = engine_class(
                bundle_dir=self.bundle_dir,
                weights_path=None,
                device=config.device,
                score_thresh=config.score_threshold,
                mask_thresh=None,
                checkpoint_key=None,
                use_checkpoint_model=False,
                strict=False,
                backend=config.backend,
                topk=config.topk,
            )
        except Exception as exc:
            raise InferenceError(f"Failed to load the RF-DETR bundle: {exc}") from exc

        self.class_names = list(getattr(self.engine, "class_names", []) or [])
        self.post_cfg = getattr(self.engine, "post_cfg", {}) or {}
        self.backend = str(
            getattr(self.engine, "active_backend", None)
            or getattr(self.engine, "backend", None)
            or "unknown"
        )
        self.min_box_size = float(self.post_cfg.get("min_box_size_default", 1.0))
        self.nms_iou = float(self.post_cfg.get("nms_iou_threshold_default", 0.3))
        self.max_dets = int(self.post_cfg.get("max_dets_default", 50))

    def annotate_frame(self, frame_bgr: np.ndarray, *, cv2_module: Any) -> tuple[np.ndarray, int]:
        try:
            result = self.engine.infer(frame_bgr)
        except Exception as exc:
            raise InferenceError(f"Inference execution failed: {exc}") from exc

        if not result.ok or result.boxes is None or result.scores is None or result.labels is None:
            message = result.message if getattr(result, "message", "") else "unknown inference failure"
            raise InferenceError(message)

        boxes = [list(box) for box in result.boxes]
        scores = [float(score) for score in result.scores]
        labels = [int(label) for label in result.labels]

        keep = _filter_degenerate(boxes, scores, labels, min_box_size=self.min_box_size)
        boxes = [boxes[index] for index in keep]
        scores = [scores[index] for index in keep]
        labels = [labels[index] for index in keep]

        keep = _apply_nms(
            boxes,
            scores,
            labels,
            iou_thresh=self.nms_iou,
            max_dets=self.max_dets,
        )
        boxes = [boxes[index] for index in keep]
        scores = [scores[index] for index in keep]
        labels = [labels[index] for index in keep]

        annotated = frame_bgr.copy()
        height, width = annotated.shape[:2]
        for box, score, label in zip(boxes, scores, labels):
            x1, y1, x2, y2 = _clamp_box(box, width=width, height=height)
            if x2 <= x1 or y2 <= y1:
                continue
            cv2_module.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_text = self.class_names[label] if 0 <= label < len(self.class_names) else str(label)
            cv2_module.putText(
                annotated,
                f"{label_text}:{score:.2f}",
                (x1, max(20, y1 - 8)),
                cv2_module.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2_module.LINE_AA,
            )

        return annotated, len(boxes)

    def _install_bundle_path(self) -> None:
        bundle_path = str(self.bundle_dir)
        if bundle_path not in sys.path:
            sys.path.insert(0, bundle_path)

    def _validate_bundle_dir(self) -> None:
        if not self.bundle_dir.exists():
            raise InferenceError(
                f"Bundle directory does not exist: {self.bundle_dir}. "
                "Copy the exported bundle there or pass --inference-bundle-dir."
            )

        required_paths = [
            self.bundle_dir / "model_config.json",
            self.bundle_dir / "preprocess.json",
            self.bundle_dir / "postprocess.json",
            self.bundle_dir / "classes.json",
            self.bundle_dir / "rfdetr_training",
        ]
        missing = [path.name for path in required_paths if not path.exists()]
        if not (self.bundle_dir / "model.onnx").exists() and not (self.bundle_dir / "checkpoint.pth").exists():
            missing.append("model.onnx or checkpoint.pth")
        if missing:
            raise InferenceError(
                f"Bundle directory {self.bundle_dir} is missing: {', '.join(missing)}."
            )


def _clamp_box(box: list[float], *, width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = [float(value) for value in box]
    return (
        max(0, min(width - 1, int(round(x1)))),
        max(0, min(height - 1, int(round(y1)))),
        max(0, min(width - 1, int(round(x2)))),
        max(0, min(height - 1, int(round(y2)))),
    )


def _filter_degenerate(
    boxes: list[list[float]],
    scores: list[float],
    labels: list[int],
    *,
    min_box_size: float,
) -> list[int]:
    keep: list[int] = []
    min_size = float(min_box_size)
    for index, box in enumerate(boxes):
        x1, y1, x2, y2 = [float(value) for value in box]
        if (x2 - x1) < min_size or (y2 - y1) < min_size:
            continue
        if not np.isfinite([x1, y1, x2, y2, float(scores[index]), float(labels[index])]).all():
            continue
        keep.append(index)
    return keep


def _apply_nms(
    boxes: list[list[float]],
    scores: list[float],
    labels: list[int],
    *,
    iou_thresh: float,
    max_dets: int,
) -> list[int]:
    if not boxes:
        return []
    if iou_thresh <= 0.0 or iou_thresh >= 1.0:
        return list(range(min(len(boxes), max_dets if max_dets > 0 else len(boxes))))

    boxes_np = np.asarray(boxes, dtype=np.float32)
    scores_np = np.asarray(scores, dtype=np.float32)
    labels_np = np.asarray(labels, dtype=np.int64)

    keep_all: list[int] = []
    for class_id in np.unique(labels_np):
        class_indices = np.nonzero(labels_np == class_id)[0]
        if class_indices.size == 0:
            continue
        class_keep = _nms_indices_numpy(
            boxes_np[class_indices],
            scores_np[class_indices],
            iou_thresh=iou_thresh,
            max_keep=max_dets,
        )
        keep_all.extend(class_indices[np.asarray(class_keep, dtype=np.int64)].tolist())

    keep_all = sorted(keep_all, key=lambda index: float(scores[index]), reverse=True)
    if max_dets > 0:
        return keep_all[:max_dets]
    return keep_all


def _nms_indices_numpy(
    boxes: np.ndarray,
    scores: np.ndarray,
    *,
    iou_thresh: float,
    max_keep: int,
) -> list[int]:
    if boxes.size == 0:
        return []

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = np.clip(x2 - x1, 0.0, None) * np.clip(y2 - y1, 0.0, None)
    order = np.argsort(-scores)
    keep: list[int] = []
    limit = int(max_keep) if int(max_keep) > 0 else int(order.shape[0])

    while order.size > 0 and len(keep) < limit:
        current = int(order[0])
        keep.append(current)
        if order.size == 1:
            break
        rest = order[1:]
        xx1 = np.maximum(x1[current], x1[rest])
        yy1 = np.maximum(y1[current], y1[rest])
        xx2 = np.minimum(x2[current], x2[rest])
        yy2 = np.minimum(y2[current], y2[rest])
        inter = np.clip(xx2 - xx1, 0.0, None) * np.clip(yy2 - yy1, 0.0, None)
        union = np.clip(areas[current] + areas[rest] - inter, 1e-6, None)
        iou = inter / union
        order = rest[iou < float(iou_thresh)]

    return keep
