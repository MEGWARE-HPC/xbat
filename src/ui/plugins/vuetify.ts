import "@mdi/font/css/materialdesignicons.css";

import "vuetify/styles";
import { createVuetify } from "vuetify";
import { aliases, mdi } from "vuetify/iconsets/mdi-svg";
// TODO wait for stable update and resolution of icon aliases
import { VFileUpload } from "vuetify/labs/VFileUpload";

import {
    mdiChevronUp,
    mdiPlus,
    mdiContentCopy,
    mdiFileDownload,
    mdiAlertCircleOutline,
    mdiOpenInNew,
    mdiPencil,
    mdiClose,
    mdiThemeLightDark,
    mdiBookOpenVariantOutline,
    mdiFileDocumentOutline,
    mdiApi,
    mdiDotsVertical,
    mdiDatabaseOutline,
    mdiLogout,
    mdiHomeOutline,
    mdiTextBoxOutline,
    mdiGroup,
    mdiAccountGroup,
    mdiGithub,
    mdiAbTesting,
    mdiMenuOpen,
    mdiMagnify,
    mdiDownload,
    mdiChartTimelineVariantShimmer,
    mdiTune,
    mdiHistory,
    mdiFilterMultipleOutline,
    mdiFilterOutline,
    mdiInformationOutline,
    mdiEye,
    mdiEyeOff,
    mdiArrowLeft,
    mdiArrowRight,
    mdiPalette,
    mdiCurrencyUsd,
    mdiServer,
    mdiShareVariantOutline,
    mdiContentDuplicate,
    mdiTrashCanOutline,
    mdiFileDocumentPlusOutline,
    mdiCompare,
    mdiChevronDown,
    mdiAccountMultipleRemoveOutline,
    mdiCancel,
    mdiConsole,
    mdiCogs,
    mdiAccount,
    mdiLockOutline,
    mdiListBoxOutline,
    mdiChevronDoubleLeft,
    mdiChevronDoubleRight,
    mdiRefreshAuto,
    mdiPlay,
    mdiPause,
    mdiMemory,
    mdiViewSequential,
    mdiViewColumn,
    mdiChartLine,
    mdiCompareHorizontal,
    mdiChartSankey,
    mdiCog,
    mdiFileOutline,
    mdiGreaterThan,
    mdiGreaterThanOrEqual,
    mdiLessThan,
    mdiLessThanOrEqual,
    mdiEqual,
    mdiNotEqual,
    mdiDatabaseExportOutline,
    mdiShapeCirclePlus,
    mdiMagnifyExpand,
    mdiContentSaveMove,
    mdiDatabaseImportOutline,
    mdiCloudUpload,
    mdiRead,
    mdiInformation,
    mdiFolderZip,
    mdiGestureTapButton,
    mdiLightningBoltOutline,
    mdiDrag,
    mdiSort,
    mdiSortNumericAscending,
    mdiSortNumericDescending,
    mdiFormatListGroupPlus,
    mdiCheckboxMarked,
    mdiCheckboxBlankOutline,
    mdiBackupRestore
} from "@mdi/js";

/*
 * Opacity is not supported in vue themes.
 * According to material design specifications the fonts should have the following values:
 * base: hsla(0, 0%, 0%, 0.87);
 * light: hsla(0, 0%, 0%, 0.6);
 * disabled: hsla(0, 0%, 0%, 0.38);
 * The chosen rgb values below are only rough approximations...
 */
