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

import honey, re

# {{ ... }} expression to eval
# {% ... %} multiline code to exec
# {# ... #} comment

_pattern = re.compile(r'(\{\{)|(\}\})|(\{%)|(%\})|(\{#)|(#\})')
_tag = {
  # start      end          count
  'comment': ('endcomment', 1),
  'if':      ('endif',      1),
  'elif':    ('endif',      0),
  'else':    ('endif',      0),
  'for':     ('endfor',     1),
  'assign':  (None,         0)
}
_endtag = {
  # end         count
  'endcomment': -1,
  'endif':      -1,
  'endfor':     -1  
}

# block memo
#
# ('{{', 'value', string or None)
# ('{%', 'tag', string or None)
# (None, string, None)

class Dict(dict):
  def __init__(self, d):
    super(Dict, self).__init__()
    for k in d:
      if isinstance(d[k], dict):
        self[k] = Dict(d[k])
      elif isinstance(d[k], list):
        self[k] = [ Dict(e) if isinstance(e, dict) else e for e in d[k] ]
      else:
        self[k] = d[k]
  def __getattr__(self, k):
    if k in self and isinstance(self[k], list):
      return [ Dict(e) if isinstance(e, dict) else e for e in self[k] ]
    else:
      return self[k]
  def __setattr__(self, k, v):
    raise
    #self[k] = v

def translate(block, config):
  if block[0][0] == '{{':
    assert len(block) == 1
    statement = block[0][1].strip()
    try:
      return str(eval(statement, Dict(config.copy())))
    except:
      return '{{ ' + block[0][1] + ' }}'
  elif block[0][0] == '{%':
    if block[0][1] == 'comment':
      return ''
    elif block[0][1] == 'if' or block[0][1] == 'elif':
      try:
        condition2 = [ b[0] == '{%' and (b[1] == 'elif' or b[1] == 'else') for b in block[1:-1] ].index(True) + 1
      except ValueError:
        condition2 = None

      condition = block[0][2]
      if condition2 is None:
        statements = block[1:-1]
      else:
        statements = block[1:condition2]

      if eval(condition, Dict(config.copy())):
        return substitute(statements, config)
      else:
        if condition2 is None:
          return ''
        else:
          statements = block[condition2:]
          
          # replace elif and else
          assert statements[0][0] == '{%'
          if statements[0][1] == 'elif':
            statements[0] = ('{%', 'if', statements[0][2])
          elif statements[0][1] == 'else':
            statements[0] = ('{%', 'if', 'True')
            
          return substitute(statements, config)
    elif block[0][1] == 'else':
      statements = block[1:-1]
      return substitute(statements, config)
    elif block[0][1] == 'for':
      condition = re.split('\s+', block[0][2].strip(), 2)
      assert len(condition) == 3 and condition[1] == 'in'
      statements = block[1:-1]

      ret = ''
      for i in eval(condition[2], Dict(config.copy())):
        config[condition[0]] = i
        ret += substitute(statements, config)
      return ret
    elif block[0][1] == 'assign':
      condition = re.split('\s+', block[0][2].strip(), 2)
      assert len(condition) == 3 and condition[1] == '='
      config[condition[0]] = eval(condition[2], Dict(config.copy()))
      return ''
    else:
      raise #NOTIMPL
  elif block[0][0] == '{#':
    return ''
  else:
    return ''.join([b[1] for b in block])

def get_first_block(content):
  if content[0][0] == '{{':
    block = [content[0]]
    return block
  elif content[0][0] == '{%':
    block = []
    endtag = _tag.get(content[0][1], (None, 0))[0]
    if not endtag:
      block = [content[0]]
      return block

    count = 0
    while content:
      b = content[0]
      content = content[1:]
      block.append(b)

      # for nest
      if b[0] == '{%':
        if b[1] in _endtag:
          count += _endtag.get(b[1])
        else:
          count += _tag.get(b[1], (None, 0))[1]
        assert count >= 0

      if b[0] == '{%' and b[1] == endtag and count == 0:
        break

    assert count == 0
    return block
  elif content[0][0] == '{#':
    block = [content[0]]
    return block
  else:
    block = [content[0]]
    return block

def substitute(block, config):
  ret = ''
  while block:
    b = get_first_block(block)
    block = block[len(b):]
    #try:
    ret += translate(b, config)
    #except:
    #  print('Syntax Error')
  return ret
  
def parse(content):
  content = list(filter(lambda s: bool(s), _pattern.split(content)))
  ret = []
  #try:
  while content:
    t = content[0]

    if t == '{{':
      endpos = content.index('}}')
      block = ''.join(content[1:endpos])
      ret.append(('{{', block, None))
      content = content[endpos+1:]
    elif t == '{%':
      endpos = content.index('%}')
      block = ''.join(content[1:endpos])
      sblock = re.split('\s+', block.strip(), 1) + [None]
      ret.append(('{%', sblock[0], sblock[1]))
      content = content[endpos+1:]
    elif t == '{#':
      endpos = content.index('#}')
      block = ''.join(content[1:endpos])
      ret.append(('{#', block, None))
      content = content[endpos+1:]
    else:
      ret.append((None, t, None))
      content = content[1:]
  #except:
  #  sys.stderr.write('parse error\n')

  return ret

@honey.template_filter('simple')
def simple_template(template, **config):
  return substitute(parse(template), config)
