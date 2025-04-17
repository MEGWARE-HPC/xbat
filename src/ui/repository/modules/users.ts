import FetchFactory from "../factory";
import type { User } from "../../store/auth";

export interface UserList {
    data: User[];
}

export interface UserPatch {
    blocked?: boolean;
    user_type?: string;
    password?: string;
}

export interface SwaggerRedirectURIs {
    redirect_uris: string;
}

class UserModule extends FetchFactory {
    private RESOURCE = "/users";

    async get() {
        return this.call<UserList[]>("GET", this.RESOURCE, undefined);
    }

    async patch(id: string, payload: UserPatch) {
        return this.call<User[]>("PATCH", `${this.RESOURCE}/${id}`, payload);
    }

    async getCurrentUser() {
        return this.call<User>("GET", "/currentuser", undefined);
    }

    async getSwaggerRedirectURIs() {
        return this.call<SwaggerRedirectURIs>(
            "GET",
            `${this.RESOURCE}/swagger`,
            undefined
        );
    }

    async patchSwaggerRedirectURIs(payload: { redirect_uris: string }) {
        return this.call<{}>("PATCH", `${this.RESOURCE}/swagger`, payload);
    }
}

export default UserModule;
