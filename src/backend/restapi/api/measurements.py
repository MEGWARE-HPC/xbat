import itertools
import csv
import re
import logging
import asyncio
import numpy as np
from io import StringIO
from flask import request, Response, jsonify
from pathlib import Path
from shared import httpErrors
from shared import questdb as qdb
from shared.mongodb import MongoDB
from shared.configuration import get_logger
from shared.date import iso8601_to_datetime
from shared.files import read_file_to_dict
from shared.helpers import dict_get_key
from shared.size import human_size, human_size_mem, human_size_mem_fixed, human_size_fixed
from backend.restapi.valkey import Valkey

questdb = qdb.QuestDB()
mongodb = MongoDB()
valkey = Valkey()

logger = logging.getLogger(get_logger())

METRICS_PATH = Path().absolute() / "restapi" / "metrics.json"
METRICS = read_file_to_dict(METRICS_PATH)
MAX_QUERY_COUNT = 8

LEVEL_MAPPING = {
    "thread": 0,
    "core": 1,
    "numa": 2,
    "socket": 3,
    "device": 4,
    "node": 5,
    "job": 6
}

CONVERTABLE_UNITS = ["byte", "uops", "flops"]


def get_metric_tables():
    tables = []
    for group in METRICS:
        for metric in METRICS[group]:
            for table in METRICS[group][metric]["metrics"]:
                tables.append(table)
    return list(set(tables))


METRIC_TABLES = get_metric_tables()


# TODO sorting
def next_lower_aggregate(aggregates, level):
    for aggregate in aggregates:
        if LEVEL_MAPPING[aggregate] < LEVEL_MAPPING[level]:
            return aggregate
    return None


def get_hightest_level(levels):
    maxLevel = max([LEVEL_MAPPING[l] for l in levels])
    return list(LEVEL_MAPPING.keys())[list(
        LEVEL_MAPPING.values()).index(maxLevel)]


def calculate_interval(records):
    if len(records) < 2: return 5.0
    start = records[0]["timestamp"]
    for entry in records:
        if entry["timestamp"] > start:
            return (entry["timestamp"] - start).total_seconds()

    return 5.0


def filter_interval(records, capture_start, capture_end):
    """
    Filters out all records that are not within the specified timestamps.

    :param records: measurement records
    :param capture_start: starting timestamp
    :param capture_end: end timestamp
    :return: filtered list
    """

    if not len(records):
        return []

    filtered = []
    capture_start = capture_start.replace(
        tzinfo=None) if capture_start is not None else None
    capture_end = capture_end.replace(
        tzinfo=None) if capture_end is not None else None

    for entry in records:
        if capture_start is not None and entry["timestamp"] < capture_start:
            continue
        if capture_end is not None and entry["timestamp"] > capture_end:
            continue
        filtered.append(entry)

    if not len(filtered):
        logger.debug("No records left after filtering for capture timeframe")
    return filtered


def aggregate(records, level, type):
    """
    Aggregates all records on the specified level as sum or average.

    :param records: measurement records
    :param level: aggregation level
    :param type: sum or average
    :return: aggregated values
    """

    aggregates = {}
    for entry in records:
        aggregate_by = entry[level] if level in entry else None

        if aggregate_by is None and level != "job": continue

        if aggregate_by is None:
            aggregate_by = "job"

        if not (aggregate_by in aggregates):
            aggregates[aggregate_by] = {}

        ts = entry["timestamp"].isoformat()

        if not (ts in aggregates[aggregate_by]):
            aggregates[aggregate_by][ts] = []

        if entry["value"] is not None:
            aggregates[aggregate_by][ts].append(entry["value"])

    # calculate averages
    for entry in aggregates:
        for interval in aggregates[entry]:

            # filter zero values to not distort average
            # this is required as LIKWID sometimes reports NaN values on unused (inactive) cores which we substitute with 0
            filtered = [v for v in aggregates[entry][interval] if v != 0]

            data_points = len(filtered)
            value = sum(filtered)

            aggregates[entry][
                interval] = value if type == "sum" or data_points == 0 else value / data_points

    return aggregates


