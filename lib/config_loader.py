from __future__ import annotations

from importlib import import_module
from typing import List

from lib.models import (
    SUPPORTED_PROVIDERS,
    SetupEntry,
    as_tuple,
    is_callable_target,
    validate_os_targets,
)


def load_config(module_name: str = "config") -> List[SetupEntry]:
    module = import_module(module_name)
    raw_config = getattr(module, "CONFIG", None)
    if raw_config is None:
        raise ValueError("config.py must define CONFIG")
    if not isinstance(raw_config, list):
        raise ValueError("CONFIG must be a list of entry dictionaries")
    return [parse_entry(item, index) for index, item in enumerate(raw_config)]


def parse_entry(raw: object, index: int = 0) -> SetupEntry:
    if not isinstance(raw, dict):
        raise ValueError(f"Config entry #{index} must be a dictionary")

    name = _require_string(raw, "name", index)
    provider = _require_string(raw, "provider", index)
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(
            f"Config entry '{name}' uses unsupported provider '{provider}'. "
            f"Supported providers: {supported}"
        )

    target = _parse_target(raw.get("target"), provider)
    os_targets = validate_os_targets(as_tuple(raw.get("os"), "os"))
    tags = as_tuple(raw.get("tags"), "tags")
    return SetupEntry(name=name, provider=provider, target=target, os_targets=os_targets, tags=tags)


def _require_string(raw: dict, key: str, index: int) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Config entry #{index} must define a non-empty string '{key}'")
    return value.strip()


def _parse_target(value: object, provider: str) -> object:
    if provider == "function":
        if not is_callable_target(value):
            raise ValueError(
                "Expected 'target' to be a callable or an import string for function provider"
            )
        _validate_function_target(value)
        return value
    return as_tuple(value, "target")


def _validate_function_target(value: object) -> None:
    if callable(value):
        return
    _resolve_function_target(value)


def resolve_function_target(value: object):
    return _resolve_function_target(value)


def _resolve_function_target(value: object):
    if callable(value):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Function target must be a callable or import string")
    module_name, separator, attr_name = value.partition(":")
    if not separator or not module_name.strip() or not attr_name.strip():
        raise ValueError(
            "Function target import string must use 'module.path:callable_name' format"
        )
    module = import_module(module_name.strip())
    target = getattr(module, attr_name.strip(), None)
    if target is None or not callable(target):
        raise ValueError(f"Function target '{value}' did not resolve to a callable")
    return target
