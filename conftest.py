"""Garante que a raiz do projeto esteja no sys.path para os testes importarem `src`."""
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
