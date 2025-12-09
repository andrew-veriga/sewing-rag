"""PDF processing service for converting PDFs to images and extracting structured data."""
import os
import tempfile
import subprocess
import logging
from pathlib import Path
from io import BytesIO
from typing import List, Tuple, Optional
from PIL import Image
from google.genai import types
import ssl
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import sys
from pathlib import Path

# Add parent directory to path to import auth_service
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth_service import auth_service
from app.config import GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)


# System instructions for PDF processing
BOUNDING_BOX_SYSTEM_INSTRUCTIONS = """
You are experienced patternmaker and garment production technologist. You list a step-by-step guide of creating a garment.
You retrieve structured data with meaningful information to your knowledge base. The data you interested contains images and texts.
For better understanding you translate all texts into English if necessary. You detect the bounding boxes for useful images.
"""


class PDFService:
    """Service for processing PDF files."""
    
    def __init__(self):
        """Initialize PDF service with Gemini client."""
        self.gemini_client = auth_service.get_gemini_client()
        self.model_name = GEMINI_MODEL_NAME
    
    def convert_pdf_to_images(
        self, 
        pdf_path: str, 
        dpi: int = 300
    ) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Image objects.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for conversion (default: 300)
            
        Returns:
            List of PIL Image objects, one per page
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_prefix = os.path.join(tmpdir, "page")
            
            # Use Poppler's pdftoppm to convert PDF to PNG
            try:
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-r", str(dpi),
                        pdf_path,
                        output_prefix
                    ],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Error converting PDF to images: {e.stderr.decode()}")
                raise
            except FileNotFoundError:
                logger.error("pdftoppm not found. Please install poppler-utils.")
                raise
            
            # Collect all generated PNG images
            png_files = sorted(Path(tmpdir).glob("*.png"))
            images = []
            
            for image_path in png_files:
                try:
                    im = Image.open(BytesIO(open(image_path, "rb").read()))
                    # Resize to max 1024x1024 while maintaining aspect ratio
                    im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
                    images.append(im)
                except Exception as e:
                    logger.warning(f"Error processing image {image_path}: {str(e)}")
                    continue
            
            logger.info(f"Converted {len(images)} pages from PDF {pdf_path}")
            return images
    
    def upload_pdf_to_gemini(self, pdf_path: str) -> any:
        """
        Prepare PDF file for Gemini API processing.
        
        With Vertex AI, we read the file and create a Part object
        instead of using files.upload() which is only available
        in the Gemini Developer client.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Part object containing the PDF data
        """
        try:
            # Read the PDF file as bytes
            with open(pdf_path, 'rb') as f:
                file_data = f.read()
            
            # Create a Part object from the file data
            # This works with Vertex AI (service account credentials)
            file_part = types.Part.from_bytes(
                data=file_data,
                mime_type='application/pdf'
            )
            
            logger.info(f"Prepared PDF {pdf_path} for Gemini processing")
            return file_part
            
        except Exception as e:
            logger.error(f"Error preparing PDF for Gemini: {str(e)}")
            raise
    
    def get_tutorial_images(self, pdf_path: str) -> Tuple[List[Image.Image], any]:
        """
        Convert PDF to images and upload to Gemini.
        This combines convert_pdf_to_images and upload_pdf_to_gemini.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (list of PIL Images, Gemini file object)
        """
        # images = self.convert_pdf_to_images(pdf_path)
        gemini_file = self.upload_pdf_to_gemini(pdf_path)
        
        return None, gemini_file
    
    def extract_structured_tutorial(
        self, 
        gemini_file: any,
        system_instructions: Optional[str] = None
    ) -> any:
        """
        Extract structured data from PDF using Gemini.
        This replaces the GetStructuredTutorial function from the notebook.
        
        Args:
            gemini_file: Gemini file object (from upload_pdf_to_gemini)
            system_instructions: Optional custom system instructions
            
        Returns:
            Parsed Instructions object (Pydantic model)
        """
        from app.models.schemas import Instructions
        
        prompt = """
        Detect text blocks and illustrations in this PDF file.
        Extract name and description of the garment from the following PDF file.
        Extract specifications, supplying, equipment, and materials. Extract fabric consumption. Extract all preprocessings.
        Extract section headers.
        Pay attention only to texts contain detailed sewing instructions in the form of sentences dictating actions.
        Select the illustrations that best match the instructions. Concatenate instructions which select the same illustration
        """
        
        system_instructions = system_instructions or BOUNDING_BOX_SYSTEM_INSTRUCTIONS
        
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=2, min=4, max=30),
            retry=retry_if_exception_type((
                ssl.SSLError,
                httpx.ReadError,
                httpx.ConnectError,
                ConnectionError,
                OSError
            )),
            reraise=True
        )
        def _generate_with_retry():
            """Generate content with retry logic for SSL and network errors."""
            try:
                return self.gemini_client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        gemini_file,
                        system_instructions,
                        prompt,
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        response_mime_type="application/json",
                        response_schema=Instructions
                    )
                )
            except (ssl.SSLError, httpx.ReadError, httpx.ConnectError) as e:
                logger.warning(f"Network/SSL error during Gemini API call, will retry: {str(e)}")
                raise
            except (ConnectionError, OSError) as e:
                logger.warning(f"Connection error during Gemini API call, will retry: {str(e)}")
                raise
        
        try:
            response = _generate_with_retry()
            
            logger.info(f"Extracted structured data. Tokens used: {response.usage_metadata.total_token_count}")
            logger.debug(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
            logger.debug(f"Output tokens: {response.usage_metadata.candidates_token_count}")
            
            return response.parsed
            
        except Exception as e:
            logger.error(f"Error extracting structured tutorial: {str(e)}")
            raise


# Global instance
pdf_service = PDFService()

