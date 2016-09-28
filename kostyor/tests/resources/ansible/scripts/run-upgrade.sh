#!/usr/bin/env bash

export SCRIPTS_PATH="$(dirname "$(readlink -f "${0}")")"
export UPGRADE_PLAYBOOKS="${SCRIPTS_PATH}/upgrade-utilities/playbooks"

function main {
    pushd ${MAIN_PATH}/playbooks
        RUN_TASKS+=("${UPGRADE_PLAYBOOKS}/lbaas-version-check.yml")
        RUN_TASKS+=("setup-hosts.yml --limit '!galera_all'")
        # RUN_TASKS+=("haproxy-install.yml")

        # Run the tasks in order
        for item in ${!RUN_TASKS[@]}; do
          run_lock $item "${RUN_TASKS[$item]}"
        done
    popd
}

main