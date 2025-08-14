import { $fetch, FetchError } from "ofetch";

export type User = {
    user_name: string;
    user_type: string;
    uidnumber?: null | string;
    gidnumber?: null | string;
    homedirectory?: string;
    blocked?: boolean;
    projects?: Project[];
    last_login: string;
};

export type Project = {
    name: string;
    _id: string;
};

type Token = {
    access_token: string;
    expires_in: number;
    token_type: string;
};

enum UserLevelEnum {
    guest = 0,
    user = 1,
    demo = 2,
    manager = 3,
    admin = 4
}

export const useAuthStore = defineStore("auth", () => {
    const runtimeConfig = useRuntimeConfig();
    const requestUrl = useRequestURL();

    const clientIdPrefix = runtimeConfig.public.clientIdPrefix;
    const apiPrefix = runtimeConfig.public.apiPrefix;

    const user = ref<User | null>(null);
    let backendUrl: string =
        runtimeConfig.app.buildId === "dev"
            ? runtimeConfig.public.devRestUrl
            : requestUrl.origin;

    if (process.server && runtimeConfig.app.buildId !== "dev")
        backendUrl = runtimeConfig.composeBackendUrl;

    let frontendUrl: string = `https://${requestUrl.host}`;
    if (process.server && runtimeConfig.app.buildId !== "dev")
        frontendUrl = runtimeConfig.composeFrontendUrl;

    const token = useCookie<Token | null>("xbat_api", {
        default: () => null,
        secure: true
    });

    const accessToken = computed(() => token.value?.access_token || null);
    const isAuthenticated = computed(() => !!token.value);
    const userName = computed(() => user.value?.user_name || "");
    const userLevel = computed(() =>
        user.value
            ? UserLevelEnum[user.value.user_type as keyof typeof UserLevelEnum]
            : UserLevelEnum.guest
    );

    const backendApiBase = computed(() => `${backendUrl}${apiPrefix}`);
    const router = useRouter();

    const _throw = (error: FetchError): void => {
        console.error(error);
        const { $store } = useNuxtApp();
        $store.error = (error as FetchError).data;
    };

    const tokenExpired = ref(false);

    const clearToken = (expired = false): void => {
        token.value = null;
        tokenExpired.value = expired;
    };

    const resetTokenState = (): void => {
        tokenExpired.value = false;
    };

    const clearUser = (): void => {
        user.value = null;
        router.push("/login");
    };

    const loadUser = async () => {
        try {
            const data = await $fetch<User>(
                backendApiBase.value + "/current_user",
                {
                    headers: {
                        Authorization: `Bearer ${token.value?.access_token}`,
                        accept: "application/json",
                        credentials: "cross-origin"
                    }
                }
            );

            user.value = data;
        } catch (error) {
            console.error(error);
            clearToken(true);
            clearUser();
        }
    };

    const revoke = async () => {
        if (!user.value || !token.value) return;

        try {
            await $fetch<{}>(`${backendUrl}/oauth/revoke`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    client_id: `${clientIdPrefix}${user.value.user_name}`,
                    token: token.value.access_token,
                    token_type_hint: "access_token"
                }).toString()
            });
        } catch (e: any) {
            _throw(e);
        } finally {
            clearToken();
            clearUser();
        }
    };

    const logout = async () => {
        await revoke();
    };

    const login = async ({
        username,
        password,
        remember = false
    }: {
        username: string;
        password: string;
        remember?: boolean;
    }) => {
        if (isAuthenticated.value) return;

        const urlParams = {
            grant_type: "password",
            client_id: `${clientIdPrefix}${username}`,
            username,
            password
        };
        try {
            const data = await $fetch<Token>(`${backendUrl}/oauth/token`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    Authorization: `Basic ${btoa(`${username}:${password}`)}`
                },
                body: new URLSearchParams(urlParams).toString()
            });
            token.value = data;
        } catch (e: any) {
            _throw(e);
        }
    };

    return {
        user,
        token,
        login,
        isAuthenticated,
        logout,
        userName,
        userLevel,
        UserLevelEnum,
        accessToken,
        backendApiBase,
        loadUser,
        backendUrl,
        frontendUrl,
        tokenExpired,
        resetTokenState,
        clearToken,
        requestUrl
    };
});

export default useAuthStore;
