"""Provjera PC konfiguracije: kompatibilnost i procjena potrošnje.

Napomena o TDP-u: kod procesora i grafičke TDP je (približno) potrošnja pod
opterećenjem. Kod CPU kulera TDP znači koliko toplote kuler može da odvede —
to NIJE potrošnja i ne ulazi u zbir, nego se poredi sa TDP-om procesora.
"""
import math
import re

# Redoslijed slotova u konfiguratoru: (tip komponente, naziv, ikonica, obavezno)
SLOTS = (
    ('CPU', 'Procesor', 'fa-microchip', True),
    ('Motherboard', 'Matična ploča', 'fa-chess-board', True),
    ('RAM', 'RAM memorija', 'fa-memory', True),
    ('GPU', 'Grafička karta', 'fa-display', False),
    ('Storage', 'Disk', 'fa-hard-drive', True),
    ('Power Supply', 'Napajanje', 'fa-plug', True),
    ('Case', 'Kućište', 'fa-server', True),
    ('CPU Cooler', 'CPU kuler', 'fa-fan', False),
)
SLOT_LABELS = {key: label for key, label, _, _ in SLOTS}

# Procjena potrošnje
CPU_PEAK_FACTOR = 1.35   # procesori pod punim opterećenjem troše više od nazivnog TDP-a (AMD PPT ≈ 1,35 × TDP)
OTHER_PARTS_W = 75       # ploča, RAM, diskovi, ventilatori, USB
PSU_HEADROOM = 1.3       # rezerva za skokove potrošnje i efikasnost napajanja
PSU_STEP = 50            # preporuka se zaokružuje naviše na 50 W


def attr(component, *names):
    """Vrijednost atributa po nazivu; nazivi se porede bez razmaka i velikih slova (npr. 'TDP (W)' = 'TDP(W)')."""
    wanted = {re.sub(r'\s+', '', n).lower() for n in names}
    for value in component.attribute_values:
        if re.sub(r'\s+', '', value.attribute.name).lower() in wanted:
            return (value.value or '').strip() or None
    return None


def number(value):
    if value is None:
        return None
    match = re.search(r'\d+(?:[.,]\d+)?', str(value))
    return float(match.group().replace(',', '.')) if match else None


def is_true(value):
    return str(value).strip().lower() in ('true', '1', 'da', 'yes')


def estimate_power(by_type):
    cpu_tdp = number(attr(by_type['CPU'], 'TDP (W)', 'TDP')) if 'CPU' in by_type else None
    gpu_tdp = number(attr(by_type['GPU'], 'TDP (W)', 'TDP', 'TBP')) if 'GPU' in by_type else None
    cpu_w = round((cpu_tdp or 0) * CPU_PEAK_FACTOR)
    gpu_w = round(gpu_tdp or 0)
    load = cpu_w + gpu_w + OTHER_PARTS_W
    recommended = int(math.ceil(load * PSU_HEADROOM / PSU_STEP) * PSU_STEP)
    psu = number(attr(by_type['Power Supply'], 'Snaga (W)', 'Snaga', 'Wattage')) if 'Power Supply' in by_type else None
    return {
        'cpu_tdp': cpu_tdp, 'cpu_w': cpu_w,
        'gpu_tdp': gpu_tdp, 'gpu_w': gpu_w,
        'other_w': OTHER_PARTS_W,
        'load': load,
        'recommended': recommended,
        'psu': int(psu) if psu else None,
        'cpu_unknown': 'CPU' in by_type and cpu_tdp is None,
        'gpu_unknown': 'GPU' in by_type and gpu_tdp is None,
    }


