import FetchFactory from "../factory";

export interface ConfigurationFolderNode {
    id: string;
    name: string;
    type: "folder";
    parentId: string | null;
    misc?: {
        owner: string;
        created: string;
        edited: string;
    };
    children?: ConfigurationFolderNode[];
}

export type ConfigurationFolderResponse = {
    data: ConfigurationFolderNode[];
};

export type Folder = {
    folderName: string;
    parentFolderId: string | null;
    sharedProjects: string[];
};

export interface ConfigurationFolderFlat {
    _id: string;
    folder: Folder;
    misc: {
        owner: string;
        created: string;
        edited: string;
    };
}

export type ConfigurationFolderFlatResponse = {
    data: ConfigurationFolderFlat[];
};

export interface CreateConfigurationFolderRequest {
    folder: Folder;
}

export interface UpdateConfigurationFolderRequest {
    folder: Folder;
    misc: {
        owner: string;
        created: string;
        edited: string;
    };
}

export type CreateConfigurationFolderResponse = {
    _id: string;
};

class ConfigurationFolderModule extends FetchFactory {
    private RESOURCE = "/configuration_folders";

    async get() {
        return this.call<ConfigurationFolderResponse>(
            "GET",
            `${this.RESOURCE}`,
            undefined // body
        );
    }

    async post(payload: CreateConfigurationFolderRequest) {
        return this.call<CreateConfigurationFolderResponse>(
            "POST",
            `${this.RESOURCE}`,
            payload
        );
    }

    async put(id: string, payload: UpdateConfigurationFolderRequest) {
        return this.call<ConfigurationFolderFlat>(
            "PUT",
            `${this.RESOURCE}/${id}`,
            payload
        );
    }

    async delete(id: string) {
        await this.call<void>("DELETE", `${this.RESOURCE}/${id}`, undefined);
    }
}

export default ConfigurationFolderModule;
