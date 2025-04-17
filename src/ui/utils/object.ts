/**
 * Utility object for managing nested properties in objects.
 */
export const ObjectUtils = {
    /**
     * Retrieves the value of a nested object property by a dot-separated string path.
     * Allows direct access to array indices using dot notation (e.g., "my.custom.path.2.value").
     *
     * @param obj - The object to retrieve the value from.
     * @param path - The dot-separated path to the property.
     * @param defaultValue - The default value to return if the property is not found.
     * @returns The value at the specified path or the default value.
     */
    getByString(
        obj: Record<string, any>,
        path: string,
        defaultValue: any = ""
    ): any {
        return path.split(".").reduce((o, p) => (o ? o[p] : defaultValue), obj);
    },

    /**
     * Sets the value of a nested object property by a dot-separated string path.
     * Allows direct access to array indices using dot notation (e.g., "my.custom.path.2.value").
     *
     * @param obj - The object to set the value in.
     * @param path - The dot-separated path to the property.
     * @param value - The value to set at the specified path.
     */
    setByString(obj: Record<string, any>, path: string, value: any = ""): void {
        if (!path) return;
        const [head, ...rest] = path.split(".");
        if (!obj[head]) obj[head] = {};
        if (!rest.length) obj[head] = value;
        else ObjectUtils.setByString(obj[head], rest.join("."), value);
    },

    /**
     * Creates a nested object structure and sets a value if it does not already exist.
     * Allows direct access to array indices using dot notation (e.g., "my.custom.path.2.value").
     *
     * @param obj - The object to create the structure in.
     * @param path - The dot-separated path to the property.
     * @param value - The value to set at the specified path if it does not already exist.
     */
    createByString(
        obj: Record<string, any>,
        path: string,
        value: any = ""
    ): void {
        const [head, ...rest] = path.split(".");
        if (!(head in obj)) obj[head] = {};
        !rest.length
            ? Object.keys(obj[head]).length
                ? ""
                : (obj[head] = value)
            : ObjectUtils.createByString(obj[head], rest.join("."), value);
    },

    /**
     * Checks if the given value is an object (but not an array or null).
     *
     * @param obj - The value to check.
     * @returns True if the value is an object, false otherwise.
     */
    isObject(obj: any): boolean {
        return typeof obj === "object" && !Array.isArray(obj) && obj !== null;
    }
};
