export const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(
        () => {},
        (err) => {
            console.error("Error copying to clipboard", err);
        }
    );
};

export const getDocType = (path?: string | null): string | null => {
    if (!path) return null;
    const regex = new RegExp(`^/docs/([a-zA-Z]+)/.*$`);
    return path.match(regex)?.[1] || null;
};
