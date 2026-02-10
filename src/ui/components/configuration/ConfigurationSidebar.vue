<template>
    <v-navigation-drawer permanent location="right" class="sidebar" width="300">
        <template #prepend>
            <div class="header">CONFIGURATIONS</div>
        </template>

        <div class="list">
            <v-list density="compact" :selected="[selectedId]">
                <!-- My Configurations -->
                <v-list-group value="my" :open="true">
                    <template #activator="{ props: groupProps }">
                        <v-list-item
                            v-bind="groupProps"
                            title="My Configurations"
                            prepend-icon="$folder"
                        />
                    </template>

                    <template v-if="showMyHomeInline">
                        <SidebarConfigItem
                            v-for="c in myHomeConfigs"
                            :key="c.id"
                            :id="c.id"
                            :doc="c.doc"
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
                        @duplicate="$emit('duplicate', $event)"
                        @delete="$emit('delete', $event)"
                    />
                </v-list-group>

                <!-- Shared Configurations -->
                <v-list-group value="shared" :open="true">
                    <template #activator="{ props: groupProps }">
                        <v-list-item
                            v-bind="groupProps"
                            title="Shared Configurations"
                            prepend-icon="$share"
                        />
                    </template>

                    <template v-if="sharedGroups.length">
                        <v-list-group
                            v-for="g in sharedGroups"
                            :key="g.key"
                            :value="g.key"
                        >
                            <template #activator="{ props: groupProps2 }">
                                <v-list-item
                                    v-bind="groupProps2"
                                    :title="g.name"
                                    prepend-icon="$group"
                                />
                            </template>

                            <SidebarConfigItem
                                v-for="c in g.items"
                                :key="c.id"
                                :id="c.id"
                                :doc="c.doc"
                                :selected-id="selectedId"
                                :user="user"
                                :user-level="userLevel"
                                :UserLevelEnum="UserLevelEnum"
                                @select="$emit('select', $event)"
                                @duplicate="$emit('duplicate', $event)"
                                @delete="$emit('delete', $event)"
                            />
                        </v-list-group>
                    </template>

                    <v-list-item
                        v-else
                        class="text-medium-emphasis"
                        title="No shared configurations"
                    />
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
import { computed } from "vue";

import SidebarFolderNode from "./sidebar/SidebarFolderNode.vue";
import SidebarConfigItem from "./sidebar/SidebarConfigItem.vue";

const props = defineProps({
    configurationCache: { type: Object, required: true },
    selectedId: { type: String, default: null },
    user: { type: Object, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true }
});

defineEmits(["select", "create", "duplicate", "delete"]);

const { $api } = useNuxtApp();

const { data: folderTree } = await useAsyncData(
    `configuration-folders-tree-${props.user.user_name}`,
    async () => (await $api.configurationFolders.get())?.data || []
);

const myMaxDepth = computed(() =>
    props.userLevel >= props.UserLevelEnum.manager ? 3 : 2
);

const allConfigs = computed(() =>
    Object.entries(props.configurationCache || {}).map(([id, doc]) => ({
        id,
        doc
    }))
);

const isManagerOrAdmin = computed(
    () => props.userLevel >= props.UserLevelEnum.manager
);

const myHomeNode = computed(() => {
    const roots = folderTree.value || [];
    return roots.find((n) => n?.name === props.user.user_name) || null;
});

const myFolderRoots = computed(() => {
    const roots = folderTree.value || [];
    if (isManagerOrAdmin.value) return roots;

    const home = myHomeNode.value;
    if (!home) return roots; // fallback
    return home.children || [];
});

const myConfigsByFolder = computed(() => {
    const m = new Map();

    for (const { id, doc } of allConfigs.value) {
        if (doc?.misc?.owner !== props.user.user_name) continue;

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

const showMyHomeInline = computed(
    () => !isManagerOrAdmin.value && !!myHomeNode.value
);

const myHomeConfigs = computed(() => {
    if (!showMyHomeInline.value) return [];
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
</style>
