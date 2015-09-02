#!/usr/bin/env python

import os
import platform
import sys
import contextlib
import zipfile

def unzip(filename, path='.'):
  with contextlib.closing(zipfile.ZipFile(filename, 'r')) as zip_file:
    zip_file.extractall(path=path)

try:
  import multiprocessing.synchronize
  gyp_parallel_support = True
except ImportError:
  gyp_parallel_support = False


CC = os.environ.get('CC', 'cc')
script_dir = os.path.dirname(__file__)
tv_root = os.path.normpath(script_dir)
output_dir = os.path.join(os.path.abspath(tv_root), 'out')

sys.path.insert(0, os.path.join(tv_root, 'deps', 'gyp', 'pylib'))
try:
  import gyp
except ImportError:
  print('not found: deps/gyp')
  sys.exit(42)


def host_arch():
  machine = platform.machine()
  if machine == 'i386': return 'ia32'
  if machine == 'x86_64': return 'x64'
  if machine.startswith('arm'): return 'arm'
  if machine.startswith('mips'): return 'mips'
  return machine  # Return as-is and hope for the best.


def run_gyp(args):
  rc = gyp.main(args)
  if rc != 0:
    print 'Error running GYP'
    sys.exit(rc)


if __name__ == '__main__':
  args = sys.argv[1:]

  # GYP bug.
  # On msvs it will crash if it gets an absolute path.
  # On Mac/make it will crash if it doesn't get an absolute path.
  if sys.platform == 'win32':
    target_fn = os.path.join(tv_root, 'tv.gyp')
    test_fn = os.path.join(tv_root, 'test.gyp')
    common_fn  = os.path.join(tv_root, 'common.gypi')
    options_fn = os.path.join(tv_root, 'options.gypi')
    # we force vs 2010 over 2008 which would otherwise be the default for gyp
    if not os.environ.get('GYP_MSVS_VERSION'):
      os.environ['GYP_MSVS_VERSION'] = '2010'
  else:
    target_fn = os.path.join(os.path.abspath(tv_root), 'tv.gyp')
    test_fn = os.path.join(os.path.abspath(tv_root), 'test.gyp')
    common_fn  = os.path.join(os.path.abspath(tv_root), 'common.gypi')
    options_fn = os.path.join(os.path.abspath(tv_root), 'options.gypi')

  if not any(a.startswith('-Dwith_test') for a in args):
    args.append(target_fn)
  else:
    # Unzip gmock
    unzip(os.path.join(tv_root, 'deps', 'gmock-1.7.0.zip'), os.path.join(tv_root, 'deps'))
    args.append(test_fn)

  if os.path.exists(common_fn):
    args.extend(['-I', common_fn])

  if os.path.exists(options_fn):
    args.extend(['-I', options_fn])

  args.append('--depth=' + tv_root)

  # There's a bug with windows which doesn't allow this feature.
  if sys.platform != 'win32':
    if '-f' not in args:
      args.extend('-f make'.split())
    if 'eclipse' not in args and 'ninja' not in args:
      args.extend(['-Goutput_dir=' + output_dir])
      args.extend(['--generator-output', output_dir])

  if not any(a.startswith('-Dhost_arch=') for a in args):
    args.append('-Dhost_arch=%s' % host_arch())

  if not any(a.startswith('-Dtarget_arch=') for a in args):
    args.append('-Dtarget_arch=x64')

  if not any(a.startswith('-Denable_shared') for a in args):
    args.append('-Denable_shared=false')
    args.append('-Dtv_library=static_library')
    args.append('-Duv_library=static_library')
  else:
    args.append('-Denable_shared=true')
    args.append('-Dtv_library=shared_library')
    args.append('-Duv_library=shared_library')

  if not any(a.startswith('-Druntime_library=') for a in args):
    args.append('-Druntime_library=default')

  if not any(a.startswith('-Dwith_ssl=') for a in args):
    args.append('-Dwith_ssl=false')

  # Some platforms (OpenBSD for example) don't have multiprocessing.synchronize
  # so gyp must be run with --no-parallel
  if not gyp_parallel_support:
    args.append('--no-parallel')

  gyp_args = list(args)
  print gyp_args
  run_gyp(gyp_args)
