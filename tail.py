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

    def generate_inner_css(self, class_: str) -> str:
        if class_ in self.lookup:
            return self.lookup[class_]

        for key, regex, rep_keys in self.special:
            if m := re.search(regex, class_):
                lookup_class = re.sub(regex, key, class_)
                if lookup_class in self.lookup:
                    if not rep_keys:
                        rep_keys = (key,)
                    res = self.lookup[lookup_class]
                    for k in rep_keys:
                        res = res.replace(k, m.group(1))
                    return res

        for namespace, var_table in self.variables.items():
            for lookup_key, template in self.lookup.items():
                if namespace not in lookup_key:
                    continue

                # A
                my_regex = lookup_key.replace(namespace, r'(.*)')
                m = re.match(my_regex, class_)
                if not m:
                    continue
                variable_nam = m.group(1)
                if variable_nam in var_table:
                    return template.replace(namespace, var_table[variable_nam])

                # B
                # for val_name, var_value in var_table.items():
                #     if lookup_key.replace(namespace, val_name) == class_:
                #         return template.replace(namespace, var_value)

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
