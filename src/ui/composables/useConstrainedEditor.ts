import type { Jobscript } from "@/repository/modules/configurations";
import * as monacoEditor from "monaco-editor/esm/vs/editor/editor.api";
import { constrainedEditor } from "constrained-editor-plugin";
import { useDebounceFn } from "@vueuse/core";

type inputValidationFunction = (input: string) => boolean | string;

type MonacoEditor = typeof monacoEditor;

type Range = [number, number, number, number];

type RangeRestriction = {
    range: Range;
    label: string;
    allowMultiline?: boolean;
    validate?: (
        value: string,
        range: monacoEditor.IRange,
        info: constrainedEditor
    ) => boolean;
};

type RangeInfo = {
    isAddition: boolean;
    startLineOfRange: boolean;
    startColumnOfRange: boolean;
    endLineOfRange: boolean;
    endColumnOfRange: boolean;
    middleLineOfRange: boolean;
    rangeIsSingleLine: boolean;
};

type EditableRangeObject = {
    [key: string]: {
        allowMultiline: boolean;
        range: monacoEditor.Range;
        originalRange: Range;
        index: number;
    };
};

type SubmittionValidationError = {
    message: string;
    label: string;
    top: number;
};

const directiveExternalLinks: { [key: string]: string } = {
    "job-name": "https://slurm.schedmd.com/sbatch.html#OPT_job-name",
    nodelist: "https://slurm.schedmd.com/sbatch.html#OPT_nodelist",
    nodes: "https://slurm.schedmd.com/sbatch.html#OPT_nodes",
    ntasks: "https://slurm.schedmd.com/sbatch.html#OPT_ntasks",
    partition: "https://slurm.schedmd.com/sbatch.html#OPT_partition",
    time: "https://slurm.schedmd.com/sbatch.html#OPT_time",
    output: "https://slurm.schedmd.com/sbatch.html#OPT_output",
    error: "https://slurm.schedmd.com/sbatch.html#OPT_error"
};

