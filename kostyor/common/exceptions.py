class KostyorException(Exception):
    """Base Kostyor exception to catch 'em all!"""


class NotFound(KostyorException):
    """Base exception for a series of "Not Found" exceptions."""


class BadRequest(KostyorException):
    """Base exception for a series of "Bad Request" exceptions."""


class ClusterNotFound(NotFound):
    """Cluster Not Found"""


class ClusterVersionIsUnknown(BadRequest):
    """Operations is not allowed since cluster version is unknown."""


class CannotUpgradeToLowerVersion(BadRequest):
    """Upgrade operation can be initiated only to higher version."""


class UpgradeIsInProgress(BadRequest):
    """Upgrade operation is in progress."""
