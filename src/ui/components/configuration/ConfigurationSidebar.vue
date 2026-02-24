<template>
    <v-navigation-drawer permanent class="sidebar" width="300">
        <template #prepend>
            <div class="header">CONFIGURATIONS</div>
        </template>

        <div class="list">
            <v-list
                density="comfortable"
                :selected="[selectedId]"
                v-model:opened="opened"
            >
                <!-- My / All Configurations -->
                <v-list-group value="my" class="sb-section">
                    <template #activator="{ props: groupProps, isOpen }">
                        <v-list-item
                            v-bind="groupProps"
                            class="sb-row sb-section-row"
                            density="comfortable"
                            :style="sectionRowStyle(0)"
                        >
                            <template #prepend>
                                <v-icon
                                    class="sb-chevron"
                                    size="small"
                                    :icon="
                                        isOpen
                                            ? '$chevronDown'
                                            : '$chevronRight'
                                    "
                                />
                                <v-icon
                                    class="sb-folder-icon"
                                    :icon="isOpen ? '$folderOpen' : '$folder'"
                                />
                            </template>

                            <v-list-item-title class="sb-title">
                                {{ myConfigTitle }}
                            </v-list-item-title>
                        </v-list-item>
                    </template>

                    <div
                        class="sb-children sb-section-children"
                        :style="sectionChildrenStyle(0)"
                    >
                        <template v-if="showMyHome">
                            <SidebarConfigItem
                                v-for="c in myHomeConfigs"
                                :key="c.id"
                                :id="c.id"
                                :doc="c.doc"
                                :depth="1"
                                :selected-id="selectedId"
                                :user="user"
                                :user-level="userLevel"
                                :UserLevelEnum="UserLevelEnum"
                                @select="$emit('select', $event)"
                                @duplicate="$emit('duplicate', $event)"
                                @delete="$emit('delete', $event)"
                            />
                        </template>

                        <SidebarFolderNode
                            v-for="n in myFolderRoots"
                            :key="n.id"
                            :node="n"
                            :configs-by-folder="myConfigsByFolder"
                            :selected-id="selectedId"
                            :user="user"
                            :user-level="userLevel"
                            :UserLevelEnum="UserLevelEnum"
                            :depth="0"
                            :max-depth="myMaxDepth"
                            @select="$emit('select', $event)"
                            @select-folder="$emit('select-folder', $event)"
                            @duplicate="$emit('duplicate', $event)"
                            @delete="$emit('delete', $event)"
                        />
                    </div>
                </v-list-group>

                <!-- Shared -->
                <v-list-group
                    v-if="showShared"
                    value="shared"
                    class="sb-section"
                >
                    <template #activator="{ props: groupProps, isOpen }">
                        <v-list-item
                            v-bind="groupProps"
                            class="sb-row sb-section-row"
                            density="comfortable"
                            :style="sectionRowStyle(0)"
                        >
                            <template #prepend>
                                <v-icon
                                    class="sb-chevron"
                                    size="small"
                                    :icon="
                                        isOpen
                                            ? '$chevronDown'
                                            : '$chevronRight'
                                    "
                                />
                                <v-icon class="sb-folder-icon" icon="$share" />
                            </template>

                            <v-list-item-title class="sb-title">
                                Shared Configurations
                            </v-list-item-title>
                        </v-list-item>
                    </template>

                    <div
                        class="sb-children sb-section-children"
                        :style="sectionChildrenStyle(0)"
                    >
                        <template v-if="sharedGroups.length">
                            <v-list-group
                                v-for="g in sharedGroups"
                                :key="g.key"
                                :value="g.key"
                                class="sb-project"
                            >
                                <template
                                    #activator="{ props: groupProps2, isOpen }"
                                >
                                    <v-list-item
                                        v-bind="groupProps2"
                                        class="sb-row sb-tight"
                                        density="comfortable"
                                        :style="sectionRowStyle(1)"
                                    >
                                        <template #prepend>
                                            <v-icon
                                                class="sb-chevron"
                                                size="small"
                                                :icon="
                                                    isOpen
                                                        ? '$chevronDown'
                                                        : '$chevronRight'
                                                "
                                            />
                                            <v-icon
                                                class="sb-folder-icon"
                                                icon="$group"
                                            />
                                        </template>

                                        <v-list-item-title class="sb-title">
                                            {{ g.name }}
                                        </v-list-item-title>
                                    </v-list-item>
                                </template>

                                <div
                                    class="sb-children sb-tight"
                                    :style="sectionChildrenStyle(1)"
                                >
                                    <SidebarConfigItem
                                        v-for="c in g.items"
                                        :key="c.id"
                                        :id="c.id"
                                        :doc="c.doc"
                                        :depth="2"
                                        :selected-id="selectedId"
                                        :user="user"
                                        :user-level="userLevel"
                                        :UserLevelEnum="UserLevelEnum"
                                        @select="$emit('select', $event)"
                                        @duplicate="$emit('duplicate', $event)"
                                        @delete="$emit('delete', $event)"
                                    />
                                </div>
                            </v-list-group>
                        </template>

                        <v-list-item
                            v-else
                            class="text-medium-emphasis sb-row sb-tight"
                            title="No shared configurations"
                        />
                    </div>
                </v-list-group>
            </v-list>
        </div>

        <v-list-item>
            <div
                v-if="userLevel > UserLevelEnum.guest"
                class="d-flex justify-center"
            >
                <v-btn
                    title="Add Configuration"
                    elevation="0"
                    variant="tonal"
                    prepend-icon="$newFile"
                    @click="$emit('create')"
                >
                    New configuration
                </v-btn>
            </div>
        </v-list-item>
    </v-navigation-drawer>
