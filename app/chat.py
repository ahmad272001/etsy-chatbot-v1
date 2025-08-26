import openai
from typing import List, Optional
from app.config import settings
from app.models import ChatRequest, ChatResponse, RetrievalRef, MessageRole
from app.rag import rag_engine


class ChatService:
    def __init__(self):
        """Initialize chat service with OpenAI."""
        from openai import OpenAI
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def build_context_prompt(self, query: str, retrieval_refs: List[RetrievalRef]) -> str:
        """Build context-aware prompt for the LLM."""
        if not retrieval_refs:
            return f"""You are a RAG assistant. You can only answer questions based on the knowledge base content.

Question: {query}

I don't have enough information in the knowledge base to answer that question. Please ask me something that relates to the documents I have access to."""

        # Build context from retrieved chunks
        context_parts = []
        for ref in retrieval_refs:
            # Get the actual chunk content
            chunks = rag_engine.get_document_chunks(ref.doc_id)
            chunk_content = next((chunk['content'] for chunk in chunks if chunk['chunk_id'] == ref.chunk_id), "")
            
            context_parts.append(f"Document: {ref.filename} (Page {ref.page})\nContent: {chunk_content}\n")

        context = "\n".join(context_parts)
        
        prompt = f"""You are a RAG assistant. You can only answer questions based on the provided context. If the context doesn't contain enough information to answer the question, say "I don't have enough information in the knowledge base to answer that."

Context:
{context}

Question: {query}

Instructions:
1. Answer ONLY using the provided context
2. Include citations in the format (filename p.X) for each piece of information
3. If you cannot answer from the context, say "I don't have enough information in the knowledge base to answer that."
4. Be concise but thorough
5. If the context is insufficient, do not make up information

Answer:"""

        return prompt
    
    async def get_chat_response(self, query: str, retrieval_refs: List[RetrievalRef]) -> str:
        """Get response from OpenAI LLM based on retrieved context."""
        try:
            prompt = self.build_context_prompt(query, retrieval_refs)
            
            response = self.client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful RAG assistant that only answers based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return "I apologize, but I encountered an error while processing your request. Please try again."
    
    async def process_chat_message(self, message: str) -> ChatResponse:
        """Process a chat message and return response with retrieval references."""
        try:
            # Search for relevant documents
            retrieval_refs = rag_engine.search_documents(message)
            
            # If no specific search results, try to get some general context
            if not retrieval_refs:
                # Try to get some general documents for context
                try:
                    # Get a few random documents for general context
                    search_result = rag_engine.qdrant_client.scroll(
                        collection_name=settings.qdrant_collection_name,
                        limit=3
                    )
                    
                    if search_result[0]:
                        # Use general context but be clear about limitations
                        context_chunks = []
                        for point in search_result[0]:
                            if point.payload.get("text", "").strip():
                                context_chunks.append(point.payload["text"])
                        
                        if context_chunks:
                            context = "\n\n".join(context_chunks)
                            prompt = f"""You are a helpful assistant. I have some general information available, but it may not be directly related to the user's question. Please provide a helpful response if possible, or politely explain what kind of information you have access to.

Available context:
{context}

User question: {message}

Please respond helpfully, but if the context doesn't contain relevant information, explain what kind of documents you have access to."""
                            
                            response = self.client.chat.completions.create(
                                model=settings.openai_chat_model,
                                messages=[
                                    {"role": "system", "content": "You are a helpful RAG assistant."},
                                    {"role": "user", "content": prompt}
                                ],
                                max_tokens=1000,
                                temperature=0.1
                            )
                            
                            response_text = response.choices[0].message.content.strip()
                            return ChatResponse(message=response_text, retrieval_refs=[])
                except Exception as e:
                    pass
            
            # If we have specific search results, use them
            if retrieval_refs:
                # Get the actual content from the search results
                query_embedding = rag_engine.get_openai_embedding(message)
                search_result = rag_engine.qdrant_client.search(
                    collection_name=settings.qdrant_collection_name,
                    query_vector=query_embedding,
                    limit=len(retrieval_refs)
                )
                
                # Extract actual text content from search results
                context_chunks = []
                for hit in search_result:
                    if hit.payload.get("text", "").strip():
                        context_chunks.append(hit.payload["text"])
                
                if context_chunks:
                    # Build context prompt with actual content
                    context = "\n\n".join(context_chunks)
                    prompt = f"""You are a helpful assistant. Use the following context to answer the user's question. If the context contains relevant information, provide a helpful answer. Only say you don't have enough information if the context is completely unrelated to the question.

Context:
{context}

Question: {message}

Answer the question based on the context above:"""
                    
                    # Get response from LLM
                    response = self.client.chat.completions.create(
                        model=settings.openai_chat_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful RAG assistant that only answers based on provided context."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.1
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    return ChatResponse(message=response_text, retrieval_refs=retrieval_refs)
            
            # Fallback response
            response_text = "I have access to technical documentation about signage and mounting methods. Please ask me specific questions about these topics, and I'll do my best to help you with the information available in my knowledge base."
            return ChatResponse(message=response_text, retrieval_refs=[])
            
        except Exception as e:
            return ChatResponse(
                message="I apologize, but I encountered an error while processing your request. Please try again.",
                retrieval_refs=[]
            )


# Global chat service instance
chat_service = ChatService()
