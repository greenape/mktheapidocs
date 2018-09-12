import inspect, os, pathlib, importlib, black, re, click
from numpydoc.docscrape import NumpyDocString, FunctionDoc, ClassDoc


def get_line(thing):
    try:
        return inspect.getsourcelines(thing)[1]
    except TypeError:
        # Might be a property
        return inspect.getsourcelines(thing.fget)[1]

def get_all_modules_from_files(module, hide=["__init__", "_version"]):
    modules = set()
    module_file = pathlib.Path(module.__file__).parent.parent
    dir_was = pathlib.Path().absolute()
    os.chdir(module_file)
    for root, dirs, files in os.walk(module.__name__):
        module_path = pathlib.Path(root)
        if not module_path.parts[-1].startswith("_"):
            module = importlib.import_module(".".join(module_path.parts))
            if not module.__name__.startswith("_"):
                modules.add((module.__name__, module, False))
                for file in files:
                    module_name = inspect.getmodulename(file)
                    if module_name is not None and module_name not in hide:
                        submodule = importlib.import_module(".".join((module_path / inspect.getmodulename(file)).parts))
                        if not module.__name__.startswith("_") and not submodule.__name__.startswith("_"):
                            modules.add((submodule.__name__, submodule, True))
    os.chdir(dir_was)
    return modules

def get_classes(module):
    return set([x for x in inspect.getmembers(module, inspect.isclass) if (not x[0].startswith("_")) and x[1].__module__ == module.__name__])

def get_funcs(module):
    return set([x for x in inspect.getmembers(module, inspect.isfunction) if (not x[0].startswith("_")) and x[1].__module__ == module.__name__])

def get_available_funcs(module):
    shared_root = module.__name__.split(".")[0]
    return set([x for x in inspect.getmembers(module, inspect.isfunction) if (not x[0].startswith("_")) and x[1].__module__.split(".")[0] == shared_root])

def get_available_classes(module):
    shared_root = module.__name__.split(".")[0]
    return set([x for x in inspect.getmembers(module, inspect.isclass) if (not x[0].startswith("_")) and x[1].__module__.split(".")[0] == shared_root])

def fix_footnotes(s):
    return re.subn("\[([0-9]+)\]_", r"[^\1]", s)[0]


def mangle_types(types):
    default = re.findall("default .+", types)
    mangled = []
    try:
        if len(default):
            default = re.sub("default (.+)", r"default ``\1``", default[0])
            mangled.append(default)
        types = re.sub("default .+", "", types)
        curlied = re.findall("{.+}", types)
        no_curls = re.subn("{.+},?", "", types)[0]
        ts = [t.strip() for t in no_curls.split(",")]
        ts = [t.split(" or ") for t in ts]
        ts =  [item for sublist in ts for item in sublist if item != ""]
        types = ts + curlied 
        for ix, typ in enumerate(types):
            ts = [f"``{t}``" for t in  typ.split(" of ")]
            mangled.append(" of ".join(ts))
    except Exception as e:
        print(e)
        print(default)
        print(types)
        raise e
    output = reversed(mangled)

    return ", ".join(output)


def mangle_examples(examples):
    was_in_python = False
    in_python = False
    lines = []
    for line in examples:
        if line.startswith(">>>"):
            in_python = True
        if line == "":
            in_python = False
        if not in_python and was_in_python:
            lines.append("\n```\n")
        elif not in_python:
            lines.append(f"{line} ")
        elif in_python and not was_in_python:
            lines.append("\n```python\n")
            lines.append(re.sub(">>> ", "", line) + "\n")
        else:
            lines.append(re.sub(">>> ", "", line) + "\n")
        was_in_python = in_python
    if was_in_python:
        lines.append("\n```")
    lines.append("\n\n")
    return lines

def notes_section(doc):
    lines = []
    if 'Notes' in doc and len(doc['Notes']) > 0:             
        lines.append("!!! note\n")
        lines.append(f"    {' '.join(doc['Notes'])}\n\n")
    return lines

'.. [1] http://barabasi.com/f/618.pdf'
                     
def refs_section(doc):
    lines = []
    if 'References' in doc and len(doc['References']) > 0:
        print("Found refs")
        for ref in doc['References']:
            print(ref)
            ref_num = re.findall("\[([0-9]+)\]", ref)[0] 
            print(ref_num)
            ref_body = " ".join(ref.split(" ")[2:])
            print(f"[^{ref_num}] {ref_body}" + "\n")
            lines.append(f"[^{ref_num}]: {ref_body}" + "\n")
            print(lines)
    return lines

def examples_section(doc, header_level):
    lines = []
    if 'Examples' in doc and len(doc['Examples']) > 0:             
        lines.append(f"{'#'*(header_level+1)} Examples \n")
        egs = '\n'.join(doc['Examples'])
        lines += mangle_examples(doc['Examples'])
    return lines

