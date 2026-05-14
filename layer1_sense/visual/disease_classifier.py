import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional

class PRISMVisualClassifier(nn.Module):
    """MobileNetV3-Large based multi-task classifier with 4 parallel heads."""

    TASK_HEADS = {
        "jaundice": 4,   # none / mild / moderate / severe
        "anemia": 2,     # negative / positive
        "cyanosis": 2,   # negative / positive
        "dengue": 2,     # negative / positive
    }

    def __init__(self, pretrained: bool = True):
        super().__init__()
        # Backbone: MobileNetV3-Large
        from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
        weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        backbone = mobilenet_v3_large(weights=weights)

        # Remove original classifier
        self.features = backbone.features
        self.avgpool = backbone.avgpool
        backbone_out = 960  # MobileNetV3-Large last channel count

        # Shared projection
        self.shared_fc = nn.Sequential(
            nn.Linear(backbone_out, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
        )

        # Task-specific heads
        self.heads = nn.ModuleDict()
        for task, num_classes in self.TASK_HEADS.items():
            self.heads[task] = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat = self.features(x)
        feat = self.avgpool(feat)
        feat = feat.flatten(1)
        shared = self.shared_fc(feat)
        return {task: head(shared) for task, head in self.heads.items()}

    def predict(self, frame_bgr: np.ndarray) -> Dict[str, float]:
        """Run inference on a single BGR frame, returns per-class probabilities."""
        import cv2
        img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))
        tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        # ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std
        tensor = tensor.unsqueeze(0)

        self.eval()
        with torch.no_grad():
            outputs = self.forward(tensor)

        results = {}
        for task, logits in outputs.items():
            probs = torch.softmax(logits, dim=-1).squeeze().numpy()
            if self.TASK_HEADS[task] == 2:
                results[task] = float(probs[1])  # positive class probability
            else:
                # For jaundice, return max severity probability
                results[f"{task}_none"] = float(probs[0])
                results[f"{task}_mild"] = float(probs[1])
                results[f"{task}_moderate"] = float(probs[2])
                results[f"{task}_severe"] = float(probs[3])
        return results
