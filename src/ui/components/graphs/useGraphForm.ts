import type { Metrics } from "~/types/graph";
import { groupLabels } from "~/components/graphs/useGraphBase";

const levels = ["thread", "core", "numa", "socket", "device", "node", "job"];

export const useGraphForm = (metrics: Ref<Metrics>) => {
    const form = reactive<Record<string, string | null>>({
        node: null,
        group: null,
        metric: null,
        level: null
    });

    const metricGroups = computed(() => {
        const groups = Object.keys(metrics.value || {});

        return groups.map((x) =>
            Object.assign({ title: groupLabels[x] || x, value: x })
        );
    });

    const metricItems = computed(() => {
        if (!metrics.value || !form.group || !(form.group in metrics.value))
            return [];

        return Object.keys(metrics.value[form.group]).map((x) => {
            const metricInfo = metrics.value[form.group][x];
            return {
                title: x,
                value: x,
                description: metricInfo.description,
                url: metricInfo.uri
                    ? `https://xbat.dev/docs/user/metrics/${metricInfo.uri}`
                    : null
            };
        });
    });

    const metricLevels = computed(() => {
        if (!form.group || !form.metric) return [];

        const levelMin = metrics.value?.[form.group]?.[form.metric]?.level_min;
        if (!levelMin) return [];
        let availableLevels = levels.slice(levels.indexOf(levelMin));
        // "device" is always levelMin for all metrics gathered on device basis
        // all other metrics do not include "device"
        if (levelMin != "device")
            availableLevels = availableLevels.filter((x) => x != "device");
        return availableLevels;
    });

    watch(
        () => form.group,
        (v) => {
            if (!v || !metrics.value[v]) return;
            if (form.metric === null || !metrics.value[v]?.[form.metric])
                form.metric = null;
            if (Object.keys(metrics.value[v]).length == 1)
                form.metric = Object.keys(metrics.value[v])[0];
        },
        { immediate: true }
    );

    watch(
        () => form.metric,
        (v) => {
            nextTick(() => {
                if (
                    v &&
                    (form.level === null ||
                        !metricLevels.value.includes(form.level))
                )
                    form.level = "job";
            });
        }
    );

    return {
        form,
        metricGroups,
        metricItems,
        metricLevels
    };
};
