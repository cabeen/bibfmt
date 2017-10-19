# vim:fileencoding=utf8

# Copyright (c) 2008, 2009, 2010, 2011, 2012  Andrey Golovizin
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
A template engine for bibliography entries and more.

Inspired by Brevé -- http://breve.twisty-industries.com/

>>> from pybtex.database import Entry, Person
>>> author = Person(first='First', last='Last', middle='Middle')
>>> fields = {
...         'title': 'The Book',
...         'year': '2000',
... }
>>> e = Entry('book', fields=fields)
>>> book_format = sentence(sep=', ') [
...     field('title'), field('year'), optional [field('sdf')]
... ]
>>> print unicode(book_format.format_data(e))
The Book, 2000.
>>> print unicode(words ['one', 'two', words ['three', 'four']].format_data(e))
one two three four
"""

from pybtex import richtext
from pybtex.exceptions import PybtexError

__test__ = {} # for doctest


class Proto(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return Node(*self.args, **self.kwargs)(*args, **kwargs)

    def __getitem__(self, children):
        return Node(*self.args, **self.kwargs)[children]

    def __repr__(self):
        return repr(Node(*self.args, **self.kwargs))

    def format_data(self, *args, **kwargs):
        return Node(*self.args, **self.kwargs).format_data(*args, **kwargs)

    def format(self):
        return self.format_data(None)


class Node(object):
    def __init__(self, name, f):
        self.name = name
        self.f = f
        self.args = []
        self.kwargs = {}
        self.children = []

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs.update(kwargs)
        return self

    def __getitem__(self, children):
        if isinstance(children, (list, tuple)):
            self.children = children
        else:
            self.children.append(children)
        return self

    def __repr__(self):
        """
        >>> join(', ')
        join(', ')
        >>> join
        join
        >>> join ['a']
        join ['a']
        >>> join ['a', 'b', 'c']
        join ['a', 'b', 'c']
        >>> join(' ') ['a', 'b', 'c']
        join(' ') ['a', 'b', 'c']
        >>> join(sep=' ') ['a', 'b', 'c']
        join(sep=' ') ['a', 'b', 'c']
        >>> join(sep=' ') [tag('em') ['a', 'b', 'c']]
        join(sep=' ') [tag('em') ['a', 'b', 'c']]

        """
        params = []
        args_repr = ', '.join(repr(arg) for arg in self.args)
        if args_repr:
            params.append(args_repr)
        kwargs_repr = ', '.join('%s=%s' % (key, repr(value))
                for (key, value) in self.kwargs.iteritems())
        if kwargs_repr:
            params.append(kwargs_repr)
        if params:
            params_repr = '(%s)' % ', '.join(params)
        else:
            params_repr = ''

        if self.children:
            children_repr = ' [%s]' % ', '.join(repr(child)
                    for child in self.children)
        else:
            children_repr = ''

        return ''.join([self.name, params_repr, children_repr])

    def format_data(self, data):
        """Format the given data into a piece of richtext.Text"""

        return self.f(self.children, data, *self.args, **self.kwargs)

    def format(self):
        """A convenience function to be used instead of format_data
        when no data is needed.
        """

        return self.format_data(None)


def _format_data(node, data):
    try:
        f = node.format_data
    except AttributeError:
        return unicode(node)
    else:
        return f(data)


def _format_list(list_, data):
    return (_format_data(part, data) for part in list_)


def node(f):
    if f.__doc__:
        __test__[f.__name__] = f
    return Proto(f.__name__, f)


@node
def join(children, data, sep='', sep2=None, last_sep=None):
    """Join text fragments together.
    >>> print unicode(join.format())
    <BLANKLINE>
    >>> print unicode(join ['a', 'b', 'c', 'd', 'e'].format())
    abcde
    >>> print unicode(join(sep=', ', sep2=' and ', last_sep=', and ') ['Tom', 'Jerry'].format())
    Tom and Jerry
    >>> print unicode(join(sep=', ', sep2=' and ', last_sep=', and ') ['Billy', 'Willy', 'Dilly'].format())
    Billy, Willy, and Dilly
    """

    if sep2 is None:
        sep2 = sep
    if last_sep is None:
        last_sep = sep
    parts = [part for part in _format_list(children, data) if part]
    if len(parts) <= 1:
        return richtext.Text(*parts)
    elif len(parts) == 2:
        return richtext.Text(sep2).join(parts)
    else:
        return richtext.Text(last_sep).join([richtext.Text(sep).join(parts[:-1]), parts[-1]])


@node
def words(children, data, sep=' '):
    """Join text fragments with spaces or something else."""

    return join(sep) [children].format_data(data)


@node
def together(children, data, last_tie=True):
    """
    Try to keep words together, like BibTeX does.

    >>> print unicode(together ['very', 'long', 'road'].format())
    very long<nbsp>road
    >>> print unicode(together ['a', 'very', 'long', 'road'].format())
    a<nbsp>very long<nbsp>road
    """
    from pybtex.bibtex.names import tie_or_space
    tie = richtext.Text(richtext.nbsp)
    space = richtext.Text(' ')
    parts = [part for part in _format_list(children, data) if part]
    if not parts:
        return richtext.Text()
    if len(parts) <= 2:
        tie2 = tie if last_tie else tie_or_space(parts[0], tie, space)
        return tie2.join(parts)
    else:
        last_tie = tie if last_tie else tie_or_space(parts[-1], tie, space)
        return richtext.Text(parts[0], tie_or_space(parts[0], tie, space),
                space.join(parts[1:-1]), last_tie, parts[-1])


@node
def sentence(children, data, capfirst=None, capitalize=True, add_period=True, sep=', '):
    """Join text fragments, capitalyze the first letter, add a period to the end.

    >>> print unicode(sentence.format())
    <BLANKLINE>
    >>> print unicode(sentence(sep=' ') ['mary', 'had', 'a', 'little', 'lamb'].format())
    Mary had a little lamb.
    >>> print unicode(sentence(capitalize=False, add_period=False) ['uno', 'dos', 'tres'].format())
    uno, dos, tres
    """

    if capfirst is not None:
        from warnings import warn
        message = (
            'sentence(capfirst={0}) is deprecated since 0.19: '
            'use sentence(capitalize={0}) instead'
        )
        warn(message.format(capfirst), DeprecationWarning)
        capitalize = capfirst

    text = join(sep) [children].format_data(data)
    if capitalize:
        text = text.capitalize()
    if add_period:
        text = text.add_period()
    return text


class FieldIsMissing(PybtexError):
    def __init__(self, field_name, entry):
        self.field_name = field_name
        super(FieldIsMissing, self).__init__(
            u'missing {0} in {1}'.format(field_name, getattr(entry, 'key', '<unnamed>'))
        )

@node
def field(children, data, name, apply_func=None):
    """Return the contents of the bibliography entry field."""

    assert not children
    try:
        field = data.fields[name]
    except KeyError:
        raise FieldIsMissing(name, data)
    else:
        if apply_func:
            field = apply_func(field)
        return field


@node
def names(children, data, role, **kwargs):
    """Return formatted names."""

    assert not children
    try:
        persons = data.persons[role]
    except KeyError:
        # role is a bibtex field so it makes sense
        # to raise FieldIsMissing; optional will catch it
        raise FieldIsMissing(role, data)
    return join(**kwargs) [[person.text for person in persons]].format_data(data)


@node
def optional(children, data):
    """If children contain a missing bibliography field, return None.
    Else return formatted children.

    >>> from pybtex.database import Entry
    >>> template = optional [field('volume'), optional['(', field('number'), ')']]
    >>> template.format_data(Entry('article'))
    Text()

    """

    try:
        return richtext.Text(*_format_list(children, data))
    except FieldIsMissing:
        return richtext.Text()

@node
def optional_field(children, data, *args, **kwargs):
    assert not children
    return optional [field(*args, **kwargs)].format_data(data)

@node
def tag(children, data, name):
    """Wrap text into a tag.

    >>> print tag('em') ['important'].format().render_as('html')
    <em>important</em>
    >>> print sentence ['ready', 'set', tag('em') ['go']].format().render_as('html')
    Ready, set, <em>go</em>.
    """
    parts = _format_list(children, data)
    return richtext.Tag(name, *_format_list(children, data))

@node
def href(children, data):
    """Wrap text into a href.

    >>> print href ['www.test.org', 'important'].format().render_as('html')
    <a href="www.test.org">important</a>
    >>> print sentence ['ready', 'set', href ['www.test.org', 'go']].format().render_as('html')
    Ready, set, <a href="www.test.org">go</a>.
    """
    parts = _format_list(children, data)
    return richtext.HRef(*parts)

@node
def first_of(children, data):
    """Return first nonempty child."""

    for child in _format_list(children, data):
        if child:
            return child
    return richtext.Text()
