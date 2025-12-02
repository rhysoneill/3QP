"""
Test suite initialization.
"""

import sys
from pathlib import Path

# Add TQP Core to path for imports
tqp_core_path = Path(__file__).parent.parent.parent / "01_TQP_Core"
if str(tqp_core_path) not in sys.path:
    sys.path.insert(0, str(tqp_core_path))
