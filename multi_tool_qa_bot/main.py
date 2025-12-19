"""
FastAPI Multi-Tool Q&A Bot with Nested Agents
Refactored with separate modules for better organization
"""

import os
import logging
import tempfile
from datetime import datetime
import uuid
from collections import defaultdict

from fastapi import FastAPI, File, UploadFile, HTTPException
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage

# Local imports
from schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
    HealthResponse,
    VectorStoreDataResponse,
    VectorStoreDocument,
)
from utils import (
    load_pdf_and_create_chunks,
    create_vectorstore,
    add_to_vectorstore,
    get_all_documents_from_vectorstore,
)
from agent import create_agent_graph, visualize_agent_graph

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Tool Q&A Bot",
    description="AI-powered Q&A bot with nested agents: Retrieval → Tools → LLM Fallback",
    version="1.0.0",
)

# Global variables
vectorstore = None
retriever = None
llm = ChatOpenAI(model="gpt-4o", temperature=0)
embeddings = OpenAIEmbeddings()

# Conversation memory: stores chat history per session
# Format: {session_id: [HumanMessage, AIMessage, ...]}
conversation_memory = defaultdict(list)


def update_vectorstore(chunks):
    """Update or create the vectorstore with new chunks"""
    global vectorstore, retriever

    try:
        if vectorstore is None:
            vectorstore = create_vectorstore(chunks, embeddings)
        else:
            vectorstore = add_to_vectorstore(vectorstore, chunks)

        # Update retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        logger.info("Vectorstore updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating vectorstore: {e}")
        return False


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Tool Q&A Bot API with Conversation Memory",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload PDF documents to create/update vectorstore",
            "POST /query": "Ask a question to the bot (with optional session_id for conversation memory)",
            "GET /health": "Check API and vectorstore health",
            "GET /vectorstore/data": "Retrieve all documents from vectorstore",
            "DELETE /vectorstore": "Clear the vectorstore",
            "GET /sessions/{session_id}/history": "Get conversation history for a session",
            "DELETE /sessions/{session_id}": "Clear a specific conversation session",
            "DELETE /sessions": "Clear all conversation sessions",
            "GET /graph/visualize": "Generate and download agent graph visualization (PNG image)",
            "GET /docs": "Interactive API documentation",
        },
        "conversation_memory": {
            "description": "Include 'session_id' in your query requests to maintain conversation context",
            "example": "First query returns a session_id, use it in subsequent queries for follow-up questions",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    doc_count = 0
    if vectorstore is not None:
        try:
            doc_count = vectorstore.index.ntotal
        except:
            doc_count = 0

    return HealthResponse(
        status="healthy",
        vectorstore_loaded=vectorstore is not None,
        documents_count=doc_count,
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to create/update the vectorstore

    - **file**: PDF file to upload (only .pdf files accepted)
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    logger.info(f"Received file: {file.filename}")

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            # Write uploaded file to temp file
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Process PDF
        chunks = load_pdf_and_create_chunks(tmp_file_path)

        # Update vectorstore
        success = update_vectorstore(chunks)

        # Clean up temp file
        os.unlink(tmp_file_path)

        if success:
            return UploadResponse(
                message="PDF processed and vectorstore updated successfully",
                filename=file.filename,
                chunks_created=len(chunks),
                vectorstore_updated=True,
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update vectorstore")

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_bot(request: QueryRequest):
    """
    Ask a question to the bot

    - **query**: The question to ask
    - **session_id**: Optional session ID to maintain conversation history

    The bot will:
    1. Try to answer from the vectorstore (RAG) with conversation context
    2. Use tools (calculator/weather) if retrieval is uncertain
    3. Use LLM fallback if tools can't answer
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Get or create session ID
    session_id = request.session_id if request.session_id else str(uuid.uuid4())

    logger.info(f"\n\n{'#'*60}")
    logger.info(f"NEW QUERY: {request.query}")
    logger.info(f"SESSION ID: {session_id}")
    logger.info(f"{'#'*60}\n")

    try:
        # Get conversation history for this session
        chat_history = conversation_memory.get(session_id, [])

        logger.info(f"Conversation history length: {len(chat_history)} messages")

        # Create initial state with conversation history
        initial_state = {
            "messages": chat_history.copy(),  # Include previous conversation
            "query": request.query,
            "retrieved_docs": [],
            "retrieval_answer": "",
            "retrieval_confidence": "",
            "tool_result": "",
            "final_answer": "",
            "current_step": "start",
            "steps_used": [],
        }

        # Run the graph
        graph = create_agent_graph(llm, retriever)
        result = graph.invoke(initial_state)

        # Update conversation memory
        conversation_memory[session_id].append(HumanMessage(content=request.query))
        conversation_memory[session_id].append(
            AIMessage(content=result["final_answer"])
        )

        # Log final result
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL ANSWER RECEIVED")
        logger.info(f"{'='*60}")
        logger.info(result['final_answer'])
        logger.info(f"{'='*60}\n")

        return QueryResponse(
            query=request.query,
            answer=result["final_answer"],
            steps_used=result["steps_used"],
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/vectorstore/data", response_model=VectorStoreDataResponse)
async def get_vectorstore_data(limit: int = 100):
    """
    Retrieve all documents from the vectorstore

    - **limit**: Maximum number of documents to return (default: 100)

    Returns all stored document chunks with their metadata
    """
    if vectorstore is None:
        raise HTTPException(
            status_code=404,
            detail="Vectorstore not initialized. Please upload a PDF first.",
        )

    logger.info(f"Retrieving vectorstore data (limit: {limit})")

    try:
        # Get all documents from vectorstore
        all_documents = get_all_documents_from_vectorstore(vectorstore)

        # Apply limit
        limited_documents = all_documents[:limit]

        # Convert to response format
        documents = [
            VectorStoreDocument(content=doc["content"], metadata=doc["metadata"])
            for doc in limited_documents
        ]

        return VectorStoreDataResponse(
            total_documents=len(all_documents),
            documents=documents,
            message=f"Retrieved {len(documents)} of {len(all_documents)} documents",
        )

    except Exception as e:
        logger.error(f"Error retrieving vectorstore data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving vectorstore data: {str(e)}"
        )


@app.delete("/vectorstore")
async def clear_vectorstore():
    """Clear the vectorstore (useful for testing)"""
    global vectorstore, retriever

    vectorstore = None
    retriever = None

    logger.info("Vectorstore cleared")

    return {"message": "Vectorstore cleared successfully"}


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in conversation_memory:
        raise HTTPException(status_code=404, detail="Session not found")

    history = conversation_memory[session_id]
    formatted_history = []

    for msg in history:
        if isinstance(msg, HumanMessage):
            formatted_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            formatted_history.append({"role": "assistant", "content": msg.content})

    return {
        "session_id": session_id,
        "message_count": len(formatted_history),
        "history": formatted_history,
    }


@app.get("/graph/visualize")
async def visualize_graph():
    """
    Generate and return a visualization of the agent graph

    Returns a PNG image showing the agent workflow:
    - Nodes: retrieval, tools, llm_fallback
    - Edges: conditional routing based on confidence and tool success
    """
    try:
        from fastapi.responses import FileResponse
        import os

        # Generate the graph visualization
        output_path = "agent_graph.png"
        visualize_agent_graph(llm, retriever, output_path)

        # Check if file was created
        if not os.path.exists(output_path):
            raise HTTPException(
                status_code=500, detail="Failed to generate graph visualization"
            )

        # Return the image file
        return FileResponse(
            output_path, media_type="image/png", filename="agent_graph.png"
        )

    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        raise HTTPException(
            status_code=500,
            detail="Graph visualization dependencies not installed. The graph structure is: Retrieval → (high confidence: END | low confidence: Tools) → (tool success: END | tool failed: LLM Fallback) → END",
        )
    except Exception as e:
        logger.error(f"Error generating graph: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating graph visualization: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Multi-Tool Q&A Bot API...")
    logger.info(f"OpenAI API Key configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    logger.info("FastAPI application started")
    logger.info("Upload PDFs via POST /upload")
    logger.info("Ask questions via POST /query")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
