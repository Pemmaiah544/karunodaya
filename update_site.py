#!/usr/bin/env python
"""
Script to update the site domain for password reset emails.
Run this after adding django.contrib.sites to INSTALLED_APPS.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'karunodaya_project.settings')
django.setup()

from django.contrib.sites.models import Site

# Update the default site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # For development
site.name = 'Karunodaya'
site.save()

print(f"Site updated: {site.domain} - {site.name}")
