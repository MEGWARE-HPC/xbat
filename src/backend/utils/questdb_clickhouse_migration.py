import csv
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Literal, Optional
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

MAX_WORKER_COUNT = 8  # Limit the number of parallel workers to avoid overwhelming the system


def _find_runNr_folders(extract_folder: Path) -> list[Path]:
    """
    Recursively find all runNr directories (numeric folder names with benchmarks.json).
    
    Args:
        extract_folder: Path to search within
        
    Returns:
        List of paths to runNr folders
    """
    runNr_folders = []

    for item in extract_folder.rglob("*"):
        if not item.is_dir():
            continue

        # Check if folder name is numeric and contains benchmarks.json
        if item.name.isdigit() and (item / "benchmarks.json").exists():
            runNr_folders.append(item)

    return runNr_folders


def _convert_timestamp(timestamp_str: str) -> str:
    """
    Convert ISO timestamp to ClickHouse format.
    
    Args:
        timestamp_str: ISO format timestamp like "2026-02-24T11:53:20.000000Z"
        
    Returns:
        ClickHouse format timestamp like "2026-02-24 11:53:20.000"
    """
    # Remove quotes if present
    timestamp_str = timestamp_str.strip('"')
    # Convert ISO format to ClickHouse format
    # From: 2026-02-24T11:53:20.000000Z
    # To: 2026-02-24 11:53:20.000
    timestamp_str = timestamp_str.replace('T', ' ')
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1]
    # Keep only 3 decimal places for milliseconds
    if '.' in timestamp_str:
        parts = timestamp_str.split('.')
        timestamp_str = parts[0] + '.' + parts[1][:3]
    return timestamp_str


def _format_csv_value(value: str,
                      is_numeric_column: bool,
                      is_timestamp: bool,
                      is_integer: bool = False) -> str:
    """
    Format a CSV value according to ClickHouse requirements.
    
    Args:
        value: The value to format
        is_numeric_column: Whether this is a numeric column
        is_timestamp: Whether this is a timestamp column
        
    Returns:
        Formatted value
    """
    value = value.strip('"')

    if value == '':
        return ''

    if is_timestamp:
        return f'"{_convert_timestamp(value)}"'

    if is_numeric_column:
        try:
            # If this should be an integer, convert float to int
            if is_integer:
                float_val = float(value)
                int_val = int(float_val)
                return str(int_val)
            # Check if it's an integer
            elif '.' not in value:
                int(value)
                return value
            else:
                float(value)
                return value
        except ValueError:
            # If conversion fails, treat as string
            return f'"{value}"'

    # Everything else is a string
    return f'"{value}"'


async def _get_table_schemas() -> dict:
    """
    Query ClickHouse to get the schema for all tables.
    
    Returns:
        Dictionary mapping table names to their column types
    """
    from shared import clickhouse as cdb

    clickhouse = cdb.ClickHouse()
    clickhouse.setup()

    table_names = await clickhouse.get_table_names(exclude_templates=True)

    schemas = {}
    for table_name in table_names:
        try:
            result = await clickhouse.execute_query(
                f"DESCRIBE TABLE {table_name}")
            column_types = {}
            for row in result:
                col_name = row.get('name', '')
                col_type = row.get('type', '')
                column_types[col_name] = col_type
            schemas[table_name] = column_types
        except Exception:
            pass

    return schemas


def _is_integer_type(col_type: str) -> bool:
    """
    Check if a ClickHouse column type is an integer type.
    """
    int_types = [
        'UInt8', 'UInt16', 'UInt32', 'UInt64', 'Int8', 'Int16', 'Int32',
        'Int64'
    ]
    return any(col_type.startswith(int_type) for int_type in int_types)


