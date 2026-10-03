from pathlib import Path
import json
from engine import evaluate

root = Path(__file__).resolve().parent
source = json.loads((root / 'data/demo.json').read_text())
result = {'baseline': evaluate(source), 'scenario_earlier_S101': evaluate(source, {'S-101':'2026-10-06'})}
(root / 'evidence.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
