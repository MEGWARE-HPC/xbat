<template>
    <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
        <div class="fb">
            <div v-if="!folder" class="fb-empty text-medium-emphasis">
                Select a folder to browse, or select a configuration to edit.
            </div>

            <div v-else class="fb-wrap">
                <!-- Header -->
                <div class="fb-header">
                    <div class="fb-title">
                        <v-icon
                            class="mr-2"
                            :class="headerIconClass"
                            :icon="headerIcon"
                        />
                        <span class="fb-title-text">{{ folder.name }}</span>
                    </div>
                </div>

                <!-- Actions -->
                <div class="fb-actions" v-if="canCreate">
                    <v-btn
                        color="primary-light"
                        title="Add Configuration"
                        prepend-icon="$newFile"
                        @click="$emit('create-config')"
                    >
                        New
                    </v-btn>
                </div>

                <!-- Table header -->
                <div class="fb-row fb-row--head" :style="rowGridStyle">
                    <div class="fb-col fb-col--name">Name</div>
                    <div v-if="showOwner" class="fb-col fb-col--owner">
                        Owner
                    </div>
                    <div class="fb-col fb-col--created">Created</div>
                    <div class="fb-col fb-col--edited">Modified</div>
                </div>

                <v-list class="fb-list" density="compact">
                    <!-- .. (go up) -->
                    <v-list-item
                        v-if="canGoUp"
                        class="fb-rowitem"
                        @click="$emit('open-folder', parentId)"
                    >
                        <template #prepend>
                            <v-icon
                                icon="$arrowLeftTop"
                                class="fb-ico fb-ico--nav"
                            />
                        </template>

                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--name fb-name">
                                    ..
                                </div>
                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
                                    —
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    —
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    —
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- folders -->
                    <v-list-item
                        v-for="child in folders"
                        :key="'f-' + child.id"
                        class="fb-rowitem"
                        @click="$emit('open-folder', child.id)"
                    >
                        <template #prepend>
                            <v-icon
                                :icon="childFolderIcon"
                                class="fb-ico"
                                :class="childFolderIconClass"
                            />
                        </template>

                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--name fb-name">
                                    {{ child.name }}
                                </div>
                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
                                    —
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    {{ formatDate(child?.misc?.created) }}
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    {{ formatDate(child?.misc?.edited) }}
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- configs -->
                    <v-list-item
                        v-for="c in configs"
                        :key="'c-' + c.id"
                        class="fb-rowitem"
                        @click="$emit('open-config', c.id)"
                    >
                        <template #prepend>
                            <v-icon
                                class="fb-ico fb-ico--config"
                                :icon="
                                    c.doc?.configuration?.sharedProjects?.length
                                        ? '$share'
                                        : '$textBox'
                                "
                                color="primary-light"
                            />
                        </template>

                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--name fb-name">
                                    {{
                                        c.doc?.configuration
                                            ?.configurationName || c.id
                                    }}
                                </div>
                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
                                    {{ c.doc?.misc?.owner || "—" }}
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    {{ formatDate(c.doc?.misc?.created) }}
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    {{ formatDate(c.doc?.misc?.edited) }}
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- empty state inside a folder -->
                    <v-list-item
                        v-if="
                            !canGoUp &&
                            folders.length === 0 &&
                            configs.length === 0
                        "
                        class="text-medium-emphasis"
                        title="This folder is empty"
                    />
                </v-list>
            </div>
        </div>
    </v-main>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    folder: { type: Object, default: null }, // expects { id, name, children?, __parentId? }
    configs: { type: Array, default: () => [] },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true }
});

defineEmits(["open-folder", "open-config", "create-config"]);

const canCreate = computed(
    () => props.userLevel > (props.UserLevelEnum?.guest ?? 0)
);

const folderId = computed(() => String(props.folder?.id ?? ""));

const isSharedView = computed(() => folderId.value.startsWith("__shared__"));
const isSharedRoot = computed(() => folderId.value === "__shared__");
const isSharedProject = computed(() =>
    folderId.value.startsWith("__shared__:")
);

const showOwner = computed(() => isSharedView.value);

const parentId = computed(() => props.folder?.__parentId ?? null);

const canGoUp = computed(() => !!props.folder && !!parentId.value);

const folders = computed(() => (props.folder?.children || []).slice());

const rowGridStyle = computed(() => ({
    "--fb-cols": showOwner.value ? "1fr 160px 160px 160px" : "1fr 160px 160px"
}));

const headerIcon = computed(() => {
    if (isSharedRoot.value) return "$folderNetwork";
    if (isSharedProject.value) return "$group";
    return "$folderOpen";
});

const headerIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-root";
    if (isSharedProject.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const childFolderIcon = computed(() => {
    if (isSharedRoot.value) return "$group";
    return "$folder";
});

const childFolderIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const formatDate = (v) => {
    if (!v) return "—";

    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return "—";
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    }).format(d);
};
</script>

<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.fb {
    padding: 16px;
}

.fb-empty {
    padding: 24px;
}

.fb-wrap {
    max-width: 100%;
}

.fb-header {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.fb-title {
    display: flex;
    align-items: center;
    font-size: 1.05rem;
    font-weight: 600;
}

.fb-title-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 12px 0 8px;
}

.fb-list {
    border-radius: 8px;
    overflow: hidden;
}

.fb-row {
    display: grid;
    grid-template-columns: var(--fb-cols, 1fr 160px 160px);
    align-items: center;
    gap: 10px;
    width: 100%;
}

.fb-row--head {
    padding: 8px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    opacity: 0.75;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.fb-col {
    min-width: 0;
}

.fb-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-owner {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    opacity: 0.75;
    font-size: 0.82rem;
}

.fb-date {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: right;
    opacity: 0.75;
    font-size: 0.82rem;
}

.fb-rowitem :deep(.v-list-item-title) {
    width: 100%;
}

.fb-rowitem :deep(.v-list-item__content) {
    overflow: hidden;
}

.fb-ico {
    margin-inline-end: 8px;
}

.fb-ico--folder {
    color: $primary-light;
    opacity: 0.8;
    filter: brightness(1.1);
}

.fb-ico--shared-root {
    color: $primary-light;
    opacity: 0.8;
}

.fb-ico--shared-project {
    color: $primary-light;
    opacity: 0.8;
}

.fb-ico--config {
    margin-inline-end: 8px;
}

.fb-ico--nav {
    color: $primary-light;
    opacity: 0.7;
}
</style>
