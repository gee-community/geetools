"""Generic accessor to add extra function to the base GEE API classes."""

from typing import Any, Callable, Type


def register_class_accessor(klass: Type, name: str) -> Callable:
    """Create an accessor through the provided namespace to a given class.

    Parameters:
        klass: The class to set the accessor to.
        name: The name of the accessor namespace

    Returns:
        The accessor function to to the class.
    """

    def decorator(accessor: Any) -> Any:
        class ClassAccessor:
            def __init__(self, name: str, accessor: Any):
                self.name, self.accessor = name, accessor

            def __get__(self, obj: Any, *args) -> Any:
                return self.accessor(obj)

        # check if the accessor already exists for this class
        if hasattr(klass, name):
            raise AttributeError(f"Accessor {name} already exists for {klass}")

        # register the accessor to the class
        setattr(klass, name, ClassAccessor(name, accessor))

        return accessor

    return decorator


def register_function_accessor(func: Type, name: str) -> Callable:
    """Create an accessor through the provided namespace to a given function.

    Parameters:
        func: The function to set the accessor to.
        name: The name of the accessor namespace

    Returns:
        The accessor function to to the function.
    """

    def decorator(accessor: Any) -> Any:

        # check if the accessor already exists for this class
        if hasattr(func, name):
            raise AttributeError(f"Accessor {name} already exists for {func}")

        # register the accessor to the class
        setattr(func, name, accessor)

        return accessor

    return decorator


# this private method should not be exposed to end user as it perform 0 checks it can overwrite
# existing methods/class/member. Only used in the lib for the Computed object as the method need
# to be shared by every other child of the class.
def _register_extention(obj: Any) -> Callable:
    """Add the function to any object."""
    return lambda f: (setattr(obj, f.__name__, f) or f)  # type: ignore
