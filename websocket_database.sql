-- Adminer 4.8.1 MySQL 10.6.9-MariaDB-1 dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

DROP TABLE IF EXISTS `cooling_states`;
CREATE TABLE `cooling_states` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` varchar(64) NOT NULL,
  `temp_device_id` int(64) unsigned NOT NULL,
  `cooling_temp` int(64) unsigned NOT NULL,
  `power_rate` int(64) unsigned NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `temp_device_id` (`temp_device_id`),
  CONSTRAINT `cooling_states_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `cooling_states_ibfk_2` FOREIGN KEY (`temp_device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;

INSERT INTO `cooling_states` (`id`, `device_id`, `state_name`, `state_value`, `temp_device_id`, `cooling_temp`, `power_rate`, `device_group_function`) VALUES
(1,	12,	'cooling_fan_1',	'true',	7,	20,	0,	'cooling'),
(2,	7,	'cooling_1',	'',	7,	20,	0,	'cooling');

DROP TABLE IF EXISTS `devices`;
CREATE TABLE `devices` (
  `device_id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_address_name` varchar(64) NOT NULL,
  `address` int(64) unsigned NOT NULL,
  `device_name` varchar(64) NOT NULL,
  `device_type` varchar(64) NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`device_id`),
  UNIQUE KEY `address` (`address`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb3;

INSERT INTO `devices` (`device_id`, `device_address_name`, `address`, `device_name`, `device_type`, `device_group_function`) VALUES
(1,	'cooling_pump_1_address',	512,	'cooling_pump_1',	'pump',	'cooling'),
(2,	'gas_valve_1_address',	513,	'gas_valve_1',	'valve',	'gas'),
(3,	'feed_pump_1_address',	514,	'feed_pump_1',	'pump',	'feed'),
(4,	'heating_mantle_1_address',	524,	'heating_mantle_1',	'heating_mantle',	'heating'),
(5,	'temp_heating_mantle_1_address',	1,	'temp_heating_mantle_1',	'thermo_element',	'measuring'),
(6,	'temp_pre_heating_1_address',	2,	'temp_pre_heating_1',	'thermo_element',	'measuring'),
(7,	'temp_coolant_1_address',	3,	'temp_coolant_1',	'thermo_element',	'measuring'),
(8,	'pre_heating_mantle_1_address',	525,	'pre_heating_mantle_1',	'heating_mantle',	'heating'),
(9,	'temp_pre_heating_mantle_1_address',	5,	'temp_pre_heating_mantle_1',	'thermo_element',	'measuring'),
(10,	'temp_feed_1_address',	4,	'temp_feed_1',	'thermo_element',	'measuring'),
(11,	'heating_feed_1_address',	560,	'heating_mantle_2',	'heating_mantle',	'heating'),
(12,	'cooling_fan_1_address',	532,	'cooling_fan_1',	'fan',	'cooling'),
(13,	'feed_pressure_1_address',	529,	'pres_feed_1',	'manometer',	'measuring');

DROP TABLE IF EXISTS `feed_1`;
CREATE TABLE `feed_1` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `pump_state` int(64) unsigned NOT NULL,
  `pressure_state` int(64) unsigned NOT NULL,
  `heating_state` int(64) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pump_state` (`pump_state`),
  KEY `pressure_state` (`pressure_state`),
  KEY `heating_state` (`heating_state`),
  CONSTRAINT `feed_1_ibfk_1` FOREIGN KEY (`pump_state`) REFERENCES `pump_states` (`id`),
  CONSTRAINT `feed_1_ibfk_2` FOREIGN KEY (`heating_state`) REFERENCES `heating_states` (`id`),
  CONSTRAINT `feed_1_ibfk_3` FOREIGN KEY (`pressure_state`) REFERENCES `pressure_states` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;

INSERT INTO `feed_1` (`id`, `pump_state`, `pressure_state`, `heating_state`) VALUES
(1,	1,	1,	3);

DROP TABLE IF EXISTS `heating_states`;
CREATE TABLE `heating_states` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` varchar(64) NOT NULL,
  `heating_temp` int(64) unsigned NOT NULL,
  `temp_device_id` int(64) unsigned NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `temp_device_id` (`temp_device_id`),
  KEY `device_id` (`device_id`),
  CONSTRAINT `heating_states_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `heating_states_ibfk_3` FOREIGN KEY (`temp_device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb3;

INSERT INTO `heating_states` (`id`, `device_id`, `state_name`, `state_value`, `heating_temp`, `temp_device_id`, `device_group_function`) VALUES
(1,	4,	'heating_mantle_1',	'true',	422,	5,	'heating'),
(2,	8,	'pre_heating_mantle_1',	'false',	300,	9,	'heating'),
(3,	11,	'heating_feed_1',	'false',	25,	10,	'heating');

DROP TABLE IF EXISTS `pressure_states`;
CREATE TABLE `pressure_states` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` varchar(64) NOT NULL,
  `pres_device_id` int(64) unsigned NOT NULL,
  `pressure_abs` float unsigned DEFAULT NULL,
  `pressure_div` float unsigned DEFAULT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  KEY `pres_device_id` (`pres_device_id`),
  CONSTRAINT `pressure_states_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`),
  CONSTRAINT `pressure_states_ibfk_2` FOREIGN KEY (`pres_device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;

INSERT INTO `pressure_states` (`id`, `device_id`, `state_name`, `state_value`, `pres_device_id`, `pressure_abs`, `pressure_div`, `device_group_function`) VALUES
(1,	13,	'feed_pressure_1',	'False',	13,	1.2,	0,	'feed'),
(2,	13,	'gas_pressure_1',	'false',	13,	1.5,	0,	'measuring');

DROP TABLE IF EXISTS `pump_states`;
CREATE TABLE `pump_states` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` varchar(64) NOT NULL,
  `rate` int(64) unsigned NOT NULL,
  `power` int(64) unsigned NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  CONSTRAINT `pump_states_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;

INSERT INTO `pump_states` (`id`, `device_id`, `state_name`, `state_value`, `rate`, `power`, `device_group_function`) VALUES
(1,	3,	'feed_pump_1',	'false',	1,	0,	'feed'),
(2,	1,	'cooling_pump_1',	'true',	0,	1,	'cooling');

DROP TABLE IF EXISTS `reflux`;
CREATE TABLE `reflux` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` int(64) unsigned NOT NULL,
  `reflux_rate` int(64) unsigned NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  CONSTRAINT `reflux_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;


DROP TABLE IF EXISTS `valve_states`;
CREATE TABLE `valve_states` (
  `id` int(64) unsigned NOT NULL AUTO_INCREMENT,
  `device_id` int(64) unsigned NOT NULL,
  `state_name` varchar(64) NOT NULL,
  `state_value` varchar(64) NOT NULL,
  `flow` int(64) unsigned NOT NULL,
  `device_group_function` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `device_id` (`device_id`),
  CONSTRAINT `valve_states_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `devices` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;

INSERT INTO `valve_states` (`id`, `device_id`, `state_name`, `state_value`, `flow`, `device_group_function`) VALUES
(1,	2,	'gas_valve_1',	'true',	0,	'gas');

-- 2023-04-13 18:56:44