</template>

<script setup>
import { computed, ref, watch, onMounted } from "vue";

import SidebarFolderNode from "./sidebar/SidebarFolderNode.vue";
import SidebarConfigItem from "./sidebar/SidebarConfigItem.vue";

const props = defineProps({
    configurationCache: { type: Object, required: true },
    selectedId: { type: String, default: null },
    user: { type: Object, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true }
});

defineEmits(["select", "select-folder", "create", "duplicate", "delete"]);

const { $api } = useNuxtApp();

const { data: folderTree } = await useAsyncData(
    `configuration-folders-tree-${props.user.user_name}`,
    async () => (await $api.configurationFolders.get())?.data || []
);

const myMaxDepth = computed(() => (isManager.value ? 3 : 2));

const allConfigs = computed(() =>
    Object.entries(props.configurationCache || {}).map(([id, doc]) => ({
        id,
        doc
    }))
);

const isManager = computed(
    () => props.userLevel >= props.UserLevelEnum.manager
);

const showShared = computed(() => !isManager.value);

const myConfigTitle = computed(() =>
    isManager.value ? "All Folders" : "My Configurations"
);

const myHomeNode = computed(() => {
    const roots = folderTree.value || [];
    return roots.find((n) => n?.name === props.user.user_name) || null;
});

const myFolderRoots = computed(() => {
    const roots = folderTree.value || [];
    if (isManager.value) return roots;

    const home = myHomeNode.value;
    if (!home) return roots; // fallback
    return home.children || [];
});

const myConfigsByFolder = computed(() => {
    const m = new Map();

    for (const { id, doc } of allConfigs.value) {
        if (!isManager.value && doc?.misc?.owner !== props.user.user_name) {
            continue;
        }

        const folderId = doc?.configuration?.folderId
            ? String(doc.configuration.folderId)
            : "root";

        if (!m.has(folderId)) m.set(folderId, []);
        m.get(folderId).push({ id, doc });
    }

    for (const [k, arr] of m.entries()) {
        arr.sort((a, b) =>
            (a.doc?.configuration?.configurationName || a.id).localeCompare(
                b.doc?.configuration?.configurationName || b.id
            )
        );
        m.set(k, arr);
    }

    return m;
});

const showMyHome = computed(() => !isManager.value && !!myHomeNode.value);

const myHomeConfigs = computed(() => {
    if (!showMyHome.value) return [];
    const homeId = myHomeNode.value.id;
    return myConfigsByFolder.value.get(homeId) || [];
});

const sharedConfigsFlat = computed(() =>
    allConfigs.value.filter(
        ({ doc }) => doc?.misc?.owner !== props.user.user_name
    )
);

const projectNameById = computed(() => {
    const m = new Map();
    for (const p of props.user?.projects || []) {
        m.set(p._id, p.name);
    }
    return m;
});

