"""Legacy method related to binary Image classification."""
from deprecated.sphinx import deprecated


@deprecated(
    version="1.0.0",
    reason="The method was completely undocumented and has been dropped",
)
def binary(conditions, classes, mask_name="dt_mask"):
    raise NotImplementedError("The method was completely undocumented and has been dropped")
