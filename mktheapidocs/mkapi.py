import inspect, os, pathlib, importlib, black, re, click, enum
from numpydoc.docscrape import NumpyDocString, FunctionDoc, ClassDoc
from functools import cmp_to_key


def get_line(thing):
    """
    Get the line number for something.
    Parameters
    ----------
    thing : function, class, module

    Returns
    -------
    int
        Line number in the source file
    """
    try:
        return inspect.getsourcelines(thing)[1]
    except TypeError:
        # Might be a property
        return inspect.getsourcelines(thing.fget)[1]
    except Exception as e:
        # print(thing)
        raise e


def _sort_modules(mods):
    """ Always sort `index` or `README` as first filename in list. """

    def compare(x, y):
        x = x[1]
        y = y[1]
        if x == y:
            return 0
        if y.stem == "__init__.py":
            return 1
        if x.stem == "__init__.py" or x < y:
            return -1
        return 1

    return sorted(mods, key=cmp_to_key(compare))


def get_submodule_files(module, hide=["_version"]):
    modules = set()
    module_file = pathlib.Path(module.__file__).parent
    for root, dirs, files in os.walk(module_file):
        module_path = pathlib.Path(root).relative_to(module_file.parent)
        if not module_path.parts[-1].startswith("_"):
            try:
                for file in files:
                    module_name = (
                        "" if "__init__.py" == file else inspect.getmodulename(file)
                    )
                    if module_name is not None and module_name not in hide:
                        submodule = importlib.import_module(
                            ".".join((module_path / module_name).parts)
                        )
                        modules.add((submodule, module_path / file))
            except ModuleNotFoundError:
                print(f"Skipping {'.'.join(module_path.parts)} - not a module.")
    return _sort_modules(modules)


def get_all_modules_from_files(module, hide=["__init__", "_version"]):
    modules = set()
    module_file = pathlib.Path(module.__file__).parent.parent
    dir_was = pathlib.Path().absolute()
    os.chdir(module_file)
    for root, dirs, files in os.walk(module.__name__):
        module_path = pathlib.Path(root)
        if not module_path.parts[-1].startswith("_"):
            try:
                module = importlib.import_module(".".join(module_path.parts))
                if not module.__name__.startswith("_"):
                    modules.add((module.__name__, module, False, module_path))
                    for file in files:
                        module_name = inspect.getmodulename(file)
                        if module_name is not None and module_name not in hide:
                            submodule = importlib.import_module(
                                ".".join(
                                    (module_path / inspect.getmodulename(file)).parts
                                )
                            )
                            if not module.__name__.startswith(
                                "_"
                            ) and not submodule.__name__.startswith("_"):
                                modules.add(
                                    (
                                        submodule.__name__,
                                        submodule,
                                        True,
                                        module_path.absolute() / file,
                                    )
                                )
            except ModuleNotFoundError:
                print(f"Skipping {'.'.join(module_path.parts)} - not a module.")
    os.chdir(dir_was)
    return modules


def get_classes(module):
    return set(
        [
            x
            for x in inspect.getmembers(module, inspect.isclass)
            if (not x[0].startswith("_"))
            and x[1].__module__ == module.__name__
            and not type(x[1]) is enum.EnumMeta
        ]
    )


def get_enums(module):
    return set(
        [
            x
            for x in inspect.getmembers(module, inspect.isclass)
            if (not x[0].startswith("_"))
            and x[1].__module__ == module.__name__
            and type(x[1]) is enum.EnumMeta
        ]
    )


def get_funcs(module):
    return set(
        [
            x
            for x in inspect.getmembers(module, inspect.isfunction)
            if (not x[0].startswith("_")) and x[1].__module__ == module.__name__
        ]
    )


def get_available_funcs(module):
    shared_root = module.__name__.split(".")[0]
    return set(
        [
            x
            for x in inspect.getmembers(module, inspect.isfunction)
            if (not x[0].startswith("_"))
            and x[1].__module__.split(".")[0] == shared_root
        ]
    )


def get_available_classes(module):
    shared_root = module.__name__.split(".")[0]
    return set(
        [
            x
            for x in inspect.getmembers(module, inspect.isclass)
            if (not x[0].startswith("_"))
            and x[1].__module__.split(".")[0] == shared_root
        ]
    )


