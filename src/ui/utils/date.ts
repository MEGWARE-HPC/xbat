/**
 * Sanitizes and formats a date string into the format "YYYY-MM-DD HH:mm:ss".
 *
 * @param d - The input date string to sanitize. If null or undefined, an empty string is returned.
 * @returns The sanitized and formatted date string in "YYYY-MM-DD HH:mm:ss" format.
 */
export const sanitizeDate = (d: string | null | undefined): string => {
    if (!d) return "";
    const date = new Date(Date.parse(d));
    return `${date.getFullYear()}-${("0" + (date.getMonth() + 1)).slice(-2)}-${(
        "0" + date.getDate()
    ).slice(-2)} ${("0" + date.getHours()).slice(-2)}:${(
        "0" + date.getMinutes()
    ).slice(-2)}:${("0" + date.getSeconds()).slice(-2)}`;
};

/**
 * Converts seconds into a formatted string in the format "DD HH:mm:ss" or "HH:mm:ss".
 *
 * @param secs - The total seconds to convert.
 * @param alwaysShowDays - A boolean flag indicating whether to always display days, even if 0.
 * @returns A string representing the duration in "DD HH:mm:ss" or "HH:mm:ss" format.
 */
export const toDDHHMMSS = (
    secs: number,
    alwaysShowDays: boolean = false
): string => {
    const secondsPerDay = 86400; // Number of seconds in a day
    const days = Math.floor(secs / secondsPerDay); // Calculate the number of full days

    const timeString = new Date((secs % secondsPerDay) * 1000)
        .toISOString()
        .substr(11, 8);

    // If days are present or alwaysShowDays is true, prepend the days to the time string
    return `${
        days > 0 || (days === 0 && alwaysShowDays)
            ? `${days < 10 ? "0" : ""}${days} `
            : ""
    }${timeString}`;
};

export const calculateRunTime = (startTimeStr, endTimeStr) => {
    const startTime = new Date(startTimeStr);
    if (endTimeStr) {
        const endTime = new Date(endTimeStr);
        const diff = endTime - startTime;
        const hours = Math.floor(
            (diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
        );
        const formatHours = hours.toString().padStart(2, "0");
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const formatMinutes = minutes.toString().padStart(2, "0");
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        const formatSeconds = seconds.toString().padStart(2, "0");

        return `${formatHours}:${formatMinutes}:${formatSeconds} (${
            diff / 1000
        }s)`;
    } else {
        return "N/A";
    }
};
