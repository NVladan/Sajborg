from app import create_app, db
from models import LagerCategory
# ====================================================================
# OVDJE DEFINIŠITE ŽELJENI REDOSLIJED TABOVA
# Samo promijenite redoslijed naziva kategorija u listi ispod.
# Kategorije koje nisu na listi će biti dodane na kraj.
# ====================================================================
DESIRED_ORDER = [
    "CPU",
    "COOLER",
    "MATICNE PLOCE",
    "RAM",
    "SSD",
    "GPU",
    "NAPOJNE JEDINICE",
    "KUCISTA",
    "VENTILATORI",
    "MONITORI",
    "TASTATURE",
    "MIŠEVI",
    "PODLOGE ZA MIŠEVE",
    "SLUSALICE",
    "ZVUČNICI",
    "TERMALNA PASTA",
    "KONFIGURACIJE",
    "POLOVNE KOMPONENTE",
    "POLOVNI KOMPJUTERI",
    "POLOVNI MONITORI",
    "POLOVNI LAPTOPOVI",
    "RAZNO"
]


def set_sort_order():
    """
    Također postavlja redoslijed za sve podkategorije na osnovu abecede.
    """
    print("Pokretanje skripte za ažuriranje redoslijeda kategorija...")

    # Ažuriranje glavnih kategorija
    for index, category_name in enumerate(DESIRED_ORDER):
        # Množimo sa 10 da ostavimo prostora za buduće unose
        sort_value = (index + 1) * 10
        category = LagerCategory.query.filter_by(name=category_name, parent_id=None).first()

        if category:
            category.sort_order = sort_value
            print(f"  [GLAVNA] Postavljam '{category.name}' na redoslijed: {sort_value}")
        else:
            print(f"  [UPOZORENJE] Glavna kategorija '{category_name}' nije pronađena u bazi.")

    # Postavljanje visokog broja za kategorije koje nisu na listi
    other_categories = LagerCategory.query.filter(
        LagerCategory.name.notin_(DESIRED_ORDER),
        LagerCategory.parent_id.is_(None)
    ).all()

    last_order_value = (len(DESIRED_ORDER) + 1) * 10
    for category in other_categories:
        category.sort_order = last_order_value
        print(f"  [GLAVNA] Postavljam nesortiranu kategoriju '{category.name}' na kraj: {last_order_value}")
        last_order_value += 10

    # Ažuriranje svih podkategorija abecednim redom unutar roditelja
    all_subcategories = LagerCategory.query.filter(LagerCategory.parent_id.isnot(None)).order_by(
        LagerCategory.name).all()

    # Grupišemo podkategorije po roditelju da bi se pravilno numerisale
    subcat_groups = {}
    for subcat in all_subcategories:
        if subcat.parent_id not in subcat_groups:
            subcat_groups[subcat.parent_id] = []
        subcat_groups[subcat.parent_id].append(subcat)

    for parent_id, subcats in subcat_groups.items():
        for index, subcat in enumerate(subcats):
            sort_value = (index + 1) * 10
            subcat.sort_order = sort_value
            print(f"    [POD] Postavljam '{subcat.name}' na redoslijed: {sort_value}")

    try:
        db.session.commit()
        print("\nUspješno sačuvane izmjene u bazi podataka!")
    except Exception as e:
        db.session.rollback()
        print(f"\nDošlo je do greške: {e}")
        print("Promjene su vraćene (rollback).")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        set_sort_order()