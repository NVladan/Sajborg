"""PC konfigurator: kompatibilnost i procjena potrošnje."""

import pytest

from extensions import db
from models import Category, CategoryAttribute, Product, ProductAttributeValue
from pc_build_check import analyze_build


@pytest.fixture
def make(app):
    """make('CPU', 'Ryzen', {'socket': 'AM5', 'TDP (W)': '105'}) -> Product sa atributima."""
    categories = {}

    def _make(component_type, name, attrs, price=100):
        if component_type not in categories:
            cat = Category(name=f'Kat {component_type}', slug=f'pb-{component_type.lower().replace(" ", "-")}',
                           component_type=component_type)
            db.session.add(cat)
            db.session.flush()
            categories[component_type] = (cat, {})
        cat, cat_attrs = categories[component_type]
        product = Product(name=name, slug=f'pb-{name.lower().replace(" ", "-")}', price=price, stock=1,
                          category_id=cat.id, component_type=component_type, is_publicly_visible=True)
        db.session.add(product)
        db.session.flush()
        for attr_name, value in attrs.items():
            if attr_name not in cat_attrs:
                a = CategoryAttribute(category_id=cat.id, name=attr_name)
                db.session.add(a)
                db.session.flush()
                cat_attrs[attr_name] = a
            db.session.add(ProductAttributeValue(product_id=product.id, attribute_id=cat_attrs[attr_name].id, value=value))
        db.session.commit()
        return product
    return _make


def by_title(result, text):
    return next(c for c in result['checks'] if text in c['title'])


def test_cooler_tdp_is_not_counted_as_power_draw(make):
    cpu = make('CPU', 'Ryzen 5 7600', {'socket': 'AM5', 'TDP (W)': '65'})
    cooler = make('CPU Cooler', 'Kuler 260', {'TDP (W)': '260', 'AM5': 'True'})
    power = analyze_build([cpu, cooler])['power']
    assert power['cpu_w'] == 88                       # 65 W x 1,35
    assert power['load'] == 88 + 75                   # kuler ne ulazi u potrošnju


def test_gpu_tdp_without_space_and_psu_snaga_are_read(make):
    gpu = make('GPU', 'RX 9070 XT', {'TDP(W)': '300'})
    psu = make('Power Supply', 'PSU 650', {'Snaga(W)': '650'})
    cpu = make('CPU', 'Ryzen 7 7700X', {'socket': 'AM5', 'TDP (W)': '105'})
    result = analyze_build([cpu, gpu, psu])
    assert result['power']['gpu_w'] == 300
    assert result['power']['psu'] == 650
    assert result['power']['load'] == 142 + 300 + 75   # 517 W
    assert result['power']['recommended'] == 700        # 517 x 1,3 = 672 -> 700
    assert by_title(result, 'granici')['status'] == 'warn'
    assert result['is_compatible'] is True


def test_too_weak_psu_is_an_error(make):
    gpu = make('GPU', 'RX 9070 XT', {'TDP(W)': '300'})
    psu = make('Power Supply', 'PSU 350', {'Snaga(W)': '350'})
    result = analyze_build([gpu, psu])
    assert by_title(result, 'preslabo')['status'] == 'error'
    assert result['is_compatible'] is False


def test_socket_ram_and_cooler_checks(make):
    cpu = make('CPU', 'i5 14400F', {'socket': 'LGA1700', 'TDP (W)': '148'})
    mb = make('Motherboard', 'B650', {'socket': 'AM5', 'RAM': 'DDR5'})
    ram = make('RAM', 'DDR4 16GB', {'RAM': 'DDR4'})
    cooler = make('CPU Cooler', 'Mali kuler', {'TDP (W)': '110', 'LGA1700': 'False'})
    result = analyze_build([cpu, mb, ram, cooler])
    assert by_title(result, 'Procesor ne odgovara ploči')['status'] == 'error'
    assert by_title(result, 'RAM ne odgovara ploči')['status'] == 'error'
    assert by_title(result, 'Kuler ne odgovara procesoru')['status'] == 'error'
    assert by_title(result, 'Kuler je slab')['status'] == 'warn'
    assert result['is_compatible'] is False


def test_compatible_build(make):
    parts = [
        make('CPU', 'Ryzen 5 7600X', {'socket': 'AM5', 'TDP (W)': '105'}),
        make('Motherboard', 'B650M', {'socket': 'AM5', 'RAM': 'DDR5'}),
        make('RAM', 'DDR5 32GB', {'RAM': 'DDR5'}),
        make('CPU Cooler', 'Peerless Assassin', {'TDP (W)': '260', 'AM5': 'True'}),
        make('GPU', 'RX 9060 XT', {'TDP(W)': '160'}),
        make('Power Supply', 'PSU 650', {'Snaga(W)': '650'}),
    ]
    result = analyze_build(parts)
    assert result['is_compatible'] is True
    assert all(c['status'] == 'ok' for c in result['checks'])
    assert set(result['missing']) == {'Storage', 'Case'}


def test_check_endpoint_returns_power(client, make):
    gpu = make('GPU', 'RX 9060 XT', {'TDP(W)': '160'})
    data = client.post('/pc-builder/check-compatibility', json={'components': [gpu.id]}).get_json()
    assert data['success'] and data['power']['gpu_w'] == 160


def test_builder_page_renders_slots(client, make):
    make('CPU', 'Ryzen 5 7600', {'socket': 'AM5', 'TDP (W)': '65'})
    html = client.get('/pc-builder/').get_data(as_text=True)
    assert 'Procesor' in html and 'Matična ploča' in html and 'Napajanje' in html
