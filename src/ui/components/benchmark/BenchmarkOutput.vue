<script lang="ts" setup>
import type { Job, JobOutput } from "@/repository/modules/jobs";

const props = defineProps<{
    job: Job; // currently selected job
    visible: boolean;
}>();

const jobId = computed(() => props.job.jobId);

const defaultTabs: OutputTab[] = [
    { title: "StdOut & StdErr", value: "standardOutput" }
];

type OutputTabKey = "standardOutput" | "standardError";
type OutputTab = { title: string; value: OutputTabKey };

// determine tabs based on whether stdout and stderr are combined
const outputTabs = computed<OutputTab[]>(() => {
    if (!jobId.value || !outputs.value[jobId.value]) return defaultTabs;

    const output = outputs.value[jobId.value];

    if (output?.standardOutput !== null)
        if (output?.standardError !== null)
            return [
                { title: "StdOut", value: "standardOutput" },
                { title: "StdErr", value: "standardError" }
            ];

    return defaultTabs;
});

const outputs: Ref<Record<string, JobOutput | null>> = ref({});
const pending = ref(false);

const { $api } = useNuxtApp();
const refresh = async () => {
    if (!jobId.value) return;

    pending.value = true;
    outputs.value[jobId.value] =
        (await $api.jobs.getOutput(jobId.value)) || null;
    pending.value = false;
};

watch(
    [jobId, () => props.visible],
    async ([id, shown]) => {
        if (!shown || id in outputs.value) return;
        await refresh();
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
