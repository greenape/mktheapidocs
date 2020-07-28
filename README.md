# mktheapidocs

A plugin for [MkDocs](http://mkdocs.org) to generate API documentation from [numpydoc](http://numpydoc.readthedocs.org) style docstrings, and type annotations.

## Installation

`pip install mktheapidocs[plugin]`

## Usage

Add to the plugins section of your mkdocs.yml file, and list the modules you want to document.

```yaml
plugins:
  - mktheapidocs:
      modules: 
        <module_name>:
          section: <docs_section> 
          source_repo: <URL_of_source>
          hidden: ["submodules", "to", "omit"]
```

The plugin will find, and document all submodules, classes, attributes, functions etc. and, if you're using `mkdocs serve`, changes to the documentation will be reflected live.

If you want to manually configure your nav, then you can specify where the api documentation section will be using an `api-docs-<docs_section>` placeholder.