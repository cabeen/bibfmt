# Copyright (c) 2006, 2007, 2008, 2009, 2010, 2011, 2012  Andrey Golovizin
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

import yaml
from pybtex.database import Entry
from pybtex.database.output import BaseWriter


class Writer(BaseWriter):
    """Outputs YAML markup"""

    def _to_dict(self, bib_data):
        def process_person_roles(entry):
            for role, persons in entry.persons.iteritems():
                yield role, list(process_persons(persons))

        def process_person(person):
            for type in ('first', 'middle', 'prelast', 'last', 'lineage'):
                name = person.get_part_as_text(type)
                if name:
                    yield type, name

        def process_persons(persons):
            for person in persons:
                yield dict(process_person(person))
                
        def process_entries(bib_data):
            for key, entry in bib_data.iteritems():
                fields = dict(entry.fields)
                fields['type'] = entry.original_type
                fields.update(process_person_roles(entry))
                yield key, fields

        data = {'entries': dict(process_entries(bib_data.entries))}
        if bib_data.preamble:
            data['preamble'] = bib_data.preamble
        return data

    def _dump(self, bib_data, encoding=None, stream=None):
        return yaml.safe_dump(bib_data, stream, encoding=encoding, allow_unicode=True, default_flow_style=False, indent=4)

    def write_stream(self, bib_data, stream):
        return self._dump(self._to_dict(bib_data), encoding='UTF-8', stream=stream)

    def to_string(self, bib_data):
        return self._dump(self._to_dict(bib_data), encoding=None)

    def to_bytes(self, bib_data):
        return self._dump(self._to_dict(bib_data), encoding='UTF-8')
