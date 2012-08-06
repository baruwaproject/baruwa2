-- FUNCTIONS
-- timestamp no params
CREATE OR REPLACE FUNCTION unix_timestamp() RETURNS BIGINT AS '
	SELECT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP(0))::bigint AS result;
' LANGUAGE 'SQL';
 
-- timestamp without time zone (i.e. 1973-11-29 21:33:09)
CREATE OR REPLACE FUNCTION unix_timestamp(TIMESTAMP) RETURNS BIGINT AS '
	SELECT EXTRACT(EPOCH FROM $1)::bigint AS result;
' LANGUAGE 'SQL';
 
-- timestamp with time zone (i.e. 1973-11-29 21:33:09+01)
CREATE OR REPLACE FUNCTION unix_timestamp(TIMESTAMP WITH TIME zone) RETURNS BIGINT AS '
	SELECT EXTRACT(EPOCH FROM $1)::bigint AS result;
' LANGUAGE 'SQL';

-- Counting
CREATE OR REPLACE FUNCTION mktotals() RETURNS trigger AS $$
DECLARE
    f1 smallint;
    f2 smallint;
    a1 double precision;
    a2 double precision;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        PERFORM 1 FROM current_domains WHERE name=NEW.from_domain;
        IF FOUND THEN
            f1 := 1;
        ELSE
            f1 := 0;
        END IF;
        PERFORM 1 FROM current_domains WHERE name=NEW.to_domain;
        IF FOUND THEN
            f2 := 1;
        ELSE
            f2 := 0;
        END IF;
        IF f1 = 1 AND f2 = 1 THEN
            a1 := 0.5;
            a2 := 0.5;
        ELSIF f1 = 1 AND f2 = 0 THEN
            a1 := 1;
            a2 := 0;
        ELSIF f1 = 0 AND f2 = 1 THEN
            a1 := 0;
            a2 := 1;
        ELSE
            a1 := 0;
            a2 := 1;
        END IF;
        --from domain
        UPDATE srcmsgtotals SET total=total + 1, volume=volume + NEW.size,
            spam=spam + NEW.spam, virii=virii + NEW.virusinfected,
            infected=infected + NEW.nameinfected,
            otherinfected=otherinfected + NEW.otherinfected,
            runtotal=runtotal + a1
            WHERE id=NEW.from_domain;
        IF NOT FOUND THEN
            --insert new record
            INSERT INTO srcmsgtotals VALUES(NEW.from_domain, 1, NEW.size, NEW.spam,
                NEW.virusinfected, NEW.nameinfected, NEW.otherinfected, a1);
        END IF;
        --to domain
        UPDATE dstmsgtotals SET total=total + 1, volume=volume + NEW.size,
            spam=spam + NEW.spam, virii=virii + NEW.virusinfected,
            infected=infected + NEW.nameinfected,
            otherinfected=otherinfected + NEW.otherinfected,
            runtotal=runtotal + a2
            WHERE id=NEW.to_domain;
        IF NOT FOUND THEN
            --insert new record
            INSERT INTO dstmsgtotals VALUES(NEW.to_domain, 1, NEW.size, NEW.spam,
                NEW.virusinfected, NEW.nameinfected, NEW.otherinfected, a2);
        END IF;
    ELSIF (TG_OP = 'DELETE') THEN
        PERFORM 1 FROM current_domains WHERE name=OLD.from_domain;
        IF FOUND THEN
            f1 := 1;
        ELSE
            f1 := 0;
        END IF;
        PERFORM 1 FROM current_domains WHERE name=OLD.to_domain;
        IF FOUND THEN
            f2 := 1;
        ELSE
            f2 := 0;
        END IF;
        IF f1 = 1 AND f2 = 1 THEN
            a1 := 0.5;
            a2 := 0.5;
        ELSIF f1 = 1 AND f2 = 0 THEN
            a1 := 1;
            a2 := 0;
        ELSIF f1 = 0 AND f2 = 1 THEN
            a1 := 0;
            a2 := 1;
        ELSE
            a1 := 0;
            a2 := 1;
        END IF;
        -- from domain
        UPDATE srcmsgtotals SET total=total - 1, volume=volume - OLD.size,
            spam=spam - OLD.spam, virii=virii - OLD.virusinfected,
            infected=infected - OLD.nameinfected,
            otherinfected=otherinfected - OLD.otherinfected,
            runtotal=runtotal - a1
            WHERE id=OLD.from_domain;
        -- to domain
        UPDATE dstmsgtotals SET total=total - 1, volume=volume - OLD.size,
            spam=spam - OLD.spam, virii=virii - OLD.virusinfected,
            infected=infected - OLD.nameinfected,
            otherinfected=otherinfected - OLD.otherinfected,
            runtotal=runtotal - a2
            WHERE id=OLD.to_domain;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

    

