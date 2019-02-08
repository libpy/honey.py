# honey.py

honey.py is a simple static site generator written in Python.

- Support template engine and plugins system
- No external dependencies outside Pythons standard library

## Usage

Build your site.

    $ ./honey.py build

Display help message.

    $ ./honey.py help

## Quick start

### Installation and create a project

Copy following files and directories.

    _config.py
    honey.py
    _layouts
    _plugins

#### Create a post

Create your first article with the following content:

    $ cat _posts/2019-02-01-hello.html
    ---
    {
      'title': 'Hello',
      'layout': 'post',
      'description': 'Hello'
    }
    ---

    <h3>Hello</h3>

#### Generate your site

    $ ./honey.py build

#### Preview your site

Run following commands and browse to http://localhost:8000/

    $ cd _site
    $ python -m http.server

## Source code

You can access the source code at: https://github.com/libpy/honey.py
