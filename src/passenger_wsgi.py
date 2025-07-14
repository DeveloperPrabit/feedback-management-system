import sys
import os

# Set project base path
project_path = '/home5/bhadahub/rental_system/src'
venv_path = '/home5/bhadahub/virtualenv/rental_system/src/3.11'

# Add project and site-packages to path
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(venv_path, 'lib/python3.11/site-packages'))

# Activate virtual environment
activate_this = os.path.join(venv_path, 'bin/activate_this.py')
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Set the settings module and import WSGI app
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_system.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
