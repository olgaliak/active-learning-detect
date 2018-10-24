-- Set up table
CREATE TABLE TagState (
    TagStateId integer NOT NULL,
    TagStateName text NOT NULL
);
-- Set up table
CREATE TABLE Image_Tags (
    TaggingId integer NOT NULL,
    Class text NOT NULL,
    Confidence double precision NOT NULL,
    X_Min integer NOT NULL,
    X_Max integer NOT NULL,
    Y_Min integer NOT NULL,
    Y_Max integer NOT NULL
);

-- Set up table and autoincrementing primary key
CREATE TABLE Image_Tagging (
    TaggingId integer NOT NULL,
    ImageId integer NOT NULL,
    TagStateId integer NOT NULL,
    CreatedDtim date NOT NULL default current_timestamp,
    Valid boolean 
);

CREATE SEQUENCE Image_Tagging_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE Image_Tagging_id_seq OWNED BY Image_Tagging.TaggingId;

ALTER TABLE ONLY Image_Tagging ALTER COLUMN TaggingId SET DEFAULT nextval('Image_Tagging_id_seq'::regclass);

ALTER TABLE ONLY Image_Tagging
    ADD CONSTRAINT Image_Tagging_pkey PRIMARY KEY (TaggingId);

-- Set up table and autoincrementing primary key
CREATE TABLE Image_Info (
    ImageId integer NOT NULL,
    OriginalImageName text NOT NULL,
    Height integer NOT NULL,
    Width integer NOT NULL
);

CREATE SEQUENCE ImgInfo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE ImgInfo_id_seq OWNED BY Image_Info.ImageId;

ALTER TABLE ONLY Image_Info ALTER COLUMN ImageId SET DEFAULT nextval('ImgInfo_id_seq'::regclass);

ALTER TABLE ONLY Image_Info
    ADD CONSTRAINT ImgInfo_pkey PRIMARY KEY (ImageId);