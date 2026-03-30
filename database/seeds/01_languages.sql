-- Seed: supported target languages
-- Front side of cards is always Russian; back side is in one of these languages.
-- Run with: mysql --default-character-set=utf8mb4 -u root -p flashlang < 01_languages.sql
SET NAMES utf8mb4;
USE flashlang;

INSERT INTO languages (code, name, flag) VALUES
  ('de', 'German',     '🇩🇪'),
  ('en', 'English',    '🇬🇧'),
  ('es', 'Spanish',    '🇪🇸'),
  ('fr', 'French',     '🇫🇷'),
  ('it', 'Italian',    '🇮🇹'),
  ('ja', 'Japanese',   '🇯🇵'),
  ('pt', 'Portuguese', '🇵🇹'),
  ('zh', 'Chinese',    '🇨🇳');
