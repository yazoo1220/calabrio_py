from .api import ApiClient, AsyncApiClient

# Optional: manager utilities depend on heavy packages (e.g., pandas, numpy, tqdm).
# Expose them only if dependencies are available to avoid import-time failures.
try:
    from .manager import ConfigManager, PeopleManager, PersonAccountsManager
except Exception as _e:  # pragma: no cover
    class _MissingOptionalDependency:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "Manager utilities require optional dependencies. Install extras: calabrio_py[pandas]"
            ) from _e

    ConfigManager = _MissingOptionalDependency  # type: ignore
    PeopleManager = _MissingOptionalDependency  # type: ignore
    PersonAccountsManager = _MissingOptionalDependency  # type: ignore
