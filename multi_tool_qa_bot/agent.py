"""
Agent logic for the multi-tool Q&A bot
Contains agent nodes and graph creation
"""

import logging
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from tools import tools, calculator_tool, weather_tool
from prompts import (
    QUERY_REPHRASE_TEMPLATE,
    get_retrieval_prompt,
    TOOL_SELECTION_TEMPLATE,
    LLM_FALLBACK_TEMPLATE,
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State of the agent"""

    messages: Annotated[list, add_messages]
    query: str
    retrieved_docs: list[Document]
    retrieval_answer: str
    retrieval_confidence: str
    tool_result: str
    final_answer: str
    current_step: str
    steps_used: list[str]


def create_retrieval_node(llm: ChatOpenAI, retriever):
    """Create retrieval node function"""

    def retrieval_node(state: AgentState) -> AgentState:
        """Step 1: Retrieval Agent - Try to answer from RAG"""
        query = state["query"]
        chat_history = state.get("messages", [])

        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 1: RETRIEVAL AGENT")
        logger.info(f"Query: {query}")
        logger.info(f"Chat history messages: {len(chat_history)}")
        logger.info(f"{'='*60}")

        state["steps_used"].append("retrieval")

        if retriever is None:
            logger.warning("Retriever not available. Skipping retrieval.")
            state["retrieval_confidence"] = "low"
            state["retrieved_docs"] = []
            state["retrieval_answer"] = "Retrieval system not available."
            state["current_step"] = "retrieval_failed"
            return state

        # Build contextualized query if there's chat history
        if chat_history:
            # Format conversation history for context
            conversation_context = "\n".join(
                [
                    f"{'User' if hasattr(msg, 'type') and msg.type == 'human' else 'Assistant'}: {msg.content}"
                    for msg in chat_history[-4:]  # Last 2 exchanges (4 messages)
                ]
            )

            # Use LLM to rephrase the query with conversation context
            rephrase_prompt = QUERY_REPHRASE_TEMPLATE.format(
                conversation_context=conversation_context, query=query
            )

            response = llm.invoke([{"role": "user", "content": rephrase_prompt}])
            contextualized_query = response.content.strip()
            logger.info(f"Contextualized Query: {contextualized_query}")
        else:
            contextualized_query = query

        # Retrieve relevant documents using contextualized query
        docs = retriever.invoke(contextualized_query)
        state["retrieved_docs"] = docs

        logger.info(f"Retrieved {len(docs)} documents")

        if docs:
            context = "\n\n".join([doc.page_content for doc in docs])

            # Build conversation history context if available
            conversation_text = ""
            if chat_history:
                conversation_text = "\n\nPrevious Conversation:\n" + "\n".join(
                    [
                        f"{'User' if hasattr(msg, 'type') and msg.type == 'human' else 'Assistant'}: {msg.content}"
                        for msg in chat_history[-4:]  # Last 2 exchanges
                    ]
                )

            prompt = get_retrieval_prompt()

            chain = prompt | llm
            response = chain.invoke(
                {
                    "context": context,
                    "conversation": conversation_text,
                    "question": query,
                }
            )
            answer_text = response.content

            # Parse confidence
            lines = answer_text.strip().split("\n")
            last_line = lines[-1].upper()

            if "HIGH" in last_line:
                confidence = "high"
                answer = "\n".join(lines[:-1]).strip()
            elif "LOW" in last_line:
                confidence = "low"
                answer = "\n".join(lines[:-1]).strip()
            else:
                confidence = "medium"
                answer = answer_text

            state["retrieval_answer"] = answer
            state["retrieval_confidence"] = confidence

            logger.info(f"Retrieval Answer: {answer}")
            logger.info(f"Confidence: {confidence}")

            # If high confidence, set final answer here
            if confidence == "high":
                state["final_answer"] = answer
        else:
            state["retrieval_answer"] = "No relevant documents found."
            state["retrieval_confidence"] = "low"
            logger.info("No relevant documents found")

        state["current_step"] = "retrieval_complete"
        return state

    return retrieval_node


def should_use_tools(
    state: AgentState,
) -> Literal["use_tools", "use_llm_fallback", "end"]:
    """Decision: Should we use tools or go to LLM fallback?"""
    confidence = state["retrieval_confidence"]

    logger.info(f"\n{'='*60}")
    logger.info(f"DECISION POINT: After Retrieval")
    logger.info(f"Confidence: {confidence}")
    logger.info(f"{'='*60}")

    if confidence == "high":
        logger.info("High confidence - returning answer directly")
        # final_answer is already set in retrieval_node
        return "end"
    else:
        logger.info("Low confidence - trying tools")
        return "use_tools"


def create_tool_node(llm: ChatOpenAI):
    """Create tool node function"""

    def tool_node(state: AgentState) -> AgentState:
        """Step 2: Tool Agent - Try to use tools (calculator, weather)"""
        query = state["query"]
        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 2: TOOL AGENT")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*60}")

        state["steps_used"].append("tools")

        # Let LLM decide which tool to use
        tool_llm = llm.bind_tools(tools)

        prompt = TOOL_SELECTION_TEMPLATE.format(
            query=query, retrieval_answer=state["retrieval_answer"]
        )

        response = tool_llm.invoke([HumanMessage(content=prompt)])

        # Check if LLM wants to use a tool
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"Tool selected: {response.tool_calls[0]['name']}")
            logger.info(f"Tool arguments: {response.tool_calls[0]['args']}")

            # Execute the tool
            tool_name = response.tool_calls[0]["name"]
            tool_args = response.tool_calls[0]["args"]

            if tool_name == "Calculator":
                result = calculator_tool.func(
                    tool_args.get("expression", tool_args.get("__arg1", ""))
                )
            elif tool_name == "Weather":
                result = weather_tool.func(
                    tool_args.get("location", tool_args.get("__arg1", ""))
                )
            else:
                result = "Unknown tool"

            state["tool_result"] = result
            logger.info(f"Tool result: {result}")

            # Check if tool provided a valid answer
            if not result.startswith("Error:"):
                state["final_answer"] = result
                state["current_step"] = "tool_success"
            else:
                state["current_step"] = "tool_failed"
        else:
            logger.info("No suitable tool found")
            state["tool_result"] = "No suitable tool available"
            state["current_step"] = "tool_failed"

        return state

    return tool_node


def should_use_llm(state: AgentState) -> Literal["use_llm_fallback", "end"]:
    """Decision: Did tools succeed?"""
    logger.info(f"\n{'='*60}")
    logger.info(f"DECISION POINT: After Tools")
    logger.info(f"Current step: {state['current_step']}")
    logger.info(f"{'='*60}")

    if state["current_step"] == "tool_success":
        logger.info("Tool succeeded - returning answer")
        return "end"
    else:
        logger.info("Tool failed - using LLM fallback")
        return "use_llm_fallback"


def create_llm_fallback_node(llm: ChatOpenAI):
    """Create LLM fallback node function"""

    def llm_fallback_node(state: AgentState) -> AgentState:
        """Step 3: LLM Fallback - Use OpenAI to generate answer"""
        query = state["query"]
        chat_history = state.get("messages", [])

        logger.info(f"\n{'='*60}")
        logger.info(f"STEP 3: LLM FALLBACK")
        logger.info(f"Query: {query}")
        logger.info(f"Chat history messages: {len(chat_history)}")
        logger.info(f"{'='*60}")

        state["steps_used"].append("llm_fallback")

        # Build context from previous attempts
        context_parts = []

        if state.get("retrieval_answer"):
            context_parts.append(
                f"Information from knowledge base: {state['retrieval_answer']}"
            )

        if state.get("tool_result") and not state["tool_result"].startswith("Error"):
            context_parts.append(f"Tool result: {state['tool_result']}")

        context = (
            "\n\n".join(context_parts)
            if context_parts
            else "No additional context available."
        )

        # Build conversation history context
        conversation_context = ""
        if chat_history:
            conversation_context = "\n\nConversation History:\n" + "\n".join(
                [
                    f"{'User' if hasattr(msg, 'type') and msg.type == 'human' else 'Assistant'}: {msg.content}"
                    for msg in chat_history[-6:]  # Last 3 exchanges
                ]
            )

        prompt = LLM_FALLBACK_TEMPLATE.format(
            context=context, conversation_context=conversation_context, query=query
        )

        response = llm.invoke([{"role": "user", "content": prompt}])
        answer = response.content

        state["final_answer"] = answer
        state["current_step"] = "llm_complete"

        logger.info(f"LLM Answer: {answer}")

        return state

    return llm_fallback_node


def create_agent_graph(llm: ChatOpenAI, retriever):
    """Create the LangGraph workflow"""
    workflow = StateGraph(AgentState)

    # Create node functions with dependencies
    retrieval_node = create_retrieval_node(llm, retriever)
    tool_node = create_tool_node(llm)
    llm_fallback_node = create_llm_fallback_node(llm)

    # Add nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("llm_fallback", llm_fallback_node)

    # Add edges
    workflow.set_entry_point("retrieval")

    workflow.add_conditional_edges(
        "retrieval",
        should_use_tools,
        {"use_tools": "tools", "end": END},
    )

    workflow.add_conditional_edges(
        "tools", should_use_llm, {"use_llm_fallback": "llm_fallback", "end": END}
    )

    workflow.add_edge("llm_fallback", END)

    # Compile
    return workflow.compile()


def visualize_agent_graph(
    llm: ChatOpenAI, retriever, output_path: str = "agent_graph.png"
):
    """
    Create a visualization of the agent graph and save it as an image

    Args:
        llm: The language model instance
        retriever: The retriever instance
        output_path: Path where the image will be saved (default: agent_graph.png)

    Returns:
        str: Path to the saved image
    """
    try:
        from IPython.display import Image

        # Create the graph
        graph = create_agent_graph(llm, retriever)

        # Generate the graph visualization
        png_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(png_data)

        logger.info(f"Graph visualization saved to {output_path}")
        return output_path
    except ImportError as e:
        logger.error(f"Missing dependencies for graph visualization: {e}")
        logger.info("Install with: pip install pygraphviz or use mermaid visualization")
        raise
    except Exception as e:
        logger.error(f"Error creating graph visualization: {e}")
        raise
