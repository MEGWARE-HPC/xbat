import type {
    NitroFetchRequest,
    $Fetch,
    AvailableRouterMethod
} from "nitropack";

type HttpMethod =
    | "GET"
    | "POST"
    | "PUT"
    | "DELETE"
    | "PATCH"
    | "HEAD"
    | "OPTIONS"
    | "TRACE"
    | "CONNECT"
    | "get"
    | "post"
    | "put"
    | "delete"
    | "patch"
    | "head"
    | "options"
    | "trace"
    | "connect";

/*
 * Wraps API calls to provide consistent interface and request-related options and data
 */
class FetchFactory {
    private fetch: $Fetch<any, NitroFetchRequest>;

    constructor(fetcher: $Fetch<any, NitroFetchRequest>) {
        this.fetch = fetcher;
    }

    /**
     * The HTTP client is utilized to control the process of making API requests.
     * @param method the HTTP method (GET, POST, ...)
     * @param url the endpoint url
     * @param data the body data
     * @param fetchOptions fetch options
     * @returns
     */
    async call<T>(
        method: HttpMethod,
        url: string,
        data?: object | FormData,
        fetchOptions: {
            responseType?: "json" | "blob" | "text";
            headers?: Record<string, string>;
        } = {}
    ): Promise<T | void> {
        const isFormData = data instanceof FormData;
        let headers: Record<string, string> = fetchOptions.headers || {};
        if (!isFormData) {
            headers = {
                "Content-Type": "application/json",
                ...fetchOptions.headers
            };
        }
        let body: BodyInit | undefined;
        if (isFormData) {
            body = data;
        } else if (data) {
            body = JSON.stringify(data);
        }
        return (
            this.fetch<T>(url, {
                method,
                body,
                headers,
                responseType: fetchOptions.responseType || "json",
                ...fetchOptions
            })
                // error handling done via custom fetch onResponseError
                .catch((error) => {})
        );
    }
}

export default FetchFactory;
