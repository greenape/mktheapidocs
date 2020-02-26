import functools
import importlib
import mkdocs
import os
import pathlib

from mkdocs.utils import nest_paths

from .mkapi import get_submodule_files, doc_module


class PyDocFile(mkdocs.structure.files.File):
    def __init__(self, path, src_dir, dest_dir, use_directory_urls, parent):
        self.parent = parent
        super().__init__(path, src_dir, dest_dir, use_directory_urls)
        self.abs_src_path = self.parent

    def is_documentation_page(self):
        return True

    def _get_stem(self):
        """ Return the name of the file without it's extension. """
        filename = os.path.basename(self.src_path)
        stem, ext = os.path.splitext(filename)
        return "index" if stem in ("index", "README", "__init__") else stem


class Module(mkdocs.config.config_options.OptionallyRequired):
    """ Validate modules specified are installed. """

    def run_validation(self, value):
        try:
            for module, details in value.items():
                importlib.import_module(module)
                if "section" not in details:
                    raise mkdocs.config.config_options.ValidationError(
                        f"Missing section for {module}"
                    )
                if "source_repo" not in details:
                    raise mkdocs.config.config_options.ValidationError(
                        f"Missing source_repo for {module}"
                    )
        except ModuleNotFoundError:
            raise mkdocs.config.config_options.ValidationError(
                f"{module} not found. Have you installed it?"
            )
        return value


def find_section_anchor(nav, anchor):
    try:
        in_this_level = nav.index(anchor)
        return in_this_level, nav
    except ValueError:
        dicts = [l for l in nav if isinstance(l, dict)]
        for d in dicts:
            d_val = list(d.items())[0][1]
            try:
                in_this_level, nav = find_section_anchor(d_val, anchor)
                return in_this_level, nav
            except ValueError:
                pass
    raise ValueError


class Plugin(mkdocs.plugins.BasePlugin):
    config_scheme = (("modules", Module()),)

    def on_config(self, config):
        # print(config)
        self.files = {}
        self.module_files = {}
        for module_name, details in self.config["modules"].items():
            target = details["section"]
            self.module_files[target] = []
            source_location = details["source_repo"]
            source_location = os.path.expandvars(source_location)
            module = importlib.import_module(module_name)
            importlib.reload(module)
            src_path = pathlib.Path(module.__file__).parent.parent.absolute()
            target_path = pathlib.Path(config["site_dir"])
            for module, file in get_submodule_files(module):
                importlib.reload(module)
                do_doc = functools.partial(
                    doc_module,
                    module.__name__,
                    module,
                    "",
                    source_location,
                    file.stem != "__init__.py",
                )
                f = PyDocFile(
                    target / file,
                    src_path,
                    target_path,
                    True,
                    pathlib.Path(module.__file__).absolute(),
                )
                # print(f.__dict__)
                # print()
                self.files[f.url] = (f, do_doc)
                self.module_files[target].append(f)
            if config["nav"]:
                try:
                    ix, nav = find_section_anchor(config["nav"], f"api-docs-{target}")
                    nav[ix] = nest_paths(f.src_path for f in self.module_files[target])[
                        0
                    ]
                except ValueError:
                    pass

    def on_files(self, files, **kwargs):
        for f, func in self.files.values():
            files.append(f)
        return files

    def on_nav(self, nav, **kwargs):
        return nav

    def on_page_read_source(self, page, **kwargs):
        try:
            f, sf = self.files[page.url]
            # print(page.__dict__)
            # print()
            return sf()[1]
        except KeyError:
            return None

    # def on_pre_build(self, config):
    #    root_path = pathlib.Path(config['docs_dir'])
    #    self.files = list(chain(*[make_api_doc(module_name, root_path / target, source_location) for module_name, target, source_location in self.config['modules']]))

    def on_serve(self, server, config, **kwargs):
        # print(server.__dict__)
        # print(config)
        builder = server.watcher._tasks[config["docs_dir"]]["func"]
        for file, func in self.files.values():
            server.watch(str(file.abs_src_path), builder)
