import { deepClone } from "~/utils/misc";

export const useNodes = ({ jobs, currentJob }) => {
    const { $api } = useNuxtApp();

    const nodeHashes = computed(() => {
        let hashes = [];
        jobs.value.forEach((x) =>
            Object.values(x?.nodes || {}).forEach((y) => hashes.push(y.hash))
        );
        return Array.from(new Set(hashes));
    });

    const nodeInfoRaw = ref({});

    watch(
        nodeHashes,
        async (v) => {
            if (!v.length) return;
            nodeInfoRaw.value = await $api.nodes.get(v);
        },
        {
            immediate: true
        }
    );

    const nodeInfo = computed(() => {
        let infos = {};

        for (const job of jobs.value) {
            const jobId = job.jobId;
            if (!job.nodes) continue;
            for (let [node, values] of Object.entries(job.nodes)) {
                if (!infos[jobId]) infos[jobId] = {};
                infos[jobId][node] = deepClone(
                    nodeInfoRaw.value[values.hash] || {}
                );
            }
        }

        return infos;
    });

    const participatingNodes = computed(() =>
        Object.fromEntries(
            jobs.value.map((x) => [x.jobId, Object.keys(x?.nodes || [])])
        )
    );

    const nodeInfoSelectedNode = ref(null);

    watch(
        (participatingNodes, currentJob),
        () => {
            if (!currentJob.value) return;
            nodeInfoSelectedNode.value = participatingNodes.value[
                currentJob.value.jobId
            ]?.length
                ? participatingNodes.value[currentJob.value.jobId][0]
                : null;
        },
        {
            deep: true,
            immediate: true
        }
    );

    const topologies = computed(() => {
        let topologies = {};
        for (let [jobId, nodes] of Object.entries(nodeInfo.value)) {
            topologies[jobId] = {};
            for (let node of Object.keys(nodes)) {
                topologies[jobId][node] = nodes[node]?.cpu?.topology || "";
            }
        }
        return topologies;
    });

    const nodeBenchmarks = computed(() => {
        let benchmarksByNode = {};
        for (let jobId of Object.keys(nodeInfo.value)) {
            for (let [node, values] of Object.entries(nodeInfo.value[jobId])) {
                if (!(node in benchmarksByNode))
                    benchmarksByNode[node] = {
                        ...(values["benchmarks"] || {})
                    };
            }
        }
        return benchmarksByNode;
    });

    return {
        nodeInfo,
        participatingNodes,
        nodeInfoSelectedNode,
        topologies,
        nodeBenchmarks
    };
};
