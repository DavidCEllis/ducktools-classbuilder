# Approaches and tools #

As this module's code generation is inspired by the workings of [David Beazley's Cluegen](https://github.com/dabeaz/cluegen)
I thought it was briefly worth discussing his note on learning an approach vs using a tool.

I think that learning an approach is valuable, this module would not exist without the
example given by `cluegen`.

However, what I found was that in essentially every case where I wanted to use 
these generating tools, I needed to modify them - often significantly. 
It quickly became easier to just create my own tool and upload it as a package.

For example, `cluegen` has a few subtle "exercises for the reader". It needs extending
and fixing for some use-cases.
   * Default values that are not builtins need to be passed as part of the globals 
     dict to `exec`.
   * No support for mutable defaults.
   * Subclass methods will be overwritten if they call a cluegen method that has not been
     generated via `super().methodname(...)`
   * `inspect.signature(cls)` does not work if `cls.__init__` has not already been generated.
     (I think this is actually a bug in inspect).
   * Need an extra filter to support things like `ClassVar`.

In the general spirit though, this module intends to provide some basic tools to help 
create your own customized boilerplate generators.
The generator included in the base module is intended to be used to help 'bootstrap' a 
modified generator with features that work how **you** want them to work.

The `prefab` module is the more fully featured tool that handles the additional cases *I*
needed. 