export default defineNuxtPlugin((app) => {
    const vuetify = createVuetify({
        ssr: true,
        components: {
            VFileUpload
        },
        theme: {
            themes: {
                light: {
                    dark: false,
                    colors: {
                        primary: "#114232",
                        "primary-light": "#1d6d59",
                        secondary: "#1481BA",
                        danger: "#B33951",
                        warning: "#EFA00B",
                        info: "#636262",
                        "font-base": "#0f0f0f",
                        "font-light": "#767676",
                        "font-disabled": "#a3a3a3"
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        primary: "#114232",
                        "primary-light": "#1d6d59",
                        secondary: "#1481BA",
                        danger: "#B33951",
                        warning: "#EFA00B",
                        info: "#E2E8DD",
                        "font-base": "#f3f3f3",
                        "font-light": "#b1b1b1",
                        "font-disabled": "#686868"
                    }
                }
            }
        },
        icons: {
            defaultSet: "mdi",
            aliases: {
                ...aliases,
                greaterThan: mdiGreaterThan,
                greaterThanOrEqual: mdiGreaterThanOrEqual,
                lessThan: mdiLessThan,
                lessThanOrEqual: mdiLessThanOrEqual,
                equal: mdiEqual,
                notEqual: mdiNotEqual,
                chevronUp: mdiChevronUp,
                chevronDown: mdiChevronDown,
                chevronDoubleLeft: mdiChevronDoubleLeft,
                chevronDoubleRight: mdiChevronDoubleRight,
                plus: mdiPlus,
                copy: mdiContentCopy,
                fileDownload: mdiFileDownload,
                alertCircle: mdiAlertCircleOutline,
                openInNew: mdiOpenInNew,
                edit: mdiPencil,
                close: mdiClose,
                menu: mdiDotsVertical,
                themeLightDark: mdiThemeLightDark,
                documentation: mdiBookOpenVariantOutline,
                fileDocument: mdiFileDocumentOutline,
                api: mdiApi,
                database: mdiDatabaseOutline,
                logout: mdiLogout,
                home: mdiHomeOutline,
                textBox: mdiTextBoxOutline,
                group: mdiGroup,
                accountGroup: mdiAccountGroup,
                github: mdiGithub,
                abtesting: mdiAbTesting,
                menuOpen: mdiMenuOpen,
                search: mdiMagnify,
                download: mdiDownload,
                trace: mdiChartTimelineVariantShimmer,
                tune: mdiTune,
                reset: mdiHistory,
                filterMultiple: mdiFilterMultipleOutline,
                filter: mdiFilterOutline,
                information: mdiInformationOutline,
                show: mdiEye,
                hide: mdiEyeOff,
                arrowLeft: mdiArrowLeft,
                arrowRight: mdiArrowRight,
                color: mdiPalette,
                currency: mdiCurrencyUsd,
                server: mdiServer,
                share: mdiShareVariantOutline,
                duplicate: mdiContentDuplicate,
                trashCan: mdiTrashCanOutline,
                newFile: mdiFileDocumentPlusOutline,
                compare: mdiCompare,
                revokeshared: mdiAccountMultipleRemoveOutline,
                cancel: mdiCancel,
                console: mdiConsole,
                cogs: mdiCogs,
                username: mdiAccount,
                password: mdiLockOutline,
                whitelist: mdiListBoxOutline,
                refresh: mdiRefreshAuto,
                play: mdiPlay,
                pause: mdiPause,
                memory: mdiMemory,
                viewSequential: mdiViewSequential,
                viewColumn: mdiViewColumn,
                chartLine: mdiChartLine,
                compareHorizontal: mdiCompareHorizontal,
                chartSankey: mdiChartSankey,
                cog: mdiCog,
                file: mdiFileOutline,
                dataExport: mdiDatabaseExportOutline,
                circlePlus: mdiShapeCirclePlus,
                fullscreen: mdiMagnifyExpand,
                saveMove: mdiContentSaveMove,
                dataImport: mdiDatabaseImportOutline,
                cloudUpload: mdiCloudUpload,
                read: mdiRead,
                info: mdiInformation,
                gestureTap: mdiGestureTapButton,
                lightningBolt: mdiLightningBoltOutline,
                sortDrag: mdiDrag,
                sortCustom: mdiSort,
                sortNumAsc: mdiSortNumericAscending,
                sortNumDesc: mdiSortNumericDescending,
                addArray: mdiFormatListGroupPlus,
                checkboxMark: mdiCheckboxMarked,
                checkboxBlank: mdiCheckboxBlankOutline,
                backupRestore: mdiBackupRestore
            },
            sets: {
                mdi
            }
        },
        defaults: {
            VTextField: {
                density: "compact",
                variant: "outlined"
            },
            VAutocomplete: {
                density: "compact",
                variant: "outlined"
            },
            VNumberInput: {
                density: "compact",
                variant: "outlined",
                inset: true,
                controlVariant: "stacked"
            },
            VSelect: {
                density: "compact",
                variant: "outlined"
            },
            VBtn: {
                density: "default"
            },
            VCard: {
                density: "compact"
            },
            VDataTable: {
                density: "comfortable",
                returnObject: true,
                hover: true
                // selectStrategy: "all"
            },
            VDialog: {
                transition: "dialog-bottom-transition"
            },
            VSwitch: {
                density: "compact",
                color: "primary-light",
                hideDetails: true
            },
            VCheckbox: {
                density: "compact",
                color: "primary-light"
            },
            VCheckboxBtn: {
                density: "compact",
                color: "primary-light"
            },
            VRow: {
                density: "compact"
            },
            VList: {
                density: "compact"
            },
            VTreeview: {
                density: "compact"
            },
            VFileUploadItem: {
                fileIcon: mdiFolderZip
            }
        }
    });
    app.vueApp.use(vuetify);
});
