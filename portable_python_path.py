import sys 
import os 
 
# Add portable site-packages to Python path 
script_dir = os.path.dirname(os.path.abspath(__file__)) 
site_packages = os.path.join(script_dir, 'portable_python', 'site-packages') 
if os.path.exists(site_packages) and site_packages not in sys.path: 
    sys.path.insert(0, site_packages) 
