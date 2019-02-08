#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 libpy
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, sys, re, shutil, argparse
from datetime import datetime

NAME = 'honey.py'
VERSION = '1.0.0'

__all__ = [ 'template_filter', 'render_filter', 'preprocessor', 'postprocessor' ]

_quiet = False
_config = {
  'destination': '_site',
  '_layouts': '_layouts',
  '_plugins': '_plugins',
  '_posts': '_posts',
  '_config.py': '_config.py',
  'template': 'simple',
  'exclude': [ r'^[_\.]', r'~$', r'\.swp$', r'honey\.py', r'LICENSE', r'README\.md' ]
}
_site = {
  'layouts': {},
  'pages': [],
  'posts': [],
  'static': [],
  # from _config.py
  'config': {
    'generator': '{} {}'.format(NAME, VERSION),
    'generator_link': '<a href="https://github.com/libpy/honey.py">{}</a>'.format(NAME)
  }
}

_template_filters = {}
_render_filters = {}
_preprocessors = []
_postprocessors = []

def template_filter(name):
  '''Register template filter'''
  def wrapper(f):
    _template_filters[name] = f
    return f
  return wrapper

def render_filter(types):
  '''Register render-filter'''
  def wrapper(f):
    for t in types: _render_filters[t] = f
    return f
  return wrapper

def preprocessor(f):
  '''Register pre-processor'''
  _preprocessors.append(f)
  return f

def postprocessor(f):
  '''Register post-processor'''
  _postprocessors.append(f)
  return f

def log(s):
  if not _quiet: print(s)

def scandir(path = './', recursive = True, ignore = True):
  exclude = _config.get('exclude')
  for e in os.scandir(path):
    if e.is_dir():
      if not ignore or not any([ re.match(p, e.name) for p in exclude ]):
        if recursive:
          yield from scandir(e.path)
        else:
          yield e
    else:
      if not ignore or not any([ re.match(p, e.name) for p in exclude ]):
        yield e
                                    
def run_postprocessor():
  for f in _postprocessors:
    log('post-processor: {} ...'.format(f.__name__))
    f(_site['pages'], _site['posts'], _site['config'])

def run_preprocessor():
  for f in _preprocessors:
    log('pre-processor: {} ...'.format(f.__name__))
    f(_site['pages'], _site['posts'], _site['config'])

def clean_site():
  destination = _config.get('destination')

  # remove old files
  if os.path.isdir(destination):
    assert destination == '_site'
    assert os.path.isfile(os.path.join(os.path.dirname(destination), os.path.basename(sys.argv[0])))  
    for e in scandir(destination, recursive = False, ignore = False):
      if e.is_dir(): shutil.rmtree(e.path)
      elif e.is_file(): os.remove(e.path)
  
def write_file(filepath, content, mode='w'):
  dirname = os.path.dirname(filepath)
  if not os.path.exists(dirname): os.makedirs(dirname)
  open(filepath, mode).write(content)

def write_files():
  destination = _config.get('destination')

  for post in _site['posts']:
    filepath = os.path.join(destination, post['filename'] + post['extension'])
    write_file(filepath, post['content'])

  for page in _site['pages']:
    filepath = os.path.join(destination, page['filename'] + page['extension'])
    write_file(filepath, page['content'])

  for static in _site['static']:
    filepath = os.path.join(destination, static['filename'] + static['extension'])
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname): os.makedirs(dirname)
    open(filepath, 'wb').write(static['content'])

def format_content(content, front_matter):
  template_filter = _template_filters.get(_config['template'])
  assert template_filter

  if isinstance(front_matter, dict):
    while True:
      if 'layout' in front_matter:
        layout = _site['layouts'][front_matter['layout']]
        content = template_filter(layout['content'], content = content, site = _site, **front_matter)
        if 'layout' in layout['front_matter']:
          front_matter['layout'] = layout['front_matter']['layout']
        else:
          del front_matter['layout']
      else:
        content = template_filter(content, site = _site, **front_matter)
        break
  else:
    pass

  return content
  
def format_contents():
  for post in _site['posts']:
    post['content'] = format_content(post['content'], post['front_matter'])
  
  for page in _site['pages']:
    page['content'] = format_content(page['content'], page['front_matter'])

def format_page(content, front_matter):
  template_filter = _template_filters.get(_config['template'])
  assert template_filter

  return {
    'content': template_filter(content, site = _site, **front_matter),
    **front_matter
  }
  
def render_page(content, front_matter):
  extension = front_matter.get('extension')
  if extension in _render_filters:
    content = _render_filters[extension](content, front_matter)

  front_matter['url'] = front_matter['filename'] + front_matter['extension']
  
  return {
    'content': content,
    'front_matter': front_matter
  }

