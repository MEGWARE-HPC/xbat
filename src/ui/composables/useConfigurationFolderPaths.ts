export type ConfigurationFolderNode = {
    id?: string;
    name?: string;
    misc?: {
        owner?: string;
    };
    children?: ConfigurationFolderNode[];
};

export const findUserHomeTree = (
    treeNodes: ConfigurationFolderNode[] = [],
    userName: string
) => {
    return (
        treeNodes.find(
            (node) => node?.name === userName && node?.misc?.owner === userName
        ) ||
        treeNodes.find((node) => node?.name === userName) ||
        null
    );
};

export const buildConfigurationFolderPathMap = (
    treeNodes: ConfigurationFolderNode[] = [],
    userName: string
) => {
    const map = new Map<string, string>();

    const ownHome = findUserHomeTree(treeNodes, userName);

    const walk = (node: ConfigurationFolderNode, parts: string[] = []) => {
        if (!node?.id) return;

        const nextParts = [...parts, String(node.name || "")].filter(Boolean);

        map.set(String(node.id), nextParts.join("/"));

        for (const child of node.children || []) {
            walk(child, nextParts);
        }
    };

    for (const root of treeNodes) {
        if (!root?.id) continue;

        const isOwnHome = ownHome && String(root.id) === String(ownHome.id);

        if (isOwnHome) {
            map.set(String(root.id), "home");

            for (const child of root.children || []) {
                walk(child, ["home"]);
            }
        } else {
            walk(root);
        }
    }

    return map;
};
