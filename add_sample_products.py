import os
import json
import random
from datetime import datetime
from app import app, db
from models import Category, Product
from config import Config

# Sample data for different product categories
sample_data = {
    'CPUs': [
        {
            'name': 'AMD Ryzen 7 5800X',
            'description': 'AMD Ryzen 7 5800X 8-Core, 16-Thread Desktop Processor with Wraith Cooler',
            'price': 299.99,
            'specs': {
                'cores': '8',
                'threads': '16',
                'base_clock': '3.8 GHz',
                'boost_clock': '4.7 GHz',
                'tdp': '105',
                'socket': 'AM4'
            },
            'component_type': 'CPU'
        },
        {
            'name': 'Intel Core i5-12600K',
            'description': 'Intel Core i5-12600K Desktop Processor 10 Cores (6P+4E) with integrated graphics',
            'price': 289.99,
            'specs': {
                'cores': '10',
                'threads': '16',
                'base_clock': '3.7 GHz',
                'boost_clock': '4.9 GHz',
                'tdp': '125',
                'socket': 'LGA1700'
            },
            'component_type': 'CPU'
        },
        {
            'name': 'AMD Ryzen 9 5900X',
            'description': 'AMD Ryzen 9 5900X 12-Core, 24-Thread Desktop Processor',
            'price': 479.99,
            'specs': {
                'cores': '12',
                'threads': '24',
                'base_clock': '3.7 GHz',
                'boost_clock': '4.8 GHz',
                'tdp': '105',
                'socket': 'AM4'
            },
            'component_type': 'CPU'
        }
    ],
    'Motherboards': [
        {
            'name': 'MSI MPG B550 GAMING EDGE WIFI',
            'description': 'MSI MPG B550 GAMING EDGE WIFI ATX Motherboard with Wi-Fi 6, Dual M.2 slots',
            'price': 199.99,
            'specs': {
                'socket': 'AM4',
                'chipset': 'B550',
                'memory_slots': '4',
                'max_memory': '128 GB',
                'pcie_slots': '2 x PCIe 4.0 x16'
            },
            'component_type': 'Motherboard'
        },
        {
            'name': 'ASUS ROG STRIX Z690-E GAMING',
            'description': 'ASUS ROG STRIX Z690-E GAMING WIFI ATX Motherboard with PCIe 5.0, DDR5',
            'price': 459.99,
            'specs': {
                'socket': 'LGA1700',
                'chipset': 'Z690',
                'memory_slots': '4',
                'max_memory': '128 GB',
                'pcie_slots': '2 x PCIe 5.0 x16'
            },
            'component_type': 'Motherboard'
        },
        {
            'name': 'GIGABYTE B550 AORUS PRO',
            'description': 'GIGABYTE B550 AORUS PRO ATX Motherboard with Dual PCIe 4.0 M.2, SATA 6Gb/s',
            'price': 189.99,
            'specs': {
                'socket': 'AM4',
                'chipset': 'B550',
                'memory_slots': '4',
                'max_memory': '128 GB',
                'pcie_slots': '1 x PCIe 4.0 x16'
            },
            'component_type': 'Motherboard'
        }
    ],
    'Memory': [
        {
            'name': 'Corsair Vengeance RGB Pro 32GB',
            'description': 'Corsair Vengeance RGB Pro 32GB (2x16GB) DDR4 3600MHz C18 Desktop Memory',
            'price': 129.99,
            'specs': {
                'capacity': '32',
                'modules': '2',
                'speed': '3600',
                'cas_latency': '18'
            },
            'component_type': 'RAM'
        },
        {
            'name': 'G.SKILL Trident Z RGB 16GB',
            'description': 'G.SKILL Trident Z RGB 16GB (2x8GB) DDR4 3200MHz Desktop Memory with RGB lighting',
            'price': 89.99,
            'specs': {
                'capacity': '16',
                'modules': '2',
                'speed': '3200',
                'cas_latency': '16'
            },
            'component_type': 'RAM'
        },
        {
            'name': 'Crucial Ballistix 32GB',
            'description': 'Crucial Ballistix 32GB (2x16GB) DDR4 3600MHz CL16 Desktop Gaming Memory',
            'price': 139.99,
            'specs': {
                'capacity': '32',
                'modules': '2',
                'speed': '3600',
                'cas_latency': '16'
            },
            'component_type': 'RAM'
        }
    ],
    'Graphics Cards': [
        {
            'name': 'NVIDIA GeForce RTX 3080',
            'description': 'NVIDIA GeForce RTX 3080 10GB GDDR6X Graphics Card with Ray Tracing',
            'price': 799.99,
            'specs': {
                'memory': '10',
                'memory_type': 'GDDR6X',
                'tdp': '320',
                'boost_clock': '1710 MHz',
                'cuda_cores': '8704'
            },
            'component_type': 'GPU'
        },
        {
            'name': 'AMD Radeon RX 6800 XT',
            'description': 'AMD Radeon RX 6800 XT 16GB GDDR6 Graphics Card with RDNA 2 architecture',
            'price': 649.99,
            'specs': {
                'memory': '16',
                'memory_type': 'GDDR6',
                'tdp': '300',
                'boost_clock': '2250 MHz',
                'stream_processors': '4608'
            },
            'component_type': 'GPU'
        },
        {
            'name': 'NVIDIA GeForce RTX 3070',
            'description': 'NVIDIA GeForce RTX 3070 8GB GDDR6 Graphics Card for gaming and content creation',
            'price': 599.99,
            'specs': {
                'memory': '8',
                'memory_type': 'GDDR6',
                'tdp': '220',
                'boost_clock': '1725 MHz',
                'cuda_cores': '5888'
            },
            'component_type': 'GPU'
        }
    ],
    'Storage': [
        {
            'name': 'Samsung 970 EVO Plus 1TB',
            'description': 'Samsung 970 EVO Plus 1TB NVMe M.2 Internal SSD with V-NAND Technology',
            'price': 149.99,
            'specs': {
                'capacity': '1',
                'interface': 'PCIe 3.0 x4',
                'read_speed': '3500 MB/s',
                'write_speed': '3300 MB/s'
            },
            'component_type': 'Storage'
        },
        {
            'name': 'Western Digital Black SN850 2TB',
            'description': 'Western Digital Black SN850 2TB PCIe Gen4 NVMe SSD with Heatsink',
            'price': 299.99,
            'specs': {
                'capacity': '2',
                'interface': 'PCIe 4.0 x4',
                'read_speed': '7000 MB/s',
                'write_speed': '5300 MB/s'
            },
            'component_type': 'Storage'
        },
        {
            'name': 'Crucial MX500 2TB',
            'description': 'Crucial MX500 2TB 3D NAND SATA 2.5 Inch Internal SSD',
            'price': 199.99,
            'specs': {
                'capacity': '2',
                'interface': 'SATA III',
                'read_speed': '560 MB/s',
                'write_speed': '510 MB/s'
            },
            'component_type': 'Storage'
        }
    ],
    'Power Supplies': [
        {
            'name': 'Corsair RM850x',
            'description': 'Corsair RM850x 850W 80+ Gold Certified Fully Modular Power Supply',
            'price': 129.99,
            'specs': {
                'wattage': '850',
                'efficiency': '80+ Gold',
                'modular': 'Fully Modular',
                'fan_size': '135mm'
            },
            'component_type': 'Power Supply'
        },
        {
            'name': 'EVGA SuperNOVA 750 G5',
            'description': 'EVGA SuperNOVA 750 G5, 80+ Gold 750W, Fully Modular Power Supply',
            'price': 109.99,
            'specs': {
                'wattage': '750',
                'efficiency': '80+ Gold',
                'modular': 'Fully Modular',
                'fan_size': '135mm'
            },
            'component_type': 'Power Supply'
        },
        {
            'name': 'Seasonic FOCUS GX-650',
            'description': 'Seasonic FOCUS GX-650, 650W 80+ Gold, Full-Modular Power Supply',
            'price': 99.99,
            'specs': {
                'wattage': '650',
                'efficiency': '80+ Gold',
                'modular': 'Fully Modular',
                'fan_size': '120mm'
            },
            'component_type': 'Power Supply'
        }
    ],
    'Cases': [
        {
            'name': 'NZXT H510',
            'description': 'NZXT H510 - Compact ATX Mid-Tower PC Gaming Case with tempered glass',
            'price': 69.99,
            'specs': {
                'type': 'Mid Tower',
                'motherboard_support': 'Mini-ITX, MicroATX, ATX',
                'gpu_length': '381mm',
                'psu_length': '210mm'
            },
            'component_type': 'Case'
        },
        {
            'name': 'Corsair 4000D Airflow',
            'description': 'Corsair 4000D Airflow Tempered Glass Mid-Tower ATX Case',
            'price': 94.99,
            'specs': {
                'type': 'Mid Tower',
                'motherboard_support': 'Mini-ITX, MicroATX, ATX, E-ATX',
                'gpu_length': '360mm',
                'psu_length': '220mm'
            },
            'component_type': 'Case'
        },
        {
            'name': 'Lian Li PC-O11 Dynamic',
            'description': 'Lian Li PC-O11 Dynamic Tempered Glass ATX Mid Tower Case',
            'price': 149.99,
            'specs': {
                'type': 'Mid Tower',
                'motherboard_support': 'Mini-ITX, MicroATX, ATX, E-ATX',
                'gpu_length': '420mm',
                'psu_length': '255mm'
            },
            'component_type': 'Case'
        }
    ],
    'Cooling': [
        {
            'name': 'Noctua NH-D15',
            'description': 'Noctua NH-D15, Premium CPU Cooler with 2x NF-A15 PWM 140mm Fans',
            'price': 99.99,
            'specs': {
                'type': 'Air Cooler',
                'fan_size': '140mm',
                'noise_level': '24.6 dB(A)',
                'height': '165mm'
            },
            'component_type': 'CPU Cooler'
        },
        {
            'name': 'Corsair H100i RGB PRO XT',
            'description': 'Corsair H100i RGB PRO XT, 240mm Radiator, Dual 120mm PWM Fans, AIO CPU Liquid Cooler',
            'price': 119.99,
            'specs': {
                'type': 'Liquid Cooler',
                'radiator_size': '240mm',
                'fan_size': '120mm',
                'noise_level': '28 dB(A)'
            },
            'component_type': 'CPU Cooler'
        },
        {
            'name': 'be quiet! Dark Rock Pro 4',
            'description': 'be quiet! Dark Rock Pro 4, BK022, 250W TDP, CPU Cooler',
            'price': 89.99,
            'specs': {
                'type': 'Air Cooler',
                'fan_size': '120mm & 135mm',
                'noise_level': '24.3 dB(A)',
                'height': '162.8mm'
            },
            'component_type': 'CPU Cooler'
        }
    ],
    'Monitors': [
        {
            'name': 'LG 27GL83A-B 27"',
            'description': 'LG 27GL83A-B 27" Ultragear QHD IPS 1ms NVIDIA G-SYNC Compatible Gaming Monitor',
            'price': 379.99,
            'specs': {
                'size': '27',
                'resolution': '2560x1440',
                'refresh_rate': '144 Hz',
                'response_time': '1ms'
            },
            'component_type': 'Monitor'
        },
        {
            'name': 'Dell S2721DGF 27"',
            'description': 'Dell S2721DGF 27" Gaming Monitor, QHD, 165Hz, 1ms, G-SYNC Compatible',
            'price': 399.99,
            'specs': {
                'size': '27',
                'resolution': '2560x1440',
                'refresh_rate': '165 Hz',
                'response_time': '1ms'
            },
            'component_type': 'Monitor'
        },
        {
            'name': 'ASUS TUF Gaming VG259QM 24.5"',
            'description': 'ASUS TUF Gaming VG259QM 24.5" Monitor, 1080P, 280Hz, G-SYNC Compatible',
            'price': 299.99,
            'specs': {
                'size': '24.5',
                'resolution': '1920x1080',
                'refresh_rate': '280 Hz',
                'response_time': '1ms'
            },
            'component_type': 'Monitor'
        }
    ]
}

