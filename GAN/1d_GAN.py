'''
An example of distribution approximation using Generative Adversarial Networks
in TensorFlow.
Based on the blog post by John Glover:
http://blog.aylien.com/introduction-generative-adversarial-networks-code-tensorflow/
'''

import argparse
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from matplotlib import animation
import seaborn as sns
import matplotlib.mlab as mlab

sns.set(color_codes=True)

seed = 127
np.random.seed(seed)
tf.set_random_seed(seed)

# Define 1-d distribution from Gaussian.
class DataDistribution(object):
    def __init__(self):
        self.mu = 8
        self.sigma = 0.5

    def sample(self, N):
        samples = np.random.normal(self.mu, self.sigma, N)
        samples.sort()
        return samples   
    
# generator with noise  
class GeneratorDistribution(object):
    def __init__(self, range):
        self.range = range

    def sample(self, N):
        return np.linspace(-self.range, self.range, N) + np.random.random(N) 
   

#  linear transformation
def linear(input, output_dim, scope=None, stddev=1.0):
    with tf.variable_scope(scope or 'linear'):
        w = tf.get_variable(
            'w',
            [input.get_shape()[1], output_dim],
            initializer=tf.random_normal_initializer(stddev=stddev)
        )
        b = tf.get_variable(
            'b',
            [output_dim],
            initializer=tf.constant_initializer(0.0)
        )
        return tf.matmul(input, w) + b

    
def generator(input, h_dim):
    h0 = tf.nn.softplus(linear(input, h_dim, 'g0'))
    h1 = linear(h0, 1, 'g1')
    return h1

#In this case we found that it was important to make sure that the discriminator is more powerful 
#than the generator, as otherwise it did not have sufficient capacity to learn to be able to distinguish 
#accurately between generated and real samples.So we made it a deeper neural network, with a larger number of dimensions. 
def discriminator(input, hidden_size):
    h0 = tf.tanh(linear(input, hidden_size * 2, 'd0'))
    h1 = tf.tanh(linear(h0, hidden_size * 2, 'd1'))
    h2 = tf.tanh(linear(h1, hidden_size * 2, 'd2'))
    h3 = tf.sigmoid(linear(h2, 1, 'd3')) #binary classification: sigmoid; multi-class use softmax
    return h3


def optimizer(loss, var_list):
    learning_rate = 0.001
    step = tf.Variable(0, trainable=False)
    optimizer = tf.train.AdamOptimizer(learning_rate).minimize(
        loss,
        global_step=step,
        var_list=var_list
    )
    return optimizer

'''
## optimizer Option 2 : exponential_decay optimizer
def optimizer(loss, var_list):
    initial_learning_rate = 0.005
    decay = 0.90
    num_decay_steps = 150  #decay every 150 steps with a base of 0.90:
    batch = tf.Variable(0)
    learning_rate = tf.train.exponential_decay(  # plain GradientDescentOptimizer with exponential learning rate decay
        initial_learning_rate,
        batch,
        num_decay_steps,
        decay,
        staircase=True
    )
    optimizer = GradientDescentOptimizer(learning_rate).minimize(
        loss,
        global_step=batch,
        var_list=var_list
    )
    return optimizer
'''

'''

################################
######### Visualize data #######
x=data.sample(1000)
num_bins = 100
# the histogram of the data
n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
# add a 'best fit' line
y = mlab.normpdf(bins, data.mu, data.sigma)
plt.plot(bins, y, 'r--')
plt.xlabel('raw data')
plt.ylabel('Probability')

# Tweak spacing to prevent clipping of ylabel
plt.subplots_adjust(left=0.15)
plt.show()

'''
###################################
#### create a TensorFlow Graph ####

num_steps=5000
batch_size=8

hidden_size=4

data=DataDistribution()
gen=GeneratorDistribution(10)



with tf.variable_scope('G', reuse=True):
    z = tf.placeholder(tf.float32, shape=(None, 1))
    G = generator(z, hidden_size)

with tf.variable_scope('D', reuse=True): # equal to with tf.variable_scope('D', reuse=True)
    x = tf.placeholder(tf.float32, shape=(None, 1))
    D1 = discriminator(x, hidden_size)
    scope.reuse_variables()
    D2 = discriminator(G, hidden_size)

loss_d = tf.reduce_mean(-tf.log(D1) - tf.log(1 - D2))
loss_g = tf.reduce_mean(-tf.log(D2))


vars = tf.trainable_variables()
d_params = [v for v in vars if v.name.startswith('D/')]
g_params = [v for v in vars if v.name.startswith('G/')]

# calculate loss separately
opt_d = optimizer(loss_d, d_params)
opt_g = optimizer(loss_g, g_params)



################################
######### train models #########

with tf.Session() as session:
    #tf.initialize_all_variables().run()
    tf.global_variables_initializer().run()

    for step in xrange(num_steps):
        # update discriminator
        x = data.sample(batch_size)
        z = gen.sample(batch_size)
        
        session.run([loss_d, opt_d], {
            x: np.reshape(x, (batch_size, 1)),
            z: np.reshape(z, (batch_size, 1))
        })
    '''
        # update generator
        z = gen.sample(batch_size)
        loss_g, _ =session.run([loss_g, opt_g], {
            z: np.reshape(z, (batch_size, 1))  
        })
        
        if step % 10 == 0:
                print('{}: {:.4f}\t{:.4f}'.format(step, loss_d, loss_g))

   '''            
                
####################################################
######## PART 2: minibatch discrimination ##########
## Problem: If the generator just produces the mean value of the real data in this simple example, 
## then it is going to be quite likely to fool the discriminator.
## Solution: Give the discriminator the ability to examine multiple examples at once -- minibatch discrimination.