def deffed_here(thing, holder):
    return inspect.getfile(thing) == inspect.getfile(holder)


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
        annotated = re.findall("[a-zA-Z]+\[.+\]", no_curls)
        no_curls = re.subn("[a-zA-Z]+\[.+\],?", "", no_curls)[0]
        ts = [t.strip() for t in no_curls.split(",")]
        ts = [t.split(" or ") for t in ts]
        ts = [item for sublist in ts for item in sublist if item != ""]
        types = ts + curlied + annotated
        for ix, typ in enumerate(types):
            ts = [f"``{t}``" for t in typ.split(" of ")]
            mangled.append(" of ".join(ts))
    except Exception as e:
        # print(e)
        # print(default)
        # print(types)
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
    if "Notes" in doc and len(doc["Notes"]) > 0:
        lines.append("!!! note\n")
        lines.append(f"    {' '.join(doc['Notes'])}\n\n")
    return lines


def warnings_section(doc):
    lines = []
    if "Warnings" in doc and len(doc["Warnings"]) > 0:
        lines.append("!!! warning\n")
        lines.append(f"    {' '.join(doc['Warnings'])}\n\n")
    return lines


def refs_section(doc):
    """
    Generate a References section.

    Parameters
    ----------
    doc : dict
        Dictionary produced by numpydoc

    Returns
    -------
    list of str
        Markdown for references section
    """
    lines = []
    if "References" in doc and len(doc["References"]) > 0:
        # print("Found refs")
        for ref in doc["References"]:
            # print(ref)
            ref_num = re.findall("\[([0-9]+)\]", ref)[0]
            # print(ref_num)
            ref_body = " ".join(ref.split(" ")[2:])
            # print(f"[^{ref_num}] {ref_body}" + "\n")
            lines.append(f"[^{ref_num}]: {ref_body}" + "\n\n")
            # print(lines)
    return lines


def examples_section(doc, header_level):
    """
    Generate markdown for Examples section.

    Parameters
    ----------
    doc : dict
        Dict from numpydoc
    header_level : int
        Number of `#`s to use for header

    Returns
    -------
    list of str
        Markdown for examples section
    """
    lines = []
    if "Examples" in doc and len(doc["Examples"]) > 0:
        lines.append(f"{'#'*(header_level+1)} Examples \n")
        egs = "\n".join(doc["Examples"])
        lines += mangle_examples(doc["Examples"])
    return lines


def returns_section(thing, doc, header_level):
    """
    Generate markdown for Returns section.

    Parameters
    ----------
    thing : function
        Function to produce returns for
    doc : dict
        Dict from numpydoc
    header_level : int
        Number of `#`s to use for header

    Returns
    -------
    list of str
        Markdown for examples section
    """
    lines = []
    return_type = None
    # print(thing)
    # print(doc)
    try:
        return_type = thing.__annotations__["return"]
    except AttributeError:
        try:
            return_type = thing.fget.__annotations__["return"]
        except:
            pass
    except KeyError:
        pass
    if return_type is None:
        return_type = ""
    else:
        # print(f"{thing} has annotated return type {return_type}")
        try:
            return_type = (
                f"{return_type.__name__}"
                if return_type.__module__ == "builtins"
                else f"{return_type.__module__}.{return_type.__name__}"
            )
        except AttributeError:
            return_type = str(return_type)
        # print(return_type)

    try:
        if "Returns" in doc and len(doc["Returns"]) > 0 or return_type != "":
            # print(doc["Returns"])
            lines.append(f"{'#'*(header_level+1)} Returns\n")
            if return_type != "" and len(doc["Returns"]) == 1:
                name, typ, desc = doc["Returns"][0]
                if typ != "" and name != "":
                    lines.append(f"- `{name}`: ``{return_type}``")
                else:
                    lines.append(f"- ``{return_type}``")
                lines.append("\n\n")
                if desc != "":
                    lines.append(f"    {' '.join(desc)}\n\n")
            elif return_type != "":
                lines.append(f"- ``{return_type}``")
                lines.append("\n\n")
            else:
                for name, typ, desc in doc["Returns"]:
                    if ":" in name:
                        name, typ = name.split(":")

                    if typ != "":
                        if name != "":
                            line = f"- `{name}`: {mangle_types(typ)}"
                        else:
                            line = f"- {mangle_types(typ)}"
                    else:
                        line = f"- {mangle_types(name)}"
                    line += "\n\n"
                    lines.append(line)
                    lines.append(f"    {' '.join(desc)}\n\n")
    except Exception as e:
        # print(e)
        # print(doc)
        pass
    return lines