def analyze_build(components):
    """Vraća {'checks': [...], 'power': {...}, 'missing': [...], 'is_compatible': bool}.

    Svaka provjera ima status 'ok', 'info', 'warn' ili 'error'. Samo 'error' znači da dijelovi ne rade zajedno.
    """
    by_type = {c.component_type: c for c in components if c.component_type}
    checks = []

    def add(status, title, detail=''):
        checks.append({'status': status, 'title': title, 'detail': detail})

    cpu, mb, ram = by_type.get('CPU'), by_type.get('Motherboard'), by_type.get('RAM')
    cooler, psu = by_type.get('CPU Cooler'), by_type.get('Power Supply')
    cpu_socket = attr(cpu, 'socket') if cpu else None

    # Procesor i ploča
    if cpu and mb:
        mb_socket = attr(mb, 'socket')
        if cpu_socket and mb_socket:
            if cpu_socket.lower() == mb_socket.lower():
                add('ok', f'Procesor i ploča: isti socket ({cpu_socket})')
            else:
                add('error', 'Procesor ne odgovara ploči',
                    f'Procesor je za {cpu_socket}, a ploča ima {mb_socket}.')
        else:
            add('warn', 'Socket procesora ili ploče nije upisan', 'Provjerite ručno da li se slažu.')

    # RAM i ploča
    if ram and mb:
        ram_type, mb_ram = attr(ram, 'RAM'), attr(mb, 'RAM')
        if ram_type and mb_ram:
            if ram_type.lower() in mb_ram.lower():
                add('ok', f'RAM i ploča: {ram_type}')
            else:
                add('error', 'RAM ne odgovara ploči', f'Memorija je {ram_type}, a ploča podržava {mb_ram}.')
        else:
            add('warn', 'Tip RAM-a nije upisan', 'Provjerite da li ploča podržava DDR4 ili DDR5.')

    # Kuler i procesor
    if cooler and cpu:
        if cpu_socket:
            support = attr(cooler, cpu_socket)
            if support is None:
                add('warn', f'Nije upisano da li kuler podržava {cpu_socket}')
            elif is_true(support):
                add('ok', f'Kuler se montira na {cpu_socket}')
            else:
                add('error', 'Kuler ne odgovara procesoru', f'Kuler nema nosač za {cpu_socket}.')
        cooler_tdp = number(attr(cooler, 'TDP (W)', 'TDP'))
        cpu_tdp = number(attr(cpu, 'TDP (W)', 'TDP'))
        if cooler_tdp and cpu_tdp:
            if cooler_tdp >= cpu_tdp:
                add('ok', f'Kuler hladi do {int(cooler_tdp)} W, procesor ima {int(cpu_tdp)} W TDP')
            else:
                add('warn', 'Kuler je slab za ovaj procesor',
                    f'Kuler hladi do {int(cooler_tdp)} W, a procesor ima {int(cpu_tdp)} W TDP. '
                    'Pod punim opterećenjem procesor će se grijati i usporavati.')

    # Napajanje
    power = estimate_power(by_type)
    if psu:
        if not power['psu']:
            add('warn', 'Snaga napajanja nije upisana')
        elif power['psu'] < power['load']:
            add('error', 'Napajanje je preslabo',
                f"Procijenjena potrošnja je oko {power['load']} W, a napajanje ima {power['psu']} W.")
        elif power['psu'] < power['recommended']:
            add('warn', 'Napajanje je na granici',
                f"Radiće, ali preporučujemo bar {power['recommended']} W zbog skokova potrošnje.")
        else:
            add('ok', f"Napajanje {power['psu']} W je dovoljno",
                f"Procijenjena potrošnja oko {power['load']} W, preporuka {power['recommended']} W.")

    missing = [key for key, _, _, required in SLOTS if required and key not in by_type]
    if cpu and not by_type.get('GPU'):
        add('info', 'Bez grafičke karte', 'Slika ide preko procesora, pa mora imati integrisanu grafiku (npr. AMD sa oznakom G, Intel bez F).')

    return {
        'checks': checks,
        'power': power,
        'missing': missing,
        'missing_labels': [SLOT_LABELS[m] for m in missing],
        'is_compatible': not any(c['status'] == 'error' for c in checks),
    }


def compatibility_messages(components):
    """Stari oblik rezultata (is_compatible, poruke) za stranicu sačuvane konfiguracije."""
    if not components:
        return True, ['Nema izabranih komponenti']
    result = analyze_build(components)
    messages = [c['title'] + (f": {c['detail']}" if c['detail'] else '')
                for c in result['checks'] if c['status'] in ('warn', 'error')]
    if result['missing_labels']:
        messages.append('Nedostaje: ' + ', '.join(result['missing_labels']))
    if not messages:
        messages.append('Konfiguracija je kompatibilna.')
    return result['is_compatible'], messages
