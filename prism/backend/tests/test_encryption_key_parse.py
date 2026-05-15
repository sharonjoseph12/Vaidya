"""ENCRYPTION_KEY parsing (BOM, wrapping, canonical base64)."""

from backend.utils.encryption_key import canonical_encryption_key_b64, load_aes_key_bytes_from_b64


def test_user_reported_key_round_trip():
    k = "xzet64zr1s5l7hNznfeLZUhUEzPUnF5ra/+A2ui0bfg="
    raw = load_aes_key_bytes_from_b64(k)
    assert len(raw) == 32
    canon = canonical_encryption_key_b64(k)
    assert load_aes_key_bytes_from_b64(canon) == raw


def test_wrapped_and_bom_still_32_bytes():
    messy = "\ufeffxzet64zr1s5l7hNznfeLZUhUEzPUnF5ra/\n+  A2ui0bfg="
    assert len(load_aes_key_bytes_from_b64(messy)) == 32
