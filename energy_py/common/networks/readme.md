# Networks 

Code make tensorflow neural networks.  Designed to be generic (i.e. not reinforcement learning specific)

**layers.fully_connected_layer()**
- Creates a single fully connected layer
- Can use either a relu or linear activation function

The layer is created using `tf.get_variable` to allow variable sharing using `scope.reuse_variables()`.  See `energy_py/notebooks/tf_variable_sharing.ipynb` for an indepth look.

**networks.feed_forward()**
- Creates a feedforward neural network (aka multi layer perceptron)
- Currently no support for batch or layer norm