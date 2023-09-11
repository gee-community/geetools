"""Generic accessor to add extra function to the base GEE API classes"""

from typing import Any, Callable, Type


class Accessor:
    """Object for implementing class accessors."""

    def __init__(self, name: str, accessor: Any):
        self.name = name
        self.accessor = accessor

    def __get__(self, obj: Any, cls: Type) -> Any:
        return self.accessor(obj)


def gee_accessor(cls: Type) -> Callable:
    """Create an accessor through the geetools namespace to a given class.

    Parameters:
        cls : The class to set the accessor to.

    Returns:
        The accessor function to to the class.
    """

    def decorator(accessor: Any) -> Any:
        setattr(cls, "geetools", Accessor("geetools", accessor))
        return accessor

    return decorator