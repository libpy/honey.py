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

import honey

tags_info = {
  'filename': 'tags/{tag}',
  'extension': '.html',
  'layout': 'tags',
  'title': '{tag}'
}

@honey.preprocessor
def preprocessor_tags(pages, posts, config):
  tags_info.update(config.get('plugin_tags', {}))

  tags = config.get('tags', {})
  for page in pages + posts:
    assert 'front_matter' in page
    for tag in page['front_matter'].get('tags', []):
      if not tag in tags: tags[tag] = []
      tags[tag].append(page)

  for tag, tagged in tags.items():
    filename = tags_info['filename'].format(tag = tag)
    extension = tags_info['extension'].format(tag = tag)
    pages.append({
      'front_matter' : {
        'filename': filename,
        'extension': extension,
        'layout': tags_info['layout'].format(tag = tag),
        'title': tags_info['title'].format(tag = tag),
        'posts': tags[tag],
        'date': config.get('date')
      },
      'content': ''
    })

  config['tags'] = tags
