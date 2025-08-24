"""
Simpler TDD test to isolate the exact issue.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
from io import StringIO

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.display_manager import DisplayManager, DisplayOptions


class TestSimpleTDD(unittest.TestCase):
    """Simple test to verify basic success tracking works."""

    def test_complete_file_increments_success_count(self):
        """Test that complete_file actually increments success count."""
        # Use a configuration that forces full progress display
        output = StringIO()
        display_manager = DisplayManager(DisplayOptions(quiet=False, no_color=True, file=output))
        
        # Force creation of full progress display  
        with patch('utils.display_manager.create_rich_display') as mock_create_rich:
            from utils.progress_display import ProgressDisplay
            mock_progress = ProgressDisplay(no_color=True, file=output)
            mock_create_rich.return_value = (mock_progress, Mock())
            
            # Re-create display manager with mocked rich display
            display_manager = DisplayManager(DisplayOptions(quiet=False, no_color=True, file=output))
            
            # Check initial state
            initial_success = display_manager.progress.stats.success_count
            
            # Call complete_file
            with display_manager.processing_context(total_files=1) as ctx:
                ctx.complete_file("test.pdf", "renamed_test.pdf")
                
            # Check final state
            final_success = display_manager.progress.stats.success_count
            
            print(f"Initial success: {initial_success}, Final success: {final_success}")
            
            # This should pass if our fix works
            self.assertEqual(final_success, initial_success + 1, 
                           "complete_file should increment success count")


if __name__ == '__main__':
    unittest.main()