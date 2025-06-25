import { isProxy, toRaw } from "vue";
import { stateColors } from "~/utils/colors";

/**
 * Vue inconsistently returns either an object or an array when accessing a ref -
 * function allows access to multiple nested refs while considering this behavior.
 *
 * @param base - The base object or array to start from.
 * @param args - Sequence of keys or indices to traverse.
 * @returns The resolved ref or value.
 */
export function getRefs(base: any, ...args: (string | number)[]): any {
    if (args && args.length) {
        base = base[args.shift() as string | number];
        if (Array.isArray(base)) base = base[0];
        if (base.$refs && args.length) base = getRefs(base.$refs, ...args);
    }
    return base;
}

/**
 * Generates an array of numbers from start to stop with a specified step.
 *
 * @param start - Starting value of the range.
 * @param stop - Stopping value of the range (exclusive).
 * @param step - Step size for the range (default is 1).
 * @returns An array of numbers in the range.
 */
export const range = (start: number, stop: number, step = 1): number[] => {
    const result = [start];
    let current = start + step;
    while (current < stop) {
        result.push(current);
        current += step;
    }
    return result;
};

/**
 * Creates a deep clone of the given object, preserving object references to prevent cycles.
 *
 * @param src - The source object to clone.
 * @param refs - A WeakMap to track references (used internally).
 * @returns A deep clone of the source object.
 */
export const deepClone = function copy<T>(
    src: T,
    refs: WeakMap<object, any> = new WeakMap()
): T {
    if (src === null || typeof src !== "object") return src;

    if (refs.has(src)) return refs.get(src);

    let dest: any;
    if (Array.isArray(src)) {
        dest = new Array(src.length);
        refs.set(src, dest);
        for (let i = 0; i < src.length; i++) dest[i] = copy(src[i], refs);

        for (const propKey of Object.keys(src).slice(src.length))
            dest[propKey] = copy((src as any)[propKey], refs);

        for (const sym of Object.getOwnPropertySymbols(src)) {
            if (Object.prototype.propertyIsEnumerable.call(src, sym))
                dest[sym] = copy((src as any)[sym], refs);
        }
    } else if (typeof (src as any).clone === "function") {
        dest = (src as any).clone(true);
        refs.set(src, dest);
    } else if (src instanceof Date) {
        dest = new Date(src.getTime());
        refs.set(src, dest);
    } else if (src instanceof RegExp) {
        dest = new RegExp(src);
        refs.set(src, dest);
    } else if (src.nodeType && typeof (src as any).cloneNode === "function") {
        dest = (src as any).cloneNode(true);
        refs.set(src, dest);
    } else if (
        src instanceof String ||
        src instanceof Boolean ||
        src instanceof Number
    ) {
        const Ctor = Object.getPrototypeOf(src).constructor;
        dest = new Ctor(src);
        refs.set(src, dest);
    } else {
        dest = Object.create(Object.getPrototypeOf(src));
        refs.set(src, dest);
        for (const propKey in src) {
            if (Object.prototype.hasOwnProperty.call(src, propKey)) {
                dest[propKey] = copy((src as any)[propKey], refs);
            }
        }
        for (const sym of Object.getOwnPropertySymbols(src)) {
            if (Object.prototype.propertyIsEnumerable.call(src, sym)) {
                dest[sym] = copy((src as any)[sym], refs);
            }
        }
    }
    return dest;
};

/**
 * Rounds a number to a specified number of decimal places.
 *
 * @param value - The number to round.
 * @param places - The number of decimal places (default is 2).
 * @returns The rounded number.
 */
export const roundTo = (value: number, places = 2): number => {
    const factor = Math.pow(10, places);
    return Math.round(value * factor) / factor;
};

/**
 * converts a SLURM batch script based on provided configuration.
 *
 * @param jobConfig - An object containing SLURM configuration parameters.
 * @returns A string containing the SLURM batch script.
 */
export const convertSlurmScript = (
    jobConfig: Record<string, string>
): string => {
    let script = "#!/bin/bash\n";
    // Define the order of keys in the SLURM script
    const keysOrder = [
        "job-name",
        "partition",
        "nodes",
        "ntasks",
        "time",
        "output",
        "error"
    ];
    // Add SBATCH directives based on the jobConfig object
    keysOrder.forEach((key) => {
        if (key in jobConfig) {
            script += `#SBATCH --${key}=${jobConfig[key]}\n`;
        }
    });
    // Add the user's custom script part
    if ("script" in jobConfig) {
        script += `${jobConfig.script}`;
    }

    return script;
};
/**
 * Triggers a download of a file with the given name and content.
 *
 * @param name - The name of the file to be downloaded.
 * @param content - The content of the file.
 * @param type - The MIME type of the file (default is "text").
 */
