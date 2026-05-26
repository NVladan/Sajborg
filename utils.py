import json
import pandas as pd
from config import Config
import traceback
import os


def eur_to_bam(eur_price):
    """Convert EUR price to BAM with markup"""
    bam_price = eur_price * Config.EUR_TO_BAM_RATE
    marked_up_price = bam_price + (bam_price * (Config.MARKUP_PERCENTAGE / 100))
    return round(marked_up_price, 2)


def format_price(price, currency='BAM'):
    """Format price with currency symbol"""
    if currency == 'BAM':
        return f'{price:.2f} KM'
    elif currency == 'EUR':
        return f'€{price:.2f}'
    return f'{price:.2f}'


def parse_product_specs(specs_string):
    """Parse JSON specs string to dictionary"""
    if not specs_string:
        return {}
    try:
        return json.loads(specs_string)
    except:
        return {}


def calculate_order_total(cart_items):
    """Calculate total order amount from cart items, including extended warranty."""
    total = 0
    for item in cart_items:
        item_price = item.product.price
        if item.extended_warranty:
            item_price *= 1.10  # Increase price by 10% for extended warranty
        total += item_price * item.quantity
    return round(total, 2)


def process_import_file(file_path):
    """Process CSV/Excel import file for products"""
    try:
        # Detect file type by extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return None, "Nepodržan format fajla. Molimo koristite CSV ili Excel."

        # Validate basic required columns
        basic_required_columns = ['name', 'description', 'price', 'stock']
        for col in basic_required_columns:
            if col not in df.columns:
                return None, f"Nedostaje obavezna kolona: {col}"

        # Validate that either category_id or category_name is present
        if 'category_id' not in df.columns and 'category_name' not in df.columns:
            return None, "Potrebna je ili 'category_id' ili 'category_name' kolona"

        # Convert column types
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if df['price'].isna().any():
                return None, "Pronađene su nevažeće vrednosti za cenu. Sve cene moraju biti numeričke."

        if 'stock' in df.columns:
            df['stock'] = pd.to_numeric(df['stock'], errors='coerce').fillna(0).astype(int)
            if df['stock'].isna().any():
                return None, "Pronađene su nevažeće vrednosti za stanje. Sve vrednosti za stanje moraju biti numeričke."

        # Handle missing optional columns
        optional_columns = ['image_url', 'specs', 'component_type']
        for col in optional_columns:
            if col not in df.columns:
                df[col] = ''

        # Convert to list of dictionaries
        products_data = df.to_dict(orient='records')

        # Validate product data
        for i, product in enumerate(products_data):
            if not product.get('name'):
                return None, f"Nedostaje naziv proizvoda u redu {i + 2}"

            if not product.get('description'):
                return None, f"Nedostaje opis proizvoda u redu {i + 2}"

            # Price validation
            if not product.get('price') or product.get('price') <= 0:
                return None, f"Nevažeća cena za proizvod '{product.get('name')}' u redu {i + 2}"

            # Validate either category_id or category_name is provided
            if not product.get('category_id') and not product.get('category_name'):
                return None, f"Za proizvod '{product.get('name')}' mora biti obezbeđen ili ID ili naziv kategorije"

        return products_data, None

    except Exception as e:
        return None, f"Greška pri obradi fajla: {str(e)}"


