import type { GraphOverrides } from "~/types/graph";

export type GeneralGraphSettings = {
    rangeslider: boolean;
    xTitle: boolean;
    hideInactive: "none" | "hidden" | "disabled";
    colorPalette: string;
};

export const usePreferences = () => {
    return {
        graphPreferences: useCookie("xbat_graph-preferences", {
            default: (): GeneralGraphSettings => ({
                rangeslider: false,
                xTitle: false,
                hideInactive: "none",
                colorPalette: "D3"
            })
        }),
        graphOverrides: useCookie("xbat_graph-overrides", {
            default: (): GraphOverrides => ({
                prefixes: {},
                traces: {}
            })
        }),
        displayColumns: useCookie("xbat_graph-arrangement-columns", {
            default: () => false
        }),
        infoCollapsed: useCookie("xbat_info-collapsed", {
            default: () => false
        }),
        overviewItemsPerPage: useCookie("xbat_overview-items-per-page", {
            default: () => 10
        })
    };
};

export default usePreferences;
