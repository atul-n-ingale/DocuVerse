"""
Custom PineconeVectorStore with enhanced metadata handling and progress updates.

This module extends LlamaIndex's PineconeVectorStore to provide:
1. Enhanced metadata transformation for hierarchical data
2. Custom node ID generation
3. Progress updates during vector operations
4. Hierarchical-aware query enhancement
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Sequence

from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.schema import BaseNode
from llama_index.core.vector_stores.types import (
    VectorStoreQuery,
    VectorStoreQueryResult,
    MetadataFilters,
    MetadataFilter,
    FilterOperator,
)
from llama_index.core.bridge.pydantic import Field

logger = logging.getLogger(__name__)


class CustomPineconeVectorStore(PineconeVectorStore):
    """
    Custom PineconeVectorStore with enhanced features for hierarchical data.
    
    Features:
    - Enhanced metadata transformation
    - Custom node ID generation
    - Progress updates during operations
    - Hierarchical-aware query enhancement
    """

    metadata_transformer: Optional[Callable[[Dict[str, Any], BaseNode], Dict[str, Any]]] = Field(
        default=None,
        description="Custom metadata transformation function"
    )
    progress_callback: Optional[Callable[[str, int, int], None]] = Field(
        default=None,
        description="Callback for progress updates (message, current, total)"
    )
    enable_hierarchical_filtering: bool = Field(
        default=True,
        description="Enable hierarchical-aware filtering"
    )

    def _update_progress(self, message: str, current: int, total: int) -> None:
        """
        Update progress via callback if available.
        
        Args:
            message: Progress message
            current: Current item being processed
            total: Total items to process
        """
        if self.progress_callback:
            try:
                self.progress_callback(message, current, total)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        # Also log progress
        percentage = (current / total * 100) if total > 0 else 0
        logger.info(f"Pinecone Progress: {message} - {current}/{total} ({percentage:.1f}%)")

    def _transform_metadata(self, node: BaseNode) -> Dict[str, Any]:
        """
        Transform node metadata for Pinecone storage.
        
        Args:
            node: Node to transform
            
        Returns:
            Transformed metadata dictionary
        """
        # Start with node metadata
        base_metadata = node.metadata.copy()
        
        # Apply custom transformation if provided
        if self.metadata_transformer:
            try:
                return self.metadata_transformer(base_metadata, node)
            except Exception as e:
                logger.warning(f"Custom metadata transformation failed: {e}")
        
        # Enhanced metadata transformation for hierarchical data
        enhanced_metadata = base_metadata.copy()
        
        # Add hierarchical information
        if "hierarchical_level" in node.metadata:
            enhanced_metadata["level"] = node.metadata["hierarchical_level"]
            enhanced_metadata["importance_score"] = node.metadata.get("importance_score", 0.5)
        
        # Add content type information
        if "content_type" in node.metadata:
            enhanced_metadata["content_type"] = node.metadata["content_type"]
            enhanced_metadata["block_type"] = node.metadata.get("block_type", "unknown")
        
        # Add LLMSherpa specific metadata (filtered for Pinecone compatibility)
        llmsherpa_keys = [
            "llmsherpa_tag", "llmsherpa_block_class", "llmsherpa_level"
        ]
        for key in llmsherpa_keys:
            if key in node.metadata:
                enhanced_metadata[key] = node.metadata[key]
        
        # Add document information
        if "document_id" in node.metadata:
            enhanced_metadata["document_id"] = node.metadata["document_id"]
        
        # Add page information
        if "page_number" in node.metadata:
            enhanced_metadata["page_number"] = node.metadata["page_number"]
        
        # Filter out complex objects that Pinecone doesn't support
        filtered_metadata = {}
        for key, value in enhanced_metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                filtered_metadata[key] = value
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                filtered_metadata[key] = value
            else:
                # Convert complex objects to string
                filtered_metadata[key] = str(value)
        
        return filtered_metadata

    def _generate_custom_node_id(self, node: BaseNode) -> str:
        """
        Generate custom node ID based on content type and hierarchy.
        
        Args:
            node: Node to generate ID for
            
        Returns:
            Custom node ID
        """
        base_id = node.node_id
        
        # Use document_id from metadata instead of deprecated ref_doc_id
        document_id = node.metadata.get("document_id")
        if document_id:
            # Include hierarchical level and content type in ID
            level = node.metadata.get("hierarchical_level", 0)
            content_type = node.metadata.get("content_type", "unknown")
            return f"{document_id}#{content_type}#{level}#{base_id}"
        
        return base_id

    def add(
        self,
        nodes: List[BaseNode],
        **add_kwargs: Any,
    ) -> List[str]:
        """
        Add nodes to Pinecone with enhanced progress tracking.
        
        Args:
            nodes: List of nodes to add
            **add_kwargs: Additional arguments
            
        Returns:
            List of node IDs
        """
        # Initial progress update
        self._update_progress(
            "Starting node addition to Pinecone",
            0,
            len(nodes)
        )

        ids = []
        entries = []
        sparse_inputs = []
        
        for i, node in enumerate(nodes):
            # Update progress
            self._update_progress(
                f"Processing node {i+1}/{len(nodes)}",
                i + 1,
                len(nodes)
            )

            # Generate custom node ID
            node_id = self._generate_custom_node_id(node)

            # Transform metadata
            metadata = self._transform_metadata(node)

            # Handle sparse vectors if enabled
            if self.add_sparse_vector and self._sparse_embedding_model is not None:
                sparse_inputs.append(node.get_content(metadata_mode="embed"))

            ids.append(node_id)

            entry = {
                "id": node_id,
                "values": node.get_embedding(),
                "metadata": metadata,
            }
            entries.append(entry)

        # Process sparse vectors if any
        if sparse_inputs:
            self._update_progress("Generating sparse vectors", 0, len(sparse_inputs))
            sparse_vectors = self._sparse_embedding_model.get_text_embedding_batch(
                sparse_inputs
            )
            for i, sparse_vector in enumerate(sparse_vectors):
                entries[i]["sparse_values"] = {
                    "indices": list(sparse_vector.keys()),
                    "values": list(sparse_vector.values()),
                }

        # Upsert to Pinecone
        self._update_progress("Upserting to Pinecone", 0, 1)
        self._pinecone_index.upsert(
            entries,
            namespace=self.namespace,
            batch_size=self.batch_size,
            **self.insert_kwargs,
        )
        
        # Final progress update
        self._update_progress(
            f"Successfully added {len(nodes)} nodes to Pinecone",
            len(nodes),
            len(nodes)
        )
        
        return ids

    def _build_hierarchical_filter(self, filters: MetadataFilters) -> MetadataFilters:
        """
        Build hierarchical-aware filters.
        
        Args:
            filters: Original filters
            
        Returns:
            Enhanced filters with hierarchical awareness
        """
        if not self.enable_hierarchical_filtering:
            return filters
        
        hierarchical_filters = []
        
        # Add level-based filtering for better results
        hierarchical_filters.append(
            MetadataFilter(
                key="level",
                value=0,  # Prefer top-level content
                operator=FilterOperator.LTE
            )
        )
        
        # Add importance score filtering
        hierarchical_filters.append(
            MetadataFilter(
                key="importance_score",
                value=0.3,  # Minimum importance threshold
                operator=FilterOperator.GTE
            )
        )
        
        # Combine with original filters
        if filters.filters:
            all_filters = filters.filters + hierarchical_filters
        else:
            all_filters = hierarchical_filters
        
        return MetadataFilters(
            filters=all_filters,
            condition=filters.condition
        )

    def query(
        self, query: VectorStoreQuery, **kwargs: Any
    ) -> VectorStoreQueryResult:
        """
        Query Pinecone with hierarchical-aware enhancements.
        
        Args:
            query: Query to execute
            **kwargs: Additional arguments
            
        Returns:
            Query results
        """
        # Enhance filters with hierarchical awareness
        if query.filters:
            query.filters = self._build_hierarchical_filter(query.filters)
        
        # Execute query using parent method
        result = super().query(query, **kwargs)
        
        # Post-process results for hierarchical relevance
        if result.nodes:
            result.nodes = self._post_process_hierarchical_results(result.nodes)
        
        return result

    def _post_process_hierarchical_results(self, nodes: List[BaseNode]) -> List[BaseNode]:
        """
        Post-process results to prioritize hierarchical relevance.
        
        Args:
            nodes: List of nodes to process
            
        Returns:
            Processed nodes with enhanced relevance
        """
        # Sort by hierarchical level and importance score
        def sort_key(node: BaseNode) -> tuple:
            level = node.metadata.get("level", 999)
            importance = node.metadata.get("importance_score", 0.0)
            return (level, -importance)  # Lower level first, higher importance first
        
        sorted_nodes = sorted(nodes, key=sort_key)
        
        # Add relevance metadata
        for i, node in enumerate(sorted_nodes):
            node.metadata["hierarchical_relevance"] = 1.0 - (i / len(sorted_nodes))
        
        return sorted_nodes

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """
        Delete nodes using document ID with progress tracking.
        
        Args:
            ref_doc_id: Document ID to delete
            **delete_kwargs: Additional arguments
        """
        self._update_progress(f"Deleting document {ref_doc_id}", 0, 1)
        
        try:
            # Delete by filtering on the document_id metadata
            self._pinecone_index.delete(
                filter={"document_id": {"$eq": ref_doc_id}},
                namespace=self.namespace,
                **delete_kwargs,
            )
            self._update_progress(f"Successfully deleted document {ref_doc_id}", 1, 1)
        except Exception as e:
            logger.warning(f"Standard delete failed for {ref_doc_id}: {e}")
            # Fallback to prefix-based deletion
            try:
                id_gen = self._pinecone_index.list(
                    prefix=ref_doc_id, namespace=self.namespace
                )
                ids_to_delete = list(id_gen)
                if ids_to_delete:
                    self._pinecone_index.delete(
                        ids=ids_to_delete, namespace=self.namespace, **delete_kwargs
                    )
                    self._update_progress(f"Deleted {len(ids_to_delete)} nodes for {ref_doc_id}", 1, 1)
            except Exception as fallback_error:
                logger.error(f"Fallback delete also failed for {ref_doc_id}: {fallback_error}")
                raise

    @classmethod
    def class_name(cls) -> str:
        """Get the class name."""
        return "CustomPineconeVectorStore" 