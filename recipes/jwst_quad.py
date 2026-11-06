"""Fitting recipe applied to WFI2033. The fitting
sequence is as follows:

1: Remove shapelets, fix power-law slope
2: Turn on shapelet complexity
3: Release power-law slope
4: MCMC sampling

To use this recipe, copy the function into `recipe.py`
within the dolphin.processor directory.
"""

__author__ = "brady-ryan"

def get_jwst_quad_recipe(self):

    kwargs_psf_iter = self._config.get_kwargs_psf_iteration()

    fitting_kwargs_list = []

    pl_index = self._get_power_law_model_index()
    shapelet_index = self._get_shapelet_model_index()

    n_particles = self._pso_num_particle
    n_iterations = self._pso_num_iteration
    
    # 0. Initial hard constraints
    # Fix shapelet complexity (n_max = -1, effectively no shapelet)
    if shapelet_index is not None:
        fitting_kwargs_list += [[
            "update_settings",
            {"source_add_fixed": [[shapelet_index, ["n_max"], [-1]]]}
        ]]
    
    # Fix lens slope initially
    if pl_index is not None:
        fitting_kwargs_list += [[
            "update_settings",
            {"lens_add_fixed": [[pl_index, ["gamma"], [1.95]]]}
        ]]
    
    # 1. PSF + Geometry Stabilization
    for _ in range(2):
        fitting_kwargs_list += [
            ["PSO", {
                "sigma_scale": 1.0,
                "n_particles": n_particles,
                "n_iterations": n_iterations,
                "threadCount": self._thread_count,
            }],
        ]
        if self._config.settings["fitting"]["psf_iteration"] is True:
            fitting_kwargs_list += [
                ["psf_iteration", kwargs_psf_iter]
            ]
    
    # 2. Turn on Source Complexity
    if shapelet_index is not None:
        n_max = self._config.settings["source_light_options"]["n_max"][0]
        fitting_kwargs_list += [[
            "update_settings",
            {"source_add_fixed": [[shapelet_index, ["n_max"], [n_max]]]}
        ]]
    
    for _ in range(2):
        fitting_kwargs_list += [
            ["PSO", {
                "sigma_scale": 1.0,
                "n_particles": n_particles,
                "n_iterations": n_iterations,
                "threadCount": self._thread_count,
            }]
        ]
        if self._config.settings["fitting"]["psf_iteration"] is True:
            fitting_kwargs_list += [
                ["psf_iteration", kwargs_psf_iter]
            ]
    
    # 3. Release Lens Slope
    if pl_index is not None:
        fitting_kwargs_list += [[
            "update_settings",
            {"lens_remove_fixed": [[pl_index, ["gamma"]]]}
        ]]

    for _ in range(2):
        fitting_kwargs_list += [
            ["PSO", {
                "sigma_scale": 0.3,
                "n_particles": n_particles,
                "n_iterations": n_iterations,
                "threadCount": self._thread_count,
            }],
        ]
        if self._config.settings["fitting"]["psf_iteration"] is True:
            fitting_kwargs_list += [
                ["psf_iteration", kwargs_psf_iter]
            ]

    # 4. POSTERIOR SAMPLING
    # if self.do_sampling in config file, sampling
    # will automatically be appeneded to fitting_kwargs_list

    return fitting_kwargs_list