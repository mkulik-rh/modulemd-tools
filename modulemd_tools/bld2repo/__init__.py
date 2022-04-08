import json
import os
import urllib.request
import subprocess

import koji

from modulemd_tools.modulemd_tools.yaml import _yaml2stream


def get_koji_build_info(build_id, session, config):
    """
    Returns build information from koji based on build id.

    :param dict build_id: build id of a build in koji.
    :param koji.ClientSession session: koji connection session object
    :return: build information.
    :rtype: dict
    """

    print("Retriewing build metadata from: ", config.koji_host)
    build = session.getBuild(build_id)
    if not build:
        raise Exception("Build with id '{id}' has not been found.".format(id=build_id))

    print("Build with the ID", build_id, "found.")

    return build


def get_buildrequire_pkgs_from_build(build, session, config):
    """
    Function which queries koji for pkgs whom belong to a given build tag
    of a koji build and paires rpms with their respective package.

    :param dict build: build information returned by koji.
    :param koji.ClientSession session: koji connection session object
    :return: list of pairings of package and rpms.
    :rtype: list
    """

    tags = session.listTags(build["build_id"])

    build_tag = [t["name"] for t in tags if t["name"].endswith("-build")]
    if not build_tag:
        raise Exception(
            "Build with id '{id}' is not tagged in a 'build' tag.".format(id=build["build_id"]))

    tag_data = session.listTaggedRPMS(build_tag[0], latest=True, inherit=True)

    print("Found the build tag '", build_tag[0], "' associated with the build.")
    tagged_rpms = tag_data[0]
    tagged_pkgs = tag_data[1]
    pkgs = []
    archs = [config.arch, "noarch"]
    print("Gathering packages and rpms tagged in '", build_tag[0], "'.")
    for pkg in tagged_pkgs:
        pkg_md = {
            "package": pkg,
            "rpms": [],
        }

        for rpm in tagged_rpms:
            if pkg["build_id"] == rpm["build_id"] and rpm["arch"] in archs:
                pkg_md["rpms"].append(rpm)

        if pkg_md["rpms"]:
            pkgs.append(pkg_md)
    print("Gathering done.")
    return pkgs


def filter_buildrequire_pkgs(build, pkgs, config):
    """
    Filter RPMs based on BuildOrder from Mobile Build Service.

    :param dict build: build information returned by koji.
    :param list pkgs: pkgs and rpms information which belong to a given build
    :return: list of filtred pkgs.
    :rtype: list
    """

    # Example: 22.module+el9.0.0+12688+90c2b6fe
    mbs_id = build['release'].split('+')[-2]

    if not mbs_id:
        raise Exception("Module build id for '{id}' cannot be found.".format(id=build["build_id"]))

    print("MBS build ID: {id}".format(id=mbs_id))

    print("Retriewing modelemd metadata from: ", config.mbs_host)
    file = download_file(
        "{url}/module-build-service/1/module-builds/{id}?verbose=true".format(url=config.mbs_host, id=mbs_id))

    mbs_json_data = json.loads(file)

    if "modulemd" not in mbs_json_data:
        raise Exception("Metadata modulemd not found.")

    stream = _yaml2stream(mbs_json_data["modulemd"])

    component_list = {"rpms": stream.get_rpm_component_names(
    ), "modules": stream.get_module_component_names()}

    # Get main component buildorder
    if build['package_name'] in component_list["rpms"]:
        main_component = stream.get_rpm_component(build['package_name'])
    else:
        main_component = stream.get_module_component(build['package_name'])

    main_component_build_order = main_component.get_buildorder()

    filtered_pkgs = []

    for pkg in pkgs:
        # Check if pkg is part of MBS component
        if any(pkg["package"]["name"] in c for c in component_list.values()):
            if main_component_build_order == 0:
                continue

            if pkg["package"]["name"] in component_list["rpms"]:
                component = stream.get_rpm_component(pkg["package"]["name"])
            else:
                component = stream.get_module_component(pkg["package"]["name"])

            component_build_order = component.get_buildorder()

            # skip not required pkgs
            if component_build_order >= main_component_build_order:
                continue

        filtered_pkgs.append(pkg)

    return filtered_pkgs


def add_rpm_urls(pkgs, config):
    """
    For each rpm from a package creates an download url and adds it to the package.

    :param list pkgs: list of packages
    :return pkgs: list of packages and their rpms
    :rtype: list
    :return rpm_num: number of rpms
    :rtype: int
    """
    rpm_num = 0
    for pkg in pkgs:
        build_path = koji.pathinfo.build(pkg["package"]).replace(koji.pathinfo.topdir, "")
        pkg["rpm_urls"] = []
        for rpm in pkg["rpms"]:
            rpm_num += 1
            rpm_filename = "-".join([rpm["name"], rpm["version"],
                                     rpm["release"]]) + "." + rpm["arch"] + ".rpm"
            rpm_url = config.koji_storage_host + build_path + "/" + rpm["arch"] + "/" + rpm_filename
            pkg["rpm_urls"].append(rpm_url)

    return pkgs, rpm_num


def download_file(url, target_pkg_dir=None, filename=None):
    """
    Wrapper function for downloading a file.

    :param str url: url to a file
    :param str target_pkg_dir: the dir where the file should be downloaded. Defaults to None.
    :param str filename: the name of the downloaded file. Defaults to None.
    :rtype: (Any, optional)
    """
    try:
        # Check last 2 function variables
        if all(v is None for v in locals()[-2:]):
            abs_file_path = "/".join([target_pkg_dir, filename])
            urllib.request.urlretrieve(url, abs_file_path)
        else:
            return urllib.request.urlopen(url).read().decode()
    except Exception as ex:
        raise Exception("HTTP error for url: {url}\nError message: {msg}\nHTTP code: {code}".format(
            url=ex.url, msg=ex.msg, code=ex.code))


def rpm_bulk_download(pkgs, rpm_num, working_dir):
    """
    Downloads all the rpms from which belong to a package.

    :param list pkgs: list of pkgs with their rpms and urls to those rpms
    :param int rpm_num: number of all the rpms included in pkgs
    :param str working_dir: the dir where the rpms will be downloaded
    """
    print("Starting bulk download of rpms...")
    rpm_dwnlded = 0

    for pkg in pkgs:
        for url in pkg["rpm_urls"]:
            # we print the status of the download
            status = "[{done}/{total}]".format(done=rpm_dwnlded, total=rpm_num)
            print(status, end="\r", flush=True)
            # we store the rpm in a similar location as it is on the storage server
            url_parts = url.split("/")
            filename = url_parts[-1]
            arch = url_parts[-2]
            pkg_name = "-".join([url_parts[-5], url_parts[-4], url_parts[-3]])
            target_pkg_dir = "/".join([working_dir, pkg_name, arch])
            # we create the package dir if it is not created
            if not os.path.exists(target_pkg_dir):
                os.makedirs(target_pkg_dir)
            else:
                # if we downloaded the file already we skip
                file_path = target_pkg_dir + "/" + filename
                if os.path.exists(file_path):
                    rpm_dwnlded += 1
                    continue
            download_file(url, target_pkg_dir, filename)
            rpm_dwnlded += 1

    # update the status last time to mark all of the rpms downloaded
    status = "[{done}/{total}]".format(done=rpm_dwnlded, total=rpm_num)
    print(status)
    print("Download successful.")


def create_repo(working_dir):
    print("Calling createrepo_c...")
    args = ["createrepo_c", working_dir]
    subprocess.Popen(args, cwd=working_dir).communicate()
    print("Repo created.")
