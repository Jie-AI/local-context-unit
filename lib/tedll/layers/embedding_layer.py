#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Author	:

Date	:

Brief	: 
"""

import tensorflow as tf
import numpy as np
from . import Layer
from . import WindowAlignmentLayer

class EmbeddingLayer(Layer):
    """EmbeddingLayer"""
    def __init__(self, vocab_size, emb_size, name="embedding", 
            initializer=None, **kwargs):
        Layer.__init__(self, name, **kwargs) 
        self._emb_size = emb_size
        if not initializer:
            initializer = tf.contrib.layers.variance_scaling_initializer()
        self._W = self.get_variable(name + '_W', shape=[vocab_size, emb_size],
                initializer=initializer)

    def _forward(self, seq):
        return tf.nn.embedding_lookup(self._W, seq)


class WindowPoolEmbeddingLayer(EmbeddingLayer):
    """WindowPoolEmbeddingLayer"""
    def __init__(self, vocab_size, emb_size, win_size, \
            win_merge_fn=None, \
            name="win_pool_embedding", \
            initializer=None, \
            **kwargs):
        
        Layer.__init__(self, name, **kwargs) 
        self._emb_size = emb_size
        self._win_size = win_size
        self._win_merge_fn = win_merge_fn
        if not initializer:
            initializer = tf.contrib.layers.variance_scaling_initializer()
        self._K = self.get_variable(name + '_K', shape=[vocab_size, win_size, emb_size],
                initializer=initializer)
        super(WindowPoolEmbeddingLayer, self).__init__(vocab_size, emb_size, name,
                initializer, **kwargs)

    def _forward(self, seq):
        # Window alignment embedding
        win_aligned_seq = WindowAlignmentLayer(self._win_size)(seq)
        win_aligned_emb = super(WindowPoolEmbeddingLayer, self)._forward(win_aligned_seq)

        return self._win_merge_fn(win_aligned_emb, axis=2)


class ScalarRegionEmbeddingLayer(EmbeddingLayer):
    """WordContextRegionEmbeddingLayer(Scalar)"""
    def __init__(self, vocab_size, emb_size, win_size, \
            win_merge_fn=None, \
            name="scalar_region_embedding", \
            initializer=None, \
            **kwargs):
        Layer.__init__(self, name, **kwargs)
        self._emb_size = emb_size
        self._win_size = win_size
        self._win_merge_fn = win_merge_fn
        if not initializer:
            initializer = tf.contrib.layers.variance_scaling_initializer()
        self._K = self.get_variable(name + '_K', shape=[vocab_size, win_size, 1],
                initializer=initializer)
        super(ScalarRegionEmbeddingLayer, self).__init__(vocab_size, emb_size, name,
                initializer, **kwargs)

    def _forward(self, seq):
        # Window alignment embedding
        win_aligned_seq = WindowAlignmentLayer(self._win_size)(seq)
        win_aligned_emb = super(ScalarRegionEmbeddingLayer, self)._forward(win_aligned_seq)

        win_radius = self._win_size / 2
        trimed_seq = seq[:, win_radius: seq.get_shape()[1] - win_radius]
        context_unit = tf.nn.embedding_lookup(self._K, trimed_seq)

        projected_emb = win_aligned_emb * context_unit
        return self._win_merge_fn(projected_emb, axis=2)


class MultiRegionEmbeddingLayer(EmbeddingLayer):
    """"WordContextRegionEmbeddingLayer(Multi-region)"""
    def __init__(self, vocab_size, emb_size, win_sizes, \
            win_merge_fn=None, \
            name="multi_region_embedding", \
            initializer=None, \
            **kwargs):
        
        Layer.__init__(self, name, **kwargs)
        self._emb_size = emb_size
        self._win_sizes = win_sizes[:]
        self._win_sizes.sort()
        self._win_merge_fn = win_merge_fn
        win_num = len(win_sizes)

        self._K = [None] * win_num
        self._K[-1] = tf.get_variable(name + '_K_%d' % (win_num - 1), \
                    shape=[vocab_size, self._win_sizes[-1], emb_size], \
                    initializer=initializer)

        for i in range(win_num - 1):
            st = self._win_sizes[-1]/2 - self._win_sizes[i]/2
            ed = st + self._win_sizes[i]
            self._K[i] = self._K[-1][:, st:ed, :]

        super(MultiRegionEmbeddingLayer, self).__init__(vocab_size, emb_size, name,
                initializer, **kwargs)

    def _forward(self, seq):
        """_forward
        """

        multi_region_emb = [] 

        for i, win_kernel in enumerate(self._K):
            win_radius = self._win_sizes[i] / 2
            win_aligned_seq = WindowAlignmentLayer(self._win_sizes[i], name="WinAlig_%d" % (i))(seq)
            win_aligned_emb = super(MultiRegionEmbeddingLayer, self)._forward(win_aligned_seq)
             
            trimed_seq = seq[:, win_radius: seq.get_shape()[1] - win_radius]
            context_unit = tf.nn.embedding_lookup(win_kernel, trimed_seq)

            projected_emb = win_aligned_emb * context_unit
            region_emb =  self._win_merge_fn(projected_emb, axis=2)
            multi_region_emb.append(region_emb)
        
        return multi_region_emb