def add_sample_products():
    """Add sample products to the database"""
    with app.app_context():
        print("Adding sample categories and products...")
        
        # Create categories
        categories = {}
        for category_name in sample_data.keys():
            slug = category_name.lower().replace(' ', '-')
            category = Category.query.filter_by(name=category_name).first()
            
            if not category:
                category = Category(
                    name=category_name,
                    slug=slug,
                    description=f"{category_name} category"
                )
                db.session.add(category)
                db.session.flush()  # Get ID without committing
            
            categories[category_name] = category
        
        # Create products
        product_count = 0
        for category_name, products_data in sample_data.items():
            category = categories[category_name]
            
            for product_data in products_data:
                # Convert EUR price to BAM with markup
                eur_price = product_data['price']
                bam_price = eur_price * Config.EUR_TO_BAM_RATE
                marked_up_price = bam_price + (bam_price * (Config.MARKUP_PERCENTAGE / 100))
                final_price = round(marked_up_price, 2)
                
                # Check if product already exists
                existing_product = Product.query.filter_by(name=product_data['name']).first()
                if existing_product:
                    continue
                
                # Create product
                product = Product(
                    name=product_data['name'],
                    description=product_data['description'],
                    price=final_price,
                    stock=random.randint(5, 50),
                    image_url="/static/img/no-image.svg",  # Default image
                    specs=json.dumps(product_data['specs']),
                    category_id=category.id,
                    component_type=product_data.get('component_type')
                )
                
                db.session.add(product)
                product_count += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"Added {product_count} products across {len(categories)} categories.")
        return product_count

if __name__ == "__main__":
    add_sample_products()