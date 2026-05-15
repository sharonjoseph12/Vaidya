
import json
from pathlib import Path

path = Path("C:/Users/Sharon/OneDrive/Desktop/Vaidya/prism/backend/.prism_mock_db.json")
data = json.loads(path.read_text(encoding="utf-8"))

demo_id = "550e8400-e29b-41d4-a716-446655440000"
if demo_id not in data["patients"]:
    data["patients"][demo_id] = {
        "id": demo_id,
        "encrypted_demographics": "0" * 200, # Dummy hex
        "consent_given": True,
        "consent_timestamp": "2026-05-14T00:00:00Z",
        "consent_purpose": "diagnostic_screening",
        "device_info": None,
        "created_at": "2026-05-14T00:00:00Z"
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Added demo patient {demo_id}")
else:
    print(f"Demo patient {demo_id} already exists")
