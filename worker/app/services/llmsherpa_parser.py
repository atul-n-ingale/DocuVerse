"""
LLMSherpa Parser Service for structured document parsing.
Supports PDF, HTML, DOCX, PPT, and Markdown files using the LLMSherpa API.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from llmsherpa.readers import LayoutPDFReader

from app.config import NLM_INGESTOR_URL


class LLMSherpaParser:
    """
    LLMSherpa-based document parser for structured content extraction.
    Supports multiple file formats with layout-aware parsing.
    """

    def __init__(self, nlm_ingestor_url: Optional[str] = None):
        """
        Initialize the LLMSherpa parser.

        Args:
            nlm_ingestor_url: URL for the LLMSherpa API service
        """
        self.nlm_ingestor_url = nlm_ingestor_url or NLM_INGESTOR_URL
        self.logger = logging.getLogger(self.__class__.__name__)

        if not self.nlm_ingestor_url:
            raise ValueError("NLM_INGESTOR_URL is required for LLMSherpa parsing")

        # Add required parameters to the API URL
        if "?" not in self.nlm_ingestor_url:
            self.nlm_ingestor_url += "?renderFormat=all&useNewIndentParser=true"
        elif "renderFormat=all" not in self.nlm_ingestor_url:
            self.nlm_ingestor_url += "&renderFormat=all&useNewIndentParser=true"

        # Initialize the LayoutPDFReader with the API URL
        self.pdf_reader = LayoutPDFReader(self.nlm_ingestor_url)

        # Supported file extensions
        self.supported_extensions = {
            ".pdf": self._parse_pdf,
            ".html": self._parse_html,
            ".htm": self._parse_html,
            ".docx": self._parse_docx,
            ".doc": self._parse_docx,
            ".ppt": self._parse_ppt,
            ".pptx": self._parse_ppt,
            ".md": self._parse_markdown,
            ".markdown": self._parse_markdown,
        }

    def parse_document(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse a document and return structured content.

        Args:
            file_path: Path to the document file

        Returns:
            List of parsed content blocks with metadata
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()

        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")

        self.logger.info(f"Parsing document: {file_path} with LLMSherpa")

        try:
            # Call the appropriate parser method
            parser_method = self.supported_extensions[file_extension]
            return parser_method(file_path)
        except Exception as e:
            self.logger.error(f"Error parsing document {file_path}: {str(e)}")
            raise

    def _parse_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse PDF document using LLMSherpa LayoutPDFReader.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of parsed content blocks with hierarchical structure
        """
        try:
            # Use LLMSherpa LayoutPDFReader for structured PDF parsing
            doc = self.pdf_reader.read_pdf(str(file_path))

            # Save the raw LLMSherpa document structure for debugging
            self._save_debug_json(file_path, doc)

            blocks = []
            block_index = 0

            # Extract the JSON structure from LLMSherpa document
            if hasattr(doc, 'json') and doc.json:
                # Process each block from the JSON structure
                for json_block in doc.json:
                    block_data = self._process_json_block(json_block, file_path, block_index)
                    if block_data:
                        blocks.append(block_data)
                        block_index += 1
            else:
                # Fallback to section-based parsing if JSON is not available
                self.logger.warning("JSON structure not available, falling back to section parsing")
                for section in doc.sections():
                    section_text = section.to_text()
                    if section_text.strip():
                        block_data = {
                            "content": section_text,
                            "block_type": "section",
                            "block_index": block_index,
                            "page_number": getattr(section, "page_number", None),
                            "bbox": getattr(section, "bbox", None),
                            "metadata": {
                                "file_path": str(file_path),
                                "file_type": "pdf",
                                "parser": "llmsherpa",
                                "block_type": "section",
                                "section_id": getattr(section, "id", None),
                            },
                        }
                        blocks.append(block_data)
                        block_index += 1

            # If no blocks found, try to get the full document text
            if not blocks:
                full_text = doc.to_text()
                if full_text.strip():
                    block_data = {
                        "content": full_text,
                        "block_type": "document",
                        "block_index": 0,
                        "page_number": None,
                        "bbox": None,
                        "metadata": {
                            "file_path": str(file_path),
                            "file_type": "pdf",
                            "parser": "llmsherpa",
                            "block_type": "document",
                        },
                    }
                    blocks.append(block_data)

            # Save the processed blocks structure for debugging
            self._save_processed_blocks_json(file_path, blocks)

            self.logger.info(f"Parsed {len(blocks)} blocks from PDF: {file_path}")
            return blocks

        except Exception as e:
            self.logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise

    def _process_json_block(self, json_block: Dict[str, Any], file_path: Path, block_index: int) -> Dict[str, Any]:
        """
        Process a single JSON block from LLMSherpa and create appropriate chunk structure.
        
        Args:
            json_block: Raw JSON block from LLMSherpa
            file_path: Path to the PDF file
            block_index: Index of the block
            
        Returns:
            Processed block data with hierarchical structure
        """
        # Extract basic information
        tag = json_block.get("tag", "unknown")
        block_class = json_block.get("block_class", "")
        level = json_block.get("level", 0)
        page_idx = json_block.get("page_idx", 0)
        block_idx = json_block.get("block_idx", 0)
        bbox = json_block.get("bbox", None)
        sentences = json_block.get("sentences", [])
        
        # Combine sentences into content
        content = " ".join(sentences) if sentences else ""
        
        if not content.strip():
            return None
        
        # Determine block type based on tag
        block_type = self._map_tag_to_block_type(tag)
        
        # Create comprehensive metadata for MongoDB storage
        full_metadata = {
            "file_path": str(file_path),
            "file_type": "pdf",
            "parser": "llmsherpa",
            "block_type": block_type,
            "llmsherpa_tag": tag,
            "llmsherpa_block_class": block_class,
            "llmsherpa_level": level,
            "llmsherpa_page_idx": page_idx,
            "llmsherpa_block_idx": block_idx,
            "llmsherpa_bbox": bbox,
            "llmsherpa_sentences": sentences,
            "content_length": len(content),
            "page_number": page_idx + 1,  # Convert to 1-based page numbering
        }
        
        # Create block data structure
        block_data = {
            "content": content,
            "block_type": block_type,
            "block_index": block_index,
            "page_number": page_idx + 1,
            "bbox": bbox,
            "metadata": full_metadata,
        }
        
        return block_data

    def _map_tag_to_block_type(self, tag: str) -> str:
        """
        Map LLMSherpa tags to our block types.
        
        Args:
            tag: LLMSherpa tag (header, para, table, list_item, etc.)
            
        Returns:
            Mapped block type
        """
        tag_mapping = {
            "header": "header",
            "para": "paragraph", 
            "table": "table",
            "list_item": "list_item",
            "figure": "figure",
            "caption": "caption",
            "footnote": "footnote",
            "abstract": "abstract",
            "title": "title",
        }
        
        return tag_mapping.get(tag, "text")

    def _save_debug_json(self, file_path: Path, doc: Any) -> None:
        """Save the raw LLMSherpa document structure to a JSON file for debugging."""
        try:
            # Create debug directory if it doesn't exist
            debug_dir = Path("debug_logs")
            debug_dir.mkdir(exist_ok=True)
            
            # Create filename based on original file
            base_name = file_path.stem
            debug_file = debug_dir / f"{base_name}_llmsherpa_raw.json"
            
            # Extract document structure
            doc_structure = {
                "document_info": {
                    "file_path": str(file_path),
                    "total_sections": len(list(doc.sections())),
                    "full_text_length": len(doc.to_text()),
                    "JSON": doc.json
                },
                "sections": []
            }
            
            # Extract section information
            for i, section in enumerate(doc.sections()):
                section_info = {
                    "section_index": i,
                    "section_id": getattr(section, "id", None),
                    "page_number": getattr(section, "page_number", None),
                    "bbox": getattr(section, "bbox", None),
                    "text_length": len(section.to_text()),
                    "text_preview": section.to_text()[:200] + "..." if len(section.to_text()) > 200 else section.to_text(),
                }
                doc_structure["sections"].append(section_info)
            
            # Save to JSON file
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(doc_structure, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved raw LLMSherpa structure to: {debug_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save debug JSON: {str(e)}")

    def _save_processed_blocks_json(self, file_path: Path, blocks: List[Dict[str, Any]]) -> None:
        """Save the processed blocks structure to a JSON file for debugging."""
        try:
            # Create debug directory if it doesn't exist
            debug_dir = Path("debug_logs")
            debug_dir.mkdir(exist_ok=True)
            
            # Create filename based on original file
            base_name = file_path.stem
            debug_file = debug_dir / f"{base_name}_processed_blocks.json"
            
            # Prepare blocks data for JSON serialization
            blocks_data = {
                "file_info": {
                    "file_path": str(file_path),
                    "total_blocks": len(blocks),
                    "parser": "llmsherpa",
                },
                "blocks": []
            }
            
            # Process each block
            for block in blocks:
                # Create a copy of the block for JSON serialization
                block_copy = block.copy()
                
                # Truncate content for readability
                if "content" in block_copy and len(block_copy["content"]) > 500:
                    block_copy["content_preview"] = block_copy["content"][:500] + "..."
                    block_copy["content_length"] = len(block_copy["content"])
                    # Don't include full content in debug file to keep it manageable
                    del block_copy["content"]
                
                blocks_data["blocks"].append(block_copy)
            
            # Save to JSON file
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(blocks_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved processed blocks structure to: {debug_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to save processed blocks JSON: {str(e)}")

    def _parse_html(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse HTML document using LLMSherpa.

        Args:
            file_path: Path to the HTML file

        Returns:
            List of parsed content blocks
        """
        try:
            # For HTML files, we'll use a simple text extraction approach
            # LLMSherpa might have HTML-specific readers in future versions
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # For now, return the content as a single block
            # This can be enhanced with HTML-specific parsing when available
            return [
                {
                    "content": content,
                    "block_type": "html",
                    "block_index": 0,
                    "page_number": 1,
                    "metadata": {
                        "file_path": str(file_path),
                        "file_type": "html",
                        "parser": "llmsherpa",
                        "block_type": "html",
                    },
                }
            ]

        except Exception as e:
            self.logger.error(f"Error parsing HTML {file_path}: {str(e)}")
            raise

    def _parse_docx(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse DOCX document using LLMSherpa.

        Args:
            file_path: Path to the DOCX file

        Returns:
            List of parsed content blocks
        """
        try:
            # Use LLMSherpa for DOCX parsing if available
            # For now, we'll use a fallback approach
            doc = self.pdf_reader.read_pdf(str(file_path))

            blocks = []
            block_index = 0

            # Process sections from the document
            for section in doc.sections():
                section_text = section.to_text()
                if section_text.strip():
                    block_data = {
                        "content": section_text,
                        "block_type": "section",
                        "block_index": block_index,
                        "page_number": getattr(section, "page_number", None),
                        "metadata": {
                            "file_path": str(file_path),
                            "file_type": "docx",
                            "parser": "llmsherpa",
                            "block_type": "section",
                        },
                    }
                    blocks.append(block_data)
                    block_index += 1

            # If no sections found, try to get the full document text
            if not blocks:
                full_text = doc.to_text()
                if full_text.strip():
                    block_data = {
                        "content": full_text,
                        "block_type": "document",
                        "block_index": 0,
                        "page_number": None,
                        "metadata": {
                            "file_path": str(file_path),
                            "file_type": "docx",
                            "parser": "llmsherpa",
                            "block_type": "document",
                        },
                    }
                    blocks.append(block_data)

            self.logger.info(f"Parsed {len(blocks)} blocks from DOCX: {file_path}")
            return blocks

        except Exception as e:
            self.logger.error(f"Error parsing DOCX {file_path}: {str(e)}")
            raise

    def _parse_ppt(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse PPT/PPTX document using LLMSherpa.

        Args:
            file_path: Path to the PPT/PPTX file

        Returns:
            List of parsed content blocks
        """
        try:
            # Use LLMSherpa for PPT parsing if available
            doc = self.pdf_reader.read_pdf(str(file_path))

            blocks = []
            block_index = 0

            # Process sections from the document
            for section in doc.sections():
                section_text = section.to_text()
                if section_text.strip():
                    block_data = {
                        "content": section_text,
                        "block_type": "section",
                        "block_index": block_index,
                        "page_number": getattr(section, "page_number", None),
                        "metadata": {
                            "file_path": str(file_path),
                            "file_type": "ppt",
                            "parser": "llmsherpa",
                            "block_type": "section",
                        },
                    }
                    blocks.append(block_data)
                    block_index += 1

            # If no sections found, try to get the full document text
            if not blocks:
                full_text = doc.to_text()
                if full_text.strip():
                    block_data = {
                        "content": full_text,
                        "block_type": "document",
                        "block_index": 0,
                        "page_number": None,
                        "metadata": {
                            "file_path": str(file_path),
                            "file_type": "ppt",
                            "parser": "llmsherpa",
                            "block_type": "document",
                        },
                    }
                    blocks.append(block_data)

            self.logger.info(f"Parsed {len(blocks)} blocks from PPT: {file_path}")
            return blocks

        except Exception as e:
            self.logger.error(f"Error parsing PPT {file_path}: {str(e)}")
            raise

    def _parse_markdown(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse Markdown document.

        Args:
            file_path: Path to the Markdown file

        Returns:
            List of parsed content blocks
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # For Markdown, we'll return the content as a single block
            # This can be enhanced with Markdown-specific parsing if needed
            return [
                {
                    "content": content,
                    "block_type": "markdown",
                    "block_index": 0,
                    "page_number": 1,
                    "metadata": {
                        "file_path": str(file_path),
                        "file_type": "markdown",
                        "parser": "llmsherpa",
                        "block_type": "markdown",
                    },
                }
            ]

        except Exception as e:
            self.logger.error(f"Error parsing Markdown {file_path}: {str(e)}")
            raise

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions
        """
        return list(self.supported_extensions.keys())

    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file format is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if the file format is supported
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_extensions
