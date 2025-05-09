import re


def escape_css_class_name(string: str) -> str:
    # TODO: replace with a better escaping function
    return (
        string.replace('/', r'\/')
        .replace(':', r'\:')
        .replace('[', r'\[')
        .replace(']', r'\]')
        .replace('(', r'\(')
        .replace(')', r'\)')
    )


class Tail:
    def __init__(
        self,
        lookup: dict[str, str],
        br_lookup: dict[str, str],
        variables: dict[str, dict[str, str]],
    ) -> None:
        self.lookup = lookup
        self.br_lookup = br_lookup
        self.variables = variables

        self.special: list[tuple[str, str, tuple[str, ...] | None]] = [
            # TODO: angle
            ('[<value>]', r'\[(.*)\]$', ('<value>',)),
            ('(<custom-property>)', r'\((.*)\)$', ('<custom-property>',)),
            ('<ratio>', r'(\d+/\d+)$', None),
            ('<fraction>', r'(\d+/\d+)$', None),
            ('<number>', r'(\d+)$', ('<number>', '<value>')),
            ('<percentage>', r'(\d+%)$', None),
        ]

    def resolve_string(
        self, string: str, lookup: dict[str, str]
    ) -> str | None:
        """
        This function resolves a string wiat a pattern to output lookup table.

        For example::

            variables = { 'namespace': { 'key': 'value' } }
            lookup = {
                'special-in-<number>': 'special-out-<number>',
                'var-in-<namespace>' -> 'var-out-<namespace>',
            }

            'special-in-123' -> 'special-out-123'
            'special-in-nothing' -> None
            'var-in-key' -> 'var-out-value'
        """
        if string in lookup:
            return lookup[string]

        for key, regex, rep_keys in self.special:
            if m := re.search(regex, string):
                lookup_class = re.sub(regex, key, string)
                if lookup_class in lookup:
                    if not rep_keys:
                        rep_keys = (key,)
                    res = lookup[lookup_class]
                    for k in rep_keys:
                        res = res.replace(k, m.group(1))
                    return res

        for namespace, var_table in self.variables.items():
            for lookup_key, template in lookup.items():
                if namespace not in lookup_key:
                    continue

                # A
                my_regex = lookup_key.replace(namespace, r'(.*)')
                m = re.match(my_regex, string)
                if not m:
                    continue
                variable_nam = m.group(1)
                if variable_nam in var_table:
                    return template.replace(namespace, var_table[variable_nam])

                # B
                # for val_name, var_value in var_table.items():
                #     if lookup_key.replace(namespace, val_name) == class_:
                #         return template.replace(namespace, var_value)

        return None

    def generate_inner_css(self, class_: str) -> str:
        if css := self.resolve_string(class_, self.lookup):
            return css
        raise ValueError(f'class not valid: {class_}')

    def generate_css(self, *classes: str) -> str:
        css: list[str] = []

        classes_: list[tuple[str, str, list[str]]] = []
        for unstripped_class in classes:
            *prefixes, class_ = unstripped_class.split(':')
            classes_.append((class_, unstripped_class, prefixes))
        # TODO: sort classes
        classes_.sort(key=lambda x: x)

        for class_, full_class, prefixes in classes_:
            try:
                inner = self.generate_inner_css(class_)
                res = inner
                for prefix in reversed(prefixes):
                    res = self.br_lookup[prefix].format(res)
                css.append(f'.{escape_css_class_name(full_class)}{{{res}}}')
            except ValueError:
                pass

        return '\n'.join(css)
