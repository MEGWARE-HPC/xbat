-- +goose up

--  Use IF NOT EXISTS to avoid errors after failed migrations.
--  Slurm stores job ID in 32-bit unsigned integer.
--  DateTime64(3, 'UTC') is used for millisecond precision (6 for microseconds and 9 for nanoseconds)
--  Device is string as it can be either numerical values or identifiers like "nvme0n1".
--  LowCardinality(String) is used for node, level, and device to optimize storage (only viable when the number of distinct values is smaller than 10.000).
--  Level uses LowCardinality(String) instead of Enum to allow for more flexibility in the future.

--  TODO:
--  - Int64 vs UInt64 for value?
--  - condense float and int tables?
--  - Scale all memory volumes to kB? Use int for volumes etc?
--  - Level as Enum or LowCardinality(String)?
--

CREATE TABLE IF NOT EXISTS template_float (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    value Float64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS template_int (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    value UInt64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS template_device_float (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    device LowCardinality(String),
    value Float64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS template_device_int (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    device LowCardinality(String),
    value UInt64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS template_topology_float (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    thread UInt16,
    core UInt16,
    numa UInt8,
    socket UInt8,
    value Float64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

CREATE TABLE IF NOT EXISTS template_topology_int (
    job_id UInt32,
    node LowCardinality(String),
    level LowCardinality(String),
    thread UInt16,
    core UInt16,
    numa UInt8,
    socket UInt8,
    value UInt64,
    ts DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (job_id, node, level, ts)
PARTITION BY toYYYYMM(ts);

-- CPU

CREATE TABLE IF NOT EXISTS likwid_branch_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_branch_mis_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_branch_mis_ratio AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_clk AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_clk_uncore AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_cpi AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_cpu_temp AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_cycles_wo_exec AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycles_wo_exec_l1d AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycles_wo_exec_l2 AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycles_wo_exec_mem_l AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_flops_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_flops_dp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_flops_avx_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_flops_avx_dp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_flops_avx512_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_flops_avx512_dp AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_instr_branch AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_cycle_stalls AS template_topology_float; -- TODO could also use int but needs code changes

CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_l1d_mis AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_l2_mis AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_mem_l AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_l1d_mis_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_l2_mis_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_cycle_stalls_mem_l_rate AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_scalar_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_scalar_dp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_packed_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_packed_dp AS template_topology_float;

CREATE TABLE IF NOT EXISTS cpu_usage AS template_topology_float;
CREATE TABLE IF NOT EXISTS cpu_user AS template_topology_float;
CREATE TABLE IF NOT EXISTS cpu_system AS template_topology_float;
CREATE TABLE IF NOT EXISTS cpu_iowait AS template_topology_float;
CREATE TABLE IF NOT EXISTS cpu_nice AS template_topology_float;
CREATE TABLE IF NOT EXISTS cpu_virtual AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_vectorization_ratio_sp AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_vectorization_ratio_dp AS template_topology_float;

-- Cache

CREATE TABLE IF NOT EXISTS likwid_l2_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l2d_l_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l2d_e_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_l_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_e_bw AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l2_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l2d_l_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_l_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l2d_e_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_e_vol AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l2_mis_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_mis_rate AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l2_mis_ratio AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_mis_ratio AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l2_req_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_req_rate AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l1i_mis_rate AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l1i_req_ratio AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l1i_stall_rate AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l1i_miss_ratio AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_l3_l_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_l_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_e_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3d_e_vol_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_mem_e_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_mem_e_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_l3_vol AS template_topology_float;

-- Memory

CREATE TABLE IF NOT EXISTS likwid_mem_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_r_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_l_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_w_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_e_bw AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_mem_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_r_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_l_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_w_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_mem_e_vol AS template_topology_float;

CREATE TABLE IF NOT EXISTS mem_usage AS template_float;
CREATE TABLE IF NOT EXISTS mem_swap_usage AS template_float;

CREATE TABLE IF NOT EXISTS mem_used AS template_int;
CREATE TABLE IF NOT EXISTS mem_swap_used AS template_int;
CREATE TABLE IF NOT EXISTS mem_buffers AS template_int;
CREATE TABLE IF NOT EXISTS mem_cached AS template_int;

CREATE TABLE IF NOT EXISTS likwid_l_s_ratio AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_hbm_r_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_hbm_w_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_hbm_bw AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_hbm_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_hbm_r_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_hbm_w_vol AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_upi_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_upi_r_bw AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_upi_t_bw AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_upi_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_upi_r_vol AS template_topology_float;
CREATE TABLE IF NOT EXISTS likwid_upi_t_vol AS template_topology_float;

-- GPU

CREATE TABLE IF NOT EXISTS gpu_clk_sm AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_clk_mem AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_clk_graphics AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_clk_video AS template_device_int;

CREATE TABLE IF NOT EXISTS gpu_mem_fb_usage AS template_device_float;
CREATE TABLE IF NOT EXISTS gpu_mem_bar1_usage AS template_device_float;
CREATE TABLE IF NOT EXISTS gpu_mem_util AS template_device_float;

CREATE TABLE IF NOT EXISTS gpu_mem_fb_used AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_mem_bar1_used AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_mem_fb_free AS template_device_int;
CREATE TABLE IF NOT EXISTS gpu_mem_bar1_free AS template_device_int;

CREATE TABLE IF NOT EXISTS gpu_pstate AS template_device_int;

CREATE TABLE IF NOT EXISTS gpu_util AS template_device_float;
CREATE TABLE IF NOT EXISTS gpu_enc_util AS template_device_float;
CREATE TABLE IF NOT EXISTS gpu_dec_util AS template_device_float;
CREATE TABLE IF NOT EXISTS gpu_mm_util AS template_device_float;

-- Power

CREATE TABLE IF NOT EXISTS likwid_cpu_power AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_core_power AS template_topology_float;

CREATE TABLE IF NOT EXISTS likwid_dram_power AS template_topology_float;

CREATE TABLE IF NOT EXISTS fpga_power AS template_device_float;

CREATE TABLE IF NOT EXISTS gpu_power AS template_device_float;

CREATE TABLE IF NOT EXISTS ipmi_power_system AS template_int;

-- Disk

CREATE TABLE IF NOT EXISTS disk_r_bw AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_w_bw AS template_device_float;

CREATE TABLE IF NOT EXISTS disk_rqm AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_rrqm AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_wrqm AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_drqm AS template_device_float;

CREATE TABLE IF NOT EXISTS disk_r_req_s AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_w_req_s AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_d_req_s AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_f_req_s AS template_device_float;

CREATE TABLE IF NOT EXISTS disk_areq_sz AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_rareq_sz AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_wareq_sz AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_dareq_sz AS template_device_float;

CREATE TABLE IF NOT EXISTS disk_util AS template_device_float;

CREATE TABLE IF NOT EXISTS disk_await AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_r_await AS template_device_float;
CREATE TABLE IF NOT EXISTS disk_w_await AS template_device_float;

-- Interconnect

CREATE TABLE IF NOT EXISTS eth_rcv_bw AS template_float;
CREATE TABLE IF NOT EXISTS eth_xmit_bw AS template_float;

CREATE TABLE IF NOT EXISTS eth_rcv_pkg AS template_float;
CREATE TABLE IF NOT EXISTS eth_xmit_pkg AS template_float;

CREATE TABLE IF NOT EXISTS ib_rcv_bw AS template_float;
CREATE TABLE IF NOT EXISTS ib_xmit_bw AS template_float;

CREATE TABLE IF NOT EXISTS ib_rcv_pkg AS template_float;
CREATE TABLE IF NOT EXISTS ib_xmit_pkg AS template_float;



-- +goose down

-- Dropping and recreating the entire database would break goose migration due to missing goose_db_version table.

DROP TABLE IF EXISTS xbat.cpu_iowait;
DROP TABLE IF EXISTS xbat.cpu_nice;
DROP TABLE IF EXISTS xbat.cpu_system;
DROP TABLE IF EXISTS xbat.cpu_user;
DROP TABLE IF EXISTS xbat.cpu_virtual;
DROP TABLE IF EXISTS xbat.cpu_usage;
DROP TABLE IF EXISTS xbat.disk_areq_sz;
DROP TABLE IF EXISTS xbat.disk_await;
DROP TABLE IF EXISTS xbat.disk_d_req_s;
DROP TABLE IF EXISTS xbat.disk_dareq_sz;
DROP TABLE IF EXISTS xbat.disk_drqm;
DROP TABLE IF EXISTS xbat.disk_f_req_s;
DROP TABLE IF EXISTS xbat.disk_r_await;
DROP TABLE IF EXISTS xbat.disk_r_bw;
DROP TABLE IF EXISTS xbat.disk_r_req_s;
DROP TABLE IF EXISTS xbat.disk_rareq_sz;
DROP TABLE IF EXISTS xbat.disk_rqm;
DROP TABLE IF EXISTS xbat.disk_rrqm;
DROP TABLE IF EXISTS xbat.disk_util;
DROP TABLE IF EXISTS xbat.disk_w_await;
DROP TABLE IF EXISTS xbat.disk_w_bw;
DROP TABLE IF EXISTS xbat.disk_w_req_s;
DROP TABLE IF EXISTS xbat.disk_wareq_sz;
DROP TABLE IF EXISTS xbat.disk_wrqm;
DROP TABLE IF EXISTS xbat.eth_rcv_bw;
DROP TABLE IF EXISTS xbat.eth_rcv_pkg;
DROP TABLE IF EXISTS xbat.eth_xmit_bw;
DROP TABLE IF EXISTS xbat.eth_xmit_pkg;
DROP TABLE IF EXISTS xbat.fpga_power;
DROP TABLE IF EXISTS xbat.gpu_clk_graphics;
DROP TABLE IF EXISTS xbat.gpu_clk_mem;
DROP TABLE IF EXISTS xbat.gpu_clk_sm;
DROP TABLE IF EXISTS xbat.gpu_clk_video;
DROP TABLE IF EXISTS xbat.gpu_dec_util;
DROP TABLE IF EXISTS xbat.gpu_enc_util;
DROP TABLE IF EXISTS xbat.gpu_mem_bar1_free;
DROP TABLE IF EXISTS xbat.gpu_mem_bar1_usage;
DROP TABLE IF EXISTS xbat.gpu_mem_bar1_used;
DROP TABLE IF EXISTS xbat.gpu_mem_fb_free;
DROP TABLE IF EXISTS xbat.gpu_mem_fb_usage;
DROP TABLE IF EXISTS xbat.gpu_mem_fb_used;
DROP TABLE IF EXISTS xbat.gpu_mem_util;
DROP TABLE IF EXISTS xbat.gpu_mm_util;
DROP TABLE IF EXISTS xbat.gpu_power;
DROP TABLE IF EXISTS xbat.gpu_pstate;
DROP TABLE IF EXISTS xbat.gpu_util;
DROP TABLE IF EXISTS xbat.ib_rcv_bw;
DROP TABLE IF EXISTS xbat.ib_rcv_pkg;
DROP TABLE IF EXISTS xbat.ib_xmit_bw;
DROP TABLE IF EXISTS xbat.ib_xmit_pkg;
DROP TABLE IF EXISTS xbat.ipmi_power_system;
DROP TABLE IF EXISTS xbat.likwid_branch_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_branch_mis_ratio;
DROP TABLE IF EXISTS xbat.likwid_branch_rate;
DROP TABLE IF EXISTS xbat.likwid_clk;
DROP TABLE IF EXISTS xbat.likwid_clk_uncore;
DROP TABLE IF EXISTS xbat.likwid_core_power;
DROP TABLE IF EXISTS xbat.likwid_cpi;
DROP TABLE IF EXISTS xbat.likwid_cpu_temp;
DROP TABLE IF EXISTS xbat.likwid_cpu_power;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_l1d_mis;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_l1d_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_l2_mis;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_l2_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_mem_l;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_mem_l_rate;
DROP TABLE IF EXISTS xbat.likwid_cycle_stalls_rate;
DROP TABLE IF EXISTS xbat.likwid_cycles_wo_exec;
DROP TABLE IF EXISTS xbat.likwid_cycles_wo_exec_l1d;
DROP TABLE IF EXISTS xbat.likwid_cycles_wo_exec_l2;
DROP TABLE IF EXISTS xbat.likwid_cycles_wo_exec_mem_l;
DROP TABLE IF EXISTS xbat.likwid_dram_power;
DROP TABLE IF EXISTS xbat.likwid_flops_avx512_dp;
DROP TABLE IF EXISTS xbat.likwid_flops_avx512_sp;
DROP TABLE IF EXISTS xbat.likwid_flops_avx_dp;
DROP TABLE IF EXISTS xbat.likwid_flops_avx_sp;
DROP TABLE IF EXISTS xbat.likwid_flops_dp;
DROP TABLE IF EXISTS xbat.likwid_flops_sp;
DROP TABLE IF EXISTS xbat.likwid_hbm_bw;
DROP TABLE IF EXISTS xbat.likwid_hbm_r_bw;
DROP TABLE IF EXISTS xbat.likwid_hbm_r_vol;
DROP TABLE IF EXISTS xbat.likwid_hbm_vol;
DROP TABLE IF EXISTS xbat.likwid_hbm_w_bw;
DROP TABLE IF EXISTS xbat.likwid_hbm_w_vol;
DROP TABLE IF EXISTS xbat.likwid_instr_branch;
DROP TABLE IF EXISTS xbat.likwid_l1i_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_l1i_miss_ratio;
DROP TABLE IF EXISTS xbat.likwid_l1i_req_ratio;
DROP TABLE IF EXISTS xbat.likwid_l1i_stall_rate;
DROP TABLE IF EXISTS xbat.likwid_l2_bw;
DROP TABLE IF EXISTS xbat.likwid_l2_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_l2_mis_ratio;
DROP TABLE IF EXISTS xbat.likwid_l2_req_rate;
DROP TABLE IF EXISTS xbat.likwid_l2_vol;
DROP TABLE IF EXISTS xbat.likwid_l2d_e_bw;
DROP TABLE IF EXISTS xbat.likwid_l2d_e_vol;
DROP TABLE IF EXISTS xbat.likwid_l2d_l_bw;
DROP TABLE IF EXISTS xbat.likwid_l2d_l_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_e_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_e_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_l_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_l_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_mis_rate;
DROP TABLE IF EXISTS xbat.likwid_l3_mis_ratio;
DROP TABLE IF EXISTS xbat.likwid_l3_req_rate;
DROP TABLE IF EXISTS xbat.likwid_l3_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_l_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_l_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_e_bw;
DROP TABLE IF EXISTS xbat.likwid_l3d_e_vol_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_mem_e_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_mem_e_vol;
DROP TABLE IF EXISTS xbat.likwid_l3_bw;
DROP TABLE IF EXISTS xbat.likwid_l3_vol;
DROP TABLE IF EXISTS xbat.likwid_l_s_ratio;
DROP TABLE IF EXISTS xbat.likwid_mem_bw;
DROP TABLE IF EXISTS xbat.likwid_mem_e_bw;
DROP TABLE IF EXISTS xbat.likwid_mem_e_vol;
DROP TABLE IF EXISTS xbat.likwid_mem_l_bw;
DROP TABLE IF EXISTS xbat.likwid_mem_l_vol;
DROP TABLE IF EXISTS xbat.likwid_mem_r_bw;
DROP TABLE IF EXISTS xbat.likwid_mem_r_vol;
DROP TABLE IF EXISTS xbat.likwid_mem_vol;
DROP TABLE IF EXISTS xbat.likwid_mem_w_bw;
DROP TABLE IF EXISTS xbat.likwid_mem_w_vol;
DROP TABLE IF EXISTS xbat.likwid_packed_dp;
DROP TABLE IF EXISTS xbat.likwid_packed_sp;
DROP TABLE IF EXISTS xbat.likwid_scalar_dp;
DROP TABLE IF EXISTS xbat.likwid_scalar_sp;
DROP TABLE IF EXISTS xbat.likwid_upi_bw;
DROP TABLE IF EXISTS xbat.likwid_upi_r_bw;
DROP TABLE IF EXISTS xbat.likwid_upi_r_vol;
DROP TABLE IF EXISTS xbat.likwid_upi_t_bw;
DROP TABLE IF EXISTS xbat.likwid_upi_t_vol;
DROP TABLE IF EXISTS xbat.likwid_upi_vol;
DROP TABLE IF EXISTS xbat.likwid_vectorization_ratio_dp;
DROP TABLE IF EXISTS xbat.likwid_vectorization_ratio_sp;
DROP TABLE IF EXISTS xbat.mem_buffers;
DROP TABLE IF EXISTS xbat.mem_cached;
DROP TABLE IF EXISTS xbat.mem_swap_usage;
DROP TABLE IF EXISTS xbat.mem_swap_used;
DROP TABLE IF EXISTS xbat.mem_usage;
DROP TABLE IF EXISTS xbat.mem_used;
DROP TABLE IF EXISTS xbat.template_device_float;
DROP TABLE IF EXISTS xbat.template_device_int;
DROP TABLE IF EXISTS xbat.template_float;
DROP TABLE IF EXISTS xbat.template_int;
DROP TABLE IF EXISTS xbat.template_topology_float;
DROP TABLE IF EXISTS xbat.template_topology_int;

