"""
Backend Integration Tests
Tests the Supabase client and search functionality
"""
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_supabase_connection():
    """Test 1: Verify Supabase connection works"""
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Supabase Connection")
    logger.info("="*50)
    
    try:
        from backend.supabase_client import SupabaseClient
        db = SupabaseClient()
        logger.info("✓ Supabase client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Supabase client: {e}")
        return False


def test_structured_search():
    """Test 2: Structured search with metadata filters"""
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Structured Search (Metadata Filter)")
    logger.info("="*50)
    
    try:
        from backend.supabase_client import SupabaseClient
        db = SupabaseClient()
        
        # Test with artist filter
        results = db.get_artworks(
            page=1, 
            items_per_page=5,
            search_params={'artist': 'Ensor'}
        )
        
        logger.info(f"Query: artist='Ensor'")
        logger.info(f"Results: {results['total_items']} items found")
        logger.info(f"Pages: {results['total_pages']} total pages")
        
        if results['items']:
            logger.info("\nFirst result:")
            first = results['items'][0]
            logger.info(f"  Inventory: {first.get('inventarisnummer', 'N/A')}")
            logger.info(f"  Artist: {first.get('beschrijving_kunstenaar', 'N/A')}")
            logger.info(f"  Title: {first.get('beschrijving_titel', 'N/A')}")
            logger.info(f"  Image: {first.get('imageOpacLink', 'N/A')[:50]}...")
            logger.info("✓ Structured search successful")
            return True
        else:
            logger.warning("⚠ No results found (database might be empty)")
            return True  # Not a failure, just no data
            
    except Exception as e:
        logger.error(f"✗ Structured search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_search():
    """Test 3: Semantic search with embeddings"""
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Semantic Search (Vector Search)")
    logger.info("="*50)
    
    try:
        from backend.supabase_client import SupabaseClient
        db = SupabaseClient()
        
        query = "dark dramatic painting with strong contrast"
        logger.info(f"Query: '{query}'")
        
        semantic_results = db.vector_search(query, limit=5)
        
        logger.info(f"Results: {len(semantic_results)} matches found")
        
        if semantic_results:
            logger.info("\nTop 3 matches:")
            for i, result in enumerate(semantic_results[:3], 1):
                logger.info(f"  {i}. {result.get('inventarisnummer', 'N/A')}")
                logger.info(f"     Similarity: {result.get('similarity', 0):.3f}")
            
            # Test fetching full artwork details
            inv_numbers = [r['inventarisnummer'] for r in semantic_results]
            full_results = db.get_artworks(
                page=1,
                items_per_page=5,
                search_params={'inventory_number': inv_numbers}
            )
            
            logger.info(f"\nFetched full details for {len(full_results['items'])} artworks")
            logger.info("✓ Semantic search successful")
            return True
        else:
            logger.warning("⚠ No semantic results found (embeddings might not be set up)")
            return True  # Not a failure
            
    except Exception as e:
        logger.error(f"✗ Semantic search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_artwork():
    """Test 4: Fetch single artwork by inventory number"""
    logger.info("\n" + "="*50)
    logger.info("TEST 4: Single Artwork Fetch")
    logger.info("="*50)
    
    try:
        from backend.supabase_client import SupabaseClient
        db = SupabaseClient()
        
        # First get any artwork
        results = db.get_artworks(page=1, items_per_page=1)
        
        if not results['items']:
            logger.warning("⚠ No artworks in database to test with")
            return True
        
        inv_number = results['items'][0]['inventarisnummer']
        logger.info(f"Fetching artwork: {inv_number}")
        
        artwork = db.get_artwork_by_inventory(inv_number)
        
        if artwork:
            logger.info("Artwork details:")
            logger.info(f"  Inventory: {artwork.get('inventarisnummer', 'N/A')}")
            logger.info(f"  Artist: {artwork.get('beschrijving_kunstenaar', 'N/A')}")
            logger.info(f"  Title: {artwork.get('beschrijving_titel', 'N/A')}")
            logger.info("✓ Single artwork fetch successful")
            return True
        else:
            logger.error("✗ Failed to fetch artwork")
            return False
            
    except Exception as e:
        logger.error(f"✗ Single artwork fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all backend tests"""
    logger.info("\n" + "="*70)
    logger.info("BACKEND INTEGRATION TESTS - Fabritius-NG")
    logger.info("="*70)
    
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("Structured Search", test_structured_search),
        ("Semantic Search", test_semantic_search),
        ("Single Artwork", test_single_artwork),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("="*70)
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