def summary(doc):
    """
    Generate markdown for summary section.

    Parameters
    ----------
    doc : dict
        Output from numpydoc

    Returns
    -------
    list of str
        Markdown strings
    """
    lines = []
    if "Summary" in doc and len(doc["Summary"]) > 0:
        lines.append(fix_footnotes(" ".join(doc["Summary"])))
        lines.append("\n")
    if "Extended Summary" in doc and len(doc["Extended Summary"]) > 0:
        lines.append(fix_footnotes(" ".join(doc["Extended Summary"])))
        lines.append("\n")
    return lines


def params_section(thing, doc, header_level):
    """
    Generate markdown for Parameters section.

    Parameters
    ----------
    thing : function
        Function to produce parameters from
    doc : dict
        Dict from numpydoc
    header_level : int
        Number of `#`s to use for header

    Returns
    -------
    list of str
        Markdown for examples section
    """
    lines = []

    class_doc = doc["Parameters"]
    return type_list(
        inspect.signature(thing),
        class_doc,
        "#" * (header_level + 1) + " Parameters\n\n",
    )


def escape(string):
    """
    Escape underscores in markdown.

    Parameters
    ----------
    string : str
        String to escape

    Returns
    -------
    str
        The string, with `_`s escaped with backslashes
    """
    return string.replace("_", "\\_")


def get_source_link(thing, source_location):
    """
    Get a link to the line number a module/class/function is defined at.

    Parameters
    ----------
    thing : function or class
        Thing to get the link for
    source_location : str
        GitHub url of the source code

    Returns
    -------
    str
        String with link to the file & line number, or empty string if it
        couldn't be found
    """
    try:
        lineno = get_line(thing)
        try:
            owner_module = inspect.getmodule(thing)
            assert owner_module is not None
        except (TypeError, AssertionError):
            owner_module = inspect.getmodule(thing.fget)

        thing_file = "/".join(owner_module.__name__.split("."))
        if owner_module.__file__.endswith("__init__.py"):
            thing_file += "/__init__.py"
        else:
            thing_file += ".py"
        return (
            f"Source: [{escape(thing_file)}]({source_location}/{thing_file}#L{lineno})"
            + "\n\n"
        )
    except Exception as e:
        # print("Failed to find source file.")
        # print(e)
        # print(lineno)
        # print(thing)
        # print(owner_module)
        # print(thing_file)
        # print(source_location)
        pass
    return ""


def get_signature(name, thing):
    """
    Get the signature for a function or class, formatted nicely if possible.
    
    Parameters
    ----------
    name : str
        Name of the thing, used as the first part of the signature
    thing : class or function
        Thing to get the signature of
    """
    if inspect.ismodule(thing):
        return ""
    if isinstance(thing, property):
        func_sig = name
    else:
        try:
            sig = inspect.signature(thing)
        except TypeError:
            sig = inspect.signature(thing.fget)
        except ValueError:
            return ""
        func_sig = f"{name}{sig}"
        try:
            mode = black.FileMode(line_length=80)
            func_sig = black.format_str(func_sig, mode=mode).strip()
        except (ValueError, TypeError):
            pass
    return f"```python\n{func_sig}\n```\n"


def _get_names(names, types):
    """
    Get names, bearing in mind that there might be no name,
    no type, and that the `:` separator might be wrongly used.
    """
    if types == "":
        try:
            names, types = names.split(":")
        except:
            pass
    return names.split(","), types