export const useConstrainedEditor = (modelValue: Ref<Jobscript>, emit: any) => {
    const {
        vNotEmpty,
        vNoSpecialChars,
        vWalltime,
        vInteger,
        vCommaSeparatedList,
        vSlurmNodeList,
        vFilePath,
        vNoSpaces,
        vWalltimeChars
    } = useFormValidation();

    const mounted = ref(false);

    let editorInstance: monacoEditor.editor.IStandaloneCodeEditor | null = null;
    let editorModel: monacoEditor.editor.ITextModel | null = null;
    let constrainedInstance: constrainedEditor | null = null;

    let restrictionsApplied = false;
    // let listenersRegistered = false;

    const directives = computed(() => {
        const defaultOut = ".xbat/outputs/%j.out";
        const v = modelValue.value;

        if (v === null || typeof v !== "object") return "";

        // for old configurations that do not have output and error fields
        if (!v.output) v.output = defaultOut;
        if (!v.error) v.error = defaultOut;

        // mind formatting - otherwise rules will not be calculated correctly
        return `#!/bin/bash
#SBATCH --job-name=${v["job-name"] || ""}
#SBATCH --ntasks=${v.ntasks || ""}
#SBATCH --partition=${
            Array.isArray(v.partition)
                ? v.partition.join(",")
                : v.partition || ""
        }
#SBATCH --nodes=${v.nodes || ""}
#SBATCH --nodelist=${v.nodelist || ""}
#SBATCH --time=${v.time || "01:00:00"}
#SBATCH --output=${defaultOut}
#SBATCH --error=${defaultOut}`;
    });

    const directiveRules: {
        [key: string]: {
            input: inputValidationFunction[];
            submission: inputValidationFunction[];
        };
    } = {
        "job-name": {
            input: [vNoSpecialChars, vNoSpaces],
            submission: [vNoSpecialChars, vNoSpaces]
        },
        nodes: {
            input: [vNoSpaces, vInteger],
            submission: [vNoSpaces, vNotEmpty, vInteger]
        },
        nodelist: {
            input: [vNoSpaces, vSlurmNodeList],
            submission: [vNoSpaces, vSlurmNodeList]
        },
        ntasks: {
            input: [vNoSpaces, vInteger],
            submission: [vNoSpaces, vNotEmpty, vInteger]
        },
        partition: {
            input: [vNoSpaces, vCommaSeparatedList],
            submission: [vNoSpaces, vNotEmpty, vCommaSeparatedList]
        },
        time: {
            input: [vNoSpaces, vWalltimeChars],
            submission: [vNotEmpty, vNoSpaces, vWalltime]
        },
        output: {
            input: [vNotEmpty, vFilePath],
            submission: [vNotEmpty, vFilePath]
        },
        error: {
            input: [vNotEmpty, vFilePath],
            submission: [vNotEmpty, vFilePath]
        }
    };

    // restrictions are currently computed whenever modelValue changes and reapplied (including listeners)
    // TODO find better way to handle restriction updates without updating them on every keystroke
    const restrictions = computed(() => {
        let _restrictions: RangeRestriction[] = [];
        const lines = directives.value.split("\n");

        for (let [lineNr, line] of lines.entries()) {
            if (!line.startsWith("#SBATCH")) continue;
            const [key, value] = line.split("=", 2);
            const label = key.replace("#SBATCH --", "");

            // temporarily disable overwriting of output and error locations as this would require further changes when retrieving output
            // this may also break output retrieval if location is outside of users home (and therefore not mounted for xbatctld)
            if (label == "output" || label == "error") continue;

            _restrictions.push({
                range: [
                    lineNr + 1,
                    key.length + 2,
                    lineNr + 1,
                    key.length + 2 + value.length
                ],
                label,
                validate
            });
        }

        if (!modelValue.value?.script) return _restrictions;

        const scriptLines = modelValue.value.script.split("\n");

        const rightmostColumnOfLastLine =
            scriptLines[scriptLines.length - 1].length;

        _restrictions.push({
            range: [
                lines.length + 1,
                1,
                lines.length + (scriptLines.length || 1),
                rightmostColumnOfLastLine + 1
            ],
            label: "script",
            allowMultiline: true
        });
        return _restrictions;
    });

    const restrictionLineNumberLabels = computed(() =>
        Object.fromEntries(restrictions.value.map((r) => [r.range[0], r.label]))
    );

    const restrictionLineNumber = computed(() =>
        Object.fromEntries(restrictions.value.map((r) => [r.label, r.range[0]]))
    );

    const submissionValidation: Ref<SubmittionValidationError[]> = ref([]);

    const validateSubmission = () => {
        const submissionRestrictions = restrictions.value.filter(
            (x) => x.label !== "script"
        );
        submissionValidation.value = [];
        for (let restriction of submissionRestrictions) {
            const label = restriction.label;
            const rules = directiveRules[label].submission;
            const value: string = modelValue.value[label];

            for (const rule of rules) {
                const result = rule(value);
                if (typeof result === "string") {
                    submissionValidation.value.push({
                        message: result,
                        top: 19 * (restrictionLineNumber.value[label] - 1),
                        label: label
                    });
                    break;
                }
            }
        }

        if (submissionValidation.value.length) return false;

        return true;
    };

    const debounceSubmissionValidation = useDebounceFn(
        validateSubmission,
        500,
        { maxWait: 1000 }
    );

    watch(
        modelValue,
        () => {
            debounceSubmissionValidation();
        },
        { deep: true, immediate: true }
    );

    const scrollOffset = reactive({
        left: 0,
        top: 0
    });

    const inputValidation = reactive({
        visible: false,
        message: "",
        left: 0,
        top: 0,
        errorPosition: { column: 0, lineNumber: 0 }
    });

    const validate = (
        v: string,
        range: monacoEditor.IRange,
        info: RangeInfo
    ) => {
        // get label to check against directiveRules
        const label = restrictionLineNumberLabels.value[range.startLineNumber];
        const rules = directiveRules[label].input;

        if (!rules || !rules?.length) return true;

        let valid = true;

        for (const rule of rules) {
            const result = rule(v);
            if (typeof result === "string") {
                inputValidation.message = result;
                valid = false;
                break;
            }
        }

        if (!editorInstance) return valid;

        const cursorPosition: monacoEditor.Position | null =
            editorInstance.getPosition();

        if (!cursorPosition) return valid;

        if (!valid) {
            inputValidation.visible = true;
            inputValidation.left =
                editorInstance.getScrolledVisiblePosition(cursorPosition)
                    ?.left || 0;
            inputValidation.top = 19 * (cursorPosition.lineNumber + 1) || 0;
            inputValidation.errorPosition.lineNumber =
                cursorPosition.lineNumber;
            inputValidation.errorPosition.column = cursorPosition.column;
        } else {
            inputValidation.visible = false;
        }

        return valid;
    };

    watch(
        [restrictions, mounted],
        () => {
            // execute in nextTick to ensure editor content updated before applying new restrictions
            nextTick(() => {
                if (
                    !constrainedInstance ||
                    !editorModel ||
                    !editorInstance ||
                    !mounted.value
                )
                    return;

                if (restrictionsApplied) {
                    constrainedInstance.removeRestrictionsIn(editorModel);
                    restrictionsApplied = false;
                }

                if (restrictions.value.length) {
                    constrainedInstance.addRestrictionsTo(
                        editorModel,
                        restrictions.value
                    );
                    restrictionsApplied = restrictions.value.length > 0;
                }

                // if (listenersRegistered) return;
                // listenersRegistered = true;

                editorModel.onDidChangeContentInEditableRange(
                    (
                        currentContent: object,
                        allContent: object,
                        editableRange: EditableRangeObject
                    ) => {
                        // make sure to not overwrite values that are not part of the editor like variant name

                        emit(
                            "update:modelValue",
                            Object.assign({}, modelValue.value, allContent)
                        );
                    }
                );

                editorInstance.onDidScrollChange(
                    (event: monacoEditor.editor.INewScrollPosition) => {
                        scrollOffset.left = event.scrollLeft || 0;
                        scrollOffset.top = event.scrollTop || 0;
                    }
                );

                editorInstance.onDidChangeCursorPosition(
                    (
                        event: monacoEditor.editor.ICursorPositionChangedEvent
                    ) => {
                        nextTick(() => {
                            if (!inputValidation.visible) return;
                            // cursor position change event is triggered twice,
                            // once on input and once when inputValidation fails and removes the last input.
                            // therefore checking for exact cursor position is not reliable
                            const cursorDistance = Math.abs(
                                inputValidation.errorPosition.column -
                                    event.position.column
                            );

                            if (
                                cursorDistance > 1 ||
                                inputValidation.errorPosition.lineNumber !=
                                    event.position.lineNumber
                            )
                                inputValidation.visible = false;
                        });
                    }
                );
            });
        },
        {
            immediate: true,
            deep: true
        }
    );

    const hoverTarget = ref<monacoEditor.editor.IMouseTarget | null>(null);
    const hoverInfo = computed(() => {
        if (!hoverTarget.value) return { left: 0, top: 0 };
        const lineNr = hoverTarget.value.position?.lineNumber || 1;

        return {
            left: 30,
            top: (lineNr - 1) * 19 - 6,
            href: directiveExternalLinks[
                restrictionLineNumberLabels.value[lineNr]
            ]
        };
    });

    const setHover = (e: monacoEditor.editor.IEditorMouseEvent) => {
        const lineNr = e.target.position?.lineNumber || 1;

        if (
            lineNr == 1 ||
            !(lineNr in restrictionLineNumberLabels.value) ||
            restrictionLineNumberLabels.value[lineNr] == "script"
        ) {
            hoverTarget.value = null;
            return;
        }
        hoverTarget.value = e.target;
    };

    const initConstrainedEditor = (
        _editor: monacoEditor.editor.IStandaloneCodeEditor,
        monaco: MonacoEditor
    ) => {
        editorInstance = _editor;

        editorInstance.onMouseMove(setHover);

        editorModel = _editor.getModel();
        constrainedInstance = constrainedEditor(monaco);
        constrainedInstance.initializeIn(editorInstance);
        mounted.value = true;
    };

    return {
        directives,
        inputValidation,
        initConstrainedEditor,
        hoverTarget,
        hoverInfo,
        submissionValidation,
        scrollOffset
    };
};

export default useConstrainedEditor;
