
from luigi import build, LuigiStatusCode

from task import Validation, VennGraph, checkDependency, tree

build([VennGraph(),Validation(),checkDependency(),tree(),checkDependency(dependency_to_check="cryptography")], local_scheduler=True, detailed_summary=True)
