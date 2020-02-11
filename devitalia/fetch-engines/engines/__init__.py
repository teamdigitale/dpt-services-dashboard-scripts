#!/usr/bin/env python

"""
Set of classes implementing statistic builder for the Developer Italia community.

Clases will create stats for:
- GitHub
- Slack
- Mailing list
- Forum
- Catalogo OSS
- Site developers/italia
"""

from .engine import Engine
from .github_stats import GitHub
from .slack_stats import Slack
from .forum_stats import Forum
from .ganalytics_stats import GAnalytics
from .onboarding_stats import Onboarding
from .catalogo_stats import Catalogo
from .catalogoregioni_stats import CatalogoRegioni
from .catalogocategories_stats import CatalogoCategories
from .catalogoaudiences_stats import CatalogoAudiences

__all__ = [
    'Engine',
    'GitHub', 'Slack', 'Forum', 'GAnalytics',
    'Onboarding',
    'Catalogo', 'CatalogoRegioni', 'CatalogoCategories', 'CatalogoAudiences'
]
