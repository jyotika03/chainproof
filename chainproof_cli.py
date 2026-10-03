"""Three reproducible capabilities for CoCo CLI and judge review."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from engine import evaluate


def run(args=None):
    parser = argparse.ArgumentParser(description='ChainProof: inspect evidence and test shipment scenarios')
    parser.add_argument('capability', choices=['diagnose', 'simulate', 'audit'])
    parser.add_argument('--data', default=str(Path(__file__).parent / 'data/demo.json'))
    parser.add_argument('--shipment')
    parser.add_argument('--arrival')
    parser.add_argument('--output')
    options = parser.parse_args(args)
    data = json.loads(Path(options.data).read_text(encoding='utf-8-sig'))
    baseline = evaluate(data)
    result = {'capability': options.capability, 'synthetic': data.get('synthetic', False),
              'generated_at': datetime.now(timezone.utc).isoformat(),
              'source_sha256': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
              'baseline': baseline}
    if options.capability == 'simulate':
        if not options.shipment or not options.arrival:
            parser.error('simulate requires --shipment and --arrival')
        changed = evaluate(data, {options.shipment: options.arrival})
        result.update(scenario=changed, assumptions={options.shipment: options.arrival},
                      recovered_orders=sorted(set(baseline['exposed_orders'])-set(changed['exposed_orders'])),
                      newly_exposed_orders=sorted(set(changed['exposed_orders'])-set(baseline['exposed_orders'])),
                      exposure_change_inr=changed['exposed_value_inr']-baseline['exposed_value_inr'])
    elif options.capability == 'audit':
        orders = {o['id']:o for o in data['orders']}
        naive = sum(orders[e['order_id']]['value_inr'] for e in baseline['evidence'])
        result.update(naive_join_value_inr=naive,
                      overstatement_inr=naive-baseline['exposed_value_inr'],
                      explanation='Naive allocation-level sums repeat full order value. Governed exposure aggregates once per order.')
    output = json.dumps(result, indent=2)
    if options.output:
        Path(options.output).write_text(output, encoding='utf-8')
    print(output)
    return result


if __name__ == '__main__':
    run()
