/**
 * Array of unit suffixes for general conversion.
 */
export const CONVERSION_SIZES: string[] = ["", "K", "M", "G", "T", "P"];

/**
 * Array of unit suffixes for memory conversion in bytes.
 */
const CONVERSION_SIZES_MEM: string[] = ["B", "KB", "MB", "GB", "TB", "PB"];

/**
 * Array of unit suffixes for memory conversion in bits.
 */
const CONVERSION_SIZES_MEM_BIT: string[] = ["b", "Kb", "Mb", "Gb", "Tb", "Pb"];

/**
 * Scales a value based on the provided base and returns the scaled value and index.
 *
 * @param value - The value to scale.
 * @param base - The base for scaling (e.g., 1000 or 1024).
 * @returns A tuple where the first element is the scaled value and the second is the index.
 */
const scaleValue = (value: number, base: number): [number, number] => {
    const i = value !== 0 ? Math.floor(Math.log(value) / Math.log(base)) : 0;
    value = Math.round(value / Math.pow(base, i));
    return [value, i];
};

/**
 * Converts a memory size in bytes to a human-readable format.
 *
 * @param bytes - The size in bytes to convert.
 * @param bit - Whether to convert to bits instead of bytes.
 * @param base - The base for conversion (default is 1024).
 * @returns A tuple with the scaled value and its corresponding unit.
 */
export const humanSizeMem = (
    bytes: number,
    bit: boolean = false,
    base: number = 1024
): [number, string] => {
    if (bit) bytes *= 8;
    const [v, i] = scaleValue(bytes, base);
    if (bit) return [v, CONVERSION_SIZES_MEM_BIT[i]];
    return [v, CONVERSION_SIZES_MEM[i]];
};

/**
 * Converts a value to a human-readable format with general unit suffixes.
 *
 * @param value - The value to convert.
 * @param base - The base for conversion (default is 1000).
 * @returns A tuple with the scaled value and its corresponding unit.
 */
export const humanSize = (
    value: number,
    base: number = 1000
): [number, string] => {
    const [v, i] = scaleValue(value, base);
    return [v, CONVERSION_SIZES[i]];
};

/**
 * Converts a value to a fixed human-readable size in a specified unit.
 *
 * @param value - The value to convert.
 * @param unit - The target unit for conversion (e.g., "K", "M").
 * @param base - The base for conversion (default is 1000).
 * @returns The value scaled to the specified unit, fixed to two decimal places.
 */
export const humanSizeFixed = (
    value: number,
    unit: string,
    base: number = 1000
): string | number => {
    if (value === 0) return 0;
    const unitPos = CONVERSION_SIZES.indexOf(unit.toUpperCase());
    for (let j = 0; j < unitPos; j++) {
        value /= base;
    }
    return value.toFixed(2);
};

/**
 * Converts a memory size in bytes to a fixed human-readable size in a specified unit.
 *
 * @param bytes - The size in bytes to convert.
 * @param unit - The target unit for conversion (e.g., "KB", "MB").
 * @param bit - Whether to convert to bits instead of bytes.
 * @param base - The base for conversion (default is 1024).
 * @returns The value scaled to the specified unit, fixed to two decimal places.
 */
export const humanSizeMemFixed = (
    bytes: number,
    unit: string,
    bit: boolean = false,
    base: number = 1024
): string | number => {
    if (bytes === 0) return 0;
    if (bit) bytes *= 8;
    const sizes = bit ? CONVERSION_SIZES_MEM_BIT : CONVERSION_SIZES_MEM;
    const unitPos = sizes.indexOf(unit.toUpperCase());
    for (let j = 0; j < unitPos; j++) {
        bytes /= base;
    }
    return bytes.toFixed(2);
};
