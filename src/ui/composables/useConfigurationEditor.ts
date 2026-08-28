import { ref, computed, type Ref, type ComputedRef } from "vue";

type TreeNode = {
    id?: string;
    name?: string;
    misc?: {
        owner?: string;
    };
    children?: TreeNode[];
};

type EditorState = {
    currentEdit: string;
    selectedEdit: string[];
    showCloseDialog: boolean;
};

type ConfigurationCacheValue = {
    configuration?: Record<string, any>;
};

type UseConfigurationEditorParams = {
    state: EditorState;
    form: Ref<Record<string, any>>;
    defaultForm: Record<string, any>;
    configurationCache: Ref<Record<string, ConfigurationCacheValue>>;
    formBeforeEdit: Ref<Record<string, Record<string, any>>>;
    currentEditNotYetSaved: ComputedRef<boolean>;
    folderTree: Ref<TreeNode[] | null | undefined>;
    userName: string;
    save: () => Promise<void>;
    resetForm: () => void;
};

export function useConfigurationEditor({
    state,
    form,
    defaultForm,
    configurationCache,
    formBeforeEdit,
    currentEditNotYetSaved,
    folderTree,
    userName,
    save,
    resetForm
}: UseConfigurationEditorParams) {
    const showFolderPickerDialog = ref(false);
    const editorFolderTree = ref<any[]>([]);

    const hasUnsavedChanges = computed(() => {
        const id = state.currentEdit;
        if (!id) return false;

        if (currentEditNotYetSaved.value) {
            const current = configurationCache.value[id]?.configuration || {};
            return JSON.stringify(current) !== JSON.stringify(defaultForm);
        }

        const original = formBeforeEdit.value[id];
        if (!original) return false;

        return JSON.stringify(form.value) !== JSON.stringify(original);
    });

    const closeEditor = () => {
        state.selectedEdit = [];
    };

    const discardAndClose = () => {
        resetForm();

        if (currentEditNotYetSaved.value && state.currentEdit) {
            delete configurationCache.value[state.currentEdit];
        }

        state.showCloseDialog = false;
        closeEditor();
    };

    const saveAndClose = async () => {
        await save();
        state.showCloseDialog = false;
        closeEditor();
    };

    const requestCloseEditor = () => {
        if (!state.currentEdit) {
            closeEditor();
            return;
        }

        if (!hasUnsavedChanges.value) {
            closeEditor();
            return;
        }

        state.showCloseDialog = true;
    };

    const folderPathById = computed(() => {
        const map = new Map<string, string>();
        const roots = folderTree.value || [];
        const ownHome =
            roots.find(
                (n) => n?.name === userName && n?.misc?.owner === userName
            ) ||
            roots.find((n) => n?.name === userName) ||
            null;

        const walk = (node: TreeNode, parts: string[] = []) => {
            if (!node?.id) return;

            const isHome = ownHome && String(node.id) === String(ownHome.id);
            const nextParts = isHome
                ? ["home"]
                : [...parts, String(node.name || "")];

            map.set(String(node.id), nextParts.join("/"));

            for (const child of node.children || []) {
                walk(child, nextParts);
            }
        };

        if (ownHome) walk(ownHome, []);
        return map;
    });

    const editorFolderPath = computed(() => {
        const fid = String(form.value?.folderId || "");
        if (!fid) return "";
        return folderPathById.value.get(fid) || "";
    });

    const buildMoveTree = (nodes: TreeNode[] = [], parentPath = "home") => {
        const result: any[] = [];

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

    const findUserHomeTree = (
        treeNodes: TreeNode[] = [],
        currentUserName: string
    ) => {
        return (
            treeNodes.find(
                (n) =>
                    n?.name === currentUserName &&
                    n?.misc?.owner === currentUserName
            ) ||
            treeNodes.find((n) => n?.name === currentUserName) ||
            null
        );
    };

    const openFolderPicker = () => {
        const fullTree = folderTree.value || [];
        const myHome = findUserHomeTree(fullTree, userName);

        if (!myHome) {
            editorFolderTree.value = [];
            showFolderPickerDialog.value = true;
            return;
        }

        editorFolderTree.value = [
            {
                id: String(myHome.id),
                name: "home",
                path: "home",
                children: buildMoveTree(myHome.children || [], "home")
            }
        ];

        showFolderPickerDialog.value = true;
    };

    const selectEditorFolder = (node: { id?: string; path?: string }) => {
        if (!node?.id) return;
        form.value.folderId = String(node.id);
        showFolderPickerDialog.value = false;
    };

    return {
        showFolderPickerDialog,
        editorFolderTree,
        editorFolderPath,

        hasUnsavedChanges,
        closeEditor,
        discardAndClose,
        saveAndClose,
        requestCloseEditor,

        openFolderPicker,
        selectEditorFolder
    };
}
