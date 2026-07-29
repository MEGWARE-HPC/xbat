import { computed, type Ref } from "vue";

type FolderNode = {
    id?: string;
    name?: string;
    children?: FolderNode[];
    misc?: {
        owner?: string;
    };
};

type ConfigDoc = {
    configuration?: {
        folderId?: string;
        configurationName?: string;
        sharedProjects?: string[];
    };
    misc?: {
        owner?: string;
    };
};

type SharedGroupItem = {
    id: string;
    doc: ConfigDoc;
};

export function useConfigurationFolder({
    folderTree,
    configurationCache,
    selectedFolderId,
    userName,
    userProjects,
    userLevel,
    managerLevel
}: {
    folderTree: Ref<FolderNode[] | null | undefined>;
    configurationCache: Ref<Record<string, ConfigDoc>>;
    selectedFolderId: Ref<string | null>;
    userName: string;
    userProjects: Array<{ _id: string; name: string }>;
    userLevel: number;
    managerLevel: number;
}) {
    const folderMap = computed(() => {
        const map = new Map();

        const walk = (
            nodes: FolderNode[] = [],
            parentId: string | null = null
        ) => {
            for (const n of nodes) {
                if (!n?.id) continue;

                const node = { ...n, __parentId: parentId };
                map.set(String(node.id), node);

                walk(n.children || [], String(node.id));
            }
        };

        walk(folderTree.value || [], null);
        return map;
    });

    const rootIdSet = computed(() => {
        const s = new Set<string>();
        for (const n of folderTree.value || []) {
            if (n?.id) s.add(String(n.id));
        }
        return s;
    });

    const configsByFolder = computed(() => {
        const m = new Map<string, SharedGroupItem[]>();

        for (const [id, doc] of Object.entries(
            configurationCache.value || {}
        )) {
            const folderId = doc?.configuration?.folderId
                ? String(doc.configuration.folderId)
                : "root";

            if (!m.has(folderId)) m.set(folderId, []);
            m.get(folderId)!.push({ id, doc });
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

    const projectNameById = computed(() => {
        const m = new Map<string, string>();
        for (const p of userProjects || []) {
            m.set(String(p._id), p.name);
        }
        return m;
    });

    const sharedConfigsFlat = computed(() => {
        const arr: SharedGroupItem[] = [];
        for (const [id, doc] of Object.entries(
            configurationCache.value || {}
        )) {
            if (doc?.misc?.owner && doc.misc.owner !== userName) {
                arr.push({ id, doc });
            }
        }
        return arr;
    });

    const sharedBucket = (doc: ConfigDoc) => {
        const ids = doc?.configuration?.sharedProjects || [];
        for (const pid of ids) {
            const k = String(pid);
            if (projectNameById.value.has(k)) return k;
        }
        return "unknown";
    };

    const sharedGroups = computed(() => {
        const buckets = new Map<
            string,
            { key: string; pid: string; name: string; items: SharedGroupItem[] }
        >();

        for (const { id, doc } of sharedConfigsFlat.value) {
            const pid = sharedBucket(doc);
            const name =
                pid === "unknown"
                    ? "Unknown / Other"
                    : projectNameById.value.get(String(pid)) ||
                      "Unknown / Other";

            const groupKey = `__shared__:${pid}`;
            if (!buckets.has(groupKey)) {
                buckets.set(groupKey, { key: groupKey, pid, name, items: [] });
            }
            buckets.get(groupKey)!.items.push({ id, doc });
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

    const sharedGroupByKey = computed(() => {
        const m = new Map();
        for (const g of sharedGroups.value) m.set(g.key, g);
        return m;
    });

    const isManager = computed(() => userLevel >= managerLevel);

    const myHomeNode = computed(() => {
        const roots = folderTree.value || [];
        return roots.find((n) => n?.name === userName) || null;
    });

    const selectedFolderNode = computed(() => {
        const key = selectedFolderId.value
            ? String(selectedFolderId.value)
            : "";
        if (!key) return null;

        if (key === "__all__") {
            const roots = (folderTree.value || []).map((n) => ({
                ...n,
                __parentId: "__all__"
            }));

            return {
                id: "__all__",
                name: "All Folders",
                __parentId: null,
                children: roots
            };
        }

        if (key === "__shared__") {
            const children = sharedGroups.value.map((g) => ({
                id: g.key,
                name: g.name,
                __parentId: "__shared__",
                children: []
            }));

            return {
                id: "__shared__",
                name: "Shared Configurations",
                __parentId: null,
                children
            };
        }

        if (key.startsWith("__shared__:")) {
            const g = sharedGroupByKey.value.get(key);
            if (!g) return null;

            return {
                id: g.key,
                name: g.name,
                __parentId: "__shared__",
                children: []
            };
        }

        const real = folderMap.value.get(key) || null;
        if (!real) return null;

        if (isManager.value && rootIdSet.value.has(key)) {
            return { ...real, __parentId: "__all__" };
        }

        return real;
    });

    const selectedFolderConfigs = computed(() => {
        const key = selectedFolderId.value
            ? String(selectedFolderId.value)
            : "";
        if (!key) return [];

        if (key === "__all__") return [];
        if (key === "__shared__") return [];

        if (key.startsWith("__shared__:")) {
            const g = sharedGroupByKey.value.get(key);
            return g?.items || [];
        }

        return configsByFolder.value.get(key) || [];
    });

    return {
        folderMap,
        rootIdSet,
        configsByFolder,
        projectNameById,
        sharedConfigsFlat,
        sharedGroups,
        sharedGroupByKey,
        selectedFolderNode,
        selectedFolderConfigs,
        myHomeNode,
        isManager
    };
}
