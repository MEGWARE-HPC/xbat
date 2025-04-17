const {
    walltime,
    noSpecialChars,
    filePath,
    commaSeparatedList,
    noSpaces,
    walltimeChars
} = useValidators();

const validationMessages = {
    notEmpty: "Value may not be empty",
    number: "Value must be a number",
    walltime: "Walltime must (partially) match the format 'd-hh:mm:ss'",
    walltimeChars: "Walltime may only contain digits, colons, and hyphens",
    integer: "Value must be positive integer",
    notNegative: "Value may not be negative",
    noSpaces: "Value must not contain spaces",
    noSpecialChars: "Value must not contain special characters",
    filePath: "Invalid file path",
    commaSeparatedList:
        "Invalid input - must be a comma-separated list without special characters"
};

export default function useFormValidation() {
    return {
        vNotEmpty: (v) => !!v || validationMessages.notEmpty,
        vNumber: (v) => !isNaN(v) || validationMessages.number,
        vWalltime: (v) => walltime(v) || validationMessages.walltime,
        vWalltimeChars: (v) =>
            walltimeChars(v) || validationMessages.walltimeChars,
        vInteger: (v) =>
            (Number.isInteger(Number(v)) && !v.toString().includes(".")) ||
            validationMessages.integer,
        vNotNegative: (v) =>
            (!isNaN(v) && v >= 0) || validationMessages.notNegative,
        vNoSpecialChars: (v) =>
            noSpecialChars(v) || validationMessages.noSpecialChars,
        vFilePath: (v) => filePath(v) || validationMessages.filePath,
        vCommaSeparatedList: (v) =>
            commaSeparatedList(v) || validationMessages.commaSeparatedList,
        vNoSpaces: (v) => noSpaces(v) || validationMessages.noSpaces,
        validationMessages
    };
}
