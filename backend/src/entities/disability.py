from enum import StrEnum


class Disability(StrEnum):
    """
    Enum representing the disabilities.
    """

    VISUEL = "visuel"
    AUDITIF = "auditif"
    MENTAL = "mental"
    PSYCHIQUE = "psychique"
    COGNITIF = "cognitif"
    AUTRE = "autre"
