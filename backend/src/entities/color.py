# see https://www.msdmanuals.com/fr/accueil/multimedia/table/classification-de-fitzpatrick-pour-les-types-de-peau
from enum import StrEnum


class SkinColor(StrEnum):
    """
    Enum representing the skin colors.
    """

    CLAIRE = "claire"
    NOIRE = "noire"
    MATE = "mate"
    FONCEE = "foncée"
