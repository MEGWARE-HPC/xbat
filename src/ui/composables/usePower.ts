import { roundTo } from "~/utils/misc";
import type { GraphQuery } from "@/types/graph";

const powerMetrics = ["CPU Power", "FPGA Power", "GPU Power"];
const powerTraces = powerMetrics.map((x) => x.toLowerCase());

const usePower = () => {
    const { $graphStore } = useNuxtApp();

    const powerQueries: Ref<{ [key: string]: GraphQuery[] }> = ref({});

    const fetch = async (jobId: number, running: boolean = false) => {
        const queries = powerMetrics.map((m) =>
            $graphStore.createQuery(jobId, "energy", m, "job")
        ) as GraphQuery[];
        await Promise.all(queries.map((q) => $graphStore.fetchMeasurements(q)));
        powerQueries.value[jobId] = queries;
    };

    const powerConsumption = computed(() => {
        let usage: { [key: string]: { [key: string]: number } } = {};
        Object.keys(powerQueries.value).forEach((jobId) => {
            powerQueries.value[jobId].forEach((q: GraphQuery) => {
                const measurement = $graphStore.getMeasurements(q);
                if (!measurement || !measurement.traces) return;

                if (!(jobId in usage)) usage[jobId] = {};

                measurement.traces.forEach((m) => {
                    if (!powerTraces.includes(m.name)) return;
                    const time = m.interval / 3600;
                    const kWh =
                        ArrayUtils.sum(m.values.map((v) => v * time)) / 1000;

                    usage[jobId][m.metric.replace("Power", "Energy")] = roundTo(
                        kWh,
                        4
                    );
                });
            });
        });
        return usage;
    });

    return { powerConsumption, fetch };
};

export default usePower;