def check_pc_build_compatibility(components):
    """
    Check if selected PC components are compatible.
    Ova verzija čita podatke iz sistema atributa umesto iz 'specs' polja.
    Returns a tuple (is_compatible, compatibility_messages)
    """
    try:
        messages = []
        is_compatible = True

        if not components:
            messages.append("Nema izabranih komponenti")
            return True, messages

        # Pomoćna funkcija za lakše dobijanje vrednosti atributa
        def get_attribute_value(component, attribute_name):
            for attr_val in component.attribute_values:
                if attr_val.attribute.name.lower() == attribute_name.lower():
                    return attr_val.value
            return 'Nepoznato'

        component_dict = {comp.component_type: comp for comp in components if comp.component_type}

        # 1. Provera kompatibilnosti CPU i matične ploče (preko socketa)
        if 'CPU' in component_dict and 'Motherboard' in component_dict:
            cpu = component_dict['CPU']
            motherboard = component_dict['Motherboard']

            cpu_socket = get_attribute_value(cpu, 'socket')
            mb_socket = get_attribute_value(motherboard, 'socket')

            if cpu_socket != 'Nepoznato' and mb_socket != 'Nepoznato' and cpu_socket.strip().lower() != mb_socket.strip().lower():
                messages.append(f"CPU podnožje ({cpu_socket}) se ne podudara sa podnožjem matične ploče ({mb_socket})")
                is_compatible = False

        # 2. Provera kompatibilnosti RAM-a i matične ploče
        if 'RAM' in component_dict and 'Motherboard' in component_dict:
            ram = component_dict['RAM']
            motherboard = component_dict['Motherboard']

            ram_type = get_attribute_value(ram, 'ram')  # Npr. "DDR4" ili "DDR5"
            mb_ram_type = get_attribute_value(motherboard, 'ram')  # Pretpostavljamo atribut "RAM"

            if ram_type != 'Nepoznato' and mb_ram_type != 'Nepoznato' and ram_type.strip().lower() not in mb_ram_type.strip().lower():
                messages.append(f"RAM tip ({ram_type}) nije kompatibilan sa matičnom pločom (podržava {mb_ram_type})")
                is_compatible = False

        # 3. Provera napajanja (PSU)
        total_tdp = 0
        for comp_type, comp in component_dict.items():
            if comp_type != 'Power Supply':
                try:
                    # Pokušava da nađe atribut 'TDP (W)' ili samo 'TDP'
                    tdp_str = get_attribute_value(comp, 'tdp (w)')
                    if tdp_str == 'Nepoznato':
                        tdp_str = get_attribute_value(comp, 'tdp')

                    if tdp_str != 'Nepoznato':
                        total_tdp += int(tdp_str)
                except (ValueError, TypeError):
                    continue  # Ignorišemo komponente bez validnog TDP-a

        if 'Power Supply' in component_dict:
            psu = component_dict['Power Supply']
            psu_wattage_str = get_attribute_value(psu, 'wattage')
            try:
                psu_wattage = int(psu_wattage_str)
                # Proveravamo da li je napajanje bar 20% jače od potrošnje
                if psu_wattage < total_tdp * 1.2:
                    messages.append(
                        f"Napajanje od {psu_wattage}W možda neće biti dovoljno. Preporučena snaga je bar {int(total_tdp * 1.2)}W.")
                    is_compatible = False
            except (ValueError, TypeError):
                messages.append("Nije moguće utvrditi snagu napajanja.")

        # 4. Provera kompletnosti
        essential_components = ['CPU', 'Motherboard', 'RAM', 'Storage', 'Power Supply', 'Case']
        missing = [comp for comp in essential_components if comp not in component_dict]

        if missing:
            messages.append(f"Konfiguraciji nedostaju osnovne komponente: {', '.join(missing)}")

        if not messages:
            messages.append("Konfiguracija je kompatibilna.")

        return is_compatible, messages

    except Exception as e:
        print(f"Greška pri proveri kompatibilnosti: {str(e)}")
        print(traceback.format_exc())
        return False, [f"Došlo je do greške u sistemu za proveru: {str(e)}"]


# File upload validation
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB


