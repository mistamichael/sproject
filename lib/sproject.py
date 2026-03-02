#!/usr/bin/env python3
"""
Projekt Rechner
Erzeugt aus den Angaben zu Resourcen, Urlaubstagen und Projekt-Angaben Reports,
wie z.B. einen Resourcenplan über der Zeit, ein Gant-Diagramm mit kritischen Pfad oder einen Kostenplan
"""

import os
import re
import json
import argparse
import configparser
from pathlib import Path
from datetime import datetime




if __name__ == "__main__":
    main()
