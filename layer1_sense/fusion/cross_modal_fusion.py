import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple

class PRISMFusionModel(nn.Module):
    """
    Cross-modal attention fusion model.
    Takes embeddings from rPPG, Audio, Visual modalities and fuses them via
    multi-head attention to produce 12-disease probability outputs with
    MC-Dropout uncertainty estimation.
    """

    DISEASES = [
        "TB", "COVID", "Pneumonia", "Whooping_Cough",
        "Asthma", "COPD", "Jaundice", "Anemia",
        "Cyanosis", "Dengue", "Parkinsons", "Healthy",
    ]

    def __init__(self, latent_dim: int = 128, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.latent_dim = latent_dim
        self.num_diseases = len(self.DISEASES)

        # Per-modality encoders: project raw features → latent_dim
        self.rppg_encoder = nn.Sequential(
            nn.Linear(7, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, latent_dim), nn.ReLU(),
        )
        self.audio_encoder = nn.Sequential(
            nn.Linear(16, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, latent_dim), nn.ReLU(),
        )
        self.visual_encoder = nn.Sequential(
            nn.Linear(11, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, latent_dim), nn.ReLU(),
        )

        # Learned modality embeddings
        self.modality_embeddings = nn.Parameter(torch.randn(3, latent_dim))

        # Cross-modal attention
        self.attention = nn.MultiheadAttention(
            embed_dim=latent_dim, num_heads=num_heads,
            dropout=dropout, batch_first=True,
        )

        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(latent_dim, latent_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(latent_dim * 2, latent_dim),
        )

        # Layer norms
        self.ln1 = nn.LayerNorm(latent_dim)
        self.ln2 = nn.LayerNorm(latent_dim)

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(latent_dim, latent_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(latent_dim, self.num_diseases),
        )

    def forward(
        self,
        rppg_feat: torch.Tensor,
        audio_feat: torch.Tensor,
        visual_feat: torch.Tensor,
        modality_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            rppg_feat:  (B, 7)
            audio_feat: (B, 16)
            visual_feat: (B, 11)
            modality_mask: (B, 3) bool tensor, True = modality is MISSING
        Returns:
            logits: (B, 12)
        """
        B = rppg_feat.shape[0]

        # Encode each modality
        enc_rppg = self.rppg_encoder(rppg_feat)     # (B, D)
        enc_audio = self.audio_encoder(audio_feat)   # (B, D)
        enc_visual = self.visual_encoder(visual_feat) # (B, D)

        # Add modality embeddings
        enc_rppg = enc_rppg + self.modality_embeddings[0]
        enc_audio = enc_audio + self.modality_embeddings[1]
        enc_visual = enc_visual + self.modality_embeddings[2]

        # Stack → (B, 3, D)
        tokens = torch.stack([enc_rppg, enc_audio, enc_visual], dim=1)

        # Attention mask for missing modalities
        key_padding_mask = modality_mask if modality_mask is not None else None

        # Self-attention
        attn_out, attn_weights = self.attention(
            tokens, tokens, tokens,
            key_padding_mask=key_padding_mask,
        )
        tokens = self.ln1(tokens + attn_out)

        # FFN
        ffn_out = self.ffn(tokens)
        tokens = self.ln2(tokens + ffn_out)

        # Global pooling over modality tokens
        if key_padding_mask is not None:
            # Zero out missing modalities before pooling
            valid_mask = (~key_padding_mask).float().unsqueeze(-1)  # (B, 3, 1)
            tokens = tokens * valid_mask
            pooled = tokens.sum(dim=1) / valid_mask.sum(dim=1).clamp(min=1)
        else:
            pooled = tokens.mean(dim=1)  # (B, D)

        logits = self.classifier(pooled)  # (B, 12)
        return logits

    def predict_with_uncertainty(
        self, rppg_feat, audio_feat, visual_feat,
        modality_mask=None, n_passes: int = 20,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """MC-Dropout uncertainty estimation."""
        self.train()  # Enable dropout
        predictions = []
        with torch.no_grad():
            for _ in range(n_passes):
                logits = self.forward(rppg_feat, audio_feat, visual_feat, modality_mask)
                probs = torch.sigmoid(logits)
                predictions.append(probs.cpu().numpy())

        preds = np.stack(predictions, axis=0)  # (T, B, 12)
        mean_probs = preds.mean(axis=0)        # (B, 12)
        std_probs = preds.std(axis=0)          # (B, 12)
        return mean_probs, std_probs
