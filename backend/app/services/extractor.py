"""PDF text extraction service using pdfplumber.

Privacy Note: All extraction is done in-memory. No files are written to disk.
"""
import hashlib
import io
from typing import Optional, Tuple
import pdfplumber


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


class ScriptExtractor:
    """Extracts text and metadata from script files (PDF and FDX)."""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
    MAX_PAGES = 300  # Sanity check for script length
    
    @staticmethod
    def compute_hash(data: bytes) -> str:
        """Compute SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    @classmethod
    def extract_pdf(cls, file_content: bytes, filename: str) -> dict:
        """Extract text and metadata from PDF file.
        
        Args:
            file_content: Raw bytes of the PDF file
            filename: Original filename (for hash computation)
            
        Returns:
            Dictionary containing:
                - text: Extracted text content
                - title: Detected title (if found)
                - page_count: Number of pages
                - file_hash: SHA256 hash of file content
                - filename_hash: SHA256 hash of filename
                
        Raises:
            PDFExtractionError: If extraction fails or file is invalid
        """
        # Validate file size
        if len(file_content) > cls.MAX_FILE_SIZE:
            raise PDFExtractionError(f"File too large: {len(file_content)} bytes (max {cls.MAX_FILE_SIZE})")
        
        # Compute hashes
        file_hash = cls.compute_hash(file_content)
        filename_hash = cls.compute_hash(filename.encode())
        
        try:
            # Open PDF from memory (no disk writes)
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                page_count = len(pdf.pages)
                
                if page_count > cls.MAX_PAGES:
                    raise PDFExtractionError(f"Too many pages: {page_count} (max {cls.MAX_PAGES})")
                
                if page_count == 0:
                    raise PDFExtractionError("PDF has no pages")
                
                # Extract text from all pages
                all_text = []
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            all_text.append(text)
                    except Exception as e:
                        # Log but continue - some pages might fail
                        print(f"Warning: Failed to extract page {i+1}: {e}")
                
                full_text = "\n\n".join(all_text)
                
                if not full_text.strip():
                    raise PDFExtractionError("No text could be extracted from PDF")
                
                # Try to detect title from first page
                title = cls._detect_title(full_text, pdf.pages[0] if pdf.pages else None)
                
                return {
                    "text": full_text,
                    "title": title,
                    "page_count": page_count,
                    "file_hash": file_hash,
                    "filename_hash": filename_hash,
                    "format": "pdf"
                }
                
        except pdfplumber.pdfminer.PDFException as e:
            raise PDFExtractionError(f"Invalid PDF: {str(e)}")
        except Exception as e:
            raise PDFExtractionError(f"Extraction failed: {str(e)}")
    
    @classmethod
    def extract_fdx(cls, file_content: bytes, filename: str) -> dict:
        """Extract text and metadata from Final Draft (.fdx) file.
        
        FDX files are XML-based and contain structured screenplay data.
        
        Args:
            file_content: Raw bytes of the FDX file
            filename: Original filename (for hash computation)
            
        Returns:
            Dictionary containing:
                - text: Extracted text content (formatted as screenplay)
                - title: Script title from metadata
                - page_count: Estimated page count (based on content length)
                - file_hash: SHA256 hash of file content
                - filename_hash: SHA256 hash of filename
                
        Raises:
            PDFExtractionError: If extraction fails or file is invalid
        """
        from lxml import etree
        
        # Validate file size
        if len(file_content) > cls.MAX_FILE_SIZE:
            raise PDFExtractionError(f"File too large: {len(file_content)} bytes (max {cls.MAX_FILE_SIZE})")
        
        # Compute hashes
        file_hash = cls.compute_hash(file_content)
        filename_hash = cls.compute_hash(filename.encode())
        
        try:
            # Parse XML from memory
            root = etree.fromstring(file_content)
            
            # Define namespace - FDX may or may not have namespace prefixes
            ns = {'fdx': 'http://www.finaldraft.com/fdx'}
            
            # Extract title - try both namespaced and non-namespaced
            title_elem = root.find('.//fdx:Content/fdx:Title', ns) or root.find('.//Content/Title')
            title = title_elem.text if title_elem is not None else None
            
            # If not found in Content, try ShowTitle
            if not title:
                show_title = root.find('.//fdx:ShowTitle', ns) or root.find('.//ShowTitle')
                title = show_title.text if show_title is not None else None
            
            # Extract all paragraphs and format them (try both namespaced and non-namespaced)
            paragraphs = root.findall('.//fdx:Paragraph', ns) or root.findall('.//Paragraph')
            
            formatted_lines = []
            for para in paragraphs:
                # Get paragraph type (Scene Heading, Action, Character, Dialogue, etc.)
                para_type = para.get('Type', 'General')
                
                # Extract text from Text elements (try both namespaced and non-namespaced)
                texts = para.findall('.//fdx:Text', ns) or para.findall('.//Text')
                para_text = ''.join(t.text or '' for t in texts)
                
                if para_text.strip():
                    # Format based on paragraph type
                    if para_type == 'Scene Heading':
                        formatted_lines.append(f"\n{para_text}")
                    elif para_type == 'Character':
                        formatted_lines.append(f"\n{' ' * 20}{para_text}")
                    elif para_type == 'Dialogue':
                        formatted_lines.append(f"{' ' * 10}{para_text}")
                    elif para_type == 'Parenthetical':
                        formatted_lines.append(f"{' ' * 15}({para_text})")
                    else:
                        formatted_lines.append(para_text)
            
            full_text = '\n'.join(formatted_lines)
            
            if not full_text.strip():
                raise PDFExtractionError("No text could be extracted from FDX file")
            
            # Estimate page count (roughly 55 lines per page for screenplays)
            line_count = len([l for l in formatted_lines if l.strip()])
            estimated_pages = max(1, line_count // 55)
            
            return {
                "text": full_text,
                "title": title,
                "page_count": estimated_pages,
                "file_hash": file_hash,
                "filename_hash": filename_hash,
                "format": "fdx"
            }
            
        except etree.XMLSyntaxError as e:
            raise PDFExtractionError(f"Invalid FDX file (XML parse error): {str(e)}")
        except Exception as e:
            raise PDFExtractionError(f"FDX extraction failed: {str(e)}")
    
    @classmethod
    def _detect_title(cls, text: str, first_page) -> Optional[str]:
        """Attempt to detect script title from content.
        
        This is a heuristic that looks for:
        1. Common title page patterns
        2. Text in the first quarter of the first page
        3. All-caps text that's likely a title
        """
        if not text:
            return None
        
        lines = text.split('\n')
        
        # Look at first 30 lines (title page or first page)
        for line in lines[:30]:
            line = line.strip()
            # Skip common non-title lines
            if not line or len(line) < 3:
                continue
            if any(skip in line.upper() for skip in [
                'WRITTEN BY', 'BY', 'AUTHOR', 'DRAFT', 'COPYRIGHT',
                'DATE', 'PAGE', 'FADE IN', 'INT.', 'EXT.'
            ]):
                continue
            # Look for title-like text (all caps, reasonable length)
            if line.upper() == line and 10 <= len(line) <= 80:
                return line.title()
            # Or just return first substantial line
            if len(line) > 10 and not line.startswith('('):
                return line[:80]
        
        return None
    
    @classmethod
    def extract(cls, file_content: bytes, filename: str) -> dict:
        """Extract text from file based on extension.
        
        Args:
            file_content: Raw bytes of the file
            filename: Original filename with extension
            
        Returns:
            Dictionary with extraction results
            
        Raises:
            PDFExtractionError: If extraction fails
        """
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext == 'pdf':
            return cls.extract_pdf(file_content, filename)
        elif ext == 'fdx':
            return cls.extract_fdx(file_content, filename)
        else:
            raise PDFExtractionError(f"Unsupported file format: .{ext}. Use .pdf or .fdx")
