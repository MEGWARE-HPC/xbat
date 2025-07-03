export default function useValidators() {
    return {
        walltime(v) {
            if (
                !/^(\d+-\d{1,2}(:\d{1,2}(:\d{1,2})?)?|\d{1,2}(:\d{1,2}(:\d{1,2})?)?)$/.test(
                    v || ""
                )
            )
                return false;
            // TODO check that hours are < 24 and minutes/seconds < 60
            return true;
        },
        walltimeChars(v) {
            return /^[\d:-]*$/.test(v || "");
        },
        noSpecialChars(v) {
            return !/[!@#$%^&*(),.?":{}|<>\\']/g.test(v || "");
        },
        filePath(v) {
            return /^[^\0]+$/.test(v || "");
        },
        commaSeparatedList(v) {
            return /^([a-zA-Z0-9_\-\[\]]*)(,[a-zA-Z0-9_\-\[\]]*)*$/.test(
                v || ""
            );
        },
        noSpaces(v) {
            return !/\s/g.test(v || "");
        }
    };
}
