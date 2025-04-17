import FetchFactory from "../factory";
import type { GraphQuery, GraphRawData } from "~/types/graph";

class MeasurementModule extends FetchFactory {
    private RESOURCE = "/measurements";

    async get(query: GraphQuery) {
        return this.call<GraphRawData>(
            "GET",
            `${this.RESOURCE}/${query.jobIds[0]}?group=${query.group}&metric=${query.metric}&level=${query.level}&node=${query.node}&deciles=${query.deciles}`,
            undefined // body
        );
    }
}

export default MeasurementModule;
