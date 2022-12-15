#!/bin/bash

BASE_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

core_ref=${1:-dev}
venv_path="/home/neon/venv"
backup_path="/home/neon/.cache/neon/venv_backup"
pip_spec="git+https://github.com/neongeckocom/neoncore@${core_ref}#egg=neon_core[core_modules,skills_required,skills_essential,skills_default,skills_extended,pi]"
timestamp=$(date +"%Y-%m-%d_%H-%M")
update_log_path="/home/neon/.local/state/neon/${timestamp}_update"

backup_venv() {
  echo "Backing up venv"
  cp -r "${venv_path}" "${backup_path}"
  chown -R neon:neon /home/neon
  echo "venv backup complete"
}

remove_backup() {
  echo "Removing venv backup"
  rm -rf "${backup_path}"
}

restore_backup() {
  if [ -d "${backup_path}" ]; then
    rm -rf "${venv_path}"
    mv "${backup_path}" "${venv_path}"
    chown -R neon:neon /home/neon
  else
    echo "No Backup to Restore!"
  fi
}

do_python_update() {
  . "${venv_path}/bin/activate"
  mkdir -p "${update_log_path}"
  pip install --upgrade pip
  pip install --report --upgrade "${pip_spec}" > "${update_log_path}/pip_report.json"
  deactivate
  chown -R neon:neon /home/neon
}

validate_module_load() {
  . "${venv_path}/bin/activate"
  status=$(python3 "${BASE_DIR}/check_neon_modules.py")
  deactivate
  if [ "${status}" == "0" ]; then
    echo "Update success"
    return 0
  else
    echo "Update failed!"
    restore_backup
    return 1
  fi
}

remove_backup
systemctl stop neon
backup_venv || exit 2
do_python_update || echo "Update Failed"
validate_module_load
systemctl start neon
