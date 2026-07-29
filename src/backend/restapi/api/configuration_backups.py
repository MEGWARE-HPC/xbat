import json
from flask import Response

from shared.date import get_current_filename_datetime_str
from backend.restapi.utils import configuration_backup
from backend.restapi.utils.folders import get_owned_folders
from backend.restapi.utils.configurations import get_owned_configs


def export_backup():
    """
    Exports configurations + folders as a JSON backup file.

    Query params:
    - scope=self|owner|all
    - owner=<username>   (required if scope=owner)
    """
    actor, scope_info = configuration_backup.get_export_scope()

    folders = get_owned_folders(scope_info["owners"])
    configurations = get_owned_configs(scope_info["owners"])

    payload = configuration_backup.build_backup_payload(
        actor=actor,
        scope_info=scope_info,
        folders=folders,
        configurations=configurations,
    )

    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    scope_name = scope_info["mode"]
    owner_name = scope_info["owner"] or "all"
    timestamp = get_current_filename_datetime_str()

    filename = (
        f"configuration-backup-{scope_name}-{owner_name}-{timestamp}.json")

    return Response(
        body,
        mimetype="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


def restore_backup():
    """
    Restore a JSON backup.

    multipart/form-data:
      - file: uploaded backup json
      - scope: self|owner|all
      - owner: required for scope=owner
      - conflictStrategy: overwrite|rename|skip
    """
    actor, restore_info = configuration_backup.get_restore_scope()
    payload = configuration_backup.read_backup_payload()
    configuration_backup.validate_unique_export_ids(payload)

    summary = configuration_backup.build_restore_summary(
        payload,
        actor,
        restore_info,
    )

    folder_mapping = configuration_backup.restore_folders(
        payload, restore_info, summary)
    configuration_backup.restore_configs(payload, restore_info, folder_mapping,
                                         summary)

    return {"data": summary}, 200
