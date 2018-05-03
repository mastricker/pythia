from collections import defaultdict
import itertools
import logging
import numpy as np
import freud

from .internal import assert_installed

logger = logging.getLogger(__name__)


def _nlist_helper(fbox, positions, neighbors, rmax_guess=2., exclude_ii=None):
    if isinstance(neighbors, int):
        nneigh = freud.locality.NearestNeighbors(rmax_guess, neighbors)
        nneigh.compute(fbox, positions, positions, exclude_ii)
        neighbors = nneigh.nlist
    elif isinstance(neighbors, float):
        lc = freud.locality.LinkCell(fbox, neighbors)
        lc.compute(fbox, positions, positions, exclude_ii)
        neighbors = lc.nlist

    return neighbors

def neighbor_average(box, positions, neigh_min=4, neigh_max=4, lmax=4,
                     negative_m=True, reference_frame='neighborhood',
                     orientations=None, rmax_guess=1., noise_samples=0,
                     noise_magnitude=0):
    """Compute the neighbor-averaged spherical harmonics over the
    nearest-neighbor bonds of a set of particles. Returns the raw
    (complex) spherical harmonic values.

    :param neigh_min: Minimum number of neighbor environment sizes to consider
    :param neigh_max: Maximum number of neighbor environment sizes to consider (inclusive)
    :param lmax: Maximum spherical harmonic degree l
    :param negative_m: Include negative m spherical harmonics in the output array?
    :param reference_frame: 'neighborhood': use diagonal inertia tensor reference frame; 'particle_local': use the given orientations array; 'global': do not rotate
    :param orientations: Per-particle orientations, only used when reference_frame == 'particle_local'
    :param rmax_guess: Initial guess of the distance to find `neigh_max` nearest neighbors. Only affects algorithm speed.
    :param noise_samples: Number of random noisy samples of positions to average the result over (disabled if 0)
    :param noise_magnitude: Magnitude of (normally-distributed) noise to apply to noise_samples different positions (disabled if `noise_samples == 0`)

    """
    if noise_samples:
        to_average = []
        for _ in range(noise_samples):
            noise = np.random.normal(0, noise_magnitude, positions.shape)
            noisy_positions = positions + noise
            to_average.append(neighbor_average(
                box, positions, neigh_min, neigh_max, lmax, negative_m,
                reference_frame, orientations, rmax_guess, 0, 0))

        return np.mean(to_average, axis=0)

    box = freud.box.Box.from_box(box)

    if orientations is None and reference_frame == 'particle_local':
        logging.error('reference_frame="particle_local" was given for '
                      'neighbor_average, but orientations were not given')
        orientations = np.zeros((positions.shape[0], 4), dtype=np.float32)
        orientations[:, 0] = 1

    result = []
    comp = freud.order.LocalDescriptors(neigh_max, lmax, rmax_guess, negative_m)
    comp.computeNList(box, positions)

    logging.debug('rmax: {}'.format(comp.getRMax()))

    for nNeigh in range(neigh_min, neigh_max + 1):
        # sphs::(Nbond, Nsph)
        comp.compute(box, nNeigh, positions, positions, orientations)
        sphs = comp.getSph()

        # average over neighbors
        sphs = sphs.reshape((positions.shape[0], nNeigh, sphs.shape[-1]))
        sphs = np.nanmean(sphs, axis=1)
        result.append(sphs)

    return np.hstack(result)

def abs_neighbor_average(box, positions, neigh_min=4, neigh_max=4, lmax=4,
                     negative_m=True, reference_frame='neighborhood',
                     orientations=None, rmax_guess=1., noise_samples=0,
                     noise_magnitude=0):
    """Compute the neighbor-averaged spherical harmonics over the
    nearest-neighbor bonds of a set of particles. Returns the absolute
    value of the (complex) spherical harmonics

    :param neigh_min: Minimum number of neighbor environment sizes to consider
    :param neigh_max: Maximum number of neighbor environment sizes to consider (inclusive)
    :param lmax: Maximum spherical harmonic degree l
    :param negative_m: Include negative m spherical harmonics in the output array?
    :param reference_frame: 'neighborhood': use diagonal inertia tensor reference frame; 'particle_local': use the given orientations array; 'global': do not rotate
    :param orientations: Per-particle orientations, only used when reference_frame == 'particle_local'
    :param rmax_guess: Initial guess of the distance to find `neigh_max` nearest neighbors. Only affects algorithm speed.
    :param noise_samples: Number of random noisy samples of positions to average the result over (disabled if 0)
    :param noise_magnitude: Magnitude of (normally-distributed) noise to apply to noise_samples different positions (disabled if `noise_samples == 0`)

    """

    return np.abs(neighbor_average(
        box, positions, neigh_min, neigh_max, lmax, negative_m,
        reference_frame, orientations, rmax_guess))

def system_average(box, positions, neigh_min=4, neigh_max=4, lmax=4,
                   negative_m=True, reference_frame='neighborhood',
                   orientations=None, rmax_guess=1., noise_samples=0,
                   noise_magnitude=0):
    """Compute the global-averaged spherical harmonics over the
    nearest-neighbor bonds of a set of particles. Returns the raw
    (complex) spherical harmonic values.

    :param neigh_min: Minimum number of neighbor environment sizes to consider
    :param neigh_max: Maximum number of neighbor environment sizes to consider (inclusive)
    :param lmax: Maximum spherical harmonic degree l
    :param negative_m: Include negative m spherical harmonics in the output array?
    :param reference_frame: 'neighborhood': use diagonal inertia tensor reference frame; 'particle_local': use the given orientations array; 'global': do not rotate
    :param orientations: Per-particle orientations, only used when reference_frame == 'particle_local'
    :param rmax_guess: Initial guess of the distance to find `neigh_max` nearest neighbors. Only affects algorithm speed.
    :param noise_samples: Number of random noisy samples of positions to average the result over (disabled if 0)
    :param noise_magnitude: Magnitude of (normally-distributed) noise to apply to noise_samples different positions (disabled if `noise_samples == 0`)

    """
    return np.mean(neighbor_average(
        box, positions, neigh_min, neigh_max, lmax, negative_m,
        reference_frame, orientations, rmax_guess), axis=0)

