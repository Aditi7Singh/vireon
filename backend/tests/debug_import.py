import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.vendor_services import detect_saas_vendors
print("Import successful")
