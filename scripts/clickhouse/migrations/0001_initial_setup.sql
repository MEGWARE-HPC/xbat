-- +goose up
CREATE TABLE xbat.my_first_table
(
    user_id UInt32,
    message String,
    timestamp DateTime,
    metric Float32
)
ENGINE = MergeTree()
PRIMARY KEY (user_id, timestamp);

-- +goose down
DROP TABLE xbat.my_first_table;