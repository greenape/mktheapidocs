import mkdocs, importlib, pathlib, os, functools
from .mkapi import make_api_doc, get_all_modules_from_files, get_submodule_files, doc_module
from itertools import chain

class PyDocFile(mkdocs.structure.files.File):
    def __init__(self, path, src_dir, dest_dir, use_directory_urls, parent):
        self.parent = parent
        super().__init__(path, src_dir, dest_dir, use_directory_urls)

    def _get_dest_path(self, use_directory_urls):
        """ Return destination path based on source path. """
        if self.is_documentation_page():
            if use_directory_urls:
                parent, filename = os.path.split(self.src_path)
                if self.name == 'index':
                    # index.md or README.md => index.html
                    return os.path.join(self.parent, parent, 'index.html')
                else:
                    # foo.md => foo/index.html
                    return os.path.join(self.parent, parent, self.name, 'index.html')
            else:
                # foo.md => foo.html
                root, ext = os.path.splitext(self.src_path)
                return os.path.join(self.parent, root + '.html')
        return os.path.join(self.parent, self.src_path)

    def is_documentation_page(self):
        return True

    def _get_stem(self):
        """ Return the name of the file without it's extension. """
        filename = os.path.basename(self.src_path)
        stem, ext = os.path.splitext(filename)
        return 'index' if stem in ('index', 'README', '__init__') else stem



class Module(mkdocs.config.config_options.OptionallyRequired):
    """ Validate modules specified are installed. """

    def run_validation(self, value):
        try:
            for mod in value:
                module, target, path = mod
                importlib.import_module(module)
        except ValueError:
            raise mkdocs.config.config_options.ValidationError('Missing part of config.')
        except ModuleNotFoundError:
            raise mkdocs.config.config_options.ValidationError(f'{module} not found. Have you installed it?')
        return value

class Plugin(mkdocs.plugins.BasePlugin):
    config_scheme = (
        ('modules', Module()),
    )

    def on_config(self, config):
        print(config)
        self.files = {}
        for module_name, target, source_location in self.config['modules']:
            module = importlib.import_module(module_name)
            src_path = pathlib.Path(module.__file__).parent.parent.absolute()
            target_path = pathlib.Path(config['site_dir'])
            for module, file in get_submodule_files(module):
                do_doc = functools.partial(doc_module, module.__name__, module, "", source_location, file.stem != "__init__.py")
                f = PyDocFile(file, src_path, target_path, True, target)
                #print(f.__dict__)
                #print()
                self.files[f.url] = (f, do_doc)


    def on_files(self, files, config):
        for f, func in self.files.values():
            files.append(f)
        return files

    def on_nav(self, nav, config, files):
        print(nav.__dict__)
        return nav


    def on_page_read_source(self, eh, page, config):
        try:
            f, sf = self.files[page.url]
            print(page.__dict__)
            print()
            return sf()[1]
        except KeyError:
            try:
                with open(page.file.abs_src_path) as fin:
                    return fin.read()
            except Exception as e:
                print(page.file.__dict__)
                print(e)
                return ""

    #def on_pre_build(self, config):
    #    root_path = pathlib.Path(config['docs_dir'])
    #    self.files = list(chain(*[make_api_doc(module_name, root_path / target, source_location) for module_name, target, source_location in self.config['modules']]))

    #def on_serve(self, server, config):
    #    print(server.__dict__)
    #    print(config)
    #    for file, func in self.files:
    #        server.watch(str(file.absolute()), func)