def calculate_statistics(values):
    return {
        "min": np.round(np.min(values), 2),
        "max": np.round(np.max(values), 2),
        "std": np.round(np.std(values), 2),
        "avg": np.round(np.mean(values), 2),
        "var": np.round(np.var(values), 2),
        "median": np.round(np.median(values), 2),
        "sum": np.round(np.sum(values), 2)
    }


def _getDeciles(values):
    values.sort()
    return list(
        [round(np.percentile(values, dec), 2) for dec in range(0, 101, 10)])


def _create_query(jobId: int,
                  metric_table: str,
                  level: str,
                  filter_level: str,
                  node: str | None = None,
                  type: str = "avg",
                  capture_start=None,
                  capture_end=None) -> str:

    value_calculation = "SUM(value)"

    if type == "avg":
        # filter zero values to not distort average  (e.g. for cpu frequency)
        # this is required as LIKWID sometimes reports NaN values on unused (inactive) cores which we substitute with 0
        value_calculation = "COALESCE(AVG(CASE WHEN value != 0 THEN value END), 0)"

    filters = [f"jobId='{jobId}'", f"level='{filter_level}'"]
    if level != "job" and node:
        filters.append(f"node='{node}'")
    if capture_start:
        filters.append(f"timestamp >= '{capture_start.isoformat()}'")
    if capture_end:
        filters.append(f"timestamp <= '{capture_end.isoformat()}'")

    columns = [f"{value_calculation} as val", "timestamp"]
    groups = ["timestamp"]

    if level != "job":
        columns.insert(0, level)
        groups.insert(0, level)

    query = f"SELECT {', '.join(columns)} FROM {metric_table} WHERE {' and '.join(filters)} GROUP BY {', '.join(groups)} ORDER BY timestamp"

    return query


def _transform_query_result(result, level):
    values = {}
    for entry in result:
        key = entry[level] if level != "job" else "job"
        if not key in values:
            values[key] = []
        values[key].append(entry["val"])
    return values


def _sanitize_uid(s):
    return re.sub(r'[\s\[\]/\(\)]', '_', s).lower()


