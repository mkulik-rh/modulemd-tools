from textwrap import dedent

import pytest


@pytest.fixture
def moduleB_yaml():
    return dedent("""
        ---
        document: modulemd-defaults
        version: 1
        data:
          module: bar
          stream: stable
          profiles:
            stable: [everything]
        ...
        ---
        document: modulemd
        version: 2
        data:
          name: bar
          stream: stable
          version: 234
          context: fc33
          summary: Let's put some bar's summary here
          description: >-
            Let's put some bar's description here
          license:
            module:
            - Bar License
            content:
            - A fresh bar license for your test suites
          profiles:
            everything:
              rpms:
              - bar-utils
          api:
            rpms:
            - bar-utils
          components:
            rpms:
              bar-utils:
                rationale: Present in the repository
          artifacts:
            rpms:
            - bar-utils-2:3-4.fc33.noarch
        ...
    """).lstrip()


@pytest.fixture
def two_modules_merged_yamls():
    return dedent("""
        ---
        document: modulemd-defaults
        version: 1
        data:
          module: bar
          stream: stable
          profiles:
            stable: [everything]
        ...
        ---
        document: modulemd
        version: 2
        data:
          name: bar
          stream: stable
          version: 234
          context: fc33
          summary: Let's put some bar's summary here
          description: >-
            Let's put some bar's description here
          license:
            module:
            - Bar License
            content:
            - A fresh bar license for your test suites
          profiles:
            everything:
              rpms:
              - bar-utils
          api:
            rpms:
            - bar-utils
          components:
            rpms:
              bar-utils:
                rationale: Present in the repository
          artifacts:
            rpms:
            - bar-utils-2:3-4.fc33.noarch
        ...
        ---
        document: modulemd-defaults
        version: 1
        data:
          module: foo
          stream: devel
          profiles:
            devel: [everything]
        ...
        ---
        document: modulemd
        version: 2
        data:
          name: foo
          stream: devel
          version: 123
          context: fc33
          summary: Let's put some foo's summary here
          description: >-
            Let's put some foo's description here
          license:
            module:
            - Foo License
            content:
            - A fresh foo license for your test suites
          profiles:
            everything:
              rpms:
              - foo-utils
          api:
            rpms:
            - foo-utils
          components:
            rpms:
              foo-utils:
                rationale: Present in the repository
          artifacts:
            rpms:
            - foo-utils-1:2-3.fc33.noarch
        ...
    """).lstrip()


@pytest.fixture
def module_with_repodata_dir():
    return dedent("""
        ---
        document: modulemd-defaults
        version: 1
        data:
          module: dummy
          stream: rolling
          profiles:
            rolling: [everything]
        ...
        ---
        document: modulemd
        version: 2
        data:
          name: dummy
          stream: rolling
          version: 1
          context: abcdef12
          summary: <auto-generated module summary>
          description: >-
            <auto-generated module description>
          license:
            module:
            - MIT
            content:
            - <FILL THIS IN>
          profiles:
            everything:
              rpms:
              - python-django-bash-completion
          api:
            rpms:
            - python-django-bash-completion
          components:
            rpms:
              python-django:
                rationale: Present in the repository
          artifacts:
            rpms:
            - python-django-bash-completion-0:3.0.10-3.fc33.noarch
        ...
        ---
        document: modulemd-defaults
        version: 1
        data:
          module: foo
          stream: devel
          profiles:
            devel: [everything]
        ...
        ---
        document: modulemd
        version: 2
        data:
          name: foo
          stream: devel
          version: 123
          context: fc33
          summary: Let's put some foo's summary here
          description: >-
            Let's put some foo's description here
          license:
            module:
            - Foo License
            content:
            - A fresh foo license for your test suites
          profiles:
            everything:
              rpms:
              - foo-utils
          api:
            rpms:
            - foo-utils
          components:
            rpms:
              foo-utils:
                rationale: Present in the repository
          artifacts:
            rpms:
            - foo-utils-1:2-3.fc33.noarch
        ...
    """).lstrip()
