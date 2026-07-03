#!/usr/bin/env python
import os, sys
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.urls import get_resolver, resolve
from django.conf import settings

# 1. Check MEDIA settings
print('MEDIA_URL:', repr(settings.MEDIA_URL))
print('MEDIA_ROOT:', repr(settings.MEDIA_ROOT))

# 2. Check file exists
path = os.path.join(settings.MEDIA_ROOT, 'faces', 'swat_cad5eb5eee184d619331dd2ebb6549be.jpg')
print('File exists:', os.path.exists(path))
print('File path:', path)

# 3. List all URL patterns
resolver = get_resolver()
print('\nAll URL patterns:')
for pattern in resolver.url_patterns:
    print(' ', pattern.pattern)

# 4. Try to resolve media URL
try:
    match = resolve('media/faces/test.jpg')
    print('\nURL matched:', match.func)
except Exception as e:
    print('\nURL resolve failed:', e)

# 5. Try with leading slash
try:
    match = resolve('/media/faces/test.jpg')
    print('URL matched with /:', match.func)
except Exception as e:
    print('URL resolve with / failed:', e)
