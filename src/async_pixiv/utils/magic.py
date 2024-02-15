import builtins as __builtin__
import ctypes
import gc
import inspect
from collections import defaultdict
from contextlib import contextmanager
from ctypes import CFUNCTYPE, Structure, c_int32, c_int64, c_void_p, py_object
from functools import wraps
from typing import Any, Callable, Generator, ParamSpec, TypeVar

__all__ = "curse", "curses", "reverse"

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")

Py_ssize_t = c_int64 if ctypes.sizeof(c_void_p) == 8 else c_int32


# dictionary holding references to the allocated function resolution
# arrays to type objects
tp_as_dict = {}
# container to cfunc callbacks
tp_func_dict = {}


class PyObject(Structure):
    def incref(self):
        self.ob_refcnt += 1

    def decref(self):
        self.ob_refcnt -= 1


class PyFile(Structure):
    pass


PyObject_p = py_object
Inquiry_p = CFUNCTYPE(ctypes.c_int, PyObject_p)
# return type is void* to allow ctypes to convert python integers to
# plain PyObject*
UnaryFunc_p = CFUNCTYPE(py_object, PyObject_p)
BinaryFunc_p = CFUNCTYPE(py_object, PyObject_p, PyObject_p)
TernaryFunc_p = CFUNCTYPE(py_object, PyObject_p, PyObject_p, PyObject_p)
LenFunc_p = CFUNCTYPE(Py_ssize_t, PyObject_p)
SSizeArgFunc_p = CFUNCTYPE(py_object, PyObject_p, Py_ssize_t)
SSizeObjArgProc_p = CFUNCTYPE(ctypes.c_int, PyObject_p, Py_ssize_t, PyObject_p)
ObjObjProc_p = CFUNCTYPE(ctypes.c_int, PyObject_p, PyObject_p)

FILE_p = ctypes.POINTER(PyFile)


def get_not_implemented():
    namespace = {}
    name = "_Py_NotImplmented"
    # noinspection PyProtectedMember
    not_implemented = ctypes.cast(ctypes.pythonapi._Py_NotImplementedStruct, py_object)

    ctypes.pythonapi.PyDict_SetItem(
        py_object(namespace), py_object(name), not_implemented
    )
    return namespace[name]


# address of the _Py_NotImplementedStruct singleton
NotImplementedRet = get_not_implemented()


class PyNumberMethods(Structure):
    _fields_ = [
        ("nb_add", BinaryFunc_p),
        ("nb_subtract", BinaryFunc_p),
        ("nb_multiply", BinaryFunc_p),
        ("nb_remainder", BinaryFunc_p),
        ("nb_divmod", BinaryFunc_p),
        ("nb_power", BinaryFunc_p),
        ("nb_negative", UnaryFunc_p),
        ("nb_positive", UnaryFunc_p),
        ("nb_absolute", UnaryFunc_p),
        ("nb_bool", Inquiry_p),
        ("nb_invert", UnaryFunc_p),
        ("nb_lshift", BinaryFunc_p),
        ("nb_rshift", BinaryFunc_p),
        ("nb_and", BinaryFunc_p),
        ("nb_xor", BinaryFunc_p),
        ("nb_or", BinaryFunc_p),
        ("nb_int", UnaryFunc_p),
        ("nb_reserved", ctypes.c_void_p),
        ("nb_float", UnaryFunc_p),
        ("nb_inplace_add", BinaryFunc_p),
        ("nb_inplace_subtract", BinaryFunc_p),
        ("nb_inplace_multiply", BinaryFunc_p),
        ("nb_inplace_remainder", BinaryFunc_p),
        ("nb_inplace_power", TernaryFunc_p),
        ("nb_inplace_lshift", BinaryFunc_p),
        ("nb_inplace_rshift", BinaryFunc_p),
        ("nb_inplace_and", BinaryFunc_p),
        ("nb_inplace_xor", BinaryFunc_p),
        ("nb_inplace_or", BinaryFunc_p),
        ("nb_floor_divide", BinaryFunc_p),
        ("nb_true_divide", BinaryFunc_p),
        ("nb_inplace_floor_divide", BinaryFunc_p),
        ("nb_inplace_true_divide", BinaryFunc_p),
        ("nb_index", BinaryFunc_p),
        ("nb_matrix_multiply", BinaryFunc_p),
        ("nb_inplace_matrix_multiply", BinaryFunc_p),
    ]


