#!/usr/bin/env python3
"""Melodia launcher — invoked by the installed /usr/bin/melodia binary."""
import sys
import os

# Allow running from source tree: python3 melodia.py
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if os.path.isdir(src_dir):
    sys.path.insert(0, src_dir)

from melodia.main import main

if __name__ == '__main__':
    sys.exit(main())
