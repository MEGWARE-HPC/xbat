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
        conflictStrategy: "overwrite" | "rename" | "skip";
        foldersCreated: number;
        foldersMerged: number;
        foldersRenamed: number;
        foldersOverwritten: number;
        configurationsCreated: number;
        configurationsSkipped: number;
        configurationsRenamed: number;
        configurationsOverwritten: number;
    };
};

class ConfigurationBackupModule extends FetchFactory {
    private EXPORT_RESOURCE = "/configuration_backups/backup";
    private RESTORE_RESOURCE = "/configuration_backups/restore";

    private getFilenameFromDisposition(disposition: string | null) {
        if (!disposition) return "configuration-backup.json";

        // RFC 5987: filename*=UTF-8''...
        const filenameStarMatch = disposition.match(
            /filename\*\s*=\s*UTF-8''([^;]+)/i
        );
        if (filenameStarMatch?.[1]) {
            try {
                return decodeURIComponent(filenameStarMatch[1]);
            } catch {
                return filenameStarMatch[1];
            }
        }

        // Basic: filename="..."
        const filenameMatch = disposition.match(/filename\s*=\s*"([^"]+)"/i);
        if (filenameMatch?.[1]) {
            return filenameMatch[1];
        }

        // Basic: filename=...
        const unquotedMatch = disposition.match(/filename\s*=\s*([^;]+)/i);
        if (unquotedMatch?.[1]) {
            return unquotedMatch[1].trim();
        }

        return "configuration-backup.json";
    }

    async download(scope: "self" | "owner" | "all" = "self", owner = "") {
        const query = new URLSearchParams();
        query.set("scope", scope);
        if (owner) query.set("owner", owner);

        const response = await this.callRaw<Blob>(
            "GET",
            `${this.EXPORT_RESOURCE}?${query.toString()}`,
            undefined,
            { responseType: "blob" }
        );

        const blob = response?._data;
        if (!blob) {
            throw new Error("Failed to export backup");
        }

        const disposition =
            response.headers.get("content-disposition") ||
            response.headers.get("Content-Disposition");

        const filename = this.getFilenameFromDisposition(disposition);

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
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
            conflictStrategy?: "overwrite" | "rename" | "skip";
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
