import { computed } from "vue";

const flopItems = [
    { value: "peakflops", title: "DP" },
    { value: "peakflops_sse", title: "DP SSE" },
    { value: "peakflops_avx", title: "DP AVX" },
    { value: "peakflops_avx_fma", title: "DP AVX FMA" },
    { value: "peakflops_avx512", title: "DP AVX512" },
    { value: "peakflops_avx512_fma", title: "DP AVX512 FMA" },
    { value: "peakflops_sp", title: "SP" },
    { value: "peakflops_sp_sse", title: "SP SSE" },
    { value: "peakflops_sp_avx", title: "SP AVX" },
    { value: "peakflops_sp_avx_fma", title: "SP AVX FMA" },
    { value: "peakflops_sp_avx512", title: "SP AVX512" },
    { value: "peakflops_sp_avx512_fma", title: "SP AVX512 FMA" }
];

const dramItems = [{ value: "bandwidth_mem", title: "Bandwidth DRAM" }];
const cacheItems = [
    { value: "bandwidth_l1", title: "Bandwidth L1" },
    { value: "bandwidth_l2", title: "Bandwidth L2" },
    { value: "bandwidth_l3", title: "Bandwidth L3" }
];
const memItems = [...dramItems, ...cacheItems];

export const useNodeBenchmarks = () => {
    const flopTitles = computed(() =>
        Object.fromEntries(flopItems.map((x) => [x.value, x.title]))
    );

    const memTitles = computed(() =>
        Object.fromEntries(memItems.map((x) => [x.value, x.title]))
    );

    const allTitels = computed(() =>
        Object.assign({}, flopTitles.value, memTitles.value)
    );

    return {
        flopItems,
        memItems,
        dramItems,
        cacheItems,
        flopTitles,
        memTitles,
        allTitels
    };
};

export default useNodeBenchmarks;
