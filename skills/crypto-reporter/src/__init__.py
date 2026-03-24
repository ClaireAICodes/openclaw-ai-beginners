#!/usr/bin/env python3
"""
Crypto Reporter Agent - Daily Cryptocurrency Analysis Skill

Generates comprehensive daily reports with fundamentals, technicals, sentiment, risks, and verdict.
"""

from .crypto_reporter import CryptoReporterAgent, Config, main

__all__ = ['CryptoReporterAgent', 'Config', 'main']
__version__ = '1.0.0'
