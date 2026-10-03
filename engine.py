"""Deterministic exposure calculations. Synthetic MVP; no AI claims."""
from datetime import date


def evaluate(data, arrival_overrides=None):
    """Return unique-order exposure and its shipment allocation evidence.

    Arrival overrides are hypothetical ISO dates. Dates are calendar dates;
    arrival on the material-needed date is considered on time.
    """
    overrides = arrival_overrides or {}
    shipments = {s['id']: s for s in data['shipments']}
    orders = {o['id']: o for o in data['orders']}
    if len(shipments) != len(data['shipments']) or len(orders) != len(data['orders']):
        raise ValueError('Duplicate entity identifiers')
    if set(overrides) - set(shipments):
        raise ValueError('Scenario references an unknown shipment')
    evidence, affected = [], set()
    seen_allocations = set()
    for allocation in data['allocations']:
        key = (allocation['shipment_id'], allocation['order_id'])
        if key in seen_allocations:
            raise ValueError('Duplicate allocation')
        seen_allocations.add(key)
        if key[0] not in shipments or key[1] not in orders:
            raise ValueError('Allocation references an unknown entity')
        shipment, order = shipments[key[0]], orders[key[1]]
        arrival = overrides.get(shipment['id'], shipment['arrival'])
        delay = max(0, (date.fromisoformat(arrival) - date.fromisoformat(order['needed'])).days)
        if delay:
            affected.add(order['id'])
            evidence.append({
                'shipment_id': shipment['id'], 'order_id': order['id'],
                'supplier': shipment['supplier'], 'part': shipment['part'],
                'plant': shipment['plant'], 'customer': order['customer'],
                'arrival': arrival, 'needed': order['needed'], 'late_days': delay,
            })
    for order in orders.values():
        if not isinstance(order['value_inr'], int) or order['value_inr'] < 0:
            raise ValueError('Order value must be a nonnegative whole number of INR')
    return {
        'exposed_orders': sorted(affected),
        'exposed_value_inr': sum(orders[k]['value_inr'] for k in affected),
        'total_orders': len(orders), 'evidence': evidence,
        'scenario': bool(overrides),
        'definition': 'Full value of unique orders with one or more late allocated shipments. Exposure, not predicted loss.',
    }