-- Counting
-- CREATE OR REPLACE FUNCTION mktotals() RETURNS trigger AS $$
-- DECLARE
--     runval numeric;
-- BEGIN
--     IF (TG_OP = 'INSERT') THEN
--         --from domain
--         runval = 0.5;
--         UPDATE srcmsgtotals SET total=total + 1, volume=volume + NEW.size,
--             spam=spam + NEW.spam, virii=virii + NEW.virusinfected,
--             infected=infected + NEW.nameinfected,
--             otherinfected=otherinfected + NEW.otherinfected,
--             runtotal=runtotal + runval
--             WHERE id=NEW.from_domain;
--         IF NOT FOUND THEN
--             --insert new record
--             INSERT INTO srcmsgtotals VALUES(NEW.from_domain, 1, NEW.size, NEW.spam,
--                 NEW.virusinfected, NEW.nameinfected, NEW.otherinfected, runval);
--         END IF;
--         --to domain
--         UPDATE dstmsgtotals SET total=total + 1, volume=volume + NEW.size,
--             spam=spam + NEW.spam, virii=virii + NEW.virusinfected,
--             infected=infected + NEW.nameinfected,
--             otherinfected=otherinfected + NEW.otherinfected,
--             runtotal=runtotal + runval
--             WHERE id=NEW.to_domain;
--         IF NOT FOUND THEN
--             --insert new record
--             INSERT INTO dstmsgtotals VALUES(NEW.to_domain, 1, NEW.size, NEW.spam,
--                 NEW.virusinfected, NEW.nameinfected, NEW.otherinfected, runval);
--         END IF;
--     ELSIF (TG_OP = 'DELETE') THEN
--         -- from domain
--         PERFORM id FROM maildomains WHERE name=OLD.to_domain;
--         UPDATE srcmsgtotals SET total=total - 1, volume=volume - OLD.size,
--             spam=spam - OLD.spam, virii=virii - OLD.virusinfected,
--             infected=infected - OLD.nameinfected,
--             otherinfected=otherinfected - OLD.otherinfected,
--             runtotal=runtotal - 0.5
--             WHERE id=OLD.from_domain;
--         -- to domain
--         PERFORM id FROM maildomains WHERE name=OLD.from_domain;
--         UPDATE dstmsgtotals SET total=total - 1, volume=volume - OLD.size,
--             spam=spam - OLD.spam, virii=virii - OLD.virusinfected,
--             infected=infected - OLD.nameinfected,
--             otherinfected=otherinfected - OLD.otherinfected,
--             runtotal=runtotal - 0.5
--             WHERE id=OLD.to_domain;
--     END IF;
--     RETURN NULL;
-- END;
-- $$ LANGUAGE plpgsql;

-- Add to messages
CREATE TRIGGER update_totals AFTER INSERT OR DELETE ON messages FOR EACH ROW EXECUTE PROCEDURE mktotals();

--updates for indexer
CREATE OR REPLACE FUNCTION update_ts() RETURNS TRIGGER AS $$
BEGIN
   NEW.ts = NOW(); 
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add to messages
CREATE TRIGGER ts_update BEFORE UPDATE ON messages FOR EACH ROW EXECUTE PROCEDURE update_ts();
-- Add to archive
CREATE TRIGGER ts_update BEFORE UPDATE ON archive FOR EACH ROW EXECUTE PROCEDURE update_ts();

-- insert deleted messages into kill list
CREATE OR REPLACE FUNCTION update_killlist() RETURNS TRIGGER AS $$
DECLARE
    tn character varying(255) := TG_TABLE_NAME;
BEGIN
    INSERT INTO indexer_killlist VALUES (OLD.id, NOW(), tn);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- add to messages
CREATE TRIGGER killlist_update AFTER DELETE ON messages FOR EACH ROW EXECUTE PROCEDURE update_killlist();
-- add to archive
CREATE TRIGGER killlist_update AFTER DELETE ON archive FOR EACH ROW EXECUTE PROCEDURE update_killlist();

