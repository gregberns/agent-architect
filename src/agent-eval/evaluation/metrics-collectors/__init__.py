"""
Metrics Collection System for Agent Evaluation

This package provides tools for:
- Calculating task and epoch scores from validation results
- Generating comprehensive reports in JSON and CSV formats  
- Analyzing trends and patterns across multiple epochs
"""

from .score_calculator import ScoreCalculator, TaskScore, EpochScore
from .report_generator import ReportGenerator
from .epoch_analyzer import EpochAnalyzer, TrendAnalysis, TaskProgression

__all__ = [
    'ScoreCalculator', 'TaskScore', 'EpochScore',
    'ReportGenerator', 
    'EpochAnalyzer', 'TrendAnalysis', 'TaskProgression'
]