import mkdocs, importlib, pathlib
from .mkapi import make_api_doc

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

    def on_pre_build(self, config):
        print(config)
        print(self.__dict__)
        root_path = pathlib.Path(config['docs_dir'])
        for module_name, target, source_location in self.config['modules']:
            make_api_doc(module_name, root_path / target, source_location)
