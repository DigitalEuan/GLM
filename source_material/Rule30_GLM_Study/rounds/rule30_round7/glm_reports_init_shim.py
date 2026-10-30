"""Shim written for the Rule 30 study: the uploaded archive has no reports/__init__.py
and no LatticeGeometryReports class.  The other mixins are re-exported unchanged;
LatticeGeometryReports is an empty placeholder (its report subjects are unavailable)."""
from .development import DevelopmentReports
from .language import LanguageReports
from .ledgers import LedgerReports
from .migration import MigrationReports
from .reasoning import ReasoningReports
from .recipe import RecipeReports
from .registers import RegisterReports
from .resolution import ResolutionReports
from .semantics import SemanticsReports
from .signal import SignalReports
from .substrate import SubstrateReports


class LatticeGeometryReports:
    """Placeholder: missing from the uploaded archive."""
