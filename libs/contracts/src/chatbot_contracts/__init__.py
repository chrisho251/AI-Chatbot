"""Typed records that workers and services exchange.

Import records from the submodules, for example chatbot_contracts.knowledge_base.
"""

from chatbot_contracts.base import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION"]