def string_annotation(typ, default):
    """
    Construct a string representation of a type annotation.

    Parameters
    ----------
    typ : type
        Type to turn into a string
    default : any
        Default value (if any) of the type

    Returns
    -------
    str
        String version of the type annotation
    """
    try:
        type_string = (
            f"`{typ.__name__}`"
            if typ.__module__ == "builtins"
            else f"`{typ.__module__}.{typ.__name__}`"
        )
    except AttributeError:
        type_string = f"`{str(typ)}`"
    if default is None:
        type_string = f"{type_string}, default ``None``"
    elif default == inspect._empty:
        pass
    else:
        type_string = f"{type_string}, default ``{default}``"
    return type_string


def type_list(signature, doc, header):
    """
    Construct a list of types, preferring type annotations to
    docstrings if they are available.

    Parameters
    ----------
    signature : Signature
        Signature of thing
    doc : list of tuple
        Numpydoc's type list section

    Returns
    -------
    list of str
        Markdown formatted type list
    """

    lines = []
    docced = set()
    lines.append(header)
    try:
        for names, types, description in doc:
            names, types = _get_names(names, types)
            unannotated = []
            for name in names:
                docced.add(name)
                try:
                    typ = signature.parameters[name].annotation
                    if typ == inspect._empty:
                        raise AttributeError
                    default = signature.parameters[name].default
                    type_string = string_annotation(typ, default)
                    lines.append(f"- `{name}`: {type_string}")
                    lines.append("\n\n")
                except (AttributeError, KeyError):
                    unannotated.append(name)  # No annotation

            if len(unannotated) > 0:
                lines.append("- ")
                lines.append(", ".join(f"`{name}`" for name in unannotated))
                if types != "" and len(unannotated) > 0:
                    lines.append(f": {mangle_types(types)}")
            lines.append("\n\n")
            lines.append(f"    {' '.join(description)}\n\n")
        for names, types, description in doc:
            names, types = _get_names(names, types)
            for name in names:
                if name not in docced:
                    try:
                        typ = signature.parameters[name].annotation
                        default = signature.parameters[name].default
                        type_string = string_annotation(typ, default)
                        lines.append(f"- `{name}`: {type_string}")
                        lines.append("\n\n")
                    except (AttributeError, KeyError):
                        lines.append(f"- `{name}`")
                        lines.append("\n\n")
    except Exception as e:
        print(f"Couldn't get type list for {signature}: {e}")
    return lines if len(lines) > 1 else []


def _split_props(thing, doc):
    """
    Separate properties from other kinds of member.
    """
    props = inspect.getmembers(thing, lambda o: isinstance(o, property))
    ps = []
    docs = [
        (*_get_names(names, types), names, types, desc) for names, types, desc in doc
    ]
    for prop_name, prop in props:
        in_doc = [d for d in enumerate(docs) if prop_name in d[0]]
        for d in in_doc:
            docs.remove(d)
        ps.append(prop_name)
    if len(docs) > 0:
        _, _, names, types, descs = zip(*docs)
        return ps, zip(names, types, descs)
    return ps, []


def attributes_section(thing, doc, header_level):
    """
    Generate an attributes section for classes.

    Prefers type annotations, if they are present.

    Parameters
    ----------
    thing : class
        Class to document
    doc : dict
        Numpydoc output
    header_level : int
        Number of `#`s to use for header

    Returns
    -------
    list of str
        Markdown formatted attribute list
    """
    # Get Attributes

    if not inspect.isclass(thing):
        return []

    props, class_doc = _split_props(thing, doc["Attributes"])
    tl = type_list(inspect.signature(thing), class_doc, "\n## Attributes\n\n")
    if len(tl) == 0 and len(props) > 0:
        tl.append("\n## Attributes\n\n")
    for prop in props:
        tl.append(f"- [`{prop}`](#{prop})\n\n")
    return tl


def enum_doc(name, enum, header_level, source_location):
    """
    Generate markdown for an enum

    Parameters
    ----------
    name : str
        Name of the thing being documented
    enum : EnumMeta
        Enum to document
    header_level : int
        Heading level
    source_location : str
        URL of repo containing source code
    """

    lines = [f"{'#'*header_level} Enum **{name}**\n\n"]
    lines.append(f"```python\n{name}\n```\n")
    lines.append(get_source_link(enum, source_location))
    try:
        doc = NumpyDocString(inspect.getdoc(enum))._parsed_data
        lines += summary(doc)
    except:
        pass
    lines.append(f"{'#'*(header_level + 1)} Members\n\n")
    lines += [f"- `{str(v).split('.').pop()}`: `{v.value}` \n\n" for v in enum]
    return lines


