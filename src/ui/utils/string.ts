/**
 * Replaces trademark symbols in a string with their corresponding HTML entities.
 *
 * @param s - The string to process.
 * @returns The processed string with trademark symbols replaced, or the original value if it is not a string.
 */
export const replaceTrademark = (s: string): string => {
    if (!s) return "";
    return s && typeof s === "string"
        ? s.replace(/\(TM\)/g, "&trade;").replace(/\(R\)/g, "&reg;")
        : s;
};

/**
 * Splits a string at a specified index.
 *
 * @param x - The string to split.
 * @param index - The index at which to split the string.
 * @returns An array containing two substrings: the part before the index and the part after the index.
 */
export const splitAtIndex = (x: string, index: number): [string, string] => [
    x.slice(0, index),
    x.slice(index)
];

/**
 * Splits a string into a prefix of non-numeric characters and a suffix of numeric characters.
 *
 * @param str - The string to split.
 * @returns An array containing the prefix and suffix. If no numeric suffix exists, the original string is returned as the only element.
 */
export const splitNumberPrefix = (str: string): [string, string?] => {
    let lastIndex = 0;
    for (let index = str.length - 1; index >= 0; index--) {
        if (isNaN(Number(str.charAt(index)))) {
            lastIndex = index;
        } else {
            break;
        }
    }
    if (lastIndex > 0) {
        return [str.substring(0, lastIndex), str.substring(lastIndex)];
    }
    return [str];
};

/**
 * Calculates the length of leading padding in a string.
 *
 * @param str - The string to examine.
 * @param pad - The padding character or substring.
 * @returns The length of the leading padding.
 */
export const getPaddingLength = (str: string, pad: string): number => {
    let padLen = 0;
    while (str.startsWith(pad)) {
        str = str.slice(pad.length);
        padLen += pad.length;
    }
    return padLen;
};

/**
 * Extracts the first sequence of digits found in a given string and returns it as a number.
 *
 * @param str - The string from which to extract the number.
 * @returns The extracted number, or NaN if no digits are found.
 */
export const extractNumber = (str: string): number => {
    const match = str.match(/\d+/);
    return match ? Number(match[0]) : NaN;
};
