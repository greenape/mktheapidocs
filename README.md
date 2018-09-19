# mktheapidocs

A plugin for [MkDocs](http://mkdocs.org) to generate API documentation from [numpydoc](http://numpydoc.readthedocs.org) style docstrings, and type annotations.

## Installation

`pip install mktheapidocs`

## Usage

Add to the plugins section of your mkdocs.yml file, and list the modules you want to document.

```yaml
plugins:
  - mktheapidocs:
      modules: 
        <module_name>:
          section: <docs_section> 
          source_repo: <URL_of_source>
```

The plugin will find, and document all submodules, classes, attributes, functions etc. and, if you're using `mkdocs serve`, changes to the documentation will be reflected live.