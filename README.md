# PL/pgSQL PyDebug

This is a CLI debugg for PL/pgSQL. It is in its early stages and rather
archaic. It does make use of the `pldbgapi` extension for PostgreSQL. You can
typically install it from the main PG repository.

# Usage

1. Checkout from GitHub
2. Install requirements: `pip3 install -r requirements.txt`
3. Ensure you have the `pldbgapi` extension installed (it will warn you if not)
4. Start a debug session: `./run.py --dsn <dsn>`. The `<dsn>` is the complete
   connection string to your running PostgreSQL instance.
5. Start to debug a PL/pgSQL function by calling `run <function call>` (see below).

# Shortcomings aka the list of shame

* No tests.
* Error handling might be incomplete, it could bail out and leave connections open.
* `source`, `br.set` commands do not yet work with other functions than the
  active target functions. In other words: you can use them only on functions
  which do not call other functions respectively you can step into them but
  not show their source or set breakpoints.
* Not all commands from `pldbgapi` implemented.

# Commands aka the list of fame

Currently, the following commands are available. There is no extensive syntax
checking as of now, so you'll maybe run into trouble here and there.

* `run <function call>` starts debugging, ensure that `<function call>` is
  complete with all arguments, i.e. like `run example_function_1(2)`.
* `stop` stops debugging.
* `continue` causes the execution to proceed to the next breakpoint.
* `vars` displays all variables of the current frame.
* `si` step-into, step into a function call, stop at the next executable instruction/breakpoint.
* `so` step-over, step over a function call, stop at the next executable instruction/breakpoint.
* `source` show the source of the current target function. Does not yet take
  into account that you could have nested functions.
* `stack` show the current stack.
* `br.show` show all active breakpoints.
* `br.set <line>` set a breakpoint in the current target function at the given
  line. Caution: does not work with nested functions yet.
* `exit` exits the debugger.
