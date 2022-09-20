import math
import random
import numpy as np
from scipy import stats

from .distributions import const
from .utils import event_occurs


def normal_sample(low=None, high=None, mean=None, sd=None, credibility=None):
    if mean is None:
        if low > high:
            raise ValueError('`high value` cannot be lower than `low value`')
        elif low == high:
            return low
        mu = (high + low) / 2
        cdf_value = 0.5 + 0.5 * credibility
        normed_sigma = stats.norm.ppf(cdf_value)
        sigma = (high - mu) / normed_sigma
    else:
        mu = mean
        sigma = sd
    return np.random.normal(mu, sigma)

    
def lognormal_sample(low=None, high=None, mean=None, sd=None, credibility=None):
    if (low is not None and low < 0) or (mean is not None and mean < 0):
        raise ValueError('lognormal_sample cannot handle negative values')
    if mean is None:
        if low > high:
            raise ValueError('`high value` cannot be lower than `low value`')
        elif low == high:
            return low
        log_low = np.log(low)
        log_high = np.log(high)
        mu = (log_high + log_low) / 2
        cdf_value = 0.5 + 0.5 * credibility
        normed_sigma = stats.norm.ppf(cdf_value)
        sigma = (log_high - mu) / normed_sigma
    else:
        mu = mean
        sigma = sd
    return np.random.lognormal(mu, sigma)


def t_sample(low, high, t, credibility=None):
    if low > high:
        raise ValueError('`high value` cannot be lower than `low value`')
    elif low == high:
        return low
    else:
        mu = (high + low) / 2
        rangex = (high - low) / 2
        return np.random.standard_t(t) * rangex * 0.6/credibility + mu


def log_t_sample(low, high, t, credibility=None):
    if low > high:
        raise ValueError('`high value` cannot be lower than `low value`')
    elif low < 0:
        raise ValueError('log_t_sample cannot handle negative values')
    elif low == high:
        return low
    else:
        log_low = np.log(low)
        log_high = np.log(high)
        mu = (log_high + log_low) / 2
        rangex = (log_high - log_low) / 2
        return np.exp(np.random.standard_t(t) * rangex * 0.6/credibility + mu)


def binomial_sample(n, p):
    return np.random.binomial(n, p)


def beta_sample(a, b):
    return np.random.beta(a, b)


def bernoulli_sample(p):
    return int(event_occurs(p))


def triangular_sample(left, mode, right):
    return np.random.triangular(left, mode, right)


def exponential_sample(scale):
    return np.random.exponential(scale)
    

def uniform_sample(low, high):
    return np.random.uniform(low, high)


def discrete_sample(items, credibility=0.9):
    if isinstance(items, dict):
        values = [const(k) for k in items.keys()]
        weights = list(items.values())
    elif isinstance(items, list):
        if isinstance(items[0], list):
            weights = [i[0] for i in items]
            values = [const(i[1]) for i in items]
        else:
            values = [const(i) for i in items]
            l = len(items)
            weights = [1 / l for i in range(l)]
    else:
        return ValueError('inputs to discrete_sample must be a dict or list')

    return mixture_sample(values, weights, credibility=credibility)


def mixture_sample(values, weights=None, credibility=0.9):
    if not isinstance(values, list):
        return ValueError('input must be list')
    elif not (isinstance(values, list) and isinstance(weights, list)) and not (isinstance(values, list) and weights is None):
        return ValueError('values / weights misinformed')

    if len(values) == 1:
        return sample(values[0], credibility=credibility)

    if weights is None:
        weights = [v[0] for v in values]
        values = [v[1] for v in values]
        
    sum_weights = sum(weights)

    if sum_weights <= 0.99 or sum_weights >= 1.01:
        raise ValueError('weights don\'t sum to 1 - they sum to {}'.format(sum_weights))

    if len(weights) != len(values):
        raise ValueError('weights and distributions not same length')

    r_ = random.random()
    weights = np.cumsum(weights)

    for i, dist in enumerate(values):
        weight = weights[i]
        if r_ <= weight:
            return sample(dist, credibility=credibility)

    return sample(dist, credibility=credibility)


def sample(var, credibility=0.9, n=1, lclip=None, rclip=None):
    n = int(n)
    if n > 1:
        return np.array([sample(var,
                                credibility=credibility,
                                n=1,
                                lclip=lclip,
                                rclip=rclip) for _ in range(n)])
    elif n <= 0:
        return ValueError('n must be >= 1')

    if callable(var):
        out = var()

    elif not isinstance(var, list) and not (len(var) == 5 or len(var) == 6):
        raise ValueError('input to sample is malformed - must be sample data')

    elif var[2] == 'const':
        out = var[0]

    elif var[2] == 'uniform':
        out = uniform_sample(var[0], var[1])

    elif var[2] == 'discrete':
        out = discrete_sample(var[0])

    elif var[2] == 'norm':
        out = normal_sample(var[0], var[1], credibility=credibility)

    elif var[2] == 'norm-mean':
        out = normal_sample(mean=var[0], sd=var[1], credibility=credibility)

    elif var[2] == 'log':
        out = lognormal_sample(var[0], var[1], credibility=credibility)

    elif var[2] == 'log-mean':
        out = lognormal_sample(mean=var[0], sd=var[1], credibility=credibility)

    elif var[2] == 'binomial':
        out = binomial_sample(n=var[0], p=var[1])

    elif var[2] == 'beta':
        out = beta_sample(a=var[0], b=var[1])

    elif var[2] == 'bernoulli':
        out = bernoulli_sample(p=var[0])

    elif var[2] == 'exponential':
        out = exponential_sample(scale=var[0])

    elif var[2] == 'triangular':
        out = triangular_sample(var[0], var[1], var[3])

    elif var[2] == 'tdist':
        out = t_sample(var[0], var[1], var[3], credibility=credibility)

    elif var[2] == 'log-tdist':
        out = log_t_sample(var[0], var[1], var[3], credibility=credibility)

    elif var[2] == 'mixture':
        out = mixture_sample(var[0], var[1], credibility=credibility)

    else:
        raise ValueError('{} sampler not found'.format(var[2]))

    lclip_ = None
    rclip_ = None
    if not callable(var):
        if var[2] == 'tdist' or var[2] == 'log-tdist' or var[2] == 'triangular':
            lclip_ = var[4]
            rclip_ = var[5]
        else:
            lclip_ = var[3]
            rclip_ = var[4]

    if lclip is None and lclip_ is not None:
        lclip = lclip_
    elif rclip is None and rclip_ is not None:
        rclip = rclip_
    elif lclip is not None and lclip_ is not None:
        lclip = max(lclip, lclip_)
    elif rclip is not None and rclip_ is not None:
        rclip = min(rclip, rclip_)

    if lclip is not None and out < lclip:
        return lclip
    elif rclip is not None and out > rclip:
        return rclip
    else:
        return out

