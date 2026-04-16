import FetchFactory from "../factory";

export type RestoreBackupResponse = {
    data: {
        schemaVersion: string;
        restoredBy: {
            userName: string;
            userType: string;
        };
        restoreMode: "self" | "owner" | "all";
        targetOwner: string | null;
        preserveOriginalOwner: boolean;
        conflictStrategy: "rename" | "skip";
        foldersCreated: number;
        foldersMerged: number;
        foldersRenamed: number;
        configurationsCreated: number;
        configurationsSkipped: number;
        configurationsRenamed: number;
    };
};

class ConfigurationBackupModule extends FetchFactory {
    private EXPORT_RESOURCE = "/configuration_backups/export";
    private RESTORE_RESOURCE = "/configuration_backups/restore";

    async download(scope: "self" | "owner" | "all" = "self", owner = "") {
        const query = new URLSearchParams();
        query.set("scope", scope);
        if (owner) query.set("owner", owner);

        const blob = await this.call<Blob>(
            "GET",
            `${this.EXPORT_RESOURCE}?${query.toString()}`,
            undefined,
            { responseType: "blob" }
        );

        if (!blob) {
            throw new Error("Failed to export backup");
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "configuration-backup.json";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    }

    async restore(
        file: File,
        options: {
            scope?: "self" | "owner" | "all";
            owner?: string;
            conflictStrategy?: "rename" | "skip";
        } = {}
    ) {
        const form = new FormData();
        form.append("file", file);

        const query = new URLSearchParams();
        query.set("scope", options.scope || "self");
        if (options.owner) query.set("owner", options.owner);
        if (options.conflictStrategy) {
            query.set("conflictStrategy", options.conflictStrategy);
        }

        const result = await this.call<RestoreBackupResponse>(
            "POST",
            `${this.RESTORE_RESOURCE}?${query.toString()}`,
            form
        );

        if (!result) {
            throw new Error("Failed to restore backup");
        }

        return result;
    }
}

export default ConfigurationBackupModule;
