import re
import decimal
from app import create_app, db
from models import LagerCategory, LagerProduct

# ====================================================================
# SVE KATEGORIJE (TABOVI) KOJE TREBA DA POSTOJE NA LAGERU
# Ako želite novi prazan tab, samo dodajte njegov naziv ovdje.
# ====================================================================
ALL_CATEGORIES = [
    "CPU", "COOLER", "MATICNE PLOCE", "RAM", "SSD", "GPU",
    "NAPOJNE JEDINICE", "KUCISTA", "VENTILATORI", "MONITORI",
    "TASTATURE", "MIŠEVI", "PODLOGE ZA MIŠEVE", "SLUSALICE", "ZVUČNICI",
    "TERMALNA PASTA", "KONFIGURACIJE", "RAZNO",
    "POLOVNI LAPTOPOVI", "POLOVNE KOMPONENTE", "POLOVNI MONITORI"  # Dodate sve kategorije
]

# ====================================================================
# SVI PODACI SA LAGERA SU SADA OVDE, AŽURIRANI PREMA EXCEL FAJLU
# ====================================================================
lager_data = {
    "CPU": {
        "AMD": [
            ["AMD Ryzen 5 3600 3.60GHz AM4 BOX", "2", "99.0", "", ""],
            ["AMD Ryzen 5 5600 3.50GHz AM4 BOX", "0", "190.0", "", ""],
            ["AMD Ryzen 7 5700X 3.40GHz AM4 BOX", "0", "258.0", "", ""],
            ["AMD Ryzen 5 7500F 3.70GHz AM5 OEM", "2", "323.0", "", "NE DOLAZI KUTIJA I COOLER"],
        ],
        "INTEL": [
            ["INTEL Core i5-12400F 2.50GHz LGA-1700 BOX", "1", "199.0", "", ""],
        ]
    },
    "COOLER": {
        "CPU HLADNJACI": [
            ["ID-COOLING SE-214-XT PLUS", "1", "45.0", "", ""],
            ["ID-COOLING DK-03 RAINBOW", "1", "21.0", "", ""],
            ["ENDORFY Spartan 5 ARGB", "1", "37.0", "", ""],
            ["ENDORFY Spartan 5 MAX ARGB", "1", "49.0", "", ""],
        ],
        "M.2 HLADNJACI": [
            ["JONSBO M.2-3 M.2 SSD heatsink - gray", "2", "13.0", "", ""],
            ["HIKVISION Hiksemi MH2 M.2 Cooler", "1", "11.0", "", ""],
        ]
    },
    "MATICNE PLOCE": {
        "AMD": [
            ["GIGABYTE A520M K V2", "1", "94.0", "", ""],
            ["GIGABYTE A520M DS3H V2", "0", "110.0", "", ""],
            ["ASUS TUF GAMING A520M-PLUS II", "1", "138.0", "", ""],
            ["MAXSUN Challenger B650M", "1", "156.0", "", ""],
            ["MAXSUN Challenger A620A 2.5G", "1", "145.0", "", ""],
        ],
        "INTEL": [
            ["GIGABYTE H610M S2H V2 DDR5", "1", "152.0", "", ""],
        ]
    },
    "RAM": {
        "DDR5": [
            ["KINGSTON FURY 16GB Beast DDR5 5600MHz CL36 KIT KF556C36BBEK2-16", "1", "117.0", "", ""],
            ["KINGSTON FURY 16GB Beast DDR5 5600MHz CL40 KIT KF556C40BBK2-16", "1", "125.0", "", ""],
        ],
        "DDR4": [
            ["TEAM GROUP 16GB T-Force Vulcan Z DDR4 3600MHz CL18 KIT", "0", "75.0", "", ""],
            ["APACER 16GB Nox RGB DDR4 3600MHz CL16 KIT", "1", "82.0", "", ""],
            ["G.SKILL 16GB Ripjaws V DDR4 3600MHz CL18 KIT F4-3600C18D-16GVK", "1", "100.0", "", ""],
            ["CRUCIAL 8GB Notebook DDR4 3200MHz CL22 CT8G4SFRA32A", "2", "34.0", "", ""],
            ["CRUCIAL 16GB Notebook DDR4 3200MHz CL22 CT16G4SFRA32A", "1", "61.0", "", ""],
        ]
    },
    "SSD": {
        "M.2": [
            ["KINGSTON 1TB NV3 M.2 PCIe M.2 2280 SNV3S/1000G", "1", "103.0", "", ""],
            ["KINGSTON 2TB NV3 M.2 PCIe M.2 2280 SNV3S/2000G", "1", "207.0", "", ""],
            ["KINGSTON 4TB NV3 M.2 PCIe M.2 2280 SNV3S/4000G", "1", "461.0", "", ""],
            ["DAHUA 512GB C900 M.2 PCIe M.2 2280 DHI-SSD-C900N512G", "1", "65.0", "", ""],
        ],
        "SATA": [
            ["TEAM GROUP 256GB CX2 SATA 3 2.5", "1", "35.0", "", ""],
            ["TEAM GROUP 512GB CX2 SATA 3 2.5", "1", "60.0", "", ""],
            ["TEAM GROUP 1TB CX2 SATA 3 2.5", "1", "107.0", "", ""],
            ["TEAM GROUP 512GB Vulcan Z SATA 3 2.5", "1", "56.0", "", ""],
        ]
    },
    "GPU": {
        "AMD": [
            ["GIGABYTE GV-R9070XTGAMING OC-16GD Radeon RX 9070 XT 16GB GDDR6 GAMING OC", "1", "1517.0", "", ""],
            ["PULSE AMD Radeon™ RX 6600 8GB (POLOVNA BEZ KUTIJE)", "1", "239.0", "", "POLOVNA BEZ KUTIJE"],
        ],
        "NVIDIA": [],
    },
    "NAPOJNE JEDINICE": {
        "NAPOJNE JEDINICE": [
            ['EZ COOL 500W', '4', '25.0', '', ''],
            ['DEEPCOOL PF750 750W', '1', '105.0', '', ''],
            ['KEEP OUT FX1000MW 1000W Modular', '1', '100.0', '', ''],
            ['AORUS ELITE P850W 80+ Platinum Modular PCIe 5.0', '1', '280.0', '', ''],
            ['LOVINGCOOL LC-SERIES G700 700W 80Plus Bronze', '1', '93.0', '', 'NA FIRMU'],
            ['LOVINGCOOL LC-SERIES G850 850W 80Plus Bronze', '1', '134.0', '', 'NA FIRMU'],
        ]
    },
    "KUCISTA": {
        "KUCISTA": [
            ["IG-MAX BUSTER 1x120mm Vent.", "1", "79.0", "", ""],
            ["Spire VISION 7022 RGB 3x120mm RGB Vent.", "1", "102.0", "", ""],
            ["Rampage PRIME tempered Glass 4x120mm ARGB Vent. E-ATX", "1", "179.0", "dr1", ""],
        ]
    },
    "RAZNO": {
        "RAZNO": [
            ["Akasa RGB (4pin) LED SPLITTER CABLE", "0", "19.0", "", ""],
            ["GIGABYTE GC-USB MCU RGB module", "5", "10.0", "Cr1", ""],
            ["HIKVISION HS-HUB-MDC1 M.2 NVMe USB-C 3.1", "0", "39.0", "", ""],
            ["GEMBIRD MA-DA2-02 Monitor stand double desk mount 17\"-32\"", "1", "79.0", "", ""],
            ["PUCK CABLE MANAGEMENT NZXT BLACK", "1", "39.0", "", ""],
            ["HIKSEMI M.2 SSD COOLER HEATSINK", "2", "11.0", "", ""],
            ["BASEUS Metal Age Gravity 4\"-6\" car holder for CD player black", "1", "20.0", "", ""],
            ["HIKVISION HS-HUB-MDC1 M.2 NVMe USB-C 3.1 External SSD Enclosure Gray", "2", "27.0", "", ""],
        ]
    },
    "SLUSALICE": {
        "SLUSALICE": [
            ["Slušalice sa mikrofonom Gaming RAMPAGE RM-K2 X-QUADRO Crne USB 7.1 RGB", "1", "52.0", "", ""],
            ["Slušalice sa mikrofonom Gaming RAMPAGE STORMY Black 7.1 USB", "1", "49.0", "", ""],
        ]
    },
    "ZVUČNICI": {
        "ZVUČNICI": [
            ["Zvučnici SPEEDLINK EVENT 2.0 Stereo SL-8004-BK", "1", "23.0", "", ""],
        ]
    },
    "MIŠEVI": {
        "MIŠEVI": [
            ["Miš SHARKOON Gaming SHARK Force II Crni", "1", "33.0", "", "NA FIRMU"],
            ["Miš SHARKOON Gaming SHARK Force III Crni", "1", "38.0", "", "NA FIRMU"],
            ["XIAOMI GAMING Lite 6200 DPI BHR8869GL", "1", "46.0", "", "NA FIRMU"],
            ["ZOWIE EC2-CW", "1", "340.0", "", "ZOWIE EC2-CW"],
        ]
    },
    "PODLOGE ZA MIŠEVE": {
        "PODLOGE ZA MIŠEVE": [
            ["Podloga za miš GEMBIRD MP-GAME-L 400x450x3mm anti slip", "1", "11.0", "", ""],
            ["Podloga za miš i tastaturu GEMBIRD MP-GAME-XL 900x350x3mm", "1", "14.0", "", ""],
        ]
    },
    "TASTATURE": {
        "TASTATURE": [
            ["EVEREST KB-961", "2", "10.0", "", ""],
        ]
    },
    "TERMALNA PASTA": {
        "TERMALNA PASTA": [
            ["NT-H2 TERMALNA PASTA 3.5g", "0", "24.0", "", ""],
        ]
    },
    "VENTILATORI": {
        "VENTILATORI": [
            ["Arcitc P12 PWM PST A-RGB Bijeli 1 kom", "2", "34.0", "", ""],
            ["Arcitc P12 PWM PST A-RGB Crni 1 kom", "0", "29.0", "", ""],
            ["Arctic P12 PWM PST CO Crni", "1", "17.0", "cr1", ""],
            ["Arctic P12 SLIM PWM PST", "1", "15.0", "", ""],
            ["Arctic P14 SLIM PWM PST", "1", "19.0", "", ""],
            ["Arctic P12 PWM PST Crni 5 komada pakovanje", "0", "59.0", "",
             "Moze prodaja na komad, cijena na komad je 12KM"],
            ["Arctic P14 3pin Crni 5 komada pakovanje", "1", "55.0", "",
             "Moze prodaja na komad, cijena na komad je 11KM"],
            ["ARCTIC COOLING BIJELI P12 PWM PST A-RGB 0dB 3-piece set", "1", "57.0", "", ""],
        ]
    },
    "MONITORI": {
        "MONITORI": [
            ["AOC 25G15N2 23.8\" VA 180Hz 1080p 1ms Adaptive Sync", "1", "233.0", "", "NA FIRMU"],
            ["Monitor AOC 27B35HM 27 VA 1080p 100Hz 1ms Adaptive Sync", "2", "204.0", "", "NA FIRMU"],
            ["Monitor XIAOMI GAMING G27i 165Hz 1ms IPS ELA5375EU", "1", "242.0", "", "NA FIRMU"],
            ["Monitor MSI MAG 25 G255F E20 FHD RAPID IPS 200Hz 0.5ms", "1", "245.0", "", "NA FIRMU"],
        ]
    },
    # Prazne kategorije koje će biti kreirane
    "KONFIGURACIJE": {"KONFIGURACIJE": []},
    "POLOVNI LAPTOPOVI": {"POLOVNI LAPTOPOVI": []},
    "POLOVNE KOMPONENTE": {"POLOVNE KOMPONENTE": []},
    "POLOVNI MONITORI": {"POLOVNI MONITORI": []}
}


