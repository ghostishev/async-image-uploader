# DB schema:

CREATE TABLE `images` (
  `image_id` int unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` tinytext NOT NULL,
  `mimetype` tinytext NOT NULL,
  `body` blob NOT NULL,
  `timestamp` int unsigned NOT NULL
) COLLATE 'utf8_general_ci';
