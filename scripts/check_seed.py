import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('data/seed_piezas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total piezas en seed: {len(data)}')

from collections import Counter
cnt = Counter(p.get('estatus_auditoria') for p in data)
print('Distribucion estatus_auditoria:', dict(cnt))

print('\nPrimeras 5 piezas - archivo_step:')
for p in data[:5]:
    print(f"  [{p.get('consecutivo_ing')}] archivo_step = {p.get('archivo_step')}")