-- update indexer counters
CREATE OR REPLACE FUNCTION update_indexer_counters (tn text, mts timestamp with time zone) RETURNS VOID AS $$
BEGIN
    LOOP
        UPDATE indexer_counters SET maxts=mts WHERE tablename=tn;
        IF FOUND THEN
            RETURN;
        END IF;
        BEGIN
            INSERT INTO indexer_counters VALUES (tn, mts);
            RETURN;
        EXCEPTION WHEN unique_violation THEN
            -- do nothing
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- type to represent ruleset row
CREATE TYPE ruleset_holder AS (
    row_number bigint,
    ruleset text,
    name character varying(50)
);

-- reports_ruleset function
CREATE OR REPLACE FUNCTION report_ruleset (rule text)
RETURNS SETOF ruleset_holder AS $$
DECLARE
    counter integer := 1;
    row ruleset_holder;
    filename text := '';
BEGIN
    IF rule = 'languages' THEN
        filename := 'languages.conf';
    ELSIF rule = 'rejectionreport' THEN
        filename := 'rejection.report.txt';
    ELSIF rule = 'deletedcontentmessage' THEN
        filename := 'deleted.content.message.txt';
    ELSIF rule = 'deletedfilenamemessage' THEN
        filename := 'deleted.filename.message.txt';
    ELSIF rule = 'deletedvirusmessage' THEN
        filename := 'deleted.virus.message.txt';
    ELSIF rule = 'deletedsizemessage' THEN
        filename := 'deleted.size.message.txt';
    ELSIF rule = 'storedcontentmessage' THEN
        filename := 'stored.content.message.txt';
    ELSIF rule = 'storedfilenamemessage' THEN
        filename := 'stored.filename.message.txt';
    ELSIF rule = 'storedvirusmessage' THEN
        filename := 'stored.virus.message.txt';
    ELSIF rule = 'storedsizemessage' THEN
        filename := 'stored.size.message.txt';
    ELSIF rule = 'disinfectedreport' THEN
        filename := 'disinfected.report.txt';
    ELSIF rule = 'inlinewarninghtml' THEN
        filename := 'inline.warning.html';
    ELSIF rule = 'inlinewarningtxt' THEN
        filename := 'inline.warning.txt';
    ELSIF rule = 'sendercontentreport' THEN
        filename := 'sender.content.report.txt';
    ELSIF rule = 'sendererrorreport' THEN
        filename := 'sender.error.report.txt';
    ELSIF rule = 'senderfilenamereport' THEN
        filename := 'sender.filename.report.txt';
    ELSIF rule = 'sendervirusreport' THEN
        filename := 'sender.virus.report.txt';
    ELSIF rule = 'sendersizereport' THEN
        filename := 'sender.size.report.txt';
    ELSIF rule = 'senderspamreport' THEN
        filename := 'sender.spam.report.txt';
    ELSIF rule = 'senderspamrblreport' THEN
        filename := 'sender.spam.rbl.report.txt';
    ELSIF rule = 'senderspamsareport' THEN
        filename := 'sender.spam.sa.report.txt';
    ELSIF rule = 'inlinespamwarning' THEN
        filename := 'inline.spam.warning.txt';
    ELSIF rule = 'recipientspamreport' THEN
        filename := 'recipient.spam.report.txt';
    END IF;
    FOR row IN SELECT 3 AS row_number, 'FromOrTo:  *@' || maildomains.name || '  %reports-base%/' || maildomains.language, '' FROM maildomains
    WHERE maildomains.status='t' AND maildomains.language != 'en'
    UNION
    SELECT 2 AS row_number, 'FromOrTo:  *@' || domainalias.name || '  %reports-base%/' || maildomains.language, '' FROM domainalias, maildomains
    WHERE maildomains.status='t' AND domainalias.status='t' AND maildomains.id=domainalias.domain_id AND maildomains.language != 'en'
    UNION
    SELECT 1 AS row_number, 'FromOrTo:  default  %report-dir%', ''
    ORDER BY row_number DESC LOOP
    row.row_number := counter;
    row.ruleset := row.ruleset || '/' || filename;
    row.name := rule;
    RETURN NEXT row;
    counter := counter + 1;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;

