"""Write KRATOS-compatible health bridge"""
import json
from pathlib import Path

state = Path.home() / '.claude' / 'state'
data = json.loads((state / 'omnis_health.json').read_text())

kratos = {
    'status': data['overall_status'],
    'score': data['overall_score'],
    'timestamp': data['timestamp'],
    'components': {
        name: {'status': c['status'], 'message': c['message']}
        for name, c in data['components'].items()
    }
}

target = state / 'kratos_health.json'
target.write_text(json.dumps(kratos, indent=2))
print(f"KRATOS bridge written: {target}")
print(f"Status: {kratos['status']} | Score: {kratos['score']}")
print(f"Components: {len(kratos['components'])}")
for name, c in kratos['components'].items():
    print(f"  {name}: {c['status']}")
