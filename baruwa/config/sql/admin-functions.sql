-- CRC32
CREATE OR REPLACE FUNCTION CRC32(x TEXT) RETURNS BIGINT AS $$
import binascii
return binascii.crc32(x) & 0xffffffff
$$ LANGUAGE plpythonu;

-- set session variables
CREATE OR REPLACE FUNCTION set_var (var text, value timestamp with time zone) RETURNS VOID AS $$
var = args[0].strip(' ')
GD[var] = args[1]
$$ LANGUAGE plpythonu;

-- get session variables
CREATE OR REPLACE FUNCTION get_var(name text) RETURNS timestamp AS $$
name = args[0].strip(' ')    
return GD[name]
$$ LANGUAGE plpythonu;