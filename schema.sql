-- MySQL dump 10.13  Distrib 9.6.0, for macos26.3 (arm64)
--
-- Host: localhost    Database: ootp_db
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '2a88cb64-26f4-11f1-a71e-f6b5a726c776:1-13308';

--
-- Table structure for table `cities`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cities` (
  `city_id` int NOT NULL,
  `nation_id` int DEFAULT NULL,
  `state_id` int DEFAULT NULL,
  `name` varchar(80) DEFAULT NULL,
  `abbreviation` varchar(10) DEFAULT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `population` int DEFAULT NULL,
  `main_language_id` int DEFAULT NULL,
  PRIMARY KEY (`city_id`),
  KEY `fk_cities_nation` (`nation_id`),
  KEY `fk_cities_state` (`state_id`,`nation_id`),
  KEY `fk_cities_language` (`main_language_id`),
  CONSTRAINT `fk_cities_language` FOREIGN KEY (`main_language_id`) REFERENCES `languages` (`language_id`),
  CONSTRAINT `fk_cities_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_cities_state` FOREIGN KEY (`state_id`, `nation_id`) REFERENCES `states` (`state_id`, `nation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coaches`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coaches` (
  `coach_id` int NOT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `nick_name` varchar(50) DEFAULT NULL,
  `age` smallint DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `city_of_birth_id` int DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `weight` smallint DEFAULT NULL,
  `height` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `experience` smallint DEFAULT NULL,
  `occupation` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `former_player_id` int DEFAULT NULL,
  `contract_salary` int DEFAULT NULL,
  `contract_years` smallint DEFAULT NULL,
  `contract_extension_salary` int DEFAULT NULL,
  `contract_extension_years` smallint DEFAULT NULL,
  `scout_major` smallint DEFAULT NULL,
  `scout_minor` smallint DEFAULT NULL,
  `scout_international` smallint DEFAULT NULL,
  `scout_amateur` smallint DEFAULT NULL,
  `scout_amateur_preference` smallint DEFAULT NULL,
  `teach_hitting` smallint DEFAULT NULL,
  `teach_pitching` smallint DEFAULT NULL,
  `teach_c` smallint DEFAULT NULL,
  `teach_if` smallint DEFAULT NULL,
  `teach_of` smallint DEFAULT NULL,
  `handle_veterans` smallint DEFAULT NULL,
  `handle_rookies` smallint DEFAULT NULL,
  `handle_players` smallint DEFAULT NULL,
  `heal_legs` smallint DEFAULT NULL,
  `heal_arms` smallint DEFAULT NULL,
  `heal_back` smallint DEFAULT NULL,
  `heal_other` smallint DEFAULT NULL,
  `heal_rest` smallint DEFAULT NULL,
  `management_style` smallint DEFAULT NULL,
  `personality` smallint DEFAULT NULL,
  `hitting_focus` smallint DEFAULT NULL,
  `pitching_focus` smallint DEFAULT NULL,
  `training_focus` smallint DEFAULT NULL,
  `teach_running` smallint DEFAULT NULL,
  `prevent_legs` smallint DEFAULT NULL,
  `prevent_arms` smallint DEFAULT NULL,
  `prevent_back` smallint DEFAULT NULL,
  `prevent_other` smallint DEFAULT NULL,
  `stealing` int DEFAULT NULL,
  `running` int DEFAULT NULL,
  `pinchrun` int DEFAULT NULL,
  `pinchhit_pos` int DEFAULT NULL,
  `pinchhit_pitch` int DEFAULT NULL,
  `hook_start` int DEFAULT NULL,
  `hook_relief` int DEFAULT NULL,
  `closer` int DEFAULT NULL,
  `lr_matchup` int DEFAULT NULL,
  `bunt_hit` int DEFAULT NULL,
  `bunt` int DEFAULT NULL,
  `hit_run` int DEFAULT NULL,
  `run_hit` int DEFAULT NULL,
  `squeeze` int DEFAULT NULL,
  `pitch_around` int DEFAULT NULL,
  `intentional_walk` int DEFAULT NULL,
  `hold_runner` int DEFAULT NULL,
  `guard_lines` int DEFAULT NULL,
  `infield_in` int DEFAULT NULL,
  `outfield_in` int DEFAULT NULL,
  `corners_in` int DEFAULT NULL,
  `shift_if` int DEFAULT NULL,
  `shift_of` int DEFAULT NULL,
  `opener` int DEFAULT NULL,
  `num_pitchers` smallint DEFAULT NULL,
  `num_hitters` smallint DEFAULT NULL,
  `favor_speed_to_power` int DEFAULT NULL,
  `favor_avg_to_obp` int DEFAULT NULL,
  `favor_defense_to_offense` int DEFAULT NULL,
  `favor_pitching_to_hitting` int DEFAULT NULL,
  `favor_veterans_to_prospects` int DEFAULT NULL,
  `trade_aggressiveness` int DEFAULT NULL,
  `player_loyalty` int DEFAULT NULL,
  `trade_frequency` int DEFAULT NULL,
  `trade_preference` int DEFAULT NULL,
  `value_stats` int DEFAULT NULL,
  `value_this_year` int DEFAULT NULL,
  `value_last_year` int DEFAULT NULL,
  `value_two_years` int DEFAULT NULL,
  `draft_value` int DEFAULT NULL,
  `intl_fa_value` int DEFAULT NULL,
  `develop_value` int DEFAULT NULL,
  `ratings_value` int DEFAULT NULL,
  `manager_value` smallint DEFAULT NULL,
  `pitching_coach_value` smallint DEFAULT NULL,
  `hitting_coach_value` smallint DEFAULT NULL,
  `scout_value` smallint DEFAULT NULL,
  `doctor_value` smallint DEFAULT NULL,
  `basecoach_value` smallint DEFAULT NULL,
  `positive_relation` smallint DEFAULT NULL,
  `negative_relation` smallint DEFAULT NULL,
  PRIMARY KEY (`coach_id`),
  KEY `fk_coaches_city` (`city_of_birth_id`),
  KEY `fk_coaches_nation` (`nation_id`),
  KEY `fk_coaches_team` (`team_id`),
  KEY `fk_coaches_former_player` (`former_player_id`),
  CONSTRAINT `fk_coaches_city` FOREIGN KEY (`city_of_birth_id`) REFERENCES `cities` (`city_id`),
  CONSTRAINT `fk_coaches_former_player` FOREIGN KEY (`former_player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_coaches_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_coaches_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `continents`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `continents` (
  `continent_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbreviation` varchar(50) DEFAULT NULL,
  `demonym` varchar(50) DEFAULT NULL,
  `population` int DEFAULT NULL,
  `main_language_id` int DEFAULT NULL,
  PRIMARY KEY (`continent_id`),
  KEY `fk_continents_language` (`main_language_id`),
  CONSTRAINT `fk_continents_language` FOREIGN KEY (`main_language_id`) REFERENCES `languages` (`language_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `divisions`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `divisions` (
  `league_id` int NOT NULL,
  `sub_league_id` int NOT NULL,
  `division_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `gender` int DEFAULT NULL,
  PRIMARY KEY (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_divisions_sub_league` FOREIGN KEY (`league_id`, `sub_league_id`) REFERENCES `sub_leagues` (`league_id`, `sub_league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `games`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `games` (
  `game_id` int NOT NULL,
  `league_id` int DEFAULT NULL,
  `home_team` int DEFAULT NULL,
  `away_team` int DEFAULT NULL,
  `attendance` int DEFAULT NULL,
  `date` date DEFAULT NULL,
  `time` smallint DEFAULT NULL,
  `game_type` smallint DEFAULT NULL,
  `played` tinyint DEFAULT NULL,
  `innings` smallint DEFAULT NULL,
  `runs0` smallint DEFAULT NULL,
  `runs1` smallint DEFAULT NULL,
  `hits0` smallint DEFAULT NULL,
  `hits1` smallint DEFAULT NULL,
  `errors0` smallint DEFAULT NULL,
  `errors1` smallint DEFAULT NULL,
  `winning_pitcher` int DEFAULT NULL,
  `losing_pitcher` int DEFAULT NULL,
  `save_pitcher` int DEFAULT NULL,
  `starter0` int DEFAULT NULL,
  `starter1` int DEFAULT NULL,
  PRIMARY KEY (`game_id`),
  KEY `fk_games_league` (`league_id`),
  KEY `fk_games_home_team` (`home_team`),
  KEY `fk_games_away_team` (`away_team`),
  KEY `fk_games_winning_pitcher` (`winning_pitcher`),
  KEY `fk_games_losing_pitcher` (`losing_pitcher`),
  KEY `fk_games_save_pitcher` (`save_pitcher`),
  KEY `fk_games_starter0` (`starter0`),
  KEY `fk_games_starter1` (`starter1`),
  CONSTRAINT `fk_games_away_team` FOREIGN KEY (`away_team`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_games_home_team` FOREIGN KEY (`home_team`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_games_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_games_losing_pitcher` FOREIGN KEY (`losing_pitcher`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_games_save_pitcher` FOREIGN KEY (`save_pitcher`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_games_starter0` FOREIGN KEY (`starter0`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_games_starter1` FOREIGN KEY (`starter1`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_games_winning_pitcher` FOREIGN KEY (`winning_pitcher`) REFERENCES `players` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `games_score`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `games_score` (
  `game_id` int NOT NULL,
  `team` smallint NOT NULL,
  `inning` smallint NOT NULL,
  `score` smallint DEFAULT NULL,
  PRIMARY KEY (`game_id`,`team`,`inning`),
  CONSTRAINT `fk_games_score_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `best_hitter_id` int DEFAULT NULL,
  `best_pitcher_id` int DEFAULT NULL,
  `best_rookie_id` int DEFAULT NULL,
  `manager_id` int DEFAULT NULL,
  `made_playoffs` tinyint DEFAULT NULL,
  `won_playoffs` tinyint DEFAULT NULL,
  `fired` tinyint DEFAULT NULL,
  `position_in_division` smallint DEFAULT NULL,
  KEY `fk_human_manager_history_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_team` (`team_id`),
  KEY `fk_human_manager_history_division` (`league_id`,`sub_league_id`,`division_id`),
  KEY `fk_human_manager_history_best_hitter` (`best_hitter_id`),
  KEY `fk_human_manager_history_best_pitcher` (`best_pitcher_id`),
  KEY `fk_human_manager_history_best_rookie` (`best_rookie_id`),
  KEY `fk_human_manager_history_manager_coach` (`manager_id`),
  CONSTRAINT `fk_human_manager_history_best_hitter` FOREIGN KEY (`best_hitter_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_human_manager_history_best_pitcher` FOREIGN KEY (`best_pitcher_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_human_manager_history_best_rookie` FOREIGN KEY (`best_rookie_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_human_manager_history_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_manager_coach` FOREIGN KEY (`manager_id`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_human_manager_history_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history_batting_stats` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `pa` int DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `h` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `d` int DEFAULT NULL,
  `t` int DEFAULT NULL,
  `hr` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `rbi` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `ibb` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `gdp` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `ebh` int DEFAULT NULL,
  `pitches_seen` int DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `rc` double DEFAULT NULL,
  `rc27` double DEFAULT NULL,
  `iso` double DEFAULT NULL,
  `tavg` double DEFAULT NULL,
  `woba` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `sbp` double DEFAULT NULL,
  KEY `fk_human_manager_history_batting_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_batting_team` (`team_id`),
  KEY `fk_human_manager_history_batting_division` (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_human_manager_history_batting_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_batting_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history_fielding_stats_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history_fielding_stats_stats` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `tc` int DEFAULT NULL,
  `a` int DEFAULT NULL,
  `po` int DEFAULT NULL,
  `e` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `tp` int DEFAULT NULL,
  `pb` int DEFAULT NULL,
  `sba` int DEFAULT NULL,
  `rto` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `range` double DEFAULT NULL,
  `rtop` double DEFAULT NULL,
  `cera` double DEFAULT NULL,
  KEY `fk_human_manager_history_fielding_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_fielding_team` (`team_id`),
  KEY `fk_human_manager_history_fielding_division` (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_human_manager_history_fielding_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_fielding_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_fielding_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history_financials`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history_financials` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `gate_revenue` int DEFAULT NULL,
  `media_revenue` int DEFAULT NULL,
  `merchandising_revenue` int DEFAULT NULL,
  `other_revenue` int DEFAULT NULL,
  `revenue_sharing` int DEFAULT NULL,
  `luxury_sharing` int DEFAULT NULL,
  `playoff_revenue` int DEFAULT NULL,
  `cash` int DEFAULT NULL,
  `player_expenses` int DEFAULT NULL,
  `staff_expenses` int DEFAULT NULL,
  `stadium_expenses` int DEFAULT NULL,
  `attendance` int DEFAULT NULL,
  `fan_interest` smallint DEFAULT NULL,
  `fan_loyalty` smallint DEFAULT NULL,
  `fan_modifier` smallint DEFAULT NULL,
  `ticket_price` double DEFAULT NULL,
  `budget` int DEFAULT NULL,
  `market` smallint DEFAULT NULL,
  `owner_expectation` smallint DEFAULT NULL,
  KEY `fk_human_manager_history_financials_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_financials_team` (`team_id`),
  KEY `fk_human_manager_history_financials_division` (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_human_manager_history_financials_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_financials_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_financials_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history_pitching_stats` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `cera` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  KEY `fk_human_manager_history_pitching_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_pitching_team` (`team_id`),
  KEY `fk_human_manager_history_pitching_division` (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_human_manager_history_pitching_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_pitching_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_manager_history_record`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_manager_history_record` (
  `human_manager_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `w` smallint DEFAULT NULL,
  `l` smallint DEFAULT NULL,
  `pos` smallint DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `gb` double DEFAULT NULL,
  `streak` smallint DEFAULT NULL,
  `magic_number` smallint DEFAULT NULL,
  KEY `fk_human_manager_history_record_manager` (`human_manager_id`),
  KEY `fk_human_manager_history_record_team` (`team_id`),
  KEY `fk_human_manager_history_record_division` (`league_id`,`sub_league_id`,`division_id`),
  CONSTRAINT `fk_human_manager_history_record_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_human_manager_history_record_manager` FOREIGN KEY (`human_manager_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_human_manager_history_record_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `human_managers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `human_managers` (
  `human_manager_id` int NOT NULL,
  `is_commish` tinyint DEFAULT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `nick_name` varchar(50) DEFAULT NULL,
  `age` smallint DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `city_of_birth_id` int DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `second_nation_id` int DEFAULT NULL,
  `weight` smallint DEFAULT NULL,
  `height` smallint DEFAULT NULL,
  `retired` tinyint DEFAULT NULL,
  `free_agent` tinyint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `last_league_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `last_team_id` int DEFAULT NULL,
  `organization_id` int DEFAULT NULL,
  `last_organization_id` int DEFAULT NULL,
  `language_ids0` int DEFAULT NULL,
  `language_ids1` int DEFAULT NULL,
  `uniform_number` smallint DEFAULT NULL,
  `experience` smallint DEFAULT NULL,
  `person_type` smallint DEFAULT NULL,
  `bats` smallint DEFAULT NULL,
  `throws` smallint DEFAULT NULL,
  `personality_greed` smallint DEFAULT NULL,
  `personality_loyalty` smallint DEFAULT NULL,
  `personality_play_for_winner` smallint DEFAULT NULL,
  `personality_work_ethic` smallint DEFAULT NULL,
  `personality_intelligence` smallint DEFAULT NULL,
  `personality_leader` smallint DEFAULT NULL,
  PRIMARY KEY (`human_manager_id`),
  KEY `fk_human_managers_city` (`city_of_birth_id`),
  KEY `fk_human_managers_nation` (`nation_id`),
  KEY `fk_human_managers_second_nation` (`second_nation_id`),
  KEY `fk_human_managers_league` (`league_id`),
  KEY `fk_human_managers_last_league` (`last_league_id`),
  KEY `fk_human_managers_team` (`team_id`),
  KEY `fk_human_managers_last_team` (`last_team_id`),
  KEY `fk_human_managers_org_team` (`organization_id`),
  KEY `fk_human_managers_last_org_team` (`last_organization_id`),
  CONSTRAINT `fk_human_managers_city` FOREIGN KEY (`city_of_birth_id`) REFERENCES `cities` (`city_id`),
  CONSTRAINT `fk_human_managers_last_league` FOREIGN KEY (`last_league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_human_managers_last_org_team` FOREIGN KEY (`last_organization_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_human_managers_last_team` FOREIGN KEY (`last_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_human_managers_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_human_managers_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_human_managers_org_team` FOREIGN KEY (`organization_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_human_managers_second_nation` FOREIGN KEY (`second_nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_human_managers_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `language_data`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `language_data` (
  `parent_table` int NOT NULL,
  `parent_id` int NOT NULL,
  `language_id` int NOT NULL,
  `percentage` int NOT NULL,
  PRIMARY KEY (`parent_table`,`parent_id`,`language_id`,`percentage`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `languages`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `languages` (
  `language_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`language_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_events`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_events` (
  `league_id` int DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `type` smallint DEFAULT NULL,
  `event_over` tinyint DEFAULT NULL,
  `deleted` tinyint DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `needs_human_action` tinyint DEFAULT NULL,
  `real_sim_date` smallint DEFAULT NULL,
  KEY `fk_league_events_league` (`league_id`),
  CONSTRAINT `fk_league_events_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_history` (
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `year` int DEFAULT NULL,
  `best_hitter_id` int DEFAULT NULL,
  `best_pitcher_id` int DEFAULT NULL,
  `best_rookie_id` int DEFAULT NULL,
  `best_manager_id` int DEFAULT NULL,
  `best_fielder_id0` int DEFAULT NULL,
  `best_fielder_id1` int DEFAULT NULL,
  `best_fielder_id2` int DEFAULT NULL,
  `best_fielder_id3` int DEFAULT NULL,
  `best_fielder_id4` int DEFAULT NULL,
  `best_fielder_id5` int DEFAULT NULL,
  `best_fielder_id6` int DEFAULT NULL,
  `best_fielder_id7` int DEFAULT NULL,
  `best_fielder_id8` int DEFAULT NULL,
  `best_fielder_id9` int DEFAULT NULL,
  KEY `fk_league_history_sub_league` (`league_id`,`sub_league_id`),
  KEY `fk_league_history_best_hitter` (`best_hitter_id`),
  KEY `fk_league_history_best_pitcher` (`best_pitcher_id`),
  KEY `fk_league_history_best_rookie` (`best_rookie_id`),
  KEY `fk_league_history_best_manager` (`best_manager_id`),
  CONSTRAINT `fk_league_history_best_hitter` FOREIGN KEY (`best_hitter_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_league_history_best_manager` FOREIGN KEY (`best_manager_id`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_league_history_best_pitcher` FOREIGN KEY (`best_pitcher_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_league_history_best_rookie` FOREIGN KEY (`best_rookie_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_league_history_sub_league` FOREIGN KEY (`league_id`, `sub_league_id`) REFERENCES `sub_leagues` (`league_id`, `sub_league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_history_all_star`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_history_all_star` (
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `year` int DEFAULT NULL,
  `all_star_pos` int DEFAULT NULL,
  `all_star` int DEFAULT NULL,
  KEY `fk_league_history_all_star_sub_league` (`league_id`,`sub_league_id`),
  KEY `fk_league_history_all_star_player` (`all_star`),
  CONSTRAINT `fk_league_history_all_star_player` FOREIGN KEY (`all_star`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_league_history_all_star_sub_league` FOREIGN KEY (`league_id`, `sub_league_id`) REFERENCES `sub_leagues` (`league_id`, `sub_league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_history_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_history_batting_stats` (
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `pa` int DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `h` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `d` int DEFAULT NULL,
  `t` int DEFAULT NULL,
  `hr` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `rbi` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `ibb` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `gdp` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `ebh` int DEFAULT NULL,
  `pitches_seen` int DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `rc` double DEFAULT NULL,
  `rc27` double DEFAULT NULL,
  `iso` double DEFAULT NULL,
  `woba` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `sbp` double DEFAULT NULL,
  `kp` double DEFAULT NULL,
  `bbp` double DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  KEY `fk_league_history_batting_team` (`team_id`),
  CONSTRAINT `fk_league_history_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_history_fielding_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_history_fielding_stats` (
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `tc` int DEFAULT NULL,
  `a` int DEFAULT NULL,
  `po` int DEFAULT NULL,
  `e` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `tp` int DEFAULT NULL,
  `pb` int DEFAULT NULL,
  `sba` int DEFAULT NULL,
  `rto` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `range` double DEFAULT NULL,
  `rtop` double DEFAULT NULL,
  `cera` double DEFAULT NULL,
  `zr` double DEFAULT NULL,
  `plays` int DEFAULT NULL,
  `plays_base` int DEFAULT NULL,
  `roe` int DEFAULT NULL,
  `eff` int DEFAULT NULL,
  `opps_0` int DEFAULT NULL,
  `opps_made_0` int DEFAULT NULL,
  `opps_1` int DEFAULT NULL,
  `opps_made_1` int DEFAULT NULL,
  `opps_2` int DEFAULT NULL,
  `opps_made_2` int DEFAULT NULL,
  `opps_3` int DEFAULT NULL,
  `opps_made_3` int DEFAULT NULL,
  `opps_4` int DEFAULT NULL,
  `opps_made_4` int DEFAULT NULL,
  `opps_5` int DEFAULT NULL,
  `opps_made_5` int DEFAULT NULL,
  `framing` double DEFAULT NULL,
  `arm` double DEFAULT NULL,
  KEY `fk_league_history_fielding_team` (`team_id`),
  KEY `fk_league_history_fielding_sub_league` (`league_id`,`sub_league_id`),
  CONSTRAINT `fk_league_history_fielding_sub_league` FOREIGN KEY (`league_id`, `sub_league_id`) REFERENCES `sub_leagues` (`league_id`, `sub_league_id`),
  CONSTRAINT `fk_league_history_fielding_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_history_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_history_pitching_stats` (
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `ir` int DEFAULT NULL,
  `irs` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `kp` double DEFAULT NULL,
  `bbp` double DEFAULT NULL,
  `kbbp` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `irsp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `war` double DEFAULT NULL,
  `ra9war` double DEFAULT NULL,
  `sd` int DEFAULT NULL,
  `md` int DEFAULT NULL,
  KEY `fk_league_history_pitching_team` (`team_id`),
  CONSTRAINT `fk_league_history_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_playoff_fixtures`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_playoff_fixtures` (
  `league_id` int DEFAULT NULL,
  `team_id0` int DEFAULT NULL,
  `team_id1` int DEFAULT NULL,
  `winner` int DEFAULT NULL,
  `finished` tinyint DEFAULT NULL,
  `best_of` smallint DEFAULT NULL,
  `played` smallint DEFAULT NULL,
  `round` smallint DEFAULT NULL,
  `result0` smallint DEFAULT NULL,
  `result1` smallint DEFAULT NULL,
  KEY `fk_league_playoff_fixtures_league` (`league_id`),
  KEY `fk_league_playoff_fixtures_team_0` (`team_id0`),
  KEY `fk_league_playoff_fixtures_team_1` (`team_id1`),
  KEY `fk_league_playoff_fixtures_winner` (`winner`),
  CONSTRAINT `fk_league_playoff_fixtures_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_league_playoff_fixtures_team_0` FOREIGN KEY (`team_id0`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_league_playoff_fixtures_team_1` FOREIGN KEY (`team_id1`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_league_playoff_fixtures_winner` FOREIGN KEY (`winner`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `league_playoffs`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `league_playoffs` (
  `league_id` int DEFAULT NULL,
  `play_off_mode` smallint DEFAULT NULL,
  `round` smallint DEFAULT NULL,
  `max_round` smallint DEFAULT NULL,
  `num_wild_cards` smallint DEFAULT NULL,
  `best_of0` smallint DEFAULT NULL,
  `best_of1` smallint DEFAULT NULL,
  `best_of2` smallint DEFAULT NULL,
  `best_of3` smallint DEFAULT NULL,
  `best_of4` smallint DEFAULT NULL,
  `best_of5` smallint DEFAULT NULL,
  `best_of6` smallint DEFAULT NULL,
  `best_of7` smallint DEFAULT NULL,
  `best_of8` smallint DEFAULT NULL,
  `best_of9` smallint DEFAULT NULL,
  `best_of10` smallint DEFAULT NULL,
  `best_of11` smallint DEFAULT NULL,
  `best_of12` smallint DEFAULT NULL,
  `best_of13` smallint DEFAULT NULL,
  `best_of14` smallint DEFAULT NULL,
  `best_of15` smallint DEFAULT NULL,
  `best_of16` smallint DEFAULT NULL,
  `best_of17` smallint DEFAULT NULL,
  `best_of18` smallint DEFAULT NULL,
  `best_of19` smallint DEFAULT NULL,
  `best_of20` smallint DEFAULT NULL,
  `best_of21` smallint DEFAULT NULL,
  `best_of22` smallint DEFAULT NULL,
  `best_of23` smallint DEFAULT NULL,
  `best_of24` smallint DEFAULT NULL,
  `best_of25` smallint DEFAULT NULL,
  `best_of26` smallint DEFAULT NULL,
  `best_of27` smallint DEFAULT NULL,
  `best_of28` smallint DEFAULT NULL,
  `best_of29` smallint DEFAULT NULL,
  `best_of30` smallint DEFAULT NULL,
  `best_of31` smallint DEFAULT NULL,
  `best_of32` smallint DEFAULT NULL,
  `best_of33` smallint DEFAULT NULL,
  `best_of34` smallint DEFAULT NULL,
  `best_of35` smallint DEFAULT NULL,
  `best_of36` smallint DEFAULT NULL,
  `best_of37` smallint DEFAULT NULL,
  `best_of38` smallint DEFAULT NULL,
  `best_of39` smallint DEFAULT NULL,
  `best_of40` smallint DEFAULT NULL,
  `best_of41` smallint DEFAULT NULL,
  `best_of42` smallint DEFAULT NULL,
  `best_of43` smallint DEFAULT NULL,
  `best_of44` smallint DEFAULT NULL,
  `best_of45` smallint DEFAULT NULL,
  `best_of46` smallint DEFAULT NULL,
  `best_of47` smallint DEFAULT NULL,
  `best_of48` smallint DEFAULT NULL,
  `best_of49` smallint DEFAULT NULL,
  `round_names0` varchar(30) DEFAULT NULL,
  `round_names1` varchar(30) DEFAULT NULL,
  `round_names2` varchar(30) DEFAULT NULL,
  `round_names3` varchar(30) DEFAULT NULL,
  `round_names4` varchar(30) DEFAULT NULL,
  `round_names5` varchar(30) DEFAULT NULL,
  `round_names6` varchar(30) DEFAULT NULL,
  `round_names7` varchar(30) DEFAULT NULL,
  `round_names8` varchar(30) DEFAULT NULL,
  `round_names9` varchar(30) DEFAULT NULL,
  `round_names10` varchar(30) DEFAULT NULL,
  `round_names11` varchar(30) DEFAULT NULL,
  `round_names12` varchar(30) DEFAULT NULL,
  `round_names13` varchar(30) DEFAULT NULL,
  `round_names14` varchar(30) DEFAULT NULL,
  `round_names15` varchar(30) DEFAULT NULL,
  `round_names16` varchar(30) DEFAULT NULL,
  `round_names17` varchar(30) DEFAULT NULL,
  `round_names18` varchar(30) DEFAULT NULL,
  `round_names19` varchar(30) DEFAULT NULL,
  `round_names20` varchar(30) DEFAULT NULL,
  `round_names21` varchar(30) DEFAULT NULL,
  `round_names22` varchar(30) DEFAULT NULL,
  `round_names23` varchar(30) DEFAULT NULL,
  `round_names24` varchar(30) DEFAULT NULL,
  `round_names25` varchar(30) DEFAULT NULL,
  `round_names26` varchar(30) DEFAULT NULL,
  `round_names27` varchar(30) DEFAULT NULL,
  `round_names28` varchar(30) DEFAULT NULL,
  `round_names29` varchar(30) DEFAULT NULL,
  `round_names30` varchar(30) DEFAULT NULL,
  `round_names31` varchar(30) DEFAULT NULL,
  `round_names32` varchar(30) DEFAULT NULL,
  `round_names33` varchar(30) DEFAULT NULL,
  `round_names34` varchar(30) DEFAULT NULL,
  `round_names35` varchar(30) DEFAULT NULL,
  `round_names36` varchar(30) DEFAULT NULL,
  `round_names37` varchar(30) DEFAULT NULL,
  `round_names38` varchar(30) DEFAULT NULL,
  `round_names39` varchar(30) DEFAULT NULL,
  `round_names40` varchar(30) DEFAULT NULL,
  `round_names41` varchar(30) DEFAULT NULL,
  `round_names42` varchar(30) DEFAULT NULL,
  `round_names43` varchar(30) DEFAULT NULL,
  `round_names44` varchar(30) DEFAULT NULL,
  `round_names45` varchar(30) DEFAULT NULL,
  `round_names46` varchar(30) DEFAULT NULL,
  `round_names47` varchar(30) DEFAULT NULL,
  `round_names48` varchar(30) DEFAULT NULL,
  `round_names49` varchar(30) DEFAULT NULL,
  `split_season` tinyint DEFAULT NULL,
  `allstar_winner_homefield` tinyint DEFAULT NULL,
  `allstar_winner` int DEFAULT NULL,
  `winner` int DEFAULT NULL,
  KEY `fk_league_playoffs_league` (`league_id`),
  KEY `fk_league_playoffs_allstar_winner` (`allstar_winner`),
  KEY `fk_league_playoffs_winner` (`winner`),
  CONSTRAINT `fk_league_playoffs_allstar_winner` FOREIGN KEY (`allstar_winner`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_league_playoffs_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_league_playoffs_winner` FOREIGN KEY (`winner`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `leagues`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leagues` (
  `league_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbr` varchar(50) DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `language_id` int DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `reputation` smallint DEFAULT NULL,
  `historical_league` tinyint DEFAULT NULL,
  `logo_file_name` varchar(200) DEFAULT NULL,
  `players_path` varchar(200) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `preferred_start_date` date DEFAULT NULL,
  `pitcher_award_name` varchar(50) DEFAULT NULL,
  `mvp_award_name` varchar(50) DEFAULT NULL,
  `rookie_award_name` varchar(50) DEFAULT NULL,
  `defense_award_name` varchar(50) DEFAULT NULL,
  `fictional_players` tinyint DEFAULT NULL,
  `start_fantasy_draft` tinyint DEFAULT NULL,
  `trading_deadline` tinyint DEFAULT NULL,
  `winter_meetings` tinyint DEFAULT NULL,
  `arbitration_offering` tinyint DEFAULT NULL,
  `show_draft_pool` tinyint DEFAULT NULL,
  `rosters_expanded` tinyint DEFAULT NULL,
  `draft_date` date DEFAULT NULL,
  `rule_5_draft_date` date DEFAULT NULL,
  `international_fa_date` date DEFAULT NULL,
  `roster_expand_date` date DEFAULT NULL,
  `trade_deadline_date` date DEFAULT NULL,
  `allstar_date` date DEFAULT NULL,
  `days_until_deadline` int DEFAULT NULL,
  `next_draft_type` int DEFAULT NULL,
  `parent_league_id` int DEFAULT NULL,
  `league_state` smallint DEFAULT NULL,
  `season_year` int DEFAULT NULL,
  `historical_year` smallint DEFAULT NULL,
  `league_level` smallint DEFAULT NULL,
  `stats_detail` int DEFAULT NULL,
  `historical_import_path` varchar(200) DEFAULT NULL,
  `foreigner_percentage` smallint DEFAULT NULL,
  `was_ootp6` tinyint DEFAULT NULL,
  `was_65` tinyint DEFAULT NULL,
  `allstar_game` tinyint DEFAULT NULL,
  `auto_schedule_allstar` tinyint DEFAULT NULL,
  `allstar_team_id0` int DEFAULT NULL,
  `allstar_team_id1` int DEFAULT NULL,
  `schedule_file_1` varchar(200) DEFAULT NULL,
  `schedule_file_2` varchar(200) DEFAULT NULL,
  `rules_rule_5` tinyint DEFAULT NULL,
  `rules_minor_league_options` tinyint DEFAULT NULL,
  `rules_trading` tinyint DEFAULT NULL,
  `rules_trading_deadline_events` smallint DEFAULT NULL,
  `rules_draft_pick_trading` tinyint DEFAULT NULL,
  `rules_financials` tinyint DEFAULT NULL,
  `rules_amateur_draft` tinyint DEFAULT NULL,
  `rules_fa_compensation` smallint DEFAULT NULL,
  `rules_schedule_balanced` tinyint DEFAULT NULL,
  `rules_schedule_inter_league` tinyint DEFAULT NULL,
  `rules_schedule_force_start_day` tinyint DEFAULT NULL,
  `rules_trades_other_leagues` tinyint DEFAULT NULL,
  `rules_free_agents_from_other_leagues` tinyint DEFAULT NULL,
  `rules_free_agents_leave_other_leagues` tinyint DEFAULT NULL,
  `rules_allstar_game` tinyint DEFAULT NULL,
  `rules_spring_training` tinyint DEFAULT NULL,
  `rules_active_roster_limit` smallint DEFAULT NULL,
  `rules_secondary_roster_limit` smallint DEFAULT NULL,
  `rules_expanded_roster_limit` smallint DEFAULT NULL,
  `rules_min_service_days` smallint DEFAULT NULL,
  `rules_waiver_period_length` smallint DEFAULT NULL,
  `rules_dfa_period_length` smallint DEFAULT NULL,
  `rules_fa_minimum_years` smallint DEFAULT NULL,
  `rules_salary_arbitration_minimum_years` smallint DEFAULT NULL,
  `rules_minor_league_fa_minimum_years` smallint DEFAULT NULL,
  `rules_foreigner_limit` smallint DEFAULT NULL,
  `rules_foreigner_pitcher_limit` smallint DEFAULT NULL,
  `rules_foreigner_hitter_limit` smallint DEFAULT NULL,
  `rules_schedule_games_per_team` smallint DEFAULT NULL,
  `rules_schedule_typical_series` smallint DEFAULT NULL,
  `rules_schedule_game_times` smallint DEFAULT NULL,
  `rules_schedule_preferred_start_day` smallint DEFAULT NULL,
  `rules_amateur_draft_rounds` smallint DEFAULT NULL,
  `rules_minimum_salary` int DEFAULT NULL,
  `rules_salary_cap` int DEFAULT NULL,
  `rules_player_salary0` int DEFAULT NULL,
  `rules_player_salary1` int DEFAULT NULL,
  `rules_player_salary2` int DEFAULT NULL,
  `rules_player_salary3` int DEFAULT NULL,
  `rules_player_salary4` int DEFAULT NULL,
  `rules_player_salary5` int DEFAULT NULL,
  `rules_player_salary6` int DEFAULT NULL,
  `rules_player_salary7` int DEFAULT NULL,
  `rules_average_coach_salary` int DEFAULT NULL,
  `rules_average_attendance` int DEFAULT NULL,
  `rules_average_national_media_contract` int DEFAULT NULL,
  `rules_cash_maximum` int DEFAULT NULL,
  `rules_average_ticket_price` double DEFAULT NULL,
  `rules_luxury_sharing` tinyint DEFAULT NULL,
  `rules_revenue_sharing` tinyint DEFAULT NULL,
  `rules_revenue_sharing_tax` smallint DEFAULT NULL,
  `rules_luxury_sharing_cap` smallint DEFAULT NULL,
  `rules_luxury_tax` smallint DEFAULT NULL,
  `rules_national_media_contract_fixed` tinyint DEFAULT NULL,
  `rules_owner_decides_budget` tinyint DEFAULT NULL,
  `rules_schedule_auto_adjust_dates` tinyint DEFAULT NULL,
  `rules_historical_import_rookies` tinyint DEFAULT NULL,
  `avg_rating_contact` int DEFAULT NULL,
  `avg_rating_gap` int DEFAULT NULL,
  `avg_rating_power` int DEFAULT NULL,
  `avg_rating_eye` int DEFAULT NULL,
  `avg_rating_strikeouts` int DEFAULT NULL,
  `avg_rating_stuff` int DEFAULT NULL,
  `avg_rating_movement` int DEFAULT NULL,
  `avg_rating_control` int DEFAULT NULL,
  `avg_rating_fielding0` int DEFAULT NULL,
  `avg_rating_fielding1` int DEFAULT NULL,
  `avg_rating_fielding2` int DEFAULT NULL,
  `avg_rating_fielding3` int DEFAULT NULL,
  `avg_rating_fielding4` int DEFAULT NULL,
  `avg_rating_fielding5` int DEFAULT NULL,
  `avg_rating_fielding6` int DEFAULT NULL,
  `avg_rating_fielding7` int DEFAULT NULL,
  `avg_rating_fielding8` int DEFAULT NULL,
  `avg_rating_fielding9` int DEFAULT NULL,
  `avg_rating_overall` int DEFAULT NULL,
  `avg_rating_age` double DEFAULT NULL,
  `league_totals_ab` int DEFAULT NULL,
  `league_totals_h` int DEFAULT NULL,
  `league_totals_d` int DEFAULT NULL,
  `league_totals_t` int DEFAULT NULL,
  `league_totals_hr` int DEFAULT NULL,
  `league_totals_bb` int DEFAULT NULL,
  `league_totals_hp` int DEFAULT NULL,
  `league_totals_k` int DEFAULT NULL,
  `league_totals_pa` int DEFAULT NULL,
  `league_totals_babip` double DEFAULT NULL,
  `league_totals_mod_h` double DEFAULT NULL,
  `league_totals_mod_d` double DEFAULT NULL,
  `league_totals_mod_t` double DEFAULT NULL,
  `league_totals_mod_hr` double DEFAULT NULL,
  `league_totals_mod_bb` double DEFAULT NULL,
  `league_totals_mod_hp` double DEFAULT NULL,
  `league_totals_mod_k` double DEFAULT NULL,
  `league_totals_mod_babip` double DEFAULT NULL,
  `ml_equivalencies_avg` double DEFAULT NULL,
  `ml_equivalencies_hr` double DEFAULT NULL,
  `ml_equivalencies_eb` double DEFAULT NULL,
  `ml_equivalencies_bb` double DEFAULT NULL,
  `ml_equivalencies_k` double DEFAULT NULL,
  `ml_equivalencies_hp` double DEFAULT NULL,
  `player_creation_modifier_contact` double DEFAULT NULL,
  `player_creation_modifier_gap` double DEFAULT NULL,
  `player_creation_modifier_power` double DEFAULT NULL,
  `player_creation_modifier_eye` double DEFAULT NULL,
  `player_creation_modifier_strikeouts` double DEFAULT NULL,
  `player_creation_modifier_stuff` double DEFAULT NULL,
  `player_creation_modifier_movement` double DEFAULT NULL,
  `player_creation_modifier_control` double DEFAULT NULL,
  `player_creation_modifier_speed` double DEFAULT NULL,
  `player_creation_modifier_fielding` double DEFAULT NULL,
  `financial_coefficient` double DEFAULT NULL,
  `world_start_year` int DEFAULT NULL,
  `current_date` date DEFAULT NULL,
  `background_color_id` varchar(8) DEFAULT NULL,
  `text_color_id` varchar(8) DEFAULT NULL,
  `scouting_coach_id` int DEFAULT NULL,
  PRIMARY KEY (`league_id`),
  KEY `fk_leagues_nation` (`nation_id`),
  KEY `fk_leagues_language` (`language_id`),
  KEY `fk_leagues_parent_league` (`parent_league_id`),
  CONSTRAINT `fk_leagues_language` FOREIGN KEY (`language_id`) REFERENCES `languages` (`language_id`),
  CONSTRAINT `fk_leagues_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_leagues_parent_league` FOREIGN KEY (`parent_league_id`) REFERENCES `leagues` (`league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `messages`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `message_id` int NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `player_id_0` int DEFAULT NULL,
  `player_id_1` int DEFAULT NULL,
  `player_id_2` int DEFAULT NULL,
  `player_id_3` int DEFAULT NULL,
  `player_id_4` int DEFAULT NULL,
  `player_id_5` int DEFAULT NULL,
  `player_id_6` int DEFAULT NULL,
  `player_id_7` int DEFAULT NULL,
  `player_id_8` int DEFAULT NULL,
  `player_id_9` int DEFAULT NULL,
  `team_id_0` int DEFAULT NULL,
  `team_id_1` int DEFAULT NULL,
  `team_id_2` int DEFAULT NULL,
  `team_id_3` int DEFAULT NULL,
  `team_id_4` int DEFAULT NULL,
  `league_id_0` int DEFAULT NULL,
  `league_id_1` int DEFAULT NULL,
  `importance` int DEFAULT NULL,
  `message_type` int DEFAULT NULL,
  `hype` smallint DEFAULT NULL,
  `sender_type` int DEFAULT NULL,
  `sender_id` int DEFAULT NULL,
  `recipient_id` int DEFAULT NULL,
  `trade_id` int DEFAULT NULL,
  `date` date DEFAULT NULL,
  `deleted` tinyint DEFAULT NULL,
  `notify` tinyint DEFAULT NULL,
  `ongoing_story_id` int DEFAULT NULL,
  `text_is_modified` tinyint DEFAULT NULL,
  PRIMARY KEY (`message_id`),
  KEY `fk_messages_player_0` (`player_id_0`),
  KEY `fk_messages_player_1` (`player_id_1`),
  KEY `fk_messages_player_2` (`player_id_2`),
  KEY `fk_messages_player_3` (`player_id_3`),
  KEY `fk_messages_player_4` (`player_id_4`),
  KEY `fk_messages_player_5` (`player_id_5`),
  KEY `fk_messages_player_6` (`player_id_6`),
  KEY `fk_messages_player_7` (`player_id_7`),
  KEY `fk_messages_player_8` (`player_id_8`),
  KEY `fk_messages_player_9` (`player_id_9`),
  KEY `fk_messages_team_0` (`team_id_0`),
  KEY `fk_messages_team_1` (`team_id_1`),
  KEY `fk_messages_team_2` (`team_id_2`),
  KEY `fk_messages_team_3` (`team_id_3`),
  KEY `fk_messages_team_4` (`team_id_4`),
  KEY `fk_messages_league_0` (`league_id_0`),
  KEY `fk_messages_league_1` (`league_id_1`),
  CONSTRAINT `fk_messages_league_0` FOREIGN KEY (`league_id_0`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_messages_league_1` FOREIGN KEY (`league_id_1`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_messages_player_0` FOREIGN KEY (`player_id_0`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_1` FOREIGN KEY (`player_id_1`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_2` FOREIGN KEY (`player_id_2`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_3` FOREIGN KEY (`player_id_3`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_4` FOREIGN KEY (`player_id_4`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_5` FOREIGN KEY (`player_id_5`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_6` FOREIGN KEY (`player_id_6`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_7` FOREIGN KEY (`player_id_7`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_8` FOREIGN KEY (`player_id_8`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_player_9` FOREIGN KEY (`player_id_9`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_messages_team_0` FOREIGN KEY (`team_id_0`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_messages_team_1` FOREIGN KEY (`team_id_1`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_messages_team_2` FOREIGN KEY (`team_id_2`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_messages_team_3` FOREIGN KEY (`team_id_3`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_messages_team_4` FOREIGN KEY (`team_id_4`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nations` (
  `nation_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `short_name` varchar(50) DEFAULT NULL,
  `abbreviation` varchar(50) DEFAULT NULL,
  `demonym` varchar(50) DEFAULT NULL,
  `population` int DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `baseball_quality` int DEFAULT NULL,
  `continent_id` int DEFAULT NULL,
  `main_language_id` int DEFAULT NULL,
  `quality_total` int DEFAULT NULL,
  `capital_id` int DEFAULT NULL,
  `use_hardcoded_ml_player_origins` tinyint DEFAULT NULL,
  `this_is_the_usa` tinyint DEFAULT NULL,
  PRIMARY KEY (`nation_id`),
  KEY `fk_nations_continent` (`continent_id`),
  KEY `fk_nations_language` (`main_language_id`),
  KEY `fk_nations_capital_city` (`capital_id`),
  CONSTRAINT `fk_nations_capital_city` FOREIGN KEY (`capital_id`) REFERENCES `cities` (`city_id`),
  CONSTRAINT `fk_nations_continent` FOREIGN KEY (`continent_id`) REFERENCES `continents` (`continent_id`),
  CONSTRAINT `fk_nations_language` FOREIGN KEY (`main_language_id`) REFERENCES `languages` (`language_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parks`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parks` (
  `park_id` int NOT NULL,
  `long` double DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `dimensions_x` smallint DEFAULT NULL,
  `dimensions_y` smallint DEFAULT NULL,
  `batter_left_x` smallint DEFAULT NULL,
  `batter_left_y` smallint DEFAULT NULL,
  `batter_right_x` smallint DEFAULT NULL,
  `batter_right_y` smallint DEFAULT NULL,
  `bases_x0` smallint DEFAULT NULL,
  `bases_x1` smallint DEFAULT NULL,
  `bases_x2` smallint DEFAULT NULL,
  `bases_y0` smallint DEFAULT NULL,
  `bases_y1` smallint DEFAULT NULL,
  `bases_y2` smallint DEFAULT NULL,
  `positions_x0` smallint DEFAULT NULL,
  `positions_x1` smallint DEFAULT NULL,
  `positions_x2` smallint DEFAULT NULL,
  `positions_x3` smallint DEFAULT NULL,
  `positions_x4` smallint DEFAULT NULL,
  `positions_x5` smallint DEFAULT NULL,
  `positions_x6` smallint DEFAULT NULL,
  `positions_x7` smallint DEFAULT NULL,
  `positions_x8` smallint DEFAULT NULL,
  `positions_x9` smallint DEFAULT NULL,
  `positions_y0` smallint DEFAULT NULL,
  `positions_y1` smallint DEFAULT NULL,
  `positions_y2` smallint DEFAULT NULL,
  `positions_y3` smallint DEFAULT NULL,
  `positions_y4` smallint DEFAULT NULL,
  `positions_y5` smallint DEFAULT NULL,
  `positions_y6` smallint DEFAULT NULL,
  `positions_y7` smallint DEFAULT NULL,
  `positions_y8` smallint DEFAULT NULL,
  `positions_y9` smallint DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `avg_l` double DEFAULT NULL,
  `avg_r` double DEFAULT NULL,
  `d` double DEFAULT NULL,
  `t` double DEFAULT NULL,
  `hr` double DEFAULT NULL,
  `hr_r` double DEFAULT NULL,
  `hr_l` double DEFAULT NULL,
  `temperature0` smallint DEFAULT NULL,
  `temperature1` smallint DEFAULT NULL,
  `temperature2` smallint DEFAULT NULL,
  `temperature3` smallint DEFAULT NULL,
  `temperature4` smallint DEFAULT NULL,
  `temperature5` smallint DEFAULT NULL,
  `temperature6` smallint DEFAULT NULL,
  `temperature7` smallint DEFAULT NULL,
  `temperature8` smallint DEFAULT NULL,
  `temperature9` smallint DEFAULT NULL,
  `temperature10` smallint DEFAULT NULL,
  `temperature11` smallint DEFAULT NULL,
  `rain0` smallint DEFAULT NULL,
  `rain1` smallint DEFAULT NULL,
  `rain2` smallint DEFAULT NULL,
  `rain3` smallint DEFAULT NULL,
  `rain4` smallint DEFAULT NULL,
  `rain5` smallint DEFAULT NULL,
  `rain6` smallint DEFAULT NULL,
  `rain7` smallint DEFAULT NULL,
  `rain8` smallint DEFAULT NULL,
  `rain9` smallint DEFAULT NULL,
  `rain10` smallint DEFAULT NULL,
  `rain11` smallint DEFAULT NULL,
  `wind` smallint DEFAULT NULL,
  `wind_direction` smallint DEFAULT NULL,
  `distances0` smallint DEFAULT NULL,
  `distances1` smallint DEFAULT NULL,
  `distances2` smallint DEFAULT NULL,
  `distances3` smallint DEFAULT NULL,
  `distances4` smallint DEFAULT NULL,
  `distances5` smallint DEFAULT NULL,
  `distances6` smallint DEFAULT NULL,
  `wall_heights0` smallint DEFAULT NULL,
  `wall_heights1` smallint DEFAULT NULL,
  `wall_heights2` smallint DEFAULT NULL,
  `wall_heights3` smallint DEFAULT NULL,
  `wall_heights4` smallint DEFAULT NULL,
  `wall_heights5` smallint DEFAULT NULL,
  `wall_heights6` smallint DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `picture` varchar(200) DEFAULT NULL,
  `picture_night` varchar(200) DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `type` smallint DEFAULT NULL,
  `foul_ground` smallint DEFAULT NULL,
  `turf` tinyint DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `model_folder` varchar(200) DEFAULT NULL,
  `file_name_3d_model` varchar(200) DEFAULT NULL,
  `home_team_dugout_is_at_first_base` tinyint DEFAULT NULL,
  PRIMARY KEY (`park_id`),
  KEY `fk_parks_nation` (`nation_id`),
  CONSTRAINT `fk_parks_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players` (
  `player_id` int NOT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `first_name` varchar(50) DEFAULT NULL,
  `last_name` varchar(50) DEFAULT NULL,
  `nick_name` varchar(50) DEFAULT NULL,
  `age` smallint DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `city_of_birth_id` int DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `second_nation_id` int DEFAULT NULL,
  `weight` smallint DEFAULT NULL,
  `height` smallint DEFAULT NULL,
  `retired` tinyint DEFAULT NULL,
  `free_agent` tinyint DEFAULT NULL,
  `last_league_id` int DEFAULT NULL,
  `last_team_id` int DEFAULT NULL,
  `organization_id` int DEFAULT NULL,
  `last_organization_id` int DEFAULT NULL,
  `language_ids0` int DEFAULT NULL,
  `language_ids1` int DEFAULT NULL,
  `uniform_number` smallint DEFAULT NULL,
  `experience` smallint DEFAULT NULL,
  `person_type` smallint DEFAULT NULL,
  `bats` smallint DEFAULT NULL,
  `throws` smallint DEFAULT NULL,
  `personality_greed` smallint DEFAULT NULL,
  `personality_loyalty` smallint DEFAULT NULL,
  `personality_play_for_winner` smallint DEFAULT NULL,
  `personality_work_ethic` smallint DEFAULT NULL,
  `personality_intelligence` smallint DEFAULT NULL,
  `personality_leader` smallint DEFAULT NULL,
  `historical_id` varchar(50) DEFAULT NULL,
  `historical_team_id` varchar(50) DEFAULT NULL,
  `best_contract_offer_id` int DEFAULT NULL,
  `injury_is_injured` tinyint DEFAULT NULL,
  `injury_dtd_injury` tinyint DEFAULT NULL,
  `injury_career_ending` tinyint DEFAULT NULL,
  `injury_dl_left` smallint DEFAULT NULL,
  `injury_dl_playoff_round` smallint DEFAULT NULL,
  `injury_left` smallint DEFAULT NULL,
  `dtd_injury_effect` smallint DEFAULT NULL,
  `dtd_injury_effect_hit` smallint DEFAULT NULL,
  `dtd_injury_effect_throw` smallint DEFAULT NULL,
  `dtd_injury_effect_run` smallint DEFAULT NULL,
  `injury_id` smallint DEFAULT NULL,
  `injury_id2` smallint DEFAULT NULL,
  `injury_dtd_injury2` tinyint DEFAULT NULL,
  `injury_left2` smallint DEFAULT NULL,
  `dtd_injury_effect2` smallint DEFAULT NULL,
  `dtd_injury_effect_hit2` smallint DEFAULT NULL,
  `dtd_injury_effect_throw2` smallint DEFAULT NULL,
  `dtd_injury_effect_run2` smallint DEFAULT NULL,
  `prone_overall` smallint DEFAULT NULL,
  `prone_leg` smallint DEFAULT NULL,
  `prone_back` smallint DEFAULT NULL,
  `prone_arm` smallint DEFAULT NULL,
  `fatigue_pitches0` smallint DEFAULT NULL,
  `fatigue_pitches1` smallint DEFAULT NULL,
  `fatigue_pitches2` smallint DEFAULT NULL,
  `fatigue_pitches3` smallint DEFAULT NULL,
  `fatigue_pitches4` smallint DEFAULT NULL,
  `fatigue_pitches5` smallint DEFAULT NULL,
  `fatigue_points` smallint DEFAULT NULL,
  `fatigue_played_today` tinyint DEFAULT NULL,
  `college` tinyint DEFAULT NULL,
  `acquired` smallint DEFAULT NULL,
  `acquired_date` date DEFAULT NULL,
  `draft_year` smallint DEFAULT NULL,
  `draft_round` smallint DEFAULT NULL,
  `draft_supplemental` tinyint DEFAULT NULL,
  `draft_pick` smallint DEFAULT NULL,
  `draft_overall_pick` smallint DEFAULT NULL,
  `draft_eligible` tinyint DEFAULT NULL,
  `hsc_status` smallint DEFAULT NULL,
  `redshirt` tinyint DEFAULT NULL,
  `picked_in_draft` tinyint DEFAULT NULL,
  `school` smallint DEFAULT NULL,
  `commit_school` smallint DEFAULT NULL,
  `hidden` tinyint DEFAULT NULL,
  `draft_league_id` int DEFAULT NULL,
  `draft_team_id` int DEFAULT NULL,
  `turned_coach` tinyint DEFAULT NULL,
  `hall_of_fame` tinyint DEFAULT NULL,
  `rust` smallint DEFAULT NULL,
  `inducted` smallint DEFAULT NULL,
  `strategy_override_team` tinyint DEFAULT NULL,
  `strategy_stealing` int DEFAULT NULL,
  `strategy_running` int DEFAULT NULL,
  `strategy_bunt_for_hit` int DEFAULT NULL,
  `strategy_sac_bunt` int DEFAULT NULL,
  `strategy_hit_run` int DEFAULT NULL,
  `strategy_hook_start` int DEFAULT NULL,
  `strategy_hook_relief` int DEFAULT NULL,
  `strategy_pitch_count` int DEFAULT NULL,
  `strategy_pitch_around` int DEFAULT NULL,
  `strategy_never_pinch_hit` tinyint DEFAULT NULL,
  `strategy_defensive_sub` tinyint DEFAULT NULL,
  `strategy_dtd_sit_min` tinyint DEFAULT NULL,
  `strategy_dtd_allow_ph` tinyint DEFAULT NULL,
  `local_pop` smallint DEFAULT NULL,
  `national_pop` smallint DEFAULT NULL,
  `draft_protected` tinyint DEFAULT NULL,
  `morale` smallint DEFAULT NULL,
  `morale_mod` smallint DEFAULT NULL,
  `morale_player_performance` smallint DEFAULT NULL,
  `morale_team_performance` smallint DEFAULT NULL,
  `morale_team_transactions` smallint DEFAULT NULL,
  `morale_team_chemistry` smallint DEFAULT NULL,
  `morale_player_role` smallint DEFAULT NULL,
  `expectation` smallint DEFAULT NULL,
  `on_loan` tinyint DEFAULT NULL,
  `loan_league_id` int DEFAULT NULL,
  `loan_team_id` int DEFAULT NULL,
  PRIMARY KEY (`player_id`),
  KEY `fk_players_team` (`team_id`),
  KEY `fk_players_league` (`league_id`),
  KEY `fk_players_birth_city` (`city_of_birth_id`),
  KEY `fk_players_nation` (`nation_id`),
  KEY `fk_players_second_nation` (`second_nation_id`),
  KEY `fk_players_last_league` (`last_league_id`),
  KEY `fk_players_last_team` (`last_team_id`),
  KEY `fk_players_organization` (`organization_id`),
  KEY `fk_players_last_organization` (`last_organization_id`),
  KEY `fk_players_draft_league` (`draft_league_id`),
  KEY `fk_players_draft_team` (`draft_team_id`),
  KEY `fk_players_loan_league` (`loan_league_id`),
  KEY `fk_players_loan_team` (`loan_team_id`),
  CONSTRAINT `fk_players_birth_city` FOREIGN KEY (`city_of_birth_id`) REFERENCES `cities` (`city_id`),
  CONSTRAINT `fk_players_draft_league` FOREIGN KEY (`draft_league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_players_draft_team` FOREIGN KEY (`draft_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_last_league` FOREIGN KEY (`last_league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_players_last_organization` FOREIGN KEY (`last_organization_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_last_team` FOREIGN KEY (`last_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_players_loan_league` FOREIGN KEY (`loan_league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_players_loan_team` FOREIGN KEY (`loan_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_players_organization` FOREIGN KEY (`organization_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_second_nation` FOREIGN KEY (`second_nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_players_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_at_bat_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_at_bat_batting_stats` (
  `player_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `opponent_player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `sac` tinyint DEFAULT NULL,
  `balls` smallint DEFAULT NULL,
  `strikes` smallint DEFAULT NULL,
  `result` smallint DEFAULT NULL,
  `base1` tinyint DEFAULT NULL,
  `base2` tinyint DEFAULT NULL,
  `base3` tinyint DEFAULT NULL,
  `Close` tinyint DEFAULT NULL,
  `pinch` tinyint DEFAULT NULL,
  `inning` smallint DEFAULT NULL,
  `run_diff` smallint DEFAULT NULL,
  `outs` smallint DEFAULT NULL,
  `sb` smallint DEFAULT NULL,
  `cs` smallint DEFAULT NULL,
  `rbi` smallint DEFAULT NULL,
  `r` smallint DEFAULT NULL,
  `spot` smallint DEFAULT NULL,
  `hit_loc` smallint DEFAULT NULL,
  `hit_xy` smallint DEFAULT NULL,
  `exit_velo` double DEFAULT NULL,
  `launch_angle` smallint DEFAULT NULL,
  `sprint_speed` smallint DEFAULT NULL,
  KEY `fk_players_at_bat_player` (`player_id`),
  KEY `fk_players_at_bat_opponent` (`opponent_player_id`),
  KEY `fk_players_at_bat_team` (`team_id`),
  KEY `fk_players_at_bat_game` (`game_id`),
  CONSTRAINT `fk_players_at_bat_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`),
  CONSTRAINT `fk_players_at_bat_opponent` FOREIGN KEY (`opponent_player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_at_bat_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_at_bat_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_awards`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_awards` (
  `player_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `award_id` smallint DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `season` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `day` smallint DEFAULT NULL,
  `month` smallint DEFAULT NULL,
  `finish` smallint DEFAULT NULL,
  KEY `fk_players_awards_player` (`player_id`),
  KEY `fk_players_awards_team` (`team_id`),
  CONSTRAINT `fk_players_awards_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_awards_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_batting`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_batting` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `bats` smallint DEFAULT NULL,
  `batting_ratings_overall_contact` smallint DEFAULT NULL,
  `batting_ratings_overall_gap` smallint DEFAULT NULL,
  `batting_ratings_overall_eye` smallint DEFAULT NULL,
  `batting_ratings_overall_strikeouts` smallint DEFAULT NULL,
  `batting_ratings_overall_hp` smallint DEFAULT NULL,
  `batting_ratings_overall_power` smallint DEFAULT NULL,
  `batting_ratings_overall_babip` smallint DEFAULT NULL,
  `batting_ratings_vsr_contact` smallint DEFAULT NULL,
  `batting_ratings_vsr_gap` smallint DEFAULT NULL,
  `batting_ratings_vsr_eye` smallint DEFAULT NULL,
  `batting_ratings_vsr_strikeouts` smallint DEFAULT NULL,
  `batting_ratings_vsr_hp` smallint DEFAULT NULL,
  `batting_ratings_vsr_power` smallint DEFAULT NULL,
  `batting_ratings_vsr_babip` smallint DEFAULT NULL,
  `batting_ratings_vsl_contact` smallint DEFAULT NULL,
  `batting_ratings_vsl_gap` smallint DEFAULT NULL,
  `batting_ratings_vsl_eye` smallint DEFAULT NULL,
  `batting_ratings_vsl_strikeouts` smallint DEFAULT NULL,
  `batting_ratings_vsl_hp` smallint DEFAULT NULL,
  `batting_ratings_vsl_power` smallint DEFAULT NULL,
  `batting_ratings_vsl_babip` smallint DEFAULT NULL,
  `batting_ratings_talent_contact` smallint DEFAULT NULL,
  `batting_ratings_talent_gap` smallint DEFAULT NULL,
  `batting_ratings_talent_eye` smallint DEFAULT NULL,
  `batting_ratings_talent_strikeouts` smallint DEFAULT NULL,
  `batting_ratings_talent_hp` smallint DEFAULT NULL,
  `batting_ratings_talent_power` smallint DEFAULT NULL,
  `batting_ratings_talent_babip` smallint DEFAULT NULL,
  `batting_ratings_misc_bunt` smallint DEFAULT NULL,
  `batting_ratings_misc_bunt_for_hit` smallint DEFAULT NULL,
  `batting_ratings_misc_gb_hitter_type` smallint DEFAULT NULL,
  `batting_ratings_misc_fb_hitter_type` smallint DEFAULT NULL,
  `running_ratings_speed` smallint DEFAULT NULL,
  `running_ratings_stealing_rate` smallint DEFAULT NULL,
  `running_ratings_stealing` smallint DEFAULT NULL,
  `running_ratings_baserunning` smallint DEFAULT NULL,
  KEY `fk_players_batting_player` (`player_id`),
  KEY `fk_players_batting_team` (`team_id`),
  CONSTRAINT `fk_players_batting_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_career_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_career_batting_stats` (
  `player_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `ab` smallint DEFAULT NULL,
  `h` smallint DEFAULT NULL,
  `k` smallint DEFAULT NULL,
  `pa` smallint DEFAULT NULL,
  `pitches_seen` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `gs` smallint DEFAULT NULL,
  `d` smallint DEFAULT NULL,
  `t` smallint DEFAULT NULL,
  `hr` smallint DEFAULT NULL,
  `r` smallint DEFAULT NULL,
  `rbi` smallint DEFAULT NULL,
  `sb` smallint DEFAULT NULL,
  `cs` smallint DEFAULT NULL,
  `bb` smallint DEFAULT NULL,
  `ibb` smallint DEFAULT NULL,
  `gdp` smallint DEFAULT NULL,
  `sh` smallint DEFAULT NULL,
  `sf` smallint DEFAULT NULL,
  `hp` smallint DEFAULT NULL,
  `ci` smallint DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `stint` smallint DEFAULT NULL,
  `ubr` double DEFAULT NULL,
  `war` double DEFAULT NULL,
  KEY `fk_players_career_batting_player` (`player_id`),
  KEY `fk_players_career_batting_team` (`team_id`),
  KEY `fk_players_career_batting_game` (`game_id`),
  CONSTRAINT `fk_players_career_batting_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`),
  CONSTRAINT `fk_players_career_batting_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_career_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_career_fielding_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_career_fielding_stats` (
  `player_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `tc` smallint DEFAULT NULL,
  `a` smallint DEFAULT NULL,
  `po` smallint DEFAULT NULL,
  `er` smallint DEFAULT NULL,
  `ip` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `gs` smallint DEFAULT NULL,
  `e` smallint DEFAULT NULL,
  `dp` smallint DEFAULT NULL,
  `tp` smallint DEFAULT NULL,
  `pb` smallint DEFAULT NULL,
  `sba` smallint DEFAULT NULL,
  `rto` smallint DEFAULT NULL,
  `ipf` smallint DEFAULT NULL,
  `plays` smallint DEFAULT NULL,
  `plays_base` smallint DEFAULT NULL,
  `roe` smallint DEFAULT NULL,
  `opps_0` smallint DEFAULT NULL,
  `opps_made_0` smallint DEFAULT NULL,
  `opps_1` smallint DEFAULT NULL,
  `opps_made_1` smallint DEFAULT NULL,
  `opps_2` smallint DEFAULT NULL,
  `opps_made_2` smallint DEFAULT NULL,
  `opps_3` smallint DEFAULT NULL,
  `opps_made_3` smallint DEFAULT NULL,
  `opps_4` smallint DEFAULT NULL,
  `opps_made_4` smallint DEFAULT NULL,
  `opps_5` smallint DEFAULT NULL,
  `opps_made_5` smallint DEFAULT NULL,
  `framing` double DEFAULT NULL,
  `arm` double DEFAULT NULL,
  `zr` double DEFAULT NULL,
  KEY `fk_players_career_fielding_player` (`player_id`),
  KEY `fk_players_career_fielding_team` (`team_id`),
  CONSTRAINT `fk_players_career_fielding_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_career_fielding_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_career_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_career_pitching_stats` (
  `player_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ip` smallint DEFAULT NULL,
  `ab` smallint DEFAULT NULL,
  `tb` smallint DEFAULT NULL,
  `ha` smallint DEFAULT NULL,
  `k` smallint DEFAULT NULL,
  `bf` smallint DEFAULT NULL,
  `rs` smallint DEFAULT NULL,
  `bb` smallint DEFAULT NULL,
  `r` smallint DEFAULT NULL,
  `er` smallint DEFAULT NULL,
  `gb` smallint DEFAULT NULL,
  `fb` smallint DEFAULT NULL,
  `pi` smallint DEFAULT NULL,
  `ipf` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `gs` smallint DEFAULT NULL,
  `w` smallint DEFAULT NULL,
  `l` smallint DEFAULT NULL,
  `s` smallint DEFAULT NULL,
  `sa` smallint DEFAULT NULL,
  `da` smallint DEFAULT NULL,
  `sh` smallint DEFAULT NULL,
  `sf` smallint DEFAULT NULL,
  `ta` smallint DEFAULT NULL,
  `hra` smallint DEFAULT NULL,
  `bk` smallint DEFAULT NULL,
  `ci` smallint DEFAULT NULL,
  `iw` smallint DEFAULT NULL,
  `wp` smallint DEFAULT NULL,
  `hp` smallint DEFAULT NULL,
  `gf` smallint DEFAULT NULL,
  `dp` smallint DEFAULT NULL,
  `qs` smallint DEFAULT NULL,
  `svo` smallint DEFAULT NULL,
  `bs` smallint DEFAULT NULL,
  `ra` smallint DEFAULT NULL,
  `cg` smallint DEFAULT NULL,
  `sho` smallint DEFAULT NULL,
  `sb` smallint DEFAULT NULL,
  `cs` smallint DEFAULT NULL,
  `hld` smallint DEFAULT NULL,
  `ir` double DEFAULT NULL,
  `irs` double DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `li` double DEFAULT NULL,
  `stint` smallint DEFAULT NULL,
  `outs` smallint DEFAULT NULL,
  `sd` smallint DEFAULT NULL,
  `md` smallint DEFAULT NULL,
  `war` double DEFAULT NULL,
  `ra9war` double DEFAULT NULL,
  KEY `fk_players_career_pitching_player` (`player_id`),
  KEY `fk_players_career_pitching_team` (`team_id`),
  KEY `fk_players_career_pitching_game` (`game_id`),
  CONSTRAINT `fk_players_career_pitching_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`),
  CONSTRAINT `fk_players_career_pitching_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_career_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_contract`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_contract` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `is_major` tinyint DEFAULT NULL,
  `no_trade` tinyint DEFAULT NULL,
  `last_year_team_option` tinyint DEFAULT NULL,
  `last_year_player_option` tinyint DEFAULT NULL,
  `last_year_vesting_option` tinyint DEFAULT NULL,
  `next_last_year_team_option` tinyint DEFAULT NULL,
  `next_last_year_player_option` tinyint DEFAULT NULL,
  `next_last_year_vesting_option` tinyint DEFAULT NULL,
  `contract_team_id` int DEFAULT NULL,
  `contract_league_id` int DEFAULT NULL,
  `season_year` int DEFAULT NULL,
  `salary0` int DEFAULT NULL,
  `salary1` int DEFAULT NULL,
  `salary2` int DEFAULT NULL,
  `salary3` int DEFAULT NULL,
  `salary4` int DEFAULT NULL,
  `salary5` int DEFAULT NULL,
  `salary6` int DEFAULT NULL,
  `salary7` int DEFAULT NULL,
  `salary8` int DEFAULT NULL,
  `salary9` int DEFAULT NULL,
  `salary10` int DEFAULT NULL,
  `salary11` int DEFAULT NULL,
  `salary12` int DEFAULT NULL,
  `salary13` int DEFAULT NULL,
  `salary14` int DEFAULT NULL,
  `years` smallint DEFAULT NULL,
  `current_year` smallint DEFAULT NULL,
  `minimum_pa` smallint DEFAULT NULL,
  `minimum_pa_bonus` int DEFAULT NULL,
  `minimum_ip` smallint DEFAULT NULL,
  `minimum_ip_bonus` int DEFAULT NULL,
  `mvp_bonus` int DEFAULT NULL,
  `cyyoung_bonus` int DEFAULT NULL,
  `allstar_bonus` int DEFAULT NULL,
  `next_last_year_option_buyout` int DEFAULT NULL,
  `last_year_option_buyout` int DEFAULT NULL,
  `opt_out` smallint DEFAULT NULL,
  `opt_out_relegation` tinyint DEFAULT NULL,
  `retained` smallint DEFAULT NULL,
  KEY `fk_players_contract_player` (`player_id`),
  KEY `fk_players_contract_team` (`team_id`),
  KEY `fk_players_contract_contract_team` (`contract_team_id`),
  CONSTRAINT `fk_players_contract_contract_team` FOREIGN KEY (`contract_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_contract_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_contract_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_contract_extension`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_contract_extension` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `is_major` tinyint DEFAULT NULL,
  `no_trade` tinyint DEFAULT NULL,
  `last_year_team_option` tinyint DEFAULT NULL,
  `last_year_player_option` tinyint DEFAULT NULL,
  `last_year_vesting_option` tinyint DEFAULT NULL,
  `next_last_year_team_option` tinyint DEFAULT NULL,
  `next_last_year_player_option` tinyint DEFAULT NULL,
  `next_last_year_vesting_option` tinyint DEFAULT NULL,
  `contract_team_id` int DEFAULT NULL,
  `contract_league_id` int DEFAULT NULL,
  `season_year` int DEFAULT NULL,
  `salary0` int DEFAULT NULL,
  `salary1` int DEFAULT NULL,
  `salary2` int DEFAULT NULL,
  `salary3` int DEFAULT NULL,
  `salary4` int DEFAULT NULL,
  `salary5` int DEFAULT NULL,
  `salary6` int DEFAULT NULL,
  `salary7` int DEFAULT NULL,
  `salary8` int DEFAULT NULL,
  `salary9` int DEFAULT NULL,
  `salary10` int DEFAULT NULL,
  `salary11` int DEFAULT NULL,
  `salary12` int DEFAULT NULL,
  `salary13` int DEFAULT NULL,
  `salary14` int DEFAULT NULL,
  `years` smallint DEFAULT NULL,
  `current_year` smallint DEFAULT NULL,
  `minimum_pa` smallint DEFAULT NULL,
  `minimum_pa_bonus` int DEFAULT NULL,
  `minimum_ip` smallint DEFAULT NULL,
  `minimum_ip_bonus` int DEFAULT NULL,
  `mvp_bonus` int DEFAULT NULL,
  `cyyoung_bonus` int DEFAULT NULL,
  `allstar_bonus` int DEFAULT NULL,
  `next_last_year_option_buyout` int DEFAULT NULL,
  `last_year_option_buyout` int DEFAULT NULL,
  `opt_out` smallint DEFAULT NULL,
  `opt_out_relegation` tinyint DEFAULT NULL,
  KEY `fk_players_contract_extension_player` (`player_id`),
  KEY `fk_players_contract_extension_team` (`team_id`),
  KEY `fk_players_contract_extension_contract_team` (`contract_team_id`),
  CONSTRAINT `fk_players_contract_extension_contract_team` FOREIGN KEY (`contract_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_contract_extension_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_contract_extension_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_fielding`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_fielding` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `fielding_ratings_infield_range` smallint DEFAULT NULL,
  `fielding_ratings_infield_arm` smallint DEFAULT NULL,
  `fielding_ratings_turn_doubleplay` smallint DEFAULT NULL,
  `fielding_ratings_outfield_range` smallint DEFAULT NULL,
  `fielding_ratings_outfield_arm` smallint DEFAULT NULL,
  `fielding_ratings_catcher_arm` smallint DEFAULT NULL,
  `fielding_ratings_catcher_ability` smallint DEFAULT NULL,
  `fielding_ratings_catcher_framing` smallint DEFAULT NULL,
  `fielding_ratings_infield_error` smallint DEFAULT NULL,
  `fielding_ratings_outfield_error` smallint DEFAULT NULL,
  `fielding_experience0` smallint DEFAULT NULL,
  `fielding_experience1` smallint DEFAULT NULL,
  `fielding_experience2` smallint DEFAULT NULL,
  `fielding_experience3` smallint DEFAULT NULL,
  `fielding_experience4` smallint DEFAULT NULL,
  `fielding_experience5` smallint DEFAULT NULL,
  `fielding_experience6` smallint DEFAULT NULL,
  `fielding_experience7` smallint DEFAULT NULL,
  `fielding_experience8` smallint DEFAULT NULL,
  `fielding_experience9` smallint DEFAULT NULL,
  `fielding_rating_pos1` smallint DEFAULT NULL,
  `fielding_rating_pos2` smallint DEFAULT NULL,
  `fielding_rating_pos3` smallint DEFAULT NULL,
  `fielding_rating_pos4` smallint DEFAULT NULL,
  `fielding_rating_pos5` smallint DEFAULT NULL,
  `fielding_rating_pos6` smallint DEFAULT NULL,
  `fielding_rating_pos7` smallint DEFAULT NULL,
  `fielding_rating_pos8` smallint DEFAULT NULL,
  `fielding_rating_pos9` smallint DEFAULT NULL,
  `fielding_rating_pos1_pot` smallint DEFAULT NULL,
  `fielding_rating_pos2_pot` smallint DEFAULT NULL,
  `fielding_rating_pos3_pot` smallint DEFAULT NULL,
  `fielding_rating_pos4_pot` smallint DEFAULT NULL,
  `fielding_rating_pos5_pot` smallint DEFAULT NULL,
  `fielding_rating_pos6_pot` smallint DEFAULT NULL,
  `fielding_rating_pos7_pot` smallint DEFAULT NULL,
  `fielding_rating_pos8_pot` smallint DEFAULT NULL,
  `fielding_rating_pos9_pot` smallint DEFAULT NULL,
  KEY `fk_players_fielding_player` (`player_id`),
  KEY `fk_players_fielding_team` (`team_id`),
  CONSTRAINT `fk_players_fielding_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_fielding_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_game_batting`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_game_batting` (
  `player_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `ab` smallint DEFAULT NULL,
  `h` smallint DEFAULT NULL,
  `k` smallint DEFAULT NULL,
  `pa` smallint DEFAULT NULL,
  `pitches_seen` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `gs` smallint DEFAULT NULL,
  `d` smallint DEFAULT NULL,
  `t` smallint DEFAULT NULL,
  `hr` smallint DEFAULT NULL,
  `r` smallint DEFAULT NULL,
  `rbi` smallint DEFAULT NULL,
  `sb` smallint DEFAULT NULL,
  `cs` smallint DEFAULT NULL,
  `bb` smallint DEFAULT NULL,
  `ibb` smallint DEFAULT NULL,
  `gdp` smallint DEFAULT NULL,
  `sh` smallint DEFAULT NULL,
  `sf` smallint DEFAULT NULL,
  `hp` smallint DEFAULT NULL,
  `ci` smallint DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `stint` smallint DEFAULT NULL,
  `ubr` double DEFAULT NULL,
  KEY `fk_players_game_batting_player` (`player_id`),
  KEY `fk_players_game_batting_team` (`team_id`),
  KEY `fk_players_game_batting_game` (`game_id`),
  CONSTRAINT `fk_players_game_batting_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`),
  CONSTRAINT `fk_players_game_batting_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_game_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_game_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_game_pitching_stats` (
  `player_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `game_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ip` smallint DEFAULT NULL,
  `ab` smallint DEFAULT NULL,
  `tb` smallint DEFAULT NULL,
  `ha` smallint DEFAULT NULL,
  `k` smallint DEFAULT NULL,
  `bf` smallint DEFAULT NULL,
  `rs` smallint DEFAULT NULL,
  `bb` smallint DEFAULT NULL,
  `r` smallint DEFAULT NULL,
  `er` smallint DEFAULT NULL,
  `gb` smallint DEFAULT NULL,
  `fb` smallint DEFAULT NULL,
  `pi` smallint DEFAULT NULL,
  `ipf` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `gs` smallint DEFAULT NULL,
  `w` smallint DEFAULT NULL,
  `l` smallint DEFAULT NULL,
  `s` smallint DEFAULT NULL,
  `sa` smallint DEFAULT NULL,
  `da` smallint DEFAULT NULL,
  `sh` smallint DEFAULT NULL,
  `sf` smallint DEFAULT NULL,
  `ta` smallint DEFAULT NULL,
  `hra` smallint DEFAULT NULL,
  `bk` smallint DEFAULT NULL,
  `ci` smallint DEFAULT NULL,
  `iw` smallint DEFAULT NULL,
  `wp` smallint DEFAULT NULL,
  `hp` smallint DEFAULT NULL,
  `gf` smallint DEFAULT NULL,
  `dp` smallint DEFAULT NULL,
  `qs` smallint DEFAULT NULL,
  `svo` smallint DEFAULT NULL,
  `bs` smallint DEFAULT NULL,
  `ra` smallint DEFAULT NULL,
  `cg` smallint DEFAULT NULL,
  `sho` smallint DEFAULT NULL,
  `sb` smallint DEFAULT NULL,
  `cs` smallint DEFAULT NULL,
  `hld` smallint DEFAULT NULL,
  `ir` double DEFAULT NULL,
  `irs` double DEFAULT NULL,
  `wpa` double DEFAULT NULL,
  `li` double DEFAULT NULL,
  `stint` smallint DEFAULT NULL,
  `outs` smallint DEFAULT NULL,
  `sd` smallint DEFAULT NULL,
  `md` smallint DEFAULT NULL,
  KEY `fk_players_game_pitching_player` (`player_id`),
  KEY `fk_players_game_pitching_team` (`team_id`),
  KEY `fk_players_game_pitching_game` (`game_id`),
  CONSTRAINT `fk_players_game_pitching_game` FOREIGN KEY (`game_id`) REFERENCES `games` (`game_id`),
  CONSTRAINT `fk_players_game_pitching_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_game_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_individual_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_individual_batting_stats` (
  `player_id` int DEFAULT NULL,
  `opponent_id` int DEFAULT NULL,
  `ab` smallint DEFAULT NULL,
  `h` smallint DEFAULT NULL,
  `hr` smallint DEFAULT NULL,
  KEY `fk_players_individual_batting_player` (`player_id`),
  CONSTRAINT `fk_players_individual_batting_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_injury_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_injury_history` (
  `player_id` int DEFAULT NULL,
  `date` date DEFAULT NULL,
  `length` smallint DEFAULT NULL,
  `setbacks` smallint DEFAULT NULL,
  `day_to_day` tinyint DEFAULT NULL,
  `effect` smallint DEFAULT NULL,
  `body_part` smallint DEFAULT NULL,
  KEY `fk_players_injury_history_player` (`player_id`),
  CONSTRAINT `fk_players_injury_history_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_league_leader`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_league_leader` (
  `player_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `category` smallint DEFAULT NULL,
  `place` smallint DEFAULT NULL,
  `amount` double DEFAULT NULL,
  KEY `fk_players_league_leader_player` (`player_id`),
  CONSTRAINT `fk_players_league_leader_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_pitching`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_pitching` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `pitching_ratings_overall_stuff` smallint DEFAULT NULL,
  `pitching_ratings_overall_movement` smallint DEFAULT NULL,
  `pitching_ratings_overall_hra` smallint DEFAULT NULL,
  `pitching_ratings_overall_pbabip` smallint DEFAULT NULL,
  `pitching_ratings_overall_control` smallint DEFAULT NULL,
  `pitching_ratings_overall_balk` smallint DEFAULT NULL,
  `pitching_ratings_overall_hp` smallint DEFAULT NULL,
  `pitching_ratings_overall_wild_pitch` smallint DEFAULT NULL,
  `pitching_ratings_vsr_stuff` smallint DEFAULT NULL,
  `pitching_ratings_vsr_movement` smallint DEFAULT NULL,
  `pitching_ratings_vsr_hra` smallint DEFAULT NULL,
  `pitching_ratings_vsr_pbabip` smallint DEFAULT NULL,
  `pitching_ratings_vsr_control` smallint DEFAULT NULL,
  `pitching_ratings_vsr_balk` smallint DEFAULT NULL,
  `pitching_ratings_vsr_hp` smallint DEFAULT NULL,
  `pitching_ratings_vsr_wild_pitch` smallint DEFAULT NULL,
  `pitching_ratings_vsl_stuff` smallint DEFAULT NULL,
  `pitching_ratings_vsl_movement` smallint DEFAULT NULL,
  `pitching_ratings_vsl_hra` smallint DEFAULT NULL,
  `pitching_ratings_vsl_pbabip` smallint DEFAULT NULL,
  `pitching_ratings_vsl_control` smallint DEFAULT NULL,
  `pitching_ratings_vsl_balk` smallint DEFAULT NULL,
  `pitching_ratings_vsl_hp` smallint DEFAULT NULL,
  `pitching_ratings_vsl_wild_pitch` smallint DEFAULT NULL,
  `pitching_ratings_talent_stuff` smallint DEFAULT NULL,
  `pitching_ratings_talent_movement` smallint DEFAULT NULL,
  `pitching_ratings_talent_hra` smallint DEFAULT NULL,
  `pitching_ratings_talent_pbabip` smallint DEFAULT NULL,
  `pitching_ratings_talent_control` smallint DEFAULT NULL,
  `pitching_ratings_talent_balk` smallint DEFAULT NULL,
  `pitching_ratings_talent_hp` smallint DEFAULT NULL,
  `pitching_ratings_talent_wild_pitch` smallint DEFAULT NULL,
  `pitching_ratings_pitches_fastball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_slider` smallint DEFAULT NULL,
  `pitching_ratings_pitches_curveball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_screwball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_forkball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_changeup` smallint DEFAULT NULL,
  `pitching_ratings_pitches_sinker` smallint DEFAULT NULL,
  `pitching_ratings_pitches_splitter` smallint DEFAULT NULL,
  `pitching_ratings_pitches_knuckleball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_cutter` smallint DEFAULT NULL,
  `pitching_ratings_pitches_circlechange` smallint DEFAULT NULL,
  `pitching_ratings_pitches_knucklecurve` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_fastball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_slider` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_curveball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_screwball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_forkball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_changeup` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_sinker` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_splitter` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_knuckleball` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_cutter` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_circlechange` smallint DEFAULT NULL,
  `pitching_ratings_pitches_talent_knucklecurve` smallint DEFAULT NULL,
  `pitching_ratings_misc_velocity` smallint DEFAULT NULL,
  `pitching_ratings_misc_velocity_target` smallint DEFAULT NULL,
  `pitching_ratings_misc_arm_slot` smallint DEFAULT NULL,
  `pitching_ratings_misc_stamina` smallint DEFAULT NULL,
  `pitching_ratings_misc_ground_fly` smallint DEFAULT NULL,
  `pitching_ratings_misc_hold` smallint DEFAULT NULL,
  KEY `fk_players_pitching_player` (`player_id`),
  KEY `fk_players_pitching_team` (`team_id`),
  CONSTRAINT `fk_players_pitching_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_roster_status`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_roster_status` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `playing_level` smallint DEFAULT NULL,
  `is_active` tinyint DEFAULT NULL,
  `is_on_secondary` tinyint DEFAULT NULL,
  `is_on_dl` tinyint DEFAULT NULL,
  `is_on_dl60` tinyint DEFAULT NULL,
  `must_be_active` tinyint DEFAULT NULL,
  `just_signed` tinyint DEFAULT NULL,
  `was_on_active` tinyint DEFAULT NULL,
  `was_on_secondary` tinyint DEFAULT NULL,
  `was_on_dl` tinyint DEFAULT NULL,
  `mlb_service_years` smallint DEFAULT NULL,
  `secondary_service_years` smallint DEFAULT NULL,
  `pro_service_years` smallint DEFAULT NULL,
  `mlb_service_days` smallint DEFAULT NULL,
  `secondary_service_days` smallint DEFAULT NULL,
  `pro_service_days` smallint DEFAULT NULL,
  `mlb_service_days_this_year` smallint DEFAULT NULL,
  `secondary_service_days_this_year` smallint DEFAULT NULL,
  `pro_service_days_this_year` smallint DEFAULT NULL,
  `dl_days_this_year` smallint DEFAULT NULL,
  `years_protected_from_rule_5` smallint DEFAULT NULL,
  `is_on_waivers` tinyint DEFAULT NULL,
  `designated_for_assignment` tinyint DEFAULT NULL,
  `irrevocable_waivers` tinyint DEFAULT NULL,
  `days_on_waivers` smallint DEFAULT NULL,
  `days_on_waivers_left` smallint DEFAULT NULL,
  `days_on_dfa_left` smallint DEFAULT NULL,
  `claimed_team_id` int DEFAULT NULL,
  `options_used` smallint DEFAULT NULL,
  `options_used_this_year` smallint DEFAULT NULL,
  `has_received_arbitration` tinyint DEFAULT NULL,
  `was_traded` tinyint DEFAULT NULL,
  `trade_status` smallint DEFAULT NULL,
  KEY `fk_players_roster_status_player` (`player_id`),
  KEY `fk_players_roster_status_team` (`team_id`),
  KEY `fk_players_roster_status_league` (`league_id`),
  KEY `fk_players_roster_status_claimed_team` (`claimed_team_id`),
  CONSTRAINT `fk_players_roster_status_claimed_team` FOREIGN KEY (`claimed_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_players_roster_status_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_players_roster_status_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_roster_status_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_salary_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_salary_history` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `year` smallint DEFAULT NULL,
  `salary` int DEFAULT NULL,
  `uniform` smallint DEFAULT NULL,
  KEY `fk_players_salary_history_player` (`player_id`),
  KEY `fk_players_salary_history_team` (`team_id`),
  CONSTRAINT `fk_players_salary_history_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_salary_history_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_streak`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_streak` (
  `player_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `streak_id` smallint DEFAULT NULL,
  `value` smallint DEFAULT NULL,
  `has_ended` tinyint DEFAULT NULL,
  `started` date DEFAULT NULL,
  `ended` date DEFAULT NULL,
  KEY `fk_players_streak_player` (`player_id`),
  CONSTRAINT `fk_players_streak_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players_value`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players_value` (
  `player_id` int DEFAULT NULL,
  `team_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `role` smallint DEFAULT NULL,
  `offensive_value` smallint DEFAULT NULL,
  `offensive_value_talent` smallint DEFAULT NULL,
  `offensive_value_vsl` smallint DEFAULT NULL,
  `offensive_value_vsr` smallint DEFAULT NULL,
  `pitching_value` smallint DEFAULT NULL,
  `pitching_value_talent` smallint DEFAULT NULL,
  `pitching_value_vsl` smallint DEFAULT NULL,
  `pitching_value_vsr` smallint DEFAULT NULL,
  `overall_value` smallint DEFAULT NULL,
  `talent_value` smallint DEFAULT NULL,
  `career_value` smallint DEFAULT NULL,
  `leadoff_value_vsl` smallint DEFAULT NULL,
  `leadoff_value_vsr` smallint DEFAULT NULL,
  `running_value` smallint DEFAULT NULL,
  `stealing_value` smallint DEFAULT NULL,
  `season_performance` double DEFAULT NULL,
  `stats_value_0` smallint DEFAULT NULL,
  `stats_value_1` smallint DEFAULT NULL,
  `stats_value_2` smallint DEFAULT NULL,
  `stats_mod_0` smallint DEFAULT NULL,
  `stats_mod_1` smallint DEFAULT NULL,
  `stats_mod_2` smallint DEFAULT NULL,
  `ratings_value` smallint DEFAULT NULL,
  `overall_sp` smallint DEFAULT NULL,
  `overall_rp` smallint DEFAULT NULL,
  `overall_c` smallint DEFAULT NULL,
  `overall_1b` smallint DEFAULT NULL,
  `overall_2b` smallint DEFAULT NULL,
  `overall_3b` smallint DEFAULT NULL,
  `overall_ss` smallint DEFAULT NULL,
  `overall_lf` smallint DEFAULT NULL,
  `overall_cf` smallint DEFAULT NULL,
  `overall_rf` smallint DEFAULT NULL,
  `award_bat` double DEFAULT NULL,
  `award_pit` double DEFAULT NULL,
  `award_field` double DEFAULT NULL,
  `oa` smallint DEFAULT NULL,
  `pot` smallint DEFAULT NULL,
  `oa_rating` smallint DEFAULT NULL,
  `pot_rating` smallint DEFAULT NULL,
  KEY `fk_players_value_player` (`player_id`),
  KEY `fk_players_value_team` (`team_id`),
  CONSTRAINT `fk_players_value_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_players_value_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `projected_starting_pitchers`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projected_starting_pitchers` (
  `team_id` int DEFAULT NULL,
  `starter_0` int DEFAULT NULL,
  `starter_1` int DEFAULT NULL,
  `starter_2` int DEFAULT NULL,
  `starter_3` int DEFAULT NULL,
  `starter_4` int DEFAULT NULL,
  `starter_5` int DEFAULT NULL,
  `starter_6` int DEFAULT NULL,
  `starter_7` int DEFAULT NULL,
  KEY `fk_projected_starting_pitchers_team` (`team_id`),
  KEY `fk_projected_starting_pitchers_0` (`starter_0`),
  KEY `fk_projected_starting_pitchers_1` (`starter_1`),
  KEY `fk_projected_starting_pitchers_2` (`starter_2`),
  KEY `fk_projected_starting_pitchers_3` (`starter_3`),
  KEY `fk_projected_starting_pitchers_4` (`starter_4`),
  KEY `fk_projected_starting_pitchers_5` (`starter_5`),
  KEY `fk_projected_starting_pitchers_6` (`starter_6`),
  KEY `fk_projected_starting_pitchers_7` (`starter_7`),
  CONSTRAINT `fk_projected_starting_pitchers_0` FOREIGN KEY (`starter_0`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_1` FOREIGN KEY (`starter_1`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_2` FOREIGN KEY (`starter_2`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_3` FOREIGN KEY (`starter_3`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_4` FOREIGN KEY (`starter_4`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_5` FOREIGN KEY (`starter_5`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_6` FOREIGN KEY (`starter_6`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_7` FOREIGN KEY (`starter_7`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_projected_starting_pitchers_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `states`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `states` (
  `state_id` int NOT NULL,
  `nation_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbreviation` varchar(50) DEFAULT NULL,
  `population` int DEFAULT NULL,
  `main_language_id` int DEFAULT NULL,
  PRIMARY KEY (`state_id`,`nation_id`),
  KEY `fk_states_nation` (`nation_id`),
  KEY `fk_states_language` (`main_language_id`),
  CONSTRAINT `fk_states_language` FOREIGN KEY (`main_language_id`) REFERENCES `languages` (`language_id`),
  CONSTRAINT `fk_states_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sub_leagues`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sub_leagues` (
  `league_id` int NOT NULL,
  `sub_league_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbr` varchar(50) DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `designated_hitter` tinyint DEFAULT NULL,
  PRIMARY KEY (`league_id`,`sub_league_id`),
  CONSTRAINT `fk_sub_leagues_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_affiliations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_affiliations` (
  `team_id` int NOT NULL,
  `affiliated_team_id` int NOT NULL,
  PRIMARY KEY (`team_id`,`affiliated_team_id`),
  KEY `fk_team_affiliations_affiliate` (`affiliated_team_id`),
  CONSTRAINT `fk_team_affiliations_affiliate` FOREIGN KEY (`affiliated_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_team_affiliations_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_batting_stats` (
  `team_id` int NOT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `pa` int DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `h` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `d` int DEFAULT NULL,
  `t` int DEFAULT NULL,
  `hr` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `rbi` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `ibb` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `gdp` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `ebh` int DEFAULT NULL,
  `pitches_seen` int DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `rc` double DEFAULT NULL,
  `rc27` double DEFAULT NULL,
  `iso` double DEFAULT NULL,
  `woba` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `sbp` double DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_batting_stats_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_bullpen_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_bullpen_pitching_stats` (
  `team_id` int NOT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_bullpen_pitching_stats_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_fielding_stats_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_fielding_stats_stats` (
  `team_id` int NOT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `tc` int DEFAULT NULL,
  `a` int DEFAULT NULL,
  `po` int DEFAULT NULL,
  `e` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `tp` int DEFAULT NULL,
  `pb` int DEFAULT NULL,
  `sba` int DEFAULT NULL,
  `rto` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `range` double DEFAULT NULL,
  `rtop` double DEFAULT NULL,
  `cera` double DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_fielding_stats_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_financials`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_financials` (
  `team_id` int NOT NULL,
  `gate_revenue` int DEFAULT NULL,
  `gate_share_gained` int DEFAULT NULL,
  `gate_share_lost` int DEFAULT NULL,
  `season_ticket_revenue` int DEFAULT NULL,
  `media_revenue` int DEFAULT NULL,
  `merchandising_revenue` int DEFAULT NULL,
  `revenue_sharing` int DEFAULT NULL,
  `luxury_sharing` int DEFAULT NULL,
  `playoff_revenue` int DEFAULT NULL,
  `cash` int DEFAULT NULL,
  `cash_owner` int DEFAULT NULL,
  `cash_trades` int DEFAULT NULL,
  `previous_balance` int DEFAULT NULL,
  `player_expenses` int DEFAULT NULL,
  `staff_expenses` int DEFAULT NULL,
  `stadium_expenses` int DEFAULT NULL,
  `season_tickets` int DEFAULT NULL,
  `attendance` int DEFAULT NULL,
  `fan_interest` smallint DEFAULT NULL,
  `fan_loyalty` smallint DEFAULT NULL,
  `fan_modifier` smallint DEFAULT NULL,
  `fan_interest_visible` smallint DEFAULT NULL,
  `ticket_price` double DEFAULT NULL,
  `local_media_contract` int DEFAULT NULL,
  `local_media_contract_expires` int DEFAULT NULL,
  `national_media_contract` int DEFAULT NULL,
  `national_media_contract_expires` int DEFAULT NULL,
  `scouting_budget` int DEFAULT NULL,
  `development_budget` int DEFAULT NULL,
  `draft_budget` int DEFAULT NULL,
  `draft_expenses` int DEFAULT NULL,
  `intl_fa_budget` int DEFAULT NULL,
  `spent_in_intl` int DEFAULT NULL,
  `budget` int DEFAULT NULL,
  `market` smallint DEFAULT NULL,
  `owner_expectation` smallint DEFAULT NULL,
  `total_revenue` int DEFAULT NULL,
  `total_expenses` int DEFAULT NULL,
  `financial_balance` int DEFAULT NULL,
  `budget_balance` int DEFAULT NULL,
  `player_payroll` int DEFAULT NULL,
  `player_payroll_next_season` int DEFAULT NULL,
  `player_payroll_offered` int DEFAULT NULL,
  `mode` smallint DEFAULT NULL,
  `cash_trades_available` int DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_financials_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbr` varchar(50) DEFAULT NULL,
  `nickname` varchar(50) DEFAULT NULL,
  `best_hitter_id` int DEFAULT NULL,
  `best_pitcher_id` int DEFAULT NULL,
  `best_rookie_id` int DEFAULT NULL,
  `manager_id` int DEFAULT NULL,
  `made_playoffs` tinyint DEFAULT NULL,
  `won_playoffs` tinyint DEFAULT NULL,
  `fired` tinyint DEFAULT NULL,
  `position_in_division` smallint DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  KEY `fk_team_history_best_hitter` (`best_hitter_id`),
  KEY `fk_team_history_best_pitcher` (`best_pitcher_id`),
  KEY `fk_team_history_best_rookie` (`best_rookie_id`),
  KEY `fk_team_history_manager` (`manager_id`),
  CONSTRAINT `fk_team_history_best_hitter` FOREIGN KEY (`best_hitter_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_team_history_best_pitcher` FOREIGN KEY (`best_pitcher_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_team_history_best_rookie` FOREIGN KEY (`best_rookie_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_team_history_manager` FOREIGN KEY (`manager_id`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_history_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history_batting_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history_batting_stats` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `pa` int DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `h` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `d` int DEFAULT NULL,
  `t` int DEFAULT NULL,
  `hr` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `rbi` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `ibb` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `gdp` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `ebh` int DEFAULT NULL,
  `pitches_seen` int DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `rc` double DEFAULT NULL,
  `rc27` double DEFAULT NULL,
  `iso` double DEFAULT NULL,
  `woba` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `sbp` double DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  CONSTRAINT `fk_team_history_batting_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history_fielding_stats_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history_fielding_stats_stats` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `position` smallint DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `tc` int DEFAULT NULL,
  `a` int DEFAULT NULL,
  `po` int DEFAULT NULL,
  `e` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `tp` int DEFAULT NULL,
  `pb` int DEFAULT NULL,
  `sba` int DEFAULT NULL,
  `rto` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `range` double DEFAULT NULL,
  `rtop` double DEFAULT NULL,
  `cera` double DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  CONSTRAINT `fk_team_history_fielding_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history_financials`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history_financials` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `gate_revenue` int DEFAULT NULL,
  `gate_share_gained` int DEFAULT NULL,
  `gate_share_lost` int DEFAULT NULL,
  `season_ticket_revenue` int DEFAULT NULL,
  `media_revenue` int DEFAULT NULL,
  `merchandising_revenue` int DEFAULT NULL,
  `revenue_sharing` int DEFAULT NULL,
  `luxury_sharing` int DEFAULT NULL,
  `playoff_revenue` int DEFAULT NULL,
  `cash` int DEFAULT NULL,
  `cash_owner` int DEFAULT NULL,
  `cash_trades` int DEFAULT NULL,
  `previous_balance` int DEFAULT NULL,
  `player_expenses` int DEFAULT NULL,
  `staff_expenses` int DEFAULT NULL,
  `stadium_expenses` int DEFAULT NULL,
  `season_tickets` int DEFAULT NULL,
  `attendance` int DEFAULT NULL,
  `fan_interest` smallint DEFAULT NULL,
  `fan_loyalty` smallint DEFAULT NULL,
  `fan_modifier` smallint DEFAULT NULL,
  `fan_interest_visible` smallint DEFAULT NULL,
  `ticket_price` double DEFAULT NULL,
  `local_media_contract` int DEFAULT NULL,
  `local_media_contract_expires` int DEFAULT NULL,
  `national_media_contract` int DEFAULT NULL,
  `national_media_contract_expires` int DEFAULT NULL,
  `scouting_budget` int DEFAULT NULL,
  `development_budget` int DEFAULT NULL,
  `draft_budget` int DEFAULT NULL,
  `draft_expenses` int DEFAULT NULL,
  `intl_fa_budget` int DEFAULT NULL,
  `spent_in_intl` int DEFAULT NULL,
  `budget` int DEFAULT NULL,
  `market` smallint DEFAULT NULL,
  `owner_expectation` smallint DEFAULT NULL,
  `total_revenue` int DEFAULT NULL,
  `total_expenses` int DEFAULT NULL,
  `financial_balance` int DEFAULT NULL,
  `budget_balance` int DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  CONSTRAINT `fk_team_history_financials_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history_pitching_stats` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  CONSTRAINT `fk_team_history_pitching_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_history_record`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_history_record` (
  `team_id` int NOT NULL,
  `year` smallint NOT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` smallint DEFAULT NULL,
  `division_id` smallint DEFAULT NULL,
  `g` smallint DEFAULT NULL,
  `w` smallint DEFAULT NULL,
  `l` smallint DEFAULT NULL,
  `t` smallint DEFAULT NULL,
  `pos` smallint DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `gb` double DEFAULT NULL,
  `streak` smallint DEFAULT NULL,
  `magic_number` smallint DEFAULT NULL,
  PRIMARY KEY (`team_id`,`year`),
  CONSTRAINT `fk_team_history_record_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_last_financials`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_last_financials` (
  `team_id` int NOT NULL,
  `gate_revenue` int DEFAULT NULL,
  `gate_share_gained` int DEFAULT NULL,
  `gate_share_lost` int DEFAULT NULL,
  `season_ticket_revenue` int DEFAULT NULL,
  `media_revenue` int DEFAULT NULL,
  `merchandising_revenue` int DEFAULT NULL,
  `revenue_sharing` int DEFAULT NULL,
  `luxury_sharing` int DEFAULT NULL,
  `playoff_revenue` int DEFAULT NULL,
  `cash` int DEFAULT NULL,
  `cash_owner` int DEFAULT NULL,
  `cash_trades` int DEFAULT NULL,
  `previous_balance` int DEFAULT NULL,
  `player_expenses` int DEFAULT NULL,
  `staff_expenses` int DEFAULT NULL,
  `stadium_expenses` int DEFAULT NULL,
  `season_tickets` int DEFAULT NULL,
  `attendance` int DEFAULT NULL,
  `fan_interest` smallint DEFAULT NULL,
  `fan_loyalty` smallint DEFAULT NULL,
  `fan_modifier` smallint DEFAULT NULL,
  `fan_interest_visible` smallint DEFAULT NULL,
  `ticket_price` double DEFAULT NULL,
  `local_media_contract` int DEFAULT NULL,
  `local_media_contract_expires` int DEFAULT NULL,
  `national_media_contract` int DEFAULT NULL,
  `national_media_contract_expires` int DEFAULT NULL,
  `scouting_budget` int DEFAULT NULL,
  `development_budget` int DEFAULT NULL,
  `draft_budget` int DEFAULT NULL,
  `draft_expenses` int DEFAULT NULL,
  `intl_fa_budget` int DEFAULT NULL,
  `spent_in_intl` int DEFAULT NULL,
  `budget` int DEFAULT NULL,
  `market` smallint DEFAULT NULL,
  `owner_expectation` smallint DEFAULT NULL,
  `total_revenue` int DEFAULT NULL,
  `total_expenses` int DEFAULT NULL,
  `financial_balance` int DEFAULT NULL,
  `budget_balance` int DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_last_financials_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_pitching_stats` (
  `team_id` int NOT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_pitching_stats_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_record`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_record` (
  `team_id` int NOT NULL,
  `g` smallint DEFAULT NULL,
  `w` smallint DEFAULT NULL,
  `l` smallint DEFAULT NULL,
  `t` smallint DEFAULT NULL,
  `pos` smallint DEFAULT NULL,
  `pct` double DEFAULT NULL,
  `gb` double DEFAULT NULL,
  `streak` smallint DEFAULT NULL,
  `magic_number` smallint DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_record_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_relations`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_relations` (
  `league_id` int NOT NULL,
  `sub_league_id` int NOT NULL,
  `division_id` int NOT NULL,
  `team_id` int NOT NULL,
  PRIMARY KEY (`league_id`,`sub_league_id`,`division_id`,`team_id`),
  KEY `fk_team_relations_team` (`team_id`),
  CONSTRAINT `fk_team_relations_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_team_relations_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_roster`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_roster` (
  `team_id` int NOT NULL,
  `player_id` int NOT NULL,
  `list_id` smallint NOT NULL,
  PRIMARY KEY (`team_id`,`player_id`,`list_id`),
  KEY `fk_team_roster_player` (`player_id`),
  CONSTRAINT `fk_team_roster_player` FOREIGN KEY (`player_id`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_team_roster_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_roster_staff`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_roster_staff` (
  `team_id` int NOT NULL,
  `head_scout` int DEFAULT NULL,
  `manager` int DEFAULT NULL,
  `general_manager` int DEFAULT NULL,
  `pitching_coach` int DEFAULT NULL,
  `hitting_coach` int DEFAULT NULL,
  `bench_coach` int DEFAULT NULL,
  `owner` int DEFAULT NULL,
  `doctor` int DEFAULT NULL,
  `first_base_coach` int DEFAULT NULL,
  `third_base_coach` int DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  KEY `fk_team_roster_staff_head_scout` (`head_scout`),
  KEY `fk_team_roster_staff_manager` (`manager`),
  KEY `fk_team_roster_staff_general_manager` (`general_manager`),
  KEY `fk_team_roster_staff_pitching_coach` (`pitching_coach`),
  KEY `fk_team_roster_staff_hitting_coach` (`hitting_coach`),
  KEY `fk_team_roster_staff_bench_coach` (`bench_coach`),
  KEY `fk_team_roster_staff_owner` (`owner`),
  KEY `fk_team_roster_staff_doctor` (`doctor`),
  KEY `fk_team_roster_staff_first_base` (`first_base_coach`),
  KEY `fk_team_roster_staff_third_base` (`third_base_coach`),
  CONSTRAINT `fk_team_roster_staff_bench_coach` FOREIGN KEY (`bench_coach`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_doctor` FOREIGN KEY (`doctor`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_first_base` FOREIGN KEY (`first_base_coach`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_general_manager` FOREIGN KEY (`general_manager`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_head_scout` FOREIGN KEY (`head_scout`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_hitting_coach` FOREIGN KEY (`hitting_coach`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_manager` FOREIGN KEY (`manager`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_owner` FOREIGN KEY (`owner`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_pitching_coach` FOREIGN KEY (`pitching_coach`) REFERENCES `coaches` (`coach_id`),
  CONSTRAINT `fk_team_roster_staff_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_team_roster_staff_third_base` FOREIGN KEY (`third_base_coach`) REFERENCES `coaches` (`coach_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team_starting_pitching_stats`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `team_starting_pitching_stats` (
  `team_id` int NOT NULL,
  `year` smallint DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `level_id` smallint DEFAULT NULL,
  `split_id` smallint DEFAULT NULL,
  `ab` int DEFAULT NULL,
  `ip` int DEFAULT NULL,
  `bf` int DEFAULT NULL,
  `tb` int DEFAULT NULL,
  `ha` int DEFAULT NULL,
  `k` int DEFAULT NULL,
  `rs` int DEFAULT NULL,
  `bb` int DEFAULT NULL,
  `r` int DEFAULT NULL,
  `er` int DEFAULT NULL,
  `gb` int DEFAULT NULL,
  `fb` int DEFAULT NULL,
  `pi` int DEFAULT NULL,
  `ipf` int DEFAULT NULL,
  `g` int DEFAULT NULL,
  `gs` int DEFAULT NULL,
  `w` int DEFAULT NULL,
  `l` int DEFAULT NULL,
  `s` int DEFAULT NULL,
  `sa` int DEFAULT NULL,
  `da` int DEFAULT NULL,
  `sh` int DEFAULT NULL,
  `sf` int DEFAULT NULL,
  `ta` int DEFAULT NULL,
  `hra` int DEFAULT NULL,
  `bk` int DEFAULT NULL,
  `ci` int DEFAULT NULL,
  `iw` int DEFAULT NULL,
  `wp` int DEFAULT NULL,
  `hp` int DEFAULT NULL,
  `gf` int DEFAULT NULL,
  `dp` int DEFAULT NULL,
  `qs` int DEFAULT NULL,
  `svo` int DEFAULT NULL,
  `bs` int DEFAULT NULL,
  `ra` int DEFAULT NULL,
  `cg` int DEFAULT NULL,
  `sho` int DEFAULT NULL,
  `sb` int DEFAULT NULL,
  `cs` int DEFAULT NULL,
  `hld` int DEFAULT NULL,
  `r9` double DEFAULT NULL,
  `avg` double DEFAULT NULL,
  `obp` double DEFAULT NULL,
  `slg` double DEFAULT NULL,
  `ops` double DEFAULT NULL,
  `h9` double DEFAULT NULL,
  `k9` double DEFAULT NULL,
  `hr9` double DEFAULT NULL,
  `bb9` double DEFAULT NULL,
  `cgp` double DEFAULT NULL,
  `fip` double DEFAULT NULL,
  `qsp` double DEFAULT NULL,
  `winp` double DEFAULT NULL,
  `rsg` double DEFAULT NULL,
  `svp` double DEFAULT NULL,
  `bsvp` double DEFAULT NULL,
  `gfp` double DEFAULT NULL,
  `era` double DEFAULT NULL,
  `pig` double DEFAULT NULL,
  `ws` double DEFAULT NULL,
  `whip` double DEFAULT NULL,
  `gbfbp` double DEFAULT NULL,
  `kbb` double DEFAULT NULL,
  `babip` double DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  CONSTRAINT `fk_team_starting_pitching_stats_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `teams`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teams` (
  `team_id` int NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `abbr` varchar(50) DEFAULT NULL,
  `nickname` varchar(50) DEFAULT NULL,
  `logo_file_name` varchar(200) DEFAULT NULL,
  `city_id` int DEFAULT NULL,
  `park_id` int DEFAULT NULL,
  `league_id` int DEFAULT NULL,
  `sub_league_id` int DEFAULT NULL,
  `division_id` int DEFAULT NULL,
  `nation_id` int DEFAULT NULL,
  `parent_team_id` int DEFAULT NULL,
  `level` int DEFAULT NULL,
  `prevent_any_moves` tinyint DEFAULT NULL,
  `human_team` tinyint DEFAULT NULL,
  `human_id` int DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `background_color_id` varchar(8) DEFAULT NULL,
  `text_color_id` varchar(8) DEFAULT NULL,
  `ballcaps_main_color_id` varchar(8) DEFAULT NULL,
  `ballcaps_visor_color_id` varchar(8) DEFAULT NULL,
  `jersey_main_color_id` varchar(8) DEFAULT NULL,
  `jersey_away_color_id` varchar(8) DEFAULT NULL,
  `jersey_secondary_color_id` varchar(8) DEFAULT NULL,
  `jersey_pin_stripes_color_id` varchar(8) DEFAULT NULL,
  `allstar_team` tinyint DEFAULT NULL,
  `historical_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`team_id`),
  KEY `fk_teams_city` (`city_id`),
  KEY `fk_teams_park` (`park_id`),
  KEY `fk_teams_division` (`league_id`,`sub_league_id`,`division_id`),
  KEY `fk_teams_nation` (`nation_id`),
  KEY `fk_teams_parent_team` (`parent_team_id`),
  KEY `fk_teams_human_manager` (`human_id`),
  CONSTRAINT `fk_teams_city` FOREIGN KEY (`city_id`) REFERENCES `cities` (`city_id`),
  CONSTRAINT `fk_teams_division` FOREIGN KEY (`league_id`, `sub_league_id`, `division_id`) REFERENCES `divisions` (`league_id`, `sub_league_id`, `division_id`),
  CONSTRAINT `fk_teams_human_manager` FOREIGN KEY (`human_id`) REFERENCES `human_managers` (`human_manager_id`),
  CONSTRAINT `fk_teams_league` FOREIGN KEY (`league_id`) REFERENCES `leagues` (`league_id`),
  CONSTRAINT `fk_teams_nation` FOREIGN KEY (`nation_id`) REFERENCES `nations` (`nation_id`),
  CONSTRAINT `fk_teams_parent_team` FOREIGN KEY (`parent_team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_teams_park` FOREIGN KEY (`park_id`) REFERENCES `parks` (`park_id`),
  CONSTRAINT `fk_teams_sub_league` FOREIGN KEY (`league_id`, `sub_league_id`) REFERENCES `sub_leagues` (`league_id`, `sub_league_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trade_history`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trade_history` (
  `date` date DEFAULT NULL,
  `summary` varchar(255) DEFAULT NULL,
  `message_id` int DEFAULT NULL,
  `team_id_0` int DEFAULT NULL,
  `player_id_0_0` int DEFAULT NULL,
  `player_id_0_1` int DEFAULT NULL,
  `player_id_0_2` int DEFAULT NULL,
  `player_id_0_3` int DEFAULT NULL,
  `player_id_0_4` int DEFAULT NULL,
  `player_id_0_5` int DEFAULT NULL,
  `player_id_0_6` int DEFAULT NULL,
  `player_id_0_7` int DEFAULT NULL,
  `player_id_0_8` int DEFAULT NULL,
  `player_id_0_9` int DEFAULT NULL,
  `draft_round_0_0` smallint DEFAULT NULL,
  `draft_team_0_0` int DEFAULT NULL,
  `draft_round_0_1` smallint DEFAULT NULL,
  `draft_team_0_1` int DEFAULT NULL,
  `draft_round_0_2` smallint DEFAULT NULL,
  `draft_team_0_2` int DEFAULT NULL,
  `draft_round_0_3` smallint DEFAULT NULL,
  `draft_team_0_3` int DEFAULT NULL,
  `draft_round_0_4` smallint DEFAULT NULL,
  `draft_team_0_4` int DEFAULT NULL,
  `cash_0` int DEFAULT NULL,
  `iafa_cap_0` int DEFAULT NULL,
  `team_id_1` int DEFAULT NULL,
  `player_id_1_0` int DEFAULT NULL,
  `player_id_1_1` int DEFAULT NULL,
  `player_id_1_2` int DEFAULT NULL,
  `player_id_1_3` int DEFAULT NULL,
  `player_id_1_4` int DEFAULT NULL,
  `player_id_1_5` int DEFAULT NULL,
  `player_id_1_6` int DEFAULT NULL,
  `player_id_1_7` int DEFAULT NULL,
  `player_id_1_8` int DEFAULT NULL,
  `player_id_1_9` int DEFAULT NULL,
  `draft_round_1_0` smallint DEFAULT NULL,
  `draft_team_1_0` int DEFAULT NULL,
  `draft_round_1_1` smallint DEFAULT NULL,
  `draft_team_1_1` int DEFAULT NULL,
  `draft_round_1_2` smallint DEFAULT NULL,
  `draft_team_1_2` int DEFAULT NULL,
  `draft_round_1_3` smallint DEFAULT NULL,
  `draft_team_1_3` int DEFAULT NULL,
  `draft_round_1_4` smallint DEFAULT NULL,
  `draft_team_1_4` int DEFAULT NULL,
  `cash_1` int DEFAULT NULL,
  `iafa_cap_1` int DEFAULT NULL,
  KEY `fk_trade_history_message` (`message_id`),
  KEY `fk_trade_history_team_0` (`team_id_0`),
  KEY `fk_trade_history_team_1` (`team_id_1`),
  KEY `fk_trade_history_player_0_0` (`player_id_0_0`),
  KEY `fk_trade_history_player_0_1` (`player_id_0_1`),
  KEY `fk_trade_history_player_0_2` (`player_id_0_2`),
  KEY `fk_trade_history_player_0_3` (`player_id_0_3`),
  KEY `fk_trade_history_player_0_4` (`player_id_0_4`),
  KEY `fk_trade_history_player_0_5` (`player_id_0_5`),
  KEY `fk_trade_history_player_0_6` (`player_id_0_6`),
  KEY `fk_trade_history_player_0_7` (`player_id_0_7`),
  KEY `fk_trade_history_player_0_8` (`player_id_0_8`),
  KEY `fk_trade_history_player_0_9` (`player_id_0_9`),
  KEY `fk_trade_history_player_1_0` (`player_id_1_0`),
  KEY `fk_trade_history_player_1_1` (`player_id_1_1`),
  KEY `fk_trade_history_player_1_2` (`player_id_1_2`),
  KEY `fk_trade_history_player_1_3` (`player_id_1_3`),
  KEY `fk_trade_history_player_1_4` (`player_id_1_4`),
  KEY `fk_trade_history_player_1_5` (`player_id_1_5`),
  KEY `fk_trade_history_player_1_6` (`player_id_1_6`),
  KEY `fk_trade_history_player_1_7` (`player_id_1_7`),
  KEY `fk_trade_history_player_1_8` (`player_id_1_8`),
  KEY `fk_trade_history_player_1_9` (`player_id_1_9`),
  KEY `fk_trade_history_draft_team_0_0` (`draft_team_0_0`),
  KEY `fk_trade_history_draft_team_0_1` (`draft_team_0_1`),
  KEY `fk_trade_history_draft_team_0_2` (`draft_team_0_2`),
  KEY `fk_trade_history_draft_team_0_3` (`draft_team_0_3`),
  KEY `fk_trade_history_draft_team_0_4` (`draft_team_0_4`),
  KEY `fk_trade_history_draft_team_1_0` (`draft_team_1_0`),
  KEY `fk_trade_history_draft_team_1_1` (`draft_team_1_1`),
  KEY `fk_trade_history_draft_team_1_2` (`draft_team_1_2`),
  KEY `fk_trade_history_draft_team_1_3` (`draft_team_1_3`),
  KEY `fk_trade_history_draft_team_1_4` (`draft_team_1_4`),
  CONSTRAINT `fk_trade_history_draft_team_0_0` FOREIGN KEY (`draft_team_0_0`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_0_1` FOREIGN KEY (`draft_team_0_1`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_0_2` FOREIGN KEY (`draft_team_0_2`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_0_3` FOREIGN KEY (`draft_team_0_3`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_0_4` FOREIGN KEY (`draft_team_0_4`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_1_0` FOREIGN KEY (`draft_team_1_0`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_1_1` FOREIGN KEY (`draft_team_1_1`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_1_2` FOREIGN KEY (`draft_team_1_2`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_1_3` FOREIGN KEY (`draft_team_1_3`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_draft_team_1_4` FOREIGN KEY (`draft_team_1_4`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_message` FOREIGN KEY (`message_id`) REFERENCES `messages` (`message_id`),
  CONSTRAINT `fk_trade_history_player_0_0` FOREIGN KEY (`player_id_0_0`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_1` FOREIGN KEY (`player_id_0_1`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_2` FOREIGN KEY (`player_id_0_2`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_3` FOREIGN KEY (`player_id_0_3`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_4` FOREIGN KEY (`player_id_0_4`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_5` FOREIGN KEY (`player_id_0_5`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_6` FOREIGN KEY (`player_id_0_6`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_7` FOREIGN KEY (`player_id_0_7`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_8` FOREIGN KEY (`player_id_0_8`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_0_9` FOREIGN KEY (`player_id_0_9`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_0` FOREIGN KEY (`player_id_1_0`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_1` FOREIGN KEY (`player_id_1_1`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_2` FOREIGN KEY (`player_id_1_2`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_3` FOREIGN KEY (`player_id_1_3`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_4` FOREIGN KEY (`player_id_1_4`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_5` FOREIGN KEY (`player_id_1_5`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_6` FOREIGN KEY (`player_id_1_6`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_7` FOREIGN KEY (`player_id_1_7`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_8` FOREIGN KEY (`player_id_1_8`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_player_1_9` FOREIGN KEY (`player_id_1_9`) REFERENCES `players` (`player_id`),
  CONSTRAINT `fk_trade_history_team_0` FOREIGN KEY (`team_id_0`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `fk_trade_history_team_1` FOREIGN KEY (`team_id_1`) REFERENCES `teams` (`team_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-23 21:11:02
