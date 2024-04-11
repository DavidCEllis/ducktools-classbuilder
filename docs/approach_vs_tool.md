# Approaches and tools #

As this module's code generation is inspired by the workings of [David Beazley's Cluegen](https://github.com/dabeaz/cluegen)
I thought it was briefly worth discussing his note on learning an approach vs using a tool.

I think that learning an approach is valuable, this module would not exist without the
example given by `cluegen`. It also wouldn't exist if I hadn't needed to extend `cluegen`
for some basic features (try using `Path` default values with `cluegen`).

In the general spirit though, this module intends to provide some basic tools to help 
build your own custom class generators.
The generator included in the base module is intended to be used to help 'bootstrap' a 
modified generator with features that work how **you** want them to work.

The `prefab` module is the more fully featured powertool *I* built with these tools. 
However, much like a prefabricated building, it may not be what you desire.
