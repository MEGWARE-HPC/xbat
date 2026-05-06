import { computed, ref, watch } from "vue";

export function useFolderBrowser(props: any, emit: any) {
    const { $api, $snackbar, $store } = useNuxtApp();

    const selectItems = ref((props.selected || []).map(String));

    watch(
        () => props.selected,
        (v) => {
            selectItems.value = (v || []).map(String);
        }
    );

    const selectedSet = computed(() => new Set(selectItems.value));

    const folderToken = (id: any) => `f:${String(id)}`;
    const configToken = (id: any) => `c:${String(id)}`;

    const isSelected = (token: any) => selectedSet.value.has(String(token));

    const setSelected = (arr: any[]) => {
        selectItems.value = arr.map(String);
        emit("update:selected", selectItems.value.slice());
    };

    const toggleSelect = (token: any) => {
        const t = String(token);
        const s = new Set(selectedSet.value);
        if (s.has(t)) s.delete(t);
        else s.add(t);
        setSelected(Array.from(s));
    };

    const selectedTokens = computed(() => selectItems.value || []);

    const selectedFolderIds = computed(() =>
        selectedTokens.value
            .filter((t) => String(t).startsWith("f:"))
            .map((t) => String(t).slice(2))
    );

    const selectedConfigIds = computed(() =>
        selectedTokens.value
            .filter((t) => String(t).startsWith("c:"))
            .map((t) => String(t).slice(2))
    );

    const hasSelect = computed(
        () =>
            selectedFolderIds.value.length + selectedConfigIds.value.length > 0
    );

    const mixedSelect = computed(
        () =>
            selectedFolderIds.value.length > 0 &&
            selectedConfigIds.value.length > 0
    );

    const configById = computed(() => {
        const m = new Map();
        for (const item of props.configs || [])
            m.set(String(item.id), item.doc);
        return m;
    });

    const ownSelectConfigIds = computed(() =>
        selectedConfigIds.value.filter((id) => {
            const doc = configById.value.get(String(id));
            return doc?.misc?.owner === props.userName;
        })
    );

    const cfgFolderIds = computed(() => {
        const ids = [];

        for (const cid of ownSelectConfigIds.value) {
            const doc = configById.value.get(String(cid));
            const fid = doc?.configuration?.folderId;
            if (fid) ids.push(String(fid));
        }

        return ids;
    });

    const cfgFolderIdSet = computed(() => new Set(cfgFolderIds.value));

    const moveInvalid = computed(() => {
        const dest = String(moveDestId.value || "");
        if (!dest) return true;

        if (cfgFolderIdSet.value.size === 1) {
            return cfgFolderIdSet.value.has(dest);
        }

        return false;
    });

    const folderNodeById = computed(() => {
        const m = new Map();
        for (const f of props.folder?.children || []) m.set(String(f.id), f);
        return m;
    });

    const ownSelectFolderIds = computed(() =>
        selectedFolderIds.value.filter((id) => {
            const node = folderNodeById.value.get(String(id));
            return (
                (node?.misc?.owner && node.misc.owner === props.userName) ||
                props.userLevel >= props.UserLevelEnum.manager
            );
        })
    );

    const canDownload = computed(
        () => !mixedSelect.value && selectedConfigIds.value.length > 0
    );

    const canShare = computed(
        () => !mixedSelect.value && ownSelectConfigIds.value.length > 0
    );

    const canRename = computed(
        () =>
            !mixedSelect.value &&
            selectedFolderIds.value.length + selectedConfigIds.value.length ===
                1
    );

    const canDuplicate = computed(
        () =>
            selectedFolderIds.value.length === 0 &&
            selectedConfigIds.value.length === 1 &&
            ownSelectConfigIds.value.length === 1
    );

    const canMove = computed(
        () =>
            !mixedSelect.value &&
            selectedFolderIds.value.length === 0 &&
            selectedConfigIds.value.length > 0 &&
            ownSelectConfigIds.value.length > 0
    );

    const canDelete = computed(() => hasSelect.value);

    const canCreate = computed(
        () => props.userLevel > (props.UserLevelEnum?.guest ?? 0)
    );

    const isPrivileged = computed(
        () => props.userLevel >= props.UserLevelEnum.manager
    );

    const backupScopeItems = computed(() => {
        if (!isPrivileged.value) {
            return [{ title: "My configurations", value: "self" }];
        }

        return [
            { title: "My configurations", value: "self" },
            { title: "Specific user", value: "owner" },
            { title: "All users (preserve owners)", value: "all" }
        ];
    });

    const conflictStrategyItems = [
        { title: "Overwrite", value: "overwrite" },
        { title: "Rename", value: "rename" },
        { title: "Skip", value: "skip" }
    ];

    const isMyRoot = computed(() => {
        const fid = String(props.folder?.id ?? "");
        return !!props.myRootId && fid === String(props.myRootId);
    });

    const headerTitle = computed(() => {
        if (isSharedView.value) return props.folder?.name || "";
        if (folderId.value === "__all__") return props.folder?.name || "";

        if (isMyRoot.value) return "Home";

        return props.folder?.name || "";
    });

    const folderId = computed(() => String(props.folder?.id ?? ""));

    const isSharedView = computed(() =>
        folderId.value.startsWith("__shared__")
    );
    const isSharedRoot = computed(() => folderId.value === "__shared__");
    const isSharedProject = computed(() =>
        folderId.value.startsWith("__shared__:")
    );

    const parentId = computed(() => props.folder?.__parentId ?? null);

    const canGoUp = computed(() => !!props.folder && !!parentId.value);

    const folders = computed(() => (props.folder?.children || []).slice());

    const sortBy = ref("name");
    const sortDesc = ref(false);

    const setSort = (key: any) => {
        if (sortBy.value === key) {
            sortDesc.value = !sortDesc.value;
            return;
        }

        sortBy.value = key;
        sortDesc.value = false;
    };

    const normalizeString = (v: any) => String(v || "").toLocaleLowerCase();

    const parseDateValue = (v: any) => {
        if (!v) return 0;
        const t = new Date(v).getTime();
        return Number.isNaN(t) ? 0 : t;
    };

    const compareValues = (a: any, b: any) => {
        if (a < b) return sortDesc.value ? 1 : -1;
        if (a > b) return sortDesc.value ? -1 : 1;
        return 0;
    };

    const sortedFolders = computed(() => {
        const arr = folders.value.slice();

        arr.sort((a, b) => {
            switch (sortBy.value) {
                case "owner":
                    return compareValues(
                        normalizeString(a?.misc?.owner),
                        normalizeString(b?.misc?.owner)
                    );

                case "created":
                    return compareValues(
                        parseDateValue(a?.misc?.created),
                        parseDateValue(b?.misc?.created)
                    );

                case "edited":
                    return compareValues(
                        parseDateValue(a?.misc?.edited),
                        parseDateValue(b?.misc?.edited)
                    );

                case "name":
                default:
                    return compareValues(
                        normalizeString(a?.name),
                        normalizeString(b?.name)
                    );
            }
        });

        return arr;
    });

    const sortedConfigs = computed(() => {
        const arr = (props.configs || []).slice();

        arr.sort((a, b) => {
            switch (sortBy.value) {
                case "owner":
                    return compareValues(
                        normalizeString(a?.doc?.misc?.owner),
                        normalizeString(b?.doc?.misc?.owner)
                    );

                case "created":
                    return compareValues(
                        parseDateValue(a?.doc?.misc?.created),
                        parseDateValue(b?.doc?.misc?.created)
                    );

                case "edited":
                    return compareValues(
                        parseDateValue(a?.doc?.misc?.edited),
                        parseDateValue(b?.doc?.misc?.edited)
                    );

                case "name":
                default:
                    return compareValues(
                        normalizeString(
                            a?.doc?.configuration?.configurationName || a?.id
                        ),
                        normalizeString(
                            b?.doc?.configuration?.configurationName || b?.id
                        )
                    );
            }
        });

        return arr;
    });

    const visibleTokens = computed(() => {
        const tokens = [];
        for (const f of folders.value)
            if (f?.id) tokens.push(folderToken(f.id));
        for (const c of props.configs || [])
            if (c?.id) tokens.push(configToken(c.id));
        return tokens;
    });

    const headerCheck = computed({
        get() {
            const toks = visibleTokens.value;
            if (!toks.length) return false;
            return toks.every((t) => selectedSet.value.has(t));
        },
        set(v) {
            const toks = visibleTokens.value;
            if (!toks.length) return;

            const s = new Set(selectedSet.value);
            if (v) {
                for (const t of toks) s.add(t);
            } else {
                for (const t of toks) s.delete(t);
            }
            setSelected(Array.from(s));
        }
    });

    const headerState = computed(() => {
        const toks = visibleTokens.value;
        if (!toks.length) return false;

        let hit = 0;
        for (const t of toks) if (selectedSet.value.has(t)) hit++;

        return hit > 0 && hit < toks.length;
    });

    const rowGridStyle = computed(() => ({
        "--fb-cols": "32px 1fr 160px 160px 160px"
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

    const formatDate = (v: any) => {
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

    const restoreModeLabel = (mode: any) => {
        switch (String(mode || "").toLowerCase()) {
            case "self":
                return "My Configurations";
            case "owner":
                return "Specific User";
            case "all":
                return "All Users";
            default:
                return String(mode || "—");
        }
    };

    const CreateFolderDlg = ref(false);
    const RenameDlg = ref(false);
    const MoveDlg = ref(false);
    const ShareDlg = ref(false);
    const DeleteDlg = ref(false);
    const ExportBackupDlg = ref(false);
    const RestoreBackupDlg = ref(false);
    const RestoreResultDlg = ref(false);

    const exportScope = ref("self");
    const exportOwner = ref("");

    const restoreFile = ref(null);
    const restoreScope = ref("self");
    const restoreOwner = ref("");
    const restoreConflictStrategy = ref("rename");
    const restoreSummary = ref(null);

    const inputFolderName = ref("");
    const inputRename = ref("");
    const shareProjectIds = ref([]);

    const moveDestId = ref("");
    const moveFolderTree = ref([]);
    const moveFolderPath = ref("");

    const selectedRestoreFile = computed(() => {
        if (Array.isArray(restoreFile.value)) {
            return restoreFile.value[0] || null;
        }
        return restoreFile.value || null;
    });

    const normalizeOwner = (v: any) => String(v || "").trim();

    const getErrorMessage = (error: any, fallback: any) => {
        if (error instanceof Error && error.message) return error.message;
        return fallback;
    };

    const clearDialogs = () => {
        CreateFolderDlg.value = false;
        RenameDlg.value = false;
        MoveDlg.value = false;
        ShareDlg.value = false;
        DeleteDlg.value = false;
        ExportBackupDlg.value = false;
        RestoreBackupDlg.value = false;
        RestoreResultDlg.value = false;
    };

    const createCfgFolderId = computed(() => {
        const fid = String(props.folder?.id || "");
        if (!fid || fid.startsWith("__")) return "";
        return fid;
    });

    const duplicateConfig = () => {
        if (!canDuplicate.value) return;

        for (const cid of ownSelectConfigIds.value) {
            emit("duplicate", { presetId: String(cid) });
        }

        setSelected([]);
    };

    const openCreateFolder = () => {
        inputFolderName.value = "";
        CreateFolderDlg.value = true;
    };

    const normalizeName = (v: any) => String(v || "").trim();

    const sibFolderName = (name: any, excludeId = "") => {
        const target = normalizeName(name);

        return (props.folder?.children || []).some(
            (child: any) =>
                String(child?.id || "") !== String(excludeId) &&
                normalizeName(child?.name) === target
        );
    };

    const sibConfigName = (name: any, excludeId = "") => {
        const target = normalizeName(name);

        return (props.configs || []).some(
            (item: any) =>
                String(item?.id || "") !== String(excludeId) &&
                normalizeName(
                    item?.doc?.configuration?.configurationName || item?.id
                ) === target
        );
    };

    const createFolder = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const name = normalizeName(inputFolderName.value);
        if (!name) return;

        if (sibFolderName(name)) {
            $snackbar.show(
                "A folder with the same name already exists in this location"
            );
            return;
        }

        const parent = folderId.value.startsWith("__")
            ? null
            : String(props.folder?.id || null);

        await $api.configurationFolders.post({
            folder: {
                folderName: name,
                parentFolderId: parent,
                sharedProjects: []
            }
        });

        CreateFolderDlg.value = false;
        $snackbar.show("Folder created");
        setSelected([]);
        emit("refresh");
    };

    // TODO: Provide a download feature for specific configurations (v2.1.0)
    const downloadSelected = () => {};

    const openExportBackup = () => {
        exportScope.value = "self";
        exportOwner.value = "";
        ExportBackupDlg.value = true;
    };

    const applyExportBackup = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const scope = String(exportScope.value || "self");
        const owner = normalizeOwner(exportOwner.value);

        if (scope === "owner" && !owner) {
            $snackbar.show("Please enter a username");
            return;
        }

        try {
            await $api.configurationBackups.download(scope, owner);
            ExportBackupDlg.value = false;
            $snackbar.show("Backup exported");
        } catch (error) {
            $snackbar.show(getErrorMessage(error, "Failed to export backup"));
        }
    };

    const openRestoreBackup = () => {
        restoreFile.value = null;
        restoreScope.value = "self";
        restoreOwner.value = "";
        restoreConflictStrategy.value = "rename";
        RestoreBackupDlg.value = true;
    };

    const applyRestoreBackup = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const file = selectedRestoreFile.value;
        const scope = String(restoreScope.value || "self");
        const owner = normalizeOwner(restoreOwner.value);
        const conflictStrategy = String(
            restoreConflictStrategy.value || "rename"
        );

        if (!file) {
            $snackbar.show("Please select a backup file");
            return;
        }

        if (scope === "owner" && !owner) {
            $snackbar.show("Please enter a username");
            return;
        }

        try {
            const result = await $api.configurationBackups.restore(file, {
                scope,
                owner,
                conflictStrategy
            });

            if (!result?.data) {
                throw new Error("Restore completed without summary");
            }

            restoreSummary.value = result.data;
            RestoreBackupDlg.value = false;
            RestoreResultDlg.value = true;

            setSelected([]);
            emit("refresh");

            $snackbar.show("Backup restored");
        } catch (error) {
            $snackbar.show(getErrorMessage(error, "Failed to restore backup"));
        }
    };

    const openShare = () => {
        shareProjectIds.value = [];
        ShareDlg.value = true;
    };

    const applyShare = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const targetIds = ownSelectConfigIds.value;
        const pids = (shareProjectIds.value || []).map(String);

        for (const cid of targetIds) {
            const doc = configById.value.get(String(cid));
            if (!doc) continue;

            const payload = {
                _id: String(cid),
                configuration: { ...doc.configuration, sharedProjects: pids },
                misc: doc.misc
            };

            await $api.configurations.put(String(cid), payload);
        }

        ShareDlg.value = false;
        $snackbar.show("Sharing updated");
        setSelected([]);
        emit("refresh");
    };

    const openRename = async () => {
        inputRename.value = "";

        // folder selected
        if (selectedFolderIds.value.length === 1) {
            const id = selectedFolderIds.value[0];
            const node = folderNodeById.value.get(String(id));
            inputRename.value = node?.name || "";
            RenameDlg.value = true;
            return;
        }

        // config selected
        if (selectedConfigIds.value.length === 1) {
            const id = selectedConfigIds.value[0];
            const doc = configById.value.get(String(id));
            inputRename.value = doc?.configuration?.configurationName || "";
            RenameDlg.value = true;
        }
    };

    const applyRename = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const name = normalizeName(inputRename.value);
        if (!name) return;

        // rename folder
        if (selectedFolderIds.value.length === 1) {
            const fid = selectedFolderIds.value[0];

            if (sibFolderName(name, fid)) {
                $snackbar.show(
                    "A folder with the same name already exists in this location"
                );
                return;
            }

            const full = await $api.configurationFolders.getOne(String(fid));
            const updated = {
                folder: {
                    ...full.folder,
                    folderName: name
                },
                misc: full.misc
            };

            await $api.configurationFolders.put(String(fid), updated);

            RenameDlg.value = false;
            $snackbar.show("Folder renamed");
            setSelected([]);
            emit("refresh");
            return;
        }

        // rename config
        if (selectedConfigIds.value.length === 1) {
            const cid = selectedConfigIds.value[0];

            if (sibConfigName(name, cid)) {
                $snackbar.show(
                    "A configuration with the same name already exists in this folder"
                );
                return;
            }

            const doc = configById.value.get(String(cid));
            if (!doc) return;

            const payload = {
                _id: String(cid),
                configuration: {
                    ...doc.configuration,
                    configurationName: name
                },
                misc: doc.misc
            };

            await $api.configurations.put(String(cid), payload);

            RenameDlg.value = false;
            $snackbar.show("Configuration renamed");
            setSelected([]);
            emit("refresh");
        }
    };

    const buildMoveTree = (nodes: any, parentPath = "home") => {
        const result = [];

        for (const node of nodes || []) {
            if (!node?.id) continue;

            const currentPath =
                parentPath === "home"
                    ? `home/${node.name}`
                    : `${parentPath}/${node.name}`;

            result.push({
                id: String(node.id),
                name: node.name,
                path: currentPath,
                children: buildMoveTree(node.children || [], currentPath)
            });
        }

        return result;
    };

    const findUserHomeTree = (treeNodes: any, userName: any) => {
        return (
            (treeNodes || []).find(
                (n: any) => n?.name === userName && n?.misc?.owner === userName
            ) || null
        );
    };

    const openMove = async () => {
        if (!canMove.value) return;

        moveDestId.value = "";
        moveFolderPath.value = "";
        MoveDlg.value = true;

        const treeResp = await $api.configurationFolders.get();
        const fullTree = treeResp?.data || [];

        const myHome = findUserHomeTree(fullTree, props.userName);

        if (!myHome) {
            moveFolderTree.value = [];
            return;
        }

        moveFolderTree.value = [
            {
                id: String(myHome.id),
                name: "home",
                path: "home",
                children: buildMoveTree(myHome.children || [], "home")
            }
        ];
    };

    const moveDestination = (node: any) => {
        if (!node?.id) return;
        moveDestId.value = String(node.id);
        moveFolderPath.value = node.path || "";
    };

    const selectMoveDestination = (node: any) =>
        String(moveDestId.value || "") === String(node?.id || "");

    const applyMove = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        const dest = String(moveDestId.value || "");
        if (!dest) return;

        for (const cid of ownSelectConfigIds.value) {
            const doc = configById.value.get(String(cid));
            if (!doc) continue;

            const payload = {
                _id: String(cid),
                configuration: { ...doc.configuration, folderId: dest },
                misc: doc.misc
            };

            await $api.configurations.put(String(cid), payload);
        }

        MoveDlg.value = false;
        $snackbar.show("Moved");
        setSelected([]);
        emit("refresh");
    };

    const openDelete = () => {
        DeleteDlg.value = true;
    };

    const applyDelete = async () => {
        if ($store?.demo) return $snackbar.show($store.demoMessage);

        for (const fid of ownSelectFolderIds.value) {
            await $api.configurationFolders.delete(String(fid));
        }

        for (const cid of ownSelectConfigIds.value) {
            await $api.configurations.delete(String(cid));
        }

        DeleteDlg.value = false;
        $snackbar.show("Deleted");
        setSelected([]);
        emit("refresh");
    };

    return {
        selectItems,
        selectedSet,
        folderToken,
        configToken,
        isSelected,
        setSelected,
        toggleSelect,
        selectedTokens,
        selectedFolderIds,
        selectedConfigIds,
        hasSelect,
        mixedSelect,
        configById,
        ownSelectConfigIds,
        cfgFolderIds,
        cfgFolderIdSet,
        moveInvalid,
        folderNodeById,
        ownSelectFolderIds,
        canDownload,
        canShare,
        canRename,
        canDuplicate,
        canMove,
        canDelete,
        canCreate,
        isPrivileged,
        backupScopeItems,
        conflictStrategyItems,
        isMyRoot,
        headerTitle,
        folderId,
        isSharedView,
        isSharedRoot,
        isSharedProject,
        parentId,
        canGoUp,
        folders,
        sortBy,
        sortDesc,
        setSort,
        normalizeString,
        parseDateValue,
        compareValues,
        sortedFolders,
        sortedConfigs,
        visibleTokens,
        headerCheck,
        headerState,
        rowGridStyle,
        headerIcon,
        headerIconClass,
        childFolderIcon,
        childFolderIconClass,
        formatDate,
        restoreModeLabel,
        CreateFolderDlg,
        RenameDlg,
        MoveDlg,
        ShareDlg,
        DeleteDlg,
        ExportBackupDlg,
        RestoreBackupDlg,
        RestoreResultDlg,
        exportScope,
        exportOwner,
        restoreFile,
        restoreScope,
        restoreOwner,
        restoreConflictStrategy,
        restoreSummary,
        inputFolderName,
        inputRename,
        shareProjectIds,
        moveDestId,
        moveFolderTree,
        moveFolderPath,
        selectedRestoreFile,
        normalizeOwner,
        getErrorMessage,
        clearDialogs,
        createCfgFolderId,
        duplicateConfig,
        openCreateFolder,
        normalizeName,
        sibFolderName,
        sibConfigName,
        createFolder,
        downloadSelected,
        openExportBackup,
        applyExportBackup,
        openRestoreBackup,
        applyRestoreBackup,
        openShare,
        applyShare,
        openRename,
        applyRename,
        buildMoveTree,
        findUserHomeTree,
        openMove,
        moveDestination,
        selectMoveDestination,
        applyMove,
        openDelete,
        applyDelete
    };
}