class PySequenceMethods(Structure):
    _fields_ = [
        ("sq_length", LenFunc_p),
        ("sq_concat", BinaryFunc_p),
        ("sq_repeat", SSizeArgFunc_p),
        ("sq_item", SSizeArgFunc_p),
        ("was_sq_slice", ctypes.c_void_p),
        ("sq_ass_item", SSizeObjArgProc_p),
        ("was_sq_ass_slice", ctypes.c_void_p),
        ("sq_contains", ObjObjProc_p),
        ("sq_inplace_concat", BinaryFunc_p),
        ("sq_inplace_repeat", SSizeArgFunc_p),
    ]


class PyMappingMethods(Structure):
    pass


class PyTypeObject(Structure):
    pass


class PyAsyncMethods(Structure):
    pass


PyObject._fields_ = [
    ("ob_refcnt", Py_ssize_t),
    ("ob_type", ctypes.POINTER(PyTypeObject)),
]

PyTypeObject._fields_ = [
    ("ob_base", PyObject),
    ("ob_size", Py_ssize_t),
    # declaration
    ("tp_name", ctypes.c_char_p),
    ("tp_basicsize", Py_ssize_t),
    ("tp_itemsize", Py_ssize_t),
    ("tp_dealloc", CFUNCTYPE(None, PyObject_p)),
    ("printfunc", CFUNCTYPE(ctypes.c_int, PyObject_p, FILE_p, ctypes.c_int)),
    ("getattrfunc", CFUNCTYPE(PyObject_p, PyObject_p, ctypes.c_char_p)),
    (
        "setattrfunc",
        CFUNCTYPE(ctypes.c_int, PyObject_p, ctypes.c_char_p, PyObject_p),
    ),
    ("tp_as_async", CFUNCTYPE(PyAsyncMethods)),
    ("tp_repr", CFUNCTYPE(PyObject_p, PyObject_p)),
    ("tp_as_number", ctypes.POINTER(PyNumberMethods)),
    ("tp_as_sequence", ctypes.POINTER(PySequenceMethods)),
    ("tp_as_mapping", ctypes.POINTER(PyMappingMethods)),
    ("tp_hash", CFUNCTYPE(ctypes.c_int64, PyObject_p)),
    ("tp_call", CFUNCTYPE(PyObject_p, PyObject_p, PyObject_p, PyObject_p)),
    ("tp_str", CFUNCTYPE(PyObject_p, PyObject_p)),
]


PyTypeObject_as_types_dict = {
    "tp_as_async": PyAsyncMethods,
    "tp_as_number": PyNumberMethods,
    "tp_as_sequence": PySequenceMethods,
    "tp_as_mapping": PyMappingMethods,
}


def patchable_builtin(klass):
    refs = gc.get_referents(klass.__dict__)
    assert len(refs) == 1
    return refs[0]


@wraps(__builtin__.dir)
def __filtered_dir__(obj=None):
    name = hasattr(obj, "__name__") and obj.__name__ or obj.__class__.__name__
    if obj is None:
        # Return names from the local scope of the calling frame,
        # taking into account indirection added by __filtered_dir__
        calling_frame = inspect.currentframe().f_back
        return sorted(calling_frame.f_locals.keys())
    return sorted(set(__dir__(obj)).difference(__hidden_elements__[name]))


# Switching to the custom dir impl declared above
__hidden_elements__ = defaultdict(list)
__dir__ = dir
__builtin__.dir = __filtered_dir__

