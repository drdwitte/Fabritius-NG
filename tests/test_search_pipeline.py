"""
Search Pipeline Module Tests

Tests for the refactored search pipeline components:
- PipelineState (state management)
- Operator functions
- UI helpers
"""

import sys
from pathlib import Path
from loguru import logger
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_pipeline_state_basic():
    """Test 1: Basic PipelineState operations"""
    logger.info("\n" + "="*50)
    logger.info("TEST 1: PipelineState - Basic Operations")
    logger.info("="*50)
    
    try:
        from search_pipeline.state import PipelineState
        
        # Initialize
        state = PipelineState()
        assert len(state.get_all_operators()) == 0, "Initial state should be empty"
        logger.info("✓ PipelineState initialized")
        
        # Add operator
        op_id = state.add_operator('Metadata Filter')
        assert op_id is not None, "Operator ID should be returned"
        assert len(state.get_all_operators()) == 1, "Should have 1 operator"
        logger.info(f"✓ Added operator: {op_id}")
        
        # Get operator
        operator = state.get_operator(op_id)
        assert operator is not None, "Operator should exist"
        assert operator['name'] == 'Metadata Filter', "Operator name should match"
        assert operator['id'] == op_id, "Operator ID should match"
        logger.info(f"✓ Retrieved operator: {operator['name']}")
        
        # Remove operator
        success = state.remove_operator(op_id)
        assert success, "Removal should succeed"
        assert len(state.get_all_operators()) == 0, "State should be empty after removal"
        logger.info("✓ Removed operator")
        
        logger.info("✅ TEST 1 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_state_deep_copy():
    """Test 2: Deep copy protection"""
    logger.info("\n" + "="*50)
    logger.info("TEST 2: PipelineState - Deep Copy Protection")
    logger.info("="*50)
    
    try:
        from search_pipeline.state import PipelineState
        
        state = PipelineState()
        op_id = state.add_operator('Semantic Search')
        
        # Update params
        state.update_params(op_id, {'query_text': 'test', 'n_results': 10})
        
        # Get operator and try to mutate
        operator = state.get_operator(op_id)
        operator['params']['query_text'] = 'HACKED'
        operator['params']['new_param'] = 'SHOULD_NOT_EXIST'
        
        # Verify original is unchanged
        original = state.get_operator(op_id)
        assert original['params']['query_text'] == 'test', "Original should be unchanged"
        assert 'new_param' not in original['params'], "New param should not exist"
        logger.info("✓ Deep copy protection works for get_operator")
        
        # Test get_all_operators
        all_ops = state.get_all_operators()
        all_ops[0]['name'] = 'HACKED'
        
        original_all = state.get_all_operators()
        assert original_all[0]['name'] == 'Semantic Search', "Original should be unchanged"
        logger.info("✓ Deep copy protection works for get_all_operators")
        
        logger.info("✅ TEST 2 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_state_params():
    """Test 3: Parameter management"""
    logger.info("\n" + "="*50)
    logger.info("TEST 3: PipelineState - Parameter Management")
    logger.info("="*50)
    
    try:
        from search_pipeline.state import PipelineState
        
        state = PipelineState()
        op_id = state.add_operator('Metadata Filter')
        
        # Update params
        params = {
            'artist': 'James Ensor',
            'year_range': [1880, 1900],
            'source': ['KMSKB', 'External']
        }
        success = state.update_params(op_id, params)
        assert success, "Update should succeed"
        logger.info(f"✓ Updated params: {params}")
        
        # Verify params
        operator = state.get_operator(op_id)
        assert operator['params'] == params, "Params should match"
        logger.info("✓ Params retrieved correctly")
        
        # Update result count
        success = state.update_result_count(op_id, 42)
        assert success, "Result count update should succeed"
        
        operator = state.get_operator(op_id)
        assert operator['result_count'] == 42, "Result count should be 42"
        logger.info("✓ Result count updated")
        
        logger.info("✅ TEST 3 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_state_reorder():
    """Test 4: Operator reordering"""
    logger.info("\n" + "="*50)
    logger.info("TEST 4: PipelineState - Operator Reordering")
    logger.info("="*50)
    
    try:
        from search_pipeline.state import PipelineState
        
        state = PipelineState()
        id1 = state.add_operator('Metadata Filter')
        id2 = state.add_operator('Semantic Search')
        id3 = state.add_operator('Similarity Search')
        
        # Check initial order
        ops = state.get_all_operators()
        assert ops[0]['id'] == id1, "First should be Metadata Filter"
        assert ops[1]['id'] == id2, "Second should be Semantic Search"
        assert ops[2]['id'] == id3, "Third should be Similarity Search"
        logger.info("✓ Initial order correct")
        
        # Reorder: reverse
        state.reorder([id3, id2, id1])
        ops = state.get_all_operators()
        assert ops[0]['id'] == id3, "First should now be Similarity Search"
        assert ops[1]['id'] == id2, "Second should be Semantic Search"
        assert ops[2]['id'] == id1, "Third should be Metadata Filter"
        logger.info("✓ Reorder successful")
        
        # Reorder with missing ID (should be ignored)
        state.reorder([id1, 'non-existent', id2, id3])
        ops = state.get_all_operators()
        assert len(ops) == 3, "Should still have 3 operators"
        assert ops[0]['id'] == id1, "Order should be preserved"
        logger.info("✓ Missing IDs handled correctly")
        
        logger.info("✅ TEST 4 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_state_json():
    """Test 5: JSON serialization"""
    logger.info("\n" + "="*50)
    logger.info("TEST 5: PipelineState - JSON Serialization")
    logger.info("="*50)
    
    try:
        from search_pipeline.state import PipelineState
        
        # Create pipeline
        state1 = PipelineState()
        id1 = state1.add_operator('Metadata Filter')
        state1.update_params(id1, {'artist': 'Ensor', 'year_range': [1880, 1900]})
        state1.update_result_count(id1, 25)
        
        id2 = state1.add_operator('Semantic Search')
        state1.update_params(id2, {'query_text': 'portrait', 'n_results': 50})
        
        # Export to JSON
        json_str = state1.to_json()
        assert json_str, "JSON should not be empty"
        logger.info(f"✓ Exported to JSON ({len(json_str)} chars)")
        
        # Validate JSON structure
        data = json.loads(json_str)
        assert isinstance(data, list), "JSON should be a list"
        assert len(data) == 2, "Should have 2 operators"
        assert data[0]['name'] == 'Metadata Filter', "First operator name should match"
        assert data[0]['params']['artist'] == 'Ensor', "Params should be preserved"
        logger.info("✓ JSON structure valid")
        
        # Import into new state
        state2 = PipelineState()
        state2.from_json(json_str)
        
        ops = state2.get_all_operators()
        assert len(ops) == 2, "Should have 2 operators after import"
        assert ops[0]['name'] == 'Metadata Filter', "First operator should match"
        assert ops[0]['params']['artist'] == 'Ensor', "Params should be restored"
        assert ops[0]['result_count'] == 25, "Result count should be restored"
        assert ops[1]['name'] == 'Semantic Search', "Second operator should match"
        logger.info("✓ Imported from JSON successfully")
        
        logger.info("✅ TEST 5 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_helpers():
    """Test 6: UI helper functions"""
    logger.info("\n" + "="*50)
    logger.info("TEST 6: UI Helpers - Format Functions")
    logger.info("="*50)
    
    try:
        from search_pipeline.ui_helpers import format_param_value
        
        # Test image dict
        result = format_param_value({'filename': 'test.jpg', 'data': 'base64...'})
        assert result == '📷 test.jpg', "Image format should show filename"
        logger.info(f"✓ Image format: {result}")
        
        # Test year range
        result = format_param_value([1880, 1900])
        assert result == '1880 - 1900', "Year range format"
        logger.info(f"✓ Year range format: {result}")
        
        # Test list with None
        result = format_param_value([None, 1900])
        assert result == 'None - 1900', "Year range with None"
        logger.info(f"✓ Year range with None: {result}")
        
        # Test string list
        result = format_param_value(['KMSKB', 'External', 'Other'])
        assert result == 'KMSKB, External, Other', "String list format"
        logger.info(f"✓ String list format: {result}")
        
        # Test long list (truncation)
        result = format_param_value(['A', 'B', 'C', 'D', 'E'])
        assert '...' in result, "Long list should be truncated"
        logger.info(f"✓ Long list truncation: {result}")
        
        # Test float to int
        result = format_param_value(15.0)
        assert result == '15', "Float without decimals should become int"
        logger.info(f"✓ Float to int: {result}")
        
        # Test long string (truncation)
        result = format_param_value('a' * 50)
        assert len(result) == 30, "Long string should be truncated to 30 chars"
        logger.info(f"✓ String truncation: {result}")
        
        logger.info("✅ TEST 6 PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all search pipeline tests"""
    logger.info("\n" + "="*70)
    logger.info("SEARCH PIPELINE MODULE TESTS")
    logger.info("="*70)
    
    results = []
    
    results.append(("Basic Operations", test_pipeline_state_basic()))
    results.append(("Deep Copy Protection", test_pipeline_state_deep_copy()))
    results.append(("Parameter Management", test_pipeline_state_params()))
    results.append(("Operator Reordering", test_pipeline_state_reorder()))
    results.append(("JSON Serialization", test_pipeline_state_json()))
    results.append(("UI Helpers", test_ui_helpers()))
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
    
    logger.info("="*70)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
