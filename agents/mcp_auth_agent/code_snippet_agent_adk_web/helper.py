import json
from typing import Any

def _jsonable(obj: Any, _seen: set[int] | None = None) -> Any:
    if _seen is None:
        _seen = set()
    oid = id(obj)
    if oid in _seen:
        return "<cyclic-ref>"
    _seen.add(oid)

    # Primitives
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # Mappings
    if isinstance(obj, dict):
        return {str(k): _jsonable(v, _seen) for k, v in obj.items()}

    # Iterables
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v, _seen) for v in obj]

    # Pydantic-like
    if hasattr(obj, "model_dump"):
        try:
            return _jsonable(obj.model_dump(), _seen)
        except Exception:
            pass

    # ADK contexts sometimes expose .state (mapping-like)
    if hasattr(obj, "state"):
        try:
            return {
                "type": type(obj).__name__,
                "state": _jsonable(dict(getattr(obj, "state")), _seen),
            }
        except Exception:
            # Fallback to __dict__ below
            pass

    # Generic objects
    if hasattr(obj, "__dict__"):
        return {
            "__type__": type(obj).__name__,
            **{k: _jsonable(v, _seen) for k, v in vars(obj).items()},
        }

    # Last resort
    return repr(obj)

def context_to_json(context: Any) -> str:
    """Best-effort JSON dump of ADK ReadonlyContext (or any object)."""
    try:
        data = _jsonable(context)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"failed to serialize context: {e}", "repr": repr(context)})
