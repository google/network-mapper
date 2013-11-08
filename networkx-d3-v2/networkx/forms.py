"""Form-handlers for visualization mutation."""
import logging

from django import forms
from django.forms.widgets import RadioSelect, HiddenInput
from google.appengine.api import users


# TODO(keroserene): Decide whether to delete this file.

# def clean_spreadsheet_link(self):
  # link = self.cleaned_data['spreadsheet_link']
  # error_msg = "This URL doesn't look like a valid spreadsheet."
  # if u'' == link:
    # return link
  # try:
    # path, params = link.split('?')
  # except ValueError:
    # raise forms.ValidationError(error_msg)
  # if '#gid=' in params:
    # splitted_params = params[:params.find('#gid=')].split('&')
  # else:
    # splitted_params = params.split('&')
  # for param in splitted_params:
    # key, value = param.split('=')
    # if 'key' == key:
      # return value
  # raise forms.ValidationError(error_msg)
