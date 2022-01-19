#!/usr/bin/env python

"""
Set of classes implementing statistic builder for the Developer Italia community.

Clases will create stats for:
- Newsletter stats
- Site padigitale2026.gov.it
"""

from .engine import Engine
from .ganalytics_stats import GAnalytics
from .newsletter_stats import Newsletter

__all__ = [
    'Engine',
    'GAnalytics',
    'Newsletter'
]
