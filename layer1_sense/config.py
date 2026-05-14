import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
from .exceptions import ConfigurationError

class PRISMSenseConfig:
    def __init__(self, config_path: str = "configs/sense_config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
        
        # Modality Configs
        self.rppg = self._config.get("rppg", {})
        self.audio = self._config.get("audio", {})
        self.visual = self._config.get("visual", {})
        self.fusion = self._config.get("fusion", {})
        
        # Validation
        self._validate()

    def _load_config(self) -> Dict[str, Any]:
        path = Path(self.config_path)
        if not path.exists():
            # Try absolute path relative to repo root if needed
            repo_root = Path(__file__).parent.parent
            path = repo_root / self.config_path
            
        if not path.exists():
            raise ConfigurationError(f"Config file not found at {path}")
            
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse config: {str(e)}")

    def _validate(self):
        required_keys = ["rppg", "audio", "visual", "fusion"]
        for key in required_keys:
            if key not in self._config:
                raise ConfigurationError(f"Missing required config section: {key}")

    @property
    def rppg_fps(self) -> int:
        return self.rppg.get("fps", 30)

    @property
    def audio_sample_rate(self) -> int:
        return self.audio.get("sample_rate", 16000)

    @property
    def fusion_latent_dim(self) -> int:
        return self.fusion.get("latent_dim", 128)
