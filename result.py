from functools import wraps
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

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

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_ok(self._value)

    def to_dict(self) -> dict:
        return {"ok": self._value}

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return self._value

    @pure
    @total
    def map_ok(self, f: Callable[[T], U]) -> "Result[U, E]":
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

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_err(self._error)

    def to_dict(self) -> dict:
        return {"err": self._error}

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self._error)

    @pure
    @total
    def map_ok(self, f: Callable[[T], U]) -> "Result[U, E]":
        return Err(self._error)
    
    @pure
    @total
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        return Err(f(self._error))

    def __eq__(self, other):
        return isinstance(other, Err) and self._error == other._error

    def __repr__(self): return f"Err({self._error!r})"

