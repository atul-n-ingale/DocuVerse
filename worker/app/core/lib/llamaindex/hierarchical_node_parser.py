"""
Custom HierarchicalNodeParser with content-type aware chunking and progress updates.

This module extends LlamaIndex's HierarchicalNodeParser to provide:
1. Content-type aware chunking strategies
2. Live progress updates during processing
3. Enhanced hierarchical relationship management
4. Custom metadata handling for LLMSherpa data
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Callable

from llama_index.core.node_parser.relational.hierarchical import (
    HierarchicalNodeParser, 
    _add_parent_child_relationship
)
from llama_index.core.node_parser.text.sentence import SentenceSplitter
from llama_index.core.schema import BaseNode, Document, NodeRelationship, RelatedNodeInfo
from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager

logger = logging.getLogger(__name__)


class ContentTypeAwareSplitter(SentenceSplitter):
    """
    Custom sentence splitter that applies different chunking strategies
    based on content type and hierarchical level.
    """

    def __init__(
        self,
        content_type_rules: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize with content-type specific rules.
        
        Args:
            content_type_rules: Dictionary mapping content types to chunking rules
                Example: {
                    "header": {"chunk_size": 256, "chunk_overlap": 10},
                    "paragraph": {"chunk_size": 512, "chunk_overlap": 20},
                    "table": {"chunk_size": 1024, "chunk_overlap": 50},
                }
        """
        # Set content type rules before calling parent
        self._content_type_rules = content_type_rules or {}
        super().__init__(**kwargs)

    @property
    def content_type_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get content type rules."""
        return self._content_type_rules

    def get_chunk_config_for_content(self, content_type: str, level: int) -> Dict[str, Any]:
        """
        Get chunk configuration based on content type and hierarchical level.
        
        Args:
            content_type: Type of content (header, paragraph, table, etc.)
            level: Hierarchical level (0, 1, 2, etc.)
            
        Returns:
            Dictionary with chunk_size and chunk_overlap
        """
        # Get base rules for content type
        base_rules = self.content_type_rules.get(content_type, {})
        
        # Apply level-specific overrides
        level_rules = base_rules.get(f"level_{level}", {})
        
        return {
            "chunk_size": level_rules.get("chunk_size", base_rules.get("chunk_size", self.chunk_size)),
            "chunk_overlap": level_rules.get("chunk_overlap", base_rules.get("chunk_overlap", self.chunk_overlap)),
        }

    def split_texts(self, texts: List[str]) -> List[str]:
        """
        Split texts with content-type awareness.
        
        Note: This is a simplified implementation. In practice, you would
        need to pass content type information through the metadata.
        """
        # For now, use default splitting
        # TODO: Implement content-type aware splitting when metadata is available
        return super().split_texts(texts)


class CustomHierarchicalNodeParser(HierarchicalNodeParser):
    """
    Custom HierarchicalNodeParser with enhanced features for our document processing.
    
    Features:
    - Content-type aware chunking
    - Live progress updates
    - Enhanced relationship management
    - LLMSherpa metadata preservation
    """

    content_type_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configuration for different content types"
    )
    progress_callback: Optional[Callable[[str, int, int], None]] = Field(
        default=None,
        description="Callback for progress updates (message, current, total)"
    )

    @classmethod
    def from_defaults(
        cls,
        chunk_sizes: Optional[List[int]] = None,
        chunk_overlap: int = 20,
        content_type_config: Optional[Dict[str, Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        include_metadata: bool = True,
        include_prev_next_rel: bool = True,
        callback_manager: Optional[CallbackManager] = None,
    ) -> "CustomHierarchicalNodeParser":
        """
        Create a CustomHierarchicalNodeParser with default settings.
        
        Args:
            chunk_sizes: List of chunk sizes for different levels
            chunk_overlap: Overlap between chunks
            content_type_config: Configuration for different content types
            progress_callback: Callback for progress updates
            include_metadata: Whether to include metadata
            include_prev_next_rel: Whether to include prev/next relationships
            callback_manager: Callback manager for LlamaIndex
        """
        callback_manager = callback_manager or CallbackManager([])

        if chunk_sizes is None:
            chunk_sizes = [2048, 512, 128]

        # Default content type configuration
        if content_type_config is None:
            content_type_config = {
                "header": {
                    "chunk_size": 256,
                    "chunk_overlap": 10,
                    "level_0": {"chunk_size": 128, "chunk_overlap": 5},
                    "level_1": {"chunk_size": 256, "chunk_overlap": 10},
                },
                "paragraph": {
                    "chunk_size": 512,
                    "chunk_overlap": 20,
                    "level_0": {"chunk_size": 256, "chunk_overlap": 10},
                    "level_1": {"chunk_size": 512, "chunk_overlap": 20},
                },
                "table": {
                    "chunk_size": 1024,
                    "chunk_overlap": 50,
                    "level_0": {"chunk_size": 512, "chunk_overlap": 25},
                    "level_1": {"chunk_size": 1024, "chunk_overlap": 50},
                },
                "list_item": {
                    "chunk_size": 256,
                    "chunk_overlap": 10,
                    "level_2": {"chunk_size": 128, "chunk_overlap": 5},
                },
            }

        # Create node parser IDs and map
        node_parser_ids = [f"chunk_size_{chunk_size}" for chunk_size in chunk_sizes]
        node_parser_map = {}
        
        for chunk_size, node_parser_id in zip(chunk_sizes, node_parser_ids):
            node_parser_map[node_parser_id] = ContentTypeAwareSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                content_type_rules=content_type_config,
                callback_manager=callback_manager,
                include_metadata=include_metadata,
                include_prev_next_rel=include_prev_next_rel,
            )

        return cls(
            chunk_sizes=chunk_sizes,
            node_parser_ids=node_parser_ids,
            node_parser_map=node_parser_map,
            content_type_config=content_type_config,
            progress_callback=progress_callback,
            include_metadata=include_metadata,
            include_prev_next_rel=include_prev_next_rel,
            callback_manager=callback_manager,
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
        logger.info(f"Progress: {message} - {current}/{total} ({percentage:.1f}%)")

    def _add_enhanced_relationships(
        self, parent_node: BaseNode, child_node: BaseNode
    ) -> None:
        """
        Add enhanced relationships between parent and child nodes.
        
        Args:
            parent_node: Parent node
            child_node: Child node
        """
        # Add standard parent-child relationship
        _add_parent_child_relationship(parent_node, child_node)
        
        # Add content-type specific relationships
        child_content_type = child_node.metadata.get("content_type")
        parent_content_type = parent_node.metadata.get("content_type")
        
        if child_content_type == "header":
            # Headers are important structural elements
            child_node.metadata["structural_importance"] = "high"
            
        elif child_content_type == "table":
            # Tables should reference their parent context
            child_node.metadata["table_parent_context"] = parent_node.node_id
            
        elif child_content_type == "list_item":
            # List items should know their list context
            child_node.metadata["list_parent"] = parent_node.node_id
            
        # Add hierarchical level information
        child_node.metadata["parent_level"] = parent_node.metadata.get("hierarchical_level", 0)
        child_node.metadata["child_level"] = child_node.metadata.get("hierarchical_level", 1)

    def _recursively_get_nodes_from_nodes(
        self,
        nodes: List[BaseNode],
        level: int,
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """
        Recursively get nodes with enhanced progress tracking and relationships.
        
        Args:
            nodes: List of nodes to process
            level: Current hierarchical level
            show_progress: Whether to show progress
            
        Returns:
            List of processed nodes
        """
        if level >= len(self.node_parser_ids):
            raise ValueError(
                f"Level {level} is greater than number of text "
                f"splitters ({len(self.node_parser_ids)})."
            )

        # Update progress for this level
        self._update_progress(
            f"Processing level {level} nodes",
            0,
            len(nodes)
        )

        # Process nodes with progress tracking
        sub_nodes = []
        for i, node in enumerate(nodes):
            # Update progress
            self._update_progress(
                f"Processing level {level} node {i+1}/{len(nodes)}",
                i + 1,
                len(nodes)
            )

            # Get content type for custom processing
            content_type = node.metadata.get("content_type", "default")
            
            # Get appropriate node parser
            node_parser = self.node_parser_map[self.node_parser_ids[level]]
            
            # Process the node
            cur_sub_nodes = node_parser.get_nodes_from_documents([node])
            
            # Add enhanced relationships if not at top level
            if level > 0:
                for sub_node in cur_sub_nodes:
                    self._add_enhanced_relationships(
                        parent_node=node,
                        child_node=sub_node,
                    )

            sub_nodes.extend(cur_sub_nodes)

        # Recursively process sub-nodes
        if level < len(self.node_parser_ids) - 1:
            sub_sub_nodes = self._recursively_get_nodes_from_nodes(
                sub_nodes,
                level + 1,
                show_progress=show_progress,
            )
        else:
            sub_sub_nodes = []

        return sub_nodes + sub_sub_nodes

    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False,
        **kwargs: Any,
    ) -> List[BaseNode]:
        """
        Parse documents into nodes with enhanced progress tracking.
        
        Args:
            documents: Documents to process
            show_progress: Whether to show progress
            **kwargs: Additional arguments
            
        Returns:
            List of processed nodes
        """
        # Initial progress update
        self._update_progress(
            "Starting document processing",
            0,
            len(documents)
        )

        all_nodes: List[BaseNode] = []
        
        for i, doc in enumerate(documents):
            # Update progress for each document
            self._update_progress(
                f"Processing document {i+1}/{len(documents)}: {doc.metadata.get('document_id', 'unknown')}",
                i + 1,
                len(documents)
            )

            # Process document recursively
            nodes_from_doc = self._recursively_get_nodes_from_nodes([doc], 0, show_progress)
            all_nodes.extend(nodes_from_doc)

        # Final progress update
        self._update_progress(
            f"Completed processing {len(documents)} documents",
            len(documents),
            len(documents)
        )

        logger.info(f"Generated {len(all_nodes)} nodes from {len(documents)} documents")
        return all_nodes

    @classmethod
    def class_name(cls) -> str:
        """Get the class name."""
        return "CustomHierarchicalNodeParser" 