def _get_column_info(headers: list[str],
                     table_name: str = None,
                     table_schemas: dict = None) -> dict:
    """
    Determine which columns are numeric based on header names.
    
    Args:
        headers: List of column headers
        
    Returns:
        Dictionary with column indices as keys and info as values
    """
    # Columns that should be treated as numbers (no quotes)
    numeric_columns = {'jobId', 'core', 'numa', 'socket', 'thread', 'value'}

    # Timestamp columns need special formatting
    timestamp_columns = {'timestamp'}

    # All other columns (node, device, level, etc.) will be treated as strings (with quotes)

    column_info = {}
    for idx, header in enumerate(headers):
        header = header.strip('"')

        # Check if value column should be integer based on schema
        is_integer = False
        if header == 'value' and table_name and table_schemas:
            schema = table_schemas.get(table_name, {})
            col_type = schema.get('value', '')
            is_integer = _is_integer_type(col_type)

        column_info[idx] = {
            'name': header,
            'is_numeric': header in numeric_columns,
            'is_timestamp': header in timestamp_columns,
            'is_integer': is_integer
        }

    return column_info


def _convert_csv_file(csv_path: Path,
                      jobs_folder: Path,
                      table_schemas: dict = None) -> None:
    """
    Convert a QuestDB CSV file to ClickHouse format and split by jobId.
    
    Args:
        csv_path: Path to the CSV file to convert
        jobs_folder: Path to the jobs folder where jobId subfolders will be created
        table_schemas: Dictionary of table schemas from ClickHouse
    """
    # Read the CSV file and group by jobId
    job_data = defaultdict(list)

    # ClickHouse column order
    clickhouse_order = [
        'jobId', 'node', 'level', 'device', 'core', 'numa', 'socket', 'thread',
        'value', 'timestamp'
    ]

    # Get table name from CSV filename (without extension)
    table_name = csv_path.stem

    with open(csv_path, 'r', encoding='utf-8',
              buffering=1024 * 1024) as f:  # 1MB buffer
        reader = csv.reader(f)

        # Read header
        header = next(reader, None)
        if not header:
            return

        # Check if this is a QuestDB format file (has header starting with "jobId")
        if not header[0].strip('"').startswith('jobId'):
            # Not a QuestDB format file, skip
            return

        # Clean headers and create index mapping
        cleaned_headers = [h.strip('"') for h in header]

        # Get column information with schema info
        column_info = _get_column_info(cleaned_headers, table_name,
                                       table_schemas)

        # Find jobId column index
        jobId_idx = None
        for idx, col_name in enumerate(cleaned_headers):
            if col_name == 'jobId':
                jobId_idx = idx
                break

        if jobId_idx is None:
            return

        # Create mapping from header name to index in original data
        header_to_idx = {name: idx for idx, name in enumerate(cleaned_headers)}

        # Filter ClickHouse order to only include columns present in source
        active_columns = [
            col for col in clickhouse_order if col in header_to_idx
        ]

        # Pre-compute column indices and info for faster lookup
        column_indices = [
            header_to_idx[col_name] for col_name in active_columns
        ]
        column_infos = [column_info[idx] for idx in column_indices]

        # Process each row
        for row in reader:
            if not row or len(row) == 0:
                continue

            # Get jobId
            jobId = row[jobId_idx].strip('"')

            # Reorder and format the row according to ClickHouse column order (only present columns)
            formatted_row = []
            for idx, col_info in zip(column_indices, column_infos):
                value = row[idx]
                formatted_value = _format_csv_value(
                    value, col_info['is_numeric'], col_info['is_timestamp'],
                    col_info.get('is_integer', False))
                formatted_row.append(formatted_value)

            job_data[jobId].append(','.join(formatted_row))

    # Write split CSV files for each jobId with buffering
    for jobId, rows in job_data.items():
        job_folder = jobs_folder / jobId
        job_folder.mkdir(parents=True, exist_ok=True)

        output_path = job_folder / csv_path.name
        with open(output_path, 'w', encoding='utf-8',
                  buffering=1024 * 1024) as f:  # 1MB buffer
            f.write('\n'.join(rows) + '\n')  # Single write operation