const sharedBucket = (doc) => {
    const ids = doc?.configuration?.sharedProjects || [];
    for (const pid of ids) if (projectNameById.value.has(pid)) return pid;
    return "unknown";
};

const sharedGroups = computed(() => {
    if (isManager.value) return [];

    const buckets = new Map();

    for (const { id, doc } of sharedConfigsFlat.value) {
        const pid = sharedBucket(doc);
        const name =
            pid === "unknown"
                ? "Unknown / Other"
                : projectNameById.value.get(pid);

        const key = `shared-${pid}`;
        if (!buckets.has(key)) buckets.set(key, { key, name, items: [] });
        buckets.get(key).items.push({ id, doc });
    }

    for (const g of buckets.values()) {
        g.items.sort((a, b) =>
            (a.doc?.configuration?.configurationName || a.id).localeCompare(
                b.doc?.configuration?.configurationName || b.id
            )
        );
    }

    return Array.from(buckets.values()).sort((a, b) =>
        a.name.localeCompare(b.name)
    );
});

const opened = ref([]);

const isInit = ref(false);

const openHome = ref(false);

const ensureOpened = (keys) => {
    const set = new Set(opened.value);
    for (const k of keys) set.add(k);
    opened.value = Array.from(set);
};

const initOpened = () => {
    const base = ["my"];
    if (showShared.value) base.push("shared");
    ensureOpened(base);
    isInit.value = true;
};

onMounted(() => {
    initOpened();
});

watch(showShared, (v) => {
    if (!isInit.value) return;

    if (!v) {
        opened.value = opened.value.filter((x) => x !== "shared");
        return;
    }

    // if shared reopened：
    // ensureOpened(["shared"]);
});

watch(
    () => [isManager.value, myHomeNode.value?.id],
    ([mgr, homeId]) => {
        if (!mgr || !homeId) return;
        if (openHome.value) return;

        const key = `folder-${homeId}`;
        ensureOpened([key]);

        openHome.value = true;
    },
    { immediate: true }
);

const INDENT = 12;
const GUIDE_GAP = 6;

const sectionRowStyle = (depth) => ({
    "--sb-indent": `${depth * INDENT}px`
});

const sectionChildrenStyle = (depth) => ({
    "--sb-indent": `${(depth + 1) * INDENT}px`,
    "--sb-guide-gap": `${GUIDE_GAP}px`
});
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.sidebar {
    .header {
        margin-top: 25px;
        text-align: center;
        color: $font-light;
    }

    .list {
        overflow-y: auto;
        max-height: 80vh;
    }
}

:deep(.v-list-group__items) {
    padding-inline-start: 0 !important;
}

:deep(.v-list-group__header .v-list-item__append) {
    display: none !important;
}

:deep(.sb-row) {
    padding-inline-start: var(--sb-indent) !important;
    min-height: 30px;
}

:deep(.sb-title) {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

:deep(.sb-tight .v-list-item__spacer) {
    width: 4px !important;
    flex: 0 0 4px !important;
}

:deep(.sb-tight .v-list-item__prepend) {
    margin-inline-end: 0 !important;
}

:deep(.sb-tight .sb-folder-icon),
:deep(.sb-tight .sb-icon) {
    margin-inline-end: 8px !important;
}

:deep(.sb-section-row .sb-folder-icon) {
    margin-inline-end: 12px !important;
}

:deep(.sb-chevron) {
    margin-inline-end: 2px;
    color: $font-disabled !important;
    opacity: 1 !important;
}

:deep(.sb-folder-icon) {
    margin-inline-end: 6px;
    color: $primary-light !important;
    opacity: 0.8 !important;
    filter: brightness(1.1);
}

:deep(.sb-folder-icon.is-open) {
    color: $primary !important;
    opacity: 0.8 !important;
}

:deep(.sb-children) {
    position: relative;
    margin-inline-start: var(--sb-indent);
    padding-inline-start: calc(var(--sb-guide-gap) + 6px);
}

:deep(.sb-children::before) {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: calc(var(--sb-guide-gap) / 2);
    width: 1px;
    background: $font-disabled;
    opacity: 0.45;
}

:deep(.sb-section-children) {
    padding-inline-start: calc(var(--sb-guide-gap) + 4px);
}
</style>