export const download = (
    name: string,
    content: string | object,
    type = "text"
): void => {
    let finalContent: string;
    let fileName: string = name;

    if (typeof content === "object") {
        if ("script" in content) {
            finalContent = convertSlurmScript(
                content as Record<string, string>
            );
        } else {
            finalContent = JSON.stringify(content, null, 2);
        }
        if ("variantName" in content) {
            const variantName = (content as Record<string, any>).variantName;
            if (variantName) {
                fileName = `${variantName}.sh`;
            }
        }
    } else {
        finalContent = content;
    }

    const el = document.createElement("a");
    if (type === "text") {
        el.setAttribute(
            "href",
            "data:text/plain;charset=utf-8," + encodeURIComponent(finalContent)
        );
    } else {
        el.setAttribute("href", finalContent);
    }
    el.setAttribute("download", fileName);
    el.style.display = "none";
    document.body.appendChild(el);
    el.click();
    document.body.removeChild(el);
};

/**
 * Copies the provided text to the clipboard.
 *
 * @param text - The text to copy to the clipboard.
 */
export const copyToClipboard = (text: string | object): void => {
    let textToCopy: string;

    if (typeof text === "object") {
        textToCopy = convertSlurmScript(text as Record<string, string>);
    } else {
        textToCopy = text;
    }

    navigator.clipboard.writeText(textToCopy).catch((err) => {
        console.error("Error copying to clipboard", err);
    });
};
/**
 * Performs a deep equality check between two objects or arrays.
 *
 * @param obj1 - The first object to compare.
 * @param obj2 - The second object to compare.
 * @param excludedKeys - Keys to exclude from comparison.
 * @returns True if the objects are deeply equal, false otherwise.
 */
export const deepEqual = (
    obj1: any,
    obj2: any,
    excludedKeys: string[] = []
): boolean => {
    if (isProxy(obj1)) obj1 = toRaw(obj1);

    if (isProxy(obj2)) obj2 = toRaw(obj2);

    if (obj1 === obj2) return true;

    if (obj1 === null && obj2 === null) return true;

    if ((obj1 === null && obj2 !== null) || (obj1 !== null && obj2 === null))
        return false;

    if (typeof obj1 === "object" && typeof obj2 === "object") {
        const keys1 = Object.keys(obj1).filter(
            (key) => !excludedKeys.includes(key)
        );
        const keys2 = Object.keys(obj2).filter(
            (key) => !excludedKeys.includes(key)
        );

        if (keys1.length !== keys2.length) return false;

        for (const key of keys1) {
            if (!deepEqual(obj1[key], obj2[key], excludedKeys)) return false;
        }
        return true;
    }

    if (Array.isArray(obj1) && Array.isArray(obj2)) {
        if (obj1.length !== obj2.length) return false;

        for (let i = 0; i < obj1.length; i++) {
            if (!deepEqual(obj1[i], obj2[i], excludedKeys)) return false;
        }
        return true;
    }

    return false;
};

/**
 * A collection of comparison operators.
 */
export const operators = {
    gt: (a: number, b: number) => a > b,
    ge: (a: number, b: number) => a >= b,
    lt: (a: number, b: number) => a < b,
    le: (a: number, b: number) => a <= b,
    eq: (a: any, b: any) => a == b,
    ne: (a: any, b: any) => a != b
};

/**
 * Determines the job state based on an array of state strings.
 *
 * @param states - An array of state strings.
 * @returns An object containing the state value and its corresponding color.
 */
export const getJobState = (
    states: string[]
): { value: string; color: string } => {
    let state: string;

    switch (true) {
        case states.includes("COMPLETED"):
            state = "done";
            break;
        case states.includes("RUNNING"):
            state = "running";
            break;
        case states.includes("PENDING"):
            state = "pending";
            break;
        case states.includes("FAILED"):
            state = "failed";
            break;
        case states.includes("TIMEOUT"):
            state = "timeout";
            break;
        case states.includes("DEADLINE"):
            state = "deadline";
            break;
        case states.includes("CANCELLED"):
            state = "cancelled";
            break;
        default:
            state = "unknown";
    }
    return { value: state, color: stateColors[state] };
};
