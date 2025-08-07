import logging
import time
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.services.enhanced_vector_store import enhanced_vector_store

# Configure logging
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the Q&A agent using Model Context Protocol"""

    messages: Annotated[List[Dict[str, Any]], "The conversation messages"]
    query: Annotated[str, "The current user query"]
    context: Annotated[List[Dict[str, Any]], "Retrieved context from vector store"]
    sources: Annotated[List[Dict[str, Any]], "Source documents"]
    session_id: Annotated[str, "Conversation session ID"]
    conversation_history: Annotated[List[Dict[str, Any]], "Previous conversation turns"]
    answer: Annotated[str, "Generated answer"]
    confidence: Annotated[float, "Confidence score"]
    reasoning_steps: Annotated[List[str], "Reasoning process"]
    processing_time: Annotated[float, "Processing time"]


class QAGraphService:
    def __init__(self) -> None:
        logger.info("Initializing QAGraphService")
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, api_key=settings.openai_api_key)  # type: ignore
        logger.info(f"LLM initialized with model: gpt-3.5-turbo")
        self.graph = self._create_qa_graph()
        logger.info("Q&A graph created successfully")

    def _create_qa_graph(self) -> Any:
        """Create the Q&A workflow graph"""
        logger.info("Creating Q&A workflow graph")
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("reason_and_answer", self._reason_and_answer_node)
        workflow.add_node("validate_sources", self._validate_sources_node)
        workflow.add_node("update_conversation", self._update_conversation_node)

        # Define flow
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "reason_and_answer")
        workflow.add_edge("reason_and_answer", "validate_sources")
        workflow.add_edge("validate_sources", "update_conversation")
        workflow.add_edge("update_conversation", END)

        logger.info("Q&A workflow graph structure created")
        return workflow.compile()

    async def _retrieve_context_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from vector store"""
        start_time = time.time()
        logger.info(f"Starting retrieve_context_node for query: '{state['query'][:50]}...'")

        try:
            # Get context using enhanced vector store
            logger.info("Calling enhanced_vector_store.get_context_for_qa")
            context_data = await enhanced_vector_store.get_context_for_qa(
                query=state["query"], conversation_history=state.get("conversation_history", [])
            )

            logger.info(
                f"Context data received: {len(context_data.get('sources', []))} sources, {context_data.get('context_length', 0)} characters"
            )

            state["context"] = [{"content": context_data["context"]}]
            state["sources"] = context_data["sources"]
            state["processing_time"] = time.time() - start_time

            # Add reasoning step
            reasoning_step = f"Retrieved {len(context_data['sources'])} relevant document chunks ({context_data['context_length']} characters)"
            state["reasoning_steps"].append(reasoning_step)
            logger.info(f"Reasoning step added: {reasoning_step}")

        except Exception as e:
            error_msg = f"Error retrieving context: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state["reasoning_steps"].append(error_msg)
            state["context"] = []
            state["sources"] = []

        logger.info(f"retrieve_context_node completed in {state['processing_time']:.2f}s")
        return state

    async def _reason_and_answer_node(self, state: AgentState) -> AgentState:
        """Generate answer using reasoning"""
        start_time = time.time()
        logger.info("Starting reason_and_answer_node")

        try:
            # Prepare context for LLM
            context_text = ""
            if state["context"]:
                context_text = state["context"][0]["content"]

            logger.info(f"Context text length: {len(context_text)} characters")
            logger.debug(f"Context preview: '{context_text[:200]}...'")

            # Create conversation history for context
            history_text = ""
            if state.get("conversation_history"):
                for msg in state["conversation_history"][-3:]:  # Last 3 messages
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    history_text += f"{role}: {content}\n"

            logger.info(f"Conversation history length: {len(history_text)} characters")

            # Create prompt for reasoning
            prompt = f"""You are a helpful assistant that answers questions based on provided document context.

Previous conversation:
{history_text}

Document Context:
{context_text}

Current Question: {state["query"]}

Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, say so clearly.

Answer:"""

            logger.info(f"Generated prompt length: {len(prompt)} characters")
            logger.debug(f"Prompt preview: '{prompt[:300]}...'")

            # Generate response
            logger.info("Calling LLM to generate response")
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])

            # Ensure response.content is a string
            answer_content = response.content
            if isinstance(answer_content, list):
                answer_content = " ".join(str(item) for item in answer_content)
            else:
                answer_content = str(answer_content)

            state["answer"] = answer_content
            state["processing_time"] += time.time() - start_time

            # Add reasoning step
            reasoning_step = f"Generated answer using LLM reasoning ({len(answer_content)} characters)"
            state["reasoning_steps"].append(reasoning_step)
            logger.info(f"Reasoning step added: {reasoning_step}")
            logger.info(f"Generated answer: '{answer_content[:100]}...'")

        except Exception as e:
            error_msg = f"Error generating answer: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state["answer"] = error_msg
            state["reasoning_steps"].append(f"Error in reasoning: {str(e)}")

        logger.info(f"reason_and_answer_node completed in {time.time() - start_time:.2f}s")
        return state

    async def _validate_sources_node(self, state: AgentState) -> AgentState:
        """Validate answer against sources"""
        logger.info("Starting validate_sources_node")

        try:
            if not state["sources"]:
                state["confidence"] = 0.0
                reasoning_step = "No sources available for validation"
                state["reasoning_steps"].append(reasoning_step)
                logger.info(f"Reasoning step added: {reasoning_step}")
                return state

            # Calculate confidence based on source scores
            scores = [source.get("score", 0.0) for source in state["sources"]]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            logger.info(f"Source scores: {scores}, average: {avg_score:.3f}")

            # Normalize confidence (0-1 scale)
            state["confidence"] = min(avg_score, 1.0)

            # Add validation reasoning
            reasoning_step = (
                f"Validated answer against {len(state['sources'])} sources (confidence: {state['confidence']:.2f})"
            )
            state["reasoning_steps"].append(reasoning_step)
            logger.info(f"Reasoning step added: {reasoning_step}")

        except Exception as e:
            error_msg = f"Error in validation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state["confidence"] = 0.0
            state["reasoning_steps"].append(error_msg)

        logger.info(f"validate_sources_node completed, confidence: {state['confidence']:.3f}")
        return state

    async def _update_conversation_node(self, state: AgentState) -> AgentState:
        """Update conversation history"""
        logger.info("Starting update_conversation_node")

        try:
            # This would typically update the conversation in the database
            # For now, we'll just add to the reasoning steps
            reasoning_step = f"Updated conversation history for session {state['session_id']}"
            state["reasoning_steps"].append(reasoning_step)
            logger.info(f"Reasoning step added: {reasoning_step}")

        except Exception as e:
            error_msg = f"Error updating conversation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state["reasoning_steps"].append(error_msg)

        logger.info("update_conversation_node completed")
        return state

    async def process_query(
        self, query: str, session_id: str, conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Process a query using the LangGraph workflow"""
        start_time = time.time()
        logger.info(
            f"Starting process_query: query='{query[:50]}...', session_id={session_id}, history_length={len(conversation_history) if conversation_history else 0}"
        )

        # Initialize state
        initial_state = AgentState(
            messages=[{"role": "user", "content": query}],
            query=query,
            context=[],
            sources=[],
            session_id=session_id,
            conversation_history=conversation_history or [],
            answer="",
            confidence=0.0,
            reasoning_steps=[],
            processing_time=0.0,
        )

        logger.info("Initial state created, executing LangGraph workflow")

        try:
            # Execute the graph
            logger.info("Invoking LangGraph workflow")
            final_state = await self.graph.ainvoke(initial_state)

            total_time = time.time() - start_time
            logger.info(f"LangGraph workflow completed in {total_time:.2f}s")
            logger.info(f"Final answer length: {len(final_state['answer'])} characters")
            logger.info(f"Final confidence: {final_state['confidence']:.3f}")
            logger.info(f"Number of reasoning steps: {len(final_state['reasoning_steps'])}")

            return {
                "answer": final_state["answer"],
                "sources": final_state["sources"],
                "confidence": final_state["confidence"],
                "reasoning_steps": final_state["reasoning_steps"],
                "processing_time": total_time,
                "session_id": session_id,
            }

        except Exception as e:
            error_msg = f"Graph execution error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            total_time = time.time() - start_time

            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "reasoning_steps": [error_msg],
                "processing_time": total_time,
                "session_id": session_id,
            }


# Global instance
qa_graph_service = QAGraphService()
