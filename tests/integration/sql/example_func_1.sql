DROP FUNCTION IF EXISTS example_func_1(INT);
CREATE FUNCTION example_func_1(arg INT) RETURNS VOID AS $$
DECLARE
  i INT;
BEGIN
  FOR i in 1..arg LOOP
    RAISE NOTICE 'Iteration: %', i;
    RAISE NOTICE 'To go: %', arg - i;
  END LOOP;
END;
$$ LANGUAGE plpgsql;
