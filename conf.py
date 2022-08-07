# -*- coding: utf-8 -*-
"""
DFHack documentation build configuration file

This file is execfile()d with the current directory set to its
containing dir.

Note that not all possible configuration values are present in this
autogenerated file.

All configuration values have a default; values that are commented out
serve to show the default.
"""

# pylint:disable=redefined-builtin

import datetime
import os
import re
import shlex  # pylint:disable=unused-import
import sphinx
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'docs', 'sphinx_extensions'))
from dfhack.util import write_file_if_changed

if os.environ.get('DFHACK_DOCS_BUILD_OFFLINE'):
    # block attempted image downloads, particularly for the PDF builder
    def request_disabled(*args, **kwargs):
        raise RuntimeError('Offline build - network request blocked')

    import urllib3.util
    urllib3.util.create_connection = request_disabled

    import urllib3.connection
    urllib3.connection.HTTPConnection.connect = request_disabled

    import requests
    requests.request = request_disabled
    requests.get = request_disabled


# -- Autodoc for DFhack plugins and scripts -------------------------------

def doc_dir(dirname, files, prefix):
    """Yield (name, includepath) for each file in the directory."""
    sdir = os.path.relpath(dirname, '.').replace('\\', '/').replace('../', '')
    if prefix == '.':
        prefix = ''
    else:
        prefix += '/'
    for f in files:
        if f[-4:] != '.rst':
            continue
        yield prefix + f[:-4], sdir + '/' + f


def doc_all_dirs():
    """Collect the commands and paths to include in our docs."""
    tools = []
    # TODO: as we scan the docs, parse out the tags and short descriptions and
    # build a map for use in generating the tags pages and links in the tool
    # doc footers
    for root, _, files in os.walk('docs/builtins'):
        tools.extend(doc_dir(root, files, os.path.relpath(root, 'docs/builtins')))
    for root, _, files in os.walk('docs/plugins'):
        tools.extend(doc_dir(root, files, os.path.relpath(root, 'docs/plugins')))
    for root, _, files in os.walk('scripts/docs'):
        tools.extend(doc_dir(root, files, os.path.relpath(root, 'scripts/docs')))
    return tuple(tools)

DOC_ALL_DIRS = doc_all_dirs()


def get_tags():
    tags = []
    tag_re = re.compile(r'- `tag/([^`]+)`: (.*)')
    with open('docs/Tags.rst') as f:
        lines = f.readlines()
        for line in lines:
            m = re.match(tag_re, line.strip())
            if m:
                tags.append((m.group(1), m.group(2)))
    return tags


def generate_tag_indices():
    os.makedirs('docs/tags', mode=0o755, exist_ok=True)
    with write_file_if_changed('docs/tags/index.rst') as topidx:
        for tag_tuple in get_tags():
            tag = tag_tuple[0]
            with write_file_if_changed(('docs/tags/{name}.rst').format(name=tag)) as tagidx:
                tagidx.write('TODO: add links to the tools that have this tag')
            topidx.write(('.. _tag/{name}:\n\n').format(name=tag))
            topidx.write(('{name}\n').format(name=tag))
            topidx.write(('{underline}\n').format(underline='-'*len(tag)))
            topidx.write(('{desc}\n\n').format(desc=tag_tuple[1]))
            topidx.write(('.. include:: /docs/tags/{name}.rst\n\n').format(name=tag))


def write_tool_docs():
    """
    Creates a file for each tool with the ".. include::" directives to pull in
    the original documentation. Then we generate a label and useful info in the
    footer.
    """
    for k in DOC_ALL_DIRS:
        header = ':orphan:\n'
        label = ('.. _{name}:\n\n').format(name=k[0])
        # TODO: can we autogenerate the :dfhack-keybind: line? it would go beneath
        # the tool header, which is currently in the middle of the included file.
        # should we remove those headers from the doc files and just generate them
        # here? That might be easier. But then where will the tags go? It would
        # look better if they were above the keybinds, but then we'd be in the
        # same situation.
        include = ('.. include:: /{path}\n\n').format(path=k[1])
        # TODO: generate a footer with links to tools that share at least one
        # tag with this tool. Just the tool names, strung across the bottom of
        # the page in one long wrapped line, similar to how the wiki does it
        os.makedirs(os.path.join('docs/tools', os.path.dirname(k[0])),
                    mode=0o755, exist_ok=True)
        with write_file_if_changed('docs/tools/{}.rst'.format(k[0])) as outfile:
            outfile.write(header)
            if k[0] != 'search':
                outfile.write(label)
            outfile.write(include)


