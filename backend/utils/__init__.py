"""
utils package — shared helpers and low-level utilities.

Exports the most commonly used helpers so callers can do:
    from utils import fn_hash_password, fn_decode_token, ...
"""

from utils.file_utils import (
    fn_allowed_file,
    fn_get_file_extension,
    fn_generate_unique_filename,
    fn_get_file_size_mb,
    fn_ensure_dir,
    fn_delete_file,
    fn_move_file,
)
from utils.pdf_utils import (
    fn_extract_text_from_pdf,
    fn_get_pdf_page_count,
    fn_extract_images_from_pdf,
)
from utils.table_utils import (
    fn_extract_tables_from_pdf,
    fn_tables_to_markdown,
)
from utils.ocr_utils import (
    fn_ocr_image,
    fn_ocr_pdf_page,
    fn_is_scanned_pdf,
)
from utils.jwt_utils import (
    fn_create_access_token,
    fn_create_refresh_token,
    fn_decode_access_token,
    fn_decode_refresh_token,
)
from utils.password_utils import (
    fn_hash_password,
    fn_verify_password,
    fn_validate_password_strength,
)
from utils.email_utils import (
    fn_build_verification_email,
    fn_build_password_reset_email,
    fn_build_welcome_email,
)
from utils.token_utils import (
    fn_generate_secure_token,
    fn_hash_token,
    fn_verify_token_hash,
)
from utils.validation_utils import (
    fn_validate_email,
    fn_validate_filename,
    fn_sanitize_string,
    fn_validate_uuid,
)

__all__ = [
    # file
    "fn_allowed_file", "fn_get_file_extension", "fn_generate_unique_filename",
    "fn_get_file_size_mb", "fn_ensure_dir", "fn_delete_file", "fn_move_file",
    # pdf
    "fn_extract_text_from_pdf", "fn_get_pdf_page_count", "fn_extract_images_from_pdf",
    # table
    "fn_extract_tables_from_pdf", "fn_tables_to_markdown",
    # ocr
    "fn_ocr_image", "fn_ocr_pdf_page", "fn_is_scanned_pdf",
    # jwt
    "fn_create_access_token", "fn_create_refresh_token",
    "fn_decode_access_token", "fn_decode_refresh_token",
    # password
    "fn_hash_password", "fn_verify_password", "fn_validate_password_strength",
    # email
    "fn_build_verification_email", "fn_build_password_reset_email", "fn_build_welcome_email",
    # token
    "fn_generate_secure_token", "fn_hash_token", "fn_verify_token_hash",
    # validation
    "fn_validate_email", "fn_validate_filename", "fn_sanitize_string", "fn_validate_uuid",
]