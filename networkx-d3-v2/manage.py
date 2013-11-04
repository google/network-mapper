#!/usr/bin/env python

from networkx.utils import customize_path, setup_appengine_env
setup_appengine_env()
customize_path()

from django.core.management import execute_manager

from networkx import settings

if __name__ == "__main__":
    execute_manager(settings)
