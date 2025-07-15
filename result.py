from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import wraps
import inspect
from typing import Generic, TypeVar, Callable, Optional, Any, cast, Dict, Union, Iterator, List, TypedDict

F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
# Generic function type for error handling - will be specialized at usage sites
F_E = TypeVar("F_E", bound=Callable[..., Any])

# MARK: Decorators for denotation

class SafetyViolation(Exception):
    """Raised when unsafe operations are called in safe context"""
    ...

class UnsafeCallError(Exception):
    """Raised when unsafe method is called inappropriately"""
    ...

# Global safety context
_safety_context: Dict[str, bool] = {"allow_unsafe": True}

@contextmanager
def safe_context() -> Iterator[None]:
    """Context manager that disables unsafe operations"""
    old_value = _safety_context["allow_unsafe"]
    _safety_context["allow_unsafe"] = False
    try:
        yield
    finally:
        _safety_context["allow_unsafe"] = old_value

@contextmanager
def unsafe_context() -> Iterator[None]:
    """Context manager that explicitly enables unsafe operations"""
    old_value = _safety_context["allow_unsafe"]
    _safety_context["allow_unsafe"] = True
    try:
        yield
    finally:
        _safety_context["allow_unsafe"] = old_value

def unsafe(reason: Optional[str] = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _safety_context["allow_unsafe"]:
                raise SafetyViolation(
                    f"Unsafe method '{func.__name__}' called in safe context. "
                    f"Reason: {reason or 'Can raise exceptions'}"
                )
            if hasattr(args[0], '_check_unsafe_preconditions'):
                args[0]._check_unsafe_preconditions(func.__name__)
            return func(*args, **kwargs)

        # Mark attributes for introspection
        setattr(wrapper, '_is_unsafe', True)
        setattr(wrapper, '_unsafe_reason', reason)
        setattr(wrapper, '_original_func', func)
        return cast(F, wrapper)
    return decorator

def pure(func: F) -> F:
    """Mark a method as pure - no side effects, no exceptions"""
    setattr(func, "_is_pure", True)
    return func

def total(func: F) -> F:
    """Mark a method as total - defined for all valid inputs"""
    setattr(func, "_is_total", True)
    return func

def partial(reason: str) -> Callable[[F], F]:
    """Mark a method as partial - not defined for all inputs"""
    def decorator(func: F) -> F:
        setattr(func, "_is_partial", True)
        setattr(func, "_partial_reason", reason)
        return func
    return decorator

def composable(func: F) -> F:
    """Mark a method as composable - safe to chain"""
    setattr(func, "_is_composable", True)
    return func

def requires_variant(*variants: str) -> Callable[[F], F]:
    """Specify which Result variants this method requires"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            class_name = self.__class__.__name__
            if not any(variant in class_name for variant in variants):
                raise UnsafeCallError(
                    f"Method '{func.__name__}' requires variant {variants}, "
                    f"but was called on {class_name}"
                )
            return func(self, *args, **kwargs)

        setattr(wrapper, "_requires_variants", variants)
        return cast(F, wrapper)
    return decorator

def safe_alternative(alternative_name: str) -> Callable[[F], F]:
    """Suggest a safe alternative for this unsafe method"""
    def decorator(func: F) -> F:
        original = getattr(func, "_original_func", func)
        setattr(original, "_safe_alternative", alternative_name)
        return cast(F, original)
    return decorator

def deprecate_unsafe(alternative: str) -> Callable[[F], F]:
    """Mark an unsafe method as deprecated"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import warnings
            warnings.warn(
                f"Method '{func.__name__}' is deprecated. Use '{alternative}' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)

        # Use setattr to avoid type checker issues with dynamic attributes
        setattr(wrapper, '_deprecated_alternative', alternative)
        return cast(F, wrapper)
    return decorator

# Type definitions for safety analysis
class UnsafeMethodInfo(TypedDict):
    name: str
    reason: Optional[str]
    alternative: Optional[str]

# MARK: Utility functions for introspection
def is_unsafe(method: Callable[..., Any]) -> bool:
    """Check if a method is marked as unsafe"""
    return getattr(method, '_is_unsafe', False)

def is_pure(method: Callable[..., Any]) -> bool:
    """Check if a method is marked as pure"""
    return getattr(method, '_is_pure', False)

def is_total(method: Callable[..., Any]) -> bool:
    """Check if a method is marked as total"""
    return getattr(method, '_is_total', False)

def get_unsafe_reason(method: Callable[..., Any]) -> Optional[str]:
    """Get the reason why a method is unsafe"""
    return getattr(method, '_unsafe_reason', None)

def get_safe_alternative(method: Callable[..., Any]) -> Optional[str]:
    """Get the safe alternative for an unsafe method"""
    return getattr(method, '_safe_alternative', None)

def analyze_class_safety(cls: type) -> SafetyAnalysis:
    """Analyze the safety profile of a class"""
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)

    safe_methods: List[str] = []
    unsafe_methods: List[UnsafeMethodInfo] = []
    pure_methods: List[str] = []

    for name, method in methods:
        if is_unsafe(method):
            unsafe_methods.append({
                'name': name,
                'reason': get_unsafe_reason(method),
                'alternative': get_safe_alternative(method)
            })
        elif is_pure(method):
            pure_methods.append(name)
        else:
            safe_methods.append(name)

    return {
        'safe_methods': safe_methods,
        'unsafe_methods': unsafe_methods,
        'pure_methods': pure_methods
    }

# Context manager for method chaining with safety
class SafeChain:
    """Fluent interface for safe method chaining"""

    def __init__(self, obj: Any) -> None:
        self._obj = obj
        self._operations: list[tuple[str, tuple[Any, ...], Dict[str, Any]]] = []

    def then(self, method_name: str, *args: Any, **kwargs: Any) -> 'SafeChain':
        """Chain a method call"""
        method = getattr(self._obj.__class__, method_name)
        if is_unsafe(method):
            raise SafetyViolation(f"Cannot chain unsafe method '{method_name}'")

        self._operations.append((method_name, args, kwargs))
        return self

    def execute(self) -> Any:
        """Execute the chained operations"""
        result = self._obj
        for method_name, args, kwargs in self._operations:
            method = getattr(result, method_name)
            result = method(*args, **kwargs)
        return result

def safe_chain(obj: Any) -> SafeChain:
    """Create a safe method chain"""
    return SafeChain(obj)

# MARK: Result class

class Result(ABC, Generic[T, E]):
    @abstractmethod
    @pure
    @total
    def is_ok(self) -> bool: ...

    @abstractmethod
    @pure
    @total
    def is_err(self) -> bool: ...

    @abstractmethod
    @pure
    @total
    def unwrap_or(self, default: T) -> T: ...

    @abstractmethod
    @pure
    @total
    def unwrap_or_else(self, f: Callable[[E], T]) -> T: ...

    @abstractmethod
    @pure
    @total
    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U: ...

    @abstractmethod
    @pure
    @total
    def to_dict(self) -> Dict[str, Union[T, E]]: ...

    def __bool__(self) -> bool:
        return self.is_ok()

#    def __hash__(self) -> int:
#        if self.is_ok():
#            return hash(("ok", self.unwrap_or(None)))
#        else:
#            return hash(("err", self.unwrap_or_else(lambda e: e)))

class Ok(Result[T, E]):
    def __init__(self, value: T) -> None:
        self._value = value

    @pure
    @total
    def is_ok(self) -> bool:
        return True

    @pure
    @total
    def is_err(self) -> bool:
        return False

    @pure
    @total
    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_ok(self._value)

    @pure
    @total
    def to_dict(self) -> Dict[str, T]:
        return {"ok": self._value}

    @pure
    @total
    def unwrap_or(self, default: T) -> T:
        return self._value

    @pure
    @total
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return self._value

    @pure
    @total
    def map(self, f: Callable[[T], U]) -> "Result[U, E]":
        return Ok(f(self._value))

    @pure
    @total
    def map_err(self, f: Callable[[E], U]) -> "Result[T, U]":
        return Ok(self._value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Ok) and self._value == other._value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

class Err(Result[T, E]):
    def __init__(self, error: E) -> None:
        self._error = error

    @pure
    @total
    def is_ok(self) -> bool:
        return False

    @pure
    @total
    def is_err(self) -> bool:
        return True

    @pure
    @total
    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_err(self._error)

    @pure
    @total
    def to_dict(self) -> Dict[str, E]:
        return {"err": self._error}

    @pure
    @total
    def unwrap_or(self, default: T) -> T:
        return default

    @pure
    @total
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self._error)

    @pure
    @total
    def map(self, f: Callable[[T], U]) -> "Result[U, E]":
        return Err(self._error)

    @pure
    @total
    def map_err(self, f: Callable[[E], U]) -> "Result[T, U]":
        return Err(f(self._error))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Err) and self._error == other._error

    def __repr__(self) -> str:
        return f"Err({self._error!r})"
