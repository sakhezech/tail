import re


def multi_format(string: str, value: str) -> str:
    return string.format(*[value for _ in range(string.count('{}'))])


def escape_css_class_name(string: str) -> str:
    return string.replace('/', r'\/').replace(':', r'\:')


class Tail:
    def __init__(
        self, prefix: str, lookup: dict[str, str], br_lookup: dict[str, str]
    ) -> None:
        self.prefix = prefix
        self.lookup = lookup
        self.br_lookup = br_lookup

    def generate_inner_css(self, class_: str) -> str:
        key = class_.removeprefix(self.prefix)
        if '[<value>]' in self.lookup and (m := re.match(r'\[(.*)\]', key)):
            val = m.group(1)
            return multi_format(self.lookup['[<value>]'], val)
        elif '(<custom-property>)' in self.lookup and (
            m := re.match(r'\((.*)\)', key)
        ):
            val = m.group(1)
            return multi_format(self.lookup['(<custom-property>)'], val)
        elif '<ratio>' in self.lookup and (m := re.match(r'\d+/\d+', key)):
            val = m.group(0)
            return multi_format(self.lookup['<ratio>'], val)
        elif '<fraction>' in self.lookup and (m := re.match(r'\d+/\d+', key)):
            val = m.group(0)
            return multi_format(self.lookup['<fraction>'], val)
        elif '<number>' in self.lookup and (m := re.match(r'\d+', key)):
            val = m.group(0)
            return multi_format(self.lookup['<number>'], val)
        return self.lookup[key]

    def generate_css(self, class_: str) -> str:
        *prefixes, class_name = class_.split(':')
        inner = self.generate_inner_css(class_name)
        res = inner
        for prefix in reversed(prefixes):
            res = self.br_lookup[prefix].format(res)

        return f'.{escape_css_class_name(class_)}{{{res}}}'
