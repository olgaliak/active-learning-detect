CREATE TABLE Image_Tagging_State_Audit (
    RowId serial primary key,
    ImageId integer NOT NULL,
    TagStateId integer NOT NULL,
    ModifiedDtim timestamp NOT NULL,
    ArchiveDtim timestamp NOT NULL,
    ActionFlag integer NOT NULL 
);