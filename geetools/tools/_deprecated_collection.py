"""Legacy ``ee.Collection`` methods."""
from deprecated.sphinx import deprecated


@deprecated(version="1.0.0", reason="Use map without indices instead.")
def enumerate(collection):
    """Create a list of lists in which each element of the list is: [index, element]."""
    raise Exception("Use map without indices instead.")