def detect_format(
        extract_folder: Path) -> Literal["questdb", "clickhouse", "unknown"]:
    """
    Detect whether the export folder is in QuestDB or ClickHouse format.
    
    Args:
        extract_folder: Path to the extracted folder containing runNr subdirectories
        
    Returns:
        "questdb" if old format detected
        "clickhouse" if new format detected
        "unknown" if format cannot be determined
    """
    # Find all runNr directories recursively
    runNr_folders = _find_runNr_folders(extract_folder)

    for runNr_folder in runNr_folders:
        # Check for jobs subfolder (ClickHouse format)
        jobs_folder = runNr_folder / "jobs"
        if jobs_folder.exists() and jobs_folder.is_dir():
            return "clickhouse"

        # Check for CSV files directly in runNr folder (QuestDB format)
        csv_files = list(runNr_folder.glob("*.csv"))
        if csv_files:
            return "questdb"

    return "unknown"


def _convert_csv_file_wrapper(args):
    """Wrapper function for multiprocessing."""
    csv_path, jobs_folder, table_schemas = args
    _convert_csv_file(csv_path, jobs_folder, table_schemas)
    return csv_path.name


async def convert_to_clickhouse(extract_folder: Path) -> Optional[Path]:
    """
    Convert QuestDB format export to ClickHouse format.
    
    Creates a new folder with a UUID, restructures the content into ClickHouse format,
    and removes the original QuestDB folder structure.
    
    Args:
        extract_folder: Path to the extracted folder containing runNr subdirectories
        
    Returns:
        Path to the new converted folder, or None if no conversion was needed
        
    Raises:
        ValueError: If the folder is already in ClickHouse format
        FileNotFoundError: If the extract_folder does not exist
    """
    if not extract_folder.exists():
        raise FileNotFoundError(
            f"Extract folder does not exist: {extract_folder}")

    format_type = detect_format(extract_folder)

    if format_type == "clickhouse":
        raise ValueError("Folder is already in ClickHouse format")

    if format_type == "unknown":
        # No CSV files found, nothing to convert
        return None

    # Get table schemas from ClickHouse
    try:
        table_schemas = await _get_table_schemas()
    except Exception as e:
        print(f"Warning: Could not fetch table schemas from ClickHouse: {e}")
        table_schemas = {}

    # Create new folder with UUID in the same parent directory
    new_uuid = str(uuid.uuid4())
    new_folder = extract_folder.parent / new_uuid
    new_folder.mkdir(parents=True, exist_ok=True)

    # Find all runNr directories recursively
    runNr_folders = _find_runNr_folders(extract_folder)

    # Process each runNr directory
    for runNr_folder in runNr_folders:
        runNr = runNr_folder.name

        # Create runNr folder in new structure
        new_runNr_folder = new_folder / runNr
        new_runNr_folder.mkdir(parents=True, exist_ok=True)

        # Copy all JSON files
        for json_file in runNr_folder.glob("*.json"):
            shutil.copy2(json_file, new_runNr_folder / json_file.name)

        # Find all CSV files in the runNr folder
        csv_files = list(runNr_folder.glob("*.csv"))

        if csv_files:
            # Create jobs folder in new structure
            jobs_folder = new_runNr_folder / "jobs"
            jobs_folder.mkdir(exist_ok=True)

            # Parallelize CSV file conversion
            max_workers = min(
                min(multiprocessing.cpu_count(), MAX_WORKER_COUNT),
                len(csv_files))
            conversion_args = [(csv_file, jobs_folder, table_schemas)
                               for csv_file in csv_files]

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(_convert_csv_file_wrapper, args)
                    for args in conversion_args
                ]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        # Log error but continue with other files
                        print(f"Error converting CSV file: {e}")

    # Remove the old QuestDB folder structure
    shutil.rmtree(extract_folder)

    return new_folder
