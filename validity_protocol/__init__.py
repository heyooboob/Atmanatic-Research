"""Standalone validity-packet schema and validator (TRUTH_VALIDITY_STANDARD.md).

Zero dependency on downstream products, wallets, or execution code. This
package only implements the generic claim-validation discipline: it does not
know what domain a claim comes from.

This is the canonical Atmanatic validity protocol. External consumers use it
through the published Atmanatic package and retain separate operational
promotion gates around it.
"""

from .levels import ValidityLevel
from .packet import Observation, ValidityPacket
from .store import PacketStore
from .validator import ValidationResult, advance, validate_packet

__all__ = [
    "ValidityLevel",
    "Observation",
    "ValidityPacket",
    "ValidationResult",
    "validate_packet",
    "advance",
    "PacketStore",
]