def to_doc(name, thing, header_level, source_location):
    """
    Generate markdown for a class or function

    Parameters
    ----------
    name : str
        Name of the thing being documented
    thing : class or function
        Class or function to document
    header_level : int
        Heading level
    source_location : str
        URL of repo containing source code
    """

    if type(thing) is enum.EnumMeta:
        return enum_doc(name, thing, header_level, source_location)
    if inspect.isclass(thing):
        header = f"{'#'*header_level} Class **{name}**\n\n"
    else:
        header = f"{'#'*header_level} {name}\n\n"
    lines = [
        header,
        get_signature(name, thing),
        get_source_link(thing, source_location),
    ]

    try:
        # print(f"{name}: {thing}")
        doc = NumpyDocString(inspect.getdoc(thing))._parsed_data
        lines += summary(doc)
        # print("Got summary")
        lines += attributes_section(thing, doc, header_level)
        # print("Got attribs")
        try:
            lines += params_section(thing, doc, header_level)
        except:
            pass  # No params
        # print("Got params")
        lines += returns_section(thing, doc, header_level)
        # print("Got returns")
        lines += examples_section(doc, header_level)
        lines += notes_section(doc)
        lines += warnings_section(doc)
        lines += refs_section(doc)
    except Exception as e:
        # print(f"No docstring for {name}, src {source_location}: {e}")
        pass
    return lines


def doc_module(module_name, module, output_dir, source_location, leaf):
    """
    Document a module

    Parameters
    ----------
    module_name : str
    module : module
    output_dir : str
    source_location : str
    leaf : bool
    """
    path = pathlib.Path(output_dir).joinpath(*module.__name__.split("."))
    available_classes = get_available_classes(module)
    deffed_classes = get_classes(module)
    deffed_funcs = get_funcs(module)
    deffed_enums = get_enums(module)
    alias_funcs = available_classes - deffed_classes
    if leaf:
        doc_path = path.with_suffix(".md")
    else:
        doc_path = path / "index.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    module_path = "/".join(module.__name__.split("."))
    doc = [f"title: {module_name.split('.')[-1]}" + "\n"]
    module_doc = module.__doc__

    # Module overview documentation
    if module_doc is not None:
        doc += to_doc(module.__name__, module, 1, source_location)
    else:
        doc.append(f"# {module.__name__}\n\n")
    doc.append("\n\n")
    for cls_name, cls in sorted(deffed_enums) + sorted(deffed_classes):
        doc += to_doc(cls_name, cls, 2, source_location)

        class_methods = [
            x
            for x in inspect.getmembers(cls, inspect.isfunction)
            if (not x[0].startswith("_")) and deffed_here(x[1], cls)
        ]
        class_methods += inspect.getmembers(cls, lambda o: isinstance(o, property))
        if len(class_methods) > 0:
            doc.append("## Methods \n\n")
            for method_name, method in class_methods:
                # print(method_name)
                doc += to_doc(method_name, method, 4, source_location)
    for fname, func in sorted(deffed_funcs):
        doc += to_doc(fname, func, 2, source_location)
    return doc_path.absolute(), "".join(doc)


@click.command()
@click.argument("module_name")
@click.argument("output_dir")
@click.argument("source-location")
def cli(module_name, output_dir, source_location):
    make_api_doc(module_name, output_dir, source_location)


def make_api_doc(module_name, output_dir, source_location):
    module = importlib.import_module(module_name)
    output_dir = pathlib.Path(output_dir).absolute()
    files = []
    for module_name, module, leaf, file in get_all_modules_from_files(module):
        # print(module_name)
        def do_doc():
            doc_path, doc = doc_module(
                module_name, module, output_dir, source_location, leaf
            )
            with open(doc_path.absolute(), "w") as doc_file:
                doc_file.write(doc)

        do_doc()
        files.append((file, do_doc))
        print(f"Built documentation for {file.absolute()}")
    return files


if __name__ == "__main__":
    cli()
