import os

from hatch.files.ci import Tox, TravisCI
from hatch.files.coverage import Codecov, CoverageConfig
from hatch.files.licenses import Apache2License, MITLicense
from hatch.files.readme import ReStructuredTextReadme
from hatch.files.setup import SetupFile
from hatch.files.vc import setup_git
from hatch.settings import DEFAULT_SETTINGS
from hatch.structures import Badge, File
from hatch.utils import create_file, normalize_package_name

LICENSES = {
    'mit': MITLicense,
    'apache2': Apache2License
}
README = {
    'rst': ReStructuredTextReadme,
}
VC_SETUP = {
    'git': setup_git,
}
CI_SERVICES = {
    'travis': TravisCI,
}
COVERAGE_SERVICES = {
    'codecov': Codecov,
}


def create_package(d, package_name, settings):
    normalized_package_name = normalize_package_name(package_name)
    cli = settings.get('cli')
    basic = settings.get('basic', DEFAULT_SETTINGS['basic'])
    extra_files = []

    name = settings.get('name') or DEFAULT_SETTINGS['name']
    email = settings.get('email') or DEFAULT_SETTINGS['email']
    pyversions = sorted(
        settings.get('pyversions') or DEFAULT_SETTINGS['pyversions']
    )
    vc_setup = VC_SETUP[settings.get('vc') or DEFAULT_SETTINGS['vc']]
    vc_url = settings.get('vc_url') or DEFAULT_SETTINGS['vc_url']
    package_url = vc_url + '/' + package_name

    readme_format = (
        settings.get('readme', {}).get('format') or
        DEFAULT_SETTINGS['readme']['format']
    )

    licenses = [
        LICENSES[li](name)
        for li in settings.get('licenses') or DEFAULT_SETTINGS['licenses']
    ]

    badges = []
    if not basic:
        for badge_info in settings.get('readme', {}).get('badges', []):
            image = badge_info.get('image', 'no_image')
            target = badge_info.get('target', 'no_target')

            try:
                badge_info.pop('image')
            except KeyError:
                pass

            try:
                badge_info.pop('target')
            except KeyError:
                pass

            badges.append(
                Badge(
                    image.format(package_name),
                    target.format(package_name),
                    badge_info
                )
            )

    readme = README[readme_format](
        package_name, pyversions, licenses, badges
    )

    setup_py = SetupFile(
        name, email, package_name, pyversions, licenses,
        readme, package_url, cli
    )

    coverage_service = settings.get('coverage') if not basic else None
    if coverage_service:
        coverage_service = COVERAGE_SERVICES[coverage_service]()
        extra_files.append(coverage_service)

    for service in settings.get('ci', []):
        if not basic:
            extra_files.append(CI_SERVICES[service](pyversions, coverage_service))

    coveragerc = CoverageConfig(package_name, cli)
    tox = Tox(pyversions, coverage_service)

    package_dir = os.path.join(d, normalized_package_name)
    init_py = File(
        '__init__.py',
        "__version__ = '0.0.1'\n"
    )
    init_py.write(package_dir)

    create_file(os.path.join(d, 'tests', '__init__.py'))
    create_file(os.path.join(d, 'requirements.txt'))

    if cli:
        cli_py = File(
            'cli.py',
            'def {}():\n    pass\n'.format(normalized_package_name)
        )
        cli_py.write(package_dir)
        main_py = File(
            '__main__.py',
            'import sys\n'
            'from {npn}.cli import {npn}\n'
            'sys.exit({npn}())\n'.format(npn=normalized_package_name)
        )
        main_py.write(package_dir)

    setup_py.write(d)
    readme.write(d)
    coveragerc.write(d)
    tox.write(d)

    for li in licenses:
        li.write(d)

    for file in extra_files:
        file.write(d)

    vc_setup(d, package_name)