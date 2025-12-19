"""
Utility functions for vectorstore management
"""

import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)


def load_pdf_and_create_chunks(
    file_path: str, chunk_size: int = 5000, chunk_overlap: int = 500
) -> List[Document]:
    """
    Load PDF and create document chunks

    Args:
        file_path: Path to the PDF file
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between chunks

    Returns:
        List of Document chunks
    """
    logger.info(f"Loading PDF: {file_path}")

    # Load PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} pages from PDF")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")

    return chunks


def create_vectorstore(chunks: List[Document], embeddings: OpenAIEmbeddings) -> FAISS:
    """
    Create a new FAISS vectorstore from chunks

    Args:
        chunks: List of document chunks
        embeddings: OpenAI embeddings instance

    Returns:
        FAISS vectorstore
    """
    logger.info("Creating new vectorstore...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    logger.info("Vectorstore created successfully")
    return vectorstore


def add_to_vectorstore(vectorstore: FAISS, chunks: List[Document]) -> FAISS:
    """
    Add chunks to existing vectorstore

    Args:
        vectorstore: Existing FAISS vectorstore
        chunks: List of document chunks to add

    Returns:
        Updated vectorstore
    """
    logger.info("Adding to existing vectorstore...")
    vectorstore.add_documents(chunks)
    logger.info("Vectorstore updated successfully")
    return vectorstore


def get_all_documents_from_vectorstore(vectorstore: FAISS) -> List[Dict[str, Any]]:
    """
    Retrieve all documents from the FAISS vectorstore

    Args:
        vectorstore: FAISS vectorstore instance

    Returns:
        List of dictionaries containing document content and metadata
    """
    logger.info("Retrieving all documents from vectorstore...")

    try:
        # Access the docstore to get all documents
        documents = []
        docstore = vectorstore.docstore

        # Get all document IDs
        index_to_docstore_id = vectorstore.index_to_docstore_id

        for idx in range(len(index_to_docstore_id)):
            doc_id = index_to_docstore_id[idx]
            doc = docstore.search(doc_id)

            if doc:
                documents.append(
                    {"content": doc.page_content, "metadata": doc.metadata}
                )

        logger.info(f"Retrieved {len(documents)} documents from vectorstore")
        return documents

    except Exception as e:
        logger.error(f"Error retrieving documents from vectorstore: {e}")
        return []