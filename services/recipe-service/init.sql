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
  directions      TEXT,                       -- cooking instructions
  img_src         TEXT,                       -- image URL
  prep_time       TEXT,                       -- preparation time
  cook_time       TEXT,                       -- cooking time
  servings        TEXT,                       -- number of servings
  rating          TEXT,                       -- recipe rating
  nutrition       TEXT,                       -- nutrition information
  url             TEXT,                       -- original recipe URL
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

