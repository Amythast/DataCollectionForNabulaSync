from contextvars import ContextVar

ttwid_var: ContextVar[str] = ContextVar("ttwid_var")