async def calculate_metrics(jobId, group, metric, level, node, deciles):
    """
    Retrieves and calculates metrics based on the provided parameters.

    :param jobId: ID of job
    :param group: group of metric
    :param metric: metric name
    :param level: aggregation level
    :param node: node name
    :param deciles: apply deciles

    :return: list of all measurements for specified metric
    """
    if not jobId or not (group in METRICS) or not (metric in METRICS[group]):
        raise httpErrors.BadRequest()

    # questdb = await get_questdb()

    # retrieve capture interval for job
    job = mongodb.getOne("jobs", {"jobId": jobId})

    if job is None:
        raise httpErrors.NotFound()

    capture_start = job["captureStart"] if "captureStart" in job else None
    capture_end = job["captureEnd"] if "captureEnd" in job else None

    # backwards compatibility
    capture_start = iso8601_to_datetime(capture_start) if isinstance(
        capture_start, str) else capture_start
    capture_end = iso8601_to_datetime(capture_end) if isinstance(
        capture_end, str) else capture_end

    metricMeta = METRICS[group][metric]

    traces = []

    # TODO check that requested level is not smaller than minimum level!

    metric_tables = metricMeta["metrics"].keys()

    queries = []
    # check which aggregation levels are available
    for metric_table in metric_tables:

        parts = [
            f"SELECT DISTINCT level FROM {metric_table} WHERE job_id='{jobId}'"
        ]
        if level != "job" and node:
            parts.append(f"AND node='{node}'")
        if capture_start:
            parts.append(f"AND timestamp >= '{capture_start.isoformat()}'")
        if capture_end:
            parts.append(f"AND timestamp <= '{capture_end.isoformat()}'")
        queries.append(" ".join(parts))

    all_levels = await questdb.execute_queries(queries)

    queries = []
    available_metric_tables = []

    # build query based on aggregation levels
    # use separate list for available metric tables to prevent result mismatch on missing tables/entries
    for idx, metric_table in enumerate(metric_tables):
        # TODO check for x validity
        preaggregated_levels = [x["level"] for x in all_levels[idx]]
        if not len(preaggregated_levels):
            continue

        filter_level = level
        if not (level in preaggregated_levels):
            # get next lower preaggregated level
            filter_level = next_lower_aggregate(preaggregated_levels, level)

        aggregation_type = metricMeta[
            "aggregation"] if "aggregation" in metricMeta else "avg"

        queries.append(
            _create_query(jobId, metric_table, level, filter_level, node,
                          aggregation_type, capture_start, capture_end))

        available_metric_tables.append(metric_table)

    if not len(queries):
        logger.debug("Unable to find entries for %s", metric)
        return {"traces": [], "statistics": {}}

    all_records = await questdb.execute_queries(queries)

    unit = metricMeta["unit"] if "unit" in metricMeta else ""

    variant_name = job["configuration"]["jobscript"]["variantName"] if not (
        "cli" in job) or not job["cli"] else None

    # calculate metrics
    for idx, metric_table in enumerate(available_metric_tables):

        records = all_records[idx]

        records = filter_interval(records, capture_start, capture_end)

        if not len(records):
            continue

        aggregation_type = metricMeta[
            "aggregation"] if "aggregation" in metricMeta else "avg"

        interval = calculate_interval(records)
        aggregates = _transform_query_result(records, level)

        timestamps = [x["timestamp"] for x in records]
        start = min(timestamps)
        stop = max(timestamps)

        stacked = False
        if "stacked" in metricMeta and metricMeta["stacked"]:
            if "stack_min_level" in metricMeta:
                stacked = LEVEL_MAPPING[level] >= LEVEL_MAPPING[
                    metricMeta["stack_min_level"]]
            else:
                stacked = True

        metricEntry = metricMeta["metrics"][metric_table]

        raw_name = metricEntry["name"] if isinstance(
            metricEntry, dict) and "name" in metricEntry else metricEntry

        description = metricEntry["description"] if isinstance(
            metricEntry, dict) else metricEntry,

        is_deciles = deciles and (level == 'thread' or level == 'core')

        trace_base = {
            "jobId": jobId,
            "group": group,
            "description": description,
            "metric": metric,
            "level": level,
            "node": node,
            "start": start,
            "stop": stop,
            "interval": interval,
            "unit": unit,
            "rawUnit": unit,
            "stacked": False,
            "table": metric_table,
            "variant": variant_name,
            "iteration": job["iteration"],
            "deciles": False
        }

        if is_deciles:
            combined_values = list(zip(*aggregates.values()))
            decile_values = []
            for ts in combined_values:
                decile_values.append(_getDeciles(list(ts)))

            for dec in range(1, 11):
                values = [v[dec] for v in decile_values]

                name = f"Decile {dec} {raw_name}"

                traces.append({
                    **trace_base, "name":
                    name,
                    "rawName":
                    raw_name,
                    "legend_group":
                    name,
                    "values":
                    values,
                    "id":
                    dec,
                    "deciles":
                    True,
                    "uid":
                    _sanitize_uid(
                        f"{trace_base['table']}-{jobId}-{level}-{name}")
                })

        else:
            for key in aggregates.keys():
                values = aggregates[key]

                if not len(values):
                    continue

                name = raw_name
                identifier = key

                if len(aggregates.keys()) > 1:
                    identifier = f"{level[0]}{key}"

                if identifier != key:
                    name = f"{name} {identifier}"

                legend_group = f"{level[0]}{key}"
                if LEVEL_MAPPING[level] >= LEVEL_MAPPING["node"]:
                    legend_group = name

                traces.append({
                    **trace_base, "name":
                    name,
                    "rawName":
                    raw_name,
                    "legend_group":
                    legend_group,
                    "values":
                    values,
                    "stacked":
                    stacked,
                    "id":
                    identifier,
                    "uid":
                    _sanitize_uid(
                        f"{trace_base['table']}-{jobId}-{level}-{name}")
                })

    # adjust unit and calculate statistics
    per_second = unit.endswith("/s")
    conversion_unit = None

    if any(map(unit.lower().__contains__, CONVERTABLE_UNITS)):
        # calculate median of all non-zero values to establish a sensible unit for conversion
        allValues = []
        for res in traces:
            allValues.extend(res["values"])

        if len(allValues):
            is_byte = "byte" in unit
            non_zero_values = [v for v in allValues if v != 0]

            if len(non_zero_values):
                max_value = np.max(non_zero_values)

                [_, u] = human_size_mem(max_value) if is_byte else human_size(
                    max_value)

                if is_byte:
                    unit = f"{u}/s" if per_second else u
                else:
                    unit = f"{u.upper()}{unit.upper().replace('/S', '')}{'/s' if per_second else ''}"
                conversion_unit = u

    values_by_metric = {}
    # apply conversion and calculate statistics for each trace
    for entry in traces:
        if conversion_unit:
            entry["rawValues"] = entry["values"]
            entry["values"] = [
                human_size_mem_fixed(v, conversion_unit) if "byte"
                in entry["unit"] else human_size_fixed(v, conversion_unit)
                for v in entry["values"]
            ]
        entry["statistics"] = calculate_statistics(entry["values"])
        entry["unit"] = unit

        values_by_metric.setdefault(entry["rawName"],
                                    []).append(entry["values"])

    # calculate statistics across all traces of same type - only used when level < node
    statistics = {}
    for key, values in values_by_metric.items():
        combined = list(zip(*values))
        statistics[key] = {
            "values": {
                "min": [np.min(i) for i in combined],
                "max": [np.max(i) for i in combined],
                "avg": [np.mean(i) for i in combined]
            },
            "general":
            calculate_statistics(list(itertools.chain.from_iterable(values)))
        }

    return {"traces": traces, "statistics": statistics}


