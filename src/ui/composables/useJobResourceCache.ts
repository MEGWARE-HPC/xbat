type Entry<T> = { revision: number; value: T };
type Request<T> = { revision: number; promise: Promise<T> };

export const useJobResourceCache = <T>(
    fetchValue: (jobId: number) => Promise<T>,
    onUpdate?: (jobId: number, revision: number) => void
) => {
    const entries = shallowReactive<Partial<Record<number, Entry<T>>>>({});
    const pending = shallowReactive<Partial<Record<number, Request<T>>>>({});

    const load = (
        jobId: number,
        revision: number,
        force = false
    ): Promise<T> => {
        const request = pending[jobId];
        if (request?.revision === revision) return request.promise;

        const entry = entries[jobId];
        if (!force && entry?.revision === revision) {
            return Promise.resolve(entry.value);
        }

        const promise: Promise<T> = Promise.resolve()
            .then(() => fetchValue(jobId))
            .then((value) => {
                if (pending[jobId]?.promise === promise) {
                    entries[jobId] = { revision, value };
                    onUpdate?.(jobId, revision);
                }
                return value;
            })
            .finally(() => {
                if (pending[jobId]?.promise === promise) {
                    delete pending[jobId];
                }
            });

        pending[jobId] = { revision, promise };
        return promise;
    };

    return { entries, pending, load };
};
