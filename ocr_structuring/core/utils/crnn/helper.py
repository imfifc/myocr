import numpy as np


def ctc_greedy_decoder(logits, ctc_invalid_index):
    """
    取每个时间步值最大的那个字符

    参考：https://github.com/tensorflow/tensorflow/blob/61c6c84964b4aec80aeace187aab8cb2c3e55a72/tensorflow/core/util/ctc/ctc_decoder.h

    :param logits: 网络的原始输出，未进行 softmax. Shape: [batch_size, time_step, num_classes]
    :return:
        out [batch_size, indexes]
        index_out [batch_size, decoded_length] 保存 out 中每一步输出结果对应的 time_step
    """
    out = []
    index_out = []
    for batch in logits:
        tmp = []
        pre_index = -1
        for ti, time_step in enumerate(batch):
            max_index = np.argmax(time_step)
            if max_index != ctc_invalid_index and max_index != pre_index:
                tmp.append(max_index)
                index_out.append(ti)
            pre_index = max_index

        out.append(tmp)

    return out, index_out


def softmax(X, axis=None):
    """
    https://nolanbconaway.github.io/blog/2017/softmax-numpy
    Compute the softmax of each element along an axis of X.

    Parameters
    ----------
    X: ND-Array. Probably should be floats.
    axis (optional): axis to compute values along. Default is the
        first non-singleton axis.

    Returns an array the same size as X. The result will sum to 1
    along the specified axis.
    """

    # make X at least 2d
    y = np.atleast_2d(X)

    # find axis
    if axis is None:
        axis = next(j[0] for j in enumerate(y.shape) if j[1] > 1)

    # subtract the max for numerical stability
    y = y - np.expand_dims(np.max(y, axis=axis), axis)

    # exponentiate y
    y = np.exp(y)

    # take the sum along the specified axis
    ax_sum = np.expand_dims(np.sum(y, axis=axis), axis)

    # finally: divide elementwise
    p = y / ax_sum

    # flatten if X was 1D
    if len(X.shape) == 1:
        p = p.flatten()

    return p
