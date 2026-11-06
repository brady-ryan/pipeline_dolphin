"""Multi-band fitting recipe applied to J1620+1203. The fitting
sequence is as follows:

1: PSO+PSF iteration F160W data
2: Align F814W data, PSO+PSF iteration two bands
3: Align F475X data, PSO+PSF iteration three bands
4: MCMC sampling

To use this recipe, copy the function into `recipe.py`
within the dolphin.processor directory.
"""

__author__ = "brady-ryan"

def get_multiband_hst_recipe(self):

    kwargs_psf_iter = self._config.get_kwargs_psf_iteration()

    n_bands = len(np.array(self._config.settings["band"]))
    n_particles = self._pso_num_particle
    n_iterations = self._pso_num_iteration

    def band_mask(active_indices):
        """Return boolean mask for the selected bands."""
        mask = [False] * n_bands
        for i in active_indices:
            mask[i] = True
        return mask

    def add_pso_psf_steps(fitting_kwargs_list, active_bands):
        """Add a PSO + PSF iteration pair for the selected bands."""
        mask = band_mask(active_bands)

        fitting_kwargs_list += [
            [
                'PSO',
                {
                    'sigma_scale': 1.0,
                    'n_particles': n_particles,
                    'n_iterations': n_iterations,
                    'threadCount': self._thread_count,
                },
            ],
            [
                'psf_iteration',
                {
                    **kwargs_psf_iter,
                    'compute_bands': mask,
                },
            ],
        ]

    fitting_kwargs_list = []
    
    # 1. INITIALIZE WITH F160W ONLY    
    active_bands = [0]
    fitting_kwargs_list += [
        [
            'update_settings',
            {
                'kwargs_likelihood': {
                    'bands_compute': band_mask(active_bands),
                },
            },
        ],
    ]

    # PSO + PSF reconstruction using only reference band
    for _ in range(3):
        add_pso_psf_steps(
            fitting_kwargs_list,
            active_bands,
        )

    # 2. ADD EACH REMAINING BAND SEQUENTIALLY    
    for i in range(1, n_bands):

        # Align the new band to the reference band    
        fitting_kwargs_list += [
            [
                'align_images',
                {
                    'n_particles': 100,
                    'n_iterations': 100,
                    'align_offset': True,
                    'align_rotation': True,
                    'delta_shift': 0.1,
                    'delta_rot': 0.1,
                    'compute_bands': band_mask([i]),
                },
            ],
        ]

        # Add the new band to the active set    
        active_bands.append(i)
        active_mask = band_mask(active_bands)
        fitting_kwargs_list += [
            [
                'update_settings',
                {
                    'kwargs_likelihood': {
                        'bands_compute': active_mask,
                    },
                },
            ],
        ]

        # Joint PSO + PSF reconstruction
        # using only the currently active bands    
        for _ in range(3):
            add_pso_psf_steps(
                fitting_kwargs_list,
                active_bands,
            )

    # 4. POSTERIOR SAMPLING
    # if self.do_sampling in config file, sampling
    # will automatically be appeneded to fitting_kwargs_list
    
    return fitting_kwargs_list