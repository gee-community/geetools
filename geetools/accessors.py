"""Generic accessor to add extra function to the base GEE API classes."""

from typing import Any, Callable, Type


class Accessor:
    """Object for implementing class accessors."""

    def __init__(self, name: str, accessor: Any):
        """Initialize the accessor."""
        self.name = name
        self.accessor = accessor

    def __get__(self, obj: Any, cls: Type) -> Any:
        """Get the accessor."""
        return self.accessor(obj)


def geetools_accessor(cls: Type) -> Callable:
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


def geetools_extend(obj: Any) -> Callable:
    """Extends the objcect whatever the type.

    Be careful when using this decorator as it can override direct members of the existing object.

    Parameters:
        cls: Class to extend.

    Returns:
        Decorator for extending classes.
    """
    return lambda f: (setattr(obj, f.__name__, f) or f)
