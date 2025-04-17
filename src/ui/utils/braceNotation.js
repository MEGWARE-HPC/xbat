import {
    splitAtIndex,
    splitNumberPrefix,
    getPaddingLength
} from "~/utils/string";

export const isValidBrace = (input) =>
    new RegExp(/([a-zA-Z0-9]+)(\[[0-9,-]+\])?/g).test(input);

export const decodeBraceNotation = (input, sort = true) => {
    if (typeof input != "string") return input;

    if (!input.startsWith("[") && !input.endsWith("]")) input = `[${input}]`;

    //TODO improve/validate regex
    input = input
        .replace(/([a-z]?[A-Z]?\d?\]?)\s*,\s*/g, "$1;")
        .replace(/(\d+);(\d+)/g, "$1,$2")
        .replace(/(\d+);(\d+)/g, "$1,$2");

    const bracedList = input.split(";");
    let result = [];
    for (let entry of bracedList) {
        let entryResult = [];

        const openBrace = entry.indexOf("[");
        const closeBrace = entry.indexOf("]");
        let suffix = "";
        if (entry.length > closeBrace + 1)
            suffix = entry.substr(closeBrace + 1);
        let baseLen;
        if (openBrace !== -1 && closeBrace !== -1 && closeBrace > openBrace) {
            let tmp = entry.split("[");
            const base = tmp[0];
            baseLen = base.length;
            const rangeSet = tmp[1].split("]")[0].split(",");
            for (let range of rangeSet) {
                if (range.includes("-")) {
                    const tmpRange = range.split("-");
                    let start = parseFloat(tmpRange[0]),
                        stop = parseFloat(tmpRange[1]);

                    const paddedLen = Math.max(
                        tmpRange[0].split(".")[0].length,
                        tmpRange[1].split(".")[0].length
                    );

                    if (start > stop) {
                        let tmp = start;
                        start = stop;
                        stop = tmp;
                    }

                    for (let i = start; i <= stop; i += 1) {
                        entryResult.push(
                            `${base}${
                                getPaddingLength(tmpRange[0], "0")
                                    ? "0".repeat(
                                          paddedLen - i.toString().length
                                      ) + i
                                    : i
                            }${suffix}`
                        );
                    }
                } else entryResult.push(`${base}${parseFloat(range)}${suffix}`);
            }
        } else entryResult.push(entry);
        if (sort)
            entryResult = entryResult.sort((a, b) => {
                a = parseFloat(splitNumberPrefix(splitAtIndex(a, baseLen)[1]));
                b = parseFloat(splitNumberPrefix(splitAtIndex(b, baseLen)[1]));
                if (a < b) return -1;
                else if (a > b) return 1;
                return 0;
            });
        result = [...result, ...entryResult];
    }

    return Array.from(new Set(result));
};

/** Converting to brace notation.
 * Function to encode given data to brace notation.
 *
 * @param {string[]|string} param with elements to encode
 * @param {string} delimiter Delimiter
 * @return {string[]} Encoded Elements
 */
export const encodeBraceNotation = (data, delimiter = ",") => {
    if (!Array.isArray(data)) data = [data];

    data = data.map(String); // Convert all elements to string

    let nodeNames = new Set(data);

    let nodesWithNoNumber = [];
    let nodeObjects = [];
    const findDigits = /(\d+)$/; // Adjusted to find numbers at the end

    nodeNames.forEach((node) => {
        const regexRes = findDigits.exec(node);
        if (regexRes === null) nodesWithNoNumber.push(node);
        else
            nodeObjects.push({
                preText: node.substring(0, regexRes.index),
                number: regexRes[0]
            });
    });

    let groups = [];
    while (nodeObjects.length > 0) {
        const tmpElem = nodeObjects.pop();
        const preText = tmpElem.preText;
        let currentGroup = {
            preText: preText,
            number: [tmpElem.number]
        };

        for (let i = nodeObjects.length - 1; i >= 0; i--) {
            if (nodeObjects[i].preText == preText) {
                currentGroup.number.push(nodeObjects[i].number);
                nodeObjects.splice(i, 1);
            }
        }

        currentGroup.number = currentGroup.number.sort(
            (a, b) => Number(a) - Number(b)
        );
        groups.push(currentGroup);
    }

    let braceEncoded = [];
    groups.forEach((elem) => {
        let braceStr = "";
        if (elem.preText) braceStr += elem.preText + "[";
        braceStr += elem.number[0];

        let lastNumber = elem.number[0];
        let minusNeeded = false;
        for (let i = 1; i < elem.number.length; i++) {
            if (Number(lastNumber) + 1 == Number(elem.number[i])) {
                lastNumber = elem.number[i];
                minusNeeded = true;
            } else {
                if (minusNeeded) braceStr += "-" + lastNumber;
                braceStr += delimiter + elem.number[i];
                lastNumber = elem.number[i];
                minusNeeded = false;
            }
        }

        if (minusNeeded) braceStr += "-" + lastNumber;
        if (elem.preText) braceStr += "]";
        braceEncoded.push(braceStr);
    });

    return braceEncoded.concat(nodesWithNoNumber);
};
