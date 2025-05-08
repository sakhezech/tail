import re


def escape_css_class_name(string: str) -> str:
    # TODO: replace with a better escaping function
    return (
        string.replace('/', r'\/')
        .replace(':', r'\:')
        .replace('[', r'\[')
        .replace(']', r'\]')
    )


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
        if key in self.lookup:
            return self.lookup[key]
        elif '[<value>]' in self.lookup and (m := re.match(r'\[(.*)\]', key)):
            val = m.group(1)
            return self.lookup['[<value>]'].replace('<value>', val)
        elif '(<custom-property>)' in self.lookup and (
            m := re.match(r'\((.*)\)', key)
        ):
            val = m.group(1)
            return self.lookup['(<custom-property>)'].replace(
                '<custom-property>', val
            )
        elif '<ratio>' in self.lookup and (m := re.match(r'\d+/\d+', key)):
            val = m.group(0)
            return self.lookup['<ratio>'].replace('<ratio>', val)
        elif '<fraction>' in self.lookup and (m := re.match(r'\d+/\d+', key)):
            val = m.group(0)
            return self.lookup['<fraction>'].replace('<fraction>', val)
        elif '<number>' in self.lookup and (m := re.match(r'\d+', key)):
            val = m.group(0)
            return self.lookup['<number>'].replace('<number>', val)
        else:
            for namespace, table in self.variables.items():
                if namespace in self.lookup and key in table:
                    return self.lookup[namespace].replace(
                        namespace, table[key]
                    )
        raise ValueError(f'class not valid: {class_}')

    def generate_css(self, class_: str, prefixes: list[str]) -> str:
        inner = self.generate_inner_css(class_)
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

        processed = []
        for unstripped_class in classes:
            *prefixes, class_ = unstripped_class.split(':')
            processed.append((class_, prefixes))

        # TODO: sort classes
        processed.sort(key=lambda x: x)

        for class_, prefixes in processed:
            for tail in self.tails:
                if class_.startswith(tail.prefix):
                    try:
                        css.append(tail.generate_css(class_, prefixes))
                    except ValueError:
                        pass
                    break

        return '\n'.join(css)
