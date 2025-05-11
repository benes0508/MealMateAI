-- services/recipe-service/init.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- optional, if you prefer UUIDs

DROP TABLE IF EXISTS recipes;
CREATE TABLE recipes (
  id              SERIAL       PRIMARY KEY,   -- integer ID
  name            TEXT         NOT NULL,      -- recipe name
  ingredients     TEXT[]       NOT NULL,      -- array of ingredient strings
  meal_type       TEXT[]       DEFAULT '{}',  -- e.g. ['breakfast','lunch']
  dietary_tags    TEXT[]       DEFAULT '{}',  -- e.g. ['vegan','gluten-free']
  allergens       TEXT[]       DEFAULT '{}',  -- e.g. ['nuts','dairy']
  difficulty      TEXT,                       -- e.g. 'easy','medium','hard'
  json_path       TEXT         NOT NULL,      -- path to original JSON file
  txt_path        TEXT         NOT NULL,      -- path to plain-text recipe file
  cuisine         TEXT[]       DEFAULT '{}',  -- e.g. ['Mexican']
  tags            TEXT[]       DEFAULT '{}',  -- any extra tags
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

