import re


def multi_format(string: str, value: str) -> str:
    return string.format(*[value for _ in range(string.count('{}'))])


def escape_css_class_name(string: str) -> str:
    return string.replace('/', r'\/').replace(':', r'\:')


class Tail:
    def __init__(
        self,
        prefix: str,
        lookup: dict[str, str],
        br_lookup: dict[str, str],
        variables: dict[str, dict[str, str]],
    ) -> None:
        self.prefix = prefix
        self.lookup = lookup
        self.br_lookup = br_lookup
        self.variables = variables

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
        else:
            for namespace, table in self.variables.items():
                if namespace in self.lookup and key in table:
                    return multi_format(self.lookup[namespace], table[key])
        return self.lookup[key]

    def generate_css(self, class_: str) -> str:
        *prefixes, class_name = class_.split(':')
        inner = self.generate_inner_css(class_name)
        res = inner
        for prefix in reversed(prefixes):
            res = self.br_lookup[prefix].format(res)

        return f'.{escape_css_class_name(class_)}{{{res}}}'


class Tails:
    def __init__(self, *tails: Tail) -> None:
        # NOTE: longer prefixes are by definition more specific
        # and prefixes with the same length cannot overlap
        #
        # NOTE: also note that if we just self.tails.append(...)
        # it will not be sorted!
        self.tails = sorted(tails, key=lambda x: len(x.prefix), reverse=True)

    def generate_css(self, *classes: str) -> str:
        css: list[str] = []

        # TODO: sort classes
        sorted_classes = sorted(set(classes), key=lambda x: x)

        for class_ in sorted_classes:
            for tail in self.tails:
                if class_.startswith(tail.prefix):
                    try:
                        css.append(tail.generate_css(class_))
                    except KeyError:
                        pass
                    break

        return '\n'.join(css)
