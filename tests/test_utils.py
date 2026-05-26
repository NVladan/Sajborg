"""
Unit tests for utility functions in utils.py

Tests cover:
- Currency conversion
- Price formatting
- Order total calculation
- PC build compatibility checking
- File upload validation (NEW)
- Filename sanitization (NEW)
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage

from utils import (
    eur_to_bam,
    format_price,
    calculate_order_total,
    validate_image_upload,
    validate_document_upload,
    secure_filename_custom,
    get_file_extension
)
from config import Config


# =============================================================================
# Currency and Price Tests
# =============================================================================

@pytest.mark.unit
class TestCurrencyConversion:
    """Test EUR to BAM currency conversion."""

    def test_eur_to_bam_basic(self):
        """Test basic EUR to BAM conversion."""
        result = eur_to_bam(100)
        # 100 EUR * 1.95583 * 1.15 (markup) = 224.92
        assert result == 224.92

    def test_eur_to_bam_zero(self):
        """Test conversion with zero."""
        result = eur_to_bam(0)
        assert result == 0.0

    def test_eur_to_bam_decimal(self):
        """Test conversion with decimal values."""
        result = eur_to_bam(50.50)
        expected = round(50.50 * Config.EUR_TO_BAM_RATE * 1.15, 2)
        assert result == expected

    def test_eur_to_bam_rounding(self):
        """Test that result is rounded to 2 decimal places."""
        result = eur_to_bam(33.33)
        assert isinstance(result, float)
        assert len(str(result).split('.')[-1]) <= 2


@pytest.mark.unit
class TestPriceFormatting:
    """Test price formatting functions."""

    def test_format_price_bam(self):
        """Test BAM price formatting."""
        result = format_price(100.50, 'BAM')
        assert result == '100.50 KM'

    def test_format_price_eur(self):
        """Test EUR price formatting."""
        result = format_price(100.50, 'EUR')
        assert result == '€100.50'

    def test_format_price_default(self):
        """Test default price formatting."""
        result = format_price(100.50)
        assert result == '100.50 KM'

    def test_format_price_unknown_currency(self):
        """Test formatting with unknown currency."""
        result = format_price(100.50, 'USD')
        assert result == '100.50'


# =============================================================================
# Order Calculation Tests
# =============================================================================

@pytest.mark.unit
class TestOrderCalculations:
    """Test order total calculations."""

    def test_calculate_order_total_single_item(self, app, sample_cart_item):
        """Test total calculation with single item."""
        with app.app_context():
            from extensions import db
            from models import CartItem
            # Refresh the cart item to bind it to the current session
            cart_item = db.session.merge(sample_cart_item)
            db.session.refresh(cart_item)
            total = calculate_order_total([cart_item])
            expected = cart_item.product.price * cart_item.quantity
            assert total == round(expected, 2)

    def test_calculate_order_total_multiple_items(self, app, sample_cart):
        """Test total calculation with multiple items."""
        with app.app_context():
            from extensions import db
            # Refresh all cart items to bind them to the current session
            cart_items = [db.session.merge(item) for item in sample_cart]
            for item in cart_items:
                db.session.refresh(item)
            total = calculate_order_total(cart_items)
            # Calculate expected total
            expected = sum(item.product.price * item.quantity for item in cart_items)
            assert total == round(expected, 2)

    def test_calculate_order_total_with_warranty(self, app, sample_user, sample_product):
        """Test total calculation with extended warranty."""
        with app.app_context():
            from models import CartItem
            from extensions import db
            # Merge fixtures to current session
            user = db.session.merge(sample_user)
            product = db.session.merge(sample_product)
            cart_item = CartItem(
                user_id=user.id,
                product_id=product.id,
                quantity=1,
                extended_warranty=True
            )
            db.session.add(cart_item)
            db.session.flush()
            db.session.refresh(cart_item)
            total = calculate_order_total([cart_item])
            # Price should be increased by 10% for warranty
            expected = round(product.price * 1.10, 2)
            assert total == expected

    def test_calculate_order_total_empty_cart(self):
        """Test total calculation with empty cart."""
        total = calculate_order_total([])
        assert total == 0.0


# =============================================================================
# File Extension Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestFileExtension:
    """Test file extension extraction."""

    def test_get_extension_normal(self):
        """Test normal file extension."""
        ext = get_file_extension('image.jpg')
        assert ext == 'jpg'

    def test_get_extension_uppercase(self):
        """Test uppercase extension is converted to lowercase."""
        ext = get_file_extension('IMAGE.JPG')
        assert ext == 'jpg'

    def test_get_extension_multiple_dots(self):
        """Test file with multiple dots."""
        ext = get_file_extension('my.file.name.png')
        assert ext == 'png'

    def test_get_extension_no_extension(self):
        """Test file without extension."""
        ext = get_file_extension('noextension')
        assert ext == ''

    def test_get_extension_empty_string(self):
        """Test empty filename."""
        ext = get_file_extension('')
        assert ext == ''

    def test_get_extension_none(self):
        """Test None filename."""
        ext = get_file_extension(None)
        assert ext == ''


# =============================================================================
# Image Upload Validation Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestImageUploadValidation:
    """Test image upload validation."""

    def test_validate_valid_jpg(self, mock_image_file):
        """Test validation of valid JPG file."""
        is_valid, error = validate_image_upload(mock_image_file)
        assert is_valid is True
        assert error is None

    def test_validate_valid_png(self):
        """Test validation of valid PNG file."""
        # Valid PNG magic bytes
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = FileStorage(
            stream=BytesIO(png_header),
            filename="test.png",
            content_type="image/png"
        )
        is_valid, error = validate_image_upload(file)
        assert is_valid is True
        assert error is None

    def test_validate_invalid_extension(self, mock_invalid_file):
        """Test rejection of invalid file extension."""
        is_valid, error = validate_image_upload(mock_invalid_file)
        assert is_valid is False
        assert "nije dozvoljen" in error.lower()
        assert "exe" not in error  # Should not expose the extension

    def test_validate_no_file(self):
        """Test validation with no file."""
        is_valid, error = validate_image_upload(None)
        assert is_valid is False
        assert "nije izabran fajl" in error.lower()

    def test_validate_empty_filename(self):
        """Test validation with empty filename."""
        file = FileStorage(
            stream=BytesIO(b"content"),
            filename="",
            content_type="image/jpeg"
        )
        is_valid, error = validate_image_upload(file)
        assert is_valid is False
        assert "izabran" in error.lower()

    def test_validate_large_file(self, mock_large_file):
        """Test rejection of file larger than 5MB."""
        is_valid, error = validate_image_upload(mock_large_file)
        assert is_valid is False
        assert "prevelik" in error.lower()
        assert "5MB" in error or "5mb" in error.upper()

    def test_validate_empty_file(self, mock_empty_file):
        """Test rejection of empty file."""
        is_valid, error = validate_image_upload(mock_empty_file)
        assert is_valid is False
        assert "prazan" in error.lower()

    def test_validate_webp(self):
        """Test validation of WebP file."""
        # Valid WebP: RIFF....WEBP
        webp_header = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 100
        file = FileStorage(
            stream=BytesIO(webp_header),
            filename="test.webp",
            content_type="image/webp"
        )
        is_valid, error = validate_image_upload(file)
        assert is_valid is True
        assert error is None

    def test_validate_gif(self):
        """Test validation of GIF file."""
        file = FileStorage(
            stream=BytesIO(b"GIF89a" + b"x" * 100),  # Valid GIF header
            filename="animation.gif",
            content_type="image/gif"
        )
        is_valid, error = validate_image_upload(file)
        assert is_valid is True
        assert error is None


# =============================================================================
# Document Upload Validation Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestDocumentUploadValidation:
    """Test document upload validation."""

    def test_validate_valid_pdf(self):
        """Test validation of valid PDF file."""
        file = FileStorage(
            stream=BytesIO(b"%PDF-1.4" + b"x" * 100),
            filename="document.pdf",
            content_type="application/pdf"
        )
        is_valid, error = validate_document_upload(file)
        assert is_valid is True
        assert error is None

    def test_validate_invalid_extension(self):
        """Test rejection of invalid document extension."""
        file = FileStorage(
            stream=BytesIO(b"content"),
            filename="script.js",
            content_type="application/javascript"
        )
        is_valid, error = validate_document_upload(file)
        assert is_valid is False
        assert "nije dozvoljen" in error.lower()

    def test_validate_large_document(self):
        """Test rejection of document larger than 10MB."""
        # Create 11MB file
        large_data = b"x" * (11 * 1024 * 1024)
        file = FileStorage(
            stream=BytesIO(large_data),
            filename="large.pdf",
            content_type="application/pdf"
        )
        is_valid, error = validate_document_upload(file)
        assert is_valid is False
        assert "prevelik" in error.lower()


# =============================================================================
# Filename Sanitization Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestFilenameSanitization:
    """Test filename sanitization for security."""

    def test_sanitize_normal_filename(self):
        """Test sanitization of normal filename."""
        result = secure_filename_custom("my_image.jpg")
        assert result == "my_image.jpg"

    def test_sanitize_directory_traversal(self):
        """Test prevention of directory traversal."""
        result = secure_filename_custom("../../etc/passwd.jpg")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
        assert result == "etcpasswd.jpg"

    def test_sanitize_spaces(self):
        """Test conversion of spaces to underscores."""
        result = secure_filename_custom("my image file.jpg")
        assert result == "my_image_file.jpg"
        assert " " not in result

    def test_sanitize_special_characters(self):
        """Test removal of special characters."""
        result = secure_filename_custom("file!@#$%^&*()name.jpg")
        assert "!" not in result
        assert "@" not in result
        assert result == "filename.jpg"

    def test_sanitize_unicode(self):
        """Test handling of unicode characters."""
        result = secure_filename_custom("fájl_šđčć.jpg")
        # Non-ASCII characters should be removed
        assert result == "fjl_.jpg"

    def test_sanitize_long_filename(self):
        """Test truncation of very long filenames."""
        long_name = "a" * 200 + ".jpg"
        result = secure_filename_custom(long_name)
        assert len(result) <= 104  # 100 + ".jpg"
        assert result.endswith(".jpg")

    def test_sanitize_no_extension(self):
        """Test filename without extension."""
        result = secure_filename_custom("noextension")
        assert result == "noextension"

    def test_sanitize_empty_filename(self):
        """Test empty filename returns 'unnamed'."""
        result = secure_filename_custom("")
        assert result == "unnamed"

    def test_sanitize_only_special_chars(self):
        """Test filename with only special characters."""
        result = secure_filename_custom("!@#$%.jpg")
        assert result == "unnamed"  # All removed, fallback to unnamed

    def test_sanitize_preserves_extension(self):
        """Test that file extension is preserved."""
        result = secure_filename_custom("test!@#$file.jpeg")
        assert result.endswith(".jpeg")

    def test_sanitize_multiple_dots(self):
        """Test handling of multiple dots in filename."""
        result = secure_filename_custom("my.file.name.jpg")
        assert result == "my.file.name.jpg"

    def test_sanitize_leading_dots(self):
        """Test removal of leading dots."""
        result = secure_filename_custom("...file.jpg")
        assert not result.startswith(".")
        assert result == "file.jpg"

    def test_sanitize_trailing_dots(self):
        """Test removal of trailing dots (before extension)."""
        result = secure_filename_custom("file....jpg")
        assert result == "file.jpg"


# =============================================================================
# PC Build Compatibility Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.slow
class TestPCBuildCompatibility:
    """Test PC build compatibility checking."""

    def test_compatibility_empty_build(self):
        """Test compatibility check with no components."""
        from utils import check_pc_build_compatibility
        is_compatible, messages = check_pc_build_compatibility([])
        assert is_compatible is True
        assert "Nema izabranih komponenti" in messages[0]

    # Note: Full PC compatibility tests would require creating products
    # with proper attributes, which is more complex.
    # These would be better as integration tests.


# =============================================================================
# Security Edge Cases
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSecurityEdgeCases:
    """Test security-related edge cases."""

    def test_null_byte_in_filename(self):
        """Test handling of null byte in filename."""
        result = secure_filename_custom("file\x00.jpg")
        assert "\x00" not in result

    def test_path_separator_variations(self):
        """Test various path separator attempts."""
        test_cases = [
            "../file.jpg",
            "..\\file.jpg",
            "folder/../file.jpg",
            "folder\\..\\file.jpg"
        ]
        for filename in test_cases:
            result = secure_filename_custom(filename)
            assert ".." not in result
            assert "/" not in result
            assert "\\" not in result

    def test_xss_attempt_in_filename(self):
        """Test XSS attempt in filename."""
        result = secure_filename_custom("<script>alert('xss')</script>.jpg")
        assert "<" not in result
        assert ">" not in result
        assert "script" in result  # Should keep alphanumeric

    def test_sql_injection_attempt_in_filename(self):
        """Test SQL injection attempt in filename."""
        result = secure_filename_custom("'; DROP TABLE users; --.jpg")
        assert ";" not in result
        assert "DROP" in result  # Alphanumeric preserved
        assert "--" not in result