def get_file_extension(filename):
    """
    Extract file extension from filename.

    Args:
        filename (str): Name of the file

    Returns:
        str: Lowercase file extension without dot, or empty string if no extension
    """
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def validate_image_upload(file):
    """
    Validate uploaded image file for security and size constraints.
    Checks both file extension and magic bytes (content-type).

    Args:
        file: FileStorage object from Flask request.files

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file:
        return False, "Nije izabran fajl"

    if file.filename == '':
        return False, "Nije izabran fajl"

    # Check extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Tip fajla nije dozvoljen. Koristite: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning

    if size > MAX_IMAGE_SIZE:
        max_size_mb = MAX_IMAGE_SIZE // (1024 * 1024)
        return False, f"Fajl je prevelik. Maksimalna veličina: {max_size_mb}MB"

    if size == 0:
        return False, "Fajl je prazan"

    # Validate magic bytes to prevent disguised file uploads
    header = file.read(12)
    file.seek(0)  # Reset to beginning

    if not _validate_image_magic_bytes(header, ext):
        return False, "Sadržaj fajla ne odgovara ekstenziji. Fajl možda nije validan."

    return True, None


# Magic byte signatures for image formats
_IMAGE_SIGNATURES = {
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'gif': [b'GIF87a', b'GIF89a'],
    'webp': [b'RIFF'],  # Full check: RIFF....WEBP
}


def _validate_image_magic_bytes(header, ext):
    """
    Validate that file header bytes match expected image format.

    Args:
        header: First 12 bytes of the file
        ext: File extension (lowercase, no dot)

    Returns:
        bool: True if magic bytes match the extension
    """
    if len(header) < 4:
        return False

    signatures = _IMAGE_SIGNATURES.get(ext, [])
    for sig in signatures:
        if header[:len(sig)] == sig:
            # Additional check for WebP: bytes 8-12 should be 'WEBP'
            if ext == 'webp' and len(header) >= 12:
                return header[8:12] == b'WEBP'
            return True

    return False


def validate_document_upload(file):
    """
    Validate uploaded document file for security and size constraints.

    Args:
        file: FileStorage object from Flask request.files

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file:
        return False, "Fajl nije prosleđen"

    if file.filename == '':
        return False, "Nije izabran fajl"

    # Check extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return False, f"Tip fajla nije dozvoljen. Koristite: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning

    if size > MAX_DOCUMENT_SIZE:
        max_size_mb = MAX_DOCUMENT_SIZE // (1024 * 1024)
        return False, f"Fajl je prevelik. Maksimalna veličina: {max_size_mb}MB"

    if size == 0:
        return False, "Fajl je prazan"

    return True, None


def secure_filename_custom(filename):
    """
    Sanitize filename to prevent directory traversal and other attacks.
    More strict than werkzeug.utils.secure_filename.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    import re

    if not filename:
        return 'unnamed'

    # First, remove path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Keep only ASCII alphanumeric, spaces, dots, and underscores
    # Remove dashes (--) for SQL injection protection and unicode chars
    # This also removes dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9\s._]', '', filename)

    # Remove leading/trailing whitespace
    filename = filename.strip()

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Replace multiple consecutive dots with single dot (file....jpg -> file.jpg)
    # This handles both legitimate cases like "file....jpg" and path traversal attempts
    filename = re.sub(r'\.{2,}', '.', filename)

    # Check if filename is only an extension BEFORE removing leading dots
    # (e.g., ".jpg" remains from "!@#$%.jpg")
    if '.' in filename:
        parts = filename.rsplit('.', 1)
        name, ext = parts
        if not name or not name.strip('.').strip():  # Only extension remains (name is empty or only dots)
            return 'unnamed'
        # Remove trailing dots from name before reconstructing
        name = name.rstrip('.')
        if not name:  # After removing trailing dots, name is empty
            return 'unnamed'
        filename = f"{name}.{ext}"

    # Remove leading dots AFTER checking for extension-only filenames
    filename = filename.lstrip('.')

    # Final check for empty filename
    if not filename:
        return 'unnamed'

    # Limit filename length (preserve extension)
    max_length = 100
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            name = name[:max_length - len(ext) - 1]  # -1 for the dot
            filename = f"{name}.{ext}"
        else:
            filename = filename[:max_length]

    return filename if filename else 'unnamed'