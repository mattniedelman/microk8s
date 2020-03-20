#!/usr/bin/python3
import os
import argparse

from common.utils import exit_if_no_permission, is_cluster_locked, wait_for_ready, is_cluster_ready, \
    get_available_addons, get_current_arch, get_addon_by_name, kubectl_get, kubectl_get_clusterroles


def is_enabled(addon, item):
    if addon in item:
        return True
    else:
        filepath = os.path.expandvars(addon)
        return os.path.isfile(filepath)
    
    return False


def print_console(isReady, enabled_addons, disabled_addons):
    console_formatter = "{:>1} {:<30} # {}"
    if isReady:
        print("microk8s is running")
    else:
        print("microk8s is not running. Use microk8s.inspect for a deeper inspection.")

    if isReady:
        print("addons:")
        if enabled_addons and len(enabled_addons) > 0:
            print('{:>2}'.format("enabled:"))
            for enabled in enabled_addons:
                print(console_formatter.format("", "{}: enabled".format(enabled["name"]), enabled["description"]))
        if disabled_addons and len(disabled_addons) > 0:
            for disabled in disabled_addons:
                print(console_formatter.format("", "{}: disabled".format(disabled["name"]), disabled["description"]))


def print_yaml(isReady, enabled_addons, disabled_addons):
    print("microk8s:")
    print("{:>2} {} {}".format("", "running:", isReady))

    if not isReady:
        print("{:>2} {} {}".format("","message:","microk8s is not running. Use microk8s.inspect for a deeper inspection."))
        return

    if isReady:    
        print("{:>2}".format("addons:"))
        for enabled in enabled_addons:
            print("{:>4} name: {:<1}".format("-", enabled["name"]))
            print("{:>4} description: {:<1}".format("", enabled["description"]))
            print("{:>4} version: {:<1}".format("", enabled["version"]))
            print("{:>4} status: enabled".format(""))

        for disabled in disabled_addons:
            print("{:>4} name: {:<1}".format("-", disabled["name"]))
            print("{:>4} description: {:<1}".format("", disabled["description"]))
            print("{:>4} version: {:<1}".format("", disabled["version"]))
            print("{:>4} status: disabled".format(""))


def print_addon_status(enabled):
    if len(enabled) > 0:
        print("enabled")
    else:
        print ("disabled")


def get_status(available_addons, isReady):  
    enabled = []
    disabled = []
    if isReady:
        kube_output = kubectl_get("all")
        cluster_output = kubectl_get_clusterroles()
        kube_output = kube_output + cluster_output
        for addon in available_addons:
            found = False
            for row in kube_output.split('\n'):
                if is_enabled(addon["check_status"], row):
                    enabled.append(addon)
                    found = True
                    break
            if not found:
                disabled.append(addon)

    return enabled, disabled


if __name__ == '__main__':
    exit_if_no_permission()
    is_cluster_locked()

    # initiate the parser with a description
    parser = argparse.ArgumentParser(description='Microk8s cluster status check.', prog='microk8s.status')
    parser.add_argument("-o", "--output", help="print cluster and addon status, output can be in yaml or console",
                        default="console", choices={"console", "yaml"})
    parser.add_argument("-w", "--wait-ready", help="wait until the cluster is in ready state", nargs='?', const=True,
                        type=bool)
    parser.add_argument("-t", "--timeout",
                        help="specify a timeout in seconds when waiting for the cluster to be ready.", type=int,
                        default=0)
    parser.add_argument("-a", "--addon", help="check the status of an addon.", default="all")
    # read arguments from the command line
    args = parser.parse_args()

    wait_ready = args.wait_ready
    timeout = args.timeout

    if wait_ready:
        isReady = wait_for_ready(wait_ready, timeout)
    else:
        isReady = is_cluster_ready()

    available_addons = get_available_addons(get_current_arch())

    if args.addon != "all":
        available_addons = get_addon_by_name(available_addons, args.addon)

    enabled, disabled = get_status(available_addons, isReady)

    if args.addon != "all":
        print_addon_status(enabled)
    else:
        if args.output == "yaml":
            print_yaml(isReady, enabled, disabled)
        else:
            print_console(isReady, enabled, disabled)
