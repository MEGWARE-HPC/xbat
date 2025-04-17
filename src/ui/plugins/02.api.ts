import type { NitroFetchRequest, $Fetch } from "nitropack";

import BenchmarkModule from "~/repository/modules/benchmarks";
import ConfigurationModule from "~/repository/modules/configurations";
import SlurmModule from "~/repository/modules/slurm";
import ProjectModule from "~/repository/modules/projects";
import UserModule from "~/repository/modules/users";
import SettingsModule from "~/repository/modules/settings";
import MetricModule from "~/repository/modules/metrics";
import JobModule from "~/repository/modules/jobs";
import NodeModule from "~/repository/modules/nodes";
import MeasurementModule from "~/repository/modules/measurements";
import { useAuthStore } from "~/store/auth";

interface ApiInstance {
    benchmarks: BenchmarkModule;
    slurm: SlurmModule;
    configurations: ConfigurationModule;
    projects: ProjectModule;
    users: UserModule;
    settings: SettingsModule;
    metrics: MetricModule;
    jobs: JobModule;
    nodes: NodeModule;
    measurements: MeasurementModule;
}

export default defineNuxtPlugin((nuxtApp) => {
    const authStore = nuxtApp.$authStore as ReturnType<typeof useAuthStore>;

    // custom fetcher for authentication and error handling
    const apiFetcher: $Fetch<any, NitroFetchRequest> = $fetch.create({
        baseURL: authStore.backendApiBase,
        async onRequest({ request, options, error }) {
            await nuxtApp.runWithContext(() => {
                const { $authStore } = useNuxtApp();
                if ($authStore.isAuthenticated) {
                    const headers = (options.headers ||= {});
                    if (Array.isArray(headers)) {
                        headers.push([
                            "Authorization",
                            `Bearer ${$authStore.accessToken}`
                        ]);
                    } else if (headers instanceof Headers) {
                        headers.set(
                            "Authorization",
                            `Bearer ${$authStore.accessToken}`
                        );
                    } else {
                        headers.Authorization = `Bearer ${$authStore.accessToken}`;
                    }
                }
            });
        },
        async onResponseError({ response }) {
            if (response.status === 401) {
                await nuxtApp.runWithContext(() => {
                    const { $store, $authStore } = useNuxtApp();
                    $store.error = {
                        title: "Unauthorized",
                        status: 401,
                        detail: "Session expired"
                    };
                    $authStore.clearToken();
                    navigateTo("/login");
                });
            } else if (!response.ok) {
                await nuxtApp.runWithContext(() => {
                    const { $store } = useNuxtApp();
                    $store.error = response._data;
                    console.error(response._data);
                });
            }
        }
    });

    // An object containing all repositories we need to expose
    const modules: ApiInstance = {
        benchmarks: new BenchmarkModule(apiFetcher),
        slurm: new SlurmModule(apiFetcher),
        configurations: new ConfigurationModule(apiFetcher),
        projects: new ProjectModule(apiFetcher),
        users: new UserModule(apiFetcher),
        settings: new SettingsModule(apiFetcher),
        metrics: new MetricModule(apiFetcher),
        jobs: new JobModule(apiFetcher),
        nodes: new NodeModule(apiFetcher),
        measurements: new MeasurementModule(apiFetcher)
    };

    return {
        provide: {
            api: modules
        }
    };
});
