import FetchFactory from "../factory";

export interface Whitelist {
    enabled: boolean;
    users: string[];
}

class SettingsModule extends FetchFactory {
    private RESOURCE = "/settings";

    async get() {
        return this.call<Whitelist>(
            "GET",
            `${this.RESOURCE}`,
            undefined // body
        );
    }

    async patch(payload: Whitelist) {
        return this.call<Whitelist>("PATCH", `${this.RESOURCE}`, payload);
    }
}

export default SettingsModule;
