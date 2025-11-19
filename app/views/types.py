import ctypes
from typing import NewType

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), 
                ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

DataBlobPointer = NewType('DataBlobPointer', ctypes.POINTER(DATA_BLOB))