def render_pages():
  for i, post in enumerate(_site['posts']):
    _site['posts'][i].update(render_page(post['content'], post['front_matter']))
    
  for i, page in enumerate(_site['pages']):
    _site['pages'][i].update(render_page(page['content'], page['front_matter']))
  
  # for previous/next
  _site['posts'].sort(key = lambda p: p['front_matter']['date'], reverse = True)
  for i, post in enumerate(_site['posts']):
    if i > 0:
      front_matter = _site['posts'][i - 1]['front_matter']
      _site['posts'][i]['front_matter']['previous'] = {
        'url': front_matter['url'],
        'title': front_matter['title']
      }
    if i + 1 < len(_site['posts']):
      front_matter = _site['posts'][i + 1]['front_matter']
      _site['posts'][i]['front_matter']['next'] = {
        'url': front_matter['url'],
        'title': front_matter['title']
      }

  for i, post in enumerate(_site['posts']):
    _site['posts'][i].update(format_page(post['content'], post['front_matter']))

  for i, page in enumerate(_site['pages']):
    _site['pages'][i].update(format_page(page['content'], page['front_matter']))

def read_front_matter(fd):
  try:
    line = fd.readline()
    if line[:3] != '---': raise

    lines = []
    while True:
      line = fd.readline()
      if line[:3] == '---': break
      elif line == '': raise
      lines.append(line)
  except:
    fd.seek(0, 0)
    return None

  ret = eval(''.join(lines)) if lines else {}
  assert isinstance(ret, dict)
  return ret
  
def read_files():
  posts = _config.get('_posts')
  if os.path.isdir(posts):
    for e in scandir(posts):
      if e.is_file():
        filename, extension = os.path.splitext(e.name)
        year, month, day, title = re.search('([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})-(.*)', filename).groups()
        with open(e.path, 'r') as fd:
          front_matter = read_front_matter(fd)
          front_matter.update({
            'filename': '{}/{}/{}/{}'.format(year, month, day, title),
            'extension': extension,
            'date': datetime(int(year), int(month), int(day)),
            'title': front_matter.get('title', title)
          })
          _site['posts'].append({
            'front_matter': front_matter,
            'content': fd.read()
          })

  for e in scandir():
    if e.is_file():
      filename, extension = os.path.splitext(e.path)
      try:
        with open(e.path, 'r') as fd:
          front_matter = read_front_matter(fd)
          front_matter.update({
            'filename': filename,
            'extension': extension
          })
          _site['pages'].append({
            'front_matter': front_matter,
            'content': fd.read()
          })
      except:
        with open(e.path, 'rb') as fd:
          _site['static'].append({
            'filename': filename,
            'extension': extension,
            'content': fd.read()
          })

def load_layouts():
  layouts = _config.get('_layouts')
  for e in scandir(layouts):
    if e.is_file():
      log('load {}'.format(e.name))
      filename, extension = os.path.splitext(e.name)
      assert extension == '.html'
      
      with open(e.path, 'r') as fd:
        front_matter = read_front_matter(fd)
        content = fd.read()
        _site['layouts'][filename] = {
          'front_matter': front_matter,
          'content': content
        }

def load_plugins():
  plugins = _config.get('_plugins')
  for e in scandir(plugins):
    if e.is_file() and e.name.endswith('.py'):
      with open(e.path, 'r') as fd:
        log('load {}'.format(e.name))
        exec(compile(fd.read(), e.path, 'exec'), globals())

def load_config():
  config = _config.get('_config.py')
  _site['config'].update(eval(open(config, 'r').read()))
  _site['config'].update({
    'date': datetime.now()
  })
        
def build_site():
  load_config()
  load_plugins()
  load_layouts()
  read_files()
  run_preprocessor()
  render_pages()
  format_contents()
  run_postprocessor()
  clean_site()
  write_files()
  log('Site generated successfully')

def main():
  sys.modules[os.path.splitext(NAME)[0]] = sys.modules[__name__]

  command_help = '''build = Build your site.
clean = Clean _site.
help = Display help message.
version = Displays the version number.'''
  parser = argparse.ArgumentParser(prog=NAME, add_help=False)
  parser.add_argument('command', nargs='?', choices=('build','clean','help','version'), default='help', help=command_help)
  parser.add_argument('-q', '--quiet', action='store_true', help='Run without output.')

  args = parser.parse_args()

  global _quiet
  if args.quiet: _quiet = True

  if args.command == 'build':
    build_site()
  elif args.command == 'clean':
    clean_site()
  elif args.command == 'version':
    log('{} {}'.format(NAME, VERSION))
  else:
    log(parser.format_help())
  
if __name__ == '__main__':
  main()