async def get_measurements(jobId,
                           group="",
                           metric="",
                           level="",
                           node="",
                           deciles=False):
    """
    Returns calculated metrics based on filters.

    :param jobId: ID of job
    :param group: group of metric
    :param metric: metric name
    :param level: aggregation level
    :param node: node
    """
    valkey_key = get_request_uri()
    cache = valkey.get(valkey_key)

    if cache is not None:
        return cache, 200

    result = await calculate_metrics(jobId, group, metric, level, node,
                                     deciles)

    if result is None: raise httpErrors.NotFound()

    # prevent caching of unfinished jobs
    if jobs_cacheable([jobId]):
        valkey.set(valkey_key, result)

    return result, 200


async def export_json(jobId,
                      group="",
                      metric="",
                      level="",
                      node="",
                      deciles=False):
    result = await calculate_metrics(jobId, group, metric, level, node,
                                     deciles)
    if result is None: raise httpErrors.NotFound()
    json_content = jsonify(result).data
    filename = f"{jobId}_{group}.json"
    return Response(
        json_content,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename={filename}"})


async def export_csv(jobId,
                     group="",
                     metric="",
                     level="",
                     node="",
                     deciles=False):
    if not group and not metric:
        if not level:
            # Temporarily set the level to job, if level is not given either
            level = "job"

        all_csv_content = []
        for group_key in METRICS:
            for metric_key in METRICS[group_key]:
                result = await calculate_metrics(jobId, group_key, metric_key,
                                                 level, node, deciles)
                if result is None or not result["traces"]:
                    continue

                csv_content = generate_csv(result)
                all_csv_content.append(csv_content)

        if not all_csv_content:
            raise httpErrors.NotFound()

        final_csv_content = "\n".join(all_csv_content)
        filename = f"{jobId}_all_metrics_{level}.csv"

    else:
        if not level:
            raise httpErrors.BadRequest(
                "Level is required for single metric export")
        result = await calculate_metrics(jobId, group, metric, level, node,
                                         deciles)
        if result is None: raise httpErrors.NotFound()

        final_csv_content = generate_csv(result)
        filename = f"{jobId}_{group}_{metric}_{level}.csv"

    return Response(
        final_csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"})


def generate_csv(result):
    output = StringIO()
    try:
        value_key = 'rawValues' if 'rawValues' in result["traces"][
            0] else 'values'
        if value_key not in result["traces"][0]:
            return ""
        fieldnames = ['jobId', 'group', 'metric', 'trace'] + [
            f'interval {i}' for i in range(len(result["traces"][0][value_key]))
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in result["traces"]:
            row_data = {
                'jobId': item['jobId'],
                'group': item['group'],
                'metric': item['metric'],
                'trace': item['name']
            }
            row_data.update({
                f'interval {i}': value
                for i, value in enumerate(item[value_key])
            })
            writer.writerow(row_data)
        csv_content = output.getvalue()
    finally:
        output.close()

    return csv_content


async def _get_statistics_rows(jobId, group="", metric="", level="", node=""):
    """
    Get statistics rows.
    """
    if not jobId:
        raise httpErrors.BadRequest("jobId is required")

    result, _ = await get_measurements(jobId=jobId,
                                       group=group,
                                       metric=metric,
                                       level=level,
                                       node=node,
                                       deciles=False)

    traces = result.get("traces", [])
    if not traces:
        raise httpErrors.NotFound("No statistics data available")

    rows = []
    for trace in traces:
        stats = trace.get("statistics", {})
        rows.append({
            "jobId": trace.get("jobId", ""),
            "group": trace.get("group", ""),
            "metric": trace.get("metric", ""),
            "rawName": trace.get("rawName", ""),
            "unit": trace.get("unit", ""),
            "min": stats.get("min", ""),
            "max": stats.get("max", ""),
            "avg": stats.get("avg", ""),
            "sum": stats.get("sum", ""),
            "median": stats.get("median", ""),
            "std": stats.get("std", ""),
            "var": stats.get("var", "")
        })

    return rows


async def export_statistics(
    jobId,
    group="",
    metric="",
    level="",
    node="",
):
    """
    Export statistics (min, max, avg, sum, median, std, var).
    """
    rows = await _get_statistics_rows(
        jobId=jobId,
        group=group,
        metric=metric,
        level=level,
        node=node,
    )
    return jsonify(rows), 200


async def export_statistics_csv(jobId, group="", metric="", level="", node=""):
    """
    Export statistics (min, max, avg, sum, median, std, var) as CSV.
    """
    rows = await _get_statistics_rows(
        jobId=jobId,
        group=group,
        metric=metric,
        level=level,
        node=node,
    )

    output = StringIO()
    try:
        fieldnames = [
            "jobId", "group", "metric", "rawName", "unit", "min", "max", "avg",
            "sum", "median", "std", "var"
        ]
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

        csv_content = output.getvalue()
    finally:
        output.close()

    level_part = level or "job"
    if group and metric:
        filename = f"{jobId}_{group}_{metric}_{level_part}_statistics.csv"
    else:
        filename = f"{jobId}_all_statistics_{level_part}.csv"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


async def calculate_energy(jobId):
    """
    Calculates energy usage metrics for a given job.

    Total energy consumption is an estimate based on the sum of all subsystems excluding core power and the system power itself.
    This is necessary as, depending on the platform, system power does not include certain subsystems like for example GPU.

    :param jobId: ID of job
    """

    result = {}
    energy_metrics = [
        "CPU Power", "Core Power", "DRAM Power", "FPGA Power", "GPU Power",
        "System Power"
    ]

    tasks = [
        calculate_metrics(jobId, "energy", energy_metric, "job", "", False)
        for energy_metric in energy_metrics
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for energy_metric, power_json in zip(energy_metrics, responses):
        key = energy_metric.split()[0].lower()
        try:
            if "traces" in power_json and len(power_json["traces"]) > 0:
                interval = power_json["traces"][0]["interval"] / 3600 / 1000
                values = power_json["traces"][0]["values"]
                energy_usage = round(sum(values) * interval, 3)
            else:
                energy_usage = None

        except Exception as e:
            logger.error(f"Error processing {energy_metric}: {e}")
            energy_usage = None

        result[key] = energy_usage

    return result, 200


def get_request_uri():
    uri = request.path
    if (request.query_string):
        uri += f"?{request.query_string.decode()}"
    return uri


def jobs_cacheable(jobIds):
    cacheable = True
    job_data = mongodb.getMany("jobs", {"jobId": {"$in": jobIds}})

    for job in job_data:
        if not ("jobInfo" in job) or (
                job["jobInfo"] is None) or not ("jobState" in job["jobInfo"]):
            cacheable = False
            break
        state = job["jobInfo"]["jobState"]
        cacheable_job_states = ["FAILED", "COMPLETED", "CANCELLED", "TIMEOUT"]
        if not any(cacheable_state in state
                   for cacheable_state in cacheable_job_states):
            cacheable = False
            break
    return cacheable


async def get_available_metrics(jobId=None, jobIds=None, intersect=False):
    """
    Check all available metrics and nodes by querying each table for a single entry containing the specified jobId.
    Assume homogeneous nodes and thus same metrics available for all of them.
    Use INTERSECT ALL to combine to single query, however this requires checking for the existence of each table first.
    Otherwise INTERSECT ALL will fail if any table is not present.

    :param jobId: ID of job
    :param jobIds: List of job IDs
    """

    # do not cache default metrics to prevent invalid cache entries after update
    if not jobId and not jobIds:
        return METRICS, 200

    valkey_key = get_request_uri()
    cache = valkey.get(valkey_key)

    if cache is not None:
        return cache, 200

    jobIds = jobIds if jobIds else [jobId]

    # prevent caching of unfinished jobs
    cacheable = jobs_cacheable(jobIds)

    available_tables = []

    # check which tables are currently present (may change during runtime as additional may be added)
    res = await questdb.execute_query("tables()")

    # support for older questdb versions
    table_column = 'table_name' if len(
        res) and 'table_name' in res[0] else 'name'

    for table in res:
        available_tables.append(table[table_column])

    result = []
    for jobId in jobIds:
        job = mongodb.getOne("jobs", {"jobId": jobId})
        raw_cs = job.get("captureStart") if job else None
        raw_ce = job.get("captureEnd") if job else None
        capture_start = iso8601_to_datetime(raw_cs) if isinstance(
            raw_cs, str) else raw_cs
        capture_end = iso8601_to_datetime(raw_ce) if isinstance(
            raw_ce, str) else raw_ce

        tableQueries = []
        # query all present tables that are also part of the metric specification
        for table in METRIC_TABLES:
            if table not in available_tables:
                continue

            time_filters = []
            if capture_start:
                time_filters.append(
                    f"timestamp >= '{capture_start.isoformat()}'")
            if capture_end:
                time_filters.append(
                    f"timestamp <= '{capture_end.isoformat()}'")
            time_clause = (" AND " +
                           " AND ".join(time_filters)) if time_filters else ""

            tableQueries.append(
                f"SELECT DISTINCT '{table}' as table_name, node, level "
                f"FROM {table} "
                f"WHERE job_id='{jobId}'{time_clause}")
        # instead of using single large query split into multiple smaller queries due to problems with questdb sometimes only returning partial results for very large queries
        queries = []
        for i in range(0, len(tableQueries), MAX_QUERY_COUNT):
            chunk = tableQueries[i:i + MAX_QUERY_COUNT]
            if len(chunk) == 1:
                queries.append(chunk[0])
            else:
                queries.append(" UNION ALL ".join(chunk))

        logger.debug(f"QUERIES: {queries}")

        jobResult = await questdb.execute_queries(queries)

        result.append([x for xs in jobResult for x in xs])

    aggregated = {}

    for idx, tables in enumerate(result):
        available = {}
        nodes = []

        available_job_tables = {}
        # aggregate all tables containing measurements for <jobId>
        for table in tables:
            if not table or not ("table_name" in table): continue
            if table["table_name"] not in available_job_tables:
                available_job_tables[table["table_name"]] = {"levels": []}
            available_job_tables[table["table_name"]]["levels"].append(
                table["level"])
            if table["node"] not in nodes:
                nodes.append(table["node"])

        # create custom metrics.json specific to <jobId>
        for group in METRICS:
            for metricName in METRICS[group]:
                metricInfo = METRICS[group][metricName]
                if not len(metricInfo["metrics"]): continue
                available_metrics = []
                available_levels = []
                for table in metricInfo["metrics"]:
                    if table not in available_job_tables:
                        continue

                    available_metrics.append(table)

                    for level in available_job_tables[table]["levels"]:
                        available_levels.append(level)

                if len(available_metrics):
                    if group not in available:
                        available[group] = {}
                    available_min_level = min(
                        [LEVEL_MAPPING[x] for x in available_levels])
                    available[group][metricName] = {
                        **metricInfo, "metrics": {
                            k: v
                            for k, v in metricInfo["metrics"].items()
                        },
                        "level_min":
                        dict_get_key(LEVEL_MAPPING, available_min_level)
                    }
        job_id = jobIds[idx]
        aggregated[job_id] = ({
            "metrics": available,
            "nodes": nodes,
            "jobId": job_id
        })

    if len(jobIds) == 1:
        response = aggregated[jobIds[0]]
        response["missing"] = [] if response["metrics"] else [jobIds[0]]
        if cacheable:
            valkey.set(valkey_key, response)
        return response, 200

    if not intersect:
        if cacheable:
            valkey.set(valkey_key, aggregated)
        return aggregated, 200

    # skip empty jobs (invalid jobId, no measurements or broken database connection)
    skipped_jobs = [
        x["jobId"] for x in aggregated.values() if not bool(x["metrics"])
    ]

    aggregated_metrics = [
        x["metrics"] for x in aggregated.values()
        if not (x["jobId"] in skipped_jobs)
    ]

    if not len(aggregated_metrics):
        response = {"metrics": {}, "nodes": [], "missing": skipped_jobs}
        if cacheable:
            valkey.set(valkey_key, response)
        return response, 200

    # check that metrics are available in all jobs
    groups = set.intersection(*map(set, [x.keys()
                                         for x in aggregated_metrics]))
    intersected_metrics = dict.fromkeys(groups)

    for group in groups:
        metricSets = set.intersection(
            *map(set, [x[group].keys() for x in aggregated_metrics]))

        intersected_metrics[group] = dict.fromkeys(metricSets)

        # TODO check which metrics/tables are present in all jobs (currently not used)
        for metricSet in metricSets:

            # set common level_min by find highest level_min as upward aggregation is always possible
            level_min = list(
                set([
                    x[group][metricSet]["level_min"]
                    for x in aggregated_metrics
                ]))

            if len(level_min) > 1:
                level_min = get_hightest_level(level_min)
            else:
                level_min = level_min[0]

            if intersected_metrics[group][metricSet] is None:
                intersected_metrics[group][metricSet] = {
                    **aggregated_metrics[0][group][metricSet], "level_min":
                    level_min
                }

    response = {
        "metrics": intersected_metrics,
        "nodes": [],
        "missing": skipped_jobs
    }
    if cacheable:
        valkey.set(valkey_key, response)

    return response, 200


async def get_roofline(jobIds=None):
    """
    Returns Roofline metrics for jobIds

    Each job returns Peak Memory_bandwidth
    and Peak, Median, Average of:
    operational_intensity (SP/DP)
    """

    ids_args = request.args.get("jobIds") if jobIds is None else jobIds
    if not ids_args:
        return {"error": "jobIds is required"}, 400
    job_Ids = [
        s.strip()
        for s in (ids_args.split(",")
                  if isinstance(ids_args, str) else [str(x) for x in ids_args])
        if s.strip()
    ]

    valkey_key = get_request_uri()
    cache = valkey.get(valkey_key)
    if cache is not None:
        return cache, 200

    def _safe_float(v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            try:
                return float(s)
            except Exception:
                return None
        return None

    def _pick_trace(traces, want_name):
        for t in traces or []:
            if t.get("name") == want_name:
                return t
        for t in traces or []:
            if t.get("rawName") == want_name:
                return t
        return None

    def _pick_raw_values(trace):
        if not trace:
            return []
        vals = trace.get("rawValues")
        if not isinstance(vals, list):
            vals = trace.get("values", [])
        out = []
        for v in vals:
            fv = _safe_float(v)
            if fv is not None:
                out.append(fv)
        return out

    def _pick_volume_raw_values(trace):
        if not trace:
            return []
        if isinstance(trace.get("rawValues"), list):
            return _pick_raw_values(trace)
        vals = _pick_raw_values(trace)
        unit = (trace.get("unit") or "").strip().lower()
        if unit in ("gb", "gbytes", "gbyte", "gib", "gibibyte"):
            return [v * 1e9 for v in vals]
        return vals

    def _get_interval(*traces):
        for tr in traces:
            if not tr:
                continue
            iv = _safe_float(tr.get("interval"))
            if iv is not None and iv > 0.0:
                return iv
        return None

    def _get_stats(flop_series, bytes_series, interval_s):
        if not flop_series or not bytes_series:
            zero = {"operational_intensity": 0.0, "performance": 0.0}
            return {
                "peak": zero,
                "median": zero,
                "average": zero,
                "total": zero
            }

        n = min(len(flop_series), len(bytes_series))
        if not interval_s or interval_s <= 0.0:
            zero = {"operational_intensity": 0.0, "performance": 0.0}
            return {
                "peak": zero,
                "median": zero,
                "average": zero,
                "total": zero
            }

        points = []
        total_flops = 0.0
        total_bytes = 0.0

        for i in range(n):
            f = flop_series[i]  # FLOPS/s
            byt = bytes_series[i]  # bytes per interval
            if f and byt and f > 0.0 and byt > 0.0:
                y = f / 1e9  # GFLOPS/s
                flops_i = f * interval_s  # FLOPs in interval
                x = flops_i / byt  # FLOPs/byte
                points.append((x, y))
                total_flops += flops_i
                total_bytes += byt

        if not points:
            zero = {"operational_intensity": 0.0, "performance": 0.0}
            return {
                "peak": zero,
                "median": zero,
                "average": zero,
                "total": zero
            }

        xs = np.fromiter((p[0] for p in points), dtype=float)
        ys = np.fromiter((p[1] for p in points), dtype=float)

        # peak by y
        peak_idx = int(np.argmax(ys))
        peak = {
            "operational_intensity": float(xs[peak_idx]),
            "performance": float(ys[peak_idx])
        }

        # median by y (closest to median(y))
        y_med = float(np.median(ys))
        med_idx = int(np.argmin(np.abs(ys - y_med)))
        median = {
            "operational_intensity": float(xs[med_idx]),
            "performance": float(ys[med_idx])
        }

        # average (component-wise)
        average = {
            "operational_intensity": float(np.mean(xs)),
            "performance": float(np.mean(ys))
        }

        # aggregate / total (global OI & global Performance)
        if total_bytes > 0.0:
            total_time = interval_s * len(points)  # seconds
            global_oi = total_flops / total_bytes  # FLOPs/byte
            global_perf = (total_flops / total_time) / 1e9  # GFLOPS/s
            aggregate = {
                "operational_intensity": float(global_oi),
                "performance": float(global_perf)
            }
        else:
            aggregate = {
                "operational_intensity": float(np.mean(xs)),
                "performance": float(np.mean(ys))
            }

        return {
            "peak": peak,
            "median": median,
            "average": average,
            "total": aggregate
        }

    data, missing = {}, []

    for job_Id in job_Ids:
        try:
            jobId = int(job_Id)
        except ValueError:
            missing.append(job_Id)
            continue

        try:
            cpu_res = await calculate_metrics(jobId, "cpu", "FLOPS", "job", "",
                                              False)
            cpu_traces = cpu_res.get("traces", []) if isinstance(
                cpu_res, dict) else []
            sp_trace = _pick_trace(cpu_traces, "SP")
            dp_trace = _pick_trace(cpu_traces, "DP")
            sp_flops = _pick_raw_values(sp_trace)
            dp_flops = _pick_raw_values(dp_trace)

            if not sp_flops and not dp_flops:
                missing.append(job_Id)
        except Exception as e:
            logger.error("roofline_punkt: cpu FLOPS failed for job %s: %s",
                         job_Id, e)
            data[job_Id] = {"points": {"sp": {}, "dp": {}}}
            missing.append(job_Id)
            continue

        try:
            mem_res = await calculate_metrics(jobId, "memory", "Data Volume",
                                              "job", "", False)
            mem_traces = mem_res.get("traces", []) if isinstance(
                mem_res, dict) else []
            mem_total_trace = _pick_trace(mem_traces, "total")
            mem_bytes = _pick_volume_raw_values(mem_total_trace)
        except Exception as e:
            logger.error(
                "roofline_punkt: memory Data Volume failed for job %s: %s",
                job_Id, e)
            mem_total_trace = None
            mem_bytes = []

        interval_s = _get_interval(sp_trace, dp_trace, mem_total_trace)

        sp_pts4 = _get_stats(sp_flops, mem_bytes, interval_s)
        dp_pts4 = _get_stats(dp_flops, mem_bytes, interval_s)

        data[job_Id] = {"sp": sp_pts4, "dp": dp_pts4}

    response = {"data": data}
    if missing:
        response["missing"] = sorted(set(missing))

    try:
        numeric_ids = [int(x) for x in job_Ids if x.isdigit()]
        if numeric_ids and jobs_cacheable(numeric_ids):
            valkey.set(valkey_key, response)
    except Exception:
        pass

    return response, 200
