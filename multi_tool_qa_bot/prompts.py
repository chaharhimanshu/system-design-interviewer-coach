"""
Prompt templates for the multi-tool Q&A bot
Centralized location for all prompt definitions
"""

from langchain_core.prompts import ChatPromptTemplate

# =============================================================================
# QUERY REPHRASING PROMPTS
# =============================================================================

QUERY_REPHRASE_TEMPLATE = """Given the conversation history, rephrase the current question to be a standalone question that includes all necessary context.

Conversation History:
{conversation_context}

Current Question: {query}

Standalone Question (be specific and include context from history):"""


# =============================================================================
# RETRIEVAL AGENT PROMPTS
# =============================================================================

RETRIEVAL_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on the provided context and conversation history.

Your task:
1. Answer the question using ONLY the information in the context
2. Use the conversation history to understand follow-up questions and references (like "it", "that", "the amount", etc.)
3. If the context contains a clear answer, provide it confidently
4. If the context doesn't contain enough information, say so clearly
5. Be concise and direct

After your answer, on a new line, rate your confidence as either HIGH or LOW.
Use HIGH if you found a clear answer in the context.
Use LOW if the information is missing, unclear, or insufficient."""

RETRIEVAL_HUMAN_PROMPT = """Context:
{context}{conversation}

Question: {question}

Answer (followed by confidence rating HIGH or LOW):"""


def get_retrieval_prompt() -> ChatPromptTemplate:
    """Get the retrieval agent prompt template"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", RETRIEVAL_SYSTEM_PROMPT),
            ("human", RETRIEVAL_HUMAN_PROMPT),
        ]
    )


# =============================================================================
# TOOL AGENT PROMPTS
# =============================================================================

TOOL_SELECTION_TEMPLATE = """You are an assistant that can use tools to answer questions.

Available tools:
- Calculator: For mathematical calculations
- Weather: For weather information

Question: {query}

Previous retrieval attempt: {retrieval_answer}

Can you answer this question using one of the available tools? If yes, use the appropriate tool. If no tool is suitable, respond with "No suitable tool available"."""


# =============================================================================
# LLM FALLBACK PROMPTS
# =============================================================================

LLM_FALLBACK_TEMPLATE = """You are a helpful assistant. Answer the user's question to the best of your ability.

Previous attempts to answer:
{context}{conversation_context}

User question: {query}

Provide a helpful, natural, and complete answer:"""