def abs_system_average(box, positions, neigh_min=4, neigh_max=4, lmax=4,
                       negative_m=True, reference_frame='neighborhood',
                       orientations=None, rmax_guess=1., noise_samples=0,
                       noise_magnitude=0):
    """Compute the global-averaged spherical harmonics over the
    nearest-neighbor bonds of a set of particles. Returns the absolute
    value of the (complex) spherical harmonics

    :param neigh_min: Minimum number of neighbor environment sizes to consider
    :param neigh_max: Maximum number of neighbor environment sizes to consider (inclusive)
    :param lmax: Maximum spherical harmonic degree l
    :param negative_m: Include negative m spherical harmonics in the output array?
    :param reference_frame: 'neighborhood': use diagonal inertia tensor reference frame; 'particle_local': use the given orientations array; 'global': do not rotate
    :param orientations: Per-particle orientations, only used when reference_frame == 'particle_local'
    :param rmax_guess: Initial guess of the distance to find `neigh_max` nearest neighbors. Only affects algorithm speed.
    :param noise_samples: Number of random noisy samples of positions to average the result over (disabled if 0)
    :param noise_magnitude: Magnitude of (normally-distributed) noise to apply to noise_samples different positions (disabled if `noise_samples == 0`)

    """
    return np.abs(system_average(
        box, positions, neigh_min, neigh_max, lmax, negative_m,
        reference_frame, orientations, rmax_guess))

def steinhardt_q(box, positions, neighbors=12, lmax=6, rmax_guess=2.):
    """Compute a vector of per-particle Steinhardt order parameters, which
    are rotationally-invariant combinations of spherical harmonics."""
    box = freud.box.Box.from_box(box)
    neighbors = _nlist_helper(box, positions, neighbors, rmax_guess)

    result = []
    for l in range(2, lmax + 1, 2):
        compute = freud.order.LocalQl(box, rmax_guess, l)
        compute.compute(positions)
        op = compute.getQl()
        result.append(op.copy())

    result = np.array(result, dtype=np.float32).T
    return result

class _clebsch_gordan_cache(object):
    _cache = {}

    def __call__(self, l1, l2, l3, m1, m2, m3):
        sympy = assert_installed('sympy')
        assert_installed('sympy.physics.wigner')
        key = (l1, l2, l3, m1, m2, m3)

        if key not in self._cache:
            self._cache[key] = float(sympy.physics.wigner.clebsch_gordan(*key))

        return self._cache[key]

def bispectrum(box, positions, neighbors, lmax, rmax_guess=2.):
    """Computes bispectrum invariants of particle local
    environments. These are rotationally-invariant descriptions
    similar to a power spectrum of the spherical harmonics
    (i.e. steinhardt order parameters), but retaining more
    information.

    :param neighbors: number of nearest-neighbors to consider for local environments
    :param lmax: maximum spherical harmonic degree to consider. O(lmax**3) descriptors will be generated.
    """
    fsph = assert_installed('fsph')
    sympy = assert_installed('sympy')

    box = freud.box.Box.from_box(box)
    nlist = _nlist_helper(box, positions, neighbors, rmax_guess)

    rijs = positions[nlist.index_j] - positions[nlist.index_i]
    box.wrap(rijs)

    phi = np.arccos(rijs[..., 2]/np.sqrt(np.sum(rijs**2, axis=-1)))
    theta = np.arctan2(rijs[..., 1], rijs[..., 0])

    sphs = fsph.pointwise_sph(phi, theta, lmax, negative_m=True)
    sphs = np.add.reduceat(sphs, nlist.segments)/nlist.neighbor_counts[:, np.newaxis]
    sphs[np.isnan(sphs)] = 0
    lm_columns = {(l, m): i for (i, (l, m)) in enumerate(fsph.get_LMs(lmax, negative_m=True))}

    result = defaultdict(lambda: 0)
    for (l1, l2, l) in itertools.product(range(lmax + 1), range(lmax + 1), range(lmax + 1)):
        result_key = (l1, l2, l)

        for m in range(-l, l + 1):
            left = sphs[:, lm_columns[(l, m)]]

            right = 0 + 0j

            nonzero = False
            m1_min = max(-l1, m - l2)
            m1_max = min(l1, m + l2)
            for m1 in range(m1_min, m1_max + 1):
                term = _clebsch_gordan_cache()(l1, l2, l, m1, m - m1, m)

                if term == 0:
                    continue
                else:
                    nonzero = True

                term *= np.conj(sphs[:, lm_columns[(l1, m1)]])
                term *= np.conj(sphs[:, lm_columns[(l2, m - m1)]])

                right += term

            if nonzero:
                result[result_key] += left*right

    result_columns = [result[key] for key in sorted(result)]
    result = np.array(result_columns, dtype=np.complex128).T
    result = np.ascontiguousarray(result).view(np.float64).reshape((positions.shape[0], -1))

    return result
