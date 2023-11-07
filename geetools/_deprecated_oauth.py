# coding=utf-8
"""Legacy Authentication functions."""
from deprecated.sphinx import deprecated

import geetools


@deprecated(version="1.0.0", reason="Use geetools.User.list instead")
def list_users(credential_path=""):
    """List local users."""
    return geetools.User.list(credential_path)


@deprecated(version="1.0.0", reason="Use geetools.User.delete instead")
def delete_local_user(user="", credential_path=""):
    """Delete a user's file."""
    geetools.User.delete(user, credential_path)


@deprecated(version="1.0.0", reason="Use geetools.User.rename instead")
def rename_current_user(name="", credential_path=""):
    """Rename the current user."""
    geetools.User.rename(name, "", credential_path)


@deprecated(version="1.0.0", reason="Use geetools.User.set instead")
def Initialize(filename, credential_path="default"):
    """Initialize to GEE with the specified credentials."""
    geetools.User.set(filename, credential_path)
