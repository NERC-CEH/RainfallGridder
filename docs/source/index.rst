.. _index:

:layout: landing


.. container::
    :name: home-head

    .. image:: /_static/rainfall_gridder_logo_circle.png
        :alt: RainfallGridder
        :width: 250
    

    .. container::

        .. raw:: html

            <h1>RainfallGridder</h1>

        .. container:: badges
           :name: badges

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
              :alt: UV

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
              :alt: Ruff Version

           .. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
              :alt: GPL v3 License


            .. .. image:: https://readthedocs.org/projects/falco-site/badge/?version=latest&style=flat
            ..   :alt: Documentation Status
         ..   .. image:: https://img.shields.io/pypi/pyversions/rainfall_gridder-app
         ..    ..   :alt: Supported Python Versions

         ..   .. image:: https://img.shields.io/pypi/dm/falco-cli
         ..      :alt: PyPI Downloads

           .. image:: https://badge.fury.io/py/falco-app.svg
              :alt: PyPI Version


.. rst-class:: lead

    Python package for interpolating rainfall data from rain gauges onto a regular grid


.. Falco is your Django toolkit for faster prototyping and deployment of your Django projects. It offers commands for project generation, CRUD view generation, guides that address common web development challenges tailored to Django and much more.
Current version: |release|

.. container:: buttons

    `Docs <installation.html>`_
    `Usage <usage.html>`_
    `Codeberg <https://codeberg.org/CEH-HOTDOG/RainfallGridder>`_


Why RainfallGridder?
====================

The goal of Time-Stream is to provide a user friendly Python library for processing time series data, particularly
in the hydrological and environmental domain. It is built on top of `Polars <https://docs.pola.rs/>`_, which handles
efficient DataFrame processes, whilst adding on specific functionality to help you manage time properties such as
resolution, periodicity, and anchor points.

- **Explicit time property management**: Perform methods on your data without worrying about whether it's handling your time data correctly.
- **Domain knowledge**: Built by software engineers and data scientists from `UKCEH <https://www.ceh.ac.uk/>`_, with years of experience working with hydrological and environmental data.
- **Building blocks**: Modular design for aggregation, flagging, QC, and infilling.
- **Polars performance**: Polars under the hood, vectorized paths where possible.

.. container:: image-row

   .. container:: image-item

      .. figure:: _static/ukceh_logo.png
         :alt: UKCEH
         :height: 100px
         :target: https://www.ceh.ac.uk

   .. container:: image-item

      .. figure:: _static/fdri_logo.png
         :alt: FDRI
         :height: 100px
         :target: https://fdri.org.uk


Community
=========

Developed at `UKCEH <https://www.ceh.ac.uk/>`_, welcoming community engagement and contributions.

License
=======

This project is licensed under the `GNU GPL v3.0 <https://codeberg.org/CEH-HOTDOG/RainfallGridder/raw/branch/main/LICENSE>`_.


.. toctree::
    :hidden:
    :maxdepth: 2
    :caption: Getting started

    installation

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: API reference

    api
