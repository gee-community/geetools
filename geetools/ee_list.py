"""Extra methods for the :py:class:`ee.List` class."""
from __future__ import annotations

import ee

from .accessors import register_class_accessor


@register_class_accessor(ee.List, "geetools")
class ListAccessor:
    """Toolbox for the :py:class:`ee.List` class."""

    def __init__(self, obj: ee.List):
        """Initialize the List class."""
        self._obj = obj

    def product(self, other: list | ee.List) -> ee.List:
        """Compute the cartesian product of 2 list.

        Values will all be considered as string and will be joined with **no spaces**.

        Parameters:
            other: The list to compute the cartesian product with.

        Returns:
            A list of strings corresponding to the cartesian product.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["a", "b", "c"])

                l1.geetools.product(l2).getInfo()
        """
        l1 = ee.List(self._obj).map(lambda e: ee.String(e))
        l2 = ee.List(other).map(lambda e: ee.String(e))
        product = l1.map(
            lambda e: l2.map(lambda f: ee.Algorithms.String(e).cat(ee.Algorithms.String(f)))
        )
        return product.flatten()

    def complement(self, other: list | ee.List) -> ee.List:
        """Compute the complement of the current list and the ``other`` list.

        The mathematical complement is the list of elements that are in the current list but not in the ``other`` list and vice-versa.

        Parameters:
            other: The list to compute the complement with.

        Returns:
            A list of strings corresponding to the complement of the current list and the ``other`` list.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["2", "3", "4"])

                l1.geetools.complement(l2).getInfo()
        """
        l1, l2 = ee.List(self._obj), ee.List(other)
        return l1.removeAll(l2).cat(l2.removeAll(l1))

    def intersection(self, other: list | ee.List) -> ee.List:
        """Compute the intersection of the current list and the ``other`` list.

        The intersection is the list of elements that are in both lists.

        Parameters:
            other: The list to compute the intersection with.

        Returns:
            A list of strings corresponding to the intersection of the current list and the ``other`` list.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["2", "3", "4"])

                l1.geetools.intersection(l2).getInfo()
        """
        l1, l2 = ee.List(self._obj), ee.List(other)
        return l1.removeAll(l1.removeAll(l2))

    def union(self, other: list | ee.List) -> ee.List:
        """Compute the union of the current list and the ``other`` list.

        This list will drop duplicated items.

        Parameters:
            other: The list to compute the union with.

        Returns:
            A list of strings corresponding to the union of the current list and the ``other`` list.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l1 = ee.List(["1", "2", "3"])
                l2 = ee.List(["2", "3", "4"])

                l1.geetools.union(l2).getInfo()
        """
        l1, l2 = ee.List(self._obj), ee.List(other)
        return l1.cat(l2).distinct()

    # this method is simply a del but the name is protected in the GEE context
    def delete(self, index: int | ee.Number) -> ee.List:
        """Delete an element from a list.

        Parameters:
            index: The index of the element to delete.

        Returns:
            The list without the element at the given index.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List(["a", "b", "c"])
                l.geetools.delete(1).getInfo()
        """
        index = ee.Number(index).toInt()
        return self._obj.slice(0, index).cat(self._obj.slice(index.add(1)))

    @classmethod
    def sequence(
        cls,
        ini: int | ee.Number,
        end: int | ee.Number,
        step: int | ee.Number = 1,
    ) -> ee.List:
        """Create a sequence from ini to end by step.

        Similar to :py:meth:`ee.List.sequence`, but if ``end != last`` item then adds the end to the end of the resulting list.

        Parameters:
            ini: The initial value of the sequence.
            end: The final value of the sequence.
            step: The step of the sequence.

        Returns:
            A list of numbers corresponding to the sequence.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List.geetools.sequence(0, 11, 2)
                l.getInfo()
        """
        ini, end = ee.Number(ini), ee.Number(end)
        step = ee.Number(step).toInt().max(1)
        return ee.List.sequence(ini, end, step).add(end.toFloat()).distinct()

    def replaceMany(self, replace: dict | ee.Dictionary) -> ee.List:
        """Replace many values in a list.

        Parameters:
            replace: the dictionary with the values to replace. the keys are the values to replace and the values are the new values.

        Returns:
            A list with the values replaced.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List(["a", "b", "c"])
                replace = ee.Dictionary({"a": "foo", "c": "bar"})
                l = l.geetools.replaceMany(replace)
                l.getInfo()
        """
        replace = ee.Dictionary(replace)
        keys = replace.keys()
        list = keys.iterate(lambda k, p: ee.List(p).replace(k, replace.get(k)), self._obj)
        return ee.List(list)  # to avoid returning a ComputedObject

    def join(self, separator: str | ee.String = ", ") -> ee.String:
        """Format a list to a string.

        Same as the join method but elements that cannot be stringtified will be returned as the object type.

        Parameters:
            separator: The separator to use.

        Returns:
            A string with the list elements separated by commas.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List(['a', 1, ee.Image(0)])
                l = l.geetools.join()
                l.getInfo()
        """
        return self.toStrings().join(separator)

    def toStrings(self) -> ee.List:
        """Convert elements of a list into Strings.

        If the list contains other elements that are not strings or numbers, it will return the object type. For example, ``['a', 1, ee.Image(0)] -> ['a', '1', 'Image']``.

        Returns:
            A list of strings corresponding to the elements of the list.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List(["a", 1, ee.Image(0)])
                l = l.geetools.toStrings()
                l.getInfo()
        """
        klasses = ee.List(["Float", "Integer", "String"])

        def getString(el):
            otype = ee.Algorithms.ObjectType(el)
            stringReady = klasses.contains(otype)
            return ee.Algorithms.If(stringReady, ee.Algorithms.String(el), otype)

        return self._obj.map(getString)

    def zip(self) -> ee.List:
        """Zip a list of lists.

        The nested lists need to all have the same size. The size of the first element will be taken as reference.

        Returns:
            A list of lists with the zipped elements.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List([[1,2,3], [4,5,6], [7,8,9]])
                l = l.geetools.zip()
                l.getInfo()
        """
        indices = ee.List.sequence(0, ee.List(self._obj.get(0)).size().subtract(1))
        return indices.map(lambda i: self._obj.map(lambda j: ee.List(j).get(i)))

    def chunked(self, parts: int | ee.Number) -> ee.List:
        """Break a :py:class:`ee.List` into lists of length `parts`.

        Args:
            parts: the number of parts to get.

        Returns:
            a list of lists.

        Examples:
            .. jupyter-execute::

                import ee, geetools
                from geetools.utils import initialize_documentation

                initialize_documentation()

                l = ee.List([1,2,3,4,5,6,7,8,9])
                l = l.geetools.chunked(3)
                l.getInfo()
        """
        size = self._obj.size()
        parts = ee.Number(parts).toInt()
        elements = size.divide(parts).floor()
        inx_list = ee.List.sequence(0, parts.subtract(1))
        # last chunk
        mod = size.mod(elements)
        rest = self._obj.slice(size.subtract(mod), size)

        def compute_parts(inx):
            inx = ee.Number(inx)
            start = inx.multiply(parts)
            end = start.add(elements)
            # handle last chunk (all this to avoid using ee.Algorithms.If)
            is_last = size.subtract(start).subtract(elements).eq(mod)
            tmp_rest = rest.map(lambda n: ee.Number(n).multiply(is_last))
            tmp_rest = tmp_rest.filter(ee.Filter.neq("item", 0))
            sl = self._obj.slice(start, end).cat(tmp_rest)
            return sl

        return ee.List(inx_list.map(compute_parts))
