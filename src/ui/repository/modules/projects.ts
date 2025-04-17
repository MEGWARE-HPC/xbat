import FetchFactory from "../factory";

export interface ProjectList {
    data: Project[];
}

export interface Project {
    _id: string;
    name: string;
    created: Date;
    members: string[];
}

class ProjectModule extends FetchFactory {
    private RESOURCE = "/projects";

    async get() {
        return this.call<ProjectList[]>(
            "GET",
            this.RESOURCE,
            undefined // body
        );
    }

    async delete(id: number) {
        return this.call<Project>(
            "DELETE",
            `${this.RESOURCE}/${id}`,
            undefined
        );
    }

    async patch(id: number, payload: Project) {
        return this.call<Project>("PATCH", `${this.RESOURCE}/${id}`, payload);
    }

    async post(payload: Project) {
        return this.call<Project>("POST", this.RESOURCE, payload);
    }
}

export default ProjectModule;
