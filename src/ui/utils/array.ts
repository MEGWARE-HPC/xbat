/**
 * Utility object for managing arrays.
 */
export const ArrayUtils = {
    /**
     * Compares two arrays for equality.
     *
     * @param arr1 - The first array to compare.
     * @param arr2 - The second array to compare.
     * @returns True if the arrays are equal, false otherwise.
     */
    isEqual(arr1: any[], arr2: any[]): boolean {
        return JSON.stringify(arr1) === JSON.stringify(arr2);
    },

    /**
     * Calculates the average of the array elements.
     *
     * @param arr - The array of numbers.
     * @returns The average of the array elements.
     */
    average(arr: number[]): number {
        return arr.length ? arr.reduce((p, c) => p + c, 0) / arr.length : 0;
    },

    /**
     * Calculates the median of the array elements.
     *
     * @param arr - The array of numbers.
     * @returns The median of the array elements.
     */
    median(arr: number[]): number {
        const sorted = [...arr].sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);
        return sorted.length % 2 === 0
            ? (sorted[middle - 1] + sorted[middle]) / 2
            : sorted[middle];
    },

    /**
     * Calculates the standard deviation of the array elements.
     *
     * @param arr - The array of numbers.
     * @returns The standard deviation of the array elements.
     */
    stdDev(arr: number[]): number {
        if (!arr.length) return 0;
        const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
        return Math.sqrt(
            arr.map((x) => Math.pow(x - mean, 2)).reduce((a, b) => a + b, 0) /
                arr.length
        );
    },

    /**
     * Calculates the sum of the array elements.
     *
     * @param arr - The array of numbers.
     * @returns The sum of the array elements.
     */
    sum(arr: number[]): number {
        return arr.reduce((a, b) => a + b, 0);
    },

    /**
     * Adds a unique item to an array.
     *
     * @param arr - The array to which the item will be added.
     * @param item - The item to add to the array.
     * @returns True if the item was added, false if it was already present.
     */
    pushUnique<T>(arr: T[], item: T): boolean {
        if (arr.includes(item)) return false;
        arr.push(item);
        return true;
    },

    /**
     * Removes an item by value from an array in place.
     *
     * @param arr - The array from which the item will be removed.
     * @param value - The value to remove from the array.
     * @returns The same array with the item removed.
     */
    popValue<T>(arr: T[], value: T): T[] {
        let index = arr.indexOf(value);
        if (index !== -1) arr.splice(index, 1);
        return arr;
    },

    /**
     * Removes duplicate items from an array.
     *
     * @param arr - The array from which duplicates will be removed.
     * @returns A new array with duplicates removed.
     */
    filterDuplicates<T>(arr: T[]): T[] {
        return [...new Set(arr)];
    },

    /**
     * Splits an array into chunks of a specified size.
     *
     * @param arr - The array to split into chunks.
     * @param n - The size of each chunk.
     * @returns An array of chunks.
     */
    chunks<T>(arr: T[], n: number): T[][] {
        const result: T[][] = [];
        for (let i = 0; i < arr.length; i += n) {
            result.push(arr.slice(i, i + n));
        }
        return result;
    }
};
