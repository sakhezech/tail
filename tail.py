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
        patterns: dict[str, str],
        variants: dict[str, str],
        variables: dict[str, dict[str, str]],
    ) -> None:
        self.variables = variables
        self.variables_regexes = {
            namespace: '|'.join(var_table.keys()).join(
                (f'(?P{namespace}', ')')
            )
            for namespace, var_table in self.variables.items()
        }
        self.special = {
            # TODO: angle
            '<value>': r'\[(?P<value>.*)\]',
            '<custom-property>': r'\((?P<custom-property>.*)\)',
            '<ratio>': r'(?P<ratio>\d+/\d+)',
            '<fraction>': r'(?P<fraction>\d+/\d+)',
            '<number>': r'(?P<number>\d+)',
            '<percentage>': r'(?P<percentage>\d+%)',
        }

        s, d = self.split_static_dynamic(patterns)
        self.p_static, self.p_dynamic = s, d
        s, d = self.split_static_dynamic(variants)
        self.v_static, self.v_dynamic = s, d

    def regexify(self, key: str) -> str:
        """
        Replaces <...>'s with their regexes.
        """
        regex = re.escape(key)
        for key, regex_part in self.special.items():
            regex = regex.replace(key, regex_part)
        for key in self.variables.keys():
            regex = regex.replace(key, self.variables_regexes[key])
        return regex

    def split_static_dynamic(
        self, lookup: dict[str, str]
    ) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
        static = {}
        dynamic = {}
        for key, template in lookup.items():
            if '<' in key:
                static_part, _, dynamic_part = key.partition('<')
                dynamic_part = f'<{dynamic_part}'
                dynamic.setdefault(static_part, {})
                regex = self.regexify(dynamic_part)
                dynamic[static_part][regex] = template
            else:
                static[key] = template
        dynamic = {
            key: dynamic[key]
            for key in sorted(
                dynamic.keys(), key=lambda x: len(x), reverse=True
            )
        }
        return static, dynamic

    def get_variable_value(self, namespace: str, key: str) -> str:
        """
        Gets the correct value depending on the namespace.

        I.e. if the namespace is <number> or something like that we don't need
          to retrieve the value, the key is the correct value; and if the
          namespace is <color> we have to go get it.
        """
        if namespace in self.special:
            return key
        else:
            return self.variables[namespace][key]

    def resolve_string(
        self,
        class_: str,
        static: dict[str, str],
        dynamic: dict[str, dict[str, str]],
    ) -> str | None:
        """
        This function resolves a string wiat a pattern to output lookup table.

        For example::

            variables = { 'namespace': { 'key': 'value' } }
            patterns = {
                'special-in-<number>': 'special-out-<number>',
                'var-in-<namespace>': 'var-out-<namespace>',
            }

            'special-in-123' -> 'special-out-123'
            'special-in-nothing' -> None
            'var-in-key' -> 'var-out-value'
        """
        if class_ in static:
            return static[class_]

        for prefix, template_table in dynamic.items():
            if not class_.startswith(prefix):
                continue
            dynamic_part = class_.removeprefix(prefix)
            for regex, template in template_table.items():
                if m := re.fullmatch(regex, dynamic_part):
                    for namespace, var_key in m.groupdict().items():
                        namespace = namespace.join('<>')
                        template = template.replace(
                            namespace,
                            self.get_variable_value(namespace, var_key),
                        )
                    return template

    def generate_inner_css(self, class_: str) -> str | None:
        return self.resolve_string(class_, self.p_static, self.p_dynamic)

    def apply_variants(self, css: str, prefixes: list[str]) -> str | None:
        for prefix in reversed(prefixes):
            template = self.resolve_string(
                prefix, self.v_static, self.v_dynamic
            )
            if not template:
                return None
            css = template.format(css)
        return css

    def generate_css(self, *classes: str) -> str:
        css: list[str] = []

        classes_: list[tuple[str, str, list[str]]] = []
        for unstripped_class in set(classes):
            *prefixes, class_ = unstripped_class.split(':')
            classes_.append((class_, unstripped_class, prefixes))
        # TODO: sort classes
        classes_.sort(key=lambda x: x)

        for class_, full_class, prefixes in classes_:
            inner = self.generate_inner_css(class_)
            if inner is None:
                continue
            outer = self.apply_variants(inner, prefixes)
            if outer is None:
                continue
            css.append(f'.{escape_css_class_name(full_class)}{{{outer}}}')

        return '\n'.join(css)