class WordContextRegionEmbeddingLayer(EmbeddingLayer):
    """WordContextRegionEmbeddingLayer"""
    def __init__(self, vocab_size, emb_size, win_size, \
            win_merge_fn=None, \
            name="word_context_region_embedding", \
            initializer=None, \
            **kwargs):
        Layer.__init__(self, name, **kwargs) 
        self._emb_size = emb_size
        self._win_size = win_size
        self._win_merge_fn = win_merge_fn
        if not initializer:
            initializer = tf.contrib.layers.variance_scaling_initializer()
        self._K = self.get_variable(name + '_K', shape=[vocab_size, win_size, emb_size],
                initializer=initializer)
        super(WordContextRegionEmbeddingLayer, self).__init__(vocab_size, emb_size, name,
                initializer, **kwargs)

    def _forward(self, seq):
        # Window alignment embedding
        win_aligned_seq = WindowAlignmentLayer(self._win_size)(seq)
        win_aligned_emb = super(WordContextRegionEmbeddingLayer, self)._forward(win_aligned_seq)

        win_radius = self._win_size / 2
        trimed_seq = seq[:, win_radius: seq.get_shape()[1] - win_radius]
        context_unit = tf.nn.embedding_lookup(self._K, trimed_seq)

        projected_emb = win_aligned_emb * context_unit
        return self._win_merge_fn(projected_emb, axis=2)


class ContextWordRegionEmbeddingLayer(EmbeddingLayer):
    """ContextWordRegionEmbeddingLayer"""
    def __init__(self, vocab_size, emb_size, win_size, 
            win_merge_fn=None,
            name="embedding",
            initializer=None, **kwargs):
        super(ContextWordRegionEmbeddingLayer, self).__init__(vocab_size * win_size, emb_size, name,
                initializer, **kwargs)
        self._win_merge_fn = win_merge_fn
        self._word_emb = tf.get_variable(name + '_wordmeb', shape=[vocab_size, emb_size], 
                initializer=initializer)
        self._unit_id_bias = np.array([i * vocab_size for i in range(win_size)])
        self._win_size = win_size

    def _win_aligned_units(self, seq):
        """
        _win_aligned_unit
        """
        win_aligned_seq = WindowAlignmentLayer(self._win_size)(seq)
        win_aligned_seq = win_aligned_seq + self._unit_id_bias
        win_aligned_unit = super(ContextWordRegionEmbeddingLayer, self)._forward(win_aligned_seq)
        return win_aligned_unit
    
    def _forward(self, seq):
        """forward
        """
        win_radius = self._win_size / 2
        word_emb = tf.nn.embedding_lookup(self._word_emb, \
                tf.slice(seq, \
                [0, win_radius], \
                [-1, tf.cast(seq.get_shape()[1] - 2 * win_radius, tf.int32)]))
        word_emb = tf.expand_dims(word_emb, 2)
        win_aligned_unit = self._win_aligned_units(seq)
        embedding = win_aligned_unit * word_emb
        embedding = self._win_merge_fn(embedding, axis=2)
        return embedding


def main():
    """main"""
    pass

if '__main__' == __name__:
    main()