as_number = (
    "tp_as_number",
    [
        ("add", "nb_add"),
        ("sub", "nb_subtract"),
        ("mul", "nb_multiply"),
        ("mod", "nb_remainder"),
        ("pow", "nb_power"),
        ("neg", "nb_negative"),
        ("pos", "nb_positive"),
        ("abs", "nb_absolute"),
        ("bool", "nb_bool"),
        ("inv", "nb_invert"),
        ("invert", "nb_invert"),
        ("lshift", "nb_lshift"),
        ("rshift", "nb_rshift"),
        ("and", "nb_and"),
        ("xor", "nb_xor"),
        ("or", "nb_or"),
        ("int", "nb_int"),
        ("float", "nb_float"),
        ("iadd", "nb_inplace_add"),
        ("isub", "nb_inplace_subtract"),
        ("imul", "nb_inplace_multiply"),
        ("imod", "nb_inplace_remainder"),
        ("ipow", "nb_inplace_power"),
        ("ilshift", "nb_inplace_lshift"),
        ("irshift", "nb_inplace_rshift"),
        ("iadd", "nb_inplace_and"),
        ("ixor", "nb_inplace_xor"),
        ("ior", "nb_inplace_or"),
        ("floordiv", "nb_floor_divide"),
        ("div", "nb_true_divide"),
        ("ifloordiv", "nb_inplace_floor_divide"),
        ("idiv", "nb_inplace_true_divide"),
        ("index", "nb_index"),
        ("matmul", "nb_matrix_multiply"),
        ("imatmul", "nb_inplace_matrix_multiply"),
    ],
)

as_sequence = (
    "tp_as_sequence",
    [
        ("len", "sq_length"),
        ("concat", "sq_concat"),
        ("repeat", "sq_repeat"),
        ("getitem", "sq_item"),
        ("setitem", "sq_ass_item"),
        ("contains", "sq_contains"),
        ("iconcat", "sq_inplace_concat"),
        ("irepeat", "sq_inplace_repeat"),
    ],
)

as_async = (
    "tp_as_async",
    [
        ("await", "am_await"),
        ("aiter", "am_aiter"),
        ("anext", "am_anext"),
    ],
)

override_dict = {}
for override in [as_number, as_sequence, as_async]:
    tp_as_name = override[0]
    for dunder, impl_method in override[1]:
        override_dict["__{}__".format(dunder)] = (tp_as_name, impl_method)

# divmod isn't a dunder, still make it overridable
override_dict["divmod()"] = ("tp_as_number", "nb_divmod")
override_dict["__str__"] = ("tp_str", "tp_str")


def _is_dunder(func_name: str) -> bool:
    return func_name.startswith("__") and func_name.endswith("__")


