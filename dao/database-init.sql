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
  `live_address` varchar(255) DEFAULT NULL COMMENT '直播间链接',
  `live_stream_file` LONGBLOB NOT NULL COMMENT '直播间视频/音频原文件',
  `live_stream_transform` JSON NOT NULL COMMENT '直播间信息转json',
  `live_danmu_file` LONGBLOB NOT NULL COMMENT '直播间弹幕文件',
  `live_danmu_transform` JSON NOT NULL COMMENT '直播间弹幕信息转json',
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