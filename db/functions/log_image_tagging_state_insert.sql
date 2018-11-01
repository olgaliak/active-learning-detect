-- ActionFlag: 1 = insert, 2 = update, 3 = delete
CREATE OR REPLACE FUNCTION log_image_tagging_state_insert()
    RETURNS trigger AS
    '
        BEGIN
            INSERT INTO Image_Tagging_State_Audit(ImageId,TagStateId,ModifiedDtim,ArchiveDtim,ActionFlag)
            VALUES(NEW.ImageId,NEW.TagStateId,NEW.ModifiedDtim,current_timestamp,1);
            
            RETURN NEW;
        END;
    '
    LANGUAGE plpgsql; 