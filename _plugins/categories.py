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

categories_info = {
  'filename': 'categories/{category}',
  'extension': '.html',
  'layout': 'categories',
  'title': '{category}'
}

@honey.preprocessor
def preprocessor_categories(pages, posts, config):
  categories_info.update(config.get('plugin_categories', {}))
  
  categories = config.get('categories', {})
  for page in pages + posts:
    assert 'front_matter' in page
    category = page['front_matter'].get('category')
    if category:
      if not category in categories: categories[category] = []
      categories[category].append(page)
      
  for category, categorized in categories.items():
    filename = categories_info['filename'].format(category = category)
    extension = categories_info['extension'].format(category = category)
    pages.append({
      'front_matter' : {
        'filename': filename,
        'extension': extension,
        'layout': categories_info['layout'].format(category = category),
        'title': categories_info['title'].format(category = category),
        'posts': categories[category],
        'date': config.get('date')
      },
      'content': ''
    })

  config['categories'] = categories
    