def all_keybinds_documented():
    """Check that all keybindings are documented with the :dfhack-keybind:
    directive somewhere."""
    undocumented_binds = set(KEYBINDS)
    tools = set(i[0] for i in DOC_ALL_DIRS)
    for t in tools:
        with open(('./docs/tools/{}.rst').format(t)) as f:
            tool_binds = set(re.findall(':dfhack-keybind:`(.*?)`', f.read()))
            undocumented_binds -= tool_binds
    if undocumented_binds:
        raise ValueError('The following DFHack commands have undocumented '
                         'keybindings: {}'.format(sorted(undocumented_binds)))


# Actually call the docs generator and run test
write_tool_docs()
generate_tag_indices()
#all_keybinds_documented() # comment out while we're transitioning

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.8'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.extlinks',
    'dfhack.changelog',
    'dfhack.lexer',
    'dfhack.tool_docs',
]

sphinx_major_version = sphinx.version_info[0]

def get_caption_str(prefix=''):
    return prefix + (sphinx_major_version >= 5 and '%s' or '')

# This config value must be a dictionary of external sites, mapping unique
# short alias names to a base URL and a prefix.
# See http://sphinx-doc.org/ext/extlinks.html
extlinks = {
    'wiki': ('https://dwarffortresswiki.org/%s', get_caption_str()),
    'forums': ('http://www.bay12forums.com/smf/index.php?topic=%s',
               get_caption_str('Bay12 forums thread ')),
    'dffd': ('https://dffd.bay12games.com/file.php?id=%s',
             get_caption_str('DFFD file ')),
    'bug': ('https://www.bay12games.com/dwarves/mantisbt/view.php?id=%s',
            get_caption_str('Bug ')),
    'source': ('https://github.com/DFHack/dfhack/tree/develop/%s',
               get_caption_str()),
    'source-scripts': ('https://github.com/DFHack/scripts/tree/master/%s',
                       get_caption_str()),
    'issue': ('https://github.com/DFHack/dfhack/issues/%s',
               get_caption_str('Issue ')),
    'commit': ('https://github.com/DFHack/dfhack/commit/%s',
               get_caption_str('Commit ')),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["docs/templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst']

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'DFHack'
copyright = '2015-%d, The DFHack Team' % datetime.datetime.now().year
author = 'The DFHack Team'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

def get_version():
    """Return the DFHack version string, from CMakeLists.txt"""
    version = release = ''  #pylint:disable=redefined-outer-name
    pattern = re.compile(r'set\((df_version|dfhack_release)\s+"(.+?)"\)')
    try:
        with open('CMakeLists.txt') as f:
            for s in f.readlines():
                for match in pattern.findall(s.lower()):
                    if match[0] == 'df_version':
                        version = match[1]
                    elif match[0] == 'dfhack_release':
                        release = match[1]
        return (version + '-' + release).replace('")\n', '')
    except IOError:
        return 'unknown'

# The short X.Y version.
# The full version, including alpha/beta/rc tags.
version = release = get_version()

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# strftime format for |today| and 'Last updated on:' timestamp at page bottom
today_fmt = html_last_updated_fmt = '%Y-%m-%d'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    'README.md',
    'build*',
    'depends/*',
    'docs/html/*',
    'docs/tags/*',
    'docs/text/*',
    'docs/builtins/*',
    'docs/pdf/*',
    'docs/plugins/*',
    'docs/pseudoxml/*',
    'docs/xml/*',
    'scripts/docs/*',
    'plugins/*',
    ]

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = 'ref'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# The default language to highlight source code in.
highlight_language = 'dfhack'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

rst_prolog = """
.. |sphinx_min_version| replace:: {sphinx_min_version}
.. |dfhack_version| replace:: {dfhack_version}
""".format(
    sphinx_min_version=needs_sphinx,
    dfhack_version=version,
)

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'logo': 'dfhack-logo.png',
    'github_user': 'DFHack',
    'github_repo': 'dfhack',
    'github_button': False,
    'travis_button': False,
    'fixed_sidebar': True,
}

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = 'DFHack Docs'

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = 'docs/styles/dfhack-icon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['docs/styles']

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    '**': [
        'about.html',
        'relations.html',
        'searchbox.html',
        'localtoc.html',
    ]
}

# If false, no module index is generated.
html_domain_indices = False

# If false, no genindex.html is generated.
html_use_index = True

html_css_files = [
    'dfhack.css',
]

if sphinx_major_version >= 5:
    html_css_files.append('sphinx5.css')

# -- Options for LaTeX output ---------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'DFHack.tex', 'DFHack Documentation',
     'The DFHack Team', 'manual'),
]

latex_toplevel_sectioning = 'part'

# -- Options for text output ---------------------------------------------

from sphinx.writers import text

text.MAXWIDTH = 52
