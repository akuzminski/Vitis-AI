

#
# Copyright 2019 Xilinx Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Logging utilities."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging as _logging
import os as _os
import sys as _sys
import time as _time
import traceback as _traceback
from logging import DEBUG
from logging import ERROR
from logging import FATAL
from logging import INFO
from logging import WARN
from logging import NOTSET
import threading

# Don't use this directly. Use get_logger() instead.
_logger = None
_logger_lock = threading.Lock()

_logging_fmt = "%(nndct_prefix)s %(message)s"

_level_names = {
    FATAL: 'FATAL',
    ERROR: 'ERROR',
    WARN: 'WARN',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
}

def _get_caller(offset=3):
  """Returns a code and frame object for the lowest non-logging stack frame."""
  # Use sys._getframe().  This avoids creating a traceback object.
  # pylint: disable=protected-access
  f = _sys._getframe(offset)
  # pylint: enable=protected-access
  our_file = f.f_code.co_filename
  f = f.f_back
  while f:
    code = f.f_code
    if code.co_filename != our_file:
      return code, f
    f = f.f_back
  return None, None

# The definition of `findCaller` changed in Python 3.2,
# and further changed in Python 3.8
if _sys.version_info.major >= 3 and _sys.version_info.minor >= 8:

  def _logger_find_caller(stack_info=False, stacklevel=1):  # pylint: disable=g-wrong-blank-lines
    code, frame = _get_caller(4)
    sinfo = None
    if stack_info:
      sinfo = '\n'.join(_traceback.format_stack())
    if code:
      return (code.co_filename, frame.f_lineno, code.co_name, sinfo)
    else:
      return '(unknown file)', 0, '(unknown function)', sinfo
elif _sys.version_info.major >= 3 and _sys.version_info.minor >= 2:

  def _logger_find_caller(stack_info=False):  # pylint: disable=g-wrong-blank-lines
    code, frame = _get_caller(4)
    sinfo = None
    if stack_info:
      sinfo = '\n'.join(_traceback.format_stack())
    if code:
      return (code.co_filename, frame.f_lineno, code.co_name, sinfo)
    else:
      return '(unknown file)', 0, '(unknown function)', sinfo
else:

  def _logger_find_caller():  # pylint: disable=g-wrong-blank-lines
    code, frame = _get_caller(4)
    if code:
      return (code.co_filename, frame.f_lineno, code.co_name)
    else:
      return '(unknown file)', 0, '(unknown function)'

def _log_prefix(level, timestamp=None, file_and_line=None):
  """Generate a nndct logline prefix."""
  # pylint: disable=global-variable-not-assigned
  global _level_names
  # pylint: enable=global-variable-not-assigned

  # Record current time
  now = timestamp or _time.time()
  now_tuple = _time.localtime(now)
  now_microsecond = int(1e6 * (now % 1.0))

  (filename, line) = file_and_line or _get_file_and_line()
  basename = _os.path.basename(filename)

  # Severity string
  severity = 'I'
  if level in _level_names:
    severity = _level_names[level][0]

  # TODO(yuwang): Format by environment variable.
  s = '%c%02d%02d %02d:%02d:%02d.%06d %s:%d]' % (
      severity,
      now_tuple[1],  # month
      now_tuple[2],  # day
      now_tuple[3],  # hour
      now_tuple[4],  # min
      now_tuple[5],  # sec
      now_microsecond,
      basename,
      line)

  return s

def get_logger():
  """Return logger instance."""
  global _logger

  # Use double-checked locking to avoid taking lock unnecessarily.
  if _logger:
    return _logger

  _logger_lock.acquire()

  try:
    if _logger:
      return _logger

    # Scope the TensorFlow logger to not conflict with users' loggers.
    logger = _logging.getLogger('nndct')
    logger.setLevel(1)

    # Override findCaller on the logger to skip internal helper functions
    logger.findCaller = _logger_find_caller

    # Don't further configure the TensorFlow logger if the root logger is
    # already configured. This prevents double logging in those cases.
    if not _logging.getLogger().handlers:
      # Determine whether we are in an interactive environment
      _interactive = False
      try:
        # This is only defined in interactive shells.
        if _sys.ps1:
          _interactive = True
      except AttributeError:
        # Even now, we may be in an interactive shell with `python -i`.
        _interactive = _sys.flags.interactive

      # If we are in an interactive environment (like Jupyter), set loglevel
      # to INFO and pipe the output to stdout.
      if _interactive:
        #logger.setLevel(INFO)
        _logging_target = _sys.stdout
      else:
        _logging_target = _sys.stderr

      # Add the output handler.
      _handler = _logging.StreamHandler(_logging_target)
      _handler.setFormatter(_logging.Formatter(_logging_fmt, None))
      logger.addHandler(_handler)

    _logger = logger
    return _logger

  finally:
    _logger_lock.release()

def log(level, msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(level)}
  get_logger().log(level, msg, *args, extra=extra, **kwargs)

def debug(msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(DEBUG)}
  get_logger().debug(msg, extra=extra, *args, **kwargs)

def info(msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(INFO)}
  get_logger().info(msg, *args, extra=extra, **kwargs)

def warn(msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(WARN)}
  get_logger().warning(msg, *args, extra=extra, **kwargs)

def error(msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(ERROR)}
  get_logger().error(msg, *args, extra=extra, **kwargs)

def fatal(msg, *args, **kwargs):
  extra = {'nndct_prefix': _log_prefix(FATAL)}
  get_logger().fatal(msg, *args, extra=extra, **kwargs)

def _get_file_and_line():
  """Returns (filename, linenumber) for the stack frame."""
  code, f = _get_caller()
  if not code:
    return ('<unknown>', 0)
  return (code.co_filename, f.f_lineno)

def get_verbosity():
  """Return how much logging output will be produced."""
  return get_logger().getEffectiveLevel()

def set_verbosity(v):
  """Sets the threshold for what messages will be logged."""
  get_logger().setLevel(v)

_min_vlog_level = None

def min_vlog_level():
  global _min_vlog_level

  if _min_vlog_level is None:
    try:
      _min_vlog_level = int(_os.getenv('VAI_MIN_VLOG_LEVEL', 0))
    except ValueError:
      _min_vlog_level = 0

  return _min_vlog_level

def vlog(level, msg, *args, **kwargs):
  if level <= min_vlog_level():
    log(level, msg, *args, **kwargs)
