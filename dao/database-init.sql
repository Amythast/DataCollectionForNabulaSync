-- create database
DROP DATABASE IF EXISTS nebula_data_collection;
CREATE DATABASE nebula_data_collection
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

-- create table
DROP TABLE IF EXISTS `nebula_live_stream_records`;
CREATE TABLE `nebula_live_stream_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `anchor_name` varchar(255) NOT NULL COMMENT '主播名',
  `platform` varchar(255) NOT NULL COMMENT '平台名',
  `category` varchar(255) NOT NULL COMMENT '直播类型',
  `live_date` DATETIME NOT NULL COMMENT '直播日期',
  `age` int(11) DEFAULT NULL COMMENT '主播年龄',
  `gender` varchar(255) DEFAULT NULL COMMENT '主播性别',
  `live_url` varchar(255) DEFAULT NULL COMMENT '直播间链接',
  `live_slice` varchar(255) NOT NULL COMMENT '直播片段名',
  `live_stream_file` varchar(255) NULL COMMENT '直播间视频/音频原文件路径索引',
  `live_stream_transform` JSON NULL COMMENT '直播间信息转json',
  `live_danmu_file` varchar(255) NULL COMMENT '直播间弹幕文件路径索引',
  `live_danmu_transform` JSON NULL COMMENT '直播间弹幕信息转json',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `nebula_finetune_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `anchor_name` varchar(255) NOT NULL COMMENT '主播名',
  `platform` varchar(255) NOT NULL COMMENT '平台名',
  `category` varchar(255) NOT NULL COMMENT '直播类型',
  `live_date` DATETIME NOT NULL COMMENT '直播日期',
  `target_platform` varchar(255) NOT NULL COMMENT '数据目标平台名',
  `data` JSON NOT NULL COMMENT 'fintune dao',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `nebula_live_stream_target` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `live_id` varchar(255) NOT NULL COMMENT '直播间id',
  `anchor_name` varchar(255) NOT NULL COMMENT '主播名',
  `category` varchar(255) NOT NULL COMMENT '直播类型',
  `platform` varchar(255) NOT NULL COMMENT '平台名',
  `url` varchar(255) NOT NULL COMMENT '直播间url',
  `need_record` TINYINT(1) DEFAULT 1 COMMENT '是否需要录制，1 需要, 0 不需要',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;