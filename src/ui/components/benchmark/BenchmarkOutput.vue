<script lang="ts" setup>
import type { Job, JobOutput } from "@/repository/modules/jobs";

const props = defineProps<{
    job: Job;
    visible: boolean;
    detailsRevision: number;
}>();

const jobId = computed(() => Number(props.job.jobId) || 0);
const { $api } = useNuxtApp();

const outputCache = useJobResourceCache<JobOutput | null>(
    async (id) => (await $api.jobs.getOutput(id)) ?? null
);
const output = computed(() => outputCache.entries[jobId.value]?.value);
const pending = computed(
    () => outputCache.pending[jobId.value]?.revision === props.detailsRevision
);

type OutputTabKey = "standardOutput" | "standardError";
type OutputTab = { title: string; value: OutputTabKey };

const defaultTabs: OutputTab[] = [
    { title: "StdOut & StdErr", value: "standardOutput" }
];

const outputTabs = computed<OutputTab[]>(() => {
    if (
        output.value &&
        output.value.standardOutput !== null &&
        output.value.standardError !== null
    ) {
        return [
            { title: "StdOut", value: "standardOutput" },
            { title: "StdErr", value: "standardError" }
        ];
    }

    return defaultTabs;
});

const refresh = async (id: number, revision: number) => {
    if (
        !props.visible ||
        !id ||
        id !== jobId.value ||
        revision !== props.detailsRevision
    )
        return;

    await outputCache.load(id, revision, true);
};

defineExpose({ refresh });

watch(
    [jobId, () => props.detailsRevision, () => props.visible],
    ([id, revision, shown]) => {
        if (!id || !shown) return;

        void outputCache.load(id, revision).catch((error) => {
            console.error(`Failed to load output for job ${id}:`, error);
        });
    },
    { immediate: true }
);

const outputTab: Ref<OutputTabKey> = ref("standardOutput");
</script>
<template>
    <v-tabs
        v-model="outputTab"
        style="margin-bottom: 20px"
        color="primary-light"
    >
        <v-tab
            v-for="v of [...outputTabs.map((x) => x.title), 'Job Script']"
            :key="v"
        >
            {{ v }}
        </v-tab>
    </v-tabs>
    <v-tabs-window v-model="outputTab">
        <template v-for="outputTab of outputTabs">
            <v-tabs-window-item>
                <div
                    class="text-medium-emphasis text-caption mb-3 ml-6"
                    v-if="props.job.jobInfo?.[outputTab.value]"
                >
                    <div class="d-flex">
                        <v-icon icon="$file" size="small"></v-icon>
                        File available at
                        <span class="font-italic ml-1">{{
                            props.job.jobInfo[outputTab.value]
                        }}</span>
                    </div>
                </div>
                <Editor
                    :model-value="
                        (() => {
                            const val = outputs?.[jobId]?.[outputTab.value];
                            return typeof val === 'string' && val.length
                                ? val
                                : '# No output available (yet)';
                        })()
                    "
                    readonly
                    height="750"
                    :filename="`${jobId}_${outputTab.value}.txt`"
                    :loading="pending"
                    language="plaintext"
                ></Editor>
            </v-tabs-window-item>
        </template>
        <v-tabs-window-item>
            <Editor
                :readonly="true"
                :modelValue="
                    props.job.userJobscriptFile ||
                    '# Job script not available (yet)'
                "
                :filename="`${jobId}_jobscript.sh`"
                height="750"
            ></Editor>
        </v-tabs-window-item>
    </v-tabs-window>
</template>
