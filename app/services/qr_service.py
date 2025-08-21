import qrcode
from io import BytesIO
from PIL import Image
from typing import Optional
from ..config import settings

class QRService:
    @staticmethod
    def generate_qr_code(
        campaign_id: str, 
        size: int = 300,
        format: str = "PNG"
    ) -> BytesIO:
        # Create the tracking URL
        tracking_url = f"{settings.base_url}/scan/{campaign_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        
        qr.add_data(tracking_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize if needed
        if size != 300:  # Default size
            qr_image = qr_image.resize((size, size), Image.LANCZOS)
        
        # Convert to bytes
        img_buffer = BytesIO()
        qr_image.save(img_buffer, format=format)
        img_buffer.seek(0)
        
        return img_buffer
    
    @staticmethod
    def get_tracking_url(campaign_id: str) -> str:
        return f"{settings.base_url}/scan/{campaign_id}"
    
    @staticmethod
    def validate_qr_scan(campaign_id: str) -> bool:
        # Basic validation - campaign ID should be 14 characters
        return len(campaign_id) == 14 and campaign_id.replace('-', '').replace('_', '').isalnum()