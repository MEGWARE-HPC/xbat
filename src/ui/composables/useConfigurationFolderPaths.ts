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
): ConfigurationFolderNode | null =>
    treeNodes.find(
        (node) => node?.name === userName && node?.misc?.owner === userName
    ) ||
    treeNodes.find((node) => node?.name === userName) ||
    null;

export const buildConfigurationFolderPathMap = (
    treeNodes: ConfigurationFolderNode[] = [],
    userName: string
): Map<string, string> => {
    const paths = new Map<string, string>();
    const ownHome = findUserHomeTree(treeNodes, userName);

    const walk = (node: ConfigurationFolderNode, parts: string[]) => {
        if (!node?.id) return;

        paths.set(String(node.id), parts.join("/"));

        for (const child of node.children || []) {
            walk(child, [...parts, String(child.name || "")].filter(Boolean));
        }
    };

    for (const root of treeNodes) {
        if (!root?.id) continue;

        const isOwnHome = ownHome && String(root.id) === String(ownHome.id);
        const rootName = isOwnHome ? "home" : String(root.name || "");
        if (!rootName) continue;

        walk(root, [rootName]);
    }

    return paths;
};
