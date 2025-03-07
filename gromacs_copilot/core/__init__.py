"""
Core module for GROMACS Copilot
"""

from gromacs_copilot.core.enums import SimulationStage, MessageType
from gromacs_copilot.core.md_agent import MDLLMAgent

__all__ = [
    'SimulationStage',
    'MessageType',
    'MDLLMAgent'
]