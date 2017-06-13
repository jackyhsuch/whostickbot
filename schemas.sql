-- Table: public.sessions

-- DROP TABLE public.sessions;

CREATE TABLE public.sessions
(
    user_id integer NOT NULL,
    state integer,
    mode integer,
    tag_id integer,
    CONSTRAINT sessions_pkey PRIMARY KEY (user_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.sessions
    OWNER to xokzqfynjpnfwe;

-- Table: public.stickers

-- DROP TABLE public.stickers;

CREATE TABLE public.stickers
(
    id integer NOT NULL DEFAULT nextval('stickers_id_seq'::regclass),
    user_id integer NOT NULL,
    tag_id integer NOT NULL,
    sticker_uuid character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT stickers_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.stickers
    OWNER to xokzqfynjpnfwe;

-- Table: public.tags

-- DROP TABLE public.tags;

CREATE TABLE public.tags
(
    id integer NOT NULL DEFAULT nextval('tags_id_seq'::regclass),
    user_id integer NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tags_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.tags
    OWNER to xokzqfynjpnfwe;