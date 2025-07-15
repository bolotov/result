from abc import ABC, abstractmethod
from contextlib import contextmanager
from functools import wraps
import inspect
from typing import Generic, TypeVar, Callable, Optional

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")

# MARK: Decorators for denotation

class SafetyViolation(Exception):
    """Raised when unsafe operations are called in safe context"""
    ...

class UnsafeCallError(Exception):
    """Raised when unsafe method is called inappropriately"""
    ...

# Global safety context
_safety_context = {"allow_unsafe": True}

@contextmanager
def safe_context():
    """Context manager that disables unsafe operations"""
    old_value = _safety_context["allow_unsafe"]
    _safety_context["allow_unsafe"] = False
    try:
        yield
    finally:
        _safety_context["allow_unsafe"] = old_value

@contextmanager
def unsafe_context():
    """Context manager that explicitly enables unsafe operations"""
    old_value = _safety_context["allow_unsafe"]
    _safety_context["allow_unsafe"] = True
    try:
        yield
    finally:
        _safety_context["allow_unsafe"] = old_value

def unsafe(reason: Optional[str] = None):
    """
    Mark a method as unsafe - can raise exceptions.

    Args:
        reason: Optional explanation of why this method is unsafe
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _safety_context["allow_unsafe"]:
                raise SafetyViolation(
                    f"Unsafe method '{func.__name__}' called in safe context. "
                    f"Reason: {reason or 'Can raise exceptions'}"
                )

            # Add runtime safety checks
            if hasattr(args[0], '_check_unsafe_preconditions'):
                args[0]._check_unsafe_preconditions(func.__name__)

            return func(*args, **kwargs)

        # Mark the function as unsafe for introspection
        wrapper._is_unsafe = True
        wrapper._unsafe_reason = reason
        wrapper._original_func = func
        return wrapper
    return decorator

def pure(func: F) -> F:
    """Mark a method as pure - no side effects, no exceptions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper._is_pure = True
    return wrapper

def total(func: F) -> F:
    """Mark a method as total - defined for all valid inputs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper._is_total = True
    return wrapper

def partial(reason: str):
    """Mark a method as partial - not defined for all inputs"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._is_partial = True
        wrapper._partial_reason = reason
        return wrapper
    return decorator

def composable(func: F) -> F:
    """Mark a method as composable - safe to chain"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper._is_composable = True
    return wrapper

def requires_variant(*variants: str):
    """Specify which Result variants this method requires"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if we're on the right variant
            class_name = self.__class__.__name__
            if not any(variant in class_name for variant in variants):
                raise UnsafeCallError(
                    f"Method '{func.__name__}' requires variant {variants}, "
                    f"but called on {class_name}"
                )
            return func(self, *args, **kwargs)

        wrapper._requires_variants = variants
        return wrapper
    return decorator

def safe_alternative(alternative_name: str):
    """Suggest a safe alternative for this unsafe method"""
    def decorator(func: F) -> F:
        original_func = func
        if hasattr(func, '_original_func'):
            original_func = func._original_func

        @wraps(original_func)
        def wrapper(*args, **kwargs):
            return original_func(*args, **kwargs)

        wrapper._safe_alternative = alternative_name
        # Copy over other attributes
        for attr in ['_is_unsafe', '_unsafe_reason', '_original_func']:
            if hasattr(func, attr):
                setattr(wrapper, attr, getattr(func, attr))

        return wrapper
    return decorator

def deprecate_unsafe(alternative: str):
    """Mark an unsafe method as deprecated"""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(
                f"Method '{func.__name__}' is deprecated. Use '{alternative}' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)

        wrapper._deprecated_alternative = alternative
        return wrapper
    return decorator


# MARK: Utility functions for introspection
def is_unsafe(method: Callable) -> bool:
    """Check if a method is marked as unsafe"""
    return getattr(method, '_is_unsafe', False)

def is_pure(method: Callable) -> bool:
    """Check if a method is marked as pure"""
    return getattr(method, '_is_pure', False)

def is_total(method: Callable) -> bool:
    """Check if a method is marked as total"""
    return getattr(method, '_is_total', False)

def get_unsafe_reason(method: Callable) -> Optional[str]:
    """Get the reason why a method is unsafe"""
    return getattr(method, '_unsafe_reason', None)

def get_safe_alternative(method: Callable) -> Optional[str]:
    """Get the safe alternative for an unsafe method"""
    return getattr(method, '_safe_alternative', None)

def analyze_class_safety(cls):
    """Analyze the safety profile of a class"""
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)

    safe_methods = []
    unsafe_methods = []
    pure_methods = []

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

    def __init__(self, obj):
        self._obj = obj
        self._operations = []

    def then(self, method_name: str, *args, **kwargs):
        """Chain a method call"""
        method = getattr(self._obj.__class__, method_name)
        if is_unsafe(method):
            raise SafetyViolation(f"Cannot chain unsafe method '{method_name}'")

        self._operations.append((method_name, args, kwargs))
        return self

    def execute(self):
        """Execute the chained operations"""
        result = self._obj
        for method_name, args, kwargs in self._operations:
            method = getattr(result, method_name)
            result = method(*args, **kwargs)
        return result

def safe_chain(obj):
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
    def to_dict(self) -> dict: ...

    def __bool__(self) -> bool:
        return self.is_ok()

    def __hash__(self) -> int:
        if self.is_ok():
            return hash(("ok", self.unwrap_or(None)))
        else:
            return hash(("err", self.unwrap_or_else(lambda e: e)))

class Ok(Result[T, E]):
    def __init__(self, value: T):
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
    def to_dict(self) -> dict:
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
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        return Ok(self._value)


    def __eq__(self, other):
        return isinstance(other, Ok) and self._value == other._value

    def __repr__(self): return f"Ok({self._value!r})"


class Err(Result[T, E]):
    def __init__(self, error: E):
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
    def to_dict(self) -> dict:
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
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        return Err(f(self._error))

    def __eq__(self, other):
        return isinstance(other, Err) and self._error == other._error

    def __repr__(self): return f"Err({self._error!r})"