# noinspection PyProtectedMember,PyUnboundLocalVariable
def _curse_special(klass: type[T], attr: str, func: Callable[P, R]) -> None:
    """
    Curse one of the "dunder" methods, i.e. methods beginning with __ which have a
    precial resolution code path
    """
    assert callable(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """
        This wrapper returns the address of the resulting object as a
        python integer which is then converted to a pointer by ctypes
        """
        try:
            return func(*args, **kwargs)
        except NotImplementedError:
            return NotImplementedRet

    type_as_name, implement_method = override_dict[attr]

    # get the pointer to the correct tp_as_* structure
    # or create it if it doesn't exist
    type_obj = PyTypeObject.from_address(id(klass))
    if type_as_name in PyTypeObject_as_types_dict:
        struct_ty = PyTypeObject_as_types_dict[type_as_name]
        tp_as_ptr = getattr(type_obj, type_as_name)
        if not tp_as_ptr:
            # allocate new array
            tp_as_obj = struct_ty()
            tp_as_dict[(klass, attr)] = tp_as_obj
            tp_as_new_ptr = ctypes.cast(
                ctypes.addressof(tp_as_obj), ctypes.POINTER(struct_ty)
            )

            setattr(type_obj, type_as_name, tp_as_new_ptr)
        tp_as = tp_as_ptr[0]

        # find the C function type
        for function_name, function_type in struct_ty._fields_:
            if function_name == implement_method:
                c_function_type = function_type

        cfunc = c_function_type(wrapper)
        tp_func_dict[(klass, attr)] = cfunc

        setattr(tp_as, implement_method, cfunc)
    else:
        # find the C function type
        for function_name, function_type in PyTypeObject._fields_:
            if function_name == implement_method:
                c_function_type = function_type

        if (klass, attr) not in tp_as_dict:
            tp_as_dict[(klass, attr)] = ctypes.cast(
                getattr(type_obj, implement_method), c_function_type
            )

        # override function call
        cfunc = c_function_type(wrapper)
        tp_func_dict[(klass, attr)] = cfunc
        setattr(type_obj, implement_method, cfunc)


# noinspection PyProtectedMember,PyUnboundLocalVariable
def _revert_special(klass: type[T], attr: str) -> None:
    type_as_name, implement_method = override_dict[attr]
    type_obj = PyTypeObject.from_address(id(klass))
    tp_as_ptr = getattr(type_obj, type_as_name)
    if tp_as_ptr:
        if type_as_name in PyTypeObject_as_types_dict:
            tp_as = tp_as_ptr[0]

            struct_ty = PyTypeObject_as_types_dict[type_as_name]
            for func_name, func_type in struct_ty._fields_:
                if func_name == implement_method:
                    cfunc_t = func_type

            setattr(
                tp_as, implement_method, ctypes.cast(ctypes.c_void_p(None), cfunc_t)
            )
        else:
            if (klass, attr) not in tp_as_dict:
                # we didn't save this pointer
                # most likely never cursed
                return

            cfunc = tp_as_dict[(klass, attr)]
            setattr(type_obj, implement_method, cfunc)


def curse(klass: type[T], attr: str, value: Any, hide_from_dir: bool = False) -> None:
    """Curse a built-in `klass` with `attr` set to `value`

    This function monkey-patches the built-in python object `attr` adding a new
    attribute to it. You can add any kind of argument to the `class`.
    """
    if _is_dunder(attr):
        _curse_special(klass, attr, value)
        return

    dikt = patchable_builtin(klass)

    old_value = dikt.get(attr, None)
    old_name = "_c_%s" % attr  # do not use .format here, it breaks py2.{5,6}

    # Patch the thing
    dikt[attr] = value

    if old_value:
        hide_from_dir = False  # It was already in dir
        dikt[old_name] = old_value

        try:
            dikt[attr].__name__ = old_value.__name__
        except (AttributeError, TypeError):  # py2.5 will raise `TypeError`
            pass
        try:
            dikt[attr].__qualname__ = old_value.__qualname__
        except AttributeError:
            pass

    ctypes.pythonapi.PyType_Modified(py_object(klass))

    if hide_from_dir:
        __hidden_elements__[klass.__name__].append(attr)


def reverse(klass: type[T], attr: str) -> None:
    """Reverse a curse in a built-in object

    This function removes *new* attributes. It is actually possible to remove
    any kind of attribute from any built-in class, but just DON'T DO IT :)
    """
    if _is_dunder(attr):
        _revert_special(klass, attr)
        return

    dikt = patchable_builtin(klass)
    del dikt[attr]

    ctypes.pythonapi.PyType_Modified(py_object(klass))


def curses(
    klass: type[T], name: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to add decorated method named `name` the class `klass`"""

    def wrapper(func: Callable[P, R]) -> Callable[P, R]:
        curse(klass, func.__name__ if name is None else name, func)
        return func

    return wrapper


@contextmanager
def cursed(
    klass: type[T], attr: str, val: Any, hide_from_dir: bool = False
) -> Generator:
    curse(klass, attr, val, hide_from_dir)
    try:
        yield
    finally:
        reverse(klass, attr)