def returns_section(doc, header_level):
    lines = []
    try:
        if 'Returns' in doc and len(doc['Returns']) > 0:
            lines.append(f"{'#'*(header_level+1)} Returns\n")
            for name, typ, desc in doc['Returns']:
                if ":" in name:
                    name, typ = name.split(":")
                
                if typ != "":
                    line = f"- `{name}`: {mangle_types(typ)}"
                else:
                    line = f"- {mangle_types(name)}"
                line += "\n\n"
                lines.append(line)
                lines.append(f"    {' '.join(desc)}\n\n")
    except Exception as e:
        print(e)
        print(doc)
    return lines

def summary(doc):
    lines = []
    if 'Summary' in doc and len(doc['Summary']) > 0:
        lines.append(fix_footnotes(" ".join(doc['Summary'])))
        lines.append("\n")
    if 'Extended Summary' in doc and len(doc['Extended Summary']) > 0:
        lines.append(fix_footnotes(" ".join(doc['Extended Summary'])))
        lines.append("\n")
    return lines

def params_section(doc, header_level):
    lines = []
    if 'Parameters' in doc and len(doc['Parameters']) > 0:
        lines.append(f"{'#'*(header_level+1)} Parameters\n")
        for names, types, description in doc['Parameters']:
            if types == "":
                try:
                    names, types = names.split(":")
                except:
                    pass
            names = names.split(",")
            lines.append("- ")
            lines.append(", ".join(f"`{name}`" for name in names))
            if types != "":
                lines.append(f": {mangle_types(types)}")
            lines.append("\n\n")
            lines.append(f"    {' '.join(description)}\n\n")
    return lines

def to_doc(name, thing, header_level, source_location):
    if inspect.isclass(thing):
        header = f"{'#'*header_level} Class **{name}**\n\n"
    else:
        header = f"{'#'*header_level} {name}\n\n"
    lines = [header]
    try:
        try:
            func_sig = black.format_str(f"{name}{inspect.signature(thing)}", 80).strip()
        except TypeError:
            func_sig = black.format_str(f"{name}{inspect.signature(thing.fget)}", 80).strip()
        lines.append(f"```python\n{func_sig}\n```\n")
    except Exception as e:
        pass
    try:
        lineno = get_line(thing)
        try:
            thing_file = "/".join(inspect.getmodule(thing).__name__.split(".")) + ".py"
        except TypeError:
            thing_file = "/".join(inspect.getmodule(thing.fget).__name__.split(".")) + ".py"
        lines.append(f"Source: [{thing_file}]({source_location}#L{lineno})" + "\n\n")
    except:
        pass
    try:
        doc = NumpyDocString(thing.__doc__)._parsed_data
        lines += summary(doc)
        lines += params_section(doc, header_level)
        lines += returns_section(doc, header_level)
        lines += examples_section(doc, header_level)  
        lines += notes_section(doc)
        lines += refs_section(doc)
    except Exception as e:
        print(f"No docstring for {thing}: {e}")
    return lines


@click.command()
@click.argument("module_name")
@click.argument("output_dir")
@click.argument("source-location")
def make_api_doc(module_name, output_dir, source_location):
    module = importlib.import_module(module_name)
    output_dir = pathlib.Path(output_dir).absolute()
    for module_name, module, leaf in get_all_modules_from_files(module):
        print(module_name)
        path = pathlib.Path(output_dir).joinpath(*module.__name__.split("."))
        available_classes = get_available_classes(module)
        deffed_classes = get_classes(module)
        deffed_funcs = get_funcs(module)
        alias_funcs = available_classes - deffed_classes
        if leaf:
            doc_path = path.with_suffix(".md")
        else:
            doc_path = path / "index.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        module_path = '/'.join(module.__name__.split('.'))
        module_file_url = f"{source_location}/tree/master/{module_path}.py" if leaf else f"{source_location}/tree/master/{module_path}/__init__.py"
        with open(doc_path.absolute(), "w") as index:
            module_doc = module.__doc__

            # Module overview documentation
            if module_doc is not None:
                index.writelines(to_doc(module.__name__, module, 1, module_file_url))
            else:
                index.write(f"# {module.__name__}\n\n")
            index.write("\n\n")
            for cls_name, cls in sorted(deffed_classes):
                lines = to_doc(cls_name, cls, 2, module_file_url)
                index.writelines(lines)

                properties = inspect.getmembers(cls, lambda o: isinstance(o, property))
                if len(properties):
                    index.write("### Properties\n\n")
                    for prop_name, prop in properties:
                        lines = to_doc(prop_name, prop, 4, module_file_url)
                        index.writelines(lines)

                class_methods = [x for x in inspect.getmembers(cls, inspect.isfunction) if (not x[0].startswith("_"))]
                if len(class_methods) > 0:
                    index.write("### Methods \n\n")
                    for method_name, method in class_methods:
                        lines = to_doc(method_name, method, 4, module_file_url)
                        index.writelines(lines)
            for fname, func in sorted(deffed_funcs):
                lines = to_doc(fname, func, 2, module_file_url)
                index.writelines(lines)


if __name__ == "__main__":
    make_api_doc()