def clear_lager_data():
    """Briše sve podatke iz lager_product i lager_category tabela."""
    print("Brisanje starih lager podataka...")
    try:
        db.session.query(LagerProduct).delete()
        db.session.query(LagerCategory).delete()
        db.session.commit()
        print("Stari lager podaci uspešno obrisani.")
    except Exception as e:
        db.session.rollback()
        print(f"Greška prilikom brisanja podataka: {e}")


def get_or_create_lager_category(name, parent=None):
    """Kreira lager kategoriju ako ne postoji."""
    base_slug = re.sub(r'[\s/]+', '-', name.lower())
    slug = f"{parent.slug}--{base_slug}" if parent else base_slug

    category = LagerCategory.query.filter_by(slug=slug).first()
    if not category:
        parent_id = parent.id if parent else None
        category = LagerCategory(name=name, slug=slug, parent_id=parent_id)
        db.session.add(category)
        db.session.flush()
    return category


def populate_lager_data():
    """Popunjava lager_product tabelu i osigurava da sve kategorije postoje."""
    print("Započinjem popunjavanje lagera...")

    # Prvo, osigurajmo da sve glavne kategorije postoje
    for cat_name in ALL_CATEGORIES:
        get_or_create_lager_category(cat_name)
    print("Sve glavne kategorije su kreirane ili već postoje.")

    # Zatim, popunjavamo podatke o proizvodima
    for cat_name, subcategories in lager_data.items():
        main_cat = get_or_create_lager_category(cat_name)

        for subcat_name, products in subcategories.items():
            target_cat = main_cat if subcat_name == cat_name else get_or_create_lager_category(subcat_name,
                                                                                               parent=main_cat)

            for item in products:
                # Osigurava da lista uvijek ima 5 elemenata da se izbjegne greška
                item_full = (item + ['', '', '', '', ''])[:5]
                name, stock, price, reservation, note = item_full

                if not name:
                    continue

                price_cleaned = re.sub(r'[^\d,.]', '', str(price)).replace(',', '.')

                try:
                    product = LagerProduct(
                        name=str(name).strip(),
                        stock=int(stock) if str(stock).isdigit() else 0,
                        purchase_price=decimal.Decimal(price_cleaned if price_cleaned else '0.0'),
                        reservation_note=str(reservation).strip(),
                        internal_note=str(note).strip(),
                        for_company='na firmu' in str(note).lower(),
                        category_id=target_cat.id
                    )
                    db.session.add(product)
                except decimal.InvalidOperation:
                    print(f"Greska: Neispravna vrednost za cenu kod proizvoda '{name}': '{price_cleaned}'")
                    continue

    try:
        db.session.commit()
        print("\nPopunjavanje lager tabele uspešno završeno!")
    except Exception as e:
        db.session.rollback()
        print(f"\nDošlo je do greške prilikom upisa u bazu: {e}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        clear_lager_data()
        populate_lager_data()