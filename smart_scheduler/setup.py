from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "smart_scheduler",
        ["scheduler_core.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=["-O3"] 
    ),
]

setup(
    name="smart_scheduler",
    version="2.0.0",
    ext_modules=ext_modules,
)