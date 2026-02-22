"""
Backend Package - Data Access & AI Services
============================================

This package handles all external integrations: database operations (Supabase),
AI model interactions (OpenAI), and AI-powered content generation.

MODULES
-------

supabase_client.py
    Database access layer for all Supabase operations.
    - SupabaseClient: Main class for DB interactions
    - Vector search (semantic similarity using pgvector)
    - Metadata filtering and full-text search
    - Tag management and artwork-tag relationships
    - Stored procedures: vector_search, metadata_filter, etc.
    
    Example:
        db = SupabaseClient()
        results = db.vector_search(query_embedding, top_k=10)

llms.py
    OpenAI API wrapper for LLM and vision model interactions.
    - LLMClient: Unified interface for GPT models
    - Text generation (GPT-4, GPT-3.5)
    - Vision API (GPT-4 Vision for image analysis)
    - Embedding generation (text-embedding-3-small/large)
    - Structured output support (Pydantic schemas)
    
    Example:
        llm = LLMClient()
        embedding = llm.get_embedding("search query text")
        caption = llm.generate_caption(image_url)

prompts.py
    Prompt templates for AI models.
    - FULL_PROMPT_VISION: Detailed artwork analysis prompt for GPT-4 Vision
    - Structured schemas (Pydantic) for validated AI outputs
    - Defines output format for artwork descriptions, subjects, themes, etc.
    
    Used by: caption_generator.py, llms.py

caption_generator.py
    Batch processing tool for generating AI captions for artworks.
    - Fetches uncaptioned artworks from database
    - Generates descriptions using GPT-4 Vision
    - Stores results back to Supabase
    - CLI tool for preprocessing/maintenance tasks
    
    Usage:
        python -m backend.caption_generator --limit 100

ARCHITECTURE FLOW
-----------------

User Query → Operator (search_pipeline) → SupabaseClient → Database
                                        ↓
                                    LLMClient → OpenAI API
                                        ↓
                                    Results → UI

DEPENDENCIES
------------
- supabase-py: Database client
- openai: LLM and embeddings
- pydantic: Data validation
- loguru: Logging

CONFIGURATION
-------------
Environment variables (in .env):
- FABRITIUS_SUPABASE_URL / SUPABASE_URL
- FABRITIUS_SUPABASE_KEY / SUPABASE_KEY
- FABRITIUS_OPENAI_API_KEY / OPENAI_API_KEY
"""
