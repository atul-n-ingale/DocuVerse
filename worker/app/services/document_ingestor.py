"""
DocumentIngestor: Hybrid ingestion using LLMSherpa for parsing and LlamaIndex for vectorization.
Supports PDF, HTML, DOCX, PPT, Markdown, image, and CSV files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union, cast

import requests
from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.file import CSVReader, ImageReader
from llama_index.vector_stores.pinecone import PineconeVectorStore

from app.config import BACKEND_URL, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX
from app.core.lib.llamaindex import (
    CustomHierarchicalNodeParser,
    CustomPineconeVectorStore,
)
from app.core.progress_manager import ProgressManager
from app.services.llmsherpa_parser import LLMSherpaParser


class DocumentIngestor:
    """
    Document ingestion service using hybrid approach (LLMSherpa + LlamaIndex).

    This class handles document ingestion with the following features:
    - LLMSherpa for structured parsing of PDF, HTML, DOCX, PPT, Markdown
    - LlamaIndex for other formats (images, CSV)
    - Hybrid storage: vectors in Pinecone, metadata in MongoDB via backend API
    - Metadata filtering for Pinecone compatibility
    """

    def __init__(
        self,
        document_id: str,
        file_path: str,
        progress_manager: Optional[ProgressManager] = None,
    ):
        """Initialize DocumentIngestor with document ID and file path."""
        self.document_id = document_id
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        self.progress_manager = progress_manager

        # Store full metadata separately for backend storage
        self.full_metadata_store: Dict[int, Dict[str, Any]] = {}

        # Initialize LLMSherpa parser
        self.llmsherpa_parser = LLMSherpaParser()

        # Get progress callback if available
        progress_callback = None
        if self.progress_manager:
            progress_callback = self.progress_manager.get_progress_callback()

        # Initialize custom LlamaIndex components
        self.chunker = CustomHierarchicalNodeParser.from_defaults(
            chunk_sizes=[4096, 2048, 1024],
            chunk_overlap=100,
            progress_callback=progress_callback,
        )

        # Initialize custom Pinecone vector store
        self.vector_store = CustomPineconeVectorStore(
            index_name=PINECONE_INDEX,
            api_key=PINECONE_API_KEY,
            environment="gcp-starter",
            namespace="",
            insert_kwargs={},
            add_sparse_vector=False,
            text_key="text",
            batch_size=100,
            remove_text_from_metadata=False,
            progress_callback=progress_callback,
        )

        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )

        # Initialize ingestion pipeline
        self.pipeline = IngestionPipeline(
            transformations=[
                self.chunker,
                self.embed_model,
            ],
            vector_store=self.vector_store,
        )

        # File readers for different formats
        self.llama_readers = {
            ".png": ImageReader(),
            ".jpg": ImageReader(),
            ".jpeg": ImageReader(),
            ".csv": CSVReader(),
        }

    def ingest(self) -> int:
        """
        Ingest document using hybrid approach (LLMSherpa + LlamaIndex).
        Returns the number of chunks created.
        """
        self.logger.info(f"Starting hybrid ingestion for {self.file_path}")

        # Start progress tracking
        if self.progress_manager:
            self.progress_manager.start_stage("parsing")

        try:
            file_extension = Path(self.file_path).suffix.lower()

            # Use LLMSherpa for supported formats
            if self.llmsherpa_parser.is_supported(self.file_path):
                self.logger.info(f"Using LLMSherpa parser for {file_extension}")
                nodes = self._ingest_with_llmsherpa()
            else:
                # Use LlamaIndex for other formats
                self.logger.info(f"Using LlamaIndex reader for {file_extension}")
                nodes = self._ingest_with_llama_index()

            # Complete parsing stage
            if self.progress_manager:
                self.progress_manager.complete_stage("parsing")

            # Set node IDs and metadata
            for i, node in enumerate(nodes):
                old_id = node.node_id
                if old_id:
                    node.node_id = f"{self.document_id}::chunk_{i}::{old_id}"
                else:
                    node.node_id = f"{self.document_id}::chunk_{i}"
                node.metadata["chunk_index"] = i
                node.metadata["document_id"] = self.document_id
                node.metadata["source_file"] = self.file_path

            # Start storage stage
            if self.progress_manager:
                self.progress_manager.start_stage("storage")

            # Run the pipeline - this will embed and store vectors in Pinecone
            embedded_nodes = self.pipeline.run(nodes=nodes)

            # Complete storage stage
            if self.progress_manager:
                self.progress_manager.complete_stage("storage")
            self.logger.info(
                f"Processed {len(nodes)} nodes for document {self.document_id}"
            )

            # Store comprehensive metadata in backend database via API
            self._store_metadata_in_backend(embedded_nodes)

            # Send completion notification with chunks data
            if self.progress_manager:
                chunks_data = self._prepare_chunks_for_completion(embedded_nodes)
                # Use the merged report_status_to_backend method
                self.progress_manager.send_final_progress_update(
                    "completed", chunks=chunks_data
                )

            return len(nodes)

        except Exception as e:
            self.logger.error(f"Error during ingestion: {str(e)}", exc_info=True)
            if self.progress_manager:
                self.progress_manager.send_final_progress_update("failed", error=str(e))
            raise

    def _filter_metadata_for_pinecone(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter metadata to only include Pinecone-compatible fields.
        Pinecone only accepts string, number, boolean, or list of strings.

        Args:
            metadata: Original metadata dictionary

        Returns:
            Filtered metadata compatible with Pinecone
        """
        filtered_metadata: Dict[str, Any] = {}

        # Essential metadata for search and retrieval
        essential_keys = [
            "document_id",
            "content_type",
            "block_type",
            "block_index",
            "page_number",
            "hierarchical_level",
            "importance_score",
            "llmsherpa_tag",
            "llmsherpa_block_class",
            "llmsherpa_level",
        ]

        for key in essential_keys:
            if key in metadata:
                value = metadata[key]
                if isinstance(value, (str, int, float, bool)):
                    filtered_metadata[key] = value
                elif value is not None:
                    filtered_metadata[key] = str(value)

        # Add any other compatible metadata
        for key, value in metadata.items():
            if key in essential_keys:
                continue  # Already processed

            # Skip complex objects that Pinecone doesn't support
            if key in [
                "bbox",
                "table_data",
                "image_info",
                "llmsherpa_bbox",
                "llmsherpa_sentences",
            ]:
                continue

            # Convert values to Pinecone-compatible types
            if isinstance(value, (str, int, float, bool)):
                filtered_metadata[key] = value
            elif isinstance(value, list):
                # Only include lists of strings
                if all(isinstance(item, str) for item in value):
                    filtered_metadata[key] = value
            elif value is not None:
                # Convert other types to string
                filtered_metadata[key] = str(value)

        return filtered_metadata

    def _store_full_metadata(self, documents: List[Document]) -> None:
        """
        Store full metadata from hierarchical documents for backend storage.

        Args:
            documents: List of LlamaIndex Document objects with full metadata
        """
        for i, doc in enumerate(documents):
            # Store full metadata for backend storage
            full_metadata = {
                "document_id": self.document_id,
                "file_path": self.file_path,
                "parser": "llmsherpa",
                "text_length": len(doc.text),
                "created_at": datetime.utcnow().isoformat(),
                "file_name": Path(self.file_path).name,
                **doc.metadata,  # Include all hierarchical metadata
            }

            # Store in class-level metadata store for backend storage
            self.full_metadata_store[i] = full_metadata

    def _ingest_with_llmsherpa(self) -> List[Any]:
        """
        Ingest document using LLMSherpa parser with hierarchical chunking.

        Returns:
            List of processed nodes with embeddings
        """
        try:
            # Parse document content using LLMSherpa
            if self.progress_manager:
                self.progress_manager.update_stage_progress(
                    "Parsing document with LLMSherpa", 0, 1
                )

            blocks = self.llmsherpa_parser.parse_document(self.file_path)

            if self.progress_manager:
                self.progress_manager.update_stage_progress(
                    f"Parsed {len(blocks)} blocks", 1, 1
                )

            # Convert blocks to LlamaIndex documents with hierarchical structure
            if self.progress_manager:
                self.progress_manager.start_stage("chunking")

            # Create documents with filtered metadata to avoid chunking issues
            documents = self._create_hierarchical_chunks_with_filtered_metadata(
                blocks, self.document_id
            )

            if self.progress_manager:
                self.progress_manager.complete_stage("chunking")

            # Store full metadata for backend storage
            self._store_full_metadata(documents)

            # Chunk the documents
            if self.progress_manager:
                self.progress_manager.start_stage("embedding")

            nodes = self.chunker.get_nodes_from_documents(documents)

            if self.progress_manager:
                self.progress_manager.complete_stage("embedding")

            return nodes

        except Exception as e:
            self.logger.error(f"Error in LLMSherpa ingestion: {str(e)}")
            if self.progress_manager:
                self.progress_manager.send_final_progress_update(
                    "failed", error=f"LLMSherpa ingestion failed: {str(e)}"
                )
            raise

    def _create_hierarchical_chunks_with_filtered_metadata(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """
        Create hierarchical chunks with filtered metadata to avoid chunking issues.

        Args:
            blocks: List of parsed blocks from LLMSherpa
            document_id: ID of the document being processed

        Returns:
            List of LlamaIndex Document objects with filtered metadata
        """
        # First create documents with full metadata for backend storage
        full_documents = self._create_hierarchical_chunks(blocks, document_id)

        # Store full metadata for backend
        self._store_full_metadata(full_documents)

        # Create documents with filtered metadata for chunking
        filtered_documents = []
        for i, doc in enumerate(full_documents):
            # Filter metadata to avoid chunking issues
            filtered_metadata = self._filter_metadata_for_chunking(doc.metadata)

            # Debug: Log metadata sizes
            original_size = len(str(doc.metadata))
            filtered_size = len(str(filtered_metadata))
            self.logger.info(
                f"Document {i}: Original metadata size: {original_size}, Filtered: {filtered_size}"
            )

            # Create new document with filtered metadata
            filtered_doc = Document(
                text=doc.text,
                metadata=filtered_metadata,
                relationships=doc.relationships,
            )
            filtered_documents.append(filtered_doc)

        return filtered_documents

    def _filter_metadata_for_chunking(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter metadata to absolute minimum for chunking to avoid size issues.

        Args:
            metadata: Original metadata dictionary

        Returns:
            Minimal metadata for chunking (only essential fields)
        """
        # Keep only the absolute minimum metadata for chunking
        # This ensures metadata is always smaller than chunk sizes
        minimal_keys = ["document_id", "content_type", "hierarchical_level"]

        filtered_metadata = {}
        for key in minimal_keys:
            if key in metadata:
                value = metadata[key]
                # Convert all values to strings to minimize size
                if value is not None:
                    filtered_metadata[key] = str(value)[:50]  # Limit string length

        # Add a simple identifier
        filtered_metadata["chunk_id"] = (
            f"chunk_{hash(str(metadata.get('document_id', '')))}"
        )

        # Safety check: ensure metadata is smaller than smallest chunk size (1024)
        metadata_str = str(filtered_metadata)
        if len(metadata_str) > 800:  # Leave some buffer
            self.logger.warning(
                f"Metadata still too large ({len(metadata_str)} chars), truncating..."
            )
            # Keep only the most essential fields
            filtered_metadata = {
                "document_id": str(metadata.get("document_id", ""))[:20],
                "content_type": str(metadata.get("content_type", ""))[:20],
                "chunk_id": f"chunk_{hash(str(metadata.get('document_id', '')))}",
            }

        return filtered_metadata

    def _create_hierarchical_chunks(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """
        Create hierarchical chunks based on LLMSherpa structure and LlamaIndex best practices.

        Args:
            blocks: Parsed content blocks from LLMSherpa
            document_id: Document identifier

        Returns:
            List of LlamaIndex Document objects with proper hierarchical structure
        """
        documents: List[Document] = []

        # Group blocks by content type for hierarchical processing
        content_groups = self._group_blocks_by_type(blocks)

        # Create hierarchical structure based on LLMSherpa levels
        hierarchical_docs = self._create_llmsherpa_hierarchy(
            content_groups, document_id
        )

        # Set up proper relationships for modern LlamaIndex compatibility
        self._setup_document_relationships(hierarchical_docs, document_id)

        self.logger.info(
            f"Created {len(hierarchical_docs)} hierarchical documents from {len(blocks)} blocks"
        )
        return hierarchical_docs

    def _setup_document_relationships(
        self, documents: List[Document], document_id: str
    ) -> None:
        """
        Set up proper relationships for modern LlamaIndex compatibility.
        Uses relationships field instead of deprecated ref_doc_id.

        Args:
            documents: List of Document objects
            document_id: Document identifier
        """
        from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

        # Create a source document node info
        source_node_info = RelatedNodeInfo(
            node_id=document_id,
            node_type="document",
            metadata={"document_id": document_id},
        )

        # Set up relationships for each document
        for doc in documents:
            # Set the source relationship (modern approach)
            doc.relationships[NodeRelationship.SOURCE] = source_node_info

            # Also keep document_id in metadata for backward compatibility
            doc.metadata["document_id"] = document_id

    def _create_llmsherpa_hierarchy(
        self, content_groups: Dict[str, List[Dict[str, Any]]], document_id: str
    ) -> List[Document]:
        """
        Create hierarchical structure based on LLMSherpa block types and levels.

        Args:
            content_groups: Blocks grouped by content type
            document_id: Document identifier

        Returns:
            List of Document objects with hierarchical relationships
        """
        documents = []

        # Process headers first (highest level - 0)
        if content_groups["headers"]:
            header_docs = self._process_headers_hierarchical(
                content_groups["headers"], document_id
            )
            documents.extend(header_docs)

        # Process paragraphs (level 1)
        if content_groups["paragraphs"]:
            paragraph_docs = self._process_paragraphs_hierarchical(
                content_groups["paragraphs"], document_id
            )
            documents.extend(paragraph_docs)

        # Process tables (level 1)
        if content_groups["tables"]:
            table_docs = self._process_tables_hierarchical(
                content_groups["tables"], document_id
            )
            documents.extend(table_docs)

        # Process lists (level 2)
        if content_groups["lists"]:
            list_docs = self._process_lists_hierarchical(
                content_groups["lists"], document_id
            )
            documents.extend(list_docs)

        # Process other content (level 3)
        if content_groups["other"]:
            other_docs = self._process_other_blocks_hierarchical(
                content_groups["other"], document_id
            )
            documents.extend(other_docs)

        return documents

    def _group_blocks_by_type(
        self, blocks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group blocks by their content type for specialized processing.

        Args:
            blocks: Parsed content blocks

        Returns:
            Dictionary of blocks grouped by content type
        """
        groups: Dict[str, List[Dict[str, Any]]] = {
            "headers": [],
            "paragraphs": [],
            "tables": [],
            "lists": [],
            "other": [],
        }

        for block in blocks:
            block_type = block.get("block_type", "other")

            if block_type == "header":
                groups["headers"].append(block)
            elif block_type == "paragraph":
                groups["paragraphs"].append(block)
            elif block_type == "table":
                groups["tables"].append(block)
            elif block_type == "list_item":
                groups["lists"].append(block)
            else:
                groups["other"].append(block)

        # Log grouping statistics
        for content_type, type_blocks in groups.items():
            if type_blocks:
                self.logger.info(f"Grouped {len(type_blocks)} {content_type}")

        return groups

    def _process_headers_hierarchical(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """Process header blocks with proper hierarchical level (0)."""
        documents = []

        for i, block in enumerate(blocks):
            # Create document with header-specific metadata and level 0
            doc = Document(
                text=block["content"],
                metadata={
                    "document_id": document_id,
                    "content_type": "header",
                    "block_type": "header",
                    "block_index": block.get("block_index", i),
                    "page_number": block.get("page_number", 1),
                    "hierarchical_level": 0,  # Highest level
                    "importance_score": 0.9,
                    "llmsherpa_tag": block.get("metadata", {}).get(
                        "llmsherpa_tag", "header"
                    ),
                    "llmsherpa_block_class": block.get("metadata", {}).get(
                        "llmsherpa_block_class", ""
                    ),
                    "llmsherpa_level": block.get("metadata", {}).get(
                        "llmsherpa_level", 0
                    ),
                    "llmsherpa_bbox": block.get("metadata", {}).get("llmsherpa_bbox"),
                    "llmsherpa_sentences": block.get("metadata", {}).get(
                        "llmsherpa_sentences", []
                    ),
                    "ref_doc_id": document_id,  # For Pinecone integration
                },
            )
            documents.append(doc)

        return documents

    def _process_paragraphs_hierarchical(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """Process paragraph blocks with hierarchical level (1)."""
        documents = []

        # Group paragraphs by page for better organization
        page_groups: Dict[int, List[Dict[str, Any]]] = {}
        for block in blocks:
            page = block.get("page_number", 1)
            if page not in page_groups:
                page_groups[page] = []
            page_groups[page].append(block)

        for page, page_blocks in page_groups.items():
            # Sort by block index for proper order
            page_blocks.sort(key=lambda x: x.get("block_index", 0))

            for i, block in enumerate(page_blocks):
                doc = Document(
                    text=block["content"],
                    metadata={
                        "document_id": document_id,
                        "content_type": "paragraph",
                        "block_type": "paragraph",
                        "block_index": block.get("block_index", i),
                        "page_number": page,
                        "hierarchical_level": 1,  # Medium level
                        "importance_score": 0.7,
                        "llmsherpa_tag": block.get("metadata", {}).get(
                            "llmsherpa_tag", "para"
                        ),
                        "llmsherpa_block_class": block.get("metadata", {}).get(
                            "llmsherpa_block_class", ""
                        ),
                        "llmsherpa_level": block.get("metadata", {}).get(
                            "llmsherpa_level", 1
                        ),
                        "llmsherpa_bbox": block.get("metadata", {}).get(
                            "llmsherpa_bbox"
                        ),
                        "llmsherpa_sentences": block.get("metadata", {}).get(
                            "llmsherpa_sentences", []
                        ),
                        "ref_doc_id": document_id,
                    },
                )
                documents.append(doc)

        return documents

    def _process_tables_hierarchical(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """Process table blocks with hierarchical level (1)."""
        documents = []

        for i, block in enumerate(blocks):
            doc = Document(
                text=block["content"],
                metadata={
                    "document_id": document_id,
                    "content_type": "table",
                    "block_type": "table",
                    "block_index": block.get("block_index", i),
                    "page_number": block.get("page_number", 1),
                    "hierarchical_level": 1,  # Medium level
                    "importance_score": 0.8,
                    "llmsherpa_tag": block.get("metadata", {}).get(
                        "llmsherpa_tag", "table"
                    ),
                    "llmsherpa_block_class": block.get("metadata", {}).get(
                        "llmsherpa_block_class", ""
                    ),
                    "llmsherpa_level": block.get("metadata", {}).get(
                        "llmsherpa_level", 1
                    ),
                    "llmsherpa_bbox": block.get("metadata", {}).get("llmsherpa_bbox"),
                    "llmsherpa_sentences": block.get("metadata", {}).get(
                        "llmsherpa_sentences", []
                    ),
                    "ref_doc_id": document_id,
                },
            )
            documents.append(doc)

        return documents

    def _process_lists_hierarchical(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """Process list item blocks with hierarchical level (2)."""
        documents = []

        # Group list items by page
        page_groups: Dict[int, List[Dict[str, Any]]] = {}
        for block in blocks:
            page = block.get("page_number", 1)
            if page not in page_groups:
                page_groups[page] = []
            page_groups[page].append(block)

        for page, page_blocks in page_groups.items():
            # Sort by block index for proper order
            page_blocks.sort(key=lambda x: x.get("block_index", 0))

            for i, block in enumerate(page_blocks):
                doc = Document(
                    text=block["content"],
                    metadata={
                        "document_id": document_id,
                        "content_type": "list_item",
                        "block_type": "list_item",
                        "block_index": block.get("block_index", i),
                        "page_number": page,
                        "hierarchical_level": 2,  # Lower level
                        "importance_score": 0.6,
                        "llmsherpa_tag": block.get("metadata", {}).get(
                            "llmsherpa_tag", "list_item"
                        ),
                        "llmsherpa_block_class": block.get("metadata", {}).get(
                            "llmsherpa_block_class", ""
                        ),
                        "llmsherpa_level": block.get("metadata", {}).get(
                            "llmsherpa_level", 2
                        ),
                        "llmsherpa_bbox": block.get("metadata", {}).get(
                            "llmsherpa_bbox"
                        ),
                        "llmsherpa_sentences": block.get("metadata", {}).get(
                            "llmsherpa_sentences", []
                        ),
                        "ref_doc_id": document_id,
                    },
                )
                documents.append(doc)

        return documents

    def _process_other_blocks_hierarchical(
        self, blocks: List[Dict[str, Any]], document_id: str
    ) -> List[Document]:
        """Process other block types with hierarchical level (3)."""
        documents = []

        for i, block in enumerate(blocks):
            doc = Document(
                text=block["content"],
                metadata={
                    "document_id": document_id,
                    "content_type": "other",
                    "block_type": block.get("block_type", "unknown"),
                    "block_index": block.get("block_index", i),
                    "page_number": block.get("page_number", 1),
                    "hierarchical_level": 3,  # Lowest level
                    "importance_score": 0.5,
                    "llmsherpa_tag": block.get("metadata", {}).get(
                        "llmsherpa_tag", "unknown"
                    ),
                    "llmsherpa_block_class": block.get("metadata", {}).get(
                        "llmsherpa_block_class", ""
                    ),
                    "llmsherpa_level": block.get("metadata", {}).get(
                        "llmsherpa_level", 3
                    ),
                    "llmsherpa_bbox": block.get("metadata", {}).get("llmsherpa_bbox"),
                    "llmsherpa_sentences": block.get("metadata", {}).get(
                        "llmsherpa_sentences", []
                    ),
                    "ref_doc_id": document_id,
                },
            )
            documents.append(doc)

        return documents

    def _ingest_with_llama_index(self) -> List[Any]:
        """
        Ingest document using LlamaIndex readers.

        Returns:
            List of LlamaIndex nodes
        """
        # Get appropriate reader
        reader = self._get_llama_reader()
        docs = reader.load_data(Path(self.file_path))
        self.logger.info(f"Loaded {len(docs)} document(s) with LlamaIndex")

        # Chunk the documents
        nodes = self.chunker.get_nodes_from_documents(docs)
        return nodes

    def _get_llama_reader(self) -> Union[ImageReader, CSVReader]:
        """Get appropriate LlamaIndex reader based on file extension."""
        file_path = Path(self.file_path)
        file_extension = file_path.suffix.lower()

        if file_extension not in self.llama_readers:
            raise ValueError(f"Unsupported file type: {file_extension}")

        return cast(Union[ImageReader, CSVReader], self.llama_readers[file_extension])

    def _prepare_chunks_for_completion(
        self, nodes: Sequence[Any]
    ) -> List[Dict[str, Any]]:
        """
        Prepare chunks data for completion notification.

        Args:
            nodes: List of processed nodes

        Returns:
            List of chunk data dictionaries
        """
        chunks_data = []
        for node in nodes:
            chunk_data = {
                "content": node.text,
                "chunk_index": node.metadata.get("chunk_index", 0),
                "document_id": self.document_id,
                "metadata": {
                    "chunk_index": node.metadata.get("chunk_index", 0),
                    "document_id": self.document_id,
                    "content_type": node.metadata.get("content_type", "unknown"),
                    "block_type": node.metadata.get("block_type", "unknown"),
                    "hierarchical_level": node.metadata.get("hierarchical_level", 0),
                    "importance_score": node.metadata.get("importance_score", 0.5),
                    "page_number": node.metadata.get("page_number", 1),
                    "llmsherpa_tag": node.metadata.get("llmsherpa_tag", ""),
                    "llmsherpa_block_class": node.metadata.get(
                        "llmsherpa_block_class", ""
                    ),
                    "llmsherpa_level": node.metadata.get("llmsherpa_level", 0),
                },
            }
            chunks_data.append(chunk_data)

        return chunks_data

    def _store_metadata_in_backend(self, nodes: Sequence[Any]) -> None:
        """Store comprehensive metadata in backend database via API."""
        file_extension = Path(self.file_path).suffix.lower()
        file_stats = Path(self.file_path).stat()

        # Prepare chunks data for backend API
        chunks_data = []
        for i, node in enumerate(nodes):
            # Use full metadata if available from class-level store (LLMSherpa), otherwise build basic metadata
            if i in self.full_metadata_store:
                # Use the full metadata from LLMSherpa parsing
                full_metadata = self.full_metadata_store[i].copy()
                # Add additional file-level metadata
                full_metadata.update(
                    {
                        "file_size": file_stats.st_size,
                        "file_modified": datetime.fromtimestamp(
                            file_stats.st_mtime
                        ).isoformat(),
                        "text_length": len(node.text),
                        "source": "document_ingestor",
                        "created_at": datetime.utcnow().isoformat(),
                        "file_name": Path(self.file_path).name,
                    }
                )
            else:
                # Build basic metadata for non-LLMSherpa documents
                full_metadata = {
                    "file_path": self.file_path,
                    "file_type": file_extension,
                    "file_size": file_stats.st_size,
                    "file_modified": datetime.fromtimestamp(
                        file_stats.st_mtime
                    ).isoformat(),
                    "text_length": len(node.text),
                    "source": "document_ingestor",
                    "created_at": datetime.utcnow().isoformat(),
                    "page_label": getattr(node, "metadata", {}).get("page_label", None),
                    "file_name": Path(self.file_path).name,
                    "parser": node.metadata.get("parser", "llama_index"),
                    "block_type": node.metadata.get("block_type", None),
                    "block_index": node.metadata.get("block_index", None),
                    "page_number": node.metadata.get("page_number", None),
                }

            chunk_data = {
                "content": node.text,
                "chunk_index": i,
                "document_id": self.document_id,
                "embedding_id": f"{self.document_id}::chunk_{i}",
                "metadata": full_metadata,
            }
            chunks_data.append(chunk_data)

        # Send to backend API for storage
        self._send_chunks_to_backend(chunks_data)

    def _send_chunks_to_backend(self, chunks_data: List[Dict[str, Any]]) -> None:
        """Send chunks data to backend API for storage."""
        try:
            # Use the existing worker status endpoint to save chunks
            payload = {
                "task_id": f"task_{self.document_id}",
                "document_id": self.document_id,
                "status": "completed",
                "chunks": chunks_data,
                "error": None,
            }

            response = requests.post(
                f"{BACKEND_URL}/worker/status", json=payload, timeout=30
            )

            if response.status_code == 200:
                self.logger.info(
                    f"Successfully stored metadata for {len(chunks_data)} chunks in backend"
                )
            else:
                self.logger.error(
                    f"Failed to store metadata in backend. Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                raise Exception(f"Backend API error: {response.status_code}")

        except Exception as e:
            self.logger.error(
                f"Error sending chunks to backend: {str(e)}", exc_info=True
            )
            raise

    @staticmethod
    def get_chunks_metadata_from_backend(
        chunk_ids: List[str], backend_url: str = BACKEND_URL
    ) -> List[Dict[str, Any]]:
        """
        Get chunks metadata from backend database.

        Args:
            chunk_ids: List of chunk IDs to retrieve
            backend_url: Backend API URL

        Returns:
            List of chunk metadata from backend
        """
        try:
            # This would be implemented as a new endpoint in the backend
            # For now, we'll use the existing document chunks endpoint
            response = requests.get(
                f"{backend_url}/documents/chunks",
                params={"chunk_ids": ",".join(chunk_ids)},
                timeout=10,
            )

            if response.status_code == 200:
                return cast(List[Dict[str, Any]], response.json())
            else:
                logging.error(f"Failed to get chunks metadata: {response.status_code}")
                return []

        except Exception as e:
            logging.error(f"Error getting chunks metadata: {str(e)}")
            return []

    @staticmethod
    def augment_vectors_with_metadata(
        vector_results: List[Any], backend_url: str = BACKEND_URL
    ) -> List[Dict[str, Any]]:
        """
        Augment vector search results with metadata from backend database.

        Args:
            vector_results: List of vector search results from Pinecone
            backend_url: Backend API URL

        Returns:
            List of augmented results with full metadata
        """
        augmented_results = []

        try:
            # Extract chunk IDs from vector results
            chunk_ids = []
            for result in vector_results:
                chunk_id = result.node.metadata.get("chunk_id", None)
                if not chunk_id:
                    # Try to construct chunk_id from other metadata
                    extracted_document_id = result.node.metadata.get("document_id", "")
                    chunk_index = result.node.metadata.get("chunk_index", 0)
                    chunk_id = f"{extracted_document_id}::chunk_{chunk_index}"
                chunk_ids.append(chunk_id)

            # Get metadata from backend
            metadata_docs = DocumentIngestor.get_chunks_metadata_from_backend(
                chunk_ids, backend_url
            )

            # Create a lookup dictionary
            metadata_lookup = {
                doc.get("embedding_id", doc.get("chunk_id")): doc
                for doc in metadata_docs
            }

            # Combine vector results with metadata
            for result in vector_results:
                chunk_id = result.node.metadata.get("chunk_id", None)
                if not chunk_id:
                    extracted_document_id = result.node.metadata.get("document_id", "")
                    chunk_index = result.node.metadata.get("chunk_index", 0)
                    chunk_id = f"{extracted_document_id}::chunk_{chunk_index}"

                metadata_doc = metadata_lookup.get(chunk_id)

                if metadata_doc:
                    # Combine vector result with backend metadata
                    augmented_result = {
                        "score": result.score,
                        "text": result.node.text,
                        "chunk_id": chunk_id,
                        "document_id": metadata_doc.get("document_id"),
                        "chunk_index": metadata_doc.get("chunk_index"),
                        "file_path": metadata_doc.get("metadata", {}).get("file_path"),
                        "file_type": metadata_doc.get("metadata", {}).get("file_type"),
                        "file_size": metadata_doc.get("metadata", {}).get("file_size"),
                        "file_modified": metadata_doc.get("metadata", {}).get(
                            "file_modified"
                        ),
                        "text_length": metadata_doc.get("metadata", {}).get(
                            "text_length"
                        ),
                        "created_at": metadata_doc.get("metadata", {}).get(
                            "created_at"
                        ),
                        "page_label": metadata_doc.get("metadata", {}).get(
                            "page_label"
                        ),
                        "file_name": metadata_doc.get("metadata", {}).get("file_name"),
                        "source": metadata_doc.get("metadata", {}).get("source"),
                        "parser": metadata_doc.get("metadata", {}).get("parser"),
                        "block_type": metadata_doc.get("metadata", {}).get(
                            "block_type"
                        ),
                        "block_index": metadata_doc.get("metadata", {}).get(
                            "block_index"
                        ),
                        "page_number": metadata_doc.get("metadata", {}).get(
                            "page_number"
                        ),
                    }
                    augmented_results.append(augmented_result)
                else:
                    # Fallback to vector result only
                    augmented_results.append(
                        {
                            "score": result.score,
                            "text": result.node.text,
                            "chunk_id": chunk_id,
                            "error": "Metadata not found in backend",
                        }
                    )

        except Exception as e:
            logging.error(f"Error augmenting vectors with metadata: {str(e)}")
            # Return vector results without augmentation on error
            for result in vector_results:
                augmented_results.append(
                    {
                        "score": result.score,
                        "text": result.node.text,
                        "chunk_id": result.node.metadata.get("chunk_id", "unknown"),
                        "error": f"Metadata augmentation failed: {str(e)}",
                    }
                )

        return augmented_results
