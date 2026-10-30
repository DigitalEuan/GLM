"""Safe respelling feature gate.

The reorganized upload retained the CLI fallback call sites but omitted the
owner's optional respelling implementation.  Keep the fallback disabled until
that implementation is supplied; the primary routed reading remains unchanged.
"""


def enabled() -> bool:
    """Return whether optional respelling is available in this checkout."""
    return False
