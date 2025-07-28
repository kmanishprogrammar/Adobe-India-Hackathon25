import os
import re
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class DocumentExtractor:
    def __init__(self):
        self.min_title_font_size = 12  # Minimum font size for title
        self.min_heading_font_size = 10  # Minimum font size for headings
    
    def extract_document_structure(self, pdf_path):
        """
        Extract title and headings from a PDF document using PyMuPDF.
        """
        # Initialize the result structure
        result = {
            "title": "Unknown Title",
            "outline": []
        }
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Extract title
            result["title"] = self._extract_title(doc)
            
            # Extract headings
            result["outline"] = self._extract_headings(doc)
            
            # Close the document
            doc.close()
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
        
        return result
    
    def _extract_title(self, doc):
        """
        Extract the title from a PDF document.
        Strategy:
        1. Try to get title from document metadata
        2. If not available, look at the first page for text with largest font size
        """
        title = "Unknown Title"
        
        # Try to get title from metadata
        metadata = doc.metadata
        if metadata.get("title") and metadata.get("title").strip():
            title = metadata["title"].strip()
            return title
        
        # If no title in metadata, try to extract from first page
        if doc.page_count > 0:
            first_page = doc[0]
            text_blocks = first_page.get_text("dict")["blocks"]
            
            # Sort blocks by font size (descending)
            text_blocks = sorted(
                [b for b in text_blocks if "lines" in b],
                key=lambda b: max([max([span["size"] for span in line["spans"]]) for line in b["lines"]]),
                reverse=True
            )
            
            # Get the first block with the largest font size
            if text_blocks:
                largest_block = text_blocks[0]
                title_text = ""
                for line in largest_block["lines"]:
                    for span in line["spans"]:
                        title_text += span["text"]
                    title_text += " "
                
                if title_text.strip():
                    title = title_text.strip()
                    
                    # Clean up the title
                    title = self._clean_title(title)
                    
                    # If title is too long, it might be a paragraph, not a title
                    if len(title) > 100 and len(text_blocks) > 1:
                        # Try the second largest text block
                        second_block = text_blocks[1]
                        second_title = ""
                        for line in second_block["lines"]:
                            for span in line["spans"]:
                                second_title += span["text"]
                            second_title += " "
                        
                        if second_title.strip() and len(second_title) < len(title):
                            title = self._clean_title(second_title.strip())
        
        return title
    
    def _clean_title(self, title):
        """
        Clean up the title text.
        """
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common prefixes like "Title:" or "Document:"
        title = re.sub(r'^(Title|Document|Subject|Name):\s*', '', title, flags=re.IGNORECASE)
        
        return title
    
    def _extract_headings(self, doc):
        """
        Extract headings from a PDF document.
        Strategy:
        1. Try to use document's table of contents (TOC)
        2. If not available, extract headings based on font properties
        """
        headings = []
        
        # Try to get headings from TOC
        toc = doc.get_toc(simple=False)
        
        # If TOC exists, use it directly
        if toc:
            for level, title, page, dest in toc:
                if 1 <= level <= 3:  # Only consider H1, H2, H3
                    heading_level = f"H{level}"
                    headings.append({
                        "level": heading_level,
                        "text": title,
                        "page": page
                    })
        else:
            # If no TOC, extract headings based on font properties
            font_sizes = {}
            heading_candidates = []
            
            # Collect all text blocks with their font sizes
            for page_num in range(doc.page_count):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                    
                    for line in block["lines"]:
                        if not line["spans"]:
                            continue
                        
                        # Get the maximum font size in this line
                        max_size = max([span["size"] for span in line["spans"]])
                        
                        # Check if any span is bold
                        is_bold = any(["bold" in span["font"].lower() for span in line["spans"]])
                        
                        # Combine all text in this line
                        text = "".join([span["text"] for span in line["spans"]]).strip()
                        
                        # Skip empty lines or very long text (likely paragraphs)
                        if not text or len(text) > 200:
                            continue
                        
                        # Skip page numbers and common footers
                        if text.isdigit() or text.startswith("Page ") or self._is_page_number_or_footer(text):
                            continue
                        
                        # Add font size to the collection
                        font_sizes[max_size] = font_sizes.get(max_size, 0) + 1
                        
                        # Add to heading candidates
                        heading_candidates.append({
                            "text": text,
                            "size": max_size,
                            "bold": is_bold,
                            "page": page_num + 1  # 1-indexed page numbers
                        })
            
            # Determine heading levels based on font sizes
            if heading_candidates:
                # Sort font sizes in descending order
                sorted_sizes = sorted(font_sizes.keys(), reverse=True)
                
                # Map top 3 sizes to heading levels
                size_to_level = {}
                for i, size in enumerate(sorted_sizes[:3]):
                    size_to_level[size] = f"H{i+1}"
                
                # Assign heading levels
                for candidate in heading_candidates:
                    if candidate["size"] in size_to_level:
                        level = size_to_level[candidate["size"]]
                        # Promote level if bold
                        if candidate["bold"] and level != "H1":
                            level_num = int(level[1])
                            level = f"H{max(1, level_num - 1)}"
                        
                        # Clean heading text
                        text = self._clean_heading_text(candidate["text"])
                        
                        headings.append({
                            "level": level,
                            "text": text,
                            "page": candidate["page"]
                        })
        
        return headings
    
    def _is_page_number_or_footer(self, text):
        """
        Check if the text is likely a page number or footer.
        """
        # Check if it's just a number
        if re.match(r'^\d+$', text):
            return True
        
        # Check for common footer patterns
        footer_patterns = [
            r'^Page \d+( of \d+)?$',
            r'^\d+/\d+$',
            r'^Copyright',
            r'^All rights reserved',
            r'^Confidential'
        ]
        
        for pattern in footer_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _clean_heading_text(self, text):
        """
        Clean up heading text.
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common heading prefixes like "Chapter 1:" or "Section 1.2:"
        text = re.sub(r'^(Chapter|Section|Part)\s+[\d\.]+[:\.]?\s*', '', text, flags=re.IGNORECASE)
        
        # Remove trailing periods if they exist
        text = re.sub(r'\.$', '', text)
        
